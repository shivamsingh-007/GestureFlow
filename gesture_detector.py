import math
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

import config as cfg


class Gesture(Enum):
    NONE = auto()
    SWIPE_LEFT = auto()
    SWIPE_RIGHT = auto()
    SWIPE_UP = auto()
    SWIPE_DOWN = auto()
    PINCH = auto()
    TWO_FINGER_SPREAD = auto()
    PEACE_SIGN = auto()


@dataclass
class Landmark:
    x: float
    y: float
    z: float


FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_PIPS = [3, 6, 10, 14, 18]
FINGER_MCPS = [2, 5, 9, 13, 17]

THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

THUMB_IP = 3
INDEX_PIP = 6
MIDDLE_PIP = 10
RING_PIP = 14
PINKY_PIP = 18

WRIST = 0


def _distance(a: Landmark, b: Landmark) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def _is_finger_extended(landmarks: List[Landmark], finger_idx: int) -> bool:
    tip = landmarks[FINGER_TIPS[finger_idx]]
    pip = landmarks[FINGER_PIPS[finger_idx]]
    mcp = landmarks[FINGER_MCPS[finger_idx]]
    wrist = landmarks[WRIST]

    if finger_idx == 0:
        palm_center_x = (wrist.x + mcp.x) / 2
        tip_dist = abs(tip.x - palm_center_x)
        mcp_dist = abs(mcp.x - palm_center_x)
        return tip_dist > mcp_dist + 0.02
    return tip.y < pip.y


def _all_fingers_curled(landmarks: List[Landmark], indices: List[int]) -> bool:
    for i in indices:
        tip = landmarks[FINGER_TIPS[i]]
        pip = landmarks[FINGER_PIPS[i]]
        if tip.y < pip.y:
            return False
    return True


class GestureDetector:
    def __init__(self, conf: cfg.Config):
        self.conf = conf
        self.wrist_buffer: deque = deque(maxlen=conf.swipe_frames)
        self._last_gesture = Gesture.NONE

    def reset(self):
        self.wrist_buffer.clear()
        self._last_gesture = Gesture.NONE

    def detect(self, landmarks: List[Landmark]) -> Gesture:
        if len(landmarks) < 21:
            return Gesture.NONE

        wrist = landmarks[WRIST]
        self.wrist_buffer.append((wrist.x, wrist.y))

        gesture = self._check_peace_sign(landmarks)
        if gesture != Gesture.NONE:
            return gesture

        gesture = self._check_two_finger_spread(landmarks)
        if gesture != Gesture.NONE:
            return gesture

        gesture = self._check_pinch(landmarks)
        if gesture != Gesture.NONE:
            return gesture

        gesture = self._check_swipe(landmarks)
        if gesture != Gesture.NONE:
            return gesture

        return Gesture.NONE

    def _check_peace_sign(self, lm: List[Landmark]) -> Gesture:
        index_up = _is_finger_extended(lm, 1)
        middle_up = _is_finger_extended(lm, 2)
        ring_curled = lm[RING_TIP].y > lm[RING_PIP].y
        pinky_curled = lm[PINKY_TIP].y > lm[PINKY_PIP].y
        thumb_curled = not _is_finger_extended(lm, 0)

        if not (index_up and middle_up and ring_curled and pinky_curled and thumb_curled):
            return Gesture.NONE

        finger_dist = _distance(lm[INDEX_TIP], lm[MIDDLE_TIP])
        if finger_dist < self.conf.spread_threshold:
            return Gesture.PEACE_SIGN
        return Gesture.NONE

    def _check_pinch(self, lm: List[Landmark]) -> Gesture:
        dist = _distance(lm[THUMB_TIP], lm[INDEX_TIP])
        if dist < self.conf.pinch_threshold:
            return Gesture.PINCH
        return Gesture.NONE

    def _check_two_finger_spread(self, lm: List[Landmark]) -> Gesture:
        index_up = _is_finger_extended(lm, 1)
        middle_up = _is_finger_extended(lm, 2)
        ring_curled = lm[RING_TIP].y > lm[RING_PIP].y
        pinky_curled = lm[PINKY_TIP].y > lm[PINKY_PIP].y

        if not (index_up and middle_up and ring_curled and pinky_curled):
            return Gesture.NONE

        dist = _distance(lm[INDEX_TIP], lm[MIDDLE_TIP])
        if dist > self.conf.spread_threshold:
            return Gesture.TWO_FINGER_SPREAD
        return Gesture.NONE

    def _check_swipe(self, lm: List[Landmark]) -> Gesture:
        if len(self.wrist_buffer) < self.conf.swipe_frames:
            return Gesture.NONE

        all_fingers = _is_finger_extended(lm, 0) and _is_finger_extended(lm, 1) and _is_finger_extended(lm, 2)
        if not all_fingers:
            return Gesture.NONE

        start_x, start_y = self.wrist_buffer[0]
        end_x, end_y = self.wrist_buffer[-1]
        dx = end_x - start_x
        dy = end_y - start_y

        threshold = self.conf.swipe_threshold

        if abs(dx) > abs(dy) and abs(dx) > threshold:
            return Gesture.SWIPE_RIGHT if dx > 0 else Gesture.SWIPE_LEFT
        elif abs(dy) > abs(dx) and abs(dy) > threshold:
            return Gesture.SWIPE_DOWN if dy > 0 else Gesture.SWIPE_UP

        return Gesture.NONE
