# Driver Drowsiness Detection System

A real-time driver drowsiness detection system written **only in Python**. It uses a webcam, MediaPipe facial landmarks and the **Eye Aspect Ratio (EAR)** to detect prolonged eye closure, shows the driver's status on screen and plays an alarm when the driver looks drowsy.

> **Important:** this is a learning / portfolio project. It is **not** a certified safety device and must not be relied on to prevent real accidents. See [Limitations](#limitations).

## Features

- Real-time webcam capture with OpenCV
- Face and facial landmark detection with MediaPipe Face Landmarker
- Eye detection from landmarks (6 points per eye)
- Eye Aspect Ratio (EAR) calculation, averaged over both eyes
- Prolonged eye closure detection over consecutive frames (a normal blink does not trigger the alarm)
- Configurable EAR threshold and closed-time limit (in seconds) in `config.py`
- Live on-screen EAR value and status: `ALERT`, `DROWSY` or `NO FACE`
- Audio alarm using pygame while the driver is `DROWSY`
- Start / stop monitoring from the keyboard
- Webcam error handling and face-not-detected handling
- Calibration tool (`calibrate.py`) that measures **your own** open-eye and closed-eye EAR and suggests a threshold

## Tech stack

| Purpose | Library |
|---|---|
| Webcam and drawing | OpenCV (`opencv-contrib-python`) |
| Face landmarks | MediaPipe |
| Numeric work | NumPy |
| Alarm sound | pygame |

Everything is free and open source. No paid APIs or services are used.

Tested with: Python 3.13.3, Windows 64-bit, mediapipe 1.2.3, numpy 2.5.5, pygame 2.6.1, opencv-contrib-python 5.1.0.95.

## Project structure

```
driver-drowsiness-detection/
├── main.py                 # runs the real-time system
├── calibrate.py            # measures your EAR and suggests a threshold
├── download_model.py       # downloads the MediaPipe model (run once)
├── config.py               # all settings in one place
├── requirements.txt
├── assets/
│   └── alarm.wav           # alarm sound
└── src/
    ├── camera.py           # webcam access and error handling
    ├── face_landmarks.py   # MediaPipe face landmark detection
    ├── ear.py              # EAR calculation
    ├── drowsiness.py       # ALERT / DROWSY / NO FACE logic
    └── alarm.py            # alarm playback
```

The model file `assets/face_landmarker.task` is not stored in the repository. It is downloaded by `download_model.py`.

## Installation (Windows, VS Code)

1. Install Python 3.13 (3.13.3 was used for testing) and make sure `python --version` works in a terminal.
2. Clone the repository and open the folder in VS Code:
   ```
   git clone https://github.com/Muskanprajapati12/driver-drowsiness-detection.git
   cd driver-drowsiness-detection
   ```
3. Create and activate a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. Install the libraries:
   ```
   pip install -r requirements.txt
   ```
5. Download the face landmark model (run once):
   ```
   python download_model.py
   ```

## How to run

```
python main.py
```

Keys on the video window:

| Key | Action |
|---|---|
| `S` | Start monitoring |
| `P` | Stop monitoring |
| `=` | Raise the EAR threshold (this run only) |
| `-` | Lower the EAR threshold (this run only) |
| `Q` or `ESC` | Quit |

The program starts in STANDBY. Press `S` to begin monitoring.

## Calibration (recommended)

The same EAR threshold does not fit every person, camera or lighting condition. Run:

```
python calibrate.py
```

Press `SPACE`, keep your eyes **open** for about 7 seconds, then **close** them for about 6 seconds when asked (the first 2 seconds of each phase are ignored so you have time to react). The tool prints your open-eye and closed-eye EAR and suggests `EAR_THRESHOLD` as 65% of your median open-eye EAR. It also warns you if the open and closed values are too close. Copy the suggested value into `config.py` if it differs a lot from the current one.

## Settings (`config.py`)

| Setting | Default | Meaning |
|---|---|---|
| `CAMERA_INDEX` | 0 | Which webcam to use (try 1 if it does not open) |
| `FRAME_WIDTH` / `FRAME_HEIGHT` | 640 / 480 | Requested frame size |
| `CAMERA_RETRY_ATTEMPTS` | 3 | Reconnect attempts if the camera fails |
| `EAR_THRESHOLD` | 0.20 | EAR below this value means the eye is closed |
|`CLOSED_SECONDS_LIMIT` | 0.7 | Seconds the eyes must stay closed before `DROWSY` (does not depend on FPS) |
| `RECOVERY_FRAMES` | 3 | Open frames in a row needed to return to `ALERT` |
| `NO_FACE_WARNING_FRAMES` | 60 | Frames without a face before a warning is shown |
| `MIN_FACE_DETECTION_CONFIDENCE`, `MIN_FACE_PRESENCE_CONFIDENCE`, `MIN_TRACKING_CONFIDENCE` | 0.5 | MediaPipe confidence limits (lowering them can help in dim light) |
| `ALARM_SOUND_PATH` | `assets/alarm.wav` | Alarm sound file (you can use your own `.wav`) |

## How it works

### 1. Facial landmarks

MediaPipe Face Landmarker finds the face in each frame and returns 478 landmark points (x, y coordinates normalised to the image). We use only 6 points around each eye, picked by index in `config.py`:

```
Right eye: [33, 160, 158, 133, 153, 144]
Left eye : [362, 385, 387, 263, 373, 380]
```

The 6 points are named p1 to p6:

- p1 and p4: the two **corners** of the eye
- p2 and p3: points on the **upper** eyelid
- p5 and p6: points on the **lower** eyelid

The order matters because the formula pairs them up.

### 2. Eye Aspect Ratio (EAR)

```
EAR = ( ||p2 - p6|| + ||p3 - p5|| ) / ( 2 * ||p1 - p4|| )
```

`||a - b||` is the straight-line (Euclidean) distance between two points:
`sqrt( (xa - xb)^2 + (ya - yb)^2 )`.

- The **numerator** adds two vertical distances (how far open the eyelids are).
- The **denominator** is twice the horizontal eye width. Dividing by it makes the value mostly independent of how far you sit from the camera.

Illustrative example: if both vertical distances are 8 px and the eye width is 30 px, then EAR = (8 + 8) / (2 * 30) = 0.27 (open eye). When the eye closes, the vertical distances shrink towards 0 and EAR drops sharply. The final EAR is the average of the left and right eye.

### 3. Prolonged closure and false alarm reduction

A blink lasts only a few frames, but drowsiness means the eyes stay closed longer. `src/drowsiness.py` therefore:

1. Counts consecutive frames where `EAR < EAR_THRESHOLD`.
2. Switches to `DROWSY` only when the eyes have stayed closed for `CLOSED_SECONDS_LIMIT` seconds.
3. Returns to `ALERT` only after `RECOVERY_FRAMES` open frames in a row, so one noisy frame does not break the count.
4. If no face is found, the counters are reset and the status is `NO FACE`. If the driver was already `DROWSY`, that state is kept on purpose.

The alarm plays while the status is `DROWSY` and stops when the eyes open again.

### 4. Error handling

- If the webcam cannot be opened, the program prints a clear error message (for example: another app is using the camera, camera permission is off) and exits without a traceback.
- If the model file is missing, the program tells you to run `python download_model.py`.
- If the face is not detected, the screen shows `NO FACE`.

### Self-test of the detection logic

```
python src/drowsiness.py
```

This runs 5 checks with made-up EAR values: short blink gives ALERT, long closure gives DROWSY, recovery gives ALERT, lost face gives NO FACE, and lost face while drowsy stays DROWSY.

## Testing in different conditions

Tested by one person (the developer) with a laptop webcam and `EAR_THRESHOLD = 0.20`. Blink = 3 normal blinks, closed = eyes closed on purpose.

| # | Condition | Open EAR (mean) | Closed EAR (mean) | Blink gave false DROWSY? | Closed eyes gave DROWSY? |
|---|---|---|---|---|---|
| 1 | Normal room light | 0.30 | 0.02 to 0.035 | No | Yes, in about 1 second |
| 3 | Low light | 0.31 | 0.105 | No | Yes, in about 1 to 2 seconds |
| 4 | Backlight (light behind the head) | 0.27 | 0.056 | No | Yes |
| 5 | Side light | not recorded | not recorded | No problem observed | No problem observed |
| 7 | Head tilted down | not recorded | not recorded | No problem observed | No problem observed |

Not tested: bright light directly on the face, sitting about 80 cm from the camera, wearing glasses.

## Limitations

Webcam-based drowsiness detection has real limits. Please read these before trusting any result.

- **Tested on one person and one webcam only.** The threshold that works for me may not work for you. Always run `calibrate.py`.
- **Low light hurts accuracy.** In low light the measured closed-eye EAR went up (about 0.105 instead of 0.02 to 0.035), so the gap between open and closed eyes became smaller. The face may also be lost more easily.
- **Detection delay depends on frame rate.** The limit is counted in frames, not seconds. In some runs the camera delivered only about 10 FPS instead of about 30 FPS (seen when the room was dim), so the same 20 frames take roughly 3 times longer and the alarm comes later.
- **Looking down can lower EAR.** When the head tilts down, the eyelids can look more closed from the camera, which can cause errors. This is a known weakness of EAR-based methods.
- **Glasses can disturb landmarks.** Reflections on glasses can move the landmark points and give odd EAR values. This was not tested here.
- **Distance and camera angle matter.** The camera should be roughly at eye level and facing the driver. Only a normal close sitting distance was tested.
- **Only eye closure is measured.** Yawning, head nodding, and microsleeps with partly open eyes are not detected.
- **Face lost while drowsy stays DROWSY.** If the face disappears during a drowsy state, the system keeps the alarm state because it cannot confirm that the driver is awake.
- **Not a real vehicle system.** It was only tested at a desk. Real driving brings vibration, sunlight changes and head movement that were not tested.
- **Windows only.** Tested on Windows with VS Code. Other systems may need changes.

## Possible future improvements

- Measure the closed time in **seconds** instead of frames, so it does not depend on FPS
- Add yawn detection (mouth aspect ratio) and head pose
- Save calibration values automatically per user
- Test with more people, glasses and real in-car lighting

## License
