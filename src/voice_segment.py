from audio_capture import AudioCapture
from video_capture import VideoCapture
import webrtcvad
from typing import List, Optional



class VoiceSegment:
    def __init__(self):
        self.vc = VideoCapture()
        self.ac = AudioCapture()
        self.vad = webrtcvad.Vad(2)
        self.sample_rate = 48000
        self.frame_duration = 20
        self.frame_size = self.ac.__VAD_BATCH_SIZE

        
        self.speech_buffer: List[bytes] = []
        self.silence_frames = 0
        self.min_silence_to_end = 15
        self.min_silence_to_start = 3
        self.is_speaking = False

        
    def process_frame(self, frame: bytes): 
        vad_frame = frame[:self.frame_size*2]

        is_speech = self.vad.is_speech(vad_frame, self.sample_rate)
        if is_speech:
            self.silence_frames = 0
            if not self.is_speaking:
                # 可能开始新语音
                self.speech_buffer.append(frame)
                if len(self.speech_buffer) >= self.min_silence_to_start:
                    # 确认语音开始
                    self.is_speaking = True
                    self.vc.start()
                    self.ac.start()
                    
            else:
                pass
        else:
            if self.is_speaking:

                # 语音中遇到静音
                self.silence_frames += 1
                if self.silence_frames >= self.min_silence_to_end:
                    # 语音结束
                    self.is_speaking = False
                    self.vc.stop()
                    self.ac.stop()
                    self.speech_buffer = [] 
            else:
                # 持续静音，保留最后几帧作为预缓冲
                self.speech_buffer.append(frame)
                if len(self.speech_buffer) > self.min_silence_to_end:
                    self.speech_buffer = self.speech_buffer[-self.min_silence_to_end:]

