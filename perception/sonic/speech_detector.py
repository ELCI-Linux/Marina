#!/usr/bin/env python3
"""
Speech Detection Module
Distinguishes speech from music and other sounds using advanced audio analysis
"""

import numpy as np
import librosa
import logging
from typing import Dict, Tuple, Optional, List
from .sound_classifier import SoundClassifier
from .vocal_analysis import VocalAnalyzer

class SpeechDetector:
    """Advanced speech detection that distinguishes speech from music and other sounds"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize components
        self.sound_classifier = SoundClassifier()
        self.vocal_analyzer = VocalAnalyzer()
        
        # Speech detection thresholds
        self.speech_confidence_threshold = 0.6
        self.music_detection_threshold = 0.5
        
        # Audio analysis parameters
        self.sample_rate = 16000
        self.frame_size = 0.025  # 25ms
        self.hop_size = 0.010    # 10ms
        
    def detect_speech(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, any]:
        """
        Detect if audio contains speech and differentiate from music
        
        Args:
            audio_data: Audio signal
            sample_rate: Sample rate of audio
            
        Returns:
            Dictionary with detection results
        """
        try:
            # Resample if needed
            if sample_rate != self.sample_rate:
                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=self.sample_rate)
                sample_rate = self.sample_rate
            
            # Basic audio analysis
            audio_features = self._extract_audio_features(audio_data, sample_rate)
            
            # Classify sound type
            sound_type = self.sound_classifier.classify(audio_data, sample_rate)
            
            # Vocal analysis for speech characteristics
            vocal_characteristics = self.vocal_analyzer.analyze_vocal_characteristics(audio_data, sample_rate)
            
            # Speech vs music classification
            speech_probability = self._calculate_speech_probability(audio_features, vocal_characteristics)
            music_probability = self._calculate_music_probability(audio_features)
            
            # Determine final classification
            is_speech = speech_probability > self.speech_confidence_threshold
            is_music = music_probability > self.music_detection_threshold
            
            # Handle ambiguous cases
            if is_speech and is_music:
                # Vocals in music vs speech
                if vocal_characteristics.get('formant_f1', 0) > 0 and vocal_characteristics.get('pitch_std', 0) < 30:
                    is_speech = True
                    is_music = False
                else:
                    is_speech = False
                    is_music = True
            
            return {
                'is_speech': is_speech,
                'is_music': is_music,
                'speech_probability': speech_probability,
                'music_probability': music_probability,
                'sound_type': sound_type,
                'vocal_characteristics': vocal_characteristics,
                'audio_features': audio_features,
                'confidence': max(speech_probability, music_probability) if is_speech or is_music else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Speech detection failed: {e}")
            return {
                'is_speech': False,
                'is_music': False,
                'speech_probability': 0.0,
                'music_probability': 0.0,
                'sound_type': 'unknown',
                'vocal_characteristics': {},
                'audio_features': {},
                'confidence': 0.0
            }
    
    def _extract_audio_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Extract comprehensive audio features for classification"""
        features = {}
        
        try:
            # Spectral features
            features['spectral_centroid'] = np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate))
            features['spectral_rolloff'] = np.mean(librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate))
            features['spectral_bandwidth'] = np.mean(librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate))
            features['spectral_contrast'] = np.mean(librosa.feature.spectral_contrast(y=audio_data, sr=sample_rate))
            
            # Rhythm features
            tempo, beats = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            features['tempo'] = tempo
            features['beat_strength'] = np.mean(librosa.onset.onset_strength(y=audio_data, sr=sample_rate))
            
            # Harmonic features
            harmonic, percussive = librosa.effects.hpss(audio_data)
            features['harmonic_ratio'] = np.mean(harmonic**2) / (np.mean(harmonic**2) + np.mean(percussive**2))
            
            # Zero crossing rate (speech indicator)
            features['zero_crossing_rate'] = np.mean(librosa.feature.zero_crossing_rate(audio_data))
            
            # MFCC features (speech-specific)
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            features['mfcc_mean'] = np.mean(mfccs)
            features['mfcc_std'] = np.std(mfccs)
            
            # Chroma features (music-specific)
            chroma = librosa.feature.chroma_stft(y=audio_data, sr=sample_rate)
            features['chroma_mean'] = np.mean(chroma)
            features['chroma_std'] = np.std(chroma)
            
            # Energy features
            features['rms_energy'] = np.mean(librosa.feature.rms(y=audio_data))
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            
        return features
    
    def _calculate_speech_probability(self, audio_features: Dict[str, float], 
                                    vocal_characteristics: Dict[str, float]) -> float:
        """Calculate probability that audio contains speech"""
        speech_score = 0.0
        
        try:
            # Zero crossing rate (speech has higher ZCR than music)
            zcr = audio_features.get('zero_crossing_rate', 0)
            if 0.05 < zcr < 0.25:  # Typical speech range
                speech_score += 0.2
            
            # Spectral characteristics
            spectral_centroid = audio_features.get('spectral_centroid', 0)
            if 1000 < spectral_centroid < 4000:  # Speech frequency range
                speech_score += 0.15
            
            # Formant presence (strong indicator of speech)
            f1 = vocal_characteristics.get('formant_f1', 0)
            f2 = vocal_characteristics.get('formant_f2', 0)
            if f1 > 200 and f2 > 800:  # Typical formant values
                speech_score += 0.3
            
            # Pitch characteristics
            pitch_mean = vocal_characteristics.get('pitch_mean', 0)
            pitch_std = vocal_characteristics.get('pitch_std', 0)
            if 80 < pitch_mean < 400 and pitch_std < 50:  # Speech pitch range
                speech_score += 0.2
            
            # Harmonic to noise ratio
            hnr = vocal_characteristics.get('hnr', 0)
            if hnr > 0.5:  # Speech typically has good HNR
                speech_score += 0.15
            
        except Exception as e:
            self.logger.error(f"Speech probability calculation failed: {e}")
            
        return min(speech_score, 1.0)
    
    def _calculate_music_probability(self, audio_features: Dict[str, float]) -> float:
        """Calculate probability that audio contains music"""
        music_score = 0.0
        
        try:
            # Tempo and beat strength (music has regular beats)
            tempo = audio_features.get('tempo', 0)
            beat_strength = audio_features.get('beat_strength', 0)
            if 60 < tempo < 200 and beat_strength > 0.1:
                music_score += 0.25
            
            # Harmonic content (music is more harmonic)
            harmonic_ratio = audio_features.get('harmonic_ratio', 0)
            if harmonic_ratio > 0.6:
                music_score += 0.2
            
            # Chroma features (music has tonal structure)
            chroma_std = audio_features.get('chroma_std', 0)
            if chroma_std > 0.1:  # Music has varied chroma
                music_score += 0.15
            
            # Spectral contrast (music has more varied frequency content)
            spectral_contrast = audio_features.get('spectral_contrast', 0)
            if spectral_contrast > 10:
                music_score += 0.2
            
            # Lower zero crossing rate than speech
            zcr = audio_features.get('zero_crossing_rate', 0)
            if zcr < 0.1:
                music_score += 0.2
            
        except Exception as e:
            self.logger.error(f"Music probability calculation failed: {e}")
            
        return min(music_score, 1.0)
    
    def is_speech_dominant(self, audio_data: np.ndarray, sample_rate: int) -> bool:
        """Quick check if speech is dominant in audio"""
        try:
            detection_result = self.detect_speech(audio_data, sample_rate)
            return detection_result['is_speech'] and detection_result['confidence'] > 0.7
        except Exception as e:
            self.logger.error(f"Speech dominance check failed: {e}")
            return False
    
    def get_speech_segments(self, audio_data: np.ndarray, sample_rate: int, 
                           segment_duration: float = 1.0) -> List[Tuple[float, float, Dict]]:
        """
        Get speech segments with timestamps
        
        Args:
            audio_data: Audio signal
            sample_rate: Sample rate
            segment_duration: Duration of each segment in seconds
            
        Returns:
            List of (start_time, end_time, detection_result) tuples
        """
        segments = []
        segment_samples = int(segment_duration * sample_rate)
        
        try:
            for i in range(0, len(audio_data), segment_samples):
                start_time = i / sample_rate
                end_time = min((i + segment_samples) / sample_rate, len(audio_data) / sample_rate)
                
                segment_audio = audio_data[i:i + segment_samples]
                if len(segment_audio) > 0:
                    detection_result = self.detect_speech(segment_audio, sample_rate)
                    segments.append((start_time, end_time, detection_result))
                    
        except Exception as e:
            self.logger.error(f"Speech segmentation failed: {e}")
            
        return segments
