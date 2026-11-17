# config.py - all project settings in one place

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- Camera settings ----
CAMERA_INDEX = 0            # 0 = default webcam. Try 1 if the camera does not open
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAMERA_RETRY_ATTEMPTS = 3   # how many times to try reconnecting if the camera fails
CAMERA_RETRY_DELAY_SEC = 1.0

# ---- Window ----
WINDOW_NAME = "Driver Drowsiness Detection"

# ---- MediaPipe Face Landmarker ----
MODEL_PATH = os.path.join(BASE_DIR, "assets", "face_landmarker.task")
MIN_FACE_DETECTION_CONFIDENCE = 0.5
MIN_FACE_PRESENCE_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# ---- Eye landmark indices (6 points per eye) ----
# p1 and p4 are the two eye corners, p2/p3 are on the upper eyelid,
# p5/p6 are on the lower eyelid. The order matters for the EAR formula.
RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

# ---- Drowsiness detection settings (change these for your own eyes) ----
EAR_THRESHOLD = 0.20        # EAR below this = eye closed (open eye ~0.30 for the developer)
CLOSED_FRAMES_LIMIT = 20    # consecutive closed frames before DROWSY (~0.7 s at 30 FPS)
RECOVERY_FRAMES = 3         # open frames needed to go back to ALERT
THRESHOLD_STEP = 0.01       # how much the = and - keys change the threshold
NO_FACE_WARNING_FRAMES = 60 # show a warning after this many frames without a face (~2 s)

# ---- Alarm ----
# If this file does not exist, a default beep sound is created automatically.
# You can replace it with your own .wav file.
ALARM_SOUND_PATH = os.path.join(BASE_DIR, "assets", "alarm.wav")

# ---- Debug display ----
SHOW_EYE_LABELS = False     # draw landmark numbers next to the eye points