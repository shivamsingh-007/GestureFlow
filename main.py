import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional

import pystray
from PIL import Image, ImageDraw

import config as cfg
from gesture_detector import Gesture
from gesture_engine import GestureEngine
from action_dispatcher import ActionDispatcher


class SliderApp:
    def __init__(self):
        self.conf = cfg.Config.load()
        self.engine: Optional[GestureEngine] = None
        self.dispatcher: Optional[ActionDispatcher] = None
        self._tray_icon: Optional[pystray.Icon] = None
        self._status = "Stopped"
        self._last_action = "None"
        self._root: Optional[tk.Tk] = None

    def _create_icon(self, color: str = "green") -> Image.Image:
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        if color == "green":
            fill = (0, 200, 0, 255)
        elif color == "red":
            fill = (200, 0, 0, 255)
        else:
            fill = (150, 150, 150, 255)
        draw.ellipse([8, 8, 56, 56], fill=fill)
        draw.ellipse([16, 16, 30, 30], fill=(255, 255, 255, 200))
        draw.ellipse([34, 16, 48, 30], fill=(255, 255, 255, 200))
        draw.rectangle([20, 34, 44, 52], fill=(255, 255, 255, 200))
        return img

    def _on_gesture(self, gesture: Gesture):
        if self.dispatcher:
            self.dispatcher.dispatch(gesture)

    def _on_action(self, action_name: str):
        self._last_action = action_name

    def _start_engine(self):
        if self.engine and self.engine.is_running:
            return
        self.dispatcher = ActionDispatcher(self.conf, on_action=self._on_action)
        if self.conf.use_com_api:
            self.dispatcher.ppt.connect()
        self.engine = GestureEngine(self.conf, on_gesture=self._on_gesture)
        self.engine.start()
        self._status = "Running"
        if self._tray_icon:
            self._tray_icon.icon = self._create_icon("green")
            self._tray_icon.update_menu()

    def _stop_engine(self):
        if self.engine:
            self.engine.stop()
            self.engine = None
        if self.dispatcher and self.dispatcher.ppt:
            self.dispatcher.ppt.disconnect()
        self.dispatcher = None
        self._status = "Stopped"
        if self._tray_icon:
            self._tray_icon.icon = self._create_icon("red")
            self._tray_icon.update_menu()

    def _quit(self, icon=None, item=None):
        self._stop_engine()
        if self._root:
            self._root.after(0, self._root.destroy)
        if self._tray_icon:
            self._tray_icon.stop()

    def _build_tray_menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: f"Status: {self._status}",
                lambda icon, item: None,
                enabled=False,
            ),
            pystray.MenuItem(
                lambda item: f"Last action: {self._last_action}",
                lambda icon, item: None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Start",
                lambda icon, item: self._start_engine(),
                visible=lambda item: self._status == "Stopped",
            ),
            pystray.MenuItem(
                "Stop",
                lambda icon, item: self._stop_engine(),
                visible=lambda item: self._status == "Running",
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", lambda icon, item: self._open_settings()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )

    def _open_settings(self):
        if self._root and self._root.winfo_exists():
            self._root.after(0, self._root.lift)
            return

        def _create_settings_window():
            self._root = tk.Tk()
            self._root.title("Slider Settings")
            self._root.geometry("400x520")
            self._root.resizable(False, False)
            self._root.protocol("WM_DELETE_WINDOW", lambda: self._root.withdraw())

            frame = ttk.Frame(self._root, padding=15)
            frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(frame, text="Slider - Gesture Control", font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))

            ttk.Label(frame, text="Camera Index").pack(anchor=tk.W)
            cam_var = tk.IntVar(value=self.conf.camera_index)
            ttk.Spinbox(frame, from_=0, to=5, textvariable=cam_var, width=5).pack(anchor=tk.W, pady=(0, 5))

            ttk.Label(frame, text="Frame Skip (lower = smoother, higher CPU)").pack(anchor=tk.W)
            skip_var = tk.IntVar(value=self.conf.skip_frames)
            ttk.Spinbox(frame, from_=1, to=4, textvariable=skip_var, width=5).pack(anchor=tk.W, pady=(0, 5))

            ttk.Label(frame, text="Swipe Threshold (lower = easier)").pack(anchor=tk.W)
            swipe_var = tk.DoubleVar(value=self.conf.swipe_threshold)
            ttk.Scale(frame, from_=0.05, to=0.25, variable=swipe_var, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))

            ttk.Label(frame, text="Swipe Cooldown (ms)").pack(anchor=tk.W)
            swipe_cd_var = tk.IntVar(value=self.conf.swipe_cooldown_ms)
            ttk.Spinbox(frame, from_=200, to=2000, increment=100, textvariable=swipe_cd_var, width=8).pack(anchor=tk.W, pady=(0, 5))

            ttk.Label(frame, text="Pinch Threshold (lower = easier)").pack(anchor=tk.W)
            pinch_var = tk.DoubleVar(value=self.conf.pinch_threshold)
            ttk.Scale(frame, from_=0.02, to=0.12, variable=pinch_var, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))

            preview_var = tk.BooleanVar(value=self.conf.show_camera_preview)
            ttk.Checkbutton(frame, text="Show Camera Preview", variable=preview_var).pack(anchor=tk.W, pady=5)

            com_var = tk.BooleanVar(value=self.conf.use_com_api)
            ttk.Checkbutton(frame, text="Use PowerPoint COM API (Windows only)", variable=com_var).pack(anchor=tk.W, pady=5)

            def save_settings():
                self.conf.camera_index = cam_var.get()
                self.conf.skip_frames = skip_var.get()
                self.conf.swipe_threshold = swipe_var.get()
                self.conf.swipe_cooldown_ms = swipe_cd_var.get()
                self.conf.pinch_threshold = pinch_var.get()
                self.conf.show_camera_preview = preview_var.get()
                self.conf.use_com_api = com_var.get()
                self.conf.save()
                was_running = self.engine and self.engine.is_running
                if was_running:
                    self._stop_engine()
                    self._start_engine()

            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=(10, 0))
            ttk.Button(btn_frame, text="Save & Apply", command=save_settings).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(btn_frame, text="Close", command=lambda: self._root.withdraw()).pack(side=tk.LEFT)

            self._root.withdraw()
            self._root.mainloop()

        threading.Thread(target=_create_settings_window, daemon=True).start()

    def run(self):
        icon_img = self._create_icon("red")
        self._tray_icon = pystray.Icon(
            "Slider",
            icon=icon_img,
            title="Slider - Gesture Control",
            menu=self._build_tray_menu(),
        )
        self._tray_icon.run()


def main():
    app = SliderApp()
    app.run()


if __name__ == "__main__":
    main()
