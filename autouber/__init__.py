"""
Marina Auto-Uber Module
Smart rideshare automation with location-based triggers
"""

from .auto_uber_daemon import AutoUberDaemon
from .uber_client import UberClient
from .location_monitor import LocationMonitor
from .scheduler import UberScheduler

__version__ = "1.0.0"
__author__ = "Marina AI System"

__all__ = [
    'AutoUberDaemon',
    'UberClient', 
    'LocationMonitor',
    'UberScheduler'
]
