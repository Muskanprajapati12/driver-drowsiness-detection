# src/drowsiness.py - prolonged eye closure detection, measured in SECONDS

import time


class DrowsinessDetector:
    """
    Decides ALERT / DROWSY / NO FACE from one EAR value per video frame.

    - ear_threshold:        EAR below this value means "eye closed"
    - closed_seconds_limit: eyes must stay closed for this many SECONDS
                            before the driver is marked DROWSY. Using seconds
                            (not frames) means the result does not depend on
                            how many frames per second the webcam delivers.
    - recovery_frames:      eyes must be open for this many frames in a row
                            before the closure timer is reset
                            (so a single noisy frame does not break it)
    """

    def __init__(self, ear_threshold=0.20, closed_seconds_limit=0.7, recovery_frames=3):
        self.ear_threshold = ear_threshold
        self.closed_seconds_limit = closed_seconds_limit
        self.recovery_frames = recovery_frames

        self.closed_since = None    # time when the current eye closure started
        self.closed_seconds = 0.0   # how long the eyes have been closed so far
        self.open_frames = 0        # consecutive frames with open eyes
        self.face_found = True
        self.is_drowsy = False

    @property
    def status(self):
        if self.is_drowsy:
            return "DROWSY"
        if not self.face_found:
            return "NO FACE"
        return "ALERT"

    def update(self, ear, now=None):
        """
        Call once per frame.
        ear: the EAR value, or None if no face was found in this frame.
        now: current time in seconds (only the tests pass this; normally leave it out).
        Returns the current status string.
        """
        if now is None:
            now = time.monotonic()

        if ear is None:
            # No face: we cannot judge the eyes, so reset the timer.
            # If the driver was already DROWSY we keep that state on purpose.
            self.face_found = False
            self.closed_since = None
            self.closed_seconds = 0.0
            self.open_frames = 0
            return self.status

        self.face_found = True

        if ear < self.ear_threshold:
            # Eyes look closed in this frame
            if self.closed_since is None:
                self.closed_since = now
            self.closed_seconds = now - self.closed_since
            self.open_frames = 0
            if self.closed_seconds >= self.closed_seconds_limit:
                self.is_drowsy = True
        else:
            # Eyes look open in this frame
            self.open_frames += 1
            if self.open_frames >= self.recovery_frames:
                self.closed_since = None
                self.closed_seconds = 0.0
                self.is_drowsy = False

        return self.status


def feed(detector, ear, seconds, fps, clock):
    """Test helper: sends frames at the given FPS. clock is a one-item list (fake time)."""
    for _ in range(int(round(seconds * fps))):
        detector.update(ear, clock[0])
        clock[0] += 1.0 / fps


if __name__ == "__main__":
    # Self-test with made-up EAR values (0.30 = open, 0.05 = closed) and a fake clock
    detector = DrowsinessDetector(ear_threshold=0.20, closed_seconds_limit=0.7, recovery_frames=3)
    clock = [0.0]

    # Test 1: a normal blink (0.3 s) must NOT trigger DROWSY
    feed(detector, 0.05, 0.3, 30, clock)
    feed(detector, 0.30, 0.3, 30, clock)
    assert detector.status == "ALERT"
    print("Test 1 passed: short blink -> ALERT")

    # Test 2: eyes closed for 1 second -> DROWSY
    feed(detector, 0.05, 1.0, 30, clock)
    assert detector.status == "DROWSY"
    print("Test 2 passed: long closure -> DROWSY")

    # Test 3: eyes open again -> ALERT, but only after 3 open frames
    detector.update(0.30, clock[0]); clock[0] += 1 / 30
    detector.update(0.30, clock[0]); clock[0] += 1 / 30
    assert detector.status == "DROWSY"
    detector.update(0.30, clock[0]); clock[0] += 1 / 30
    assert detector.status == "ALERT"
    print("Test 3 passed: recovery -> ALERT")

    # Test 4: face lost while alert -> NO FACE
    detector.update(None, clock[0]); clock[0] += 1 / 30
    assert detector.status == "NO FACE"
    print("Test 4 passed: face lost -> NO FACE")

    # Test 5: face lost while drowsy -> stays DROWSY
    detector.update(0.30, clock[0]); clock[0] += 1 / 30
    feed(detector, 0.05, 1.0, 30, clock)
    detector.update(None, clock[0]); clock[0] += 1 / 30
    assert detector.status == "DROWSY"
    print("Test 5 passed: face lost while drowsy -> still DROWSY")

    # Test 6: same result at a low frame rate (10 FPS), the point of this upgrade
    slow = DrowsinessDetector(ear_threshold=0.20, closed_seconds_limit=0.7, recovery_frames=3)
    clock = [0.0]
    feed(slow, 0.05, 0.5, 10, clock)
    assert slow.status == "ALERT"
    feed(slow, 0.05, 0.5, 10, clock)
    assert slow.status == "DROWSY"
    print("Test 6 passed: at 10 FPS, 0.5 s closed -> ALERT, 1.0 s closed -> DROWSY")

    print("ALL DROWSINESS TESTS PASSED")