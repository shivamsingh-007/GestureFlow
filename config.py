import json
import os
from dataclasses import dataclass, asdict

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


@dataclass
class Config:
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480

    swipe_threshold: float = 0.12
    swipe_frames: int = 5
    swipe_cooldown_ms: int = 600

    pinch_threshold: float = 0.06
    pinch_cooldown_ms: int = 400

    spread_threshold: float = 0.10
    spread_cooldown_ms: int = 400

    peace_cooldown_ms: int = 800

    min_detection_confidence: float = 0.7
    min_tracking_confidence: float = 0.6
    num_hands: int = 1

    zoom_step: float = 0.1
    use_com_api: bool = True

    show_camera_preview: bool = False
    skip_frames: int = 2

    @classmethod
    def load(cls) -> "Config":
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()

    def save(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(asdict(self), f, indent=2)
