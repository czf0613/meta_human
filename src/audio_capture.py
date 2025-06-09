from dataclasses import dataclass
from threading import Thread
import pyaudio
import queue
import time
import webrtcvad
from typing import List, Optional

@dataclass
class AudioFrame:
    chunk: bytes

class VoiceSegment:
    def __init__(self):
        self.vad = webrtcvad.Vad(2)
        self.sample_rate = 48000
        self.frame_duration = 20
        self.frame_size = AudioCapture.__VAD_BATCH_SIZE
        
        self.speech_buffer: List[bytes] = []
        self.silence_frames = 0
        self.min_silence_to_end = 15
        self.min_silence_to_start = 3

        self.is_speaking = False
        self.segment_start = 0.0
        
    def process_frame(self, frame: AudioFrame) -> Optional[List[bytes]]:
        vad_frame = frame[:self.frame_size*2]

        is_speech = self.vad.is_speech(vad_frame, self.sample_rate)
        current_time = time.time()
        if is_speech:
            self.silence_frames = 0
            if not self.is_speaking:
                # 可能开始新语音
                self.speech_buffer.append(frame)
                if len(self.speech_buffer) >= self.min_silence_to_start:
                    # 确认语音开始
                    self.is_speaking = True
                    self.segment_start = current_time
            else:
                # 继续语音
                self.speech_buffer.append(frame)
        else:
            if self.is_speaking:
                # 语音中遇到静音
                self.silence_frames += 1
                self.speech_buffer.append(frame)
                if self.silence_frames >= self.min_silence_to_end:
                    # 语音结束
                    self.is_speaking = False
                    segment = self.speech_buffer.copy()
                    self.speech_buffer = []
                    return segment
            else:
                # 持续静音，保留最后几帧作为预缓冲
                self.speech_buffer.append(frame)
                if len(self.speech_buffer) > self.min_silence_to_end:
                    self.speech_buffer = self.speech_buffer[-self.min_silence_to_end:]
        
        return None  # 没有完整的语音段可返回

class AudioCapture(Thread):
    SAMPLE_RATE = 48000
    CHANNELS = 1
    CHUNK_SIZE = 1024
    # 可能得小心一下__VAD_BATCH_SIZE会不会大于CHUNK_SIZE
    __VAD_BATCH_SIZE = 20 * SAMPLE_RATE // 1000

    __working: bool
    __audio: pyaudio.PyAudio
    __stream: pyaudio.Stream
    __vad: webrtcvad.Vad
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
        self.start()
    
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
