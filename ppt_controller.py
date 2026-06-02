import sys
from typing import Optional

if sys.platform == "win32":
    try:
        import win32com.client
        import pythoncom
        HAS_COM = True
    except ImportError:
        HAS_COM = False
else:
    HAS_COM = False


class PPTController:
    def __init__(self):
        self._app: Optional[object] = None
        self._connected = False

    def connect(self) -> bool:
        if not HAS_COM:
            return False
        try:
            pythoncom.CoInitialize()
            self._app = win32com.client.GetObject(Class="PowerPoint.Application")
            self._connected = True
            return True
        except Exception:
            try:
                self._app = win32com.client.Dispatch("PowerPoint.Application")
                self._app.Visible = True
                self._connected = True
                return True
            except Exception:
                self._connected = False
                return False

    def disconnect(self):
        self._app = None
        self._connected = False
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass

    @property
    def is_connected(self) -> bool:
        if not self._connected or not self._app:
            return False
        try:
            _ = self._app.Presentations.Count
            return True
        except Exception:
            self._connected = False
            return False

    def zoom_in(self, step: float = 0.1) -> bool:
        if not self._ensure_connected():
            return False
        try:
            slideshow = self._app.SlideShowWindows(1)
            view = slideshow.View
            current_zoom = view.Zoom
            view.Zoom = min(current_zoom + step * 100, 400)
            return True
        except Exception:
            return self._zoom_keyboard_fallback("add")

    def zoom_out(self, step: float = 0.1) -> bool:
        if not self._ensure_connected():
            return False
        try:
            slideshow = self._app.SlideShowWindows(1)
            view = slideshow.View
            current_zoom = view.Zoom
            view.Zoom = max(current_zoom - step * 100, 50)
            return True
        except Exception:
            return self._zoom_keyboard_fallback("subtract")

    def next_slide(self) -> bool:
        if not self._ensure_connected():
            return False
        try:
            slideshow = self._app.SlideShowWindows(1)
            slideshow.View.NextSlide()
            return True
        except Exception:
            return False

    def prev_slide(self) -> bool:
        if not self._ensure_connected():
            return False
        try:
            slideshow = self._app.SlideShowWindows(1)
            slideshow.View.PreviousSlide()
            return True
        except Exception:
            return False

    def _ensure_connected(self) -> bool:
        if self.is_connected:
            return True
        return self.connect()

    def _zoom_keyboard_fallback(self, key: str) -> bool:
        import pyautogui
        try:
            pyautogui.keyDown("ctrl")
            pyautogui.press(key)
            pyautogui.keyUp("ctrl")
            return True
        except Exception:
            return False
