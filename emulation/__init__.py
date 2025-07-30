"""
Marina Emulation Framework
=========================

A comprehensive emulation system for simulating various devices, operating systems,
and hardware components for testing and development purposes.

Components:
- Device Emulation (Mobile, Desktop, IoT)
- OS Environment Emulation (Android, iOS, Windows, macOS, Linux)
- Hardware Abstraction Layer
- Network Interface Emulation
- Sensor Emulation
- Audio/Video Processing Emulation
"""

__version__ = "1.0.0"
__author__ = "Marina Development Team"

from .core import EmulationEngine
from .devices import DeviceEmulator
from .os_environments import OSEnvironmentManager
from .hardware import HardwareAbstractionLayer
from .network import NetworkEmulator
from .sensors import SensorEmulator

__all__ = [
    'EmulationEngine',
    'DeviceEmulator', 
    'OSEnvironmentManager',
    'HardwareAbstractionLayer',
    'NetworkEmulator',
    'SensorEmulator'
]
