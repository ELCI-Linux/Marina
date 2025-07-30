"""
Utility functions for DAMD operations.
"""

import hashlib
import time
from typing import Any, Dict

import zstandard as zstd


def compress_data(data: bytes, level: int = 3) -> bytes:
    """Compress data using Zstandard."""
    compressor = zstd.ZstdCompressor(level=level)
    return compressor.compress(data)


def decompress_data(data: bytes) -> bytes:
    """Decompress Zstandard compressed data."""
    decompressor = zstd.ZstdDecompressor()
    return decompressor.decompress(data)


def calculate_checksum(data: bytes) -> str:
    """Calculate SHA-256 checksum of data."""
    return hashlib.sha256(data).hexdigest()


def get_timestamp() -> float:
    """Get current timestamp."""
    return time.time()


def format_size(size_bytes: int) -> str:
    """Format byte size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def validate_key(key: str) -> bool:
    """Validate DAMD segment key."""
    if not key:
        return False
    
    # Keys should be alphanumeric with underscores, hyphens, and dots
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
    return all(c in allowed_chars for c in key)


def detect_content_type(data: bytes, filename: str = "") -> str:
    """Detect content type from data and filename."""
    # Simple content type detection
    if filename:
        ext = filename.lower().split('.')[-1] if '.' in filename else ""
        content_types = {
            'txt': 'text/plain',
            'json': 'application/json',
            'xml': 'application/xml',
            'html': 'text/html',
            'css': 'text/css',
            'js': 'application/javascript',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'pdf': 'application/pdf',
            'zip': 'application/zip',
        }
        if ext in content_types:
            return content_types[ext]
    
    # Check data headers
    if data.startswith(b'\x89PNG'):
        return 'image/png'
    elif data.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
        return 'image/gif'
    elif data.startswith(b'RIFF') and b'WEBP' in data[:20]:
        return 'image/webp'
    elif data.startswith(b'%PDF'):
        return 'application/pdf'
    elif data.startswith(b'PK'):
        return 'application/zip'
    
    # Try to decode as text
    try:
        data.decode('utf-8')
        return 'text/plain'
    except UnicodeDecodeError:
        pass
    
    return 'application/octet-stream'
