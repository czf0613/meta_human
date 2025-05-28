import time
import consts
start_time1, start_time2 = None, None

def gen_video_pts() -> int:
    global start_time1
    if start_time1 is None:
        start_time1 = time.time()
    return int((time.time() - start_time1) / consts.VIDEO_TIME_BASE)
    


samples_generated = 0
AUDIO_TIME_BASE = 1 / consts.SAMPLE_RATE

def gen_audio_pts() -> int:
    global start_time2
    if start_time2 is None:
        start_time2 = time.time()
    return int((time.time() - start_time2) / AUDIO_TIME_BASE)

