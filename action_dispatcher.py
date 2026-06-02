import sys
import time
from typing import Callable, Optional

import pyautogui

import config as cfg
from gesture_detector import Gesture
from ppt_controller import PPTController

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01


class ActionDispatcher:
    def __init__(self, conf: cfg.Config, on_action: Optional[Callable[[str], None]] = None):
        self.conf = conf
        self.on_action = on_action
        self.ppt = PPTController()
        self._cooldowns: dict = {}

    def dispatch(self, gesture: Gesture) -> bool:
        now = time.time() * 1000
        cooldown_map = {
            Gesture.SWIPE_LEFT: self.conf.swipe_cooldown_ms,
            Gesture.SWIPE_RIGHT: self.conf.swipe_cooldown_ms,
            Gesture.SWIPE_UP: self.conf.swipe_cooldown_ms,
            Gesture.SWIPE_DOWN: self.conf.swipe_cooldown_ms,
            Gesture.PINCH: self.conf.pinch_cooldown_ms,
            Gesture.TWO_FINGER_SPREAD: self.conf.spread_cooldown_ms,
            Gesture.PEACE_SIGN: self.conf.peace_cooldown_ms,
        }

        cd = cooldown_map.get(gesture, 500)
        last = self._cooldowns.get(gesture, 0)
        if now - last < cd:
            return False

        self._cooldowns[gesture] = now
        action_name = self._execute(gesture)
        if action_name and self.on_action:
            self.on_action(action_name)
        return True

    def _execute(self, gesture: Gesture) -> Optional[str]:
        if gesture == Gesture.SWIPE_RIGHT:
            return self._next_slide()
        elif gesture == Gesture.SWIPE_LEFT:
            return self._prev_slide()
        elif gesture == Gesture.SWIPE_UP:
            return self._page_up()
        elif gesture == Gesture.SWIPE_DOWN:
            return self._page_down()
        elif gesture == Gesture.PINCH:
            return self._zoom_in()
        elif gesture == Gesture.TWO_FINGER_SPREAD:
            return self._zoom_out()
        elif gesture == Gesture.PEACE_SIGN:
            return self._exit_presentation()
        return None

    def _next_slide(self) -> str:
        if self.conf.use_com_api and self.ppt.is_connected:
            if self.ppt.next_slide():
                return "next_slide (COM)"
        pyautogui.press("right")
        return "next_slide"

    def _prev_slide(self) -> str:
        if self.conf.use_com_api and self.ppt.is_connected:
            if self.ppt.prev_slide():
                return "prev_slide (COM)"
        pyautogui.press("left")
        return "prev_slide"

    def _page_up(self) -> str:
        pyautogui.press("pageup")
        return "page_up"

    def _page_down(self) -> str:
        pyautogui.press("pagedown")
        return "page_down"

    def _zoom_in(self) -> str:
        if self.conf.use_com_api and self.ppt.is_connected:
            if self.ppt.zoom_in(self.conf.zoom_step):
                return "zoom_in (COM)"
        pyautogui.keyDown("ctrl")
        pyautogui.press("add")
        pyautogui.keyUp("ctrl")
        return "zoom_in"

    def _zoom_out(self) -> str:
        if self.conf.use_com_api and self.ppt.is_connected:
            if self.ppt.zoom_out(self.conf.zoom_step):
                return "zoom_out (COM)"
        pyautogui.keyDown("ctrl")
        pyautogui.press("subtract")
        pyautogui.keyUp("ctrl")
        return "zoom_out"

    def _exit_presentation(self) -> str:
        pyautogui.press("escape")
        return "exit_presentation"
