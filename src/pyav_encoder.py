import av
import av.container
import numpy as np
from fractions import Fraction
import cv2
from threading import Thread
import queue
import consts
from video_capture import CurrentVideoFrame
from audio_capture import CurrentAudioFrameChunk

class PyAVEncoder(Thread):
    __working: bool
    buffer_queue: queue.Queue[CurrentVideoFrame|CurrentAudioFrameChunk]
    container: av.container.OutputContainer
    video_stream:av.VideoStream
    audio_stream:av.AudioStream
    def __init__(self, output_path:str, width:int, height:int):

        super().__init__(daemon=True)
        self.__working = True

        #初始化视频和音频队列
        self.buffer_queue = queue.Queue(maxsize=256)

        #初始化编码器    
        self.container = av.open(output_path, mode="w")

        #视频流设置
        self.video_stream = self.container.add_stream("h264", rate=30)
        self.video_stream.width = width
        self.video_stream.height = height
        self.video_stream.pix_fmt = "yuv420p"
        self.video_stream.options = {"preset": "ultrafast", "crf": "23"}
        self.video_stream.time_base = Fraction(1, 90000)

        #音频流设置
        self.audio_stream = self.container.add_stream("aac", rate=consts.SAMPLE_RATE)
        self.audio_stream.format = "fltp"
        self.audio_stream.layout = "mono"
        self.audio_stream.time_base = Fraction(1, consts.SAMPLE_RATE)
                         

    def run(self):
        print("PyAV Encoder started...")
        try:
            while self.__working:
                #处理视频帧
                datapack = self.buffer_queue.get()
                if isinstance(datapack, CurrentVideoFrame):
                    self.__encode_video_frame(datapack.frame, datapack.pts)
                
                elif isinstance(datapack, CurrentAudioFrameChunk):
                    self.__encode_audio_frame(datapack.pcm_chunk, datapack.pts)

        except queue.ShutDown:
            print("Encoder shutdown requested.")

    def __encode_video_frame(self, bgr_frame: cv2.typing.MatLike, pts: int):
        """编码视频帧"""
        try:
            yuv_frame = av.VideoFrame.from_ndarray(bgr_frame, format="bgr24")
            yuv_frame.pts = pts
            for packet in self.video_stream.encode(yuv_frame):
                self.container.mux(packet)
        except Exception as e:
            print(f"Video encoding error: {str(e)}")

    def __encode_audio_frame(self, pcm_chunk: bytes, pts: int):
        """编码音频帧"""
        try:
            audio_array = np.frombuffer(pcm_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            audio_frame = av.AudioFrame.from_ndarray(
                audio_array.reshape(1, -1), 
                format="fltp", 
                layout="mono"
            )
            audio_frame.pts = pts
            audio_frame.sample_rate = self.audio_stream.rate
            for packet in self.audio_stream.encode(audio_frame):
                self.container.mux(packet)
        except Exception as e:
            print(f"Audio encoding error: {str(e)}")

    def add_frame(self, frame: CurrentVideoFrame|CurrentAudioFrameChunk):
        """添加视频帧到队列"""
        if not self.__working:
            return False
            
        try:
            self.buffer_queue.put(frame, block=False)
            return True
        except queue.Full:
            print("Video queue is full, dropping frame")
            return False

    def stop(self):
        #停止编码器
        if self.__working:
            self.__working = False
            self.buffer_queue.shutdown()
            
            # 刷新编码器缓冲区
            try:
                for packet in self.video_stream.encode(None):
                    self.container.mux(packet)
            except Exception as e:
                print(f"Error flushing video encoder: {str(e)}")
                    

            try:
                for packet in self.audio_stream.encode(None):
                    self.container.mux(packet)
            except Exception as e:
                print(f"Error flushing audio encoder: {str(e)}")
            
            # 关闭容器
                try:
                    self.container.close()
                except Exception as e:
                    print(f"Error closing container: {str(e)}")
            
            print("Encoder stopped")

    def __del__(self):
        self.stop()

