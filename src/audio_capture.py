from threading import Thread
import pyaudio
import queue
import time
from dataclasses import dataclass
from time_utils import gen_audio_pts
import webrtcvad


@dataclass
class CurrentAudioFrameChunk:
    pcm_chunk: bytes
    pts: int


class AudioCapture(Thread):
    __working: bool
    __audio: pyaudio.PyAudio
    __stream: pyaudio.Stream
    frame_queue: queue.Queue[CurrentAudioFrameChunk]
    vad: webrtcvad.Vad

    # 采样率
    SAMPLE_RATE = 16000
    # 每个chunk的持续时间ms
    CHUNK_DURATION = 30
    # 每一个chunk里面包含多少个采样数据
    SAMPLE_COUNT = SAMPLE_RATE // 1000 * CHUNK_DURATION
    VAD_LEVEL = 1

    def __init__(self):
        super().__init__(daemon=True)

        self.__audio = pyaudio.PyAudio()
        self.__stream = self.__audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=AudioCapture.SAMPLE_RATE,
            input=True,
            frames_per_buffer=AudioCapture.SAMPLE_COUNT,
        )

        self.__working = True
        self.frame_queue = queue.Queue(maxsize=128)
        self.vad = webrtcvad.Vad(AudioCapture.VAD_LEVEL)

    def run(self):
        print("Audio capture started...")

        while self.__working:
            chunk = self.__stream.read(
                AudioCapture.SAMPLE_COUNT, exception_on_overflow=False
            )

            # 语音活跃检测
            if not self.vad.is_speech(chunk, AudioCapture.SAMPLE_RATE):
                continue

            try:             
                self.frame_queue.put(
                    CurrentAudioFrameChunk(chunk, gen_audio_pts(AudioCapture.SAMPLE_COUNT)),
                    block=False,
                )
            except queue.Full:
                print("Audio queue is full, dropping data.")
                time.sleep(0.5)

    def stop(self):
        if self.__working:
            self.__working = False
            time.sleep(1)
            print("Stopping audio capture...")

            self.__stream.close()
            self.__audio.terminate()
            self.frame_queue.shutdown()

    def __del__(self):
        self.stop()
