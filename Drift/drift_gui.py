#!/usr/bin/env python3
"""
Drift GUI - Marina-integrated Login Manager Interface
Beautiful, lightweight login screen with Marina integration

Author: Marina AI Assistant
"""

import os
import sys
import json
import time
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# Import the core system
from drift_core import DriftCore, UserProfile, AuthMethod, SessionType, LoginStatus

# GUI toolkit
try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Gdk', '4.0')
    gi.require_version('Adw', '1')
    from gi.repository import Gtk, Gdk, GLib, GObject, Gio, Adw
    GTK_AVAILABLE = True
except ImportError:
    print("GTK4 not available. Please install python3-gi and libgtk-4-dev")
    GTK_AVAILABLE = False
    sys.exit(1)

# Audio recording for voice auth
try:
    import sounddevice as sd
    import numpy as np
    import wave
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


class DriftLoginWindow(Adw.ApplicationWindow):
    """Main login window with Marina-themed design."""
    
    def __init__(self, app: Adw.Application):
        super().__init__(application=app)
        
        # Use local test config if not running as root
        if os.geteuid() != 0:
            test_config = os.path.join(os.path.dirname(__file__), 'test_drift.conf')
            if not os.path.exists(test_config):
                # Create test config
                config_data = {
                    'database_path': os.path.join(os.path.dirname(__file__), 'test_db/drift.db'),
                    'log_file': os.path.join(os.path.dirname(__file__), 'test_logs/drift.log'),
                    'marina_path': '/home/adminx/Marina'
                }
                os.makedirs(os.path.dirname(config_data['database_path']), exist_ok=True)
                os.makedirs(os.path.dirname(config_data['log_file']), exist_ok=True)
                with open(test_config, 'w') as f:
                    json.dump(config_data, f)
            self.drift_core = DriftCore(config_path=test_config)
        else:
            self.drift_core = DriftCore()
        self.users = self.drift_core.get_system_users()
        self.current_user_index = 0
        self.recording_voice = False
        self.voice_data = None
        
        self.setup_window()
        self.setup_ui()
        self.setup_styling()
        self.start_background_updates()
    
    def setup_window(self):
        """Configure main window properties."""
        self.set_title("Drift - Marina Login Manager")
        self.set_default_size(1920, 1080)
        self.set_resizable(False)
        
        # Make it fullscreen for login manager behavior
        if os.environ.get('DRIFT_FULLSCREEN', '1') == '1':
            self.fullscreen()
    
    def setup_ui(self):
        """Create the main UI layout."""
        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)
        
        # Background overlay
        self.overlay = Gtk.Overlay()
        self.main_box.append(self.overlay)
        
        # Background image/gradient
        self.setup_background()
        
        # Main content
        self.content_grid = Gtk.Grid()
        self.content_grid.set_halign(Gtk.Align.CENTER)
        self.content_grid.set_valign(Gtk.Align.CENTER)
        self.content_grid.set_row_spacing(20)
        self.content_grid.set_column_spacing(20)
        self.overlay.add_overlay(self.content_grid)
        
        # Marina logo/branding
        self.setup_branding()
        
        # System status display
        self.setup_system_status()
        
        # User selection area
        self.setup_user_selection()
        
        # Login controls
        self.setup_login_controls()
        
        # Session selection
        self.setup_session_selection()
        
        # Bottom info bar
        self.setup_info_bar()
        
        # Time display
        self.setup_time_display()
    
    def setup_background(self):
        """Setup animated background."""
        self.background_box = Gtk.Box()
        self.background_box.set_size_request(1920, 1080)
        
        # Marina-themed gradient background
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .drift-background {
                background: linear-gradient(135deg, 
                    #1a1a1a 0%, 
                    #0d1421 50%, 
                    #1a1a1a 100%);
            }
        """)
        
        self.background_box.add_css_class("drift-background")
        self.background_box.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.overlay.set_child(self.background_box)
    
    def setup_branding(self):
        """Setup Marina branding and welcome message."""
        branding_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        branding_box.set_halign(Gtk.Align.CENTER)
        
        # Marina logo (text for now, could be image)
        logo_label = Gtk.Label()
        logo_label.set_markup('<span size="24000" weight="bold" foreground="#00d4aa">🌊 Marina Drift</span>')
        branding_box.append(logo_label)
        
        # Welcome message with Marina context
        welcome_label = Gtk.Label()
        welcome_label.set_markup('<span size="12000" foreground="#cccccc">Where Marina drifts in as your system awakens</span>')
        branding_box.append(welcome_label)
        
        # System status indicator
        self.marina_status_label = Gtk.Label()
        branding_box.append(self.marina_status_label)
        
        self.content_grid.attach(branding_box, 1, 0, 1, 1)
    
    def setup_system_status(self):
        """Setup system status display."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        status_box.set_halign(Gtk.Align.END)
        status_box.set_valign(Gtk.Align.START)
        status_box.set_margin_top(20)
        status_box.set_margin_end(20)
        
        self.uptime_label = Gtk.Label()
        self.load_label = Gtk.Label()
        self.memory_label = Gtk.Label()
        
        status_box.append(self.uptime_label)
        status_box.append(self.load_label)
        status_box.append(self.memory_label)
        
        self.content_grid.attach(status_box, 2, 0, 1, 1)
        
        # Update system status
        self.update_system_status()
    
    def setup_user_selection(self):
        """Setup user avatar and selection."""
        user_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        user_box.set_halign(Gtk.Align.CENTER)
        
        # User avatar
        self.user_avatar = Gtk.Button()
        self.user_avatar.set_size_request(120, 120)
        self.user_avatar.add_css_class("circular")
        self.user_avatar.connect("clicked", self.on_cycle_users)
        
        # User name and info
        self.user_name_label = Gtk.Label()
        self.user_info_label = Gtk.Label()
        
        # Navigation buttons for multiple users
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        nav_box.set_halign(Gtk.Align.CENTER)
        
        self.prev_user_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self.prev_user_btn.connect("clicked", self.on_previous_user)
        
        self.next_user_btn = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self.next_user_btn.connect("clicked", self.on_next_user)
        
        nav_box.append(self.prev_user_btn)
        nav_box.append(self.next_user_btn)
        
        user_box.append(self.user_avatar)
        user_box.append(self.user_name_label)
        user_box.append(self.user_info_label)
        user_box.append(nav_box)
        
        self.content_grid.attach(user_box, 1, 1, 1, 1)
        
        # Update current user display
        self.update_user_display()
    
    def setup_login_controls(self):
        """Setup login input controls."""
        login_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        login_box.set_halign(Gtk.Align.CENTER)
        login_box.set_size_request(350, -1)
        
        # Password entry
        self.password_entry = Gtk.PasswordEntry()
        # GTK4 PasswordEntry doesn't have set_placeholder_text, use props
        self.password_entry.props.placeholder_text = "Enter password..."
        self.password_entry.set_show_peek_icon(True)
        self.password_entry.connect("activate", self.on_login_clicked)
        
        # Authentication method selection
        auth_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        auth_box.set_halign(Gtk.Align.CENTER)
        
        # Password login button
        self.login_btn = Gtk.Button.new_with_label("Login")
        self.login_btn.add_css_class("suggested-action")
        self.login_btn.connect("clicked", self.on_login_clicked)
        
        # Voice login button
        self.voice_btn = Gtk.Button.new_from_icon_name("audio-input-microphone-symbolic")
        self.voice_btn.set_tooltip_text("Voice Authentication")
        self.voice_btn.connect("clicked", self.on_voice_auth_clicked)
        if not AUDIO_AVAILABLE:
            self.voice_btn.set_sensitive(False)
        
        # Face login button
        self.face_btn = Gtk.Button.new_from_icon_name("camera-photo-symbolic")
        self.face_btn.set_tooltip_text("Face Authentication")
        self.face_btn.connect("clicked", self.on_face_auth_clicked)
        
        # Token login button
        self.token_btn = Gtk.Button.new_from_icon_name("channel-secure-symbolic")
        self.token_btn.set_tooltip_text("Marina Token Authentication")
        self.token_btn.connect("clicked", self.on_token_auth_clicked)
        
        auth_box.append(self.voice_btn)
        auth_box.append(self.face_btn)
        auth_box.append(self.token_btn)
        
        # Guest login button
        self.guest_btn = Gtk.Button.new_with_label("Guest Session")
        self.guest_btn.add_css_class("flat")
        self.guest_btn.connect("clicked", self.on_guest_clicked)
        
        login_box.append(self.password_entry)
        login_box.append(self.login_btn)
        login_box.append(auth_box)
        login_box.append(self.guest_btn)
        
        self.content_grid.attach(login_box, 1, 2, 1, 1)
    
    def setup_session_selection(self):
        """Setup session type selection."""
        session_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        session_box.set_halign(Gtk.Align.CENTER)
        
        # Session type dropdown
        self.session_dropdown = Gtk.DropDown()
        session_types = ["Wayland", "X11", "Marina Shell", "Custom"]
        string_list = Gtk.StringList()
        for session_type in session_types:
            string_list.append(session_type)
        self.session_dropdown.set_model(string_list)
        self.session_dropdown.set_selected(0)  # Default to Wayland
        
        session_label = Gtk.Label.new("Session:")
        session_box.append(session_label)
        session_box.append(self.session_dropdown)
        
        self.content_grid.attach(session_box, 1, 3, 1, 1)
    
    def setup_info_bar(self):
        """Setup bottom information bar."""
        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        info_box.set_halign(Gtk.Align.FILL)
        info_box.set_valign(Gtk.Align.END)
        info_box.set_margin_bottom(20)
        info_box.set_margin_start(20)
        info_box.set_margin_end(20)
        
        # Left side - Marina status
        left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Marina daemon indicator
        self.daemon_indicator = Gtk.Label()
        left_box.append(self.daemon_indicator)
        
        # Right side - power options
        right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        right_box.set_halign(Gtk.Align.END)
        right_box.set_hexpand(True)
        
        # Shutdown button
        shutdown_btn = Gtk.Button.new_from_icon_name("system-shutdown-symbolic")
        shutdown_btn.set_tooltip_text("Shutdown")
        shutdown_btn.connect("clicked", self.on_shutdown_clicked)
        
        # Restart button
        restart_btn = Gtk.Button.new_from_icon_name("system-reboot-symbolic")
        restart_btn.set_tooltip_text("Restart")
        restart_btn.connect("clicked", self.on_restart_clicked)
        
        # Settings button
        settings_btn = Gtk.Button.new_from_icon_name("preferences-system-symbolic")
        settings_btn.set_tooltip_text("Drift Settings")
        settings_btn.connect("clicked", self.on_settings_clicked)
        
        right_box.append(settings_btn)
        right_box.append(restart_btn)
        right_box.append(shutdown_btn)
        
        info_box.append(left_box)
        info_box.append(right_box)
        
        self.content_grid.attach(info_box, 0, 4, 3, 1)
    
    def setup_time_display(self):
        """Setup time and date display."""
        time_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        time_box.set_halign(Gtk.Align.START)
        time_box.set_valign(Gtk.Align.START)
        time_box.set_margin_top(20)
        time_box.set_margin_start(20)
        
        self.time_label = Gtk.Label()
        self.date_label = Gtk.Label()
        
        time_box.append(self.time_label)
        time_box.append(self.date_label)
        
        self.content_grid.attach(time_box, 0, 0, 1, 1)
        
        # Update time display
        self.update_time_display()
    
    def setup_styling(self):
        """Apply Marina-themed styling."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .drift-window {
                background: linear-gradient(135deg, #1a1a1a 0%, #0d1421 50%, #1a1a1a 100%);
                color: #ffffff;
            }
            
            .circular {
                border-radius: 60px;
                border: 3px solid #00d4aa;
            }
            
            .user-avatar {
                background: #333333;
                color: #00d4aa;
                font-size: 48px;
                font-weight: bold;
            }
            
            .status-text {
                color: #cccccc;
                font-size: 12px;
            }
            
            .time-text {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
            }
            
            .date-text {
                color: #cccccc;
                font-size: 14px;
            }
            
            .marina-status-good {
                color: #00d4aa;
            }
            
            .marina-status-warning {
                color: #ffaa00;
            }
            
            .marina-status-error {
                color: #ff4444;
            }
        """)
        
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def update_user_display(self):
        """Update the current user display."""
        if not self.users:
            return
        
        user = self.users[self.current_user_index]
        
        # Update user name
        self.user_name_label.set_markup(f'<span size="16000" weight="bold">{user.full_name}</span>')
        
        # Update user info
        last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"
        persona_info = f" • {user.marina_persona}" if user.marina_persona else ""
        self.user_info_label.set_markup(
            f'<span size="10000" foreground="#cccccc">@{user.username} • Last login: {last_login}{persona_info}</span>'
        )
        
        # Update avatar (use initials for now)
        avatar_text = user.full_name[0].upper() if user.full_name else user.username[0].upper()
        avatar_label = Gtk.Label.new(avatar_text)
        avatar_label.add_css_class("user-avatar")
        
        # Clear existing avatar content (GTK4 handles this automatically)
        self.user_avatar.set_child(avatar_label)
        
        # Update navigation button sensitivity
        self.prev_user_btn.set_sensitive(len(self.users) > 1)
        self.next_user_btn.set_sensitive(len(self.users) > 1)
    
    def update_system_status(self):
        """Update system status information."""
        status = self.drift_core.get_system_status()
        
        if status:
            uptime_hours = status.get('uptime_hours', 0)
            uptime_str = f"{int(uptime_hours)}h {int((uptime_hours % 1) * 60)}m"
            
            self.uptime_label.set_markup(f'\u003cspan foreground="#cccccc" size="10000"\u003eUptime: {uptime_str}\u003c/span\u003e')
            
            load_avg = status.get('load_average', ['0.0', '0.0', '0.0'])
            self.load_label.set_markup(f'\u003cspan foreground="#cccccc" size="10000"\u003eLoad: {load_avg[0]}\u003c/span\u003e')
            
            memory_percent = status.get('memory_usage_percent', 0)
            self.memory_label.set_markup(f'\u003cspan foreground="#cccccc" size="10000"\u003eMemory: {memory_percent:.1f}%\u003c/span\u003e')
    
    def update_marina_status(self):
        """Update Marina daemon status."""
        daemons = self.drift_core._check_marina_daemons()
        
        if daemons:
            status_text = f"Marina: {len(daemons)} daemons active"
            color = "#00d4aa"  # marina-status-good
        else:
            status_text = "Marina: Ready to start"
            color = "#ffaa00"  # marina-status-warning
        
        self.marina_status_label.set_markup(f'\u003cspan foreground="{color}"\u003e{status_text}\u003c/span\u003e')
        
        # Update daemon indicator in info bar
        self.daemon_indicator.set_markup(f'\u003cspan foreground="#cccccc"\u003e{status_text}\u003c/span\u003e')
    
    def update_time_display(self):
        """Update time and date display."""
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        date_str = now.strftime("%A, %B %d, %Y")
        
        self.time_label.set_markup(f'<span foreground="#ffffff" size="18000" weight="bold">{time_str}</span>')
        self.date_label.set_markup(f'<span foreground="#cccccc" size="14000">{date_str}</span>')
    
    def start_background_updates(self):
        """Start background update timers."""
        # Update time every second
        GLib.timeout_add_seconds(1, self.update_time_display)
        
        # Update system status every 30 seconds
        GLib.timeout_add_seconds(30, self.update_system_status)
        
        # Update Marina status every 10 seconds
        GLib.timeout_add_seconds(10, self.update_marina_status)
    
    # Event handlers
    def on_cycle_users(self, button):
        """Cycle to next user when avatar is clicked."""
        self.on_next_user(button)
    
    def on_previous_user(self, button):
        """Switch to previous user."""
        if len(self.users) > 1:
            self.current_user_index = (self.current_user_index - 1) % len(self.users)
            self.update_user_display()
            self.password_entry.set_text("")
            self.password_entry.grab_focus()
    
    def on_next_user(self, button):
        """Switch to next user."""
        if len(self.users) > 1:
            self.current_user_index = (self.current_user_index + 1) % len(self.users)
            self.update_user_display()
            self.password_entry.set_text("")
            self.password_entry.grab_focus()
    
    def on_login_clicked(self, button):
        """Handle password login."""
        if not self.users:
            self.show_error("No users available")
            return
        
        user = self.users[self.current_user_index]
        password = self.password_entry.get_text()
        
        if not password:
            self.show_error("Please enter a password")
            return
        
        # Disable UI during authentication
        self.set_ui_sensitive(False)
        
        # Perform authentication in background thread
        threading.Thread(
            target=self.authenticate_user,
            args=(user.username, password, AuthMethod.PASSWORD),
            daemon=True
        ).start()
    
    def on_voice_auth_clicked(self, button):
        """Handle voice authentication."""
        if not AUDIO_AVAILABLE:
            self.show_error("Voice authentication not available")
            return
        
        if self.recording_voice:
            self.stop_voice_recording()
        else:
            self.start_voice_recording()
    
    def on_face_auth_clicked(self, button):
        """Handle face authentication."""
        if not self.users:
            self.show_error("No users available")
            return
        
        user = self.users[self.current_user_index]
        
        # Disable UI during authentication
        self.set_ui_sensitive(False)
        
        # Perform authentication in background thread
        threading.Thread(
            target=self.authenticate_user,
            args=(user.username, "", AuthMethod.FACE),
            daemon=True
        ).start()
    
    def on_token_auth_clicked(self, button):
        """Handle Marina token authentication."""
        # Show token input dialog
        dialog = Gtk.Dialog()
        dialog.set_title("Marina Token Authentication")
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        
        content_area = dialog.get_content_area()
        
        label = Gtk.Label.new("Enter Marina token:")
        content_area.append(label)
        
        token_entry = Gtk.Entry()
        token_entry.set_placeholder_text("marina_token_here...")
        content_area.append(token_entry)
        
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Authenticate", Gtk.ResponseType.OK)
        
        dialog.connect("response", self.on_token_dialog_response, token_entry)
        dialog.present()
    
    def on_guest_clicked(self, button):
        """Handle guest login."""
        # Disable UI during authentication
        self.set_ui_sensitive(False)
        
        # Perform authentication in background thread
        threading.Thread(
            target=self.authenticate_user,
            args=("guest", "", AuthMethod.GUEST),
            daemon=True
        ).start()
    
    def on_shutdown_clicked(self, button):
        """Handle shutdown request."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Shutdown System?",
            secondary_text="This will shutdown the computer immediately."
        )
        
        dialog.connect("response", self.on_shutdown_response)
        dialog.present()
    
    def on_restart_clicked(self, button):
        """Handle restart request."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Restart System?",
            secondary_text="This will restart the computer immediately."
        )
        
        dialog.connect("response", self.on_restart_response)
        dialog.present()
    
    def on_settings_clicked(self, button):
        """Handle settings request."""
        # TODO: Implement settings dialog
        self.show_info("Settings dialog coming soon!")
    
    def on_token_dialog_response(self, dialog, response, token_entry):
        """Handle token dialog response."""
        if response == Gtk.ResponseType.OK:
            token = token_entry.get_text()
            if token and self.users:
                user = self.users[self.current_user_index]
                
                # Disable UI during authentication
                self.set_ui_sensitive(False)
                
                # Perform authentication in background thread
                threading.Thread(
                    target=self.authenticate_user,
                    args=(user.username, token, AuthMethod.TOKEN),
                    daemon=True
                ).start()
        
        dialog.destroy()
    
    def on_shutdown_response(self, dialog, response):
        """Handle shutdown dialog response."""
        if response == Gtk.ResponseType.YES:
            subprocess.run(['sudo', 'shutdown', '-h', 'now'])
        dialog.destroy()
    
    def on_restart_response(self, dialog, response):
        """Handle restart dialog response."""
        if response == Gtk.ResponseType.YES:
            subprocess.run(['sudo', 'reboot'])
        dialog.destroy()
    
    def authenticate_user(self, username: str, password: str, auth_method: AuthMethod):
        """Authenticate user (runs in background thread)."""
        success, error_msg = self.drift_core.authenticate_user(username, password, auth_method)
        
        # Update UI on main thread
        GLib.idle_add(self.on_authentication_complete, success, error_msg, username)
    
    def on_authentication_complete(self, success: bool, error_msg: str, username: str):
        """Handle authentication completion (runs on main thread)."""
        self.set_ui_sensitive(True)
        
        if success:
            # Get selected session type
            session_index = self.session_dropdown.get_selected()
            session_types = [SessionType.WAYLAND, SessionType.X11, SessionType.MARINA_SHELL, SessionType.CUSTOM]
            session_type = session_types[session_index] if session_index < len(session_types) else SessionType.WAYLAND
            
            # Launch session
            if self.drift_core.launch_session(username, session_type):
                self.show_success(f"Login successful! Starting {session_type.value} session...")
                # In a real login manager, this would exit and start the session
                GLib.timeout_add_seconds(2, lambda: self.get_application().quit())
            else:
                self.show_error("Failed to start session")
        else:
            self.show_error(error_msg or "Authentication failed")
            self.password_entry.set_text("")
            self.password_entry.grab_focus()
    
    def start_voice_recording(self):
        """Start recording voice for authentication."""
        if not AUDIO_AVAILABLE:
            return
        
        self.recording_voice = True
        self.voice_btn.set_icon_name("media-record-symbolic")
        self.voice_btn.add_css_class("destructive-action")
        
        # Record 5 seconds of audio
        sample_rate = 44100
        duration = 5
        
        def record_audio():
            try:
                self.voice_data = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=1, dtype=np.float32)
                sd.wait()
                GLib.idle_add(self.on_voice_recording_complete)
            except Exception as e:
                GLib.idle_add(self.show_error, f"Recording failed: {e}")
                GLib.idle_add(self.stop_voice_recording)
        
        threading.Thread(target=record_audio, daemon=True).start()
    
    def stop_voice_recording(self):
        """Stop voice recording."""
        self.recording_voice = False
        self.voice_btn.set_icon_name("audio-input-microphone-symbolic")
        self.voice_btn.remove_css_class("destructive-action")
    
    def on_voice_recording_complete(self):
        """Handle voice recording completion."""
        self.stop_voice_recording()
        
        if self.voice_data is not None and self.users:
            user = self.users[self.current_user_index]
            
            # Save voice data to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                # Convert numpy array to wav file
                import scipy.io.wavfile as wav
                wav.write(f.name, 44100, self.voice_data)
                voice_file = f.name
            
            # Disable UI during authentication
            self.set_ui_sensitive(False)
            
            # Perform authentication in background thread
            threading.Thread(
                target=self.authenticate_user,
                args=(user.username, voice_file, AuthMethod.VOICE),
                daemon=True
            ).start()
    
    def set_ui_sensitive(self, sensitive: bool):
        """Enable/disable UI elements."""
        self.password_entry.set_sensitive(sensitive)
        self.login_btn.set_sensitive(sensitive)
        self.voice_btn.set_sensitive(sensitive and AUDIO_AVAILABLE)
        self.face_btn.set_sensitive(sensitive)
        self.token_btn.set_sensitive(sensitive)
        self.guest_btn.set_sensitive(sensitive)
        self.session_dropdown.set_sensitive(sensitive)
    
    def show_error(self, message: str):
        """Show error message."""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(5)
        # Note: In a real implementation, you'd add this to a toast overlay
        print(f"Error: {message}")
    
    def show_success(self, message: str):
        """Show success message."""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(3)
        # Note: In a real implementation, you'd add this to a toast overlay
        print(f"Success: {message}")
    
    def show_info(self, message: str):
        """Show info message."""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(3)
        # Note: In a real implementation, you'd add this to a toast overlay
        print(f"Info: {message}")


class DriftApplication(Adw.Application):
    """Main Drift application."""
    
    def __init__(self):
        super().__init__(application_id="ai.marina.drift")
        self.connect("activate", self.on_activate)
    
    def on_activate(self, app):
        """Application activation."""
        self.window = DriftLoginWindow(self)
        self.window.present()


def main():
    """Main entry point."""
    if not GTK_AVAILABLE:
        print("GTK4 not available")
        return 1
    
    app = DriftApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
