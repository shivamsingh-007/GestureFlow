import threading
import time
from typing import Callable, Optional

import cv2
import mediapipe as mp
import numpy as np

import config as cfg
from gesture_detector import GestureDetector, Gesture, Landmark


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

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.conf.num_hands,
            min_detection_confidence=self.conf.min_detection_confidence,
            min_tracking_confidence=self.conf.min_tracking_confidence,
        )
        self._preview_frame: Optional[np.ndarray] = None

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
        if self._started:
            try:
                self.hands.close()
            except Exception:
                pass
        with self._lock:
            self._preview_frame = None

    def _run_loop(self):
        self._cap = cv2.VideoCapture(self.conf.camera_index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.conf.frame_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.conf.frame_height)

        if not self._cap.isOpened():
            self._running.clear()
            return

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
            results = self.hands.process(rgb)

            gesture = Gesture.NONE

            if results.multi_hand_landmarks:
                hand_lm = results.multi_hand_landmarks[0]
                landmarks = [
                    Landmark(x=lm.x, y=lm.y, z=lm.z) for lm in hand_lm.landmark
                ]
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

    def _draw_landmarks(self, frame, hand_landmarks):
        mp.solutions.drawing_utils.draw_landmarks(
            frame,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2),
            mp.solutions.drawing_utils.DrawingSpec(color=(255, 0, 0), thickness=1),
        )
