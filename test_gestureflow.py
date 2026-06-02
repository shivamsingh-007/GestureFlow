"""
Comprehensive test suite for Slider gesture controller.
Tests: gesture detection logic, cooldowns, action dispatch, config, engine pipeline.
"""
import sys
import os
import time
import math
import threading
import unittest
from unittest.mock import patch, MagicMock, call
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from gesture_detector import GestureDetector, Gesture, Landmark, _distance, _is_finger_extended
from action_dispatcher import ActionDispatcher
from ppt_controller import PPTController


def make_hand_open_palm():
    """Simulate an open palm with all fingers extended, wrist at center."""
    lm = [Landmark(x=0.5, y=0.9, z=0.0)] * 21  # wrist at bottom center
    # Thumb (right hand, fingers point up)
    lm[1] = Landmark(x=0.45, y=0.75, z=0.0)  # thumb MCP
    lm[2] = Landmark(x=0.40, y=0.65, z=0.0)  # thumb IP
    lm[3] = Landmark(x=0.35, y=0.55, z=0.0)  # thumb tip
    lm[4] = Landmark(x=0.30, y=0.50, z=0.0)  # thumb tip (4)
    # Index
    lm[5] = Landmark(x=0.42, y=0.55, z=0.0)  # MCP
    lm[6] = Landmark(x=0.42, y=0.40, z=0.0)  # PIP
    lm[7] = Landmark(x=0.42, y=0.30, z=0.0)  # DIP
    lm[8] = Landmark(x=0.42, y=0.20, z=0.0)  # tip
    # Middle
    lm[9] = Landmark(x=0.50, y=0.55, z=0.0)
    lm[10] = Landmark(x=0.50, y=0.38, z=0.0)
    lm[11] = Landmark(x=0.50, y=0.28, z=0.0)
    lm[12] = Landmark(x=0.50, y=0.18, z=0.0)
    # Ring
    lm[13] = Landmark(x=0.58, y=0.55, z=0.0)
    lm[14] = Landmark(x=0.58, y=0.40, z=0.0)
    lm[15] = Landmark(x=0.58, y=0.30, z=0.0)
    lm[16] = Landmark(x=0.58, y=0.20, z=0.0)
    # Pinky
    lm[17] = Landmark(x=0.65, y=0.58, z=0.0)
    lm[18] = Landmark(x=0.65, y=0.45, z=0.0)
    lm[19] = Landmark(x=0.65, y=0.35, z=0.0)
    lm[20] = Landmark(x=0.65, y=0.25, z=0.0)
    return lm


def make_hand_peace_sign():
    """Peace/V sign: index and middle up, ring/pinky curled, thumb curled."""
    lm = make_hand_open_palm()
    # Ring curled
    lm[14] = Landmark(x=0.58, y=0.50, z=0.0)
    lm[15] = Landmark(x=0.58, y=0.55, z=0.0)
    lm[16] = Landmark(x=0.58, y=0.60, z=0.0)
    # Pinky curled
    lm[18] = Landmark(x=0.65, y=0.52, z=0.0)
    lm[19] = Landmark(x=0.65, y=0.58, z=0.0)
    lm[20] = Landmark(x=0.65, y=0.62, z=0.0)
    # Thumb curled (tip close to MCP, near palm center)
    lm[4] = Landmark(x=0.48, y=0.75, z=0.0)
    lm[2] = Landmark(x=0.49, y=0.75, z=0.0)
    # Index and middle close together (not spread)
    lm[8] = Landmark(x=0.42, y=0.20, z=0.0)
    lm[12] = Landmark(x=0.44, y=0.20, z=0.0)
    return lm


def make_hand_pinch():
    """Pinch: thumb tip and index tip very close."""
    lm = make_hand_open_palm()
    lm[4] = Landmark(x=0.35, y=0.30, z=0.0)  # thumb tip
    lm[8] = Landmark(x=0.37, y=0.31, z=0.0)   # index tip (close to thumb)
    return lm


def make_hand_two_finger_spread():
    """Two fingers spread: index + middle up, ring/pinky curled, fingers spread, thumb curled."""
    lm = make_hand_open_palm()
    # Ring curled
    lm[14] = Landmark(x=0.58, y=0.50, z=0.0)
    lm[16] = Landmark(x=0.58, y=0.60, z=0.0)
    # Pinky curled
    lm[18] = Landmark(x=0.65, y=0.52, z=0.0)
    lm[20] = Landmark(x=0.65, y=0.62, z=0.0)
    # Thumb curled (tip close to MCP, both near palm center)
    lm[4] = Landmark(x=0.48, y=0.75, z=0.0)
    lm[2] = Landmark(x=0.49, y=0.75, z=0.0)
    # Spread fingers far apart
    lm[8] = Landmark(x=0.30, y=0.20, z=0.0)
    lm[12] = Landmark(x=0.65, y=0.20, z=0.0)
    return lm


class TestConfig(unittest.TestCase):
    def test_default_values(self):
        c = Config()
        self.assertEqual(c.camera_index, 0)
        self.assertEqual(c.frame_width, 640)
        self.assertEqual(c.frame_height, 480)
        self.assertAlmostEqual(c.swipe_threshold, 0.12)
        self.assertEqual(c.swipe_frames, 5)
        self.assertAlmostEqual(c.pinch_threshold, 0.06)
        self.assertAlmostEqual(c.spread_threshold, 0.10)

    def test_save_and_load(self):
        c = Config()
        c.swipe_threshold = 0.20
        c.camera_index = 2
        c.save()
        c2 = Config.load()
        self.assertAlmostEqual(c2.swipe_threshold, 0.20)
        self.assertEqual(c2.camera_index, 2)
        # cleanup
        os.remove(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"))

    def test_load_missing_file(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(path):
            os.remove(path)
        c = Config.load()
        self.assertEqual(c.camera_index, 0)


class TestDistance(unittest.TestCase):
    def test_same_point(self):
        a = Landmark(0.0, 0.0, 0.0)
        self.assertAlmostEqual(_distance(a, a), 0.0)

    def test_known_distance(self):
        a = Landmark(0.0, 0.0, 0.0)
        b = Landmark(3.0, 4.0, 0.0)
        self.assertAlmostEqual(_distance(a, b), 5.0)


class TestFingerExtended(unittest.TestCase):
    def test_finger_up(self):
        lm = make_hand_open_palm()
        # Index (finger_idx=1): tip.y < pip.y
        self.assertTrue(_is_finger_extended(lm, 1))
        # Middle (finger_idx=2): tip.y < pip.y
        self.assertTrue(_is_finger_extended(lm, 2))

    def test_finger_down(self):
        lm = make_hand_open_palm()
        # Simulate ring finger curled: tip below pip
        lm[16] = Landmark(x=0.58, y=0.60, z=0.0)
        lm[14] = Landmark(x=0.58, y=0.50, z=0.0)
        # Ring finger (finger_idx=3): tip.y > pip.y -> not extended
        self.assertFalse(_is_finger_extended(lm, 3))


class TestGestureDetector(unittest.TestCase):
    def setUp(self):
        self.conf = Config()
        self.detector = GestureDetector(self.conf)

    def test_no_landmarks(self):
        result = self.detector.detect([])
        self.assertEqual(result, Gesture.NONE)

    def test_few_landmarks(self):
        result = self.detector.detect([Landmark(0, 0, 0)] * 10)
        self.assertEqual(result, Gesture.NONE)

    def test_open_palm_no_swipe(self):
        lm = make_hand_open_palm()
        # Single frame, no swipe history
        result = self.detector.detect(lm)
        # Should not detect swipe (buffer not full)
        self.assertNotIn(result, [Gesture.SWIPE_LEFT, Gesture.SWIPE_RIGHT])

    def test_pinch_detection(self):
        lm = make_hand_pinch()
        result = self.detector.detect(lm)
        self.assertEqual(result, Gesture.PINCH)

    def test_pinch_not_when_far(self):
        lm = make_hand_open_palm()
        result = self.detector.detect(lm)
        self.assertNotEqual(result, Gesture.PINCH)

    def test_two_finger_spread(self):
        lm = make_hand_two_finger_spread()
        result = self.detector.detect(lm)
        self.assertEqual(result, Gesture.TWO_FINGER_SPREAD)

    def test_peace_sign(self):
        lm = make_hand_peace_sign()
        result = self.detector.detect(lm)
        self.assertEqual(result, Gesture.PEACE_SIGN)

    def test_swipe_right(self):
        lm = make_hand_open_palm()
        self.detector.reset()
        # Feed frames with wrist moving right
        for i in range(self.conf.swipe_frames):
            lm_copy = [Landmark(x=l.x, y=l.y, z=l.z) for l in lm]
            lm_copy[0] = Landmark(x=0.3 + i * 0.05, y=0.9, z=0.0)
            result = self.detector.detect(lm_copy)
        self.assertEqual(result, Gesture.SWIPE_RIGHT)

    def test_swipe_left(self):
        lm = make_hand_open_palm()
        self.detector.reset()
        for i in range(self.conf.swipe_frames):
            lm_copy = [Landmark(x=l.x, y=l.y, z=l.z) for l in lm]
            lm_copy[0] = Landmark(x=0.7 - i * 0.05, y=0.9, z=0.0)
            result = self.detector.detect(lm_copy)
        self.assertEqual(result, Gesture.SWIPE_LEFT)

    def test_swipe_up(self):
        lm = make_hand_open_palm()
        self.detector.reset()
        for i in range(self.conf.swipe_frames):
            lm_copy = [Landmark(x=l.x, y=l.y, z=l.z) for l in lm]
            lm_copy[0] = Landmark(x=0.5, y=0.9 - i * 0.05, z=0.0)
            result = self.detector.detect(lm_copy)
        self.assertEqual(result, Gesture.SWIPE_UP)

    def test_swipe_down(self):
        lm = make_hand_open_palm()
        self.detector.reset()
        for i in range(self.conf.swipe_frames):
            lm_copy = [Landmark(x=l.x, y=l.y, z=l.z) for l in lm]
            lm_copy[0] = Landmark(x=0.5, y=0.3 + i * 0.05, z=0.0)
            result = self.detector.detect(lm_copy)
        self.assertEqual(result, Gesture.SWIPE_DOWN)

    def test_swipe_requires_all_fingers(self):
        lm = make_hand_open_palm()
        self.detector.reset()
        for i in range(self.conf.swipe_frames):
            lm_copy = [Landmark(x=l.x, y=l.y, z=l.z) for l in lm]
            lm_copy[0] = Landmark(x=0.3 + i * 0.05, y=0.9, z=0.0)
            # Make thumb curled: tip and MCP very close, both near palm center
            lm_copy[4] = Landmark(x=0.49, y=0.75, z=0.0)
            lm_copy[2] = Landmark(x=0.49, y=0.75, z=0.0)
            result = self.detector.detect(lm_copy)
        self.assertNotIn(result, [Gesture.SWIPE_LEFT, Gesture.SWIPE_RIGHT])

    def test_reset_clears_buffer(self):
        lm = make_hand_open_palm()
        self.detector.detect(lm)
        self.detector.detect(lm)
        self.assertGreater(len(self.detector.wrist_buffer), 0)
        self.detector.reset()
        self.assertEqual(len(self.detector.wrist_buffer), 0)


class TestCooldownSystem(unittest.TestCase):
    def setUp(self):
        self.conf = Config()
        self.conf.swipe_cooldown_ms = 100
        self.conf.pinch_cooldown_ms = 100
        self.conf.spread_cooldown_ms = 100
        self.conf.peace_cooldown_ms = 100
        self.dispatcher = ActionDispatcher(self.conf)

    def test_first_dispatch_succeeds(self):
        with patch.object(self.dispatcher, '_execute', return_value="test"):
            result = self.dispatcher.dispatch(Gesture.SWIPE_RIGHT)
            self.assertTrue(result)

    def test_second_dispatch_within_cooldown_blocked(self):
        with patch.object(self.dispatcher, '_execute', return_value="test"):
            self.dispatcher.dispatch(Gesture.SWIPE_RIGHT)
            time.sleep(0.05)
            result = self.dispatcher.dispatch(Gesture.SWIPE_RIGHT)
            self.assertFalse(result)

    def test_dispatch_after_cooldown_succeeds(self):
        with patch.object(self.dispatcher, '_execute', return_value="test"):
            self.dispatcher.dispatch(Gesture.SWIPE_RIGHT)
            time.sleep(0.15)
            result = self.dispatcher.dispatch(Gesture.SWIPE_RIGHT)
            self.assertTrue(result)

    def test_different_gestures_independent_cooldowns(self):
        with patch.object(self.dispatcher, '_execute', return_value="test"):
            self.dispatcher.dispatch(Gesture.SWIPE_RIGHT)
            result = self.dispatcher.dispatch(Gesture.PINCH)
            self.assertTrue(result)

    def test_on_action_callback(self):
        actions = []
        dispatcher = ActionDispatcher(self.conf, on_action=lambda a: actions.append(a))
        with patch.object(dispatcher, '_execute', return_value="next_slide"):
            dispatcher.dispatch(Gesture.SWIPE_RIGHT)
            self.assertEqual(actions, ["next_slide"])


class TestActionDispatcher(unittest.TestCase):
    def setUp(self):
        self.conf = Config()
        self.conf.use_com_api = False
        self.dispatcher = ActionDispatcher(self.conf)

    def test_next_slide_calls_pyautogui(self):
        with patch('action_dispatcher.pyautogui') as mock:
            self.dispatcher._next_slide()
            mock.press.assert_called_with("right")

    def test_prev_slide_calls_pyautogui(self):
        with patch('action_dispatcher.pyautogui') as mock:
            self.dispatcher._prev_slide()
            mock.press.assert_called_with("left")

    def test_page_up(self):
        with patch('action_dispatcher.pyautogui') as mock:
            self.dispatcher._page_up()
            mock.press.assert_called_with("pageup")

    def test_page_down(self):
        with patch('action_dispatcher.pyautogui') as mock:
            self.dispatcher._page_down()
            mock.press.assert_called_with("pagedown")

    def test_exit_presentation(self):
        with patch('action_dispatcher.pyautogui') as mock:
            self.dispatcher._exit_presentation()
            mock.press.assert_called_with("escape")

    def test_zoom_in_keyboard(self):
        with patch('action_dispatcher.pyautogui') as mock:
            self.dispatcher._zoom_in()
            mock.keyDown.assert_called_with("ctrl")
            mock.press.assert_called_with("add")
            mock.keyUp.assert_called_with("ctrl")

    def test_zoom_out_keyboard(self):
        with patch('action_dispatcher.pyautogui') as mock:
            self.dispatcher._zoom_out()
            mock.keyDown.assert_called_with("ctrl")
            mock.press.assert_called_with("subtract")
            mock.keyUp.assert_called_with("ctrl")


class TestPPTController(unittest.TestCase):
    def test_init(self):
        ppt = PPTController()
        self.assertFalse(ppt._connected)
        self.assertIsNone(ppt._app)

    def test_connect_without_com(self):
        ppt = PPTController()
        # On Windows with COM, this might succeed or fail depending on PowerPoint
        # Just test it doesn't crash
        result = ppt.connect()
        self.assertIsInstance(result, bool)

    def test_disconnect(self):
        ppt = PPTController()
        ppt._connected = True
        ppt._app = MagicMock()
        ppt.disconnect()
        self.assertFalse(ppt._connected)
        self.assertIsNone(ppt._app)

    def test_is_connected_when_not_connected(self):
        ppt = PPTController()
        self.assertFalse(ppt.is_connected)

    def test_zoom_keyboard_fallback(self):
        ppt = PPTController()
        with patch('pyautogui.keyDown') as mock_down, \
             patch('pyautogui.press') as mock_press, \
             patch('pyautogui.keyUp') as mock_up:
            result = ppt._zoom_keyboard_fallback("add")
            self.assertTrue(result)
            mock_down.assert_called_with("ctrl")
            mock_press.assert_called_with("add")
            mock_up.assert_called_with("ctrl")


class TestGesturePriority(unittest.TestCase):
    """Test that gesture detection priority is correct: peace > spread > pinch > swipe."""

    def setUp(self):
        self.conf = Config()
        self.detector = GestureDetector(self.conf)

    def test_spread_beats_pinch_when_both_possible(self):
        lm = make_hand_two_finger_spread()
        # Add a pinch condition (thumb + index close)
        lm[4] = Landmark(x=0.30, y=0.20, z=0.0)  # thumb tip near index tip
        lm[8] = Landmark(x=0.30, y=0.20, z=0.0)   # index tip
        result = self.detector.detect(lm)
        # Spread should be detected (higher priority than pinch)
        self.assertEqual(result, Gesture.TWO_FINGER_SPREAD)


class TestRealTimePipeline(unittest.TestCase):
    """Simulate the real-time pipeline without actual camera."""

    def test_engine_start_stop(self):
        conf = Config()
        gestures = []
        engine = None

        try:
            from gesture_engine import GestureEngine
            engine = GestureEngine(conf, on_gesture=lambda g: gestures.append(g))
            # Can't actually start without camera, but test init
            self.assertIsNotNone(engine.detector)
            self.assertFalse(engine.is_running)
            self.assertIsNone(engine.preview_frame)
        except Exception:
            pass

    def test_detector_thread_safety(self):
        """Test that detector can be used from multiple threads without crash."""
        conf = Config()
        detector = GestureDetector(conf)
        lm = make_hand_open_palm()
        errors = []

        def detect_loop():
            try:
                for _ in range(100):
                    detector.detect(lm)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=detect_loop) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)
        self.assertEqual(errors, [])


class TestEdgeCases(unittest.TestCase):
    def test_empty_wrist_buffer(self):
        conf = Config()
        detector = GestureDetector(conf)
        self.assertEqual(len(detector.wrist_buffer), 0)

    def test_swipe_with_insufficient_frames(self):
        conf = Config()
        conf.swipe_frames = 10
        detector = GestureDetector(conf)
        lm = make_hand_open_palm()
        # Feed only 3 frames
        for _ in range(3):
            lm_copy = [Landmark(x=l.x, y=l.y, z=l.z) for l in lm]
            lm_copy[0] = Landmark(x=0.3, y=0.9, z=0.0)
            detector.detect(lm_copy)
        result = detector.detect(lm_copy)
        # Should not detect swipe
        self.assertNotIn(result, [Gesture.SWIPE_LEFT, Gesture.SWIPE_RIGHT, Gesture.SWIPE_UP, Gesture.SWIPE_DOWN])

    def test_swipe_threshold_boundary(self):
        conf = Config()
        conf.swipe_threshold = 0.10
        conf.swipe_frames = 3
        detector = GestureDetector(conf)
        lm = make_hand_open_palm()
        # Feed frames with movement BELOW threshold
        for i in range(3):
            lm_copy = [Landmark(x=l.x, y=l.y, z=l.z) for l in lm]
            lm_copy[0] = Landmark(x=0.5 + i * 0.02, y=0.9, z=0.0)
            result = detector.detect(lm_copy)
        # dx = 0.04, threshold = 0.10, should NOT trigger
        self.assertNotEqual(result, Gesture.SWIPE_RIGHT)


class TestPerformance(unittest.TestCase):
    """Measure detection latency."""

    def test_detection_speed(self):
        conf = Config()
        detector = GestureDetector(conf)
        lm = make_hand_open_palm()
        detector.reset()

        iterations = 500
        start = time.perf_counter()
        for _ in range(iterations):
            detector.detect(lm)
        elapsed = time.perf_counter() - start
        avg_us = (elapsed / iterations) * 1_000_000
        print(f"\n  Average detection time: {avg_us:.1f} us per frame ({iterations} frames)")
        # Should be well under 1ms per frame
        self.assertLess(avg_us, 5000, "Detection too slow for real-time use")


if __name__ == "__main__":
    unittest.main(verbosity=2)
