from threading import Thread
import cv2
import time
from dataclasses import dataclass
import queue
from time_utils import gen_video_pts


@dataclass
class CurrentVideoFrame:
    frame: cv2.typing.MatLike
    pts: int


class VideoCapture(Thread):
    # 这些是成员变量
    __working: bool
    __cap: cv2.VideoCapture
    width: int
    height: int
    current_fps: float
    frame_queue: queue.Queue[CurrentVideoFrame]

    def __calc_fps(last_time: float, current_time: float) -> float:
        if last_time <= 0 or (current_time - last_time <= 0):
            return 0.0

        return 1 / (current_time - last_time)

    def __init__(self):
        super().__init__(daemon=True)

        self.__cap = cv2.VideoCapture(0)
        if not self.__cap.isOpened():
            raise Exception("Could not open front camera.")

        self.width = int(self.__cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.__cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_fps = 0.0
        print(f"Video capture started. Width: {self.width}, Height: {self.height}")

        self.__working = True
        self.frame_queue = queue.Queue(maxsize=256)

    def run(self):
        last_time = time.time()

        while self.__working:
            ret, frame = self.__cap.read()
            if not ret:
                print("Could not read frame from front camera.")
                break

            current_time = time.time()
            self.current_fps = VideoCapture.__calc_fps(last_time, current_time)
            last_time = current_time

            try:
                self.frame_queue.put(
                    CurrentVideoFrame(frame, gen_video_pts()),
                    block=False,
                )
            except queue.Full:
                print("Frame queue is full, dropping frames.")
                time.sleep(0.5)

    def stop(self):
        if self.__working:
            self.__working = False
            time.sleep(1)
            print("Stopping video capture...")

            self.__cap.release()
            self.frame_queue.shutdown()

    def __del__(self):
        self.stop()
