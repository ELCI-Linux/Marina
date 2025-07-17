"""
Vocal Analysis Module
Advanced vocal pattern recognition, emotion detection, and speaker identification
"""

import numpy as np
import librosa
import scipy.stats
from typing import Dict, List, Tuple, Optional
import logging

class VocalAnalyzer:
    """Advanced vocal analysis with emotion detection and speaker identification"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Vocal characteristics thresholds
        self.pitch_ranges = {
            'male': (85, 180),
            'female': (165, 265),
            'child': (250, 400)
        }
        
        # Emotion classification features
        self.emotion_features = {
            'anger': {'pitch_mean': 'high', 'pitch_var': 'high', 'energy': 'high'},
            'happiness': {'pitch_mean': 'high', 'pitch_var': 'medium', 'energy': 'high'},
            'sadness': {'pitch_mean': 'low', 'pitch_var': 'low', 'energy': 'low'},
            'fear': {'pitch_mean': 'high', 'pitch_var': 'very_high', 'energy': 'medium'},
            'neutral': {'pitch_mean': 'medium', 'pitch_var': 'medium', 'energy': 'medium'}
        }
    
    def analyze_vocal_characteristics(self, audio: np.ndarray, 
                                    sample_rate: int) -> Dict[str, float]:
        """Extract comprehensive vocal characteristics"""
        # Fundamental frequency (pitch) analysis
        f0 = librosa.yin(audio, fmin=50, fmax=400, sr=sample_rate)
        f0_clean = f0[f0 > 0]  # Remove unvoiced frames
        
        # Formant analysis (simplified using spectral peaks)
        formants = self._estimate_formants(audio, sample_rate)
        
        # Vocal tract characteristics
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sample_rate))
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sample_rate))
        
        # Jitter and shimmer (voice quality measures)
        jitter = self._calculate_jitter(f0_clean)
        shimmer = self._calculate_shimmer(audio, sample_rate)
        
        # Voice strength indicators
        hnr = self._calculate_hnr(audio, sample_rate)  # Harmonics-to-noise ratio
        
        return {
            'pitch_mean': np.mean(f0_clean) if len(f0_clean) > 0 else 0,
            'pitch_std': np.std(f0_clean) if len(f0_clean) > 0 else 0,
            'pitch_range': np.max(f0_clean) - np.min(f0_clean) if len(f0_clean) > 0 else 0,
            'formant_f1': formants[0] if len(formants) > 0 else 0,
            'formant_f2': formants[1] if len(formants) > 1 else 0,
            'formant_f3': formants[2] if len(formants) > 2 else 0,
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'jitter': jitter,
            'shimmer': shimmer,
            'hnr': hnr,
            'voice_strength': self._calculate_voice_strength(audio)
        }
    
    def detect_emotion(self, vocal_characteristics: Dict[str, float]) -> Dict[str, float]:
        """Detect emotion based on vocal characteristics"""
        emotion_scores = {}
        
        # Normalize features for comparison
        pitch_norm = self._normalize_feature(vocal_characteristics['pitch_mean'], 50, 400)
        pitch_var_norm = self._normalize_feature(vocal_characteristics['pitch_std'], 0, 50)
        energy_norm = vocal_characteristics['voice_strength']
        
        # Calculate similarity to each emotion profile
        for emotion, profile in self.emotion_features.items():
            score = self._calculate_emotion_score(pitch_norm, pitch_var_norm, energy_norm, profile)
            emotion_scores[emotion] = score
        
        # Normalize scores to sum to 1
        total_score = sum(emotion_scores.values())
        if total_score > 0:
            emotion_scores = {k: v/total_score for k, v in emotion_scores.items()}
        
        return emotion_scores
    
    def identify_speaker_characteristics(self, vocal_characteristics: Dict[str, float]) -> Dict[str, str]:
        """Identify speaker characteristics from vocal features"""
        characteristics = {}
        
        # Gender classification based on pitch
        pitch_mean = vocal_characteristics['pitch_mean']
        if pitch_mean > 0:
            if pitch_mean < 150:
                characteristics['gender'] = 'male'
            elif pitch_mean < 250:
                characteristics['gender'] = 'female'
            else:
                characteristics['gender'] = 'child'
        else:
            characteristics['gender'] = 'unknown'
        
        # Age estimation (simplified)
        if vocal_characteristics['hnr'] > 0.8 and vocal_characteristics['jitter'] < 0.01:
            characteristics['age_group'] = 'young'
        elif vocal_characteristics['hnr'] > 0.6 and vocal_characteristics['jitter'] < 0.02:
            characteristics['age_group'] = 'middle'
        else:
            characteristics['age_group'] = 'elderly'
        
        # Voice quality assessment
        if vocal_characteristics['hnr'] > 0.7 and vocal_characteristics['shimmer'] < 0.1:
            characteristics['voice_quality'] = 'healthy'
        elif vocal_characteristics['hnr'] > 0.5:
            characteristics['voice_quality'] = 'mild_pathology'
        else:
            characteristics['voice_quality'] = 'pathological'
        
        return characteristics
    
    def analyze_speech_patterns(self, audio: np.ndarray, 
                               sample_rate: int) -> Dict[str, float]:
        """Analyze speech patterns and prosody"""
        # Voice activity detection
        voice_activity = self._detect_voice_activity(audio, sample_rate)
        
        # Speech rate calculation
        speech_rate = self._calculate_speech_rate(voice_activity, sample_rate)
        
        # Pause analysis
        pause_stats = self._analyze_pauses(voice_activity, sample_rate)
        
        # Stress and emphasis detection
        stress_patterns = self._detect_stress_patterns(audio, sample_rate)
        
        return {
            'speech_rate': speech_rate,
            'pause_frequency': pause_stats['frequency'],
            'average_pause_duration': pause_stats['avg_duration'],
            'stress_frequency': stress_patterns['frequency'],
            'voice_activity_ratio': np.mean(voice_activity)
        }
    
    def _estimate_formants(self, audio: np.ndarray, sample_rate: int) -> List[float]:
        """Estimate formant frequencies using LPC analysis"""
        # Apply pre-emphasis
        pre_emphasis = 0.97
        emphasized = np.append(audio[0], audio[1:] - pre_emphasis * audio[:-1])
        
        # LPC analysis
        lpc_order = int(sample_rate / 1000) + 2  # Rule of thumb
        lpc_coeffs = librosa.lpc(emphasized, order=lpc_order)
        
        # Find formants from LPC roots
        roots = np.roots(lpc_coeffs)
        roots = roots[np.imag(roots) >= 0]  # Keep positive imaginary parts
        
        # Convert to frequencies
        formants = []
        for root in roots:
            if abs(root) > 0.5:  # Avoid spurious formants
                freq = np.angle(root) * sample_rate / (2 * np.pi)
                if 200 < freq < 4000:  # Typical formant range
                    formants.append(freq)
        
        return sorted(formants)[:3]  # Return first 3 formants
    
    def _calculate_jitter(self, f0: np.ndarray) -> float:
        """Calculate pitch jitter (period-to-period variation)"""
        if len(f0) < 2:
            return 0.0
        
        # Convert to periods
        periods = 1.0 / f0
        
        # Calculate relative period differences
        period_diffs = np.abs(np.diff(periods))
        avg_period = np.mean(periods[:-1])
        
        return np.mean(period_diffs) / avg_period if avg_period > 0 else 0.0
    
    def _calculate_shimmer(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate amplitude shimmer (amplitude variation)"""
        # Extract amplitude envelope
        amplitude = np.abs(librosa.stft(audio))
        amplitude_envelope = np.mean(amplitude, axis=0)
        
        if len(amplitude_envelope) < 2:
            return 0.0
        
        # Calculate relative amplitude differences
        amp_diffs = np.abs(np.diff(amplitude_envelope))
        avg_amplitude = np.mean(amplitude_envelope[:-1])
        
        return np.mean(amp_diffs) / avg_amplitude if avg_amplitude > 0 else 0.0
    
    def _calculate_hnr(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate Harmonics-to-Noise Ratio"""
        # Autocorrelation-based HNR estimation
        autocorr = np.correlate(audio, audio, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        # Find fundamental period
        min_period = int(sample_rate / 400)  # 400 Hz max
        max_period = int(sample_rate / 50)   # 50 Hz min
        
        if max_period < len(autocorr):
            period_range = autocorr[min_period:max_period]
            if len(period_range) > 0:
                max_autocorr = np.max(period_range)
                noise_floor = np.mean(autocorr[max_period:])
                
                if noise_floor > 0:
                    return max_autocorr / noise_floor
        
        return 0.0
    
    def _calculate_voice_strength(self, audio: np.ndarray) -> float:
        """Calculate overall voice strength/energy"""
        return np.sqrt(np.mean(audio**2))
    
    def _normalize_feature(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize feature to 0-1 range"""
        return np.clip((value - min_val) / (max_val - min_val), 0, 1)
    
    def _calculate_emotion_score(self, pitch_norm: float, pitch_var_norm: float, 
                               energy_norm: float, emotion_profile: Dict) -> float:
        """Calculate similarity score to emotion profile"""
        # Convert qualitative descriptors to numeric values
        level_map = {'very_low': 0.1, 'low': 0.3, 'medium': 0.5, 'high': 0.7, 'very_high': 0.9}
        
        pitch_target = level_map[emotion_profile['pitch_mean']]
        pitch_var_target = level_map[emotion_profile['pitch_var']]
        energy_target = level_map[emotion_profile['energy']]
        
        # Calculate distances
        pitch_dist = abs(pitch_norm - pitch_target)
        pitch_var_dist = abs(pitch_var_norm - pitch_var_target)
        energy_dist = abs(energy_norm - energy_target)
        
        # Combined similarity score
        return 1.0 - (pitch_dist + pitch_var_dist + energy_dist) / 3.0
    
    def _detect_voice_activity(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Simple voice activity detection"""
        # Frame-based energy calculation
        frame_length = int(0.025 * sample_rate)  # 25ms frames
        hop_length = int(0.010 * sample_rate)    # 10ms hop
        
        frames = librosa.util.frame(audio, frame_length=frame_length, 
                                   hop_length=hop_length, axis=0)
        
        # Energy-based VAD
        energy = np.sum(frames**2, axis=1)
        threshold = np.mean(energy) * 0.1  # Adaptive threshold
        
        return energy > threshold
    
    def _calculate_speech_rate(self, voice_activity: np.ndarray, 
                             sample_rate: int) -> float:
        """Calculate speech rate in syllables per second"""
        # Simplified: count voice activity transitions as syllable boundaries
        transitions = np.diff(voice_activity.astype(int))
        syllable_onsets = np.sum(transitions > 0)
        
        duration = len(voice_activity) * 0.010  # 10ms hop
        return syllable_onsets / duration if duration > 0 else 0.0
    
    def _analyze_pauses(self, voice_activity: np.ndarray, 
                       sample_rate: int) -> Dict[str, float]:
        """Analyze pause patterns in speech"""
        # Find pause segments
        pauses = ~voice_activity
        pause_segments = []
        
        in_pause = False
        pause_start = 0
        
        for i, is_pause in enumerate(pauses):
            if is_pause and not in_pause:
                pause_start = i
                in_pause = True
            elif not is_pause and in_pause:
                pause_segments.append(i - pause_start)
                in_pause = False
        
        if not pause_segments:
            return {'frequency': 0.0, 'avg_duration': 0.0}
        
        # Convert to seconds
        pause_durations = [seg * 0.010 for seg in pause_segments]
        total_duration = len(voice_activity) * 0.010
        
        return {
            'frequency': len(pause_segments) / total_duration,
            'avg_duration': np.mean(pause_durations)
        }
    
    def _detect_stress_patterns(self, audio: np.ndarray, 
                              sample_rate: int) -> Dict[str, float]:
        """Detect stress and emphasis patterns"""
        # Simplified stress detection based on energy peaks
        frame_length = int(0.050 * sample_rate)  # 50ms frames
        hop_length = int(0.025 * sample_rate)    # 25ms hop
        
        frames = librosa.util.frame(audio, frame_length=frame_length, 
                                   hop_length=hop_length, axis=0)
        
        # Calculate energy for each frame
        energy = np.sum(frames**2, axis=1)
        
        # Find stress peaks (energy peaks above threshold)
        threshold = np.mean(energy) + 2 * np.std(energy)
        stress_peaks = energy > threshold
        
        duration = len(energy) * 0.025  # 25ms hop
        stress_frequency = np.sum(stress_peaks) / duration if duration > 0 else 0.0
        
        return {'frequency': stress_frequency}
