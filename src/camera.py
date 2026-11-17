# src/camera.py - webcam handling

import cv2


class CameraError(Exception):
    """Raised for any webcam-related problem."""


class Camera:
    def __init__(self, index=0, width=640, height=480):
        self.index = index
        self.width = width
        self.height = height
        self.cap = None

    def open(self):
        """Opens the webcam. Raises CameraError if it cannot be opened."""
        # Try the DirectShow backend first (works best on Windows)
        backend = getattr(cv2, "CAP_DSHOW", cv2.CAP_ANY)
        self.cap = cv2.VideoCapture(self.index, backend)

        # If that fails, retry with the default backend
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(self.index)

        if not self.cap.isOpened():
            self.cap.release()
            self.cap = None
            raise CameraError(
                f"Could not open webcam (index {self.index}). "
                "Check: Is another app (Zoom/Teams) using the camera? "
                "Is camera permission ON in Windows Settings > Privacy & security > Camera? "
                "Try CAMERA_INDEX = 1 in config.py."
            )

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self):
        """Returns one frame. Raises CameraError if no frame is available."""
        if self.cap is None:
            raise CameraError("Call open() before reading frames.")

        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise CameraError(
                "Could not read a frame from the webcam. "
                "The camera may have been disconnected."
            )
        return frame

    def release(self):
        """Closes the webcam."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None