import os
import shutil
import time
import queue
import cv2
import ffmpeg
import numpy as np
from video_capture import VideoCapture
from audio_capture import AudioCapture

class MP4Encoder:
    def __init__(self, output_path, width, height, fps, sample_rate, channels):
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.sample_rate = sample_rate
        self.channels = channels
        
        # 初始化FFmpeg进程
        self.process = (
            ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='bgr24', 
                  s=f'{width}x{height}', r=fps)
            .output(
                ffmpeg.input('pipe:', format='s16le', ac=channels, ar=sample_rate),
                output_path,
                pix_fmt='yuv420p',
                vcodec='libx264',
                acodec='aac',
                preset='fast',
                crf=23,
                movflags='faststart'
            )
            .overwrite_output()
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
        )
        
    def write_frame(self, video_frame, audio_frame=None):
        # 写入视频帧
        self.process.stdin.write(
            video_frame
            .astype(np.uint8)
            .tobytes()
        )
        
        # 写入音频帧（如果有）
        if audio_frame is not None:
            self.process.stdin.write(audio_frame.tobytes())
    
    def close(self):
        self.process.stdin.close()
        self.process.wait()

if __name__ == "__main__":
    # 清理并创建缓存目录
    shutil.rmtree("cache", ignore_errors=True)
    os.makedirs("cache", exist_ok=True)
    
    output_path = "output.mp4"
    vc = None
    ac = None
    encoder = None

    try:
        # 初始化捕获设备
        vc = VideoCapture()
        ac = AudioCapture()
        
        # 获取参数
        width, height = vc.width, vc.height
        sample_rate, channels = AudioCapture.SAMPLE_RATE, 1
        
        # 估算帧率（初始值，实际会动态调整）
        estimated_fps = 30  
        encoder = MP4Encoder(output_path, width, height, 
                           estimated_fps, sample_rate, channels)
        
        vc.start()
        ac.start()
        
        print(f'\nPress "q" to stop recording and save to {output_path}\n')

        last_frame_time = time.time()
        frame_times = []
        
        while True:
            # 获取视频帧
            video_pack = vc.frame_queue.get()
            video_frame, video_pts = video_pack.frame, video_pack.pts
            
            # 尝试获取音频帧
            audio_pack = None
            try:
                audio_pack = ac.frame_queue.get_nowait()
            except queue.Empty:
                pass
                
            # 计算实际帧率（动态调整）
            current_time = time.time()
            frame_times.append(current_time)
            if len(frame_times) > 10:
                frame_times.pop(0)
                actual_fps = len(frame_times) / (frame_times[-1] - frame_times[0])
                
            # 添加调试信息到视频帧
            cv2.putText(
                video_frame,
                f"FPS: {vc.current_fps:.1f} | PTS: {video_pts}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
            
            # 编码帧
            encoder.write_frame(
                video_frame,
                audio_pack.pcm_chunk if audio_pack else None
            )
            
            # 显示预览
            cv2.imshow("Recording...", video_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 清理资源
        if vc is not None:
            vc.stop()
        if ac is not None:
            ac.stop()
        if encoder is not None:
            encoder.close()
        cv2.destroyAllWindows()
        
        print(f"\nRecording saved to {output_path}")