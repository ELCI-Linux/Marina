"""
Marina Sonic Perception Module
Advanced audio processing and analysis capabilities
"""

from .audio_processor import AudioProcessor
from .frequency_analyzer import FrequencyAnalyzer
from .sound_classifier import SoundClassifier
from .spatial_audio import SpatialAudioProcessor
from .vocal_analysis import VocalAnalyzer
from . import exo
# from .environmental_audio import EnvironmentalAudioMonitor
# from .audio_signature import AudioSignatureEngine
# from .realtime_analyzer import RealtimeAudioAnalyzer

__version__ = "1.0.0"
__author__ = "Marina AI Framework"

# Core sonic perception components
SONIC_MODULES = {
    'processor': AudioProcessor,
    'frequency': FrequencyAnalyzer,
    'classifier': SoundClassifier,
    'spatial': SpatialAudioProcessor,
    'vocal': VocalAnalyzer,
    # 'environmental': EnvironmentalAudioMonitor,
    # 'signature': AudioSignatureEngine,
    # 'realtime': RealtimeAudioAnalyzer
}

def initialize_sonic_perception():
    """Initialize all sonic perception modules"""
    return {name: module() for name, module in SONIC_MODULES.items()}
