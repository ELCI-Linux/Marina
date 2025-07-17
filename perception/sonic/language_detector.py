#!/usr/bin/env python3
"""
Language Detection Module
Detects the language of spoken audio using phonetic and acoustic analysis
"""

import numpy as np
import librosa
import logging
from typing import Dict, List, Tuple, Optional
import tempfile
import os

# Try to import language detection libraries
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

class LanguageDetector:
    """Advanced language detection for speech audio"""
    
    def __init__(self, model_size: str = "base"):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        self.model_size = model_size
        self.model = None
        self.engine = None
        
        # Language mappings with flag emojis
        self.language_flags = {
            'en': ('🇺🇸', 'English'),
            'es': ('🇪🇸', 'Spanish'),
            'fr': ('🇫🇷', 'French'),
            'de': ('🇩🇪', 'German'),
            'it': ('🇮🇹', 'Italian'),
            'pt': ('🇵🇹', 'Portuguese'),
            'ru': ('🇷🇺', 'Russian'),
            'zh': ('🇨🇳', 'Chinese'),
            'ja': ('🇯🇵', 'Japanese'),
            'ko': ('🇰🇷', 'Korean'),
            'ar': ('🇸🇦', 'Arabic'),
            'hi': ('🇮🇳', 'Hindi'),
            'th': ('🇹🇭', 'Thai'),
            'vi': ('🇻🇳', 'Vietnamese'),
            'nl': ('🇳🇱', 'Dutch'),
            'sv': ('🇸🇪', 'Swedish'),
            'da': ('🇩🇰', 'Danish'),
            'no': ('🇳🇴', 'Norwegian'),
            'fi': ('🇫🇮', 'Finnish'),
            'pl': ('🇵🇱', 'Polish'),
            'cs': ('🇨🇿', 'Czech'),
            'hu': ('🇭🇺', 'Hungarian'),
            'ro': ('🇷🇴', 'Romanian'),
            'tr': ('🇹🇷', 'Turkish'),
            'el': ('🇬🇷', 'Greek'),
            'he': ('🇮🇱', 'Hebrew'),
            'uk': ('🇺🇦', 'Ukrainian'),
            'bg': ('🇧🇬', 'Bulgarian'),
            'hr': ('🇭🇷', 'Croatian'),
            'sk': ('🇸🇰', 'Slovak'),
            'sl': ('🇸🇮', 'Slovenian'),
            'et': ('🇪🇪', 'Estonian'),
            'lv': ('🇱🇻', 'Latvian'),
            'lt': ('🇱🇹', 'Lithuanian'),
            'mt': ('🇲🇹', 'Maltese'),
            'cy': ('🏴󠁧󠁢󠁷󠁬󠁳󠁿', 'Welsh'),
            'ga': ('🇮🇪', 'Irish'),
            'is': ('🇮🇸', 'Icelandic'),
            'ca': ('🇪🇸', 'Catalan'),
            'eu': ('🇪🇸', 'Basque'),
            'gl': ('🇪🇸', 'Galician'),
            'ms': ('🇲🇾', 'Malay'),
            'id': ('🇮🇩', 'Indonesian'),
            'tl': ('🇵🇭', 'Filipino'),
            'sw': ('🇰🇪', 'Swahili'),
            'yo': ('🇳🇬', 'Yoruba'),
            'zu': ('🇿🇦', 'Zulu'),
            'af': ('🇿🇦', 'Afrikaans'),
            'am': ('🇪🇹', 'Amharic'),
            'az': ('🇦🇿', 'Azerbaijani'),
            'be': ('🇧🇾', 'Belarusian'),
            'bn': ('🇧🇩', 'Bengali'),
            'bs': ('🇧🇦', 'Bosnian'),
            'fa': ('🇮🇷', 'Persian'),
            'gu': ('🇮🇳', 'Gujarati'),
            'ha': ('🇳🇬', 'Hausa'),
            'hy': ('🇦🇲', 'Armenian'),
            'jw': ('🇮🇩', 'Javanese'),
            'ka': ('🇬🇪', 'Georgian'),
            'kk': ('🇰🇿', 'Kazakh'),
            'km': ('🇰🇭', 'Khmer'),
            'kn': ('🇮🇳', 'Kannada'),
            'ku': ('🇮🇶', 'Kurdish'),
            'ky': ('🇰🇬', 'Kyrgyz'),
            'la': ('🇻🇦', 'Latin'),
            'lo': ('🇱🇦', 'Lao'),
            'mk': ('🇲🇰', 'Macedonian'),
            'ml': ('🇮🇳', 'Malayalam'),
            'mn': ('🇲🇳', 'Mongolian'),
            'mr': ('🇮🇳', 'Marathi'),
            'my': ('🇲🇲', 'Myanmar'),
            'ne': ('🇳🇵', 'Nepali'),
            'pa': ('🇮🇳', 'Punjabi'),
            'ps': ('🇦🇫', 'Pashto'),
            'si': ('🇱🇰', 'Sinhala'),
            'sq': ('🇦🇱', 'Albanian'),
            'sr': ('🇷🇸', 'Serbian'),
            'su': ('🇮🇩', 'Sundanese'),
            'ta': ('🇮🇳', 'Tamil'),
            'te': ('🇮🇳', 'Telugu'),
            'tg': ('🇹🇯', 'Tajik'),
            'tk': ('🇹🇲', 'Turkmen'),
            'tt': ('🇷🇺', 'Tatar'),
            'ug': ('🇨🇳', 'Uyghur'),
            'ur': ('🇵🇰', 'Urdu'),
            'uz': ('🇺🇿', 'Uzbek'),
            'xh': ('🇿🇦', 'Xhosa'),
            'yi': ('🇮🇱', 'Yiddish')
        }
        
        # Initialize model
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the language detection model"""
        if FASTER_WHISPER_AVAILABLE:
            try:
                self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                self.engine = "faster-whisper"
                self.logger.info(f"Initialized faster-whisper model: {self.model_size}")
                return
            except Exception as e:
                self.logger.error(f"Failed to initialize faster-whisper: {e}")
        
        if WHISPER_AVAILABLE:
            try:
                self.model = whisper.load_model(self.model_size)
                self.engine = "whisper"
                self.logger.info(f"Initialized whisper model: {self.model_size}")
                return
            except Exception as e:
                self.logger.error(f"Failed to initialize whisper: {e}")
        
        self.logger.warning("No language detection model available")
    
    def detect_language(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, any]:
        """
        Detect the language of spoken audio
        
        Args:
            audio_data: Audio signal
            sample_rate: Sample rate of audio
            
        Returns:
            Dictionary with language detection results
        """
        if not self.model:
            return self._fallback_language_detection(audio_data, sample_rate)
        
        try:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
                
                # Resample to 16kHz if needed (Whisper requirement)
                if sample_rate != 16000:
                    audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
                
                # Save audio to temporary file
                import soundfile as sf
                sf.write(temp_filename, audio_data, 16000)
            
            # Detect language using the model
            if self.engine == "faster-whisper":
                segments, info = self.model.transcribe(temp_filename, language=None)
                detected_language = info.language
                confidence = info.language_probability
                
            elif self.engine == "whisper":
                # Load and pad/trim audio for whisper
                audio = whisper.load_audio(temp_filename)
                audio = whisper.pad_or_trim(audio)
                
                # Detect language
                mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
                _, probs = self.model.detect_language(mel)
                detected_language = max(probs, key=probs.get)
                confidence = probs[detected_language]
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            # Get flag and language name
            flag, language_name = self.language_flags.get(detected_language, ('🏳️', 'Unknown'))
            
            return {
                'language_code': detected_language,
                'language_name': language_name,
                'flag': flag,
                'confidence': confidence,
                'success': True,
                'method': 'whisper'
            }
            
        except Exception as e:
            self.logger.error(f"Language detection failed: {e}")
            return self._fallback_language_detection(audio_data, sample_rate)
    
    def _fallback_language_detection(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, any]:
        """Fallback language detection using acoustic features"""
        try:
            # Extract basic acoustic features
            features = self._extract_language_features(audio_data, sample_rate)
            
            # Simple heuristic-based language detection
            detected_language = self._heuristic_language_detection(features)
            
            flag, language_name = self.language_flags.get(detected_language, ('🏳️', 'Unknown'))
            
            return {
                'language_code': detected_language,
                'language_name': language_name,
                'flag': flag,
                'confidence': 0.5,  # Lower confidence for fallback
                'success': True,
                'method': 'heuristic'
            }
            
        except Exception as e:
            self.logger.error(f"Fallback language detection failed: {e}")
            return {
                'language_code': 'en',
                'language_name': 'English',
                'flag': '🇺🇸',
                'confidence': 0.1,
                'success': False,
                'method': 'default'
            }
    
    def _extract_language_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Extract acoustic features that can help identify language"""
        features = {}
        
        try:
            # Pitch-related features (different languages have different pitch patterns)
            f0 = librosa.yin(audio_data, fmin=50, fmax=400, sr=sample_rate)
            f0_clean = f0[f0 > 0]
            
            if len(f0_clean) > 0:
                features['pitch_mean'] = np.mean(f0_clean)
                features['pitch_std'] = np.std(f0_clean)
                features['pitch_range'] = np.max(f0_clean) - np.min(f0_clean)
            
            # Spectral features (different languages have different spectral characteristics)
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)
            features['spectral_centroid_mean'] = np.mean(spectral_centroid)
            features['spectral_centroid_std'] = np.std(spectral_centroid)
            
            # Formant-like features
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            features['mfcc_mean'] = np.mean(mfccs)
            features['mfcc_std'] = np.std(mfccs)
            
            # Rhythm and timing features
            tempo, beats = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            features['tempo'] = tempo
            
            # Zero crossing rate (consonant patterns)
            zcr = librosa.feature.zero_crossing_rate(audio_data)
            features['zcr_mean'] = np.mean(zcr)
            features['zcr_std'] = np.std(zcr)
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            
        return features
    
    def _heuristic_language_detection(self, features: Dict[str, float]) -> str:
        """Simple heuristic-based language detection using acoustic features"""
        # This is a simplified heuristic - in practice, you'd use trained models
        
        pitch_mean = features.get('pitch_mean', 150)
        pitch_std = features.get('pitch_std', 20)
        spectral_centroid = features.get('spectral_centroid_mean', 2000)
        zcr_mean = features.get('zcr_mean', 0.1)
        
        # Simple rules based on typical language characteristics
        if pitch_mean > 200 and pitch_std > 30:
            # High pitch variation - might be tonal language
            return 'zh'  # Chinese
        elif pitch_mean > 180 and spectral_centroid > 2500:
            # High pitch and bright spectrum - might be Japanese
            return 'ja'
        elif zcr_mean > 0.15:
            # High consonant content - might be German
            return 'de'
        elif pitch_mean < 140 and pitch_std < 25:
            # Low pitch variation - might be English
            return 'en'
        elif spectral_centroid > 2200:
            # Bright spectrum - might be Spanish
            return 'es'
        else:
            # Default to English
            return 'en'
    
    def get_supported_languages(self) -> List[Tuple[str, str, str]]:
        """Get list of supported languages with codes, names, and flags"""
        return [(code, name, flag) for code, (flag, name) in self.language_flags.items()]
    
    def get_language_flag(self, language_code: str) -> str:
        """Get flag emoji for a language code"""
        return self.language_flags.get(language_code, ('🏳️', 'Unknown'))[0]
    
    def get_language_name(self, language_code: str) -> str:
        """Get language name for a language code"""
        return self.language_flags.get(language_code, ('🏳️', 'Unknown'))[1]
    
    def is_available(self) -> bool:
        """Check if language detection is available"""
        return self.model is not None
    
    def get_confidence_threshold(self) -> float:
        """Get minimum confidence threshold for reliable detection"""
        return 0.6
