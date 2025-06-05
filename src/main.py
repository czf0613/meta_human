from video_capture import VideoCapture
from audio_capture import AudioCapture
from h264_encoder import H264Encoder
import cv2

if __name__ == "__main__":
    vc = VideoCapture()
    ac = AudioCapture()
    encoder = H264Encoder("output.mp4", vc, ac)

    try:
        while True:
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        encoder.stop()
        cv2.destroyAllWindows()
        print("Program terminated.")
