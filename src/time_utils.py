import time
import consts
start_time = None

def gen_video_pts() -> int:
    global start_time
    current_time = time.perf_counter()
    if start_time is None:
        start_time = current_time
    return int((current_time - start_time) / consts.VIDEO_TIME_BASE)
    


samples_generated = 0
AUDIO_TIME_BASE = 1 / consts.SAMPLE_RATE

def gen_audio_pts() -> int:
    global start_time
    current_time = time.perf_counter()
    if start_time is None:
        start_time = current_time
    return int((current_time - start_time) / AUDIO_TIME_BASE)

