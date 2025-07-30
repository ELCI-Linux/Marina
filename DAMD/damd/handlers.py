"""
File type handlers for specialized DAMD operations.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from PIL import Image

from .core import DAMDFile
from .utils import detect_content_type, get_timestamp


class DAMDHandler(ABC):
    """Base class for DAMD file handlers."""
    
    @abstractmethod
    def can_handle(self, filepath: Path) -> bool:
        """Check if this handler can process the given file."""
        pass
    
    @abstractmethod
    def extract_metadata(self, filepath: Path) -> Dict[str, Any]:
        """Extract metadata from the file."""
        pass
    
    def process_file(self, filepath: Path, damd_file: DAMDFile) -> None:
        """Process file and add metadata to DAMD file."""
        metadata = self.extract_metadata(filepath)
        
        # Add extracted metadata
        for key, value in metadata.items():
            if isinstance(value, (str, bytes)):
                content_type = detect_content_type(
                    value.encode() if isinstance(value, str) else value,
                    f"{key}.data"
                )
                damd_file.add_segment(
                    key=key,
                    data=value,
                    content_type=content_type,
                    metadata={"extracted_at": get_timestamp()}
                )


class ImageHandler(DAMDHandler):
    """Handler for image files."""
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    
    def can_handle(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def extract_metadata(self, filepath: Path) -> Dict[str, Any]:
        metadata = {}
        
        try:
            with Image.open(filepath) as img:
                # Basic image info
                info = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                }
                metadata["image_info"] = json.dumps(info)
                
                # EXIF data
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = img._getexif()
                    if exif_data:
                        # Convert to string representation
                        exif_str = json.dumps({str(k): str(v) for k, v in exif_data.items()})
                        metadata["exif_data"] = exif_str
                
                # Create thumbnail
                thumbnail_size = (128, 128)
                thumbnail = img.copy()
                thumbnail.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                
                # Save thumbnail as bytes
                import io
                thumb_buffer = io.BytesIO()
                thumbnail.save(thumb_buffer, format='JPEG', quality=85)
                metadata["thumbnail"] = thumb_buffer.getvalue()
                
        except Exception as e:
            metadata["extraction_error"] = str(e)
        
        return metadata


class TextHandler(DAMDHandler):
    """Handler for text files."""
    
    SUPPORTED_EXTENSIONS = {'.txt', '.md', '.rst', '.log', '.csv', '.json', '.xml', '.html'}
    
    def can_handle(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def extract_metadata(self, filepath: Path) -> Dict[str, Any]:
        metadata = {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Basic text statistics
                lines = content.split('\n')
                words = content.split()
                
                stats = {
                    "line_count": len(lines),
                    "word_count": len(words),
                    "char_count": len(content),
                    "encoding": "utf-8"
                }
                metadata["text_stats"] = json.dumps(stats)
                
                # First few lines as summary
                summary_lines = lines[:5]
                metadata["summary"] = '\n'.join(summary_lines)
                
                # For JSON files, validate and extract structure
                if filepath.suffix.lower() == '.json':
                    try:
                        parsed_json = json.loads(content)
                        schema_info = {
                            "type": type(parsed_json).__name__,
                            "keys": list(parsed_json.keys()) if isinstance(parsed_json, dict) else None,
                            "length": len(parsed_json) if isinstance(parsed_json, (list, dict)) else None
                        }
                        metadata["json_schema"] = json.dumps(schema_info)
                    except json.JSONDecodeError as e:
                        metadata["json_error"] = str(e)
                
        except Exception as e:
            metadata["extraction_error"] = str(e)
        
        return metadata


class AudioHandler(DAMDHandler):
    """Handler for audio files."""
    
    SUPPORTED_EXTENSIONS = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}
    
    def can_handle(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def extract_metadata(self, filepath: Path) -> Dict[str, Any]:
        metadata = {}
        
        try:
            # Try to use mutagen for audio metadata (if available)
            try:
                from mutagen import File as MutagenFile
                audio_file = MutagenFile(filepath)
                
                if audio_file:
                    # Extract basic tags
                    tags = {}
                    for key, value in audio_file.items():
                        if isinstance(value, list) and len(value) == 1:
                            value = value[0]
                        tags[key] = str(value)
                    
                    metadata["audio_tags"] = json.dumps(tags)
                    
                    # Audio properties
                    if hasattr(audio_file, 'info'):
                        info = audio_file.info
                        properties = {
                            "length": getattr(info, 'length', 0),
                            "bitrate": getattr(info, 'bitrate', 0),
                            "sample_rate": getattr(info, 'sample_rate', 0),
                            "channels": getattr(info, 'channels', 0),
                        }
                        metadata["audio_properties"] = json.dumps(properties)
                        
            except ImportError:
                metadata["extraction_note"] = "mutagen not available, basic metadata only"
                
        except Exception as e:
            metadata["extraction_error"] = str(e)
        
        return metadata


class VideoHandler(DAMDHandler):
    """Handler for video files."""
    
    SUPPORTED_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.webm', '.mov', '.wmv'}
    
    def can_handle(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def extract_metadata(self, filepath: Path) -> Dict[str, Any]:
        metadata = {}
        
        try:
            # Basic file info
            file_stat = filepath.stat()
            basic_info = {
                "file_size": file_stat.st_size,
                "created": file_stat.st_ctime,
                "modified": file_stat.st_mtime,
            }
            metadata["file_info"] = json.dumps(basic_info)
            
            # Placeholder for video-specific metadata
            # In a real implementation, you'd use ffprobe or similar
            metadata["video_note"] = "Advanced video metadata extraction requires ffmpeg/ffprobe"
            
        except Exception as e:
            metadata["extraction_error"] = str(e)
        
        return metadata


# Handler registry
_handlers: List[Type[DAMDHandler]] = [
    ImageHandler,
    TextHandler,
    AudioHandler,
    VideoHandler,
]


def register_handler(handler_class: Type[DAMDHandler]) -> None:
    """Register a new DAMD handler."""
    if handler_class not in _handlers:
        _handlers.append(handler_class)


def get_handler(filepath: Path) -> Optional[DAMDHandler]:
    """Get appropriate handler for a file."""
    for handler_class in _handlers:
        handler = handler_class()
        if handler.can_handle(filepath):
            return handler
    return None


def list_handlers() -> List[str]:
    """List all registered handlers."""
    return [handler.__name__ for handler in _handlers]
