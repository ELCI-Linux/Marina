#!/usr/bin/env python3
"""
Live Translation Module
Real-time speech translation using 5-second audio clips
"""

import numpy as np
import threading
import time
import queue
import logging
from typing import Dict, List, Callable, Optional, Tuple
import tempfile
import os
from datetime import datetime, timedelta

# Translation libraries
try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

class LiveTranslator:
    """Real-time speech translation using 5-second audio clips"""
    
    def __init__(self, target_language: str = 'en', model_size: str = 'base'):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        self.target_language = target_language
        self.model_size = model_size
        
        # Models
        self.speech_model = None
        self.translator = None
        self.speech_engine = None
        
        # Translation state
        self.is_active = False
        self.audio_queue = queue.Queue()
        self.translation_thread = None
        self.translation_callbacks = []
        
        # Audio parameters
        self.sample_rate = 16000
        self.clip_duration = 5.0  # 5 seconds
        self.clip_samples = int(self.clip_duration * self.sample_rate)
        
        # Translation history
        self.translation_history = []
        self.max_history = 50
        
        # Initialize components
        self._initialize_models()
        
    def _initialize_models(self):
        """Initialize speech recognition and translation models"""
        # Initialize speech recognition
        if FASTER_WHISPER_AVAILABLE:
            try:
                self.speech_model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                self.speech_engine = "faster-whisper"
                self.logger.info(f"Initialized faster-whisper model: {self.model_size}")
            except Exception as e:
                self.logger.error(f"Failed to initialize faster-whisper: {e}")
        
        if not self.speech_model and WHISPER_AVAILABLE:
            try:
                self.speech_model = whisper.load_model(self.model_size)
                self.speech_engine = "whisper"
                self.logger.info(f"Initialized whisper model: {self.model_size}")
            except Exception as e:
                self.logger.error(f"Failed to initialize whisper: {e}")
        
        # Initialize translator
        if GOOGLETRANS_AVAILABLE:
            try:
                self.translator = Translator()
                self.logger.info("Initialized Google Translator")
            except Exception as e:
                self.logger.error(f"Failed to initialize translator: {e}")
        
    def add_translation_callback(self, callback: Callable[[Dict], None]):
        """Add callback for translation results"""
        self.translation_callbacks.append(callback)
    
    def remove_translation_callback(self, callback: Callable[[Dict], None]):
        """Remove translation callback"""
        if callback in self.translation_callbacks:
            self.translation_callbacks.remove(callback)
    
    def _notify_translation_callbacks(self, translation_result: Dict):
        """Notify all callbacks of new translation"""
        for callback in self.translation_callbacks:
            try:
                callback(translation_result)
            except Exception as e:
                self.logger.error(f"Translation callback error: {e}")
    
    def start_translation(self, source_language: Optional[str] = None) -> bool:
        """Start live translation"""
        if not self.is_available():
            self.logger.error("Translation not available - missing dependencies")
            return False
        
        if self.is_active:
            self.logger.warning("Translation already active")
            return True
        
        self.is_active = True
        self.source_language = source_language  # None for auto-detect
        
        # Start translation thread
        self.translation_thread = threading.Thread(target=self._translation_worker)
        self.translation_thread.daemon = True
        self.translation_thread.start()
        
        self.logger.info(f"Started live translation to {self.target_language}")
        return True
    
    def stop_translation(self):
        """Stop live translation"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # Wait for translation thread to finish
        if self.translation_thread and self.translation_thread.is_alive():
            self.translation_thread.join(timeout=3.0)
        
        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        self.logger.info("Stopped live translation")
    
    def add_audio_clip(self, audio_data: np.ndarray, sample_rate: int, timestamp: Optional[float] = None):
        """Add audio clip for translation"""
        if not self.is_active:
            return
        
        if timestamp is None:
            timestamp = time.time()
        
        # Resample if needed
        if sample_rate != self.sample_rate:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=self.sample_rate)
        
        # Ensure clip is exactly 5 seconds
        if len(audio_data) > self.clip_samples:
            audio_data = audio_data[:self.clip_samples]
        elif len(audio_data) < self.clip_samples:
            # Pad with zeros
            audio_data = np.pad(audio_data, (0, self.clip_samples - len(audio_data)))
        
        # Add to queue
        try:
            self.audio_queue.put((audio_data, timestamp), timeout=0.1)
        except queue.Full:
            self.logger.warning("Audio queue full - dropping clip")
    
    def _translation_worker(self):
        """Background thread for processing audio clips"""
        while self.is_active:
            try:
                # Get audio clip with timeout
                audio_data, timestamp = self.audio_queue.get(timeout=1.0)
                
                # Process the audio clip
                translation_result = self._process_audio_clip(audio_data, timestamp)
                
                if translation_result:
                    # Add to history
                    self.translation_history.append(translation_result)
                    if len(self.translation_history) > self.max_history:
                        self.translation_history.pop(0)
                    
                    # Notify callbacks
                    self._notify_translation_callbacks(translation_result)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Translation worker error: {e}")
    
    def _process_audio_clip(self, audio_data: np.ndarray, timestamp: float) -> Optional[Dict]:
        """Process a single audio clip for translation"""
        try:
            # Check if audio contains speech
            if not self._has_speech(audio_data):
                return None
            
            # Transcribe audio
            transcription_result = self._transcribe_audio(audio_data)
            if not transcription_result or not transcription_result.get('text'):
                return None
            
            original_text = transcription_result['text'].strip()
            source_language = transcription_result.get('language', 'unknown')
            
            # Skip if text is too short
            if len(original_text) < 3:
                return None
            
            # Translate if needed
            translated_text = original_text
            if self.translator and source_language != self.target_language:
                try:
                    translation = self.translator.translate(original_text, dest=self.target_language)
                    translated_text = translation.text
                except Exception as e:
                    self.logger.error(f"Translation failed: {e}")
                    translated_text = original_text
            
            return {
                'timestamp': timestamp,
                'original_text': original_text,
                'translated_text': translated_text,
                'source_language': source_language,
                'target_language': self.target_language,
                'confidence': transcription_result.get('confidence', 0.0),
                'processing_time': time.time() - timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Audio clip processing failed: {e}")
            return None
    
    def _has_speech(self, audio_data: np.ndarray) -> bool:
        """Quick check if audio contains speech"""
        try:
            # Simple energy-based speech detection
            energy = np.sqrt(np.mean(audio_data**2))
            return energy > 0.01  # Threshold for speech presence
        except Exception:
            return False
    
    def _transcribe_audio(self, audio_data: np.ndarray) -> Optional[Dict]:
        """Transcribe audio using speech recognition model"""
        if not self.speech_model:
            return None
        
        try:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
                
                # Save audio to temporary file
                import soundfile as sf
                sf.write(temp_filename, audio_data, self.sample_rate)
            
            # Transcribe using the model
            if self.speech_engine == "faster-whisper":
                segments, info = self.speech_model.transcribe(
                    temp_filename, 
                    language=self.source_language
                )
                
                # Combine all segments
                text = ""
                for segment in segments:
                    text += segment.text + " "
                
                result = {
                    'text': text.strip(),
                    'language': info.language,
                    'confidence': info.language_probability
                }
                
            elif self.speech_engine == "whisper":
                transcription = self.speech_model.transcribe(
                    temp_filename,
                    language=self.source_language
                )
                
                result = {
                    'text': transcription['text'].strip(),
                    'language': transcription.get('language', 'unknown'),
                    'confidence': 1.0  # Whisper doesn't provide confidence
                }
            
            # Clean up temporary file
            os.unlink(temp_filename)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            return None
    
    def get_translation_history(self) -> List[Dict]:
        """Get translation history"""
        return self.translation_history.copy()
    
    def clear_history(self):
        """Clear translation history"""
        self.translation_history.clear()
    
    def get_recent_translations(self, minutes: int = 5) -> List[Dict]:
        """Get translations from the last N minutes"""
        cutoff_time = time.time() - (minutes * 60)
        return [t for t in self.translation_history if t['timestamp'] > cutoff_time]
    
    def set_target_language(self, language_code: str):
        """Set target language for translation"""
        self.target_language = language_code
        self.logger.info(f"Target language set to: {language_code}")
    
    def set_source_language(self, language_code: Optional[str]):
        """Set source language (None for auto-detect)"""
        self.source_language = language_code
        if language_code:
            self.logger.info(f"Source language set to: {language_code}")
        else:
            self.logger.info("Source language set to auto-detect")
    
    def get_supported_languages(self) -> List[Tuple[str, str]]:
        """Get list of supported languages for translation"""
        # Common language codes supported by Google Translate
        return [
            ('en', 'English'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('de', 'German'),
            ('it', 'Italian'),
            ('pt', 'Portuguese'),
            ('ru', 'Russian'),
            ('zh', 'Chinese'),
            ('ja', 'Japanese'),
            ('ko', 'Korean'),
            ('ar', 'Arabic'),
            ('hi', 'Hindi'),
            ('th', 'Thai'),
            ('vi', 'Vietnamese'),
            ('nl', 'Dutch'),
            ('sv', 'Swedish'),
            ('da', 'Danish'),
            ('no', 'Norwegian'),
            ('fi', 'Finnish'),
            ('pl', 'Polish'),
            ('cs', 'Czech'),
            ('hu', 'Hungarian'),
            ('ro', 'Romanian'),
            ('tr', 'Turkish'),
            ('el', 'Greek'),
            ('he', 'Hebrew'),
            ('uk', 'Ukrainian'),
            ('bg', 'Bulgarian'),
            ('hr', 'Croatian'),
            ('sk', 'Slovak'),
            ('sl', 'Slovenian')
        ]
    
    def is_available(self) -> bool:
        """Check if translation is available"""
        return (self.speech_model is not None and 
                (self.translator is not None or self.target_language == 'en'))
    
    def get_status(self) -> Dict[str, any]:
        """Get current translation status"""
        return {
            'is_active': self.is_active,
            'target_language': self.target_language,
            'source_language': getattr(self, 'source_language', None),
            'speech_model_available': self.speech_model is not None,
            'translator_available': self.translator is not None,
            'queue_size': self.audio_queue.qsize() if self.is_active else 0,
            'history_count': len(self.translation_history)
        }
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_translation()
        self.translation_callbacks.clear()
        self.translation_history.clear()
