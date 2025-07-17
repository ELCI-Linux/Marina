# somatosensation_engine.py
"""
Somatosensation Engine for Marina's perception of being touched.
This engine simulates tactile sensations through different input methods
and provides an API for tactile perception processing.
"""

import numpy as np
import time
import logging
from typing import Dict, List, Tuple, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
import threading


class TouchType(Enum):
    CONTACT = "contact"
    PRESSURE = "pressure"
    VIBRATION = "vibration"
    TEMPERATURE = "temperature"


@dataclass
class TouchEvent:
    """Represents a touch event."""
    timestamp: float
    position: Tuple[int, int]  # (x, y) coordinates
    touch_type: TouchType
    intensity: float           # 0.0 (no sensation) to 1.0 (maximum sensation)
    metadata: Dict[str, any] = field(default_factory=dict)


class SomatosensationEngine:
    """Main somatosensation engine for processing touch events."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.callbacks: List[Callable[[TouchEvent], None]] = []
        self.sensitivity_map = self._initialize_sensitivity_map()
        self.is_running = False

    def _initialize_sensitivity_map(self) -> np.ndarray:
        """
        Initialize a simple sensitivity map for tactile perception.
        Assume a 100x100 grid with varying sensitivity across different regions.
        """
        sensitivity = np.random.rand(100, 100)
        return sensitivity

    def add_callback(self, callback: Callable[[TouchEvent], None]):
        """Add a callback to be triggered on touch events."""
        self.callbacks.append(callback)

    def simulate_touch(self, position: Tuple[int, int], touch_type: TouchType, duration: float, intensity: float):
        """Simulate a touch event manually."""
        if not (0 <= position[0] < 100) or not (0 <= position[1] < 100):
            self.logger.error(f"Position {position} out of bounds!")
            return

        base_intensity = intensity * self.sensitivity_map[position[0], position[1]]
        event = TouchEvent(
            timestamp=time.time(),
            position=position,
            touch_type=touch_type,
            intensity=base_intensity,
            metadata={
                'duration': duration
            }
        )
        self._process_event(event)

    def start_monitoring(self):
        """Start the tactile monitoring process."""
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self._monitor_touch_inputs).start()

    def stop_monitoring(self):
        """Stop the tactile monitoring process."""
        self.is_running = False

    def _monitor_touch_inputs(self):
        """Mocked function to simulate live touch inputs in the tactile sensing grid."""
        while self.is_running:
            # Simulate random touch inputs at random positions
            x, y = np.random.randint(0, 100, size=2)
            touch_type = np.random.choice(list(TouchType))
            intensity = np.random.rand()
            duration = np.random.uniform(0.1, 1.0)
            self.simulate_touch((x, y), touch_type, duration, intensity)
            time.sleep(np.random.uniform(0.1, 2.0))  # delay between events

    def _process_event(self, event: TouchEvent):
        """Process a touch event and trigger callbacks."""
        self.logger.info(f"Processing touch event at {event.position} with intensity {event.intensity:.2f}")
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in callback: {e}")


# Example implementation callback
if __name__ == "__main__":
    def example_callback(event: TouchEvent):
        print(f"Detected {event.touch_type.value} at {event.position} with intensity {event.intensity:.2f}")

    engine = SomatosensationEngine()
    engine.add_callback(example_callback)
    engine.start_monitoring()

    # Run for a short time to demonstrate
    try:
        time.sleep(10)
    finally:
        engine.stop_monitoring()

