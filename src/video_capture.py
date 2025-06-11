from threading import Thread
from dataclasses import dataclass
import cv2
import queue
import time
from fractions import Fraction


@dataclass
class VideoFrame:
    frame: cv2.typing.MatLike
    pts: int


class VideoCapture(Thread):
    __cap: cv2.VideoCapture
    __working: bool
    __first_frame_ts: float | None

    frame_queue: queue.Queue[VideoFrame]
    width: int
    height: int

    VIDEO_TIMEBASE = Fraction(1, 90000)  # 随便给一个就行
    __INNER_TIME_BASE = 1 / 90000

    def __init__(self):
        super().__init__(daemon=True)

        self.__cap = cv2.VideoCapture(0)
        if not self.__cap.isOpened():
            print("Error: Could not open video device.")
            exit(1)

        # try to get a frame and set width and height
        test_success, test_frame = self.__cap.read()
        if not test_success:
            print("Error: Could not read from video device.")
            exit(1)

        self.width = test_frame.shape[1]
        self.height = test_frame.shape[0]
        print(f"Video Capture initialized: {self.width}x{self.height}")

        self.frame_queue = queue.Queue(maxsize=128)
        self.__working = True
        self.__first_frame_ts = None


    def __generate_pts(self) -> int:
        now = time.time()

        if self.__first_frame_ts is None:
            self.__first_frame_ts = now

        return int((now - self.__first_frame_ts) / self.__INNER_TIME_BASE)

    def run(self):
        while self.__working and not self.frame_queue.is_shutdown:
            success, frame = self.__cap.read()
            pts = self.__generate_pts()

            if not success:
                print("Error: Could not read from video device.")
                break
            try:
                self.frame_queue.put_nowait(VideoFrame(frame=frame, pts=pts))
            except queue.Full:
                print("Warning: Video Frame queue is full, dropping frame.")
                time.sleep(0.5)
                continue
            except Exception as e:
                print(f"Error: {e}")
                break

    def stop(self):
        if not self.__working:
            return

        print("Stopping video capture...")
        self.__working = False
        time.sleep(1)

        self.frame_queue.shutdown()
        self.__cap.release()

    def __del__(self):
        self.stop()
