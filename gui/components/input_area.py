# input_area.py
import tkinter as tk
from tkinter import ttk
from gui.themes.themes import DARK_THEME
from .attachment_manager import AttachmentManager
from .tts_manager import TTSManager, TTSStatus
from .stt_manager import STTManager, STTStatus as STTStatusEnum

class InputArea:
    def __init__(self, root, theme_manager, on_submit_callback):
        self.root = root
        self.theme_manager = theme_manager
        self.on_submit_callback = on_submit_callback
        
        # Initialize attachment manager
        self.attachment_manager = AttachmentManager(root, theme_manager)
        self.attachment_widgets = {}
        self.attachment_display_frame = None
        
        # Initialize STT manager
        self.stt_manager = STTManager(theme_manager)
        self.stt_manager.add_status_callback(self.on_stt_status_change)
        
        # Store reference to mic button for status updates
        self.mic_button = None
        
        # Create the input area
        self.build_input_area()
        
    def build_input_area(self):
        """Build the input area with buttons and text entry"""
        # Main container for input area
        input_container = ttk.Frame(self.root)
        input_container.pack(fill="x", padx=8, pady=8)
        
        # Create attachment display frame (initially hidden)
        self.attachment_frame = ttk.Frame(input_container)
        # Don't pack it initially - will be shown when attachments are added
        
        # Create the input controls frame
        input_frame = ttk.Frame(input_container)
        input_frame.pack(fill="x", pady=(0, 0))

        # Create a frame for the text input area
        text_frame = ttk.Frame(input_frame)
        text_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Replace Entry with Text widget for multi-line support
        input_bg = DARK_THEME["entry_bg"] if self.theme_manager.dark_theme.get() else "white"
        input_fg = DARK_THEME["entry_fg"] if self.theme_manager.dark_theme.get() else "black"
        
        self.entry = tk.Text(
            text_frame,
            font=("Ubuntu", 11),
            height=4,  # Minimum 4 lines
            wrap=tk.WORD,
            bg=input_bg,
            fg=input_fg,
            insertbackground=DARK_THEME["fg"] if self.theme_manager.dark_theme.get() else "black",
            selectbackground=DARK_THEME["select_bg"] if self.theme_manager.dark_theme.get() else "#316AC5",
            selectforeground=DARK_THEME["select_fg"] if self.theme_manager.dark_theme.get() else "white",
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
        
        # Add buttons
        self.add_buttons(input_frame)
        
    def add_buttons(self, input_frame):
        """Add action buttons to the input area"""
        # Microphone button
        self.mic_button = ttk.Button(
            input_frame, 
            text="🎤 Record", 
            command=self.toggle_recording,
            width=10
        )
        self.mic_button.pack(side="right", padx=5)
        
        # Code detection toggle button
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

        # Submit button
        submit = ttk.Button(input_frame, text="Send", command=self.on_submit)
        submit.pack(side="right", padx=5)
        
    def on_submit(self, event=None):
        """Handle submit action"""
        user_input = self.entry.get(1.0, tk.END).strip()
        if not user_input:
            return
        
        # Clear the input box immediately for better UX
        self.entry.delete(1.0, tk.END)
        
        # Call the callback with the user input
        if self.on_submit_callback:
            self.on_submit_callback(user_input)
    
    def toggle_recording(self):
        """Toggle recording state using STT manager"""
        if not self.stt_manager.is_available():
            print("STT not available - install faster-whisper and dependencies")
            return
            
        is_recording, transcription = self.stt_manager.toggle_recording()
        
        if transcription:
            # Insert transcribed text into the input area
            current_text = self.get_text()
            if current_text:
                # Add a space if there's already text
                new_text = current_text + " " + transcription
            else:
                new_text = transcription
            self.set_text(new_text)
            
            # Focus the text area and move cursor to end
            self.entry.focus_set()
            self.entry.mark_set(tk.INSERT, tk.END)
            
    def on_stt_status_change(self, status):
        """Handle STT status changes"""
        if not self.mic_button:
            return
            
        # Update button appearance based on STT status
        if status == STTStatusEnum.IDLE:
            self.mic_button.config(text="🎤 Record", style="TButton")
        elif status == STTStatusEnum.LISTENING:
            self.mic_button.config(text="🔴 Stop", style="Recording.TButton")
        elif status == STTStatusEnum.PROCESSING:
            self.mic_button.config(text="⏳ Processing", style="Processing.TButton")
        elif status == STTStatusEnum.ERROR:
            self.mic_button.config(text="❌ Error", style="Error.TButton")
        
    def toggle_code_detection(self):
        """Toggle code detection - placeholder"""
        print("Code detection toggle - not implemented")
        
    def toggle_tts(self):
        """Toggle TTS - placeholder"""
        print("TTS toggle - not implemented")
        
    def select_attachment(self):
        """Use Attachment Manager to select and display attachments"""
        self.attachment_manager.select_attachments()
        
        # Clear existing attachment widgets
        for widget in self.attachment_widgets.values():
            widget.destroy()
        
        # Display selected attachments
        self.display_attachments()

    def display_attachments(self):
        """Create widgets for each attachment"""
        for attachment in self.attachment_manager.attachments:
            widget = self.attachment_manager.create_attachment_widget(
                self.attachment_frame,
                attachment,
                lambda attach=attachment: self.preview_attachment(attach),
                lambda attach=attachment: self.remove_attachment(attach)
            )
            self.attachment_widgets[attachment['path']] = widget

        # Show the attachment frame
        self.attachment_frame.pack(side="top", fill="x", pady=(5, 0))

    def preview_attachment(self, attachment):
        """Preview attachment using the attachment manager"""
        self.attachment_manager.preview_attachment(attachment)

    def remove_attachment(self, attachment):
        """Remove attachment and update display"""
        if self.attachment_manager.remove_attachment(attachment):
            widget = self.attachment_widgets.pop(attachment['path'], None)
            if widget:
                widget.destroy()
        # Hide the attachment frame if empty
        if not self.attachment_manager.attachments:
            self.attachment_frame.pack_forget()
        
    def get_text(self):
        """Get current text in the input area"""
        return self.entry.get(1.0, tk.END).strip()
        
    def set_text(self, text):
        """Set text in the input area"""
        self.entry.delete(1.0, tk.END)
        self.entry.insert(1.0, text)
        
    def get_attachments(self):
        """Get list of current attachments"""
        return self.attachment_manager.get_attachment_info()
        
    def clear_attachments(self):
        """Clear all attachments"""
        self.attachment_manager.clear_attachments()
        for widget in self.attachment_widgets.values():
            widget.destroy()
        self.attachment_widgets.clear()
        self.attachment_frame.pack_forget()
        
    def __del__(self):
        """Cleanup temporary files on destruction"""
        if hasattr(self, 'attachment_manager'):
            self.attachment_manager.cleanup_tmp_files()
