# src/ear.py - Eye Aspect Ratio (EAR) calculation

import numpy as np


def euclidean_distance(point_a, point_b):
    """Straight-line distance between two (x, y) points."""
    return float(np.linalg.norm(np.asarray(point_a) - np.asarray(point_b)))


def eye_aspect_ratio(eye):
    """
    Calculates EAR for ONE eye.

    eye: 6 (x, y) points in this order:
         p1 = eye corner, p2 = upper lid, p3 = upper lid,
         p4 = other eye corner, p5 = lower lid, p6 = lower lid

    EAR = ( |p2 - p6| + |p3 - p5| ) / ( 2 * |p1 - p4| )
    """
    eye = np.asarray(eye, dtype=float)
    if eye.shape != (6, 2):
        raise ValueError(f"Expected 6 (x, y) points, got shape {eye.shape}")

    p1, p2, p3, p4, p5, p6 = eye

    vertical_1 = euclidean_distance(p2, p6)
    vertical_2 = euclidean_distance(p3, p5)
    horizontal = euclidean_distance(p1, p4)

    if horizontal == 0:
        return 0.0  # avoid division by zero

    return (vertical_1 + vertical_2) / (2.0 * horizontal)


def average_ear(points, left_indices, right_indices):
    """
    Returns (average_ear, left_ear, right_ear).
    points: NumPy array of shape (478, 2) from FaceLandmarkDetector.detect()
    """
    left_ear = eye_aspect_ratio(points[left_indices])
    right_ear = eye_aspect_ratio(points[right_indices])
    return (left_ear + right_ear) / 2.0, left_ear, right_ear


if __name__ == "__main__":
    # Hand-made eyes so the maths can be checked by hand
    open_eye = [(0, 0), (1, 1), (3, 1), (4, 0), (3, -1), (1, -1)]
    closed_eye = [(0, 0), (1, 0.1), (3, 0.1), (4, 0), (3, -0.1), (1, -0.1)]

    open_ear = eye_aspect_ratio(open_eye)
    closed_ear = eye_aspect_ratio(closed_eye)

    print(f"Open eye EAR   = {open_ear:.3f}  (expected 0.500)")
    print(f"Closed eye EAR = {closed_ear:.3f}  (expected 0.050)")

    assert abs(open_ear - 0.5) < 1e-9
    assert abs(closed_ear - 0.05) < 1e-9
    print("EAR self-test PASSED")