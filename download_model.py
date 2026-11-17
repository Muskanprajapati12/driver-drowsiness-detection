# download_model.py - downloads the free MediaPipe Face Landmarker model (run once)

import os
import sys
import urllib.error
import urllib.request

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MODEL_PATH = os.path.join(ASSETS_DIR, "face_landmarker.task")
TEMP_PATH = MODEL_PATH + ".part"
MIN_EXPECTED_BYTES = 1_000_000  # a valid model is several MB


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    if os.path.isfile(MODEL_PATH) and os.path.getsize(MODEL_PATH) > MIN_EXPECTED_BYTES:
        print("Model already exists:", MODEL_PATH)
        return 0

    print("Downloading the model (a few MB), please wait...")
    try:
        urllib.request.urlretrieve(MODEL_URL, TEMP_PATH)
    except (urllib.error.URLError, OSError) as error:
        if os.path.isfile(TEMP_PATH):
            os.remove(TEMP_PATH)
        print("ERROR: download failed:", error)
        print("You can download it manually in a browser from:")
        print(MODEL_URL)
        print("and save it as assets\\face_landmarker.task")
        return 1

    size = os.path.getsize(TEMP_PATH)
    if size < MIN_EXPECTED_BYTES:
        os.remove(TEMP_PATH)
        print("ERROR: downloaded file is too small, so it is probably not the model.")
        return 1

    os.replace(TEMP_PATH, MODEL_PATH)
    print(f"Done. Saved to {MODEL_PATH} ({size / 1_000_000:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())