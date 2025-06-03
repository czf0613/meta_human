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

    #添加VAD统计变量
    __vad_stats: dict
    __last_print_time: float

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
        self.__vad_stats = {
            "speech_frames": 0,
            "non_speech_frames": 0,
            "total_frames": 0,
            "last_speech_time": 0,
            "speech_detection_latency": 0
        }
        self.__last_print_time = time.time()

    def run(self):
        print("Audio capture started...")

        while self.__working:
            chunk = self.__stream.read(
                consts.SAMPLE_COUNT, exception_on_overflow=False
            )

            # 更新总帧数统计
            self.__vad_stats["total_frames"] += 1

            # 语音活跃检测
            is_speech = self.vad.is_speech(chunk, consts.SAMPLE_RATE)
            if is_speech:
                self.__vad_stats['speech_frames'] += 1
                current_time = time.time()
                # 如果是新开始的语音段（距离上次语音超过1秒）
                if current_time - self.__vad_stats['last_speech_time'] > 1.0:
                    if self.__vad_stats['last_speech_time'] > 0:  # 非首次检测
                        self.__vad_stats['detection_latency'] = current_time - self.__vad_stats['last_speech_time']
                    self.__vad_stats['last_speech_time'] = current_time
            else:
                self.__vad_stats['non_speech_frames'] += 1

            # 每5秒打印一次统计
            if time.time() - self.last_print_time >= 5.0:
                self.__print_stats()
                self.last_print_time = time.time()

            try:             
                self.frame_queue.put(
                    CurrentAudioFrameChunk(chunk, gen_audio_pts()),
                    block=False,
                )
            except queue.Full:
                print("Audio queue is full, dropping data.")
                time.sleep(0.5)

    def __print_stats(self):
        total = self.__vad_stats['total_frames']
        if total == 0:
            return
        
        speech_ratio = (self.__vad_stats['speech_frames'] / total) * 100
        non_speech_ratio = (self.__vad_stats['non_speech_frames'] / total) * 100
    
        print("\n=== VAD效率统计 ===")
        print(f"总处理帧数: {total}")
        print(f"语音帧: {self.__vad_stats['speech_frames']} ({speech_ratio:.1f}%)")
        print(f"非语音帧: {self.__vad_stats['non_speech_frames']} ({non_speech_ratio:.1f}%)")
        if self.__vad_stats['speech_frames'] > 0:
            print(f"平均检测延迟: {self.__vad_stats['speech_detection_latency']:.3f}秒")
        print("=================\n")

    def stop(self):
        if self.__working:
            self.__working = False
            time.sleep(1)
            print("Stopping audio capture...")
            self.__print_stats()

            self.__stream.close()
            self.__audio.terminate()
            self.frame_queue.shutdown()

    def __del__(self):
        self.stop()
