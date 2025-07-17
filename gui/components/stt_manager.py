#!/usr/bin/env python3
"""
STT Manager for Marina GUI
Handles speech-to-text functionality using faster-whisper
"""

import os
import time
import threading
import tempfile
import wave
import pyaudio
from enum import Enum
from typing import Callable, Optional, List
import numpy as np

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("faster-whisper not available. Install with: pip install faster-whisper")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("whisper not available. Install with: pip install openai-whisper")

class STTStatus(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    ERROR = "error"

class STTManager:
    def __init__(self, theme_manager, model_size="base", engine="faster-whisper"):
        self.theme_manager = theme_manager
        self.model_size = model_size
        self.engine = engine  # "faster-whisper" or "whisper"
        self.model = None
        self.status = STTStatus.IDLE
        self.is_recording = False
        self.audio_thread = None
        self.status_callbacks = []
        
        # Audio recording parameters
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.audio_format = pyaudio.paInt16
        
        # Audio data storage
        self.audio_frames = []
        self.audio_stream = None
        self.pyaudio_instance = None
        
        # Voice Activity Detection parameters
        self.silence_threshold = 500  # Adjust based on your environment
        self.silence_duration = 2.0  # Stop recording after 2 seconds of silence
        self.min_recording_duration = 1.0  # Minimum recording duration
        
        # Initialize the model
        self.initialize_model()
        
    def initialize_model(self):
        """Initialize the Whisper model"""
        if self.engine == "faster-whisper":
            if not FASTER_WHISPER_AVAILABLE:
                print("faster-whisper not available")
                return
                
            try:
                # Try to use GPU if available, fallback to CPU
                try:
                    self.model = WhisperModel(self.model_size, device="cuda", compute_type="float16")
                    print(f"faster-whisper model '{self.model_size}' loaded on GPU")
                except Exception:
                    self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
                    print(f"faster-whisper model '{self.model_size}' loaded on CPU")
                    
            except Exception as e:
                print(f"Failed to load faster-whisper model: {e}")
                self.model = None
                
        elif self.engine == "whisper":
            if not WHISPER_AVAILABLE:
                print("whisper not available")
                return
                
            try:
                self.model = whisper.load_model(self.model_size)
                print(f"whisper model '{self.model_size}' loaded")
            except Exception as e:
                print(f"Failed to load whisper model: {e}")
                self.model = None
            
    def add_status_callback(self, callback: Callable[[STTStatus], None]):
        """Add a callback for status changes"""
        self.status_callbacks.append(callback)
        
    def _notify_status_change(self, status: STTStatus):
        """Notify all callbacks of status change"""
        self.status = status
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                print(f"Error in STT status callback: {e}")
                
    def is_available(self) -> bool:
        """Check if STT is available"""
        if self.engine == "faster-whisper":
            return FASTER_WHISPER_AVAILABLE and self.model is not None
        elif self.engine == "whisper":
            return WHISPER_AVAILABLE and self.model is not None
        return False
        
    def start_recording(self) -> bool:
        """Start recording audio"""
        if not self.is_available():
            print("STT not available")
            return False
            
        if self.is_recording:
            print("Already recording")
            return False
            
        try:
            # Initialize PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Open audio stream
            self.audio_stream = self.pyaudio_instance.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            # Reset audio frames
            self.audio_frames = []
            self.is_recording = True
            
            # Start recording thread
            self.audio_thread = threading.Thread(target=self._record_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
            self._notify_status_change(STTStatus.LISTENING)
            return True
            
        except Exception as e:
            print(f"Failed to start recording: {e}")
            self._notify_status_change(STTStatus.ERROR)
            return False
            
    def stop_recording(self) -> Optional[str]:
        """Stop recording and transcribe audio"""
        if not self.is_recording:
            return None
            
        self.is_recording = False
        
        # Wait for recording thread to finish
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=5.0)
            
        # Clean up audio stream
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
            self.pyaudio_instance = None
            
        # Transcribe the recorded audio
        return self._transcribe_audio()
        
    def _record_audio(self):
        """Record audio in a separate thread with voice activity detection"""
        silence_start = None
        recording_start = time.time()
        
        try:
            while self.is_recording:
                # Read audio data
                try:
                    data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_frames.append(data)
                    
                    # Simple voice activity detection
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    # Handle potential empty or invalid audio data
                    if len(audio_data) > 0:
                        volume = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
                    else:
                        volume = 0.0
                    
                    current_time = time.time()
                    
                    # Check for silence
                    if volume < self.silence_threshold:
                        if silence_start is None:
                            silence_start = current_time
                        elif (current_time - silence_start > self.silence_duration and 
                              current_time - recording_start > self.min_recording_duration):
                            # Stop recording due to silence
                            break
                    else:
                        # Reset silence timer when voice is detected
                        silence_start = None
                        
                except Exception as e:
                    print(f"Error reading audio: {e}")
                    break
                    
        except Exception as e:
            print(f"Error in recording thread: {e}")
            
        # Stop recording
        self.is_recording = False
        
    def _transcribe_audio(self) -> Optional[str]:
        """Transcribe recorded audio using Whisper"""
        if not self.audio_frames or not self.model:
            return None
            
        try:
            self._notify_status_change(STTStatus.PROCESSING)
            
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
                
                # Write audio data to WAV file
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)  # 16-bit audio = 2 bytes
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(self.audio_frames))
                
            # Transcribe using Whisper
            if self.engine == "faster-whisper":
                segments, info = self.model.transcribe(temp_filename, beam_size=5)
                
                # Combine all segments
                transcription = ""
                for segment in segments:
                    transcription += segment.text + " "
            elif self.engine == "whisper":
                result = self.model.transcribe(temp_filename)
                transcription = result["text"]
                
            # Clean up temporary file
            os.unlink(temp_filename)
            
            # Clean up transcription
            transcription = transcription.strip()
            
            print(f"Transcription: {transcription}")
            self._notify_status_change(STTStatus.IDLE)
            
            return transcription if transcription else None
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            self._notify_status_change(STTStatus.ERROR)
            return None
            
    def toggle_recording(self) -> tuple[bool, Optional[str]]:
        """Toggle recording state. Returns (is_recording, transcription)"""
        if self.is_recording:
            # Stop recording and return transcription
            transcription = self.stop_recording()
            return False, transcription
        else:
            # Start recording
            success = self.start_recording()
            return success, None
            
    def get_status(self) -> STTStatus:
        """Get current STT status"""
        return self.status
        
    def get_available_engines(self) -> List[str]:
        """Get list of available STT engines"""
        engines = []
        if FASTER_WHISPER_AVAILABLE:
            engines.append("faster-whisper")
        if WHISPER_AVAILABLE:
            engines.append("whisper")
        return engines
        
    def set_engine(self, engine: str) -> bool:
        """Set the STT engine (faster-whisper or whisper)"""
        if self.is_recording:
            print("Cannot change engine while recording")
            return False
            
        if engine not in self.get_available_engines():
            print(f"Engine '{engine}' not available")
            return False
            
        if engine == self.engine:
            return True  # Already using this engine
            
        # Clean up current model
        self.model = None
        
        # Set new engine
        self.engine = engine
        
        # Initialize new model
        self.initialize_model()
        
        print(f"STT engine changed to: {engine}")
        return self.model is not None
        
    def get_engine(self) -> str:
        """Get current STT engine"""
        return self.engine
        
    def cleanup(self):
        """Clean up resources"""
        if self.is_recording:
            self.stop_recording()
            
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
