"""
Advanced Audio Processing Engine
Handles multi-format audio processing, enhancement, and analysis
"""

import numpy as np
import sounddevice as sd
import librosa
import scipy.signal
import threading
import queue
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import psutil
import psutil
import logging
import logging

class AudioProcessor:
    cpu_percent = 0
    ram_usage = 0
    psutil_available = True
    """Advanced audio processing with real-time capabilities"""
    
    psutil_available = True

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 4096):
        try:
            import psutil
            self.process = psutil.Process()
        except ImportError:
            self.psutil_available = False
            self.logger.warning("psutil not available. CPU and RAM usage metrics will not be available.")
            self.process = None
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.audio_queue = queue.Queue()
        self.processing_thread = None
        self.is_recording = False
        self.audio_buffer = []
        
        # Audio enhancement parameters
        self.noise_reduction_enabled = True
        self.voice_enhancement_enabled = True
        self.dynamic_range_compression = True
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
    def start_realtime_processing(self, callback=None):
        """Start real-time audio processing"""
        self.is_recording = True
        self.processing_thread = threading.Thread(
            target=self._realtime_processing_loop, 
            args=(callback,), 
            daemon=True
        )
        self.processing_thread.start()
        
    def stop_realtime_processing(self):
        """Stop real-time audio processing"""
        self.is_recording = False
        if self.processing_thread:
            self.processing_thread.join()
    
    def _realtime_processing_loop(self, callback):
        """Main real-time processing loop"""
        def audio_callback(indata, frames, time, status):
            if status:
                self.logger.warning(f"Audio callback status: {status}")
            self.audio_queue.put(indata.copy())
        
        try:
            with sd.InputStream(callback=audio_callback, 
                              samplerate=self.sample_rate,
                              blocksize=self.buffer_size,
                              channels=1):
                while self.is_recording:
                    try:
                        audio_chunk = self.audio_queue.get(timeout=1.0)
                        processed_chunk = self.process_audio_chunk(audio_chunk)
                        
                        if callback:
                            callback(processed_chunk)
                            
                    except queue.Empty:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Real-time processing error: {e}")
    
    def process_audio_chunk(self, audio_chunk: np.ndarray) -> Dict[str, Any]:
        """Process a single audio chunk with multiple analyses"""
        # Flatten if stereo
        if len(audio_chunk.shape) > 1:
            audio_chunk = audio_chunk.flatten()
        
        # Apply audio enhancements
        enhanced_audio = self._enhance_audio(audio_chunk)
        
        # Extract features
        features = self._extract_features(enhanced_audio)
        
        # Detect audio events
        events = self._detect_audio_events(enhanced_audio)
        
        return {
            'timestamp': time.time(),
            'raw_audio': audio_chunk,
            'enhanced_audio': enhanced_audio,
            'features': features,
            'events': events,
            'rms_level': np.sqrt(np.mean(enhanced_audio**2)),
            'peak_level': np.max(np.abs(enhanced_audio))
        }
    
    def _enhance_audio(self, audio: np.ndarray) -> np.ndarray:
        """Apply audio enhancement techniques"""
        enhanced = audio.copy()
        
        # Noise reduction using spectral subtraction
        if self.noise_reduction_enabled:
            enhanced = self._spectral_subtraction(enhanced)
        
        # Voice enhancement using formant sharpening
        if self.voice_enhancement_enabled:
            enhanced = self._enhance_voice(enhanced)
        
        # Dynamic range compression
        if self.dynamic_range_compression:
            enhanced = self._compress_dynamic_range(enhanced)
        
        return enhanced
    
    def _spectral_subtraction(self, audio: np.ndarray) -> np.ndarray:
        """Reduce noise using spectral subtraction"""
        # Compute STFT
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise floor (first 0.1 seconds)
        noise_frames = min(int(0.1 * self.sample_rate / 512), magnitude.shape[1])
        noise_spectrum = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Spectral subtraction
        alpha = 2.0  # Over-subtraction factor
        enhanced_magnitude = magnitude - alpha * noise_spectrum
        enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)
        
        # Reconstruct audio
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        return librosa.istft(enhanced_stft, hop_length=512)
    
    def _enhance_voice(self, audio: np.ndarray) -> np.ndarray:
        """Enhance voice characteristics"""
        # Apply pre-emphasis filter
        pre_emphasis = 0.97
        emphasized = np.append(audio[0], audio[1:] - pre_emphasis * audio[:-1])
        
        # Apply formant enhancement (simple high-pass filter)
        sos = scipy.signal.butter(4, 300, 'hp', fs=self.sample_rate, output='sos')
        return scipy.signal.sosfilt(sos, emphasized)
    
    def _compress_dynamic_range(self, audio: np.ndarray) -> np.ndarray:
        """Apply dynamic range compression"""
        # Simple AGC (Automatic Gain Control)
        target_rms = 0.1
        current_rms = np.sqrt(np.mean(audio**2))
        
        if current_rms > 0:
            gain = target_rms / current_rms
            # Limit gain to prevent over-amplification
            gain = np.clip(gain, 0.1, 10.0)
            return audio * gain
        
        return audio
    
    def _extract_features(self, audio: np.ndarray) -> Dict[str, float]:
        """Extract audio features for analysis"""
        features = {}
        
        # Time domain features
        features['rms'] = np.sqrt(np.mean(audio**2))
        features['peak'] = np.max(np.abs(audio))
        features['zero_crossing_rate'] = np.mean(librosa.feature.zero_crossing_rate(audio))
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate)
        features['spectral_centroid'] = np.mean(spectral_centroids)
        
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate)
        features['spectral_rolloff'] = np.mean(spectral_rolloff)
        
        # MFCC features
        mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=13)
        for i, mfcc in enumerate(mfccs):
            features[f'mfcc_{i+1}'] = np.mean(mfcc)
        
        return features
    
    def _detect_audio_events(self, audio: np.ndarray) -> List[Dict[str, Any]]:
        """Detect audio events in the signal"""
        events = []
        
        # Voice activity detection
        if self._is_voice_activity(audio):
            events.append({
                'type': 'voice_activity',
                'confidence': self._voice_confidence(audio),
                'timestamp': time.time()
            })
        
        # Silence detection
        if self._is_silence(audio):
            events.append({
                'type': 'silence',
                'duration': len(audio) / self.sample_rate,
                'timestamp': time.time()
            })
        
        # Transient detection (sudden changes)
        if self._detect_transient(audio):
            events.append({
                'type': 'transient',
                'timestamp': time.time()
            })
        
        return events
    
    def _is_voice_activity(self, audio: np.ndarray) -> bool:
        """Simple voice activity detection"""
        # Energy-based VAD with spectral features
        energy = np.sum(audio**2)
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate))
        
        # Voice typically has energy > threshold and spectral centroid in human voice range
        return energy > 0.001 and 85 <= spectral_centroid <= 255
    
    def _voice_confidence(self, audio: np.ndarray) -> float:
        """Calculate voice confidence score"""
        # Simplified voice confidence based on spectral characteristics
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate))
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate))
        
        # Normalize to 0-1 range based on typical voice characteristics
        centroid_score = 1.0 - abs(spectral_centroid - 170) / 170
        rolloff_score = 1.0 - abs(spectral_rolloff - 2000) / 2000
        
        return np.clip((centroid_score + rolloff_score) / 2, 0, 1)
    
    def _is_silence(self, audio: np.ndarray) -> bool:
        """Detect silence in audio"""
        rms = np.sqrt(np.mean(audio**2))
        return rms < 0.01  # Threshold for silence
    
    def _detect_transient(self, audio: np.ndarray) -> bool:
        """Detect transient events (sudden changes)"""
        # Simple onset detection
        onset_frames = librosa.onset.onset_detect(y=audio, sr=self.sample_rate)
        return len(onset_frames) > 0
    
    def load_audio_file(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file with librosa"""
        try:
            audio, sr = librosa.load(file_path, sr=self.sample_rate)
            return audio, sr
        except Exception as e:
            self.logger.error(f"Error loading audio file {file_path}: {e}")
            return None, None
    
    def save_audio_file(self, audio: np.ndarray, file_path: str):
        """Save audio to file"""
        try:
            import soundfile as sf
            sf.write(file_path, audio, self.sample_rate)
        except Exception as e:
            self.logger.error(f"Error saving audio file {file_path}: {e}")
    
    def get_system_usage(self):
        if not self.psutil_available:
            return 0, 0
        try:
            self.cpu_percent = self.process.cpu_percent(interval=0.1)
            self.ram_usage = self.process.memory_info().rss / (1024 * 1024)  # in MB
            return self.cpu_percent, self.ram_usage
        except Exception as e:
            self.logger.error(f"Error getting system usage: {e}")
            return 0, 0
        try:
            process = psutil.Process()
            self.cpu_percent = process.cpu_percent(interval=0.1)
            self.ram_usage = process.memory_info().rss / (1024 * 1024)  # in MB
            return self.cpu_percent, self.ram_usage
        except Exception as e:
            self.logger.error(f"Error getting system usage: {e}")
            return 0, 0
        """Get comprehensive audio information"""
        return {
            'duration': len(audio) / self.sample_rate,
            'sample_rate': self.sample_rate,
            'channels': 1 if len(audio.shape) == 1 else audio.shape[1],
            'rms_level': np.sqrt(np.mean(audio**2)),
            'peak_level': np.max(np.abs(audio)),
            'dynamic_range': np.max(np.abs(audio)) - np.min(np.abs(audio)),
            'features': self._extract_features(audio)
        }
