# hearing_hud.py
import tkinter as tk
from tkinter import ttk
import threading
import time
import queue
import sys
import os
import asyncio
import tempfile
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
import soundfile as sf
import librosa
try:
    import sounddevice as sd
except ImportError:
    sd = None
    
try:
    import psutil
except ImportError:
    psutil = None

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from gui.themes.themes import DARK_THEME

# Import perception modules
try:
    from perception.sonic.audio_processor import AudioProcessor
    from perception.sonic.sound_classifier import SoundClassifier
    from perception.sonic.exo import recognize_song_sync
    from perception.sonic.song_recognition import SongRecognitionManager
except ImportError as e:
    print(f"Warning: Could not import perception modules: {e}")
    AudioProcessor = None
    SoundClassifier = None
    recognize_song_sync = None
    SongRecognitionManager = None
    
    # Try alternative import path
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'perception', 'sonic')))
        from song_recognition import SongRecognitionManager
        print("Successfully imported SongRecognitionManager with alternative path")
    except ImportError:
        print("Failed to import SongRecognitionManager with alternative path")
        SongRecognitionManager = None

class HearingHUD:
    def __init__(self, parent_frame, theme_manager):
        self.parent_frame = parent_frame
        self.theme_manager = theme_manager
        self.is_visible = False
        self.is_listening = False
        self.is_processing = False
        self.current_input = ""
        self.confidence_level = 0.0
        self.last_activity = None
        
        # Audio processing components
        self.audio_processor = None
        self.sound_classifier = None
        self.song_recognition_manager = None
        self.audio_thread = None
        self.audio_queue = queue.Queue()
        
        # Real-time audio processing
        self.recording_buffer = []
        self.recording_chunk_size = 4096
        self.music_recognition_buffer = []
        self.max_music_buffer_seconds = 10
        
        # Smart pane container
        self.pane_frame = None
        self.widgets = {}
        
        # HUD widgets dictionary
        self.hud_widgets = {}
        
        # Reference to root window
        self.root = parent_frame
        
        # Animation variables
        self.animation_frame = 0
        self.animation_thread = None
        self.animation_running = False
        
        # Audio input buffer
        self.audio_buffer = []
        self.max_buffer_size = 50
        
        self.selected_audio_device = tk.StringVar()
        self.available_audio_devices = []
        
        # Sonic perception module status
        self.sonic_modules_status = {
            'audio_processor': False,
            'sound_classifier': False,
            'spatial_audio': False,
            'frequency_analyzer': False,
            'vocal_analyzer': False,
            'music_recognition': False
        }
        
        # Sonic perception module running status
        self.sonic_modules_running = {
            'audio_processor': False,
            'sound_classifier': False,
            'spatial_audio': False,
            'frequency_analyzer': False,
            'vocal_analyzer': False,
            'music_recognition': False
        }
        
        # Initialize audio processing
        self.init_audio_processing()
        
        # Initialize song recognition manager
        self.init_song_recognition()
        
        # Build the HUD
        self.build_hud()
        
    def init_audio_processing(self):
        """Initialize audio processing components"""
        try:
            if AudioProcessor and SoundClassifier:
                self.audio_processor = AudioProcessor()
                self.sound_classifier = SoundClassifier()
                print("Audio processing initialized successfully")
            else:
                print("Audio processing modules not available")
        except Exception as e:
            print(f"Failed to initialize audio processing: {e}")
            self.audio_processor = None
            self.sound_classifier = None
            
        # Update module status after initialization
        if hasattr(self, 'sonic_modules_status'):
            self.update_sonic_modules_status()
        
    def build_hud(self):
        """Build the HUD overlay window"""
        # Create a toplevel window for the HUD
        self.hud_window = tk.Toplevel(self.root)
        self.hud_window.title("We're Hearing - Marina HUD")
        self.hud_window.geometry("500x600")  # Larger window to accommodate new features
        
        # Configure window properties
        self.hud_window.attributes('-topmost', True)  # Always on top
        self.hud_window.resizable(False, False)
        
        # Apply theme
        bg_color = DARK_THEME["bg"] if self.theme_manager.dark_theme.get() else "#f0f0f0"
        fg_color = DARK_THEME["fg"] if self.theme_manager.dark_theme.get() else "#000000"
        
        self.hud_window.configure(bg=bg_color)
        
        # Initially hide the HUD
        self.hud_window.withdraw()
        
        # Create main frame
        main_frame = ttk.Frame(self.hud_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header frame
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))
        
        # Title with icon
        title_label = ttk.Label(
            header_frame,
            text="🎧 We're Hearing",
            font=("Ubuntu", 14, "bold")
        )
        title_label.pack(side="left")
        
        # Close button
        close_button = ttk.Button(
            header_frame,
            text="✕",
            command=self.hide_hud,
            width=3
        )
        close_button.pack(side="right")
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(0, 10))

        # Start Listening button
        self.hud_widgets['start_listening_button'] = ttk.Button(
            buttons_frame,
            text="Start Listening",
            command=self.start_listening
        )
        self.hud_widgets['start_listening_button'].pack(side="left", padx=5)

        # Stop Listening button
        self.hud_widgets['stop_listening_button'] = ttk.Button(
            buttons_frame,
            text="Stop Listening",
            command=self.stop_listening
        )
        self.hud_widgets['stop_listening_button'].pack(side="left", padx=5)

        # Start Processing button
        self.hud_widgets['start_processing_button'] = ttk.Button(
            buttons_frame,
            text="Start Processing",
            command=self.start_processing
        )
        self.hud_widgets['start_processing_button'].pack(side="left", padx=5)

        # Stop Processing button
        self.hud_widgets['stop_processing_button'] = ttk.Button(
            buttons_frame,
            text="Stop Processing",
            command=self.stop_processing
        )
        self.hud_widgets['stop_processing_button'].pack(side="left", padx=5)
        
        # Performance meter frame
        performance_frame = ttk.LabelFrame(main_frame, text="Performance")
        performance_frame.pack(fill="x", pady=(0, 10))

        # CPU usage label
        self.hud_widgets['cpu_label'] = ttk.Label(
            performance_frame,
            text="CPU Usage: N/A"
        )
        self.hud_widgets['cpu_label'].pack(side="left", padx=5)

        # RAM usage label
        self.hud_widgets['ram_label'] = ttk.Label(
            performance_frame,
            text="RAM Usage: N/A"
        )
        self.hud_widgets['ram_label'].pack(side="left", padx=5)
        
        device_frame = ttk.LabelFrame(main_frame, text="Audio Input Device")
        device_frame.pack(fill="x", pady=(0, 10))
        
        # Get available audio devices
        self.populate_audio_devices()
        
        # Audio device dropdown
        self.hud_widgets['audio_device_combo'] = ttk.Combobox(
            device_frame,
            textvariable=self.selected_audio_device,
            values=self.available_audio_devices,
            state="readonly",
            width=50
        )
        self.hud_widgets['audio_device_combo'].pack(padx=5, pady=5)
        
        # Set default device
        if self.available_audio_devices:
            self.selected_audio_device.set(self.available_audio_devices[0])
        
        # Sonic perception modules status frame
        modules_frame = ttk.LabelFrame(main_frame, text="Sonic Perception Modules")
        modules_frame.pack(fill="x", pady=(0, 10))
        
        # Music recognition result display
        self.hud_widgets['music_recognition_text'] = ttk.Label(
            main_frame,
            text="",
            font=("Ubuntu", 10, "italic"),
            foreground="blue"
        )
        self.hud_widgets['music_recognition_text'].pack(fill="x", pady=(0, 10))
        
        # Create legend for status indicators
        legend_frame = ttk.Frame(modules_frame)
        legend_frame.pack(fill="x", padx=5, pady=2)
        
        legend_label = ttk.Label(
            legend_frame,
            text="✅ Active  ❌ Inactive  🏃 Running 😴  Idle",
            font=("Ubuntu", 8),
            foreground="gray"
        )
        legend_label.pack(side="left")
        
        # Create status indicators for each module
        self.create_module_status_indicators(modules_frame)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=(0, 10))
        
        # Listening status
        self.hud_widgets['status_label'] = ttk.Label(
            status_frame,
            text="🔴 Not Listening",
            font=("Ubuntu", 12, "bold")
        )
        self.hud_widgets['status_label'].pack(side="left")
        
        # Confidence meter
        confidence_frame = ttk.Frame(status_frame)
        confidence_frame.pack(side="right")
        
        ttk.Label(confidence_frame, text="Confidence:").pack(side="left")
        self.hud_widgets['confidence_bar'] = ttk.Progressbar(
            confidence_frame,
            length=100,
            mode='determinate'
        )
        self.hud_widgets['confidence_bar'].pack(side="left", padx=(5, 0))
        
        # Audio input display
        input_frame = ttk.LabelFrame(main_frame, text="Current Input")
        input_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Text display with scrollbar
        text_frame = ttk.Frame(input_frame)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.hud_widgets['input_text'] = tk.Text(
            text_frame,
            height=8,
            wrap=tk.WORD,
            font=("Ubuntu Mono", 10),
            bg=bg_color,
            fg=fg_color,
            state='disabled'
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.hud_widgets['input_text'].yview)
        self.hud_widgets['input_text'].configure(yscrollcommand=scrollbar.set)
        
        self.hud_widgets['input_text'].pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Audio activity indicator
        activity_frame = ttk.Frame(main_frame)
        activity_frame.pack(fill="x")
        
        ttk.Label(activity_frame, text="Audio Activity:").pack(side="left")
        
        # Visual audio level indicator
        self.hud_widgets['audio_canvas'] = tk.Canvas(
            activity_frame,
            width=200,
            height=30,
            bg=bg_color,
            highlightthickness=0
        )
        self.hud_widgets['audio_canvas'].pack(side="left", padx=(10, 0))
        
        # Initialize audio bars
        self.audio_bars = []
        for i in range(20):
            bar = self.hud_widgets['audio_canvas'].create_rectangle(
                i * 10, 25, (i + 1) * 10 - 2, 30,
                fill="#333333", outline=""
            )
            self.audio_bars.append(bar)
        
        # Processing indicator
        self.hud_widgets['processing_label'] = ttk.Label(
            activity_frame,
            text="",
            font=("Ubuntu", 10)
        )
        self.hud_widgets['processing_label'].pack(side="right")
        
        # Update sonic perception module status
        self.update_sonic_modules_status()
        
        # Start the update loop
        self.start_update_loop()
        
    def init_song_recognition(self):
        """Initialize and start the Song Recognition Manager"""
        try:
            if SongRecognitionManager:
                self.song_recognition_manager = SongRecognitionManager()

                # Note: Callback will be registered by the main GUI
                # The main GUI will handle song recognition display

                # Start the song recognition manager
                self.song_recognition_manager.start()
                print("Song recognition initialized successfully")
            else:
                print("Song recognition manager module not available")
        except Exception as e:
            print(f"Failed to initialize song recognition: {e}")
            
    def show_hud(self):
        """Show the HUD"""
        if not self.is_visible:
            self.is_visible = True
            self.hud_window.deiconify()
            self.hud_window.lift()
            self.start_animation()
            
    def hide_hud(self):
        """Hide the HUD"""
        if self.is_visible:
            self.is_visible = False
            self.hud_window.withdraw()
            self.stop_animation()
            
    def cleanup(self):
        """Cleanup resources when HUD is closed"""
        # Stop song recognition manager
        if self.song_recognition_manager:
            self.song_recognition_manager.stop()
            
        # Stop animation
        self.stop_animation()
        
        # Stop audio processing
        if self.audio_processor:
            self.audio_processor.stop_realtime_processing()
            
    def toggle_hud(self):
        """Toggle HUD visibility"""
        if self.is_visible:
            self.hide_hud()
        else:
            self.show_hud()
            
    def start_listening(self):
        """Start listening mode"""
        self.is_listening = True
        self.last_activity = datetime.now()
        self.update_status()
        self.update_sonic_modules_running_status()
        
    def stop_listening(self):
        """Stop listening mode"""
        self.is_listening = False
        self.update_status()
        self.update_sonic_modules_running_status()
        
    def start_processing(self):
        """Start processing mode"""
        self.is_processing = True
        self.update_status()
        self.update_sonic_modules_running_status()
        
    def stop_processing(self):
        """Stop processing mode"""
        self.is_processing = False
        self.update_status()
        self.update_sonic_modules_running_status()
        
    def update_input(self, text, confidence=0.0):
        """Update the current input text"""
        self.current_input = text
        self.confidence_level = confidence
        self.last_activity = datetime.now()
        
        self.update_music_recognition_text(text, confidence)
        
    def update_music_recognition_text(self, text, confidence=0.0):
        """Update the music recognition text bar"""
        self.hud_widgets['music_recognition_text'].config(text=text)
        
        # Update confidence bar
        self.hud_widgets['confidence_bar']['value'] = confidence * 100
        
    def add_audio_activity(self, level):
        """Add audio activity level (0.0 to 1.0)"""
        self.audio_buffer.append(level)
        if len(self.audio_buffer) > self.max_buffer_size:
            self.audio_buffer.pop(0)
            
        self.last_activity = datetime.now()
        self.update_audio_visualization()
        
    def update_audio_visualization(self):
        """Update the audio visualization bars"""
        if not self.hud_widgets.get('audio_canvas'):
            return
            
        # Get recent audio levels
        recent_levels = self.audio_buffer[-20:] if len(self.audio_buffer) >= 20 else self.audio_buffer
        
        # Update bars
        for i, bar in enumerate(self.audio_bars):
            if i < len(recent_levels):
                level = recent_levels[i]
                height = int(level * 25)
                
                # Color based on level
                if level > 0.7:
                    color = "#ff4444"  # Red for high levels
                elif level > 0.4:
                    color = "#ffaa44"  # Orange for medium levels
                elif level > 0.1:
                    color = "#44ff44"  # Green for low levels
                else:
                    color = "#333333"  # Dark for no activity
                    
                # Update bar
                self.hud_widgets['audio_canvas'].coords(
                    bar,
                    i * 10, 30 - height,
                    (i + 1) * 10 - 2, 30
                )
                self.hud_widgets['audio_canvas'].itemconfig(bar, fill=color)
            else:
                # No data, make it dark
                self.hud_widgets['audio_canvas'].coords(
                    bar,
                    i * 10, 25,
                    (i + 1) * 10 - 2, 30
                )
                self.hud_widgets['audio_canvas'].itemconfig(bar, fill="#333333")
                
    def update_performance_meters(self):
        try:
            if psutil is None:
                self.hud_widgets['cpu_label'].config(text="CPU Usage: N/A (psutil not available)")
                self.hud_widgets['ram_label'].config(text="RAM Usage: N/A (psutil not available)")
                return
                
            # Get CPU usage percentage
            cpu_usage = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            ram_usage_gb = memory.used / (1024 ** 3)  # Convert to GB
            ram_percent = memory.percent
            
            self.hud_widgets['cpu_label'].config(text=f"CPU Usage: {cpu_usage:.1f}%")
            self.hud_widgets['ram_label'].config(text=f"RAM Usage: {ram_usage_gb:.1f} GB ({ram_percent:.1f}%)")
        except Exception as e:
            print(f"Error getting performance info: {e}")
            self.hud_widgets['cpu_label'].config(text="CPU Usage: N/A")
            self.hud_widgets['ram_label'].config(text="RAM Usage: N/A")
    
    def update_status(self):
        """Update the status display"""
        if not self.hud_widgets.get('status_label'):
            return
            
        if self.is_processing:
            status_text = "🔄 Processing..."
            processing_text = "🔍 Analyzing input..."
        elif self.is_listening:
            status_text = "🟢 Listening"
            processing_text = "👂 Ready for input"
        else:
            status_text = "🔴 Not Listening"
            processing_text = "😴 Standby"
            
        self.hud_widgets['status_label'].config(text=status_text)
        self.hud_widgets['processing_label'].config(text=processing_text)
        
    def start_animation(self):
        """Start the animation loop"""
        if not self.animation_running:
            self.animation_running = True
            self.animation_thread = threading.Thread(target=self.animation_loop)
            self.animation_thread.daemon = True
            self.animation_thread.start()
            
    def stop_animation(self):
        """Stop the animation loop"""
        self.animation_running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1)
            
    def animation_loop(self):
        """Animation loop for visual effects"""
        while self.animation_running:
            self.animation_frame += 1
            
            # Animate processing indicator
            if self.is_processing:
                dots = "." * (self.animation_frame % 4)
                if self.hud_widgets.get('processing_label'):
                    self.root.after(0, lambda: self.hud_widgets['processing_label'].config(text=f"🧠 Analyzing{dots}"))
            
            # Simulate audio activity if listening
            if self.is_listening and not self.is_processing:
                # Add some random audio activity for demonstration
                import random
                level = random.random() * 0.3 if random.random() > 0.7 else 0.0
                self.add_audio_activity(level)
                
            time.sleep(0.2)
            
    def start_update_loop(self):
        """Start the main update loop"""
        self.update_display()
        self.root.after(100, self.start_update_loop)
        
    def update_display(self):
        """Update the display elements"""
        if not self.is_visible:
            return
            
        # Update time since last activity
        self.update_performance_meters()

        if self.last_activity:
            time_diff = (datetime.now() - self.last_activity).total_seconds()
            if time_diff > 5:  # 5 seconds of inactivity
                # Fade out audio bars
                for bar in self.audio_bars:
                    self.hud_widgets['audio_canvas'].itemconfig(bar, fill="#333333")
                    
    def start_real_time_audio_processing(self):
        """Start real-time audio processing using AudioProcessor"""
        if not self.audio_processor:
            self.update_input("Audio processing not available", 0.0)
            return
            
        self.start_listening()
        
        def audio_callback(processed_chunk):
            """Handle processed audio chunks"""
            # Update audio visualization
            rms_level = processed_chunk.get('rms_level', 0.0)
            peak_level = processed_chunk.get('peak_level', 0.0)
            
            # Normalize levels for visualization
            normalized_level = min(1.0, max(0.0, peak_level * 5))  # Scale for visibility
            self.add_audio_activity(normalized_level)
            
            # Check for voice activity
            events = processed_chunk.get('events', [])
            voice_events = [e for e in events if e.get('type') == 'voice_activity']
            
            if voice_events:
                # Found voice activity
                confidence = voice_events[0].get('confidence', 0.0)
                self.update_input(f"Voice detected (confidence: {confidence:.2f})", confidence)
                
                # Accumulate audio for music recognition
                self.recording_buffer.append(processed_chunk.get('enhanced_audio', []))
                
                # Try to classify the sound
                if self.sound_classifier:
                    try:
                        sound_type = self.sound_classifier.classify(
                            processed_chunk.get('enhanced_audio', []), 
                            self.audio_processor.sample_rate
                        )
                        if sound_type != 'unknown':
                            self.update_input(f"Sound classified as: {sound_type}", confidence)
                    except Exception as e:
                        print(f"Sound classification error: {e}")
            
            # Buffer management for music recognition
            if len(self.recording_buffer) > self.max_music_buffer_seconds * 10:  # ~10 chunks per second
                # Try music recognition on accumulated audio
                self.try_music_recognition()
                
        try:
            self.audio_processor.start_realtime_processing(callback=audio_callback)
        except Exception as e:
            self.update_input(f"Audio processing error: {str(e)}", 0.0)
            print(f"Real-time audio processing error: {e}")
    
    def stop_real_time_audio_processing(self):
        """Stop real-time audio processing"""
        if self.audio_processor:
            self.audio_processor.stop_realtime_processing()
        self.stop_listening()
        
    def try_music_recognition(self):
        """Try to recognize music using Shazamio"""
        if not recognize_song_sync or not self.recording_buffer:
            return
            
        self.start_processing()
        
        def recognition_thread():
            try:
                # Combine audio chunks
                combined_audio = np.concatenate(self.recording_buffer)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    sf.write(tmp_file.name, combined_audio, self.audio_processor.sample_rate)
                    
                    # Try Shazam recognition
                    result = recognize_song_sync(tmp_file.name)
                    
                    if result.get('success'):
                        track = result.get('track', {})
                        title = track.get('title', 'Unknown')
                        artist = track.get('subtitle', 'Unknown')
                        recognition_text = f"🎶 Now Playing: {title} - {artist}"
                        self.update_music_recognition_text(recognition_text, 0.9)
                    else:
                        self.update_input("🎵 Music detected but not recognized", 0.5)
                        
                    # Clean up
                    os.unlink(tmp_file.name)
                    
            except Exception as e:
                self.update_music_recognition_text(f"Recognition error: {str(e)}", 0.0)
                print(f"Music recognition error: {e}")
            finally:
                self.stop_processing()
                self.recording_buffer.clear()
                
        # Run recognition in separate thread to avoid blocking
        threading.Thread(target=recognition_thread, daemon=True).start()
        
    def process_audio_file(self, file_path: str):
        """Process an audio file for recognition and analysis"""
        if not self.audio_processor:
            self.update_input("Audio processing not available", 0.0)
            return
            
        self.start_processing()
        
        def process_thread():
            try:
                # Load audio file
                audio_data, sample_rate = self.audio_processor.load_audio_file(file_path)
                
                if audio_data is None:
                    self.update_input(f"Failed to load audio file: {file_path}", 0.0)
                    return
                    
                # Get audio info
                audio_info = self.audio_processor.get_audio_info(audio_data)
                duration = audio_info.get('duration', 0)
                
                self.update_input(f"Processing audio file ({duration:.1f}s)...", 0.5)
                
                # Try music recognition
                if recognize_song_sync:
                    result = recognize_song_sync(file_path)
                    
                    if result.get('success'):
                        track = result.get('track', {})
                        title = track.get('title', 'Unknown')
                        artist = track.get('subtitle', 'Unknown')
                        recognition_text = f"🎵 Recognized: {title} by {artist}"
                        self.update_input(recognition_text, 0.9)
                    else:
                        self.update_input("🎵 Music not recognized", 0.3)
                        
                # Try sound classification
                if self.sound_classifier:
                    try:
                        sound_type = self.sound_classifier.classify(audio_data, sample_rate)
                        if sound_type != 'unknown':
                            current_text = self.current_input
                            self.update_input(f"{current_text}\n🔊 Classified as: {sound_type}", 0.7)
                    except Exception as e:
                        print(f"Sound classification error: {e}")
                        
            except Exception as e:
                self.update_input(f"Error processing audio file: {str(e)}", 0.0)
                print(f"Audio file processing error: {e}")
            finally:
                self.stop_processing()
                
        # Run processing in separate thread
        threading.Thread(target=process_thread, daemon=True).start()
        
    def simulate_speech_input(self, text):
        """Simulate speech input for testing (kept for backward compatibility)"""
        self.start_listening()
        
        # Simulate gradual speech recognition
        words = text.split()
        current_text = ""
        
        for i, word in enumerate(words):
            current_text += word + " "
            confidence = min(0.9, 0.3 + (i / len(words)) * 0.6)
            
            # Add some audio activity
            self.add_audio_activity(0.8)
            
            # Update display
            self.update_input(current_text.strip(), confidence)
            
            # Small delay to simulate real-time recognition
            time.sleep(0.3)
            
        # Finish processing
        self.start_processing()
        time.sleep(1)
        self.stop_processing()
        self.stop_listening()
        
    def simulate_ambient_listening(self):
        """Simulate ambient listening mode (kept for backward compatibility)"""
        self.start_listening()
        
        # Simulate background noise detection
        import random
        for _ in range(20):
            level = random.random() * 0.2
            self.add_audio_activity(level)
            time.sleep(0.1)
            
        # Simulate detecting speech
        self.update_input("Hello Marina...", 0.4)
        time.sleep(1)
        
        # Continue with more speech
        self.update_input("Hello Marina, can you help me with something?", 0.8)
        time.sleep(2)
        
        # Start processing
        self.start_processing()
        time.sleep(1.5)
        self.stop_processing()
        self.stop_listening()
        
    def populate_audio_devices(self):
        """Populate the list of available audio devices"""
        self.available_audio_devices = []
        
        if sd is None:
            self.available_audio_devices = ["SoundDevice not available"]
            return
            
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                # Only include devices with input channels
                if device['max_input_channels'] > 0:
                    device_name = f"{i}: {device['name']} ({device['max_input_channels']} ch)"
                    self.available_audio_devices.append(device_name)
                    
            if not self.available_audio_devices:
                self.available_audio_devices = ["No input devices found"]
                
        except Exception as e:
            print(f"Error querying audio devices: {e}")
            self.available_audio_devices = ["Error querying devices"]
            
    def create_module_status_indicators(self, parent_frame):
        """Create status indicators for sonic perception modules"""
        # Module status widgets
        self.module_status_widgets = {}
        self.module_running_widgets = {}
        
        # Create a container frame for grid layout
        grid_frame = ttk.Frame(parent_frame)
        grid_frame.pack(fill="x", padx=5, pady=2)
        
        # Create a grid for module status
        modules_info = {
            'audio_processor': {'icon': '🎙️', 'name': 'Audio Processor'},
            'sound_classifier': {'icon': '🔊', 'name': 'Sound Classifier'},
            'spatial_audio': {'icon': '🎯', 'name': 'Spatial Audio'},
            'frequency_analyzer': {'icon': '📊', 'name': 'Frequency Analyzer'},
            'vocal_analyzer': {'icon': '🗣️', 'name': 'Vocal Analyzer'},
            'music_recognition': {'icon': '🎵', 'name': 'Music Recognition'}
        }
        
        row = 0
        col = 0
        for module_key, module_info in modules_info.items():
            # Create frame for this module
            module_frame = ttk.Frame(grid_frame)
            module_frame.grid(row=row, column=col, padx=5, pady=2, sticky="w")
            
            # Availability status indicator (circle)
            status_label = ttk.Label(module_frame, text="⚪", font=("Ubuntu", 12))
            status_label.pack(side="left")
            
            # Running status indicator (smaller circle)
            running_label = ttk.Label(module_frame, text="⚫", font=("Ubuntu", 8))
            running_label.pack(side="left")
            
            # Module icon and name
            info_label = ttk.Label(
                module_frame,
                text=f"{module_info['icon']} {module_info['name']}",
                font=("Ubuntu", 10)
            )
            info_label.pack(side="left", padx=(5, 0))
            
            # Store references to status labels
            self.module_status_widgets[module_key] = status_label
            self.module_running_widgets[module_key] = running_label
            
            # Move to next position
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
                
    def update_sonic_modules_status(self):
        """Update the status of sonic perception modules"""
        # Check module availability and update status
        self.sonic_modules_status['audio_processor'] = self.audio_processor is not None
        self.sonic_modules_status['sound_classifier'] = self.sound_classifier is not None
        self.sonic_modules_status['music_recognition'] = (recognize_song_sync is not None) or (self.song_recognition_manager is not None)
        
        # Check for other modules
        try:
            from perception.sonic.spatial_audio import SpatialAudioProcessor
            self.sonic_modules_status['spatial_audio'] = True
        except ImportError:
            self.sonic_modules_status['spatial_audio'] = False
            
        try:
            from perception.sonic.frequency_analyzer import FrequencyAnalyzer
            self.sonic_modules_status['frequency_analyzer'] = True
        except ImportError:
            self.sonic_modules_status['frequency_analyzer'] = False
            
        try:
            from perception.sonic.vocal_analysis import VocalAnalyzer
            self.sonic_modules_status['vocal_analyzer'] = True
        except ImportError:
            self.sonic_modules_status['vocal_analyzer'] = False
            
        # Update visual indicators (only if widgets exist)
        if hasattr(self, 'module_status_widgets'):
            for module_key, status in self.sonic_modules_status.items():
                if module_key in self.module_status_widgets:
                    widget = self.module_status_widgets[module_key]
                    if status:
                        widget.config(text="🟢")  # Green circle for active
                    else:
                        widget.config(text="🔴")  # Red circle for inactive
                        
        # Update running indicators
        self.update_sonic_modules_running_status()
        
    def update_sonic_modules_running_status(self):
        """Update the running status of sonic perception modules"""
        # Update running status based on current listening state
        self.sonic_modules_running['audio_processor'] = self.is_listening and self.audio_processor is not None
        self.sonic_modules_running['sound_classifier'] = self.is_listening and self.sound_classifier is not None
        
        # Music recognition is running if either the sync version is processing or the manager is running
        song_manager_running = self.song_recognition_manager is not None and self.song_recognition_manager.is_running
        sync_recognition_running = self.is_processing and recognize_song_sync is not None
        self.sonic_modules_running['music_recognition'] = song_manager_running or sync_recognition_running
        
        # For now, other modules are not actively running
        self.sonic_modules_running['spatial_audio'] = False
        self.sonic_modules_running['frequency_analyzer'] = False
        self.sonic_modules_running['vocal_analyzer'] = False
        
        # Update visual indicators (only if widgets exist)
        if hasattr(self, 'module_running_widgets'):
            for module_key, running in self.sonic_modules_running.items():
                if module_key in self.module_running_widgets:
                    widget = self.module_running_widgets[module_key]
                    if running:
                        widget.config(text="🟡")  # Yellow circle for running
                    else:
                        widget.config(text="⚫")  # Black circle for not running
                        
    def set_module_running(self, module_key: str, running: bool):
        """Set the running status of a specific module"""
        if module_key in self.sonic_modules_running:
            self.sonic_modules_running[module_key] = running
            self.update_sonic_modules_running_status()
                    
    def get_selected_audio_device_index(self):
        """Get the index of the selected audio device"""
        selected = self.selected_audio_device.get()
        if selected and ':' in selected:
            try:
                return int(selected.split(':')[0])
            except (ValueError, IndexError):
                return None
        return None
        
    def get_status_info(self):
        """Get current status information"""
        return {
            'is_visible': self.is_visible,
            'is_listening': self.is_listening,
            'is_processing': self.is_processing,
            'current_input': self.current_input,
            'confidence_level': self.confidence_level,
            'last_activity': self.last_activity,
            'audio_buffer_size': len(self.audio_buffer),
            'selected_audio_device': self.selected_audio_device.get(),
            'sonic_modules_status': self.sonic_modules_status
        }
