import time

# 时间基
VIDEO_TIME_BASE = 1 / 90000


start_time1 = None

def gen_video_pts() -> int:
    global start_time1
    if start_time1 is None:
        start_time1 = time.time()
    return int((time.time() - start_time1) / VIDEO_TIME_BASE)
    


samples_generated = 0

def gen_audio_pts(num_samples:int) -> int:
    global samples_generated
    pts= samples_generated
    samples_generated += num_samples
    return pts

