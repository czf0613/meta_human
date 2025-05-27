import os
import shutil
from video_capture import VideoCapture
from audio_capture import AudioCapture
import cv2
import queue
import av
import numpy as np

class PyAVEncoder:
    def __init__(self, output_path:str, width:int, height:int, sample_rate:int, channels:int=1, current_fps:float=30.0):
        output_path = "output.mp4"
        self.container = av.open(output_path, mode="w")
        self.video_stream = self.container.add_stream("h264", rate=30)
        self.video_stream.width = width
        self.video_stream.height = height
        self.video_stream.pix_fmt = "yuv420p"
        self.video_stream.options = {"preset": "ultrafast", "crf": "23"}

        self.audio_stream = self.container.add_stream("aac", rate=sample_rate)
        self.audio_stream.sample_rate = sample_rate
        self.audio_stream.format = "s16"


        self.video_pts = 0
        self.audio_pts = 0
        self.video_frame_duration = 1.0/current_fps

    
    def write_video_frame(self, bgr_frame:np.ndarray):
        yuv_frame = av.VideoFrame.from_ndarray(bgr_frame, format="bgr24")
        yuv_frame.pts = self.video_pts
        self.video_pts += int(1.0/self.video_frame_duration*90000)
        for packet in self.video_stream.encode(yuv_frame):
            self.container.mux(packet)
        return yuv_frame


    def write_audio_frame(self, pcm_chunk:bytes):
        audio_array = np.frombuffer(pcm_chunk, dtype=np.int16)
        audio_frame = av.AudioFrame.from_ndarray(audio_array.reshape(1,-1), format="s16", layout="mono")
        audio_frame.pts = self.audio_pts
        self.audio_pts += len(audio_array) 
        for packet in self.audio_stream.encode(audio_frame):
            self.container.mux(packet)
        return audio_frame
        

    def close(self):
        for packet in self.video_stream.encode():
            self.container.mux(packet)

        for packet in self.audio_stream.encode():
            self.container.mux(packet)

        self.container.close()


if __name__ == "__main__":
    shutil.rmtree("cache", ignore_errors=True)
    os.makedirs("cache", exist_ok=True)

    vc: VideoCapture | None = None
    ac: AudioCapture | None = None

    try:
        vc = VideoCapture()
        width, height = vc.width, vc.height

        ac = AudioCapture()
        sample_rate, channels = AudioCapture.SAMPLE_RATE, 1

        encoder= PyAVEncoder(
    output_path="output.mp4",
    width=vc.width,
    height=vc.height,
    sample_rate=AudioCapture.SAMPLE_RATE,
    channels=1,
    current_fps=30.0)   

        vc.start()
        ac.start()

        print(f'{os.linesep}Press "q" to on window stop the video capture.{os.linesep}')

        while True:
            video_pack = vc.frame_queue.get()
            video_frame, video_pts = video_pack.frame, video_pack.pts
            encoder.write_video_frame(video_frame)

            try:
                audio_pack = ac.frame_queue.get(block=False)
                encoder.write_audio_frame(audio_pack.pcm_chunk)
                audio_frame, audio_pts = (
                    audio_pack.pcm_chunk,
                    audio_pack.pts,
                )
            except queue.Empty:
                print("no active voice detected")

            cv2.putText(
                video_frame,
                f"FPS: {vc.current_fps:.1f}  PTS: {video_pts}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            cv2.imshow("Camera Capture", video_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if vc is not None:
            vc.stop()

        if ac is not None:
            ac.stop()       