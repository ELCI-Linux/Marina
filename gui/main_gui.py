#!/usr/bin/env python3
"""
Marina LLM Chat GUI - Modular Version
This is the main entry point for the GUI application, now properly modularized.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our modular components
from gui.themes.themes import ThemeManager, LLMS
from gui.components.chat_feed import ChatFeed
from gui.components.input_area import InputArea
from gui.components.llm_manager import LLMManager
from gui.components.priming_manager import PrimingManager
from gui.components.hearing_hud import HearingHUD
from gui.components.tts_manager import TTSManager, TTSStatus
from gui.components.stt_manager import STTManager, STTStatus as STTStatusEnum
from gui.components.song_display import SongDisplayWidget
from gui.components.weather_widget import WeatherWidget
from gui.components.spectra_browser import SpectraBrowserManager
# Import media upload logic from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from media_upload_logic import MediaUploadLogic
from gui.utils.utils import detect_gpu

class ModularLLMChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Marina LLM Chat - Modular")
        self.root.geometry("1200x800")
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(root)
        self.theme_manager.apply_dark_theme()
        
        # Initialize state variables
        self.initialize_state()
        
        # Build the GUI components
        self.build_gui()
        
        # Display startup message
        self.display_startup_message()
        
        print("Modular GUI initialized successfully!")
        
    def initialize_state(self):
        """Initialize application state variables"""
        self.n = 1  # Prompt counter
        self.previous_responses = {}  # Store responses from last round
        
        # Mode selection
        self.mode = tk.StringVar(value="wide")
        self.selected_llm = tk.StringVar(value=LLMS[0])
        
        # GPU detection
        self.has_gpu, self.gpu_name = detect_gpu()
        
        # LLM state management
        self.llm_enabled = {llm: tk.BooleanVar(value=self.get_default_llm_state(llm)) for llm in LLMS}
        
        # Log visibility
        self.log_visible = tk.BooleanVar(value=False)
        
    def get_default_llm_state(self, llm):
        """Get the default enabled state for an LLM based on type and GPU availability"""
        # Local LLMs that require GPU acceleration
        local_llms = ['LLaMA', 'Local', 'Mistral']
        
        if llm in local_llms:
            # Local LLMs are only enabled by default if GPU is available
            return self.has_gpu
        else:
            # Cloud-based LLMs are enabled by default
            return True
            
    def build_gui(self):
        """Build the main GUI components"""
        # Build chat feed
        self.chat_feed = ChatFeed(self.root, self.theme_manager)
        
        # Build priming manager
        self.priming_manager = PrimingManager(self.chat_feed, self.log_message)
        
        # Build LLM manager
        self.llm_manager = LLMManager(self.chat_feed, self.priming_manager, self.log_message)
        
        # Build song display widget (above input area)
        self.song_display = SongDisplayWidget(self.root, self.theme_manager)
        
        # Build weather widget
        self.weather_widget = WeatherWidget(self.root, self.theme_manager)
        
        # Build input area
        self.input_area = InputArea(self.root, self.theme_manager, self.on_submit)
        
        # Build hearing HUD
        self.hearing_hud = HearingHUD(self.root, self.theme_manager)
        
        # Build TTS manager
        self.tts_manager = TTSManager(self.theme_manager)
        self.tts_manager.add_status_callback(self.on_tts_status_change)
        
        # Build STT manager
        self.stt_manager = STTManager(self.theme_manager)
        self.stt_manager.add_status_callback(self.on_stt_status_change)
        
        # Build Spectra browser manager
        self.spectra_browser = SpectraBrowserManager(self.theme_manager)
        
        # Connect TTS to input area
        self.input_area.tts_manager = self.tts_manager
        
        # Connect STT to input area
        self.input_area.stt_manager = self.stt_manager
        
        # Connect song display to HUD
        self.connect_song_recognition()
        
        # Configure button styles
        self.configure_button_styles()
        
        # Build controls after all managers are initialized
        self.build_controls()
        
    def configure_button_styles(self):
        """Configure custom button styles"""
        style = ttk.Style()
        
        # Configure recording button style (red background)
        style.configure('Recording.TButton', 
                       background='#ff4444',
                       foreground='white',
                       borderwidth=2,
                       focuscolor='none')
        
        # Configure processing button style (orange background)
        style.configure('Processing.TButton', 
                       background='#ff8800',
                       foreground='white',
                       borderwidth=2,
                       focuscolor='none')
        
        # Configure error button style (dark red background)
        style.configure('Error.TButton', 
                       background='#cc0000',
                       foreground='white',
                       borderwidth=2,
                       focuscolor='none')
        
    def build_controls(self):
        """Build the control panel"""
        controls = ttk.Frame(self.root)
        controls.pack(fill="x", padx=5, pady=5)

        # Theme toggle button
        theme_button = ttk.Button(controls, text="🌓 Theme", command=self.toggle_theme, width=8)
        theme_button.pack(side="left", padx=5)
        
        # Log toggle button
        log_button = ttk.Button(controls, text="📋 Log", command=self.toggle_log, width=8)
        log_button.pack(side="left", padx=5)
        
        # HUD toggle button
        hud_button = ttk.Button(controls, text="🎧 HUD", command=self.toggle_hud, width=8)
        hud_button.pack(side="left", padx=5)
        
        # TTS toggle button
        self.tts_button = ttk.Button(controls, text="🔇 TTS", command=self.toggle_tts, width=8)
        self.tts_button.pack(side="left", padx=5)
        
        # STT microphone button
        self.stt_button = ttk.Button(controls, text="🎤 STT", command=self.toggle_stt, width=8)
        self.stt_button.pack(side="left", padx=5)
        
        # Browser button
        browser_button = ttk.Button(controls, text="🌐 Browser", command=self.open_browser, width=10)
        browser_button.pack(side="left", padx=5)
        
        # STT Engine Dropdown
        stt_engines = self.stt_manager.get_available_engines()
        ttk.Label(controls, text="STT Engine:").pack(side="left")
        self.stt_engine_var = tk.StringVar(value=self.stt_manager.get_engine())
        stt_engine_dropdown = ttk.Combobox(controls, textvariable=self.stt_engine_var, values=stt_engines, state="readonly", width=15)
        stt_engine_dropdown.pack(side="left", padx=5)
        stt_engine_dropdown.bind('<<ComboboxSelected>>', self.change_stt_engine)
        
        # Separator
        ttk.Separator(controls, orient="vertical").pack(side="left", fill="y", padx=10)

        # Mode selection
        ttk.Label(controls, text="Mode:").pack(side="left")
        mode_menu = ttk.Combobox(controls, textvariable=self.mode, values=["wide", "focused"], state="readonly", width=10)
        mode_menu.pack(side="left", padx=5)
        
        # Separator
        ttk.Separator(controls, orient="vertical").pack(side="left", fill="y", padx=10)
        
        # LLM status indicators (simplified for now)
        ttk.Label(controls, text="LLMs:").pack(side="left")
        for llm in LLMS:
            # Create simple status indicator
            status_text = "✓" if self.llm_enabled[llm].get() else "✗"
            color = "green" if self.llm_enabled[llm].get() else "red"
            label = ttk.Label(controls, text=f"{llm}: {status_text}", foreground=color)
            label.pack(side="left", padx=5)
        
        # Add LLM selector for focused mode
        ttk.Separator(controls, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Label(controls, text="Focus:").pack(side="left")
        llm_menu = ttk.Combobox(controls, textvariable=self.selected_llm, values=LLMS, state="readonly", width=10)
        llm_menu.pack(side="left", padx=5)
        
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        is_dark = self.theme_manager.toggle_theme()
        
        # Update chat feed theme
        self.chat_feed.theme_manager = self.theme_manager
        
        # You would normally refresh all components here
        # For now, just print the theme change
        print(f"Theme changed to {'dark' if is_dark else 'light'}")
        
    def toggle_log(self):
        """Toggle log visibility"""
        self.log_visible.set(not self.log_visible.get())
        if self.log_visible.get():
            print("Log enabled")
        else:
            print("Log disabled")
            
    def toggle_hud(self):
        """Toggle HUD visibility"""
        self.hearing_hud.toggle_hud()
        if self.hearing_hud.is_visible:
            print("HUD enabled")
            # Start real-time audio processing
            self.start_real_audio_processing()
        else:
            print("HUD disabled")
            # Stop real-time audio processing
            self.stop_real_audio_processing()
            
    def toggle_tts(self):
        """Toggle TTS functionality"""
        enabled = self.tts_manager.toggle_tts()
        if enabled:
            print("TTS enabled")
        else:
            print("TTS disabled")
            
    def toggle_stt(self):
        """Toggle STT recording via input area"""
        if hasattr(self.input_area, 'toggle_recording'):
            self.input_area.toggle_recording()
        else:
            print("STT not available in input area")
            
    def on_tts_status_change(self, status, enabled):
        """Handle TTS status changes"""
        # Update TTS button appearance based on status
        if not enabled:
            self.tts_button.config(text="🔇 TTS")
        elif status == TTSStatus.PLAYING:
            self.tts_button.config(text="🔊 TTS")
        elif status == TTSStatus.GENERATING:
            self.tts_button.config(text="⏳ TTS")
        else:
            self.tts_button.config(text="🔉 TTS")
            
    def change_stt_engine(self, event=None):
        """Change STT engine based on dropdown selection"""
        selected_engine = self.stt_engine_var.get()
        if self.stt_manager.set_engine(selected_engine):
            print(f"STT engine changed to {selected_engine} successfully.")
        else:
            print(f"Failed to change STT engine to {selected_engine}.")
        
    def on_stt_status_change(self, status):
        """Handle STT status changes"""
        # Update STT button appearance based on status
        if status == STTStatusEnum.IDLE:
            self.stt_button.config(text="🎤 STT", style="TButton")
        elif status == STTStatusEnum.LISTENING:
            self.stt_button.config(text="🔴 STT", style="Recording.TButton")
        elif status == STTStatusEnum.PROCESSING:
            self.stt_button.config(text="⏳ STT", style="Processing.TButton")
        elif status == STTStatusEnum.ERROR:
            self.stt_button.config(text="❌ STT", style="Error.TButton")
            
    def open_browser(self):
        """Open Chromium browser with Marina widgets"""
        try:
            import subprocess
            import threading
            
            # Path to the Marina browser launcher script (use standalone version)
            launcher_script = os.path.join(os.path.dirname(__file__), '..', 'spectra', 'launch_marina_browser_standalone.py')
            
            # Launch the Marina browser in a separate thread
            def launch_browser():
                try:
                    result = subprocess.run(
                        [sys.executable, launcher_script],
                        capture_output=True,
                        text=True,
                        cwd=os.path.dirname(__file__)
                    )
                    
                    if result.returncode == 0:
                        print("Marina browser launched successfully")
                    else:
                        print(f"Marina browser launch failed: {result.stderr}")
                        
                except Exception as e:
                    print(f"Error launching Marina browser: {e}")
            
            # Start browser launch in background thread
            browser_thread = threading.Thread(target=launch_browser, daemon=True)
            browser_thread.start()
            
            self.chat_feed.append_chat("System", "🌐 Marina browser with AI widgets is launching...", "action")
            print("Marina browser launch initiated")
            
        except Exception as e:
            error_msg = f"Failed to launch Marina browser: {str(e)}"
            self.chat_feed.append_chat("System", f"❌ {error_msg}", "action")
            print(f"Error launching Marina browser: {e}")
            
    def on_submit(self, user_input):
        """Handle user input submission"""
        # If HUD is visible, show the input as recognized speech
        if self.hearing_hud.is_visible:
            # Update HUD with the recognized input
            self.hearing_hud.update_input(f"Recognized: {user_input}", 0.9)
            
        # Get attachments from input area
        attachments = self.input_area.get_attachments()
        
        # Add user message to chat (with attachment info if any)
        if attachments:
            attachment_info = f" [{len(attachments)} attachment(s)]"
            self.chat_feed.append_chat("You", user_input + attachment_info, "user")
            
            # Log attachment details
            for att in attachments:
                self.log_message(f"Attachment: {att['name']} ({att['size']}) - {att['path']}")
        else:
            self.chat_feed.append_chat("You", user_input, "user")
        
        # Determine which LLMs to query
        if self.mode.get() == "wide":
            # In wide mode, query all enabled LLMs
            targets = [llm for llm in LLMS if self.llm_enabled[llm].get()]
        else:
            # In focused mode, query only selected LLM if it's enabled
            targets = [self.selected_llm.get()] if self.llm_enabled[self.selected_llm.get()].get() else []
        
        if not targets:
            self.chat_feed.append_chat("System", "No LLMs are enabled. Please enable at least one LLM to continue.", "user")
            return
        
        # Analyze and optimize media upload before querying
        media_logic = MediaUploadLogic()
        actions = media_logic.analyze_and_optimize(user_input, attachments, self.selected_llm.get())
        
        # Log optimization actions
        for name, action in actions:
            self.log_message(f"Attachment: {name} - {action}")
        
        # Query the selected LLMs using the LLM manager (with attachments)
        self.llm_manager.query_multiple_llms(targets, user_input, attachments)
        
        # Clear attachments after submission
        self.input_area.clear_attachments()
            
        # Increment prompt counter
        self.n += 1
        
    def connect_song_recognition(self):
        """Connect the song recognition system to the main window display"""
        # Wait a moment for the HUD to initialize
        def delayed_connection():
            print(f"Attempting to connect song recognition...")
            print(f"HUD has song_recognition_manager: {hasattr(self.hearing_hud, 'song_recognition_manager')}")
            
            if hasattr(self.hearing_hud, 'song_recognition_manager'):
                print(f"Song recognition manager exists: {self.hearing_hud.song_recognition_manager is not None}")
                if self.hearing_hud.song_recognition_manager:
                    print(f"Song recognition manager is running: {self.hearing_hud.song_recognition_manager.is_running}")
                    
                    # Clear existing callbacks
                    self.hearing_hud.song_recognition_manager.callbacks.clear()
                    
                    # Add our callback
                    self.hearing_hud.song_recognition_manager.add_callback(self.on_song_recognized)
                    
                    # Connect the song recognition manager to the song display widget
                    self.song_display.set_song_recognition_manager(self.hearing_hud.song_recognition_manager)
                    
                    print("Song recognition connected successfully")
                else:
                    print("Song recognition manager is None")
            else:
                print("Song recognition manager attribute not found")
        
        # Delay the connection to allow HUD initialization
        self.root.after(1000, delayed_connection)
            
    def on_song_recognized(self, song_name, artist_name):
        """Handle song recognition results"""
        if song_name and artist_name:
            # Update the song display in the main window
            self.song_display.update_song(song_name, artist_name)
            
            # Log the recognition
            self.log_message(f"Song recognized: {song_name} by {artist_name}")
        else:
            # Clear the display if no song is recognized
            self.song_display.clear_song()
            
    def start_real_audio_processing(self):
        """Start real-time audio processing"""
        try:
            self.hearing_hud.start_real_time_audio_processing()
            print("Real-time audio processing started")
        except Exception as e:
            print(f"Failed to start real-time audio processing: {e}")
            self.hearing_hud.update_input(f"Audio processing failed: {str(e)}", 0.0)
            
    def stop_real_audio_processing(self):
        """Stop real-time audio processing"""
        try:
            self.hearing_hud.stop_real_time_audio_processing()
            print("Real-time audio processing stopped")
        except Exception as e:
            print(f"Failed to stop real-time audio processing: {e}")
            
    def demo_hud_functionality(self):
        """Demonstrate HUD functionality"""
        import threading
        import time
        
        def demo_sequence():
            # Wait a bit for HUD to fully appear
            time.sleep(1)
            
            # Show ambient listening
            self.hearing_hud.simulate_ambient_listening()
            
            # Wait and show another interaction
            time.sleep(3)
            
            # Simulate a different speech input
            if self.hearing_hud.is_visible:
                self.hearing_hud.simulate_speech_input("Show me the weather forecast for tomorrow")
            
        # Run demo in background thread
        thread = threading.Thread(target=demo_sequence)
        thread.daemon = True
        thread.start()
        
    def log_message(self, message):
        """Log a message (for now just print)"""
        if self.log_visible.get():
            print(f"[LOG] {message}")
        else:
            print(f"[LOG] {message}")
        
    def display_startup_message(self):
        """Display startup messages"""
        self.chat_feed.append_chat("System", "Marina Agentic Intelligence Framework - Modular Version", "user")
        
        if self.has_gpu:
            self.chat_feed.append_chat("System", f"GPU detected: {self.gpu_name}", "action")
        else:
            self.chat_feed.append_chat("System", "No GPU detected - local LLMs will be disabled", "action")
            
        self.chat_feed.append_chat("System", "System initialized and ready for user input.", "user")

def main():
    """Main entry point"""
    print("Starting Marina LLM Chat GUI (Modular Version)...")
    
    # Create the main window
    root = tk.Tk()
    
    # Create the application
    app = ModularLLMChatApp(root)
    
    # Start the GUI event loop
    root.mainloop()

if __name__ == "__main__":
    main()
