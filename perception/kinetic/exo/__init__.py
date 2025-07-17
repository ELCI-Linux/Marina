"""
Exo (External) Kinetic Perception Engine
======================================

This module provides external kinetic perception capabilities for the Marina system.
It focuses on detecting and analyzing movement and kinetic patterns in the external environment.
"""

from .external_kinetic_engine import ExternalKineticEngine
from .motion_detector import MotionDetector
from .environmental_tracker import EnvironmentalTracker

__all__ = [
    'ExternalKineticEngine',
    'MotionDetector',
    'EnvironmentalTracker'
]

__version__ = '1.0.0'
