import av
import numpy as np
from fractions import Fraction
import cv2
from threading import Thread

class PyAVEncoder():
    def __init__(self, output_path:str, width:int, height:int, sample_rate:int,current_fps:float=30.0):
        # super().__init__(daemon=True)
        output_path = "output.mp4"
        self.container = av.open(output_path, mode="w")
        self.video_stream = self.container.add_stream("h264", rate=30)
        self.video_stream.width = width
        self.video_stream.height = height
        self.video_stream.pix_fmt = "yuv420p"
        self.video_stream.options = {"preset": "ultrafast", "crf": "23"}
        self.video_stream.time_base = Fraction(1, 90000)

        self.audio_stream = self.container.add_stream("aac", rate=sample_rate)
        self.audio_stream.format = "fltp"
        self.audio_stream.layout = "mono"
        self.audio_stream.time_base = Fraction(1, sample_rate)
        self.audio_pts = 0

    def write_video_frame(self, bgr_frame:cv2.typing.MatLike,pts:int):
        yuv_frame = av.VideoFrame.from_ndarray(bgr_frame, format="bgr24")
        yuv_frame.pts = pts
        for packet in self.video_stream.encode(yuv_frame):
            self.container.mux(packet)


    def write_audio_frame(self, pcm_chunk:bytes, pts:int):
        audio_array = np.frombuffer(pcm_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        audio_frame = av.AudioFrame.from_ndarray(audio_array.reshape(1,-1), format="fltp", layout="mono")
        audio_frame.pts = pts
        audio_frame.sample_rate = self.audio_stream.rate
        for packet in self.audio_stream.encode(audio_frame):
            self.container.mux(packet)
        

    def close(self):
        try:
            for packet in self.video_stream.encode(None):
                self.container.mux(packet)

            for packet in self.audio_stream.encode(None):
                self.container.mux(packet)

        finally:
            self.container.close()

