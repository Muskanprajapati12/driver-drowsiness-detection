# calibrate.py - measures YOUR open-eye and closed-eye EAR and suggests a threshold
# Run it with:  python calibrate.py

import time

import cv2
import numpy as np

import config
from src.camera import Camera, CameraError
from src.ear import average_ear
from src.face_landmarks import FaceLandmarkDetector, ModelNotFoundError

FONT = cv2.FONT_HERSHEY_SIMPLEX
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
ORANGE = (0, 165, 255)
WINDOW = config.WINDOW_NAME + " - Calibration"

# (message, total seconds, seconds to ignore at the start so you have time to react)
PHASES = [
    ("Look at the camera. Keep your eyes OPEN", 7.0, 2.0),
    ("Now CLOSE your eyes and keep them closed", 6.0, 2.0),
]
MIN_SAMPLES = 20  # need at least this many frames with a detected face


def draw_text(frame, lines):
    """Draws lines of text on a black strip at the top of the frame."""
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 15 + 30 * len(lines)), (0, 0, 0), -1)
    y = 30
    for text, color in lines:
        cv2.putText(frame, text, (10, y), FONT, 0.7, color, 2)
        y += 30


def wait_for_start(camera):
    """Shows the camera until SPACE is pressed. Returns False if the user quits."""
    while True:
        frame = cv2.flip(camera.read(), 1)
        draw_text(frame, [("Press SPACE to start the calibration", WHITE),
                          ("Q = quit", WHITE)])
        cv2.imshow(WINDOW, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # SPACE
            return True
        if key in (ord("q"), ord("Q"), 27):
            return False


def run_phase(camera, detector, message, duration, ignore_seconds):
    """Shows one instruction and collects EAR values. Returns None if the user quits."""
    values = []
    start = time.time()

    while True:
        elapsed = time.time() - start
        if elapsed >= duration:
            return values

        frame = cv2.flip(camera.read(), 1)
        points = detector.detect(frame)

        lines = [(message, WHITE), (f"Time left: {duration - elapsed:.0f} s", WHITE)]
        if points is None:
            lines.append(("Face not detected!", ORANGE))
        else:
            ear, _, _ = average_ear(points, config.LEFT_EYE_INDICES, config.RIGHT_EYE_INDICES)
            if elapsed >= ignore_seconds:
                values.append(ear)
                state = "recording"
            else:
                state = "get ready..."
            lines.append((f"EAR: {ear:.3f}  ({state})", GREEN))

        draw_text(frame, lines)
        cv2.imshow(WINDOW, frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            return None


def summarize(open_values, closed_values):
    """Prints the measured EAR values and a suggested threshold."""
    open_arr = np.array(open_values)
    closed_arr = np.array(closed_values)

    print()
    print("=== Calibration result ===")
    print(f"Open eyes  : mean={open_arr.mean():.3f}  min={open_arr.min():.3f}  "
          f"max={open_arr.max():.3f}  ({len(open_arr)} frames)")
    print(f"Closed eyes: mean={closed_arr.mean():.3f}  min={closed_arr.min():.3f}  "
          f"max={closed_arr.max():.3f}  ({len(closed_arr)} frames)")

    gap = float(open_arr.mean() - closed_arr.mean())
    suggested = round(float(np.median(open_arr)) * 0.65, 2)
    closed_high = float(np.percentile(closed_arr, 95))

    print()
    print(f"Suggested EAR_THRESHOLD = {suggested:.2f}   (65% of your open-eye EAR)")
    print(f"Current   EAR_THRESHOLD = {config.EAR_THRESHOLD:.2f}   (from config.py)")

    if gap < 0.08:
        print("WARNING: open-eye and closed-eye EAR are very close. "
              "Try better lighting, or move the camera to eye level.")
    if suggested <= closed_high:
        print("WARNING: the suggested threshold is not above your closed-eye values, "
              "so closed eyes may not be detected reliably.")


def main():
    try:
        detector = FaceLandmarkDetector(
            config.MODEL_PATH,
            config.MIN_FACE_DETECTION_CONFIDENCE,
            config.MIN_FACE_PRESENCE_CONFIDENCE,
            config.MIN_TRACKING_CONFIDENCE,
        )
    except ModelNotFoundError as error:
        print("ERROR:", error)
        return
    except Exception as error:
        print("ERROR: could not start the face landmark model:", error)
        return

    camera = Camera(config.CAMERA_INDEX, config.FRAME_WIDTH, config.FRAME_HEIGHT)
    try:
        camera.open()
    except CameraError as error:
        print("ERROR:", error)
        detector.close()
        return

    results = []
    try:
        if wait_for_start(camera):
            for message, duration, ignore_seconds in PHASES:
                values = run_phase(camera, detector, message, duration, ignore_seconds)
                if values is None:
                    break
                results.append(values)
    except CameraError as error:
        print("ERROR:", error)
    except KeyboardInterrupt:
        print("Stopped with Ctrl+C.")
    finally:
        camera.release()
        detector.close()
        cv2.destroyAllWindows()

    if len(results) != len(PHASES):
        print("Calibration was not completed.")
        return

    open_values, closed_values = results
    for name, values in (("open-eye", open_values), ("closed-eye", closed_values)):
        if len(values) < MIN_SAMPLES:
            print(f"ERROR: a face was found in only {len(values)} frames of the {name} phase. "
                  "Improve the lighting and face the camera.")
            return

    summarize(open_values, closed_values)


if __name__ == "__main__":
    main()