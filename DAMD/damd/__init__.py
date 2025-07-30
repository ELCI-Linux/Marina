"""
DAMD - Data As Metadata in Data

A library for embedding small related data within larger host files,
enabling ultra-fast access and reducing file count.
"""

from .core import DAMDFile, DAMDError, DAMDSegment
from .handlers import register_handler, get_handler, list_handlers
from .utils import compress_data, decompress_data, calculate_checksum

__version__ = "0.1.0"
__all__ = [
    "DAMDFile",
    "DAMDError", 
    "DAMDSegment",
    "register_handler",
    "get_handler",
    "list_handlers",
    "compress_data",
    "decompress_data",
    "calculate_checksum",
]
