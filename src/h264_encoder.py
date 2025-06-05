import av.container
from video_capture import VideoCapture
from audio_capture import AudioCapture
from threading import Thread
import queue
import av
import numpy as np


class H264Encoder(Thread):
    __working: bool
    __container: av.container.OutputContainer
    __video_stream: av.VideoStream
    __audio_stream: av.AudioStream
    __vc: VideoCapture
    __ac: AudioCapture

    def __init__(
        self,
        output_file: str,
        vc: VideoCapture,
        ac: AudioCapture,
    ):
        super().__init__(daemon=True)
        self.__vc = vc
        self.__ac = ac

        self.__container = av.open(output_file, mode="w")
        self.__video_stream = self.__container.add_stream("h264")
        self.__video_stream.time_base = VideoCapture.VIDEO_TIMEBASE
        self.__video_stream.width = vc.width
        self.__video_stream.height = vc.height

        self.__audio_stream = self.__container.add_stream("aac")
        self.__audio_stream.layout = "mono" if AudioCapture.CHANNELS == 1 else "stereo"
        self.__audio_stream.sample_rate = AudioCapture.SAMPLE_RATE
        self.__audio_stream.format = "fltp"

        self.__working = True
        self.start()

    def run(self):
        while self.__working:
            try:
                video_frame = self.__vc.frame_queue.get_nowait()
                vf = av.VideoFrame.from_ndarray(video_frame.frame, format="bgr24")
                vf.pts = video_frame.pts

                video_packets = self.__video_stream.encode(vf)
                self.__container.mux(video_packets)
            except queue.Empty:
                pass
            except queue.ShutDown:
                break
            except Exception as e:
                print(f"Error processing video frame: {e}")
                break

            try:
                audio_frame = self.__ac.frame_queue.get_nowait()
                # 音频需要预处理
                array = (
                    np.frombuffer(audio_frame.chunk, dtype=np.int16).astype(np.float32)
                    / 32768.0
                )

                af = av.AudioFrame.from_ndarray(
                    array.reshape(AudioCapture.CHANNELS, -1),
                    format="fltp",
                    layout="mono" if AudioCapture.CHANNELS == 1 else "stereo",
                )
                af.sample_rate = AudioCapture.SAMPLE_RATE

                audio_packets = self.__audio_stream.encode(af)
                self.__container.mux(audio_packets)
            except queue.Empty:
                pass
            except queue.ShutDown:
                break
            except Exception as e:
                print(f"Error processing audio frame: {e}")
                break

    def stop(self):
        if not self.__working:
            return

        print("Stopping H264 Encoder...")
        self.__working = False
        self.__ac.stop()
        self.__vc.stop()

        remaining_video_packs = self.__video_stream.encode()
        self.__container.mux(remaining_video_packs)

        remaining_audio_packs = self.__audio_stream.encode()
        self.__container.mux(remaining_audio_packs)

        self.__container.close()

    def __del__(self):
        self.stop()
