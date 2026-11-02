import os
import urllib.request
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
MODEL_PATH = "hand_landmarker.task"

class HandTracker:
    def __init__(self):
        self._ensure_model()
        
        try:
            base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=1,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            self.use_tasks = True
        except Exception as e:
            print(f"Failed to load Tasks API: {e}. Falling back to mp.solutions.hands")
            self.use_tasks = False
            self.mp_hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        
    def _ensure_model(self):
        if not os.path.exists(MODEL_PATH):
            print(f"Downloading hand_landmarker.task from {MODEL_URL}...")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print("Download complete.")

    def process(self, frame):
        if self.use_tasks:
            # Convert BGR frame to RGB format for MediaPipe Tasks
            rgb_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame[:, :, ::-1].copy())
            detection_result = self.detector.detect(rgb_frame)
            
            if not detection_result.hand_landmarks:
                return None
            return detection_result.hand_landmarks[0]
        else:
            # Fallback
            rgb_frame = frame[:, :, ::-1].copy()
            results = self.mp_hands.process(rgb_frame)
            if not results.multi_hand_landmarks:
                return None
            return results.multi_hand_landmarks[0].landmark
