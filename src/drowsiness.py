# src/drowsiness.py - prolonged eye closure detection with consecutive-frame validation


class DrowsinessDetector:
    """
    Decides ALERT / DROWSY / NO FACE from one EAR value per video frame.

    - ear_threshold:       EAR below this value means "eye closed"
    - closed_frames_limit: eyes must stay closed for this many frames
                           before the driver is marked DROWSY
    - recovery_frames:     eyes must be open for this many frames in a row
                           before the closed-frame count is reset
                           (so a single noisy frame does not break the count)
    """

    def __init__(self, ear_threshold=0.20, closed_frames_limit=20, recovery_frames=3):
        self.ear_threshold = ear_threshold
        self.closed_frames_limit = closed_frames_limit
        self.recovery_frames = recovery_frames

        self.closed_frames = 0   # frames with closed eyes (in the current closure)
        self.open_frames = 0     # consecutive frames with open eyes
        self.face_found = True
        self.is_drowsy = False

    @property
    def status(self):
        if self.is_drowsy:
            return "DROWSY"
        if not self.face_found:
            return "NO FACE"
        return "ALERT"

    def update(self, ear):
        """
        Call once per frame.
        ear: the EAR value, or None if no face was found in this frame.
        Returns the current status string.
        """
        if ear is None:
            # No face: we cannot judge the eyes, so reset the counters.
            # If the driver was already DROWSY we keep that state on purpose.
            self.face_found = False
            self.closed_frames = 0
            self.open_frames = 0
            return self.status

        self.face_found = True

        if ear < self.ear_threshold:
            # Eyes look closed in this frame
            self.closed_frames += 1
            self.open_frames = 0
            if self.closed_frames >= self.closed_frames_limit:
                self.is_drowsy = True
        else:
            # Eyes look open in this frame
            self.open_frames += 1
            if self.open_frames >= self.recovery_frames:
                self.closed_frames = 0
                self.is_drowsy = False

        return self.status


if __name__ == "__main__":
    # Simple self-test with made-up EAR values (0.30 = open, 0.05 = closed)
    detector = DrowsinessDetector(ear_threshold=0.20, closed_frames_limit=20, recovery_frames=3)

    # Test 1: a normal blink (6 closed frames) must NOT trigger DROWSY
    for _ in range(6):
        detector.update(0.05)
    for _ in range(10):
        detector.update(0.30)
    assert detector.status == "ALERT"
    print("Test 1 passed: short blink -> ALERT")

    # Test 2: eyes closed for 25 frames -> DROWSY
    for _ in range(25):
        detector.update(0.05)
    assert detector.status == "DROWSY"
    print("Test 2 passed: long closure -> DROWSY")

    # Test 3: eyes open again -> ALERT, but only after 3 open frames
    detector.update(0.30)
    detector.update(0.30)
    assert detector.status == "DROWSY"
    detector.update(0.30)
    assert detector.status == "ALERT"
    print("Test 3 passed: recovery -> ALERT")

    # Test 4: face lost while alert -> NO FACE
    detector.update(None)
    assert detector.status == "NO FACE"
    print("Test 4 passed: face lost -> NO FACE")

    # Test 5: face lost while drowsy -> stays DROWSY
    detector.update(0.30)
    for _ in range(25):
        detector.update(0.05)
    detector.update(None)
    assert detector.status == "DROWSY"
    print("Test 5 passed: face lost while drowsy -> still DROWSY")

    print("ALL DROWSINESS TESTS PASSED")