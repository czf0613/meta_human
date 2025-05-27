import os
import shutil
from video_capture import VideoCapture
from audio_capture import AudioCapture
import cv2
import queue
import av
import numpy as np

class PyAVEncoder:
    def __init__(self, width:int, height:int, sample_rate:int, channels:int=1, current_fps:float=30.0):
        self.container = av.open("cache/output.mp4", mode="w")
        self.video_stream = self.container.add_stream("h264", rate=current_fps)
        self.video_stream.width = width
        self.video_stream.height = height
        self.video_stream.pix_fmt = "yuv420p"
        self.video_stream.options = {"preset": "ultrafast", "crf": "23"}

        self.audio_stream = self.container.add_stream("aac", rate=sample_rate)
        self.audio_stream.channels = channels
        self.audio_stream.sample_rate = sample_rate
        self.audio_stream.format = "s16"


        self.video_pts = 0
        self.audio_pts = 0
        self.video_stream.time_base = av.Rational(1, current_fps)

    
    def write_video_frame(self, bgr_frame:np.ndarray):
        yuv_frame = av.VideoFrame.from_ndarray(bgr_frame, format="bgr24")
        yuv_frame.pts = self.video_pts
        self.video_pts += int(1/self.video_stream.time_base*90000)
        self.encode_video(yuv_frame)
        return yuv_frame


    def write_audio_frame(self, pcm_chunk:bytes):
        if isinstance(pcm_chunk, bytes):
            pcm_chunk = np.frombuffer(pcm_chunk, dtype=np.int16)
        elif isinstance(pcm_chunk, np.ndarray) and pcm_chunk.dtype != np.int16:
            pcm_chunk = pcm_chunk.astype(np.int16)
        audio_frame = av.AudioFrame.from_ndarray(pcm_chunk.reshape(-1,1), format="s16", layout="mono")
        audio_frame.pts = self.audio_pts
        self.audio_pts += len(pcm_chunk) // 2 
        self.encode_audio(audio_frame)
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

        vc.start()
        ac.start()

        print(f'{os.linesep}Press "q" to on window stop the video capture.{os.linesep}')

        while True:
            video_pack = vc.frame_queue.get()
            video_frame, video_pts = video_pack.frame, video_pack.pts

            try:
                audio_pack = ac.frame_queue.get(block=False)
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

encoder= PyAVEncoder(
    output_path="output.mp4",
    video_width=vc.width,
    video_height=vc.height,
    sample_rate=AudioCapture.SAMPLE_RATE,
    current_fps=30.0)   

encoder.write_video_frame(video_frame)
if audio_pack:
    encoder.write_audio_frame(audio_pack.pcm_chunk)
encoder.close()       