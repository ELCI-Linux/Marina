#!/usr/bin/env python3
"""
iPhone Audio Bridge for Marina Agentic Intelligence Framework

This module creates a bridge to receive audio from iPhone and feed it to Marina's
audio processing system, effectively extending Marina's auditory range.
"""

import socket
import threading
import time
import os
import sys
import json
import tempfile
import wave
import pyaudio
from datetime import datetime
from typing import Optional, Callable

# Add Marina's root directory to Python path
MARINA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, MARINA_ROOT)

try:
    from perception.sonic.audio_processor import AudioProcessor
    from perception.sonic.soundscape_detector import SoundscapeDetector
    from perception.sonic.song_recognition import SongRecognitionManager
    MARINA_AUDIO_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Marina audio modules not available: {e}")
    MARINA_AUDIO_AVAILABLE = False

class iPhoneAudioBridge:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.client_socket = None
        self.audio_buffer = []
        self.audio_callbacks = []
        
        # Audio parameters
        self.sample_rate = 44100
        self.channels = 1
        self.chunk_size = 1024
        self.audio_format = pyaudio.paInt16
        
        # Marina integration
        self.audio_processor = None
        self.soundscape_detector = None
        self.song_recognition = None
        self.initialize_marina_audio()
        
    def initialize_marina_audio(self):
        """Initialize Marina's audio processing components"""
        if not MARINA_AUDIO_AVAILABLE:
            print("Marina audio modules not available")
            return
            
        try:
            self.audio_processor = AudioProcessor()
            print("✅ Marina AudioProcessor initialized")
        except Exception as e:
            print(f"⚠️  Could not initialize AudioProcessor: {e}")
            
        try:
            self.soundscape_detector = SoundscapeDetector()
            print("✅ Marina SoundscapeDetector initialized")
        except Exception as e:
            print(f"⚠️  Could not initialize SoundscapeDetector: {e}")
            
        try:
            self.song_recognition = SongRecognitionManager()
            print("✅ Marina SongRecognitionManager initialized")
        except Exception as e:
            print(f"⚠️  Could not initialize SongRecognitionManager: {e}")
    
    def add_audio_callback(self, callback: Callable[[bytes], None]):
        """Add a callback function to process received audio"""
        self.audio_callbacks.append(callback)
    
    def start_server(self):
        """Start the audio bridge server"""
        if self.running:
            print("Server already running")
            return
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            
            self.running = True
            print(f"🎙️  iPhone Audio Bridge started on {self.host}:{self.port}")
            print("📱 Use an iPhone app like 'AudioRelay' or 'WO Mic' to connect")
            print(f"🔗 Connect to: {self.get_local_ip()}:{self.port}")
            
            # Start server thread
            server_thread = threading.Thread(target=self._server_loop, daemon=True)
            server_thread.start()
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            self.running = False
    
    def _server_loop(self):
        """Main server loop to handle client connections"""
        while self.running:
            try:
                print("⏳ Waiting for iPhone connection...")
                client_socket, addr = self.server_socket.accept()
                print(f"📱 iPhone connected from {addr}")
                
                self.client_socket = client_socket
                self._handle_client(client_socket)
                
            except Exception as e:
                if self.running:
                    print(f"❌ Server error: {e}")
                    time.sleep(1)
    
    def _handle_client(self, client_socket):
        """Handle audio data from connected iPhone"""
        try:
            while self.running:
                # Receive audio data
                data = client_socket.recv(self.chunk_size * 2)  # 16-bit audio
                if not data:
                    break
                
                # Process the audio data
                self._process_audio_data(data)
                
                # Call registered callbacks
                for callback in self.audio_callbacks:
                    try:
                        callback(data)
                    except Exception as e:
                        print(f"⚠️  Error in audio callback: {e}")
                        
        except Exception as e:
            print(f"❌ Error handling client: {e}")
        finally:
            client_socket.close()
            self.client_socket = None
            print("📱 iPhone disconnected")
    
    def _process_audio_data(self, audio_data):
        """Process received audio data with Marina's audio system"""
        if not self.audio_processor:
            return
            
        try:
            # Convert bytes to numpy array for processing
            import numpy as np
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Normalize to float32 for processing
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Process with Marina's audio processor
            self.audio_processor.process_audio_chunk(audio_float)
            
            # Analyze soundscape if detector is available
            if self.soundscape_detector:
                try:
                    soundscape = self.soundscape_detector.analyze_audio_chunk(audio_float, self.sample_rate)
                    if soundscape:
                        print(f"🔊 Soundscape detected: {soundscape}")
                except Exception as e:
                    # Soundscape detection might fail, that's ok
                    pass
                    
        except Exception as e:
            print(f"⚠️  Error processing audio: {e}")
    
    def get_local_ip(self):
        """Get the local IP address for iPhone connection"""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    def stop_server(self):
        """Stop the audio bridge server"""
        if not self.running:
            return
            
        self.running = False
        
        if self.client_socket:
            self.client_socket.close()
            
        if self.server_socket:
            self.server_socket.close()
            
        print("🛑 iPhone Audio Bridge stopped")
    
    def get_status(self):
        """Get current bridge status"""
        return {
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'connected': self.client_socket is not None,
            'local_ip': self.get_local_ip(),
            'marina_audio_available': MARINA_AUDIO_AVAILABLE
        }


def main():
    """Main entry point for the iPhone Audio Bridge"""
    import argparse
    
    parser = argparse.ArgumentParser(description='iPhone Audio Bridge for Marina')
    parser.add_argument('--host', default='0.0.0.0', help='Server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8888, help='Server port (default: 8888)')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    
    args = parser.parse_args()
    
    bridge = iPhoneAudioBridge(host=args.host, port=args.port)
    
    if args.status:
        status = bridge.get_status()
        print("📊 iPhone Audio Bridge Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        return
    
    try:
        bridge.start_server()
        
        # Keep the main thread alive
        while bridge.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping iPhone Audio Bridge...")
        bridge.stop_server()


if __name__ == "__main__":
    main()
