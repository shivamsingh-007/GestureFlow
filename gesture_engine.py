import os
import threading
import time
from typing import Callable, Optional

import cv2
import mediapipe as mp
import numpy as np

import config as cfg
from gesture_detector import GestureDetector, Gesture, Landmark

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "hand_landmarker.task")


class GestureEngine:
    def __init__(self, conf: cfg.Config, on_gesture: Callable[[Gesture], None]):
        self.conf = conf
        self.on_gesture = on_gesture
        self.detector = GestureDetector(conf)
        self._running = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_count = 0
        self._lock = threading.Lock()
        self._started = False
        self._preview_frame: Optional[np.ndarray] = None
        self._landmarker = None

    def _init_landmarker(self):
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=self.conf.num_hands,
            min_hand_detection_confidence=self.conf.min_detection_confidence,
            min_tracking_confidence=self.conf.min_tracking_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    @property
    def preview_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._preview_frame.copy() if self._preview_frame is not None else None

    def start(self):
        if self._running.is_set():
            return
        self._running.set()
        self._started = True
        self.detector.reset()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None
        if self._cap and self._cap.isOpened():
            self._cap.release()
            self._cap = None
        if self._landmarker:
            try:
                self._landmarker.close()
            except Exception:
                pass
            self._landmarker = None
        with self._lock:
            self._preview_frame = None

    def _run_loop(self):
        try:
            self._init_landmarker()
        except Exception:
            self._running.clear()
            self._started = False
            return

        self._cap = cv2.VideoCapture(self.conf.camera_index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.conf.frame_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.conf.frame_height)

        if not self._cap.isOpened():
            self._running.clear()
            self._started = False
            return

        timestamp_ms = 0

        while self._running.is_set():
            success, frame = self._cap.read()
            if not success:
                time.sleep(0.01)
                continue

            self._frame_count += 1
            if self._frame_count % self.conf.skip_frames != 0:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            timestamp_ms += int(1000 / 30)
            result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

            gesture = Gesture.NONE

            if result.hand_landmarks:
                hand_lm = result.hand_landmarks[0]
                landmarks = [Landmark(x=lm.x, y=lm.y, z=lm.z) for lm in hand_lm]
                gesture = self.detector.detect(landmarks)

                if self.conf.show_camera_preview:
                    self._draw_landmarks(frame, hand_lm)

            if self.conf.show_camera_preview:
                with self._lock:
                    self._preview_frame = frame

            if gesture != Gesture.NONE:
                self.on_gesture(gesture)

        if self._cap and self._cap.isOpened():
            self._cap.release()

    def _draw_landmarks(self, frame, landmarks):
        h, w = frame.shape[:2]
        for lm in landmarks:
            x, y = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
