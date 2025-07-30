#!/usr/bin/env python3
"""
STAVE - Semantic Temporal Audio Vector Engine
Don't record the world. Record the change.
"""

__version__ = "0.1.0-luthier"
__author__ = "Marina AI"
__description__ = "ContinuumDelta-native Digital Audio Workstation"

# Core imports
try:
    from .delta.delta_spec import Delta, DeltaLibrary, DeltaValidator
    from .delta.delta_stack import DeltaStack
    from .core.audio_asset import AudioAsset, AudioAssetManager
    
    __all__ = [
        'Delta',
        'DeltaLibrary', 
        'DeltaValidator',
        'DeltaStack',
        'AudioAsset',
        'AudioAssetManager'
    ]
    
except ImportError as e:
    print(f"[STAVE] Warning: Could not import all modules: {e}")
    __all__ = []
