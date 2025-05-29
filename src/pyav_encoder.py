import av
import numpy as np
from fractions import Fraction
import cv2
from threading import Thread
import queue
from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class VideoFrameData:
    frame: cv2.typing.MatLike
    pts:int

@dataclass
class AudioFrameData:
    pcm_chunk: bytes
    pts:int

class PyAVEncoder(Thread):
    def __init__(self, output_path:str, width:int, height:int, sample_rate:int,fps:float=30.0):

        super().__init__(daemon=True)
        self.__working = True

        #初始化视频和音频队列
        self.video_queue = queue.Queue(maxsize=256)
        self.audio_queue = queue.Queue(maxsize=256)

        #初始化编码器参数
        self.output_path = output_path
        self.width = width
        self.height = height
        self.sample_rate = sample_rate
        self.fps = fps

        #初始化容器和流
        self.container: Optional[av.container.OutputContainer] = None
        self.video_stream: Optional[av.stream.VideoStream] = None
        self.audio_stream: Optional[av.stream.AudioStream] = None

        #初始化编码器
        self.init_encoder()
    def init_encoder(self):
            try:
                self.output_path = "output.mp4"
                self.container = av.open(self.output_path, mode="w")

                #视频流设置
                self.video_stream = self.container.add_stream("h264", rate=round(self.fps))
                self.video_stream.width = self.width
                self.video_stream.height = self.height
                self.video_stream.pix_fmt = "yuv420p"
                self.video_stream.options = {"preset": "ultrafast", "crf": "23"}
                self.video_stream.time_base = Fraction(1, 90000)

                #音频流设置
                self.audio_stream = self.container.add_stream("aac", rate=self.sample_rate)
                self.audio_stream.format = "fltp"
                self.audio_stream.layout = "mono"
                self.audio_stream.time_base = Fraction(1, self.sample_rate)
                
                print(f"Encoder initialized. Output:{self.output_path}")
        
            except Exception as e:
                print(f"Failed to initialize encoder: {e}")
                self.__working = False

    def run(self):
        print("PyAV Encoder started...")

        while self.__working:
            try:
                #处理视频帧
                if not self.video_queue.empty():
                    video_data = self.video_queue.get_nowait()
                    self.write_video_frame(video_data.frame, video_data.pts)

                #处理音频帧
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get_nowait()
                    self.write_audio_frame(audio_data.pcm_chunk, audio_data.pts)

                time.sleep(0.001)  # 避免CPU占用过高

            except queue.Empty:
                time.sleep(0.01)  
            except Exception as e:
                print(f"Encodeing error: {e}")
                self.__working = False

    def __encode_video_frame(self, bgr_frame: cv2.typing.MatLike, pts: int):
        """编码视频帧"""
        if not self.__working or self.video_stream is None:
            return
            
        try:
            yuv_frame = av.VideoFrame.from_ndarray(bgr_frame, format="bgr24")
            yuv_frame.pts = pts
            for packet in self.video_stream.encode(yuv_frame):
                self.container.mux(packet)
        except Exception as e:
            print(f"Video encoding error: {str(e)}")

    def __encode_audio_frame(self, pcm_chunk: bytes, pts: int):
        """编码音频帧"""
        if not self.__working or self.audio_stream is None:
            return
            
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

    def add_video_frame(self, frame: cv2.typing.MatLike, pts: int):
        """添加视频帧到队列"""
        if not self.__working:
            return False
            
        try:
            self.video_queue.put(VideoFrameData(frame, pts), block=False)
            return True
        except queue.Full:
            print("Video queue is full, dropping frame")
            return False

    def add_audio_frame(self, pcm_chunk: bytes, pts: int):
        """添加音频帧到队列"""
        if not self.__working:
            return False
            
        try:
            self.audio_queue.put(AudioFrameData(pcm_chunk, pts), block=False)
            return True
        except queue.Full:
            print("Audio queue is full, dropping frame")
            return False

    def stop(self):
        #停止编码器
        if self.__working:
            self.__working = False
            
            # 刷新编码器缓冲区
            if self.container is not None and self.video_stream is not None:
                try:
                    for packet in self.video_stream.encode(None):
                        self.container.mux(packet)
                except Exception as e:
                    print(f"Error flushing video encoder: {str(e)}")
                    
            if self.container is not None and self.audio_stream is not None:
                try:
                    for packet in self.audio_stream.encode(None):
                        self.container.mux(packet)
                except Exception as e:
                    print(f"Error flushing audio encoder: {str(e)}")
            
            # 关闭容器
            if self.container is not None:
                try:
                    self.container.close()
                except Exception as e:
                    print(f"Error closing container: {str(e)}")
            
            print("Encoder stopped")

    def __del__(self):
        self.stop()

