#!/usr/bin/env python3
"""
STAVE Core Module
Audio asset management and processing.
"""

from .audio_asset import (
    AudioAsset,
    AudioAssetManager,
    AudioMetadata
)

__all__ = [
    'AudioAsset',
    'AudioAssetManager',
    'AudioMetadata'
]
