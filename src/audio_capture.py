from threading import Thread
import pyaudio
import queue
import time
from dataclasses import dataclass
from time_utils import gen_audio_pts
import webrtcvad
import consts

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

    def __init__(self):
        super().__init__(daemon=True)

        self.__audio = pyaudio.PyAudio()
        self.__stream = self.__audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=consts.SAMPLE_RATE,
            input=True,
            frames_per_buffer=consts.SAMPLE_COUNT,
        )

        self.__working = True
        self.frame_queue = queue.Queue(maxsize=128)
        self.vad = webrtcvad.Vad(consts.VAD_LEVEL)

    def run(self):
        print("Audio capture started...")

        while self.__working:
            chunk = self.__stream.read(
                consts.SAMPLE_COUNT, exception_on_overflow=False
            )

            # 语音活跃检测
            frame_chunk = CurrentAudioFrameChunk(chunk, max(gen_audio_pts()-consts.SAMPLE_COUNT, 0))
            is_speech = self.vad.is_speech(chunk, consts.SAMPLE_RATE)
            if not is_speech:
                continue
            try:             
                self.frame_queue.put(
                    frame_chunk,
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
