#!/usr/bin/env python3
"""
STAVE Audio Asset Management
Handles base audio files with metadata, lazy loading, and hash-based identity.
"""

import os
import time
import hashlib
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from pathlib import Path
import json

# Audio processing imports
try:
    import soundfile as sf
    import librosa
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    print("[AUDIO_ASSET] Warning: soundfile and/or librosa not available")
    AUDIO_LIBS_AVAILABLE = False

@dataclass
class AudioMetadata:
    """Metadata for audio assets"""
    filename: str
    file_size: int
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int
    format: str
    created: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    tags: Dict[str, Any] = field(default_factory=dict)
    
    def add_tag(self, key: str, value: Any):
        """Add metadata tag"""
        self.tags[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "filename": self.filename,
            "file_size": self.file_size,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "bit_depth": self.bit_depth,
            "format": self.format,
            "created": self.created,
            "tags": self.tags
        }

class AudioAsset:
    """
    Represents a base audio file with lazy loading and delta compatibility.
    
    This is the foundation of STAVE's delta system - all deltas reference
    these base assets by their content hash.
    """
    
    def __init__(self, filepath: str, load_on_init: bool = False):
        self.filepath = Path(filepath).resolve()
        self.asset_id = ""
        self.content_hash = ""
        self.metadata: Optional[AudioMetadata] = None
        self.audio_data: Optional[np.ndarray] = None
        self.loaded = False
        self.cache_enabled = True
        
        # Validate file exists
        if not self.filepath.exists():
            raise FileNotFoundError(f"Audio file not found: {filepath}")
        
        # Initialize metadata and hash
        self._initialize_metadata()
        self._compute_content_hash()
        
        # Generate asset ID from hash
        self.asset_id = f"asset_{self.content_hash[:12]}"
        
        if load_on_init:
            self.load_audio()
        
        print(f"[AUDIO_ASSET] Created asset {self.asset_id} for {self.filepath.name}")
    
    def _initialize_metadata(self):
        """Initialize audio metadata without loading full audio data"""
        if not AUDIO_LIBS_AVAILABLE:
            # Fallback metadata
            stat = self.filepath.stat()
            self.metadata = AudioMetadata(
                filename=self.filepath.name,
                file_size=stat.st_size,
                duration=0.0,
                sample_rate=44100,  # Assumed
                channels=2,         # Assumed
                bit_depth=16,       # Assumed
                format=self.filepath.suffix.lower()
            )
            return
        
        try:
            info = sf.info(str(self.filepath))
            stat = self.filepath.stat()
            
            self.metadata = AudioMetadata(
                filename=self.filepath.name,
                file_size=stat.st_size,
                duration=info.duration,
                sample_rate=info.samplerate,
                channels=info.channels,
                bit_depth=info.subtype_info.bits_per_sample if hasattr(info, 'subtype_info') else 16,
                format=info.format_info.name if hasattr(info, 'format_info') else self.filepath.suffix
            )
            
            # Add file system metadata
            self.metadata.add_tag("file_created", time.ctime(stat.st_ctime))
            self.metadata.add_tag("file_modified", time.ctime(stat.st_mtime))
            
        except Exception as e:
            print(f"[AUDIO_ASSET] Warning: Could not read metadata for {self.filepath}: {e}")
            # Fallback to basic metadata
            stat = self.filepath.stat()
            self.metadata = AudioMetadata(
                filename=self.filepath.name,
                file_size=stat.st_size,
                duration=0.0,
                sample_rate=44100,
                channels=2,
                bit_depth=16,
                format=self.filepath.suffix.lower()
            )
    
    def _compute_content_hash(self):
        """Compute hash of audio file content"""
        try:
            hash_obj = hashlib.md5()
            
            # Hash file content in chunks to handle large files
            with open(self.filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            
            self.content_hash = hash_obj.hexdigest()
            
        except Exception as e:
            print(f"[AUDIO_ASSET] Error computing hash for {self.filepath}: {e}")
            # Fallback hash based on file path and size
            fallback_content = f"{self.filepath.name}_{self.metadata.file_size}"
            self.content_hash = hashlib.md5(fallback_content.encode()).hexdigest()
    
    def load_audio(self, force_reload: bool = False) -> bool:
        """Load audio data into memory"""
        if self.loaded and not force_reload:
            return True
        
        if not AUDIO_LIBS_AVAILABLE:
            print("[AUDIO_ASSET] Cannot load audio: audio libraries not available")
            return False
        
        try:
            print(f"[AUDIO_ASSET] Loading audio data for {self.asset_id}")
            
            # Load audio with librosa for consistency
            self.audio_data, actual_sr = librosa.load(
                str(self.filepath), 
                sr=None,  # Keep original sample rate
                mono=False  # Keep original channel configuration
            )
            
            # Ensure 2D array (channels, samples)
            if self.audio_data.ndim == 1:
                self.audio_data = self.audio_data.reshape(1, -1)
            
            # Update metadata with actual values
            if actual_sr != self.metadata.sample_rate:
                print(f"[AUDIO_ASSET] Sample rate mismatch: expected {self.metadata.sample_rate}, got {actual_sr}")
                self.metadata.sample_rate = actual_sr
            
            self.loaded = True
            print(f"[AUDIO_ASSET] Loaded {self.audio_data.shape} audio array")
            return True
            
        except Exception as e:
            print(f"[AUDIO_ASSET] Error loading audio for {self.filepath}: {e}")
            return False
    
    def unload_audio(self):
        """Free audio data from memory"""
        if self.loaded:
            self.audio_data = None
            self.loaded = False
            print(f"[AUDIO_ASSET] Unloaded audio data for {self.asset_id}")
    
    def get_audio_data(self, ensure_loaded: bool = True) -> Optional[np.ndarray]:
        """Get audio data, optionally ensuring it's loaded"""
        if ensure_loaded and not self.loaded:
            if not self.load_audio():
                return None
        
        return self.audio_data
    
    def get_audio_segment(self, start_time: float, end_time: float) -> Optional[np.ndarray]:
        """Get a segment of audio data by time"""
        if not self.loaded:
            if not self.load_audio():
                return None
        
        if not self.metadata:
            return None
        
        # Convert time to samples
        start_sample = int(start_time * self.metadata.sample_rate)
        end_sample = int(end_time * self.metadata.sample_rate)
        
        # Validate range
        if start_sample < 0 or end_sample > self.audio_data.shape[1]:
            print(f"[AUDIO_ASSET] Invalid time range: {start_time:.3f}s - {end_time:.3f}s")
            return None
        
        return self.audio_data[:, start_sample:end_sample]
    
    def get_channel_data(self, channel: int = 0) -> Optional[np.ndarray]:
        """Get data for a specific audio channel"""
        if not self.loaded:
            if not self.load_audio():
                return None
        
        if channel >= self.audio_data.shape[0]:
            print(f"[AUDIO_ASSET] Invalid channel: {channel} (available: {self.audio_data.shape[0]})")
            return None
        
        return self.audio_data[channel, :]
    
    def analyze_audio(self) -> Dict[str, Any]:
        """Perform basic audio analysis"""
        if not self.loaded:
            if not self.load_audio():
                return {}
        
        if not AUDIO_LIBS_AVAILABLE:
            return {"status": "analysis_unavailable"}
        
        try:
            # Get mono version for analysis
            mono_audio = librosa.to_mono(self.audio_data)
            
            # Basic analysis
            analysis = {
                "rms_energy": float(np.sqrt(np.mean(mono_audio ** 2))),
                "peak_amplitude": float(np.max(np.abs(mono_audio))),
                "zero_crossing_rate": float(np.mean(librosa.feature.zero_crossing_rate(mono_audio))),
                "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(y=mono_audio, sr=self.metadata.sample_rate))),
                "dynamic_range": float(np.max(mono_audio) - np.min(mono_audio))
            }
            
            # Tempo estimation
            try:
                tempo, _ = librosa.beat.beat_track(y=mono_audio, sr=self.metadata.sample_rate)
                analysis["estimated_tempo"] = float(tempo)
            except:
                analysis["estimated_tempo"] = None
            
            # Pitch estimation (simplified)
            try:
                pitches, magnitudes = librosa.piptrack(y=mono_audio, sr=self.metadata.sample_rate)
                pitch_values = pitches[magnitudes > np.percentile(magnitudes, 85)]
                if len(pitch_values) > 0:
                    analysis["average_pitch"] = float(np.mean(pitch_values))
                else:
                    analysis["average_pitch"] = None
            except:
                analysis["average_pitch"] = None
            
            return analysis
            
        except Exception as e:
            print(f"[AUDIO_ASSET] Error analyzing audio: {e}")
            return {"status": "analysis_failed", "error": str(e)}
    
    def export_audio(self, output_path: str, format: str = "wav", 
                    sample_rate: Optional[int] = None) -> bool:
        """Export audio data to file"""
        if not self.loaded:
            if not self.load_audio():
                return False
        
        if not AUDIO_LIBS_AVAILABLE:
            print("[AUDIO_ASSET] Cannot export: audio libraries not available")
            return False
        
        try:
            export_sr = sample_rate or self.metadata.sample_rate
            export_data = self.audio_data
            
            # Convert to librosa format (samples, channels) if needed
            if export_data.shape[0] <= 2:  # Assume channels-first
                export_data = export_data.T
            
            sf.write(output_path, export_data, export_sr, format=format)
            print(f"[AUDIO_ASSET] Exported to {output_path}")
            return True
            
        except Exception as e:
            print(f"[AUDIO_ASSET] Export failed: {e}")
            return False
    
    def create_backup(self, backup_dir: str) -> bool:
        """Create a backup of the original audio file"""
        try:
            backup_path = Path(backup_dir) / f"{self.asset_id}_{self.filepath.name}"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy original file
            import shutil
            shutil.copy2(self.filepath, backup_path)
            
            # Save metadata
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump({
                    "asset_id": self.asset_id,
                    "content_hash": self.content_hash,
                    "original_path": str(self.filepath),
                    "metadata": self.metadata.to_dict(),
                    "backup_created": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                }, f, indent=2)
            
            print(f"[AUDIO_ASSET] Created backup: {backup_path}")
            return True
            
        except Exception as e:
            print(f"[AUDIO_ASSET] Backup failed: {e}")
            return False
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information"""
        usage = {
            "loaded": self.loaded,
            "audio_data_size": 0,
            "metadata_size": 0
        }
        
        if self.loaded and self.audio_data is not None:
            usage["audio_data_size"] = self.audio_data.nbytes
        
        if self.metadata:
            # Rough estimate of metadata size
            metadata_str = json.dumps(self.metadata.to_dict())
            usage["metadata_size"] = len(metadata_str.encode('utf-8'))
        
        usage["total_size"] = usage["audio_data_size"] + usage["metadata_size"]
        return usage
    
    def validate_integrity(self) -> bool:
        """Validate asset integrity by checking file and hash"""
        if not self.filepath.exists():
            print(f"[AUDIO_ASSET] Integrity check failed: file missing")
            return False
        
        # Recompute hash and compare
        old_hash = self.content_hash
        self._compute_content_hash()
        
        if self.content_hash != old_hash:
            print(f"[AUDIO_ASSET] Integrity check failed: hash mismatch")
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize asset information to dictionary"""
        return {
            "asset_id": self.asset_id,
            "filepath": str(self.filepath),
            "content_hash": self.content_hash,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "loaded": self.loaded,
            "cache_enabled": self.cache_enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioAsset':
        """Create asset from dictionary (for serialization)"""
        asset = cls(data["filepath"], load_on_init=False)
        asset.cache_enabled = data.get("cache_enabled", True)
        return asset
    
    def __str__(self) -> str:
        status = "loaded" if self.loaded else "unloaded"
        duration = f"{self.metadata.duration:.2f}s" if self.metadata else "unknown"
        return f"AudioAsset({self.asset_id}, {self.filepath.name}, {duration}, {status})"
    
    def __repr__(self) -> str:
        return self.__str__()

class AudioAssetManager:
    """
    Manages collections of audio assets with caching and optimization.
    """
    
    def __init__(self, cache_limit_mb: int = 1024):
        self.assets: Dict[str, AudioAsset] = {}
        self.cache_limit_bytes = cache_limit_mb * 1024 * 1024
        self.access_times: Dict[str, float] = {}
        
        print(f"[ASSET_MANAGER] Initialized with {cache_limit_mb}MB cache limit")
    
    def add_asset(self, filepath: str, asset_id: str = "") -> AudioAsset:
        """Add an audio asset to the manager"""
        asset = AudioAsset(filepath)
        
        # Use provided ID or generated one
        if asset_id:
            asset.asset_id = asset_id
        
        self.assets[asset.asset_id] = asset
        self.access_times[asset.asset_id] = time.time()
        
        print(f"[ASSET_MANAGER] Added asset {asset.asset_id}")
        return asset
    
    def get_asset(self, asset_id: str) -> Optional[AudioAsset]:
        """Get an asset by ID"""
        if asset_id in self.assets:
            self.access_times[asset_id] = time.time()
            return self.assets[asset_id]
        return None
    
    def remove_asset(self, asset_id: str) -> bool:
        """Remove an asset from the manager"""
        if asset_id in self.assets:
            asset = self.assets[asset_id]
            asset.unload_audio()  # Free memory
            del self.assets[asset_id]
            del self.access_times[asset_id]
            print(f"[ASSET_MANAGER] Removed asset {asset_id}")
            return True
        return False
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get total memory usage of all assets"""
        total_usage = {
            "total_assets": len(self.assets),
            "loaded_assets": 0,
            "total_memory_bytes": 0,
            "audio_data_bytes": 0,
            "metadata_bytes": 0
        }
        
        for asset in self.assets.values():
            usage = asset.get_memory_usage()
            total_usage["total_memory_bytes"] += usage["total_size"]
            total_usage["audio_data_bytes"] += usage["audio_data_size"]
            total_usage["metadata_bytes"] += usage["metadata_size"]
            
            if usage["loaded"]:
                total_usage["loaded_assets"] += 1
        
        return total_usage
    
    def optimize_cache(self):
        """Optimize cache by unloading least recently used assets if over limit"""
        usage = self.get_memory_usage()
        
        if usage["total_memory_bytes"] <= self.cache_limit_bytes:
            return
        
        print(f"[ASSET_MANAGER] Cache over limit ({usage['total_memory_bytes']/1024/1024:.1f}MB), optimizing...")
        
        # Sort assets by access time (oldest first)
        sorted_assets = sorted(
            [(asset_id, self.access_times[asset_id]) for asset_id in self.assets.keys()],
            key=lambda x: x[1]
        )
        
        # Unload oldest assets until under limit
        for asset_id, _ in sorted_assets:
            asset = self.assets[asset_id]
            if asset.loaded:
                asset.unload_audio()
                print(f"[ASSET_MANAGER] Unloaded {asset_id} for cache optimization")
                
                # Check if we're now under limit
                current_usage = self.get_memory_usage()
                if current_usage["total_memory_bytes"] <= self.cache_limit_bytes:
                    break
    
    def list_assets(self) -> List[Dict[str, Any]]:
        """List all managed assets"""
        return [asset.to_dict() for asset in self.assets.values()]

if __name__ == "__main__":
    # Test audio asset functionality
    print("🎵 STAVE Audio Asset Test")
    print("=" * 50)
    
    # This would normally test with a real audio file
    print("⚠️  Audio asset system ready (requires real audio files for full testing)")
    
    # Create asset manager
    manager = AudioAssetManager(cache_limit_mb=512)
    print(f"📊 Manager created with cache limit")
    
    # Test memory usage tracking
    usage = manager.get_memory_usage()
    print(f"💾 Memory usage: {usage}")
    
    print("\n🎯 Audio asset system ready!")
