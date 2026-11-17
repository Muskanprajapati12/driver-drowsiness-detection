# src/face_landmarks.py - face detection + facial landmarks using MediaPipe

import os
import time

import cv2
import mediapipe as mp
import numpy as np


class ModelNotFoundError(Exception):
    """Raised when the face_landmarker.task model file is missing."""


class FaceLandmarkDetector:
    def __init__(self, model_path, min_detection_confidence=0.5,
                 min_presence_confidence=0.5, min_tracking_confidence=0.5):
        if not os.path.isfile(model_path):
            raise ModelNotFoundError(
                f"Model file not found: {model_path}\n"
                "Run this once to download it:  python download_model.py"
            )

        BaseOptions = mp.tasks.BaseOptions
        FaceLandmarker = mp.tasks.vision.FaceLandmarker
        FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
        RunningMode = mp.tasks.vision.RunningMode

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.VIDEO,   # tracking across webcam frames
            num_faces=1,                      # only the driver
            min_face_detection_confidence=min_detection_confidence,
            min_face_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = FaceLandmarker.create_from_options(options)
        self._start_time = time.monotonic()
        self._last_timestamp_ms = -1

    def detect(self, frame_bgr):
        """
        Finds the face in one BGR frame.
        Returns a NumPy array of shape (478, 2) with landmark positions in
        pixels (x, y), or None if no face is found.
        """
        # MediaPipe expects RGB, but OpenCV gives BGR
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # VIDEO mode needs a timestamp (ms) that always increases
        timestamp_ms = int((time.monotonic() - self._start_time) * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.face_landmarks:
            return None

        height, width = frame_bgr.shape[:2]
        landmarks = result.face_landmarks[0]  # first (only) face
        # Landmarks are normalized (0 to 1), so multiply by the image size
        return np.array([[lm.x * width, lm.y * height] for lm in landmarks])

    def close(self):
        """Releases the MediaPipe model."""
        self._landmarker.close()