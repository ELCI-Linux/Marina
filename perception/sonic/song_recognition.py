#!/usr/bin/env python3
"""
Song Recognition Module for Marina
Automatically records audio every 45 seconds and identifies songs using Shazam
"""

import asyncio
import pyaudio
import wave
import tempfile
import os
import threading
import time
import json
from datetime import datetime
from typing import Optional, Callable, Tuple
from shazamio import Shazam
from .soundscape_detector import SoundscapeDetector, SoundscapeResult

class SongRecognitionManager:
    def __init__(self, recognition_interval=45):
        self.recognition_interval = recognition_interval
        self.is_running = False
        self.recognition_thread = None
        self.current_song = None
        self.current_artist = None
        self.last_recognition_time = 0
        self.callbacks = []
        self.status_callbacks = []
        self.soundscape_callbacks = []
        
        # Audio recording parameters
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.record_duration = 10  # seconds
        
        # Initialize Shazam
        self.shazam = Shazam()
        
        # Initialize soundscape detector
        self.soundscape_detector = SoundscapeDetector()
        self.current_soundscape = None
        
        # File paths
        self.likes_file = os.path.expanduser("~/Marina/memory/likes/music.json")
        self.soundscape_file = os.path.expanduser("~/Marina/memory/soundscape/analysis.json")
        self.revisions_file = os.path.expanduser("~/Marina/memory/revisions/song_revisions.json")
        
    def add_callback(self, callback: Callable[[Optional[str], Optional[str]], None]):
        """Add a callback function to be called when song is recognized"""
        self.callbacks.append(callback)
        
    def remove_callback(self, callback: Callable[[Optional[str], Optional[str]], None]):
        """Remove a callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            
    def add_status_callback(self, callback: Callable[[str, dict], None]):
        """Add a status callback function"""
        self.status_callbacks.append(callback)
        
    def remove_status_callback(self, callback: Callable[[str, dict], None]):
        """Remove a status callback function"""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
            
    def add_soundscape_callback(self, callback: Callable[[SoundscapeResult], None]):
        """Add a soundscape callback function"""
        self.soundscape_callbacks.append(callback)
        
    def remove_soundscape_callback(self, callback: Callable[[SoundscapeResult], None]):
        """Remove a soundscape callback function"""
        if callback in self.soundscape_callbacks:
            self.soundscape_callbacks.remove(callback)
            
    def _notify_callbacks(self, song_name: Optional[str], artist_name: Optional[str]):
        """Notify all callbacks about song recognition result"""
        for callback in self.callbacks:
            try:
                callback(song_name, artist_name)
            except Exception as e:
                print(f"Error in song recognition callback: {e}")
                
    def _notify_status_callbacks(self, status: str, data: dict = None):
        """Notify all status callbacks about recognition status"""
        if data is None:
            data = {}
        for callback in self.status_callbacks:
            try:
                callback(status, data)
            except Exception as e:
                print(f"Error in song recognition status callback: {e}")
                
    def record_audio(self) -> Optional[str]:
        """Record audio from microphone and save to temporary file"""
        try:
            # Initialize PyAudio
            audio = pyaudio.PyAudio()
            
            # Open stream
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            
            # Record audio
            for i in range(0, int(self.sample_rate / self.chunk_size * self.record_duration)):
                if not self.is_running:  # Check if we should stop
                    break
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
            
            # Stop and close stream
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            if not frames:
                return None
                
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_filename = temp_file.name
            temp_file.close()
            
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
            
            return temp_filename
            
        except Exception as e:
            print(f"Error recording audio: {e}")
            return None
            
    async def recognize_audio(self, audio_file: str) -> Tuple[Optional[str], Optional[str]]:
        """Recognize audio using Shazam"""
        try:
            result = await self.shazam.recognize(audio_file)
            
            if result and 'track' in result:
                track = result['track']
                track_name = track.get('title', 'Unknown')
                artist_name = track.get('subtitle', 'Unknown')
                print(f"🎵 Detected: {track_name} by {artist_name}")
                return track_name, artist_name
            else:
                print("🔍 No song match found")
                return None, None
                
        except Exception as e:
            print(f"Error during song recognition: {e}")
            return None, None
            
    async def _recognition_cycle(self):
        """Single recognition cycle - record and recognize"""
        audio_file = None
        try:
            # Notify start of recording
            self._notify_status_callbacks("recording", {"duration": self.record_duration})
            
            # Record audio
            audio_file = self.record_audio()
            if not audio_file:
                self._notify_status_callbacks("error", {"message": "Failed to record audio"})
                return
                
            # Notify start of recognition
            self._notify_status_callbacks("recognizing", {})
            
            # Recognize the audio
            song_name, artist_name = await self.recognize_audio(audio_file)
            
            # Check for known misidentifications and auto-correct
            if song_name and artist_name:
                corrected_info = self.check_for_known_misidentification(song_name, artist_name)
                if corrected_info:
                    corrected_song, corrected_artist = corrected_info
                    print(f"🔄 Auto-corrected: {song_name} by {artist_name} → {corrected_song} by {corrected_artist}")
                    song_name, artist_name = corrected_song, corrected_artist
            
            # Update current song info
            self.current_song = song_name
            self.current_artist = artist_name
            self.last_recognition_time = time.time()
            
            # Notify result
            if song_name and artist_name:
                self._notify_status_callbacks("recognized", {
                    "song": song_name,
                    "artist": artist_name
                })
            else:
                self._notify_status_callbacks("no_match", {})
            
            # Notify callbacks
            self._notify_callbacks(song_name, artist_name)
            
            # After song recognition, perform soundscape detection
            await self._analyze_soundscape(audio_file)
            
        except Exception as e:
            print(f"Error in recognition cycle: {e}")
            self._notify_status_callbacks("error", {"message": str(e)})
        finally:
            # Clean up temporary file
            if audio_file:
                try:
                    os.unlink(audio_file)
                except:
                    pass
            
    def _recognition_loop(self):
        """Main recognition loop that runs in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while self.is_running:
                # Run recognition cycle
                loop.run_until_complete(self._recognition_cycle())
                
                # Wait for the next cycle with countdown updates
                for remaining in range(self.recognition_interval, 0, -1):
                    if not self.is_running:
                        break
                    
                    # Send countdown status update
                    self._notify_status_callbacks("waiting", {
                        "remaining_seconds": remaining,
                        "total_interval": self.recognition_interval
                    })
                    
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Error in recognition loop: {e}")
        finally:
            loop.close()
            
    def start(self):
        """Start the song recognition service"""
        if self.is_running:
            print("Song recognition already running")
            return
            
        self.is_running = True
        self.recognition_thread = threading.Thread(target=self._recognition_loop, daemon=True)
        self.recognition_thread.start()
        print(f"🎵 Song recognition started (checking every {self.recognition_interval} seconds)")
        
    def stop(self):
        """Stop the song recognition service"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self.recognition_thread:
            self.recognition_thread.join(timeout=5)
        print("🎵 Song recognition stopped")
        
    def get_current_song(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the currently recognized song"""
        return self.current_song, self.current_artist
        
    def get_last_recognition_time(self) -> float:
        """Get the timestamp of the last recognition attempt"""
        return self.last_recognition_time
        
    def is_song_info_fresh(self, max_age_seconds: int = 60) -> bool:
        """Check if the current song info is fresh (within max_age_seconds)"""
        if self.last_recognition_time == 0:
            return False
        return (time.time() - self.last_recognition_time) < max_age_seconds
        
    def _load_likes(self) -> dict:
        """Load liked songs from JSON file"""
        try:
            if os.path.exists(self.likes_file):
                with open(self.likes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"liked_songs": []}
        except Exception as e:
            print(f"Error loading likes: {e}")
            return {"liked_songs": []}
            
    def _save_likes(self, likes_data: dict) -> bool:
        """Save liked songs to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.likes_file), exist_ok=True)
            
            with open(self.likes_file, 'w', encoding='utf-8') as f:
                json.dump(likes_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving likes: {e}")
            return False
            
    def like_current_song(self) -> bool:
        """Like the currently recognized song"""
        if not self.current_song or not self.current_artist:
            print("No current song to like")
            return False
            
        try:
            # Load existing likes
            likes_data = self._load_likes()
            
            # Create song entry
            song_entry = {
                "song": self.current_song,
                "artist": self.current_artist,
                "liked_at": datetime.now().isoformat(),
                "recognition_time": self.last_recognition_time
            }
            
            # Check if song is already liked
            existing_song = None
            for liked_song in likes_data["liked_songs"]:
                if (liked_song["song"].lower() == self.current_song.lower() and 
                    liked_song["artist"].lower() == self.current_artist.lower()):
                    existing_song = liked_song
                    break
            
            if existing_song:
                # Update existing entry
                existing_song["liked_at"] = song_entry["liked_at"]
                existing_song["recognition_time"] = song_entry["recognition_time"]
                print(f"❤️  Updated like for: {self.current_song} by {self.current_artist}")
            else:
                # Add new entry
                likes_data["liked_songs"].append(song_entry)
                print(f"❤️  Liked: {self.current_song} by {self.current_artist}")
            
            # Save to file
            if self._save_likes(likes_data):
                return True
            else:
                print("Failed to save like")
                return False
                
        except Exception as e:
            print(f"Error liking song: {e}")
            return False
            
    def unlike_current_song(self) -> bool:
        """Unlike the currently recognized song"""
        if not self.current_song or not self.current_artist:
            print("No current song to unlike")
            return False
            
        try:
            # Load existing likes
            likes_data = self._load_likes()
            
            # Find and remove the song
            original_count = len(likes_data["liked_songs"])
            likes_data["liked_songs"] = [
                song for song in likes_data["liked_songs"]
                if not (song["song"].lower() == self.current_song.lower() and 
                       song["artist"].lower() == self.current_artist.lower())
            ]
            
            if len(likes_data["liked_songs"]) < original_count:
                print(f"💔 Unliked: {self.current_song} by {self.current_artist}")
                return self._save_likes(likes_data)
            else:
                print(f"Song not found in likes: {self.current_song} by {self.current_artist}")
                return False
                
        except Exception as e:
            print(f"Error unliking song: {e}")
            return False
            
    def is_current_song_liked(self) -> bool:
        """Check if the current song is liked"""
        if not self.current_song or not self.current_artist:
            return False
            
        try:
            likes_data = self._load_likes()
            for liked_song in likes_data["liked_songs"]:
                if (liked_song["song"].lower() == self.current_song.lower() and 
                    liked_song["artist"].lower() == self.current_artist.lower()):
                    return True
            return False
        except Exception as e:
            print(f"Error checking if song is liked: {e}")
            return False
            
    def get_liked_songs(self) -> list:
        """Get all liked songs"""
        try:
            likes_data = self._load_likes()
            return likes_data["liked_songs"]
        except Exception as e:
            print(f"Error getting liked songs: {e}")
            return []
            
    async def _analyze_soundscape(self, audio_file: str):
        """Analyze soundscape using the same audio file from song recognition"""
        try:
            # Notify start of soundscape analysis
            self._notify_status_callbacks("analyzing_soundscape", {})
            
            # Run soundscape analysis in a separate thread to avoid blocking
            def analyze():
                return self.soundscape_detector.analyze_audio_file(audio_file)
            
            # Use thread executor to run the analysis
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(analyze)
                soundscape_result = future.result(timeout=30)  # 30 second timeout
            
            if soundscape_result:
                # Update current soundscape
                self.current_soundscape = soundscape_result
                
                # Save results to file
                self.soundscape_detector.save_results(soundscape_result, self.soundscape_file)
                
                # Notify callbacks
                self._notify_soundscape_callbacks(soundscape_result)
                
                # Notify status with summary
                self._notify_status_callbacks("soundscape_analyzed", {
                    "environment": soundscape_result.environment_type,
                    "confidence": soundscape_result.confidence,
                    "sound_events": soundscape_result.sound_events,
                    "noise_level": soundscape_result.noise_level,
                    "description": soundscape_result.description
                })
                
                print(f"🎧 Soundscape: {soundscape_result.description}")
                
            else:
                self._notify_status_callbacks("soundscape_error", {"message": "Failed to analyze soundscape"})
                
        except Exception as e:
            print(f"Error in soundscape analysis: {e}")
            self._notify_status_callbacks("soundscape_error", {"message": str(e)})
            
    def _notify_soundscape_callbacks(self, soundscape_result: SoundscapeResult):
        """Notify all soundscape callbacks"""
        for callback in self.soundscape_callbacks:
            try:
                callback(soundscape_result)
            except Exception as e:
                print(f"Error in soundscape callback: {e}")
                
    def get_current_soundscape(self) -> Optional[SoundscapeResult]:
        """Get the current soundscape analysis result"""
        return self.current_soundscape
        
    def get_soundscape_history(self) -> list:
        """Get soundscape analysis history"""
        try:
            if os.path.exists(self.soundscape_file):
                with open(self.soundscape_file, 'r') as f:
                    data = json.load(f)
                    return data.get('soundscape_history', [])
            return []
        except Exception as e:
            print(f"Error loading soundscape history: {e}")
            return []
            
    def get_status(self) -> dict:
        """Get the current status of the song recognition service"""
        return {
            'running': self.is_running,
            'current_song': self.current_song,
            'current_artist': self.current_artist,
            'last_recognition_time': self.last_recognition_time,
            'recognition_interval': self.recognition_interval,
            'is_fresh': self.is_song_info_fresh()
        }
        
    def _load_revisions(self) -> dict:
        """Load song revisions from JSON file"""
        try:
            if os.path.exists(self.revisions_file):
                with open(self.revisions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"revisions": []}
        except Exception as e:
            print(f"Error loading revisions: {e}")
            return {"revisions": []}
            
    def _save_revisions(self, revisions_data: dict) -> bool:
        """Save song revisions to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.revisions_file), exist_ok=True)
            
            with open(self.revisions_file, 'w', encoding='utf-8') as f:
                json.dump(revisions_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving revisions: {e}")
            return False
            
    def revise_current_song(self, correct_song: str, correct_artist: str, revision_reason: str = "User correction") -> bool:
        """Revise the current song recognition with correct information"""
        if not self.current_song or not self.current_artist:
            print("No current song to revise")
            return False
            
        try:
            # Load existing revisions
            revisions_data = self._load_revisions()
            
            # Create revision entry
            revision_entry = {
                "original_song": self.current_song,
                "original_artist": self.current_artist,
                "corrected_song": correct_song,
                "corrected_artist": correct_artist,
                "revision_reason": revision_reason,
                "revised_at": datetime.now().isoformat(),
                "recognition_time": self.last_recognition_time
            }
            
            # Add revision to list
            revisions_data["revisions"].append(revision_entry)
            
            # Save to file
            if self._save_revisions(revisions_data):
                # Update current song info
                old_song = f"{self.current_song} by {self.current_artist}"
                self.current_song = correct_song
                self.current_artist = correct_artist
                new_song = f"{correct_song} by {correct_artist}"
                
                print(f"✏️  Revised: {old_song} → {new_song}")
                
                # Notify callbacks with corrected information
                self._notify_callbacks(correct_song, correct_artist)
                
                return True
            else:
                print("Failed to save revision")
                return False
                
        except Exception as e:
            print(f"Error revising song: {e}")
            return False
            
    def get_revisions(self) -> list:
        """Get all song revisions"""
        try:
            revisions_data = self._load_revisions()
            return revisions_data["revisions"]
        except Exception as e:
            print(f"Error getting revisions: {e}")
            return []
            
    def get_revision_suggestions(self, song_name: str, artist_name: str) -> list:
        """Get revision suggestions based on historical corrections"""
        try:
            revisions_data = self._load_revisions()
            suggestions = []
            
            for revision in revisions_data["revisions"]:
                # Check if this is a common misidentification
                if (revision["original_song"].lower() == song_name.lower() and 
                    revision["original_artist"].lower() == artist_name.lower()):
                    suggestion = {
                        "song": revision["corrected_song"],
                        "artist": revision["corrected_artist"],
                        "reason": revision["revision_reason"],
                        "revised_at": revision["revised_at"]
                    }
                    if suggestion not in suggestions:
                        suggestions.append(suggestion)
                        
            return suggestions
        except Exception as e:
            print(f"Error getting revision suggestions: {e}")
            return []
            
    def check_for_known_misidentification(self, song_name: str, artist_name: str) -> Optional[Tuple[str, str]]:
        """Check if a song is a known misidentification and return correct info"""
        try:
            revisions_data = self._load_revisions()
            
            for revision in revisions_data["revisions"]:
                if (revision["original_song"].lower() == song_name.lower() and 
                    revision["original_artist"].lower() == artist_name.lower()):
                    return revision["corrected_song"], revision["corrected_artist"]
                    
            return None
        except Exception as e:
            print(f"Error checking for misidentification: {e}")
            return None

# For testing/standalone usage
if __name__ == "__main__":
    def on_song_recognized(song_name, artist_name):
        if song_name and artist_name:
            print(f"🎵 Now Playing: {song_name} by {artist_name}")
        else:
            print("🔍 No song detected")
    
    manager = SongRecognitionManager(recognition_interval=45)
    manager.add_callback(on_song_recognized)
    
    try:
        manager.start()
        print("Song recognition service started. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping song recognition service...")
        manager.stop()
        print("Service stopped.")
