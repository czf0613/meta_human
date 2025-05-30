import os
import shutil
from video_capture import VideoCapture
from audio_capture import AudioCapture
from pyav_encoder import PyAVEncoder
import consts
import cv2
import queue


if __name__ == "__main__":
    shutil.rmtree("cache", ignore_errors=True)
    os.makedirs("cache", exist_ok=True) 

    vc: VideoCapture | None = None
    ac: AudioCapture | None = None
    encoder: PyAVEncoder | None = None

    try:
        vc = VideoCapture()
        width, height = vc.width, vc.height

        ac = AudioCapture()
        sample_rate = consts.SAMPLE_RATE

        encoder = PyAVEncoder(
            output_path = "output.mp4",
            width = vc.width,
            height = vc.height)

        
        vc.start()
        ac.start()
        encoder.start()

        print(f'{os.linesep}Press "q" to on window stop the video capture.{os.linesep}')

        while True:

            try:
                video_pack = vc.frame_queue.get(block=False)
                encoder.add_frame(video_pack)
                cv2.imshow("Camera Capture", video_pack.frame)
            except queue.Empty:
                pass

            try:
                audio_pack = ac.frame_queue.get(block=False)
                encoder.add_frame(audio_pack)
            except queue.Empty:
                print("no active voice detected")

            # cv2.putText(
            #     video_frame,
            #     f"FPS: {vc.current_fps:.1f}  PTS: {video_pts}",
            #     (10, 30),
            #     cv2.FONT_HERSHEY_SIMPLEX,
            #     1,
            #     (0, 255, 0),
            #     2,
            # )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        pass

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if vc is not None:
            vc.stop()

        if ac is not None:
            ac.stop()   

        if encoder is not None:
            encoder.stop()    