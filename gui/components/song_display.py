#!/usr/bin/env python3
"""
Song Display Widget for Marina
Shows currently playing song with album art in the main window
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
from typing import Optional, Tuple
from .album_art_fetcher import AlbumArtFetcher
from perception.sonic.speech_detector import SpeechDetector
from perception.sonic.language_detector import LanguageDetector
from perception.sonic.live_translator import LiveTranslator
import pyaudio
import numpy as np

class SongDisplayWidget:
    def __init__(self, parent_frame, theme_manager):
        self.parent_frame = parent_frame
        self.theme_manager = theme_manager
        
        # Album art fetcher
        self.art_fetcher = AlbumArtFetcher()
        
        # Current song info
        self.current_song = None
        self.current_artist = None
        self.current_album_art = None
        
        # Song recognition manager reference (will be set later)
        self.song_recognition_manager = None
        
        # Current display mode: 'song', 'soundscape', or 'speech'
        self.display_mode = 'song'
        
        # Speech detection and translation
        self.speech_detector = SpeechDetector()
        self.language_detector = LanguageDetector()
        self.live_translator = LiveTranslator()
        
        # Speech state
        self.current_language = None
        self.translation_active = False
        self.audio_recording = False
        self.audio_thread = None
        self.pyaudio_instance = None
        self.audio_stream = None
        
        # Audio parameters
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.audio_format = pyaudio.paInt16
        
        # UI elements
        self.display_frame = None
        self.album_art_label = None
        self.song_label = None
        self.artist_label = None
        self.like_button = None
        self.left_button = None
        self.right_button = None
        self.mode_indicator = None
        self.ear_button = None
        
        # Create the display widget
        self.create_display()
        
    def create_display(self):
        """Create the song display widget"""
        # Main frame for the song display
        self.display_frame = ttk.Frame(self.parent_frame)
        # Don't pack initially - will be shown when song is detected
        
        # Create a container with border for better visibility
        container = ttk.LabelFrame(self.display_frame, text="🎵 Audio Analysis", padding=10)
        container.pack(fill="x", padx=5, pady=5)
        
        # Navigation header frame
        nav_frame = ttk.Frame(container)
        nav_frame.pack(fill="x", pady=(0, 10))
        
        # Left navigation button
        self.left_button = ttk.Button(
            nav_frame,
            text="◀",
            command=self.navigate_left,
            width=3
        )
        self.left_button.pack(side="left")
        
        # Mode indicator in the center
        self.mode_indicator = ttk.Label(
            nav_frame,
            text="🎵 Song Recognition",
            font=("Ubuntu", 11, "bold"),
            foreground="#4CAF50"
        )
        self.mode_indicator.pack(side="left", padx=(10, 10), expand=True)
        
        # Right navigation button
        self.right_button = ttk.Button(
            nav_frame,
            text="▶",
            command=self.navigate_right,
            width=3
        )
        self.right_button.pack(side="right")
        
        # Create horizontal layout frame
        content_frame = ttk.Frame(container)
        content_frame.pack(fill="x")
        
        # Album art on the left
        self.album_art_label = ttk.Label(content_frame)
        self.album_art_label.pack(side="left", padx=(0, 15))
        
        # Song info on the right
        info_frame = ttk.Frame(content_frame)
        info_frame.pack(side="left", fill="both", expand=True)
        
        # Song name
        self.song_label = ttk.Label(
            info_frame, 
            text="No song playing", 
            font=("Ubuntu", 12, "bold"),
            foreground="#4CAF50"
        )
        self.song_label.pack(anchor="w", pady=(0, 5))
        
        # Artist name
        self.artist_label = ttk.Label(
            info_frame, 
            text="", 
            font=("Ubuntu", 10),
            foreground="#888888"
        )
        self.artist_label.pack(anchor="w")
        
        # Buttons on the right
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(side="right", padx=(15, 0))

        # Like button
        self.like_button = ttk.Button(
            button_frame,
            text="❤️", 
            command=self.toggle_like, 
            width=3
        )
        self.like_button.pack()

        # Revision button
        self.revision_button = ttk.Button(
            button_frame,
            text="✏️",
            command=self.open_revision_dialog,
            width=3
        )
        self.revision_button.pack(pady=(5, 0))

        # Close button under revision
        close_button = ttk.Button(
            button_frame,
            text="✕",
            command=self.hide_display,
            width=3
        )
        close_button.pack(pady=(5, 0))

        # Set default album art
        self._set_default_album_art()
        
    def _set_default_album_art(self):
        """Set default album art placeholder"""
        try:
            # Get default image from art fetcher
            default_image = self.art_fetcher._get_default_image((64, 64))
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(default_image)
            
            # Store reference to prevent garbage collection
            self.current_album_art = photo
            
            # Update label
            if self.album_art_label:
                self.album_art_label.config(image=photo)
                print(f"Set default album art: {default_image.size}")
                
        except Exception as e:
            print(f"Error setting default album art: {e}")
            # Fallback to simple colored rectangle
            try:
                fallback_image = Image.new('RGB', (64, 64), color='#4CAF50')
                photo = ImageTk.PhotoImage(fallback_image)
                self.current_album_art = photo
                if self.album_art_label:
                    self.album_art_label.config(image=photo)
            except Exception as e2:
                print(f"Error with fallback album art: {e2}")
            
    def _update_album_art(self, image: Image.Image):
        """Update album art display"""
        try:
            print(f"Updating album art with image: {image.size}, mode: {image.mode}")
            
            # Convert PIL Image to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Store reference to prevent garbage collection
            self.current_album_art = photo
            
            # Update label on main thread
            if self.album_art_label:
                self.album_art_label.after(0, lambda: self.album_art_label.config(image=photo))
                print(f"Album art updated successfully")
            else:
                print("Album art label not found")
                
        except Exception as e:
            print(f"Error updating album art: {e}")
            import traceback
            traceback.print_exc()
            
    def update_song(self, song_name: str, artist_name: str):
        """Update the currently displayed song"""
        self.current_song = song_name
        self.current_artist = artist_name
        
        # Update text labels
        if self.song_label:
            self.song_label.config(text=song_name or "Unknown Song")
            
        if self.artist_label:
            self.artist_label.config(text=f"by {artist_name}" if artist_name else "Unknown Artist")
            
        # Update like button state
        self._update_like_button()
            
        # Fetch album art asynchronously
        if song_name and artist_name:
            self.art_fetcher.fetch_album_art_async(
                song_name, 
                artist_name, 
                self._update_album_art,
                size=(64, 64)
            )
        else:
            self._set_default_album_art()
            
        # Show the display
        self.show_display()
        
    def show_display(self):
        """Show the song display widget"""
        if self.display_frame:
            self.display_frame.pack(fill="x", padx=5, pady=(0, 5))
            
    def hide_display(self):
        """Hide the song display widget"""
        if self.display_frame:
            self.display_frame.pack_forget()
            
    def is_visible(self) -> bool:
        """Check if the display is currently visible"""
        return self.display_frame and self.display_frame.winfo_viewable()
        
    def get_current_song(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the current song info"""
        return self.current_song, self.current_artist
        
    def clear_song(self):
        """Clear the current song display"""
        self.current_song = None
        self.current_artist = None
        
        if self.song_label:
            self.song_label.config(text="No song playing")
            
        if self.artist_label:
            self.artist_label.config(text="")
            
        self._set_default_album_art()
        self.hide_display()
        
    def set_theme(self, is_dark: bool):
        """Update theme colors"""
        if is_dark:
            text_color = "#FFFFFF"
            secondary_color = "#BBBBBB"
            accent_color = "#4CAF50"
        else:
            text_color = "#000000"
            secondary_color = "#666666"
            accent_color = "#2E7D32"
            
        # Update label colors
        if self.song_label:
            self.song_label.config(foreground=accent_color)
            
        if self.artist_label:
            self.artist_label.config(foreground=secondary_color)
            
    def set_song_recognition_manager(self, manager):
        """Set the song recognition manager reference"""
        self.song_recognition_manager = manager
        
    def _update_like_button(self):
        """Update like button appearance based on current song's like status"""
        if not self.like_button or not self.song_recognition_manager:
            return
            
        try:
            # Check if current song is liked
            is_liked = self.song_recognition_manager.is_current_song_liked()
            
            # Update button appearance
            if is_liked:
                self.like_button.config(text="❤️")  # Red heart for liked
            else:
                self.like_button.config(text="🤍")  # White heart for not liked
                
        except Exception as e:
            print(f"Error updating like button: {e}")
            # Fallback to default
            self.like_button.config(text="🤍", foreground="#888888")
            
    def toggle_like(self):
        """Toggle like status for the current song"""
        if not self.song_recognition_manager:
            print("Song recognition manager not available")
            return
            
        if not self.current_song or not self.current_artist:
            print("No current song to like")
            return
            
        try:
            # Check current like status
            is_liked = self.song_recognition_manager.is_current_song_liked()
            
            if is_liked:
                # Unlike the song
                if self.song_recognition_manager.unlike_current_song():
                    print(f"💔 Unliked: {self.current_song} by {self.current_artist}")
                    self._update_like_button()
                else:
                    print("Failed to unlike song")
            else:
                # Like the song
                if self.song_recognition_manager.like_current_song():
                    print(f"❤️ Liked: {self.current_song} by {self.current_artist}")
                    self._update_like_button()
                else:
                    print("Failed to like song")
                    
        except Exception as e:
            print(f"Error toggling like: {e}")
            
    def get_liked_songs(self) -> list:
        """Get all liked songs from the recognition manager"""
        if not self.song_recognition_manager:
            return []
            
        try:
            return self.song_recognition_manager.get_liked_songs()
        except Exception as e:
            print(f"Error getting liked songs: {e}")
            return []
            
    def navigate_left(self):
        """Navigate to the left (previous) display mode"""
        if self.display_mode == 'soundscape':
            self.display_mode = 'song'
            self.update_display_mode()
        elif self.display_mode == 'speech':
            self.display_mode = 'soundscape'
            self.update_display_mode()
            
    def navigate_right(self):
        """Navigate to the right (next) display mode"""
        if self.display_mode == 'song':
            self.display_mode = 'soundscape'
            self.update_display_mode()
        elif self.display_mode == 'soundscape':
            self.display_mode = 'speech'
            self.update_display_mode()
            
    def update_display_mode(self):
        """Update the display based on current mode"""
        if self.display_mode == 'song':
            self.update_song_display()
        elif self.display_mode == 'soundscape':
            self.update_soundscape_display()
        elif self.display_mode == 'speech':
            self.update_speech_display()
            
    def update_song_display(self):
        """Update display for song recognition mode"""
        # Update mode indicator
        if self.mode_indicator:
            self.mode_indicator.config(text="🎵 Song Recognition")
            
        # Show/hide appropriate elements
        if self.album_art_label:
            self.album_art_label.pack(side="left", padx=(0, 15))
            
        if self.like_button:
            self.like_button.pack()
            
        # Update content based on current song
        if self.current_song and self.current_artist:
            if self.song_label:
                self.song_label.config(text=self.current_song)
            if self.artist_label:
                self.artist_label.config(text=f"by {self.current_artist}")
        else:
            if self.song_label:
                self.song_label.config(text="No song playing")
            if self.artist_label:
                self.artist_label.config(text="")
                
    def update_soundscape_display(self):
        """Update display for soundscape analysis mode"""
        # Update mode indicator
        if self.mode_indicator:
            self.mode_indicator.config(text="🌊 Soundscape Analysis")
            
        # Hide album art and like button for soundscape mode
        if self.album_art_label:
            self.album_art_label.pack_forget()
            
        if self.like_button:
            self.like_button.pack_forget()
            
        # Update content for soundscape info
        if self.song_label:
            self.song_label.config(text="Analyzing ambient sounds...")
            
        if self.artist_label:
            self.artist_label.config(text="Soundscape recognition active")
            
    def update_soundscape_info(self, soundscape_data):
        """Update soundscape information display"""
        if self.display_mode != 'soundscape':
            return
            
        try:
            # Extract relevant soundscape information
            dominant_sounds = soundscape_data.get('dominant_sounds', [])
            confidence = soundscape_data.get('confidence', 0)
            environment_type = soundscape_data.get('environment_type', 'Unknown')
            
            # Format the display text
            if dominant_sounds:
                sound_text = ", ".join(dominant_sounds[:3])  # Show top 3 sounds
                if self.song_label:
                    self.song_label.config(text=f"Detected: {sound_text}")
            else:
                if self.song_label:
                    self.song_label.config(text="Listening...")
                    
            # Show environment info
            env_text = f"Environment: {environment_type}"
            if confidence > 0:
                env_text += f" ({confidence:.1%} confidence)"
                
            if self.artist_label:
                self.artist_label.config(text=env_text)
                
        except Exception as e:
            print(f"Error updating soundscape info: {e}")
            if self.song_label:
                self.song_label.config(text="Soundscape analysis error")
            if self.artist_label:
                self.artist_label.config(text="Please try again")
                
    def update_speech_display(self):
        """Update display for speech detection mode"""
        # Update mode indicator
        if self.mode_indicator:
            self.mode_indicator.config(text="👂 Speech Detection")
            
        # Hide album art and like button for speech mode
        if self.album_art_label:
            self.album_art_label.pack_forget()
            
        if self.like_button:
            self.like_button.pack_forget()
            
        # Show ear button if not present
        if not self.ear_button:
            self._create_ear_button()
            
        # Update content for speech info
        if self.song_label:
            self.song_label.config(text="Listening for speech...")
            
        if self.artist_label:
            self.artist_label.config(text="Click the ear to start translation")
            
        # Start audio monitoring
        self._start_audio_monitoring()
    
    def _create_ear_button(self):
        """Create the ear button for speech translation"""
        if not self.ear_button:
            # Find the button frame
            button_frame = None
            for child in self.display_frame.winfo_children():
                if isinstance(child, ttk.LabelFrame):
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, ttk.Frame):
                            for ggchild in grandchild.winfo_children():
                                if isinstance(ggchild, ttk.Frame) and ggchild.winfo_children():
                                    # Check if this is the button frame
                                    if any(isinstance(btn, ttk.Button) for btn in ggchild.winfo_children()):
                                        button_frame = ggchild
                                        break
            
            if button_frame:
                self.ear_button = ttk.Button(
                    button_frame,
                    text="👂",
                    command=self.toggle_translation,
                    width=3
                )
                self.ear_button.pack(pady=(5, 0))
    
    def toggle_translation(self):
        """Toggle live translation on/off"""
        if self.translation_active:
            self.stop_translation()
        else:
            self.start_translation()
    
    def start_translation(self):
        """Start live translation"""
        if self.translation_active:
            return
            
        self.translation_active = True
        
        # Update ear button
        if self.ear_button:
            self.ear_button.config(text="👂🔴")  # Red dot indicates active
            
        # Start live translator
        self.live_translator.add_translation_callback(self._on_translation_result)
        self.live_translator.start_translation()
        
        # Update display
        if self.song_label:
            self.song_label.config(text="🔴 Live translation active")
        if self.artist_label:
            self.artist_label.config(text="Speaking...")
            
        print("🎙️ Live translation started")
    
    def stop_translation(self):
        """Stop live translation"""
        if not self.translation_active:
            return
            
        self.translation_active = False
        
        # Update ear button
        if self.ear_button:
            self.ear_button.config(text="👂")
            
        # Stop live translator
        self.live_translator.stop_translation()
        
        # Update display
        if self.song_label:
            self.song_label.config(text="Translation stopped")
        if self.artist_label:
            self.artist_label.config(text="Click the ear to start translation")
            
        print("🛑 Live translation stopped")
    
    def _start_audio_monitoring(self):
        """Start monitoring audio for speech detection"""
        if self.audio_recording:
            return
            
        try:
            self.audio_recording = True
            self.audio_thread = threading.Thread(target=self._audio_monitoring_loop)
            self.audio_thread.daemon = True
            self.audio_thread.start()
        except Exception as e:
            print(f"Failed to start audio monitoring: {e}")
    
    def _audio_monitoring_loop(self):
        """Background audio monitoring loop"""
        try:
            # Initialize PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Open audio stream
            self.audio_stream = self.pyaudio_instance.open(
                format=self.audio_format,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            # 5-second buffer for translation
            buffer_duration = 5.0
            buffer_size = int(buffer_duration * self.sample_rate)
            audio_buffer = np.zeros(buffer_size, dtype=np.int16)
            buffer_index = 0
            
            while self.audio_recording and self.display_mode == 'speech':
                try:
                    # Read audio data
                    data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    
                    # Add to circular buffer
                    chunk_len = len(audio_chunk)
                    if buffer_index + chunk_len <= buffer_size:
                        audio_buffer[buffer_index:buffer_index + chunk_len] = audio_chunk
                        buffer_index += chunk_len
                    else:
                        # Wrap around
                        remaining = buffer_size - buffer_index
                        audio_buffer[buffer_index:] = audio_chunk[:remaining]
                        audio_buffer[:chunk_len - remaining] = audio_chunk[remaining:]
                        buffer_index = chunk_len - remaining
                    
                    # Process full buffer every 5 seconds
                    if buffer_index >= buffer_size or (buffer_index > 0 and buffer_index % (self.sample_rate // 2) == 0):
                        self._process_audio_buffer(audio_buffer.copy())
                        
                        # Reset buffer
                        if buffer_index >= buffer_size:
                            buffer_index = 0
                            
                except Exception as e:
                    print(f"Audio monitoring error: {e}")
                    break
                    
        except Exception as e:
            print(f"Audio monitoring initialization failed: {e}")
        finally:
            self._cleanup_audio_stream()
    
    def _process_audio_buffer(self, audio_buffer: np.ndarray):
        """Process audio buffer for speech detection"""
        try:
            # Convert to float
            audio_float = audio_buffer.astype(np.float32) / 32768.0
            
            # Detect speech
            speech_result = self.speech_detector.detect_speech(audio_float, self.sample_rate)
            
            if speech_result['is_speech'] and speech_result['confidence'] > 0.7:
                # Detect language
                language_result = self.language_detector.detect_language(audio_float, self.sample_rate)
                
                if language_result['success']:
                    # Update display with language info
                    self.current_language = language_result['language_code']
                    self._update_language_display(language_result)
                    
                    # Add to translator if active
                    if self.translation_active:
                        self.live_translator.add_audio_clip(audio_float, self.sample_rate)
                        
        except Exception as e:
            print(f"Audio processing error: {e}")
    
    def _update_language_display(self, language_result):
        """Update display with detected language"""
        try:
            flag = language_result['flag']
            language_name = language_result['language_name']
            confidence = language_result['confidence']
            
            # Update on main thread
            if self.song_label:
                self.song_label.after(0, lambda: self.song_label.config(
                    text=f"{flag} {language_name} detected"
                ))
            
            if self.artist_label:
                self.artist_label.after(0, lambda: self.artist_label.config(
                    text=f"Confidence: {confidence:.1%}"
                ))
                
        except Exception as e:
            print(f"Language display update error: {e}")
    
    def _on_translation_result(self, translation_result):
        """Handle translation result callback"""
        try:
            original_text = translation_result['original_text']
            translated_text = translation_result['translated_text']
            source_language = translation_result['source_language']
            
            # Get language flag
            flag = self.language_detector.get_language_flag(source_language)
            
            # Update display on main thread
            if self.song_label:
                self.song_label.after(0, lambda: self.song_label.config(
                    text=f"{flag} {original_text[:50]}..."
                ))
            
            if self.artist_label:
                self.artist_label.after(0, lambda: self.artist_label.config(
                    text=f"🔄 {translated_text[:50]}..."
                ))
                
            print(f"Translation: {original_text} -> {translated_text}")
            
        except Exception as e:
            print(f"Translation result error: {e}")
    
    def _cleanup_audio_stream(self):
        """Clean up audio stream resources"""
        self.audio_recording = False
        
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
            self.audio_stream = None
            
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except:
                pass
            self.pyaudio_instance = None
    
    def cleanup(self):
        """Clean up resources"""
        # Stop translation
        if self.translation_active:
            self.stop_translation()
            
        # Clean up audio
        self._cleanup_audio_stream()
        
        # Clean up other resources
        if self.art_fetcher:
            self.art_fetcher.active_requests.clear()
            
        # Clean up translators
        if self.live_translator:
            self.live_translator.cleanup()
            
        # Clear image references
        self.current_album_art = None
        
    def open_revision_dialog(self):
        """Open song revision dialog"""
        if not self.song_recognition_manager:
            print("Song recognition manager not available")
            return
            
        if not self.current_song or not self.current_artist:
            print("No current song to revise")
            return
            
        # Create revision dialog
        dialog = tk.Toplevel(self.parent_frame)
        dialog.title("Revise Song Recognition")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        
        # Make dialog modal
        dialog.transient(self.parent_frame)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.parent_frame.winfo_rootx() + 50, self.parent_frame.winfo_rooty() + 50))
        
        # Main frame with padding
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="✏️ Revise Song Recognition", font=("Ubuntu", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Current song info
        current_frame = ttk.LabelFrame(main_frame, text="Current Recognition", padding=10)
        current_frame.pack(fill="x", pady=(0, 20))
        
        ttk.Label(current_frame, text="Song:", font=("Ubuntu", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Label(current_frame, text=self.current_song, font=("Ubuntu", 10)).grid(row=0, column=1, sticky="w")
        
        ttk.Label(current_frame, text="Artist:", font=("Ubuntu", 10, "bold")).grid(row=1, column=0, sticky="w", padx=(0, 10))
        ttk.Label(current_frame, text=self.current_artist, font=("Ubuntu", 10)).grid(row=1, column=1, sticky="w")
        
        # Revision suggestions
        suggestions = self.song_recognition_manager.get_revision_suggestions(self.current_song, self.current_artist)
        if suggestions:
            suggestion_frame = ttk.LabelFrame(main_frame, text="Previous Corrections", padding=10)
            suggestion_frame.pack(fill="x", pady=(0, 20))
            
            for i, suggestion in enumerate(suggestions[:3]):  # Show up to 3 suggestions
                btn_text = f"{suggestion['song']} by {suggestion['artist']}"
                btn = ttk.Button(
                    suggestion_frame, 
                    text=btn_text,
                    command=lambda s=suggestion: self._apply_suggestion(s, dialog)
                )
                btn.pack(fill="x", pady=2)
        
        # Manual correction frame
        correction_frame = ttk.LabelFrame(main_frame, text="Manual Correction", padding=10)
        correction_frame.pack(fill="x", pady=(0, 20))
        
        # Song name field
        ttk.Label(correction_frame, text="Correct Song:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        song_var = tk.StringVar(value=self.current_song)
        song_entry = ttk.Entry(correction_frame, textvariable=song_var, width=40)
        song_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))
        
        # Artist name field
        ttk.Label(correction_frame, text="Correct Artist:").grid(row=1, column=0, sticky="w", pady=(0, 5))
        artist_var = tk.StringVar(value=self.current_artist)
        artist_entry = ttk.Entry(correction_frame, textvariable=artist_var, width=40)
        artist_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))
        
        # Reason field
        ttk.Label(correction_frame, text="Reason:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        reason_var = tk.StringVar(value="User correction")
        reason_combo = ttk.Combobox(correction_frame, textvariable=reason_var, width=37)
        reason_combo['values'] = [
            "User correction",
            "Wrong version/cover",
            "Remix vs original",
            "Sample misidentification",
            "Different artist rendition",
            "Live vs studio version",
            "Instrumental vs vocal",
            "Other"
        ]
        reason_combo.grid(row=2, column=1, sticky="ew", pady=(0, 5))
        
        # Configure grid weights
        correction_frame.columnconfigure(1, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side="right", padx=(5, 0))
        
        # Apply button
        apply_btn = ttk.Button(
            button_frame, 
            text="Apply Revision", 
            command=lambda: self._apply_revision(song_var.get(), artist_var.get(), reason_var.get(), dialog)
        )
        apply_btn.pack(side="right")
        
        # Focus on song entry
        song_entry.focus()
        song_entry.select_range(0, tk.END)
        
    def _apply_suggestion(self, suggestion, dialog):
        """Apply a revision suggestion"""
        try:
            if self.song_recognition_manager.revise_current_song(
                suggestion['song'], 
                suggestion['artist'], 
                f"Applied previous correction: {suggestion['reason']}"
            ):
                # Update display
                self.update_song(suggestion['song'], suggestion['artist'])
                dialog.destroy()
                print(f"✅ Applied suggestion: {suggestion['song']} by {suggestion['artist']}")
            else:
                print("❌ Failed to apply suggestion")
        except Exception as e:
            print(f"Error applying suggestion: {e}")
            
    def _apply_revision(self, correct_song, correct_artist, reason, dialog):
        """Apply manual revision"""
        # Validate input
        if not correct_song.strip() or not correct_artist.strip():
            # Show error message
            error_label = ttk.Label(dialog, text="⚠️ Please enter both song and artist names", foreground="red")
            error_label.pack(pady=5)
            dialog.after(3000, error_label.destroy)  # Remove after 3 seconds
            return
            
        try:
            if self.song_recognition_manager.revise_current_song(
                correct_song.strip(), 
                correct_artist.strip(), 
                reason.strip() or "User correction"
            ):
                # Update display
                self.update_song(correct_song.strip(), correct_artist.strip())
                dialog.destroy()
                print(f"✅ Revision applied: {correct_song} by {correct_artist}")
            else:
                print("❌ Failed to apply revision")
        except Exception as e:
            print(f"Error applying revision: {e}")


# Test widget
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import ttk
    
    class DummyThemeManager:
        def __init__(self):
            self.dark_theme = tk.BooleanVar(value=True)
    
    def test_widget():
        root = tk.Tk()
        root.title("Song Display Test")
        root.geometry("400x200")
        
        # Create theme manager
        theme_manager = DummyThemeManager()
        
        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create song display
        song_display = SongDisplayWidget(main_frame, theme_manager)
        
        # Test buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        def test_song():
            song_display.update_song("Bohemian Rhapsody", "Queen")
            
        def test_song2():
            song_display.update_song("Hotel California", "Eagles")
            
        def clear_song():
            song_display.clear_song()
            
        def test_soundscape():
            # Test soundscape data
            soundscape_data = {
                'dominant_sounds': ['birds', 'wind', 'water'],
                'confidence': 0.85,
                'environment_type': 'Natural outdoor'
            }
            song_display.update_soundscape_info(soundscape_data)
            
        ttk.Button(button_frame, text="Test Song 1", command=test_song).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Test Song 2", command=test_song2).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Test Soundscape", command=test_soundscape).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear", command=clear_song).pack(side="left", padx=5)
        
        # Some other content
        ttk.Label(main_frame, text="This is the main content area").pack(pady=20)
        
        root.mainloop()
        
    test_widget()
