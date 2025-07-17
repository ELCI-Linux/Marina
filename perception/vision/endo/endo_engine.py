# endo_engine.py
"""
Internal observation engine for analyzing documents and on-screen content.
"""

import cv2
import time
import threading
import numpy as np
from typing import Optional, Dict, Any, List
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from observation_engine import ObservationEngine, ObservationType, ObservationResult, ImageAnalyzer

try:
    import pyautogui
    import pytesseract
    SCREEN_CAPTURE_AVAILABLE = True
except ImportError:
    SCREEN_CAPTURE_AVAILABLE = False
    print("Warning: pyautogui or pytesseract not available. Screen capture will be mocked.")


class InternalObservationEngine(ObservationEngine):
    def __init__(self):
        super().__init__(name="InternalObservation", observation_type=ObservationType.INTERNAL)
        self._capture_thread = None

    def start_observation(self):
        if not self.is_running:
            self.is_running = True
            self._capture_thread = threading.Thread(target=self._run)
            self._capture_thread.start()

    def stop_observation(self):
        if self.is_running:
            self.is_running = False
            if self._capture_thread:
                self._capture_thread.join()

    def _run(self):
        while self.is_running:
            # Capture the screen (mocked here with a sample screenshot)
            screenshot = np.random.randint(0, 255, (500, 500, 3), dtype=np.uint8)
            observation_result = self._analyze_screenshot(screenshot)

            # Notify all callbacks
            self._notify_callbacks(observation_result)

            # Simulate a delay for capturing
            time.sleep(1)

    def _analyze_screenshot(self, screenshot: np.ndarray) -> ObservationResult:
        # Analyze the image
        objects = ImageAnalyzer.detect_objects(screenshot)
        text_regions = ImageAnalyzer.analyze_text_regions(screenshot)
        features = ImageAnalyzer.calculate_image_features(screenshot)

        # Construct result
        result = ObservationResult(
            timestamp=time.time(),
            observation_type=ObservationType.INTERNAL,
            source="internal_screenshot",
            confidence=0.85,  # Mocked confidence
            data={
                'objects': objects,
                'text_regions': text_regions,
                'features': features
            },
            metadata={
                'resolution': screenshot.shape
            }
        )
        return result

    def get_current_observation(self) -> Optional[ObservationResult]:
        # For simplicity, return None (a real implementation might return current state)
        return None
