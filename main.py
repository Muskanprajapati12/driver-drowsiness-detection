# main.py - STEP 11: all components integrated, with start/stop control and error handling

import time

import cv2

import config
from src.alarm import AlarmPlayer
from src.camera import Camera, CameraError
from src.drowsiness import DrowsinessDetector
from src.ear import average_ear
from src.face_landmarks import FaceLandmarkDetector, ModelNotFoundError

FONT = cv2.FONT_HERSHEY_SIMPLEX
GREEN = (0, 255, 0)
RED = (0, 0, 255)
ORANGE = (0, 165, 255)
YELLOW = (0, 255, 255)
CYAN = (255, 255, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)

STATUS_COLORS = {"ALERT": GREEN, "DROWSY": RED, "NO FACE": ORANGE, "STANDBY": GRAY}


def draw_face_box(frame, points):
    """Draws a rectangle around all detected landmarks."""
    x_min, y_min = points.min(axis=0)
    x_max, y_max = points.max(axis=0)
    cv2.rectangle(frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), GREEN, 2)


def draw_eye_points(frame, points, indices, show_labels):
    """Draws a dot (and optionally the landmark number) for each eye point."""
    for index in indices:
        x, y = int(points[index][0]), int(points[index][1])
        cv2.circle(frame, (x, y), 2, YELLOW, -1)
        if show_labels:
            cv2.putText(frame, str(index), (x + 3, y - 3), FONT, 0.35, CYAN, 1)


def make_drowsiness_detector(threshold):
    """Creates a fresh drowsiness detector (all counters at zero)."""
    return DrowsinessDetector(threshold, config.CLOSED_SECONDS_LIMIT, config.RECOVERY_FRAMES)


def reconnect_camera(camera, attempts, delay_seconds):
    """Tries to reopen the webcam. Returns True if it worked, False otherwise."""
    camera.release()
    for attempt in range(1, attempts + 1):
        print(f"Trying to reconnect the camera ({attempt}/{attempts})...")
        time.sleep(delay_seconds)
        try:
            camera.open()
            camera.read()  # make sure frames really arrive
            print("Camera reconnected.")
            return True
        except CameraError as error:
            camera.release()
            print("Reconnect failed:", error)
    return False


def main():
    # 1. Start the face landmark model
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

    # 2. Audio alarm (works without sound too, it just prints a warning)
    alarm = AlarmPlayer(config.ALARM_SOUND_PATH)

    # 3. Start the webcam
    camera = Camera(config.CAMERA_INDEX, config.FRAME_WIDTH, config.FRAME_HEIGHT)
    try:
        camera.open()
    except CameraError as error:
        print("ERROR:", error)
        alarm.close()
        detector.close()
        return

    print("Camera is ready. The system is in STANDBY.")
    print("Keys on the video window:")
    print("  S = start monitoring   P = stop monitoring   Q or ESC = quit")
    print("  = raises the EAR threshold, - lowers it (this run only)")

    monitoring = False
    drowsiness = make_drowsiness_detector(config.EAR_THRESHOLD)
    no_face_frames = 0
    previous_time = time.time()

    try:
        while True:
            # ---- 1. Get a frame (try to recover if the webcam fails) ----
            try:
                frame = camera.read()
            except CameraError as error:
                print("ERROR:", error)
                alarm.stop()
                if not reconnect_camera(camera, config.CAMERA_RETRY_ATTEMPTS,
                                        config.CAMERA_RETRY_DELAY_SEC):
                    print("The camera could not be recovered. Closing the program.")
                    break
                previous_time = time.time()
                continue

            frame = cv2.flip(frame, 1)  # mirror view feels more natural
            height, width = frame.shape[:2]

            now = time.time()
            fps = 1.0 / (now - previous_time) if now > previous_time else 0.0
            previous_time = now

            # ---- 2. Detection (only while monitoring) ----
            ear_text = "EAR: --"
            detail_text = "Left: --  Right: --"

            if monitoring:
                points = detector.detect(frame)
                if points is not None:
                    no_face_frames = 0
                    draw_face_box(frame, points)
                    draw_eye_points(frame, points, config.RIGHT_EYE_INDICES, config.SHOW_EYE_LABELS)
                    draw_eye_points(frame, points, config.LEFT_EYE_INDICES, config.SHOW_EYE_LABELS)

                    ear, left_ear, right_ear = average_ear(
                        points, config.LEFT_EYE_INDICES, config.RIGHT_EYE_INDICES
                    )
                    status = drowsiness.update(ear)
                    ear_text = f"EAR: {ear:.3f}"
                    detail_text = f"Left: {left_ear:.3f}  Right: {right_ear:.3f}"
                else:
                    no_face_frames += 1
                    status = drowsiness.update(None)
            else:
                status = "STANDBY"

            # ---- 3. Alarm: starts once when DROWSY begins, stops otherwise ----
            alarm.update(status)

            # ---- 4. Draw the screen ----
            if status == "DROWSY":
                cv2.rectangle(frame, (0, 0), (width - 1, height - 1), RED, 8)
                cv2.putText(frame, "WAKE UP!", (width // 2 - 110, height - 60),
                            FONT, 1.4, RED, 3)

            if monitoring and no_face_frames > config.NO_FACE_WARNING_FRAMES:
                cv2.putText(frame, "Face not visible - look at the camera",
                            (width // 2 - 235, height // 2), FONT, 0.7, ORANGE, 2)

            if not monitoring:
                cv2.putText(frame, "Press S to START monitoring",
                            (width // 2 - 190, height // 2), FONT, 0.8, WHITE, 2)

            if not alarm.available:
                alarm_text = "Alarm: no sound device"
            elif alarm.is_playing:
                alarm_text = "Alarm: ON"
            else:
                alarm_text = "Alarm: off"

            cv2.rectangle(frame, (0, 0), (360, 225), (0, 0, 0), -1)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 28), FONT, 0.7, GREEN, 2)
            cv2.putText(frame, ear_text, (10, 58), FONT, 0.9, WHITE, 2)
            cv2.putText(frame, detail_text, (10, 82), FONT, 0.55, WHITE, 1)
            cv2.putText(frame, f"Threshold: {drowsiness.ear_threshold:.2f}", (10, 108),
                        FONT, 0.6, WHITE, 1)
            cv2.putText(frame,
                        f"Closed: {drowsiness.closed_seconds:.2f}/{drowsiness.closed_seconds_limit:.2f} s",
                        (10, 134), FONT, 0.6, WHITE, 1)
            cv2.putText(frame, alarm_text, (10, 160), FONT, 0.6, WHITE, 1)
            cv2.putText(frame, status, (10, 205), FONT, 1.4, STATUS_COLORS[status], 3)

            cv2.putText(frame, "S: start   P: stop   Q: quit   =/-: threshold",
                        (10, height - 12), FONT, 0.5, WHITE, 1)

            cv2.imshow(config.WINDOW_NAME, frame)

            # ---- 5. Keyboard control ----
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == ord("Q") or key == 27:  # 27 = ESC key
                break
            elif key in (ord("s"), ord("S")):
                if not monitoring:
                    monitoring = True
                    drowsiness = make_drowsiness_detector(drowsiness.ear_threshold)
                    no_face_frames = 0
                    print("Monitoring started.")
            elif key in (ord("p"), ord("P")):
                if monitoring:
                    monitoring = False
                    alarm.stop()
                    print("Monitoring stopped.")
            elif key == ord("="):
                drowsiness.ear_threshold = min(0.50, round(drowsiness.ear_threshold + config.THRESHOLD_STEP, 3))
            elif key == ord("-"):
                drowsiness.ear_threshold = max(0.05, round(drowsiness.ear_threshold - config.THRESHOLD_STEP, 3))

    except KeyboardInterrupt:
        print("Stopped with Ctrl+C.")
    finally:
        alarm.close()
        camera.release()
        detector.close()
        cv2.destroyAllWindows()
        print("Alarm, camera and model released.")


if __name__ == "__main__":
    main()