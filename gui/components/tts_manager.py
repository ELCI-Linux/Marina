#!/usr/bin/env python3
"""
TTS Manager for Marina LLM Chat GUI
Handles text-to-speech with Gemini TTS integration and response scheduling
"""

import os
import sys
import threading
import queue
import time
import tempfile
import wave
import subprocess
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Try to import Gemini TTS
try:
    from google import genai
    from google.genai import types
    GEMINI_TTS_AVAILABLE = True
except ImportError:
    GEMINI_TTS_AVAILABLE = False
    print("Warning: Gemini TTS not available. Install google-genai for TTS functionality.")

# Try to import audio playback libraries
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

class TTSStatus(Enum):
    IDLE = "idle"
    GENERATING = "generating"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"

@dataclass
class TTSRequest:
    text: str
    voice_name: str
    sender: str
    priority: int = 0
    callback: Optional[Callable] = None
    id: Optional[str] = None

class TTSManager:
    def __init__(self, theme_manager=None):
        self.theme_manager = theme_manager
        self.enabled = False
        self.status = TTSStatus.IDLE
        self.current_request = None
        
        # Gemini TTS client
        self.gemini_client = None
        if GEMINI_TTS_AVAILABLE:
            try:
                self.gemini_client = genai.Client()
                print("Gemini TTS client initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Gemini TTS client: {e}")
                self.gemini_client = None
        
        # Request queue and scheduling
        self.request_queue = queue.PriorityQueue()
        self.active_requests = {}
        self.request_counter = 0
        
        # Threading
        self.processor_thread = None
        self.stop_event = threading.Event()
        self.current_playback_process = None
        
        # Voice configuration
        self.voice_mapping = {
            "GPT-4": "Kore",
            "Claude": "Puck", 
            "Gemini": "Zephyr",
            "DeepSeek": "Kore",
            "Mistral": "Puck",
            "LLaMA": "Zephyr",
            "Local": "Kore",
            "System": "Puck"
        }
        
        # Audio settings
        self.volume = 0.8
        self.speech_rate = 1.0
        self.temp_dir = tempfile.mkdtemp(prefix="marina_tts_")
        
        # Status callbacks
        self.status_callbacks = []
        
        # Start the processor thread
        self.start_processor()
        
        print("TTS Manager initialized successfully")
    
    def start_processor(self):
        """Start the TTS processor thread"""
        if self.processor_thread is None or not self.processor_thread.is_alive():
            self.stop_event.clear()
            self.processor_thread = threading.Thread(target=self._process_requests, daemon=True)
            self.processor_thread.start()
    
    def stop_processor(self):
        """Stop the TTS processor thread"""
        self.stop_event.set()
        if self.processor_thread and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=2)
    
    def enable_tts(self):
        """Enable TTS functionality"""
        self.enabled = True
        self.start_processor()
        self._notify_status_change()
    
    def disable_tts(self):
        """Disable TTS functionality"""
        self.enabled = False
        self.stop_current_playback()
        self.clear_queue()
        self._notify_status_change()
    
    def toggle_tts(self):
        """Toggle TTS on/off"""
        if self.enabled:
            self.disable_tts()
        else:
            self.enable_tts()
        return self.enabled
    
    def is_enabled(self) -> bool:
        """Check if TTS is enabled"""
        return self.enabled
    
    def get_status(self) -> TTSStatus:
        """Get current TTS status"""
        return self.status
    
    def speak_text(self, text: str, sender: str = "System", priority: int = 0, callback: Optional[Callable] = None) -> str:
        """Queue text for TTS playback"""
        if not self.enabled or not text.strip():
            return None
        
        # Clean up the text
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return None
        
        # Create request
        request_id = f"tts_{self.request_counter}_{int(time.time())}"
        self.request_counter += 1
        
        voice_name = self.voice_mapping.get(sender, "Kore")
        
        request = TTSRequest(
            text=cleaned_text,
            voice_name=voice_name,
            sender=sender,
            priority=priority,
            callback=callback,
            id=request_id
        )
        
        # Add to queue
        self.request_queue.put((priority, time.time(), request))
        self.active_requests[request_id] = request
        
        print(f"TTS: Queued request {request_id} for {sender}: {cleaned_text[:50]}...")
        return request_id
    
    def stop_current_playback(self):
        """Stop current TTS playback"""
        if self.current_playback_process:
            try:
                self.current_playback_process.terminate()
                self.current_playback_process.wait(timeout=2)
            except:
                try:
                    self.current_playback_process.kill()
                except:
                    pass
            self.current_playback_process = None
        
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.stop()
            except:
                pass
        
        self.status = TTSStatus.STOPPED
        self._notify_status_change()
    
    def clear_queue(self):
        """Clear the TTS request queue"""
        while not self.request_queue.empty():
            try:
                self.request_queue.get_nowait()
            except queue.Empty:
                break
        self.active_requests.clear()
    
    def cancel_request(self, request_id: str):
        """Cancel a specific TTS request"""
        if request_id in self.active_requests:
            del self.active_requests[request_id]
        
        # If it's the current request, stop playback
        if self.current_request and self.current_request.id == request_id:
            self.stop_current_playback()
    
    def set_voice_for_sender(self, sender: str, voice_name: str):
        """Set voice for a specific sender"""
        self.voice_mapping[sender] = voice_name
    
    def set_volume(self, volume: float):
        """Set playback volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        if PYGAME_AVAILABLE:
            pygame.mixer.music.set_volume(self.volume)
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices"""
        return ["Kore", "Puck", "Zephyr", "Charon", "Fenrir", "Aoede"]
    
    def add_status_callback(self, callback: Callable):
        """Add a status change callback"""
        self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable):
        """Remove a status change callback"""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    def _process_requests(self):
        """Main processing loop for TTS requests"""
        while not self.stop_event.is_set():
            try:
                # Get next request with timeout
                try:
                    priority, timestamp, request = self.request_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Check if request is still active
                if request.id not in self.active_requests:
                    continue
                
                # Skip if TTS is disabled
                if not self.enabled:
                    continue
                
                self.current_request = request
                self._process_single_request(request)
                
                # Remove from active requests
                if request.id in self.active_requests:
                    del self.active_requests[request.id]
                
                self.current_request = None
                
            except Exception as e:
                print(f"TTS processing error: {e}")
                self.status = TTSStatus.IDLE
                self._notify_status_change()
    
    def _process_single_request(self, request: TTSRequest):
        """Process a single TTS request"""
        try:
            # Update status
            self.status = TTSStatus.GENERATING
            self._notify_status_change()
            
            # Generate audio
            audio_file = self._generate_audio(request.text, request.voice_name)
            
            if audio_file and os.path.exists(audio_file):
                # Update status
                self.status = TTSStatus.PLAYING
                self._notify_status_change()
                
                # Play audio
                self._play_audio(audio_file)
                
                # Cleanup
                try:
                    os.remove(audio_file)
                except:
                    pass
                
                # Call callback if provided
                if request.callback:
                    request.callback(request.id, True)
            else:
                print(f"TTS: Failed to generate audio for request {request.id}")
                if request.callback:
                    request.callback(request.id, False)
            
        except Exception as e:
            print(f"TTS request processing error: {e}")
            if request.callback:
                request.callback(request.id, False)
        finally:
            self.status = TTSStatus.IDLE
            self._notify_status_change()
    
    def _generate_audio(self, text: str, voice_name: str) -> Optional[str]:
        """Generate audio using Gemini TTS"""
        if not self.gemini_client:
            print("TTS: Gemini client not available")
            return None
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name
                            )
                        )
                    ),
                ),
            )
            
            # Extract audio data
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            
            # Save to temporary file
            audio_file = os.path.join(self.temp_dir, f"tts_{int(time.time())}.wav")
            self._save_wave(audio_file, audio_data)
            
            return audio_file
            
        except Exception as e:
            print(f"TTS generation error: {e}")
            return None
    
    def _save_wave(self, filename: str, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
        """Save PCM data as WAV file"""
        try:
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(rate)
                wf.writeframes(pcm_data)
        except Exception as e:
            print(f"Error saving wave file: {e}")
            raise
    
    def _play_audio(self, audio_file: str):
        """Play audio file"""
        try:
            # Try pygame first
            if PYGAME_AVAILABLE:
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    if self.stop_event.is_set():
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.1)
                return
            
            # Try playsound
            if PLAYSOUND_AVAILABLE:
                playsound.playsound(audio_file)
                return
            
            # Fallback to system audio player
            if sys.platform.startswith('linux'):
                self.current_playback_process = subprocess.Popen(
                    ['aplay', audio_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.current_playback_process.wait()
            elif sys.platform.startswith('darwin'):
                self.current_playback_process = subprocess.Popen(
                    ['afplay', audio_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.current_playback_process.wait()
            elif sys.platform.startswith('win'):
                self.current_playback_process = subprocess.Popen(
                    ['powershell', '-c', f'(New-Object Media.SoundPlayer "{audio_file}").PlaySync()'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.current_playback_process.wait()
            
        except Exception as e:
            print(f"Audio playback error: {e}")
        finally:
            self.current_playback_process = None
    
    def _clean_text(self, text: str) -> str:
        """Clean text for TTS processing"""
        # Remove markdown formatting
        import re
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`.*?`', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.,!?;:\-\(\)]', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit length
        if len(text) > 1000:
            text = text[:1000] + "..."
        
        return text
    
    def _notify_status_change(self):
        """Notify status change callbacks"""
        for callback in self.status_callbacks:
            try:
                callback(self.status, self.enabled)
            except Exception as e:
                print(f"Status callback error: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_processor()
        self.stop_current_playback()
        
        # Clean up temporary files
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def __del__(self):
        """Destructor"""
        self.cleanup()

# Example usage
if __name__ == "__main__":
    tts = TTSManager()
    tts.enable_tts()
    
    # Test TTS
    def callback(request_id, success):
        print(f"TTS callback: {request_id} - {'Success' if success else 'Failed'}")
    
    tts.speak_text("Hello, this is a test of the TTS system.", "System", callback=callback)
    
    # Wait for completion
    time.sleep(5)
    tts.cleanup()
