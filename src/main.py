from video_capture import VideoCapture
from audio_capture import AudioCapture
from h264_encoder import H264Encoder
import cv2
import queue
if __name__ == "__main__":
    vc = VideoCapture()
    ac = AudioCapture()
    encoder = H264Encoder("output.mp4", vc, ac)

    try:
        while True:

            try:
                video_pack = vc.frame_queue.get(block=False)
                # encoder.add_frame(video_pack)
                cv2.imshow("Camera Capture", video_pack.frame)
            except queue.Empty:
                pass

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        encoder.stop()
        cv2.destroyAllWindows()
        print("Program terminated.")
