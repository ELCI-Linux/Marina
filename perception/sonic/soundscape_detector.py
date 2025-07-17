#!/usr/bin/env python3
"""
Soundscape Detection Module for Marina
Analyzes audio files to identify environmental sounds and audio characteristics
"""

import numpy as np
import librosa
import os
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class SoundscapeFeatures:
    """Data class for soundscape features"""
    spectral_centroid: float
    spectral_rolloff: float
    spectral_bandwidth: float
    zero_crossing_rate: float
    mfcc_mean: List[float]
    tempo: float
    rms_energy: float
    pitch_variance: float
    frequency_peaks: List[float]
    dominant_frequency: float

@dataclass
class SoundscapeResult:
    """Data class for soundscape detection results"""
    timestamp: str
    environment_type: str
    confidence: float
    sound_events: List[str]
    acoustic_features: SoundscapeFeatures
    noise_level: str
    audio_quality: str
    description: str

class SoundscapeDetector:
    def __init__(self):
        self.sample_rate = 44100
        self.hop_length = 512
        self.n_mfcc = 13
        
        # Environment classification thresholds
        self.environment_thresholds = {
            'indoor_quiet': {
                'rms_energy': (0.0, 0.05),
                'spectral_centroid': (0, 3000),
                'zero_crossing_rate': (0.0, 0.15)
            },
            'indoor_active': {
                'rms_energy': (0.05, 0.3),
                'spectral_centroid': (1000, 8000),
                'zero_crossing_rate': (0.1, 0.4)
            },
            'outdoor_urban': {
                'rms_energy': (0.1, 0.8),
                'spectral_centroid': (2000, 12000),
                'zero_crossing_rate': (0.2, 0.6)
            },
            'outdoor_nature': {
                'rms_energy': (0.02, 0.4),
                'spectral_centroid': (500, 8000),
                'zero_crossing_rate': (0.05, 0.5)
            },
            'vehicle_interior': {
                'rms_energy': (0.3, 0.9),
                'spectral_centroid': (500, 4000),
                'zero_crossing_rate': (0.1, 0.3)
            },
            'construction_industrial': {
                'rms_energy': (0.4, 1.0),
                'spectral_centroid': (3000, 15000),
                'zero_crossing_rate': (0.3, 0.8)
            }
        }
        
        # Sound event detection patterns
        self.sound_patterns = {
            'speech': {
                'freq_range': (85, 255),
                'spectral_centroid': (500, 3000),
                'mfcc_pattern': 'speech_like'
            },
            'music': {
                'freq_range': (20, 20000),
                'spectral_centroid': (1000, 8000),
                'mfcc_pattern': 'harmonic'
            },
            'traffic': {
                'freq_range': (50, 4000),
                'spectral_centroid': (200, 2000),
                'mfcc_pattern': 'continuous_noise'
            },
            'machinery': {
                'freq_range': (100, 8000),
                'spectral_centroid': (1000, 6000),
                'mfcc_pattern': 'mechanical'
            },
            'nature_sounds': {
                'freq_range': (200, 12000),
                'spectral_centroid': (1000, 8000),
                'mfcc_pattern': 'natural'
            },
            'footsteps': {
                'freq_range': (50, 2000),
                'spectral_centroid': (200, 1500),
                'mfcc_pattern': 'transient'
            },
            'doors_clicks': {
                'freq_range': (100, 8000),
                'spectral_centroid': (500, 4000),
                'mfcc_pattern': 'impact'
            },
            'electronic_beeps': {
                'freq_range': (500, 5000),
                'spectral_centroid': (1000, 4000),
                'mfcc_pattern': 'tonal'
            }
        }
        
    def analyze_audio_file(self, audio_file_path: str) -> Optional[SoundscapeResult]:
        """
        Analyze an audio file for soundscape characteristics
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            SoundscapeResult object with analysis results
        """
        try:
            # Load audio file
            y, sr = librosa.load(audio_file_path, sr=self.sample_rate)
            
            if len(y) == 0:
                return None
                
            # Extract acoustic features
            features = self._extract_features(y, sr)
            
            # Classify environment
            environment_type, env_confidence = self._classify_environment(features)
            
            # Detect sound events
            sound_events = self._detect_sound_events(y, sr, features)
            
            # Assess noise level and audio quality
            noise_level = self._assess_noise_level(features)
            audio_quality = self._assess_audio_quality(y, sr)
            
            # Generate description
            description = self._generate_description(environment_type, sound_events, features)
            
            return SoundscapeResult(
                timestamp=datetime.now().isoformat(),
                environment_type=environment_type,
                confidence=env_confidence,
                sound_events=sound_events,
                acoustic_features=features,
                noise_level=noise_level,
                audio_quality=audio_quality,
                description=description
            )
            
        except Exception as e:
            print(f"Error analyzing audio file: {e}")
            return None
    
    def _extract_features(self, y: np.ndarray, sr: int) -> SoundscapeFeatures:
        """Extract acoustic features from audio signal"""
        
        # Spectral features
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0])
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)[0])
        spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)[0])
        
        # Zero crossing rate
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y)[0])
        
        # MFCC features
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
        mfcc_mean = np.mean(mfcc, axis=1).tolist()
        
        # Tempo
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # RMS energy
        rms_energy = np.mean(librosa.feature.rms(y=y)[0])
        
        # Pitch variance
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        pitch_variance = np.var(pitch_values) if pitch_values else 0.0
        
        # Frequency analysis
        stft = librosa.stft(y)
        magnitude = np.abs(stft)
        frequency_spectrum = np.mean(magnitude, axis=1)
        
        # Find frequency peaks
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(frequency_spectrum, height=np.max(frequency_spectrum) * 0.3)
        frequency_peaks = (peaks * sr / (2 * len(frequency_spectrum))).tolist()
        
        # Dominant frequency
        dominant_freq_idx = np.argmax(frequency_spectrum)
        dominant_frequency = dominant_freq_idx * sr / (2 * len(frequency_spectrum))
        
        return SoundscapeFeatures(
            spectral_centroid=float(spectral_centroid),
            spectral_rolloff=float(spectral_rolloff),
            spectral_bandwidth=float(spectral_bandwidth),
            zero_crossing_rate=float(zero_crossing_rate),
            mfcc_mean=mfcc_mean,
            tempo=float(tempo),
            rms_energy=float(rms_energy),
            pitch_variance=float(pitch_variance),
            frequency_peaks=frequency_peaks[:10],  # Top 10 peaks
            dominant_frequency=float(dominant_frequency)
        )
    
    def _classify_environment(self, features: SoundscapeFeatures) -> Tuple[str, float]:
        """Classify the environment type based on acoustic features"""
        
        scores = {}
        
        for env_type, thresholds in self.environment_thresholds.items():
            score = 0
            total_criteria = 0
            
            # Check RMS energy
            if 'rms_energy' in thresholds:
                min_rms, max_rms = thresholds['rms_energy']
                if min_rms <= features.rms_energy <= max_rms:
                    score += 1
                total_criteria += 1
            
            # Check spectral centroid
            if 'spectral_centroid' in thresholds:
                min_sc, max_sc = thresholds['spectral_centroid']
                if min_sc <= features.spectral_centroid <= max_sc:
                    score += 1
                total_criteria += 1
            
            # Check zero crossing rate
            if 'zero_crossing_rate' in thresholds:
                min_zcr, max_zcr = thresholds['zero_crossing_rate']
                if min_zcr <= features.zero_crossing_rate <= max_zcr:
                    score += 1
                total_criteria += 1
            
            # Calculate confidence
            confidence = score / total_criteria if total_criteria > 0 else 0
            scores[env_type] = confidence
        
        # Find best match
        best_env = max(scores, key=scores.get)
        best_confidence = scores[best_env]
        
        return best_env, best_confidence
    
    def _detect_sound_events(self, y: np.ndarray, sr: int, features: SoundscapeFeatures) -> List[str]:
        """Detect specific sound events in the audio"""
        
        detected_events = []
        
        # Speech detection
        if self._is_speech_like(features):
            detected_events.append('speech')
        
        # Music detection (if not already detected by song recognition)
        if self._is_music_like(features):
            detected_events.append('music')
        
        # Traffic noise detection
        if self._is_traffic_like(features):
            detected_events.append('traffic')
        
        # Machinery detection
        if self._is_machinery_like(features):
            detected_events.append('machinery')
        
        # Nature sounds detection
        if self._is_nature_like(features):
            detected_events.append('nature_sounds')
        
        # Transient events (footsteps, door clicks, etc.)
        if self._has_transient_events(y, sr):
            detected_events.append('transient_events')
        
        # Electronic beeps/alarms
        if self._has_electronic_sounds(features):
            detected_events.append('electronic_beeps')
        
        return detected_events
    
    def _is_speech_like(self, features: SoundscapeFeatures) -> bool:
        """Check if audio contains speech-like characteristics"""
        # Speech typically has specific MFCC patterns and spectral characteristics
        speech_indicators = 0
        
        # Check spectral centroid (speech typically 500-3000 Hz)
        if 500 <= features.spectral_centroid <= 3000:
            speech_indicators += 1
        
        # Check zero crossing rate (speech has moderate ZCR)
        if 0.1 <= features.zero_crossing_rate <= 0.4:
            speech_indicators += 1
        
        # Check MFCC pattern (simplified check)
        if len(features.mfcc_mean) >= 3:
            # Speech typically has certain MFCC characteristics
            if features.mfcc_mean[1] > features.mfcc_mean[2]:
                speech_indicators += 1
        
        return speech_indicators >= 2
    
    def _is_music_like(self, features: SoundscapeFeatures) -> bool:
        """Check if audio contains music-like characteristics"""
        music_indicators = 0
        
        # Music typically has higher spectral bandwidth
        if features.spectral_bandwidth > 1000:
            music_indicators += 1
        
        # Music has detectable tempo
        if features.tempo > 60:
            music_indicators += 1
        
        # Music has harmonic content (multiple frequency peaks)
        if len(features.frequency_peaks) >= 3:
            music_indicators += 1
        
        return music_indicators >= 2
    
    def _is_traffic_like(self, features: SoundscapeFeatures) -> bool:
        """Check if audio contains traffic-like characteristics"""
        # Traffic has continuous low-frequency content
        return (features.spectral_centroid < 2000 and 
                features.rms_energy > 0.1 and
                features.zero_crossing_rate < 0.3)
    
    def _is_machinery_like(self, features: SoundscapeFeatures) -> bool:
        """Check if audio contains machinery-like characteristics"""
        # Machinery has consistent spectral content and higher energy
        return (features.rms_energy > 0.3 and
                features.pitch_variance < 1000 and
                features.spectral_centroid > 1000)
    
    def _is_nature_like(self, features: SoundscapeFeatures) -> bool:
        """Check if audio contains nature-like characteristics"""
        # Nature sounds have varied spectral content and moderate energy
        return (features.spectral_bandwidth > 2000 and
                features.zero_crossing_rate > 0.2 and
                len(features.frequency_peaks) >= 2)
    
    def _has_transient_events(self, y: np.ndarray, sr: int) -> bool:
        """Check for transient events like footsteps, door clicks"""
        # Detect sudden energy changes
        rms = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
        energy_diff = np.diff(rms)
        
        # Count significant energy changes
        threshold = np.std(energy_diff) * 2
        transients = np.sum(np.abs(energy_diff) > threshold)
        
        return transients > 5  # Arbitrary threshold
    
    def _has_electronic_sounds(self, features: SoundscapeFeatures) -> bool:
        """Check for electronic beeps, alarms, notifications"""
        # Electronic sounds often have pure tones
        return (features.pitch_variance < 100 and
                1000 <= features.dominant_frequency <= 4000 and
                features.spectral_bandwidth < 1000)
    
    def _assess_noise_level(self, features: SoundscapeFeatures) -> str:
        """Assess the noise level of the environment"""
        if features.rms_energy < 0.05:
            return 'quiet'
        elif features.rms_energy < 0.2:
            return 'moderate'
        elif features.rms_energy < 0.5:
            return 'loud'
        else:
            return 'very_loud'
    
    def _assess_audio_quality(self, y: np.ndarray, sr: int) -> str:
        """Assess the quality of the audio recording"""
        # Check for clipping
        clipping_ratio = np.sum(np.abs(y) > 0.95) / len(y)
        
        # Check dynamic range
        dynamic_range = np.max(y) - np.min(y)
        
        # Check for silence
        silence_ratio = np.sum(np.abs(y) < 0.01) / len(y)
        
        if clipping_ratio > 0.1:
            return 'poor_clipped'
        elif dynamic_range < 0.1:
            return 'poor_low_dynamic_range'
        elif silence_ratio > 0.8:
            return 'mostly_silent'
        else:
            return 'good'
    
    def _generate_description(self, environment_type: str, sound_events: List[str], 
                            features: SoundscapeFeatures) -> str:
        """Generate a human-readable description of the soundscape"""
        
        # Environment descriptions
        env_descriptions = {
            'indoor_quiet': 'quiet indoor environment',
            'indoor_active': 'active indoor environment',
            'outdoor_urban': 'urban outdoor environment',
            'outdoor_nature': 'natural outdoor environment',
            'vehicle_interior': 'vehicle interior',
            'construction_industrial': 'construction or industrial area'
        }
        
        base_desc = env_descriptions.get(environment_type, 'unidentified environment')
        
        # Add sound events
        if sound_events:
            events_desc = ', '.join(sound_events)
            desc = f"{base_desc} with {events_desc}"
        else:
            desc = base_desc
        
        # Add energy level context
        if features.rms_energy > 0.5:
            desc += " (high energy)"
        elif features.rms_energy < 0.05:
            desc += " (low energy)"
        
        return desc.capitalize()
    
    def save_results(self, results: SoundscapeResult, file_path: str):
        """Save soundscape analysis results to file"""
        try:
            # Convert to dictionary for JSON serialization
            result_dict = {
                'timestamp': results.timestamp,
                'environment_type': results.environment_type,
                'confidence': results.confidence,
                'sound_events': results.sound_events,
                'acoustic_features': {
                    'spectral_centroid': results.acoustic_features.spectral_centroid,
                    'spectral_rolloff': results.acoustic_features.spectral_rolloff,
                    'spectral_bandwidth': results.acoustic_features.spectral_bandwidth,
                    'zero_crossing_rate': results.acoustic_features.zero_crossing_rate,
                    'mfcc_mean': results.acoustic_features.mfcc_mean,
                    'tempo': results.acoustic_features.tempo,
                    'rms_energy': results.acoustic_features.rms_energy,
                    'pitch_variance': results.acoustic_features.pitch_variance,
                    'frequency_peaks': results.acoustic_features.frequency_peaks,
                    'dominant_frequency': results.acoustic_features.dominant_frequency
                },
                'noise_level': results.noise_level,
                'audio_quality': results.audio_quality,
                'description': results.description
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Load existing data if file exists
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
            else:
                data = {'soundscape_history': []}
            
            # Add new result
            data['soundscape_history'].append(result_dict)
            
            # Keep only last 100 entries
            if len(data['soundscape_history']) > 100:
                data['soundscape_history'] = data['soundscape_history'][-100:]
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving soundscape results: {e}")
