import av
import numpy as np
from fractions import Fraction
import cv2

class PyAVEncoder:
    def __init__(self, output_path:str, width:int, height:int, sample_rate:int, channels:int=1, current_fps:float=30.0):
        output_path = "output.mp4"
        self.container = av.open(output_path, mode="w")
        self.video_stream = self.container.add_stream("h264", rate=30)
        self.video_stream.width = width
        self.video_stream.height = height
        self.video_stream.pix_fmt = "yuv420p"
        self.video_stream.options = {"preset": "ultrafast", "crf": "23"}
        self.video_stream.time_base = Fraction(1, 90000)

        self.audio_stream = self.container.add_stream("pcm_s16le", rate=sample_rate)
        self.audio_stream.sample_rate = sample_rate
        self.audio_stream.format = "s16"
        self.audio_stream.layout = "mono"

        self.audio_pts = 0

    def write_video_frame(self, bgr_frame:cv2.typing.MatLike,pts:int):
        
        yuv_frame = av.VideoFrame.from_ndarray(bgr_frame, format="bgr24")
        yuv_frame.pts = pts
        for packet in self.video_stream.encode(yuv_frame):
            self.container.mux(packet)


    def write_audio_frame(self, pcm_chunk:bytes):
        audio_array = np.frombuffer(pcm_chunk, dtype=np.int16)
        audio_frame = av.AudioFrame.from_ndarray(audio_array.reshape(1,-1), format="s16", layout="mono")
        audio_frame.pts = self.audio_pts
        self.audio_pts += len(audio_array) 
        # for packet in self.audio_stream.encode(audio_frame):
            # self.container.mux(packet)
            # pass
        

    def close(self):
        for packet in self.video_stream.encode():
            self.container.mux(packet)

        for packet in self.audio_stream.encode():
            self.container.mux(packet)

        self.container.close()

