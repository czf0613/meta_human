from dataclasses import dataclass
from threading import Thread
import pyaudio
import queue
import time

@dataclass
class AudioFrame:
    chunk: bytes

class AudioCapture(Thread):
    SAMPLE_RATE = 48000
    CHANNELS = 1
    CHUNK_SIZE = 1024
    # 可能得小心一下__VAD_BATCH_SIZE会不会大于CHUNK_SIZE
    __VAD_BATCH_SIZE = 20 * SAMPLE_RATE // 1000

    __working: bool
    __audio: pyaudio.PyAudio
    __stream: pyaudio.Stream
    frame_queue: queue.Queue[AudioFrame]

    def __init__(self):
        super().__init__(daemon=True)

        if self.__VAD_BATCH_SIZE > self.CHUNK_SIZE * self.CHANNELS:
            print("index may out of range, reduce the vad batch size.")
            exit(2)

        self.__audio = pyaudio.PyAudio()
        self.__stream = self.__audio.open(
            format=pyaudio.paInt16,
            channels=self.CHANNELS,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK_SIZE,
        )

        self.__working = True
        self.frame_queue = queue.Queue(maxsize=512)
    
    def run(self):
        while self.__working and not self.frame_queue.is_shutdown:
            chunk = self.__stream.read(self.CHUNK_SIZE, exception_on_overflow=False)

            #vad目前设置是检测20ms，所以要截取，音频样本数*声道*16bit
            # if not self.__vad.is_speech(
            #     chunk[: (self.__VAD_BATCH_SIZE * self.CHANNELS * 2)], self.SAMPLE_RATE
            # ):
            #     pass

            try:
                self.frame_queue.put_nowait(AudioFrame(chunk=chunk))
            except queue.Full:
                print("Audio frame queue is full, dropping frame.")
                time.sleep(0.5)
                continue
            except Exception as e:
                print(f"Error processing audio frame: {e}")
                break

    def stop(self):
        if not self.__working:
            return

        print("Stopping Audio Capture...")
        self.__working = False
        time.sleep(1)

        self.__stream.close()
        self.__audio.terminate()

    def __del__(self):
        self.stop()
