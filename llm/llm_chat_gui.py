import sys
import os
import sounddevice as sd
import wavio
import subprocess
from faster_whisper import WhisperModel
import tempfile
import pyttsx3
import time
import socket
import requests
import asyncio
import threading
from shazamio import Shazam
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import key_env_loader
key_env_loader.load_env_keys(verbose=True)

import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import threading
from llm.llm_router import query_llm_response
from brain.action_engine import run_action_command  # ← Import the action runner
from brain.code_detector import interpret_code_from_response  # ← Import code detection

def record_audio(filename="temp_clip.wav", duration=7, fs=44100):
    print("Listening...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    wavio.write(filename, recording, fs, sampwidth=2)
    print(f"Saved audio to {filename}")
    return filename

LLMS = ["GPT-4", "Claude", "Gemini", "DeepSeek", "Mistral", "LLaMA", "Local"]

# Context window limits for each LLM (in tokens)
CONTEXT_LIMITS = {
    "GPT-4": 128000,
    "Claude": 200000,
    "Gemini": 128000,
    "DeepSeek": 128000,
    "Mistral": 32000,
    "LLaMA": 128000,
    "Local": 8000
}

# Ping endpoints for web-based LLMs
PING_ENDPOINTS = {
    "GPT-4": "api.openai.com",
    "Claude": "api.anthropic.com",
    "Gemini": "generativelanguage.googleapis.com",
    "DeepSeek": "api.deepseek.com",
    "Mistral": "api.mistral.ai",
    "LLaMA": "api.together.xyz",
    # "Local" is excluded as it's not web-based
}

# Light theme colors
LIGHT_COLORS = {
    "GPT-4": "#cce5ff",
    "Claude": "#d4edda",
    "Gemini": "#fff3cd",
    "DeepSeek": "#ffe4e1",
    "Mistral": "#f8d7da",
    "LLaMA": "#e2e3e5",
    "Local": "#d1c4e9"
}

# Dark theme colors
DARK_COLORS = {
    "GPT-4": "#1a4d80",
    "Claude": "#2d5a3d",
    "Gemini": "#665c2d",
    "DeepSeek": "#663d3a",
    "Mistral": "#664044",
    "LLaMA": "#4a4d52",
    "Local": "#52497a"
}

# Dark theme configuration with a blue tint
DARK_THEME = {
    "bg": "#1b1b32",
    "fg": "#ffffff",
    "select_bg": "#2f2f5f",
    "select_fg": "#ffffff",
    "entry_bg": "#2f2f5f",
    "entry_fg": "#ffffff",
    "button_bg": "#2f2f5f",
    "button_fg": "#ffffff",
    "button_active_bg": "#3e3e7b",
    "scrollbar_bg": "#2f2f5f",
    "scrollbar_fg": "#666699"
}

class LLMChatApp:
    def __init__(self, root):
        self.n = 1  # Prompt counter
        self.previous_responses = {}  # Store responses from last round
        self.prime_prefix = self.get_priming_text()  # Only fetched once

        self.root = root
        self.root.title("LLM Groupchat")
        self.root.geometry("1200x800")  # Set larger window size
        
        # Dark theme setup
        self.dark_theme = tk.BooleanVar(value=True)  # Default to dark theme
        self.colors = DARK_COLORS if self.dark_theme.get() else LIGHT_COLORS
        self.apply_dark_theme()

        self.mode = tk.StringVar(value="wide")
        self.selected_llm = tk.StringVar(value=LLMS[0])
        self.agent_mode_enabled = tk.BooleanVar(value=False)
        self.agent_controls_frame = ttk.Frame(self.root)
        
        # Initialize log_visible first before any logging operations
        self.log_visible = tk.BooleanVar(value=False)
        self.log_frame = None
        
        # GPU detection
        self.has_gpu = self.detect_gpu()
        
        # Dictionary to track enabled/disabled state for each LLM
        # Local LLMs are disabled by default unless GPU is available
        self.llm_enabled = {llm: tk.BooleanVar(value=self.get_default_llm_state(llm)) for llm in LLMS}
        self.llm_buttons = {}
        self.llm_logos = {}
        self.loading_labels = {}  # Track loading indicators for each LLM
        self.llm_failed = {llm: False for llm in LLMS}  # Track failed LLMs
        self.llm_failure_reasons = {llm: None for llm in LLMS}  # Store failure reasons
        
        # Attachment system
        self.attachments = []  # List of attachment file paths
        self.attachment_buttons = {}  # Track attachment buttons
        self.attachment_frame = None  # Frame for attachment display
        self.long_press_timer = None  # Timer for long press detection
        self.long_press_widget = None  # Widget being long pressed
        
        # Message collapsing system
        self.message_counter = 0
        self.collapsed_messages = set()  # Track which messages are collapsed
        self.message_data = {}  # Store full message content
        
        # Speech-to-text variables
        self.is_recording = False
        self.recording_thread = None
        self.recording_stop_event = None
        self.whisper_model = None
        self.mic_button = None
        
        # Text-to-speech variables
        self.tts_engine = None
        self.tts_enabled = tk.BooleanVar(value=True)
        
        # Context window tracking
        self.context_bars = {}  # Store context bar widgets
        self.context_usage = {llm: 0 for llm in LLMS}  # Track token usage
        
        # Network latency tracking
        self.ping_times = {llm: None for llm in LLMS}  # Store ping times in ms
        self.ping_labels = {}  # Store ping label widgets
        self.ping_thread = None  # Thread for periodic pinging
        
        # Shazamio music recognition
        self.shazam = None  # Shazam instance
        self.music_recognition_enabled = tk.BooleanVar(value=True)
        self.current_song = "No song detected"
        self.music_hud = None  # Music HUD widget
        self.music_recognition_thread = None
        self.music_recognition_running = False
        
        # Microphone meter variables
        self.mic_level = 0.0  # Current microphone level (0.0 to 1.0)
        self.mic_meter_canvas = None  # Canvas for microphone meter
        self.mic_meter_frame = None  # Frame for microphone meter
        
        self.load_logos()
        self.build_controls()
        self.build_context_bars()
        self.build_chat_feed()
        self.build_input_area()
        self.build_log_area()
        self.build_agent_controls()
        # self.build_music_hud()  # DISABLED: Causes segmentation fault
        
        # Display priming information at startup
        self.display_startup_priming()
        
        # Initialize context bars after GUI is built
        self.root.after(100, self.update_all_context_bars)
        
        # Start periodic ping monitoring
        self.start_ping_monitoring()
        
        # Start music recognition after GUI is built
        # DISABLED: Music recognition causes segmentation fault
        # self.start_music_recognition()
    
    def detect_gpu(self):
        """Detect if a GPU is available for local LLM processing"""
        try:
            # Check for NVIDIA GPU using nvidia-smi
            result = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                gpu_name = result.stdout.strip()
                self.log_message(f"NVIDIA GPU detected: {gpu_name}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Check for AMD GPU using rocm-smi
            result = subprocess.run(["rocm-smi", "--showproductname"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and "GPU" in result.stdout:
                self.log_message("AMD GPU detected via rocm-smi")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Check for GPU via lspci
            result = subprocess.run(["lspci", "-nn"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_indicators = ['VGA', 'Display', 'NVIDIA', 'AMD', 'Radeon', 'GeForce']
                for line in result.stdout.split('\n'):
                    if any(indicator in line for indicator in gpu_indicators):
                        if any(gpu_brand in line for gpu_brand in ['NVIDIA', 'AMD', 'Radeon', 'GeForce']):
                            self.log_message(f"GPU detected via lspci: {line.strip()}")
                            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Check for GPU via /proc/driver/nvidia/version
            if os.path.exists('/proc/driver/nvidia/version'):
                with open('/proc/driver/nvidia/version', 'r') as f:
                    version_info = f.read().strip()
                    if version_info:
                        self.log_message(f"NVIDIA driver detected: {version_info}")
                        return True
        except Exception:
            pass
        
        self.log_message("No GPU detected - local LLMs will be disabled by default")
        return False
    
    def get_default_llm_state(self, llm):
        """Get the default enabled state for an LLM based on type and GPU availability"""
        # Local LLMs that require GPU acceleration
        local_llms = ['LLaMA', 'Local', 'Mistral']  # Add more as needed
        
        if llm in local_llms:
            # Local LLMs are only enabled by default if GPU is available
            return self.has_gpu
        else:
            # Cloud-based LLMs are enabled by default
            return True
    
    def apply_dark_theme(self):
        """Apply dark theme to the root window and configure ttk styles"""
        if self.dark_theme.get():
            self.root.configure(bg=DARK_THEME["bg"])
            
            # Configure ttk styles for dark theme
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure ttk widgets for dark theme
            style.configure('TFrame', background=DARK_THEME["bg"])
            style.configure('TLabel', background=DARK_THEME["bg"], foreground=DARK_THEME["fg"], font=('Ubuntu', 10))
            style.configure('TButton', background=DARK_THEME["button_bg"], foreground=DARK_THEME["button_fg"], font=('Ubuntu', 10))
            style.map('TButton', background=[('active', DARK_THEME["button_active_bg"])])
            style.configure('TEntry', fieldbackground=DARK_THEME["entry_bg"], foreground=DARK_THEME["entry_fg"], bordercolor=DARK_THEME["scrollbar_fg"], font=('Ubuntu', 10))
            style.configure('TCombobox', fieldbackground=DARK_THEME["entry_bg"], foreground=DARK_THEME["entry_fg"], bordercolor=DARK_THEME["scrollbar_fg"], font=('Ubuntu', 10))
            style.configure('TCheckbutton', background=DARK_THEME["bg"], foreground=DARK_THEME["fg"], font=('Ubuntu', 10))
            style.configure('TSeparator', background=DARK_THEME["scrollbar_fg"])
        else:
            self.root.configure(bg="#f0f0f0")
            style = ttk.Style()
            style.theme_use('default')

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.dark_theme.set(not self.dark_theme.get())
        self.colors = DARK_COLORS if self.dark_theme.get() else LIGHT_COLORS
        self.apply_dark_theme()
        self.refresh_ui()

    def refresh_ui(self):
        """Refresh UI elements after theme change"""
        # Update chat feed colors
        if self.dark_theme.get():
            self.chat_frame.configure(bg=DARK_THEME["bg"], fg=DARK_THEME["fg"])
        else:
            self.chat_frame.configure(bg="white", fg="black")
        
        # Update chat tags
        for llm in LLMS:
            self.chat_frame.tag_config(llm, background=self.colors[llm])
        
        # Update LLM buttons
        for llm in LLMS:
            if self.llm_enabled[llm].get():
                if llm in self.llm_logos:
                    self.llm_buttons[llm].config(bg=self.colors[llm])
                else:
                    self.llm_buttons[llm].config(bg=self.colors[llm], fg="white" if self.dark_theme.get() else "black")

    def load_logos(self):
        """Load logo images for LLMs that have them available"""
        logo_files = {
            "Gemini": "gemini_logo.png",
            "DeepSeek": "DeepSeek_logo.png"
        }
        
        for llm, filename in logo_files.items():
            try:
                if os.path.exists(filename):
                    img = Image.open(filename)
                    img = img.resize((24, 24), Image.Resampling.LANCZOS)
                    self.llm_logos[llm] = ImageTk.PhotoImage(img)
                    # Create greyed out version for disabled state
                    grey_img = img.convert('L').convert('RGB')
                    self.llm_logos[f"{llm}_grey"] = ImageTk.PhotoImage(grey_img)
            except Exception as e:
                print(f"Could not load logo for {llm}: {e}")

    def build_controls(self):
        controls = ttk.Frame(self.root)
        controls.pack(fill="x", padx=5, pady=5)

        # Theme toggle button
        theme_button = ttk.Button(controls, text="🌓 Theme", command=self.toggle_theme, width=8)
        theme_button.pack(side="left", padx=5)
        
        # Log toggle button
        log_button = ttk.Button(controls, text="📋 Log", command=self.toggle_log, width=8)
        log_button.pack(side="left", padx=5)
        
        # Separator
        ttk.Separator(controls, orient="vertical").pack(side="left", fill="y", padx=10)

        # Mode selection
        ttk.Label(controls, text="Mode:").pack(side="left")
        mode_menu = ttk.Combobox(controls, textvariable=self.mode, values=["wide", "focused"], state="readonly", width=10)
        mode_menu.pack(side="left", padx=5)
        mode_menu.bind("<<ComboboxSelected>>", lambda e: None)
        
        # Separator
        ttk.Separator(controls, orient="vertical").pack(side="left", fill="y", padx=10)
        
        # LLM toggle buttons
        ttk.Label(controls, text="LLMs:").pack(side="left")
        llm_buttons_frame = ttk.Frame(controls)
        llm_buttons_frame.pack(side="left", padx=5)
        
        for llm in LLMS:
            self.create_llm_button(llm_buttons_frame, llm)
        
        # Add LLM selector for focused mode
        ttk.Separator(controls, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Label(controls, text="Focus:").pack(side="left")
        llm_menu = ttk.Combobox(controls, textvariable=self.selected_llm, values=LLMS, state="readonly", width=10)
        llm_menu.pack(side="left", padx=5)
    
    def create_llm_button(self, parent, llm):
        """Create a toggle button for an LLM with logo (if available) or text"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(side="left", padx=2)
        
        # Check if we have a logo for this LLM
        has_logo = llm in self.llm_logos
        
        if has_logo:
            # Create image button
            button = tk.Button(
                button_frame,
                image=self.llm_logos[llm],
                command=lambda: self.toggle_llm(llm),
                relief="solid",
                borderwidth=2,
                bg=self.colors[llm],
                activebackground=self.colors[llm],
                fg="white" if self.dark_theme.get() else "black",
                font=("Ubuntu", 8, "bold"),
                height=30
            )
            # Add tooltip with LLM name
            self.create_tooltip(button, llm)
        else:
            # Create text button
            button = tk.Button(
                button_frame,
                text=llm,
                command=lambda: self.toggle_llm(llm),
                relief="solid",
                borderwidth=2,
                bg=self.colors[llm],
                activebackground=self.colors[llm],
                fg="white" if self.dark_theme.get() else "black",
                font=("Ubuntu", 8, "bold"),
                width=8,
                height=2
            )
        
        button.pack()
        self.llm_buttons[llm] = button
        
        # Create status label below button - set based on actual enabled state
        initial_state = self.llm_enabled[llm].get()
        status_text = "ON" if initial_state else "OFF"
        status_color = "green" if initial_state else "red"
        status_label = ttk.Label(button_frame, text=status_text, font=("Ubuntu", 7), foreground=status_color)
        status_label.pack()
        self.llm_buttons[f"{llm}_status"] = status_label
        
        # Set initial button appearance based on enabled state
        if not initial_state:
            disabled_bg = "#404040" if self.dark_theme.get() else "#f0f0f0"
            disabled_fg = "#666666" if self.dark_theme.get() else "gray"
            if llm in self.llm_logos:
                button.config(image=self.llm_logos[f"{llm}_grey"], bg=disabled_bg)
            else:
                button.config(bg=disabled_bg, fg=disabled_fg)
        
        # Create ping label below status (initially hidden for Local LLM)
        if llm in PING_ENDPOINTS:
            ping_label = ttk.Label(button_frame, text="...", font=("Ubuntu", 6), foreground="gray")
            ping_label.pack()
            self.ping_labels[llm] = ping_label
        
        # Create loading indicator (initially hidden)
        loading_label = ttk.Label(button_frame, text="⏳", font=("Ubuntu", 8), foreground="orange")
        self.loading_labels[llm] = loading_label
    
    def create_tooltip(self, widget, text):
        """Create a simple tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            tooltip_bg = "#555555" if self.dark_theme.get() else "lightyellow"
            tooltip_fg = "white" if self.dark_theme.get() else "black"
            label = tk.Label(tooltip, text=text, background=tooltip_bg, foreground=tooltip_fg, relief="solid", borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def handle_llm_failure(self, llm, error_message):
        """Handle an individual LLM failure"""
        # Mark the LLM as failed
        self.llm_failed[llm] = True
        self.llm_failure_reasons[llm] = error_message
        
        # Disable the LLM
        if self.llm_enabled[llm].get():
            self.toggle_llm(llm)
        
        # Log the failure
        self.log_message(f"{llm} has been automatically disabled due to failure: {error_message}")
        self.append_chat("System", f"⚠️ {llm} has been disabled due to failure: {error_message[:150]}...", "user")
        
    def clear_llm_failure(self, llm):
        """Clear failure state for an LLM after it has been re-enabled"""
        self.llm_failed[llm] = False
        self.llm_failure_reasons[llm] = None
        
        # Log the successful reactivation
        self.log_message(f"{llm} failure cleared and ready for use")

    def toggle_llm(self, llm):
        """Toggle the enabled/disabled state of an LLM"""
        current_state = self.llm_enabled[llm].get()
        new_state = not current_state
        self.llm_enabled[llm].set(new_state)
        
        button = self.llm_buttons[llm]
        status_label = self.llm_buttons[f"{llm}_status"]
        
        if new_state:  # Enabled
            # Clear failure state when manually re-enabling
            if self.llm_failed[llm]:
                self.clear_llm_failure(llm)
            
            if llm in self.llm_logos:
                button.config(image=self.llm_logos[llm], bg=self.colors[llm])
            else:
                button.config(bg=self.colors[llm], fg="white" if self.dark_theme.get() else "black")
            status_label.config(text="ON", foreground="green")
            
            # Log the reactivation
            self.log_message(f"{llm} manually reactivated")
            self.append_chat("System", f"🔄 {llm} has been manually reactivated", "action")
            
        else:  # Disabled
            disabled_bg = "#404040" if self.dark_theme.get() else "#f0f0f0"
            disabled_fg = "#666666" if self.dark_theme.get() else "gray"
            if llm in self.llm_logos:
                button.config(image=self.llm_logos[f"{llm}_grey"], bg=disabled_bg)
            else:
                button.config(bg=disabled_bg, fg=disabled_fg)
            status_label.config(text="OFF", foreground="red")

    def build_context_bars(self):
        """Build context window bars for each LLM"""
        self.context_frame = ttk.Frame(self.root)
        self.context_frame.pack(fill="x", padx=8, pady=(0, 4))
        
        # Title label
        title_label = ttk.Label(self.context_frame, text="Context Windows:", font=("Ubuntu", 10, "bold"))
        title_label.pack(anchor="w")
        
        # Create individual context bars for each LLM
        for llm in LLMS:
            bar_frame = ttk.Frame(self.context_frame)
            bar_frame.pack(fill="x", pady=1)
            
            # LLM label
            llm_label = ttk.Label(bar_frame, text=f"{llm}:", font=("Ubuntu", 9), width=10)
            llm_label.pack(side="left")
            
            # Progress bar container
            progress_frame = tk.Frame(bar_frame, bg=DARK_THEME["bg"] if self.dark_theme.get() else "white", height=16)
            progress_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))
            
            # Progress bar (initially full - 0% used)
            progress_bar = tk.Canvas(
                progress_frame, 
                height=14,
                bg=DARK_THEME["entry_bg"] if self.dark_theme.get() else "#f0f0f0",
                highlightthickness=0
            )
            progress_bar.pack(fill="both", expand=True)
            
            # Percentage label
            percent_label = ttk.Label(bar_frame, text="0%", font=("Ubuntu", 8), width=4)
            percent_label.pack(side="right", padx=(5, 0))
            
            # Token count label
            token_label = ttk.Label(bar_frame, text="0 tokens", font=("Ubuntu", 8), width=10)
            token_label.pack(side="right")
            
            # Store references
            self.context_bars[llm] = {
                'canvas': progress_bar,
                'percent_label': percent_label,
                'token_label': token_label
            }
            
            # Initial draw
            self.update_context_bar(llm, 0)
    
    def estimate_tokens(self, text):
        """Estimate token count for text (rough approximation)"""
        # Rough approximation: 1 token ≈ 4 characters for English text
        # This is a simplification - real tokenization is more complex
        return len(text) // 4
    
    def update_context_bar(self, llm, token_count):
        """Update the context bar for a specific LLM"""
        if llm not in self.context_bars:
            return
            
        bar_data = self.context_bars[llm]
        canvas = bar_data['canvas']
        percent_label = bar_data['percent_label']
        token_label = bar_data['token_label']
        
        # Calculate usage percentage
        max_tokens = CONTEXT_LIMITS[llm]
        usage_percent = min(100, (token_count / max_tokens) * 100)
        
        # Update the canvas
        canvas.delete("all")
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width > 1:  # Only draw if canvas is properly sized
            # Background (unused portion)
            canvas.create_rectangle(
                0, 0, canvas_width, canvas_height,
                fill=DARK_THEME["entry_bg"] if self.dark_theme.get() else "#f0f0f0",
                outline=""
            )
            
            # Used portion
            used_width = int((usage_percent / 100) * canvas_width)
            if used_width > 0:
                # Color based on usage level
                if usage_percent < 50:
                    color = "#4CAF50"  # Green
                elif usage_percent < 75:
                    color = "#FF9800"  # Orange
                else:
                    color = "#F44336"  # Red
                
                canvas.create_rectangle(
                    0, 0, used_width, canvas_height,
                    fill=color,
                    outline=""
                )
        
        # Update labels
        percent_label.config(text=f"{usage_percent:.1f}%")
        token_label.config(text=f"{token_count:,} tokens")
    
    def update_all_context_bars(self):
        """Update all context bars based on current conversation state"""
        for llm in LLMS:
            # Calculate total tokens for this LLM
            total_tokens = 0
            
            # Add priming text tokens
            total_tokens += self.estimate_tokens(self.prime_prefix)
            
            # Add current user input tokens
            current_input = self.entry.get(1.0, tk.END).strip()
            total_tokens += self.estimate_tokens(current_input)
            
            # Add conversation history tokens
            if self.n > 1:
                for response in self.previous_responses.values():
                    total_tokens += self.estimate_tokens(response)
            
            # Add attachment tokens
            for attachment_path in self.attachments:
                total_tokens += self.estimate_file_tokens(attachment_path)
            
            # Update the context usage and bar
            self.context_usage[llm] = total_tokens
            self.update_context_bar(llm, total_tokens)

    def build_chat_feed(self):
        # Configure chat frame with dark theme support
        chat_bg = DARK_THEME["bg"] if self.dark_theme.get() else "white"
        chat_fg = DARK_THEME["fg"] if self.dark_theme.get() else "black"
        
        self.chat_frame = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD, 
            font=("Ubuntu", 12),
            bg=chat_bg,
            fg=chat_fg,
            insertbackground=DARK_THEME["fg"] if self.dark_theme.get() else "black",
            selectbackground=DARK_THEME["select_bg"] if self.dark_theme.get() else "#316AC5",
            selectforeground=DARK_THEME["select_fg"] if self.dark_theme.get() else "white"
        )
        self.chat_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Configure text tags
        user_fg = DARK_THEME["fg"] if self.dark_theme.get() else "black"
        action_fg = "#87CEEB" if self.dark_theme.get() else "blue"
        
        self.chat_frame.tag_config("user", foreground=user_fg, font=("Ubuntu", 12, "bold"))
        for llm in LLMS:
            self.chat_frame.tag_config(llm, background=self.colors[llm], lmargin1=10, lmargin2=10, spacing3=6, font=("Ubuntu", 11))
        self.chat_frame.tag_config("action", foreground=action_fg, font=("Ubuntu Mono", 10))
        self.chat_frame.tag_config("prompt", foreground="#FFD700" if self.dark_theme.get() else "#B8860B", font=("Ubuntu", 11, "italic"))

    def build_input_area(self):
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill="x", padx=8, pady=8)

        # Create a frame for the text input area
        text_frame = ttk.Frame(input_frame)
        text_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Replace Entry with Text widget for multi-line support
        input_bg = DARK_THEME["entry_bg"] if self.dark_theme.get() else "white"
        input_fg = DARK_THEME["entry_fg"] if self.dark_theme.get() else "black"
        
        self.entry = tk.Text(
            text_frame,
            font=("Ubuntu", 11),
            height=4,  # Minimum 4 lines
            wrap=tk.WORD,
            bg=input_bg,
            fg=input_fg,
            insertbackground=DARK_THEME["fg"] if self.dark_theme.get() else "black",
            selectbackground=DARK_THEME["select_bg"] if self.dark_theme.get() else "#316AC5",
            selectforeground=DARK_THEME["select_fg"] if self.dark_theme.get() else "white",
            relief="solid",
            borderwidth=1
        )
        self.entry.pack(fill="both", expand=True)
        
        # Add scrollbar for the text area
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.entry.yview)
        scrollbar.pack(side="right", fill="y")
        self.entry.config(yscrollcommand=scrollbar.set)
        
        # Bind Ctrl+Return and Shift+Return to submit (Return key now only creates new lines)
        self.entry.bind("<Control-Return>", self.on_submit)
        self.entry.bind("<Shift-Return>", self.on_submit)
        
        # Ensure Return key only creates new line behavior
        # The Text widget naturally handles Return for new lines
        
        # Bind text changes to update context bars
        self.entry.bind("<KeyRelease>", self.on_text_change)
        self.entry.bind("<ButtonRelease>", self.on_text_change)

        # Microphone button with clearer labeling
        self.mic_button = ttk.Button(
            input_frame, 
            text="🎤 Record", 
            command=self.toggle_recording,
            width=10
        )
        self.mic_button.pack(side="right", padx=5)
        
        # Code detection toggle button
        self.code_detection_enabled = tk.BooleanVar(value=True)
        code_button = ttk.Button(
            input_frame,
            text="💻 Code",
            command=self.toggle_code_detection,
            width=8
        )
        code_button.pack(side="right", padx=5)
        
        # TTS toggle button
        tts_button = ttk.Button(
            input_frame,
            text="🔊 TTS",
            command=self.toggle_tts,
            width=8
        )
        tts_button.pack(side="right", padx=5)
        
        # Attachment button
        attachment_button = ttk.Button(
            input_frame,
            text="📎 Attach",
            command=self.select_attachment,
            width=8
        )
        attachment_button.pack(side="right", padx=5)

        submit = ttk.Button(input_frame, text="Send", command=self.on_submit)
        submit.pack(side="right", padx=5)
        
        # Create attachment display frame (initially hidden)
        self.attachment_frame = ttk.Frame(input_frame)
        self.attachment_frame.pack(side="top", fill="x", pady=(5, 0))

    def build_log_area(self):
        """Build the log area that can be toggled on/off"""
        # This will be created dynamically when toggled
        pass

    def toggle_log(self):
        """Toggle the log area visibility"""
        if self.log_visible.get():
            # Hide log
            if self.log_frame:
                self.log_frame.destroy()
                self.log_frame = None
            self.log_visible.set(False)
        else:
            # Show log
            self.log_frame = ttk.Frame(self.root)
            self.log_frame.pack(fill="both", expand=False, padx=8, pady=4)
            
            log_label = ttk.Label(self.log_frame, text="Log Output:", font=("Ubuntu", 10, "bold"))
            log_label.pack(anchor="w")
            
            # Configure log text area
            log_bg = DARK_THEME["bg"] if self.dark_theme.get() else "white"
            log_fg = DARK_THEME["fg"] if self.dark_theme.get() else "black"
            
            self.log_text = scrolledtext.ScrolledText(
                self.log_frame,
                wrap=tk.WORD,
                font=("Ubuntu Mono", 9),
                height=8,
                bg=log_bg,
                fg=log_fg,
                insertbackground=DARK_THEME["fg"] if self.dark_theme.get() else "black",
                selectbackground=DARK_THEME["select_bg"] if self.dark_theme.get() else "#316AC5",
                selectforeground=DARK_THEME["select_fg"] if self.dark_theme.get() else "white"
            )
            self.log_text.pack(fill="both", expand=True)
            
            # Add some sample log content
            self.log_text.insert(tk.END, "[LOG] GUI initialized\n")
            self.log_text.insert(tk.END, "[LOG] Dark theme enabled\n")
            self.log_text.insert(tk.END, "[LOG] Ready for user input\n")
            
            self.log_visible.set(True)

    def log_message(self, message):
        """Add a message to the log if it's visible"""
        if self.log_visible.get() and hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, f"[LOG] {message}\n")
            self.log_text.see(tk.END)

    def show_loading(self, llm):
        """Show loading indicator for specific LLM"""
        if llm in self.loading_labels:
            self.loading_labels[llm].pack()
            self.animate_loading(llm)

    def hide_loading(self, llm):
        """Hide loading indicator for specific LLM"""
        if llm in self.loading_labels:
            self.loading_labels[llm].pack_forget()

    def animate_loading(self, llm):
        """Animate the loading indicator"""
        if llm in self.loading_labels and self.loading_labels[llm].winfo_viewable():
            current_text = self.loading_labels[llm].cget("text")
            if current_text == "⏳":
                self.loading_labels[llm].config(text="⌛")
            else:
                self.loading_labels[llm].config(text="⏳")
            # Continue animation
            self.root.after(500, lambda: self.animate_loading(llm))

    def on_submit(self, event=None):
        user_input = self.entry.get(1.0, tk.END).strip()
        if not user_input:
            return
        
        # Clear the input box immediately for better UX
        self.entry.delete(1.0, tk.END)
        
        # Show the prompt immediately in chat
        self.append_chat("You", user_input, "user")
        
        # Log the prompt
        self.log_message(f"User prompt: {user_input}")

        if self.mode.get() == "wide":
            # In wide mode, query all enabled LLMs
            targets = [llm for llm in LLMS if self.llm_enabled[llm].get()]
        else:
            # In focused mode, query only selected LLM if it's enabled
            targets = [self.selected_llm.get()] if self.llm_enabled[self.selected_llm.get()].get() else []
        
        if not targets:
            self.append_chat("System", "No LLMs are enabled. Please enable at least one LLM to continue.", "user")
            return
        
        # Show what prompt is being sent to each LLM
        for llm in targets:
            if self.n == 1:
                primed_prompt = self.prime_prefix + "\n\nUser: " + user_input
            else:
                llm_reactions = "\n\n".join(
                    [f"[{name} response to previous prompt]:\n{resp}" for name, resp in self.previous_responses.items()]
                )
                primed_prompt = llm_reactions + "\n\nUser: " + user_input
            
            # Show prompt being sent to LLM
            self.append_chat(f"→ {llm}", f"Processing prompt...", "prompt")
            self.log_message(f"Sending prompt to {llm}")
            
            # Show loading indicator
            self.show_loading(llm)
        
        # Process LLMs in separate threads for better responsiveness
        new_responses = {}
        
        def process_llm(llm, prompt):
            try:
                response = self.query_llm(llm, prompt)
                new_responses[llm] = response
                
                # Update UI in main thread
                self.root.after(0, lambda: self.handle_llm_response(llm, response))
            except Exception as e:
                self.root.after(0, lambda: self.handle_llm_error(llm, str(e)))
        
        # Start threads for each LLM
        for llm in targets:
            if self.n == 1:
                primed_prompt = self.prime_prefix + "\n\nUser: " + user_input
            else:
                llm_reactions = "\n\n".join(
                    [f"[{name} response to previous prompt]:\n{resp}" for name, resp in self.previous_responses.items()]
                )
                primed_prompt = llm_reactions + "\n\nUser: " + user_input
            
            thread = threading.Thread(target=process_llm, args=(llm, primed_prompt))
            thread.daemon = True
            thread.start()
        
        self.previous_responses = new_responses
        self.n += 1

    def extract_code_blocks_from_message(self, message, sender):
        """Extract code blocks from LLM messages and replace them with placeholder text"""
        if sender not in LLMS:
            return message, None
        
        code_blocks = []
        parts = message.split('```')
        processed_message = ""
        for i, part in enumerate(parts):
            if i % 2 == 0:
                processed_message += part
            else:
                code_placeholder = f"[Code Block {len(code_blocks)+1}]"
                processed_message += code_placeholder
                code_blocks.append(part)
        
        return processed_message, code_blocks

    def create_code_block_buttons(self, code_block, index, msg_id):
        """Create run, save, preview buttons for each code block"""
        button_frame = ttk.Frame(self.chat_frame)
        button_frame.pack(anchor="w", padx=20)

        # Run button
        run_button = ttk.Button(
            button_frame,
            text="Run",
            command=lambda: self.run_code(code_block),
            width=6
        )
        run_button.pack(side="left", padx=2)

        # Save button
        save_button = ttk.Button(
            button_frame,
            text="Save",
            command=lambda: self.save_code(code_block),
            width=6
        )
        save_button.pack(side="left", padx=2)

        # Preview button
        preview_button = ttk.Button(
            button_frame,
            text="Preview",
            command=lambda: self.preview_code(code_block),
            width=6
        )
        preview_button.pack(side="left", padx=2)

    def handle_llm_response(self, llm, response):
        """Handle LLM response in main thread"""
        # Hide loading indicator
        self.hide_loading(llm)
        
        # Log the response
        self.log_message(f"{llm} responded: {response[:100]}..." if len(response) > 100 else f"{llm} responded: {response}")
        
        # Add response to chat
        self.append_chat(llm, response, llm)
        
        # Handle code detection if enabled
        if self.code_detection_enabled.get():
            self.detect_and_handle_code(response)
        
        # Handle action commands
        if response.startswith("[action]"):
            action_cmd = response[len("[action]"):].strip()
            stdout, stderr = run_action_command(action_cmd)
            self.display_action_result(action_cmd, stdout, stderr)
            self.log_message(f"Action executed: {action_cmd}")

    def handle_llm_error(self, llm, error):
        """Handle LLM error in main thread"""
        # Hide loading indicator
        self.hide_loading(llm)
        
        # Log the error
        self.log_message(f"{llm} error: {error}")
        
        # Show error in chat
        self.append_chat(llm, f"Error: {error}", "user")

    def append_chat(self, sender, message, tag):
        # Store full message data
        msg_id = self.message_counter
        
        # Process message to extract code blocks if sender is an LLM
        processed_message, code_blocks = self.extract_code_blocks_from_message(message, sender)
        
        self.message_data[msg_id] = {
            'sender': sender,
            'message': processed_message,
            'original_message': message,
            'code_blocks': code_blocks,
            'tag': tag,
            'collapsed': False
        }
        
        # Create truncated version for collapsing (first 3 lines)
        lines = processed_message.split('\n')
        if len(lines) > 3 and len(processed_message) > 200:
            truncated = '\n'.join(lines[:3]) + '\n...'
            self.message_data[msg_id]['truncated'] = truncated
            self.message_data[msg_id]['is_long'] = True
        else:
            self.message_data[msg_id]['is_long'] = False
            
        self.render_message(msg_id)
        self.message_counter += 1
        self.chat_frame.see(tk.END)
        
    def render_message(self, msg_id):
        """Render a message in the chat frame"""
        msg_data = self.message_data[msg_id]
        sender = msg_data['sender']
        message = msg_data['message']
        tag = msg_data['tag']
        
        # Insert sender with clickable expand/collapse button if message is long
        if msg_data['is_long']:
            collapse_symbol = "▼" if not msg_data['collapsed'] else "▶"
            clickable_sender = f"{collapse_symbol} {sender}: "
            
            # Insert clickable sender
            start_pos = self.chat_frame.index(tk.END)
            self.chat_frame.insert(tk.END, clickable_sender, f"clickable_{msg_id}")
            
            # Configure clickable tag
            self.chat_frame.tag_config(f"clickable_{msg_id}", foreground="#87CEEB" if self.dark_theme.get() else "blue", underline=True)
            self.chat_frame.tag_bind(f"clickable_{msg_id}", "<Button-1>", lambda e: self.toggle_message_collapse(msg_id))
            
            # Insert message content
            if msg_data['collapsed']:
                display_message = msg_data['truncated']
            else:
                display_message = message
        else:
            # Regular message without collapse functionality
            self.chat_frame.insert(tk.END, f"{sender}: ", tag)
            display_message = message
            
        self.chat_frame.insert(tk.END, f"{display_message}\n", tag)
        
        # Add code block buttons if any exist
        if 'code_blocks' in msg_data and msg_data['code_blocks']:
            for i, code_block in enumerate(msg_data['code_blocks']):
                self.create_code_block_buttons(code_block, i, msg_id)
        
    def toggle_message_collapse(self, msg_id):
        """Toggle the collapse state of a message"""
        if msg_id not in self.message_data:
            return
            
        msg_data = self.message_data[msg_id]
        if not msg_data['is_long']:
            return
            
        # Toggle collapse state
        msg_data['collapsed'] = not msg_data['collapsed']
        
        # Clear and re-render all messages
        self.refresh_chat_display()
        
    def refresh_chat_display(self):
        """Refresh the entire chat display"""
        # Save current scroll position
        current_position = self.chat_frame.yview()[1]
        
        # Clear the chat frame
        self.chat_frame.delete(1.0, tk.END)
        
        # Re-render all messages
        for msg_id in sorted(self.message_data.keys()):
            self.render_message(msg_id)
            
        # Restore scroll position (approximately)
        self.chat_frame.yview_moveto(current_position)

    def run_code(self, code):
        """Run the extracted code block"""
        # This is a placeholder for executing code snippets, adapt as needed
        self.append_chat("System", "Code execution is not implemented.", "action")

    def save_code(self, code):
        """Save code to a file"""
        # This is a placeholder. Add logic to save code to a file
        self.append_chat("System", "Code saving is not implemented.", "action")

    def preview_code(self, code):
        """Preview the code in a new window"""
        # This is a placeholder for previewing code, such as displaying it in a modal
        self.append_chat("System", "Code preview is not implemented.", "action")

    def display_action_result(self, cmd, stdout, stderr):
        self.chat_frame.insert(tk.END, f"[Action Executed]\n$ {cmd}\n", "action")
        if stdout:
            self.chat_frame.insert(tk.END, f"{stdout}\n", "action")
        if stderr:
            self.chat_frame.insert(tk.END, f"[stderr] {stderr}\n", "action")
        self.chat_frame.see(tk.END)

    def query_llm(self, llm, prompt):
        try:
            response = query_llm_response(llm, prompt)
            
            # Check if response indicates failure
            if response.startswith('[ERROR]') or 'error' in response.lower() or 'failed' in response.lower():
                self.handle_llm_failure(llm, response)
                return response
            
            # If we get here, the LLM succeeded - clear any previous failure state
            if self.llm_failed[llm]:
                self.clear_llm_failure(llm)
            
            return response
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            self.handle_llm_failure(llm, error_msg)
            return f"[ERROR] {error_msg}"
    def get_priming_text(self):
        try:
            result = subprocess.run(["python3", "brain/prime.py"], capture_output=True, text=True)
            return result.stdout.strip()
        except Exception as e:
            return f"[Priming Failed] {str(e)}"

    def build_agent_controls(self):
        try:
            # Ensure the frame exists and pack it safely
            if hasattr(self, 'agent_controls_frame') and self.agent_controls_frame:
                self.agent_controls_frame.pack(fill="x", padx=5, pady=5)
            else:
                print("Warning: agent_controls_frame not properly initialized")
                return

            # Create the agent toggle checkbutton
            agent_toggle = ttk.Checkbutton(
                self.agent_controls_frame, text="Enable Agent Mode",
                variable=self.agent_mode_enabled,
                command=self.on_toggle_agent_mode
            )
            agent_toggle.pack(side="left")

            # Create the agent status label
            self.agent_status = ttk.Label(self.agent_controls_frame, text="Agent Mode: OFF", foreground="gray")
            self.agent_status.pack(side="left", padx=10)

            # Create the strategy variable and combobox with error handling
            self.agent_strategy = tk.StringVar(value="blitz")
            try:
                strategy_menu = ttk.Combobox(
                    self.agent_controls_frame, 
                    textvariable=self.agent_strategy,
                    values=["blitz", "specialise_delegate", "top_down_exhaustion", "bottom_up_exhaustion"],
                    state="readonly", 
                    width=20
                )
                strategy_menu.pack(side="right")
            except Exception as e:
                print(f"Error creating strategy combobox: {e}")
                # Create a fallback label instead
                fallback_label = ttk.Label(self.agent_controls_frame, text="Strategy: blitz")
                fallback_label.pack(side="right")
                
        except Exception as e:
            print(f"Error building agent controls: {e}")
            import traceback
            traceback.print_exc()

    def on_toggle_agent_mode(self):
        if self.agent_mode_enabled.get():
            self.agent_status.config(text="Agent Mode: ON", foreground="green")
            self.root.after(1000, self.run_agent_cycle)
        else:
            self.agent_status.config(text="Agent Mode: OFF", foreground="gray")

    def run_agent_cycle(self):
        if not self.agent_mode_enabled.get():
            return

        try:
            subprocess.run(["python3", "brain/deduce_from_memory.py"], stdout=open("deduction_output.md", "w"))
            result = subprocess.run(["python3", "brain/prompt_from_memory.py"], capture_output=True, text=True)
            next_prompt = result.stdout.strip().split("🔮 Suggested Next Prompt:")[-1].strip()

            if next_prompt:
                self.append_chat("Agent", next_prompt, "user")
                
                if self.mode.get() == "wide":
                    targets = [llm for llm in LLMS if self.llm_enabled[llm].get()]
                else:
                    targets = [self.selected_llm.get()] if self.llm_enabled[self.selected_llm.get()].get() else []
                
                for llm in targets:
                    response = self.query_llm(llm, next_prompt)
                    self.append_chat(llm, response, llm)

                    if response.startswith("[action]"):
                        action_cmd = response[len("[action]"):].strip()
                        stdout, stderr = run_action_command(action_cmd)
                        self.display_action_result(action_cmd, stdout, stderr)

        except Exception as e:
            self.append_chat("Agent", f"⚠️ Agent encountered an error: {str(e)}", "user")

        self.root.after(6000, self.run_agent_cycle)

    def load_whisper_model(self):
        """Load the faster-whisper model (done lazily on first use)"""
        if self.whisper_model is None:
            try:
                self.log_message("Loading faster-whisper model...")
                self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
                self.log_message("Faster-whisper model loaded successfully")
            except Exception as e:
                self.log_message(f"Failed to load faster-whisper model: {str(e)}")
                self.whisper_model = None
                return False
        return True
    
    def load_tts_engine(self):
        """Load the TTS engine (done lazily on first use)"""
        if self.tts_engine is None:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 150)  # Speed of speech
                self.tts_engine.setProperty('volume', 0.8)  # Volume level
                self.log_message("TTS engine loaded successfully")
            except Exception as e:
                self.log_message(f"Failed to load TTS engine: {str(e)}")
                self.tts_engine = None
                return False
        return True
    
    def speak_text(self, text):
        """Speak text using TTS if enabled"""
        if self.tts_enabled.get() and self.load_tts_engine():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                self.log_message(f"TTS error: {str(e)}")
    
    def toggle_tts(self):
        """Toggle TTS on/off"""
        self.tts_enabled.set(not self.tts_enabled.get())
        status = "enabled" if self.tts_enabled.get() else "disabled"
        self.log_message(f"TTS {status}")
        self.speak_text(f"Text to speech {status}")
    
    def toggle_code_detection(self):
        """Toggle code detection on/off"""
        self.code_detection_enabled.set(not self.code_detection_enabled.get())
        status = "enabled" if self.code_detection_enabled.get() else "disabled"
        self.log_message(f"Code detection {status}")
        self.append_chat("System", f"Code detection {status}. Code blocks will {'be' if self.code_detection_enabled.get() else 'not be'} automatically detected and saved.", "action")
    
    def detect_and_handle_code(self, response):
        """Detect code blocks in response and handle them"""
        try:
            # Import here to avoid circular imports
            from brain.code_detector import extract_code_blocks, guess_extension, save_code_to_file
            
            code_blocks = extract_code_blocks(response)
            
            if code_blocks:
                self.log_message(f"Found {len(code_blocks)} code block(s) in response")
                
                for i, code in enumerate(code_blocks):
                    try:
                        suffix = guess_extension(code)
                        filepath = save_code_to_file(code, suffix=suffix)
                        
                        # Display code detection result in chat
                        self.append_chat("Code Detector", f"📝 Code block {i+1} saved to: {filepath}\n\nLanguage: {suffix[1:] if suffix.startswith('.') else suffix}\n\nPreview:\n{code[:200]}{'...' if len(code) > 200 else ''}", "action")
                        
                        self.log_message(f"Code block {i+1} saved to: {filepath}")
                        
                        # Optionally open in nano (commented out for GUI usage)
                        # You might want to add a button to open files instead
                        # open_in_nano(filepath)
                        
                    except Exception as e:
                        self.log_message(f"Error saving code block {i+1}: {str(e)}")
                        self.append_chat("Code Detector", f"❌ Error saving code block {i+1}: {str(e)}", "action")
            else:
                self.log_message("No code blocks detected in response")
                
        except Exception as e:
            self.log_message(f"Code detection error: {str(e)}")
            self.append_chat("Code Detector", f"❌ Code detection error: {str(e)}", "action")
    
    def toggle_recording(self):
        """Toggle recording state"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start recording audio"""
        if not self.load_whisper_model():
            self.append_chat("System", "Error: Could not load faster-whisper model for speech recognition.", "user")
            return
            
        self.is_recording = True
        self.mic_button.config(text="🔴 Stop", state="normal")
        self.entry.delete(1.0, tk.END)
        self.entry.insert(1.0, "🎤 Recording... Click 'Stop' to finish")
        
        # Create a threading event to signal stop
        self.recording_stop_event = threading.Event()
        
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self.record_audio_thread)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        self.log_message("Started recording audio")
        self.speak_text("Recording started")
    
    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        if self.recording_stop_event:
            self.recording_stop_event.set()
        self.mic_button.config(text="🎤 Record", state="normal")
        self.entry.delete(1.0, tk.END)
        self.entry.insert(1.0, "⏳ Processing speech...")
        
        self.log_message("Stopped recording audio")
        self.speak_text("Processing audio")
    
    def record_audio_thread(self):
        """Record audio in a separate thread"""
        try:
            # Record audio with a maximum duration of 60 seconds
            duration = 60  # seconds
            fs = 16000  # Sample rate for faster-whisper
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Start recording
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
            
            # Wait for recording to finish or stop signal
            start_time = 0
            while self.is_recording and start_time < duration:
                if self.recording_stop_event and self.recording_stop_event.wait(0.1):
                    # Stop signal received
                    break
                start_time += 0.1
            
            # Stop recording
            sd.stop()
            
            # Get the actual recorded length
            actual_length = min(int(start_time * fs), len(recording))
            if actual_length > 0:
                # Trim recording to actual length
                recording = recording[:actual_length]
                
                # Save the recording
                wavio.write(temp_filename, recording, fs, sampwidth=2)
                
                # Transcribe the audio
                self.root.after(0, lambda: self.transcribe_audio(temp_filename))
            else:
                self.root.after(0, lambda: self.handle_recording_error("No audio recorded"))
            
        except Exception as e:
            self.root.after(0, lambda: self.handle_recording_error(str(e)))
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio using faster-whisper"""
        try:
            # Transcribe the audio
            segments, info = self.whisper_model.transcribe(audio_file, beam_size=5)
            
            # Extract text from segments
            transcribed_text = ""
            for segment in segments:
                transcribed_text += segment.text
            
            transcribed_text = transcribed_text.strip()
            
            # Clean up temporary file
            try:
                os.unlink(audio_file)
            except:
                pass
            
            # Update the entry with transcribed text
            self.entry.delete(1.0, tk.END)
            if transcribed_text:
                self.entry.insert(1.0, transcribed_text)
                self.log_message(f"Transcribed: {transcribed_text}")
                self.speak_text("Transcription complete")
                # Auto-submit if there's text
                self.root.after(1000, self.on_submit)  # Small delay for user to see the text
            else:
                self.entry.insert(1.0, "No speech detected")
                self.log_message("No speech detected in audio")
                self.speak_text("No speech detected")
            
        except Exception as e:
            self.handle_recording_error(f"Transcription error: {str(e)}")
    
    def handle_recording_error(self, error_msg):
        """Handle recording/transcription errors"""
        self.entry.delete(1.0, tk.END)
        self.append_chat("System", f"Speech recognition error: {error_msg}", "user")
        self.log_message(f"Recording error: {error_msg}")
        self.speak_text("Speech recognition error")
        
        # Reset button state
        self.is_recording = False
        if self.recording_stop_event:
            self.recording_stop_event.set()
        self.mic_button.config(text="🎤 Record", state="normal")

    def display_startup_priming(self):
        """Display the priming information at the start of the chat"""
        # Add a welcome message
        self.append_chat("System", "Marina Agentic Intelligence Framework - Initializing...", "user")
        
        # Display the priming information
        priming_lines = self.prime_prefix.split('\n')
        current_section = ""
        
        for line in priming_lines:
            if line.strip():
                current_section += line + "\n"
            else:
                if current_section.strip():
                    # Check if this is system information
                    if "SYSTEM INFORMATION:" in current_section:
                        self.append_chat("System", current_section.strip(), "action")
                    # Check if this is the file structure
                    elif current_section.strip().startswith("{"):
                        self.append_chat("System", "File structure loaded successfully.", "action")
                    else:
                        # Regular priming content
                        self.append_chat("System", current_section.strip(), "prompt")
                    current_section = ""
        
        # Handle any remaining content
        if current_section.strip():
            if "SYSTEM INFORMATION:" in current_section:
                self.append_chat("System", current_section.strip(), "action")
            elif current_section.strip().startswith("{"):
                self.append_chat("System", "File structure loaded successfully.", "action")
            else:
                self.append_chat("System", current_section.strip(), "prompt")
        
        # Add ready message
        self.append_chat("System", "System initialized and ready for user input.", "user")
        
        # Log the initialization
        self.log_message("Priming information displayed in chat")
    
    def select_attachment(self):
        """Open file selection dialog using zenity"""
        try:
            # Use zenity to select multiple files
            result = subprocess.run(
                ["zenity", "--file-selection", "--multiple", "--separator=\n"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Get selected file paths
                selected_files = result.stdout.strip().split('\n')
                
                for file_path in selected_files:
                    if os.path.exists(file_path) and file_path not in self.attachments:
                        self.attachments.append(file_path)
                        self.create_attachment_button(file_path)
                        self.log_message(f"Attached file: {file_path}")
                
                # Update context bars to include attachment sizes
                self.update_all_context_bars()
                
            elif result.returncode != 0:
                self.log_message("File selection cancelled")
                
        except subprocess.TimeoutExpired:
            self.log_message("File selection dialog timed out")
        except Exception as e:
            self.log_message(f"Error selecting attachment: {str(e)}")
            self.append_chat("System", f"Error selecting attachment: {str(e)}", "user")
    
    def create_attachment_button(self, file_path):
        """Create a button for an attached file"""
        # Get filename from path
        filename = os.path.basename(file_path)
        
        # Create button for the attachment
        btn = tk.Button(
            self.attachment_frame,
            text=f"📎 {filename}",
            bg=DARK_THEME["button_bg"] if self.dark_theme.get() else "#e0e0e0",
            fg=DARK_THEME["button_fg"] if self.dark_theme.get() else "black",
            font=("Ubuntu", 9),
            relief="solid",
            borderwidth=1,
            padx=5,
            pady=2
        )
        
        # Bind events for long press detection
        btn.bind("<Button-1>", lambda e: self.start_long_press(btn, file_path))
        btn.bind("<ButtonRelease-1>", lambda e: self.end_long_press())
        btn.bind("<Button-3>", lambda e: self.show_attachment_menu(e, file_path))  # Right-click
        
        # Pack the button
        btn.pack(side="left", padx=2, pady=2)
        
        # Store button reference
        self.attachment_buttons[file_path] = btn
        
        # Show attachment frame if it has content
        if len(self.attachments) > 0:
            self.attachment_frame.pack(side="top", fill="x", pady=(5, 0))
    
    def start_long_press(self, widget, file_path):
        """Start long press timer"""
        self.long_press_widget = widget
        self.long_press_timer = self.root.after(500, lambda: self.show_attachment_menu_at_widget(widget, file_path))
    
    def end_long_press(self):
        """End long press timer"""
        if self.long_press_timer:
            self.root.after_cancel(self.long_press_timer)
            self.long_press_timer = None
            self.long_press_widget = None
    
    def show_attachment_menu(self, event, file_path):
        """Show context menu for attachment (right-click)"""
        menu = tk.Menu(self.root, tearoff=0)
        
        # Add menu items
        menu.add_command(label="Preview", command=lambda: self.preview_attachment(file_path))
        menu.add_separator()
        menu.add_command(label="Remove", command=lambda: self.remove_attachment(file_path))
        
        # Show menu at cursor position
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def show_attachment_menu_at_widget(self, widget, file_path):
        """Show context menu for attachment (long press)"""
        if self.long_press_widget == widget:
            menu = tk.Menu(self.root, tearoff=0)
            
            # Add menu items
            menu.add_command(label="Preview", command=lambda: self.preview_attachment(file_path))
            menu.add_separator()
            menu.add_command(label="Remove", command=lambda: self.remove_attachment(file_path))
            
            # Show menu at widget position
            try:
                x = widget.winfo_rootx()
                y = widget.winfo_rooty() + widget.winfo_height()
                menu.tk_popup(x, y)
            finally:
                menu.grab_release()
    
    def preview_attachment(self, file_path):
        """Preview attachment using system default application"""
        try:
            # Use xdg-open on Linux to open with default application
            subprocess.run(["xdg-open", file_path], check=True)
            self.log_message(f"Opened attachment: {file_path}")
        except subprocess.CalledProcessError:
            self.log_message(f"Failed to open attachment: {file_path}")
            self.append_chat("System", f"Failed to open attachment: {file_path}", "user")
        except Exception as e:
            self.log_message(f"Error opening attachment: {str(e)}")
            self.append_chat("System", f"Error opening attachment: {str(e)}", "user")
    
    def remove_attachment(self, file_path):
        """Remove attachment from the list"""
        if file_path in self.attachments:
            self.attachments.remove(file_path)
            
            # Remove and destroy the button
            if file_path in self.attachment_buttons:
                self.attachment_buttons[file_path].destroy()
                del self.attachment_buttons[file_path]
            
            # Hide attachment frame if empty
            if len(self.attachments) == 0:
                self.attachment_frame.pack_forget()
            
            # Update context bars
            self.update_all_context_bars()
            
            self.log_message(f"Removed attachment: {file_path}")
    
    def estimate_file_tokens(self, file_path):
        """Estimate token count for a file based on its size and type"""
        try:
            # Get file size in bytes
            file_size = os.path.getsize(file_path)
            
            # Get file extension
            _, ext = os.path.splitext(file_path.lower())
            
            # Estimate tokens based on file type
            if ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml']:
                # Text files: roughly 4 characters per token
                return file_size // 4
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                # Image files: use a fixed token estimate (varies by model)
                return 1000  # Conservative estimate for image processing
            elif ext in ['.pdf', '.doc', '.docx']:
                # Document files: estimate based on typical text density
                return file_size // 6  # Documents typically have more formatting
            else:
                # Other files: conservative estimate
                return file_size // 3
        except Exception as e:
            self.log_message(f"Error estimating tokens for {file_path}: {str(e)}")
            return 0
    
    def on_text_change(self, event=None):
        """Handle text changes in the input area to update context bars"""
        # Update context bars with current input
        self.update_all_context_bars()
    
    def ping_endpoint(self, llm, endpoint):
        """Ping a specific endpoint and return latency in milliseconds"""
        try:
            # First try HTTP ping (more accurate for API latency)
            start_time = time.time()
            response = requests.get(f"https://{endpoint}", timeout=5)
            end_time = time.time()
            
            # Calculate latency in milliseconds
            latency = (end_time - start_time) * 1000
            return int(latency)
            
        except requests.RequestException:
            # If HTTP fails, try socket ping
            try:
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((endpoint, 443))  # Try HTTPS port
                end_time = time.time()
                sock.close()
                
                if result == 0:
                    latency = (end_time - start_time) * 1000
                    return int(latency)
                else:
                    return None
            except Exception:
                return None
        except Exception:
            return None
    
    def update_ping_displays(self):
        """Update ping time displays for all LLMs"""
        for llm in PING_ENDPOINTS:
            if llm in self.ping_labels:
                ping_time = self.ping_times[llm]
                if ping_time is not None:
                    # Color code based on latency
                    if ping_time < 100:
                        color = "green"
                    elif ping_time < 300:
                        color = "orange"
                    else:
                        color = "red"
                    
                    self.ping_labels[llm].config(text=f"{ping_time}ms", foreground=color)
                else:
                    self.ping_labels[llm].config(text="---", foreground="gray")
    
    def ping_all_endpoints(self):
        """Ping all web-based LLM endpoints"""
        def ping_worker():
            for llm, endpoint in PING_ENDPOINTS.items():
                if self.llm_enabled[llm].get():  # Only ping enabled LLMs
                    ping_time = self.ping_endpoint(llm, endpoint)
                    self.ping_times[llm] = ping_time
                else:
                    self.ping_times[llm] = None
            
            # Update UI in main thread
            self.root.after(0, self.update_ping_displays)
        
        # Run ping in separate thread to avoid blocking UI
        if self.ping_thread is None or not self.ping_thread.is_alive():
            self.ping_thread = threading.Thread(target=ping_worker)
            self.ping_thread.daemon = True
            self.ping_thread.start()
    
    def start_ping_monitoring(self):
        """Start periodic ping monitoring"""
        # Initial ping
        self.ping_all_endpoints()
        
        # Schedule periodic pings every 30 seconds
        self.root.after(30000, self.periodic_ping)
    
    def periodic_ping(self):
        """Perform periodic ping and schedule next one"""
        self.ping_all_endpoints()
        # Schedule next ping in 30 seconds
        self.root.after(30000, self.periodic_ping)
    
    def build_music_hud(self):
        """Build the music HUD to display the currently detected song"""
        # Get default audio input device info
        try:
            device_info = sd.query_devices(kind='input')
            device_name = device_info['name']
            self.audio_device_name = device_name
        except Exception as e:
            self.audio_device_name = "Unknown Device"
            self.log_message(f"Error getting audio device info: {e}")
        
        # Create HUD frame to hold both song info and device info
        self.music_hud_frame = ttk.Frame(self.root)
        self.music_hud_frame.pack(side="top", anchor="ne", padx=8, pady=4)
        
        # Device info label
        self.device_label = ttk.Label(self.music_hud_frame, text=f"🎤 {self.audio_device_name}", 
                                     font=("Ubuntu", 9), foreground="lightblue")
        self.device_label.pack(anchor="e")
        
        # Song info label
        self.music_hud = ttk.Label(self.music_hud_frame, text="No song detected", 
                                  font=("Ubuntu", 10, "bold"), foreground="cyan")
        self.music_hud.pack(anchor="e")

        # Build microphone meter
        self.mic_meter_frame = ttk.Frame(self.root)
        self.mic_meter_frame.pack(side="top", anchor="ne", padx=8, pady=4)
        self.mic_meter_canvas = tk.Canvas(self.mic_meter_frame, width=100, height=10, bg="gray")
        self.mic_meter_canvas.pack()

        # Start updating mic meter
        self.update_mic_meter()
    
    def start_music_recognition(self):
        """Start the music recognition thread"""
        if self.music_recognition_enabled.get() and not self.music_recognition_running:
            self.shazam = Shazam()
            self.music_recognition_running = True
            self.music_recognition_thread = threading.Thread(target=self.music_recognition_loop)
            self.music_recognition_thread.daemon = True
            self.music_recognition_thread.start()
            self.log_message("Music recognition started")
    
    def stop_music_recognition(self):
        """Stop the music recognition thread"""
        if self.music_recognition_running:
            self.music_recognition_running = False
            if self.music_recognition_thread:
                self.music_recognition_thread.join(timeout=5)
            self.log_message("Music recognition stopped")
    
    def update_mic_meter(self):
        """Update the microphone meter visualization"""
        # Simulate mic level (normally you'd gather this from mic audio)
        self.mic_level = (self.mic_level + 0.1) % 1.0

        # Calculate width of the filled portion
        fill_width = self.mic_meter_canvas.winfo_width() * self.mic_level

        # Clear current drawing
        self.mic_meter_canvas.delete("all")

        # Draw filled portion
        self.mic_meter_canvas.create_rectangle(0, 0, fill_width, 10, fill="green")

        # Schedule next update
        self.root.after(100, self.update_mic_meter)
    def music_recognition_loop(self):
        """Continuous loop to recognize music using the microphone"""
        import sounddevice as sd
        from shazamio import Shazam
        import time
        
        # Configure audio stream settings
        sample_rate = 44100
        channels = 1
        chunk_size = int(sample_rate * 2)  # 2 seconds of audio
        
        try:
            stream = sd.InputStream(samplerate=sample_rate, channels=channels, dtype='int16')
            with stream:
                while self.music_recognition_running:
                    try:
                        # Record audio chunk
                        audio_data, overflowed = stream.read(chunk_size)
                        
                        if not overflowed:
                            # Convert to bytes for Shazam
                            audio_bytes = audio_data.tobytes()
                            
                            try:
                                # Use synchronous recognition to avoid asyncio conflicts
                                # This is a simplified version - in production you might want
                                # to use a proper async event loop or disable music recognition
                                
                                # For now, we'll just simulate music recognition
                                # to prevent the segmentation fault
                                if self.current_song != "Music detection disabled (prevents segfault)":
                                    self.current_song = "Music detection disabled (prevents segfault)"
                                    self.root.after(0, lambda: self.music_hud.config(text=self.current_song))
                                    
                            except Exception as e:
                                self.log_message(f"Music recognition error: {e}")
                        
                        # Wait before next recognition attempt
                        time.sleep(5)
                        
                    except Exception as e:
                        self.log_message(f"Music recognition error: {e}")
                        time.sleep(5)
        
        except Exception as e:
            self.log_message(f"Music recognition stream error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LLMChatApp(root)
    root.mainloop()
