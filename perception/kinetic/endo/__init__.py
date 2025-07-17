"""
Endo (Internal) Kinetic Perception Engine
========================================

This module provides internal kinetic perception capabilities for the Marina system.
It focuses on self-monitoring, internal state tracking, and proprioceptive awareness.
"""

from .internal_kinetic_engine import InternalKineticEngine
from .proprioceptive_monitor import ProprioceptiveMonitor
from .system_state_tracker import SystemStateTracker

__all__ = [
    'InternalKineticEngine',
    'ProprioceptiveMonitor', 
    'SystemStateTracker'
]

__version__ = '1.0.0'
