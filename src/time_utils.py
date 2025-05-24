import time

# 计算PTS的基准时间
TIME_START = time.time()
# 时间基
TIME_BASE = 1 / 90000


def gen_pts() -> int:
    now = time.time()
    return int((now - TIME_START) / TIME_BASE)
