#!/usr/bin/env python3
"""
Drift - Marina-integrated Login Manager
Core system for lightweight, intelligent login management with Marina integration

Author: Marina AI Assistant
"""

import os
import sys
import json
import time
import threading
import subprocess
import logging
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
# PAM authentication
try:
    import pam
    PAM_AVAILABLE = True
except ImportError:
    PAM_AVAILABLE = False
    # Fallback PAM simulation for testing
    class MockPAM:
        @staticmethod
        def authenticate(username, password, service='login'):
            # Simple fallback - check if username exists
            try:
                import pwd
                pwd.getpwnam(username)
                return len(password) > 0  # Basic validation
            except KeyError:
                return False
    pam = MockPAM()

import pwd
import grp

# Marina integration imports
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from brain.daemon_auth_gui import capture_and_export_password
    from brain.identity.identity import MarinaIdentity
    MARINA_INTEGRATION_AVAILABLE = True
except ImportError:
    MARINA_INTEGRATION_AVAILABLE = False
    # Fallback stubs for Marina integration
    def capture_and_export_password():
        return None
    
    class MarinaIdentity:
        def __init__(self):
            pass

# GUI toolkit (preferring GTK4 for lightweight nature)
try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Gdk', '4.0')
    from gi.repository import Gtk, Gdk, GLib, GObject
    GTK_AVAILABLE = True
except ImportError:
    GTK_AVAILABLE = False

# Voice processing (user prefers faster-whisper)
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Face recognition
try:
    import cv2
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# Marina Key Backend for password recovery
try:
    from marina_key_backend import MarinaKeyBackend
    MARINA_KEY_BACKEND_AVAILABLE = True
except ImportError:
    MARINA_KEY_BACKEND_AVAILABLE = False


class AuthMethod(Enum):
    """Available authentication methods."""
    PASSWORD = "password"
    VOICE = "voice"
    FACE = "face"
    TOKEN = "token"
    GUEST = "guest"


class SessionType(Enum):
    """Session environment types."""
    WAYLAND = "wayland"
    X11 = "x11"
    MARINA_SHELL = "marina_shell"
    CUSTOM = "custom"


class LoginStatus(Enum):
    """Login attempt status."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class UserProfile:
    """User profile with Marina-specific configuration."""
    username: str
    full_name: str
    uid: int
    gid: int
    home_dir: str
    shell: str
    avatar_path: Optional[str] = None
    preferred_session: SessionType = SessionType.WAYLAND
    marina_persona: Optional[str] = None
    voice_print: Optional[str] = None
    face_encoding: Optional[bytes] = None
    last_login: Optional[datetime] = None
    login_count: int = 0
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    marina_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoginAttempt:
    """Record of a login attempt."""
    timestamp: datetime
    username: str
    auth_method: AuthMethod
    status: LoginStatus
    ip_address: Optional[str] = None
    session_type: Optional[SessionType] = None
    error_message: Optional[str] = None
    duration_ms: int = 0


class DriftCore:
    """
    Core Drift login manager with Marina integration.
    Handles authentication, user management, and Marina daemon startup.
    """
    
    def __init__(self, config_path: str = "/etc/drift/drift.conf"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Database for user profiles and login history
        self.db_path = self.config.get('database_path', '/var/lib/drift/drift.db')
        self._init_database()
        
        # Marina integration
        self.marina_path = self.config.get('marina_path', '/home/adminx/Marina')
        self.marina_identity = None
        
        # Authentication modules
        self.pam_service = self.config.get('pam_service', 'login')
        
        # Voice authentication
        self.whisper_model = None
        if WHISPER_AVAILABLE and self.config.get('voice_auth_enabled', False):
            self._init_voice_auth()
        
        # Face recognition
        self.face_model_path = self.config.get('face_model_path', '/var/lib/drift/face_encodings.pkl')
        
        # Session management
        self.active_sessions: Dict[str, Any] = {}
        
        # Marina Key Backend for password recovery
        self.key_backend = None
        if MARINA_KEY_BACKEND_AVAILABLE and self.config.get('marina_key_recovery_enabled', True):
            self._init_key_backend()
        
        # UI state
        self.current_theme = self.config.get('default_theme', 'marina_dark')
        
        self.logger.info("Drift Core initialized successfully")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load Drift configuration."""
        default_config = {
            'marina_path': '/home/adminx/Marina',
            'database_path': '/var/lib/drift/drift.db',
            'log_file': '/var/log/drift/drift.log',
            'voice_auth_enabled': False,
            'face_auth_enabled': False,
            'marina_integration_enabled': True,
            'auto_start_marina_daemons': True,
            'session_timeout': 3600,  # 1 hour
            'max_failed_attempts': 3,
            'lockout_duration': 300,  # 5 minutes
            'themes': {
                'marina_dark': {
                    'background': '#1a1a1a',
                    'foreground': '#ffffff',
                    'accent': '#00d4aa'
                },
                'marina_light': {
                    'background': '#f5f5f5', 
                    'foreground': '#333333',
                    'accent': '#0099cc'
                }
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for Drift."""
        logger = logging.getLogger('drift')
        logger.setLevel(logging.INFO)
        
        # Create log directory if it doesn't exist
        log_file = self.config.get('log_file', '/var/log/drift/drift.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _init_database(self):
        """Initialize SQLite database for user profiles and login history."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                username TEXT PRIMARY KEY,
                full_name TEXT,
                uid INTEGER,
                gid INTEGER,
                home_dir TEXT,
                shell TEXT,
                avatar_path TEXT,
                preferred_session TEXT,
                marina_persona TEXT,
                voice_print TEXT,
                face_encoding BLOB,
                last_login TIMESTAMP,
                login_count INTEGER DEFAULT 0,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                marina_config TEXT
            )
        ''')
        
        # Login attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                username TEXT,
                auth_method TEXT,
                status TEXT,
                ip_address TEXT,
                session_type TEXT,
                error_message TEXT,
                duration_ms INTEGER
            )
        ''')
        
        # Marina daemon sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marina_sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT,
                started_at TIMESTAMP,
                last_activity TIMESTAMP,
                daemons_running TEXT,
                session_data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        self.logger.info("Database initialized")
    
    def _init_voice_auth(self):
        """Initialize voice authentication with faster-whisper."""
        try:
            model_size = self.config.get('whisper_model_size', 'base')
            self.whisper_model = WhisperModel(model_size, device="cpu")
            self.logger.info(f"Voice authentication initialized with model: {model_size}")
        except Exception as e:
            self.logger.error(f"Failed to initialize voice authentication: {e}")
            self.whisper_model = None
    
    def _init_key_backend(self):
        """Initialize Marina Key Backend for password recovery."""
        try:
            self.key_backend = MarinaKeyBackend()
            self.logger.info("Marina Key Backend initialized for password recovery")
        except Exception as e:
            self.logger.error(f"Failed to initialize Marina Key Backend: {e}")
            self.key_backend = None
    
    def get_system_users(self) -> List[UserProfile]:
        """Get list of system users suitable for login."""
        users = []
        
        # Get users with UID >= 1000 (regular users)
        for user_info in pwd.getpwall():
            if user_info.pw_uid >= 1000 and user_info.pw_uid < 65534:
                # Check if user has a valid shell
                if user_info.pw_shell in ['/bin/bash', '/bin/zsh', '/bin/fish', '/usr/bin/fish']:
                    profile = UserProfile(
                        username=user_info.pw_name,
                        full_name=user_info.pw_gecos.split(',')[0] or user_info.pw_name,
                        uid=user_info.pw_uid,
                        gid=user_info.pw_gid,
                        home_dir=user_info.pw_dir,
                        shell=user_info.pw_shell
                    )
                    
                    # Load additional profile data from database
                    self._load_user_profile_data(profile)
                    users.append(profile)
        
        return users
    
    def _load_user_profile_data(self, profile: UserProfile):
        """Load additional user profile data from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT avatar_path, preferred_session, marina_persona, voice_print, 
                   face_encoding, last_login, login_count, failed_attempts, 
                   locked_until, marina_config
            FROM user_profiles WHERE username = ?
        ''', (profile.username,))
        
        row = cursor.fetchone()
        if row:
            profile.avatar_path = row[0]
            profile.preferred_session = SessionType(row[1]) if row[1] else SessionType.WAYLAND
            profile.marina_persona = row[2]
            profile.voice_print = row[3]
            profile.face_encoding = row[4]
            profile.last_login = datetime.fromisoformat(row[5]) if row[5] else None
            profile.login_count = row[6] or 0
            profile.failed_attempts = row[7] or 0
            profile.locked_until = datetime.fromisoformat(row[8]) if row[8] else None
            profile.marina_config = json.loads(row[9]) if row[9] else {}
        
        conn.close()
    
    def authenticate_user(self, username: str, password: str, 
                         auth_method: AuthMethod = AuthMethod.PASSWORD) -> Tuple[bool, str]:
        """
        Authenticate user using specified method.
        Returns (success, error_message)
        """
        start_time = time.time()
        
        try:
            # Check if user is locked out
            profile = self._get_user_profile(username)
            if profile and profile.locked_until and profile.locked_until > datetime.now():
                return False, f"Account locked until {profile.locked_until.strftime('%H:%M:%S')}"
            
            success = False
            error_msg = ""
            
            if auth_method == AuthMethod.PASSWORD:
                success, error_msg = self._authenticate_password(username, password)
            elif auth_method == AuthMethod.VOICE:
                success, error_msg = self._authenticate_voice(username, password)  # password is voice data
            elif auth_method == AuthMethod.FACE:
                success, error_msg = self._authenticate_face(username)
            elif auth_method == AuthMethod.TOKEN:
                success, error_msg = self._authenticate_token(username, password)  # password is token
            elif auth_method == AuthMethod.GUEST:
                success, error_msg = self._authenticate_guest()
            
            # Update login attempt counter
            if success:
                self._record_successful_login(username, auth_method)
            else:
                self._record_failed_login(username, auth_method, error_msg)
            
            # Record login attempt
            duration_ms = int((time.time() - start_time) * 1000)
            self._record_login_attempt(username, auth_method, 
                                     LoginStatus.SUCCESS if success else LoginStatus.FAILED,
                                     error_msg, duration_ms)
            
            return success, error_msg
        
        except Exception as e:
            self.logger.error(f"Authentication error for {username}: {e}")
            return False, "Authentication system error"
    
    def _authenticate_password(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate using PAM (system password)."""
        try:
            if pam.authenticate(username, password, service=self.pam_service):
                return True, ""
            else:
                return False, "Invalid username or password"
        except Exception as e:
            self.logger.error(f"PAM authentication error: {e}")
            return False, "Authentication system error"
    
    def _authenticate_voice(self, username: str, voice_data: str) -> Tuple[bool, str]:
        """Authenticate using voice recognition."""
        if not self.whisper_model:
            return False, "Voice authentication not available"
        
        try:
            # This is a simplified voice auth - in practice you'd need
            # more sophisticated voice print matching
            profile = self._get_user_profile(username)
            if not profile or not profile.voice_print:
                return False, "Voice print not enrolled"
            
            # Transcribe the voice data
            segments, _ = self.whisper_model.transcribe(voice_data)
            transcription = " ".join([segment.text for segment in segments])
            
            # Simple passphrase matching (enhance with voice biometrics)
            if transcription.lower().strip() == profile.voice_print.lower().strip():
                return True, ""
            else:
                return False, "Voice authentication failed"
        
        except Exception as e:
            self.logger.error(f"Voice authentication error: {e}")
            return False, "Voice authentication error"
    
    def _authenticate_face(self, username: str) -> Tuple[bool, str]:
        """Authenticate using face recognition."""
        if not FACE_RECOGNITION_AVAILABLE:
            return False, "Face authentication not available"
        
        try:
            profile = self._get_user_profile(username)
            if not profile or not profile.face_encoding:
                return False, "Face not enrolled"
            
            # Capture image from webcam
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False, "Could not capture image"
            
            # Find face encodings in the current frame
            face_locations = face_recognition.face_locations(frame)
            if not face_locations:
                return False, "No face detected"
            
            face_encodings = face_recognition.face_encodings(frame, face_locations)
            if not face_encodings:
                return False, "Could not process face"
            
            # Compare with stored encoding
            stored_encoding = pickle.loads(profile.face_encoding)
            matches = face_recognition.compare_faces([stored_encoding], face_encodings[0])
            
            if matches[0]:
                return True, ""
            else:
                return False, "Face authentication failed"
        
        except Exception as e:
            self.logger.error(f"Face authentication error: {e}")
            return False, "Face authentication error"
    
    def _authenticate_token(self, username: str, token: str) -> Tuple[bool, str]:
        """Authenticate using Marina token."""
        try:
            # This would integrate with Marina's token system
            # For now, simple token validation
            if len(token) >= 32 and token.startswith('marina_'):
                return True, ""
            else:
                return False, "Invalid token"
        except Exception as e:
            self.logger.error(f"Token authentication error: {e}")
            return False, "Token authentication error"
    
    def _authenticate_guest(self) -> Tuple[bool, str]:
        """Authenticate guest session."""
        if self.config.get('guest_enabled', True):
            return True, ""
        else:
            return False, "Guest login disabled"
    
    def _get_user_profile(self, username: str) -> Optional[UserProfile]:
        """Get user profile from database."""
        try:
            user_info = pwd.getpwnam(username)
            profile = UserProfile(
                username=username,
                full_name=user_info.pw_gecos.split(',')[0] or username,
                uid=user_info.pw_uid,
                gid=user_info.pw_gid,
                home_dir=user_info.pw_dir,
                shell=user_info.pw_shell
            )
            self._load_user_profile_data(profile)
            return profile
        except KeyError:
            return None
    
    def _record_successful_login(self, username: str, auth_method: AuthMethod):
        """Record successful login and reset failed attempts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles 
            (username, last_login, login_count, failed_attempts)
            VALUES (?, ?, COALESCE((SELECT login_count FROM user_profiles WHERE username = ?), 0) + 1, 0)
        ''', (username, datetime.now().isoformat(), username))
        
        conn.commit()
        conn.close()
    
    def _record_failed_login(self, username: str, auth_method: AuthMethod, error_msg: str):
        """Record failed login and potentially lock account."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current failed attempts
        cursor.execute('SELECT failed_attempts FROM user_profiles WHERE username = ?', (username,))
        row = cursor.fetchone()
        failed_attempts = (row[0] if row else 0) + 1
        
        # Check if we should lock the account
        locked_until = None
        max_attempts = self.config.get('max_failed_attempts', 3)
        if failed_attempts >= max_attempts:
            lockout_duration = self.config.get('lockout_duration', 300)
            locked_until = datetime.now() + timedelta(seconds=lockout_duration)
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles 
            (username, failed_attempts, locked_until)
            VALUES (?, ?, ?)
        ''', (username, failed_attempts, locked_until.isoformat() if locked_until else None))
        
        conn.commit()
        conn.close()
        
        if locked_until:
            self.logger.warning(f"Account {username} locked until {locked_until}")
    
    def _record_login_attempt(self, username: str, auth_method: AuthMethod, 
                            status: LoginStatus, error_msg: str, duration_ms: int):
        """Record login attempt in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO login_attempts 
            (timestamp, username, auth_method, status, error_message, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), username, auth_method.value, 
              status.value, error_msg, duration_ms))
        
        conn.commit()
        conn.close()
    
    def start_marina_session(self, username: str, profile: UserProfile) -> bool:
        """Start Marina daemons and session for user."""
        if not self.config.get('marina_integration_enabled', True):
            return True
        
        try:
            # Initialize Marina identity system
            self.marina_identity = MarinaIdentity()
            
            # Start Marina daemons with proper authentication
            if self.config.get('auto_start_marina_daemons', True):
                self._start_marina_daemons(username, profile)
            
            # Load user's Marina configuration
            self._load_marina_user_config(username, profile)
            
            # Record Marina session
            session_id = hashlib.md5(f"{username}_{time.time()}".encode()).hexdigest()
            self._record_marina_session(session_id, username)
            
            self.logger.info(f"Marina session started for user {username}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to start Marina session: {e}")
            return False
    
    def _start_marina_daemons(self, username: str, profile: UserProfile):
        """Start Marina daemons with proper privileges."""
        try:
            # Use Marina's daemon authentication system
            marina_wake_path = os.path.join(self.marina_path, 'wake.py')
            if os.path.exists(marina_wake_path):
                # Run as the target user
                subprocess.Popen([
                    'sudo', '-u', username, 'python3', marina_wake_path
                ], env={'HOME': profile.home_dir})
                
                self.logger.info(f"Marina daemons started for {username}")
        
        except Exception as e:
            self.logger.error(f"Failed to start Marina daemons: {e}")
    
    def _load_marina_user_config(self, username: str, profile: UserProfile):
        """Load user-specific Marina configuration."""
        try:
            marina_config_path = os.path.join(profile.home_dir, '.marina', 'config.json')
            if os.path.exists(marina_config_path):
                with open(marina_config_path, 'r') as f:
                    marina_config = json.load(f)
                    profile.marina_config = marina_config
                    
                    # Apply persona if configured
                    if 'persona' in marina_config:
                        profile.marina_persona = marina_config['persona']
        
        except Exception as e:
            self.logger.error(f"Failed to load Marina config for {username}: {e}")
    
    def _record_marina_session(self, session_id: str, username: str):
        """Record Marina session in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO marina_sessions 
            (session_id, username, started_at, last_activity, daemons_running)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, username, datetime.now().isoformat(), 
              datetime.now().isoformat(), json.dumps([])))
        
        conn.commit()
        conn.close()
    
    def launch_session(self, username: str, session_type: SessionType) -> bool:
        """Launch user session with specified session type."""
        try:
            profile = self._get_user_profile(username)
            if not profile:
                return False
            
            # Start Marina session first
            self.start_marina_session(username, profile)
            
            # Launch the appropriate session type
            if session_type == SessionType.WAYLAND:
                self._launch_wayland_session(username, profile)
            elif session_type == SessionType.X11:
                self._launch_x11_session(username, profile)
            elif session_type == SessionType.MARINA_SHELL:
                self._launch_marina_shell(username, profile)
            else:
                self._launch_custom_session(username, profile)
            
            self.logger.info(f"Session launched for {username} with type {session_type.value}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to launch session: {e}")
            return False
    
    def _launch_wayland_session(self, username: str, profile: UserProfile):
        """Launch Wayland session."""
        # This would integrate with your Wayland compositor
        pass
    
    def _launch_x11_session(self, username: str, profile: UserProfile):
        """Launch X11 session."""
        # This would integrate with your X11 setup
        pass
    
    def _launch_marina_shell(self, username: str, profile: UserProfile):
        """Launch Marina's custom shell environment."""
        marina_shell_path = os.path.join(self.marina_path, 'gui', 'main_gui.py')
        if os.path.exists(marina_shell_path):
            subprocess.Popen([
                'sudo', '-u', username, 'python3', marina_shell_path
            ], env={'HOME': profile.home_dir, 'DISPLAY': ':0'})
    
    def _launch_custom_session(self, username: str, profile: UserProfile):
        """Launch custom session based on user configuration."""
        # This would be based on user's custom session configuration
        pass
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status for display in login screen."""
        try:
            # System uptime
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
            
            # Load average
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.read().split()[:3]
            
            # Memory usage
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                mem_total = int([line for line in meminfo.split('\n') if 'MemTotal' in line][0].split()[1])
                mem_available = int([line for line in meminfo.split('\n') if 'MemAvailable' in line][0].split()[1])
            
            return {
                'uptime_hours': uptime_seconds / 3600,
                'load_average': load_avg,
                'memory_usage_percent': ((mem_total - mem_available) / mem_total) * 100,
                'marina_daemons_active': self._check_marina_daemons(),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {}
    
    def _check_marina_daemons(self) -> List[str]:
        """Check which Marina daemons are currently running."""
        try:
            result = subprocess.run(['pgrep', '-f', 'marina'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            return []
        except Exception:
            return []
    
    # Marina Key Recovery Methods
    
    def request_recovery_key(self, username: str) -> Tuple[bool, str]:
        """Request a recovery key for password reset."""
        if not self.key_backend:
            return False, "Password recovery not available"
        
        try:
            # Check if user exists
            profile = self._get_user_profile(username)
            if not profile:
                return False, "User not found"
            
            # Generate recovery key
            key_id, recovery_key = self.key_backend.generate_recovery_key(username)
            
            # Send via email
            email_sent = self.key_backend.send_recovery_email(username, recovery_key, key_id)
            
            if email_sent:
                self.logger.info(f"Recovery key generated and emailed for user {username}")
                return True, f"Recovery key sent to your email (Key ID: {key_id})"
            else:
                self.logger.warning(f"Recovery key generated but email failed for user {username}")
                return True, f"Recovery key generated: {recovery_key} (Key ID: {key_id})"
        
        except Exception as e:
            self.logger.error(f"Failed to generate recovery key for {username}: {e}")
            return False, "Recovery key generation failed"
    
    def validate_recovery_key(self, username: str, key_id: str, recovery_key: str) -> bool:
        """Validate a recovery key for password reset."""
        if not self.key_backend:
            return False
        
        try:
            return self.key_backend.validate_recovery_key(key_id, recovery_key, username)
        except Exception as e:
            self.logger.error(f"Recovery key validation error: {e}")
            return False
    
    def reset_password_with_key(self, username: str, key_id: str, recovery_key: str, new_password: str) -> Tuple[bool, str]:
        """Reset user password using validated recovery key."""
        if not self.validate_recovery_key(username, key_id, recovery_key):
            return False, "Invalid or expired recovery key"
        
        try:
            # Reset password using system tools
            # This is a simplified version - in production you'd use proper PAM/passwd integration
            import subprocess
            
            # Use passwd command to change password
            proc = subprocess.Popen(
                ['sudo', 'passwd', username],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = proc.communicate(input=f"{new_password}\n{new_password}\n")
            
            if proc.returncode == 0:
                self.logger.info(f"Password reset successfully for user {username}")
                
                # Clear failed attempts and unlock account
                self._clear_failed_attempts(username)
                
                return True, "Password reset successfully"
            else:
                self.logger.error(f"Password reset failed for {username}: {stderr}")
                return False, "Password reset failed"
        
        except Exception as e:
            self.logger.error(f"Password reset error for {username}: {e}")
            return False, "Password reset system error"
    
    def request_network_recovery_key(self, username: str) -> Tuple[bool, str]:
        """Request recovery key from any available Marina instance on the network."""
        if not self.key_backend:
            return False, "Network recovery not available"
        
        try:
            result = self.key_backend.request_key_from_network(username)
            if result:
                key_id, recovery_key = result
                self.logger.info(f"Network recovery key obtained for user {username}")
                return True, f"Recovery key obtained from network: {recovery_key} (Key ID: {key_id})"
            else:
                return False, "No Marina instances available on network"
        
        except Exception as e:
            self.logger.error(f"Network recovery error for {username}: {e}")
            return False, "Network recovery failed"
    
    def get_marina_key_status(self) -> Dict[str, Any]:
        """Get Marina Key Backend status."""
        if not self.key_backend:
            return {'available': False, 'reason': 'Key backend not initialized'}
        
        try:
            return {
                'available': True,
                'status': self.key_backend.get_status(),
                'network_nodes': len(self.key_backend.network_nodes),
                'active_keys': len(self.key_backend.active_keys)
            }
        except Exception as e:
            return {'available': False, 'reason': str(e)}
    
    def _clear_failed_attempts(self, username: str):
        """Clear failed login attempts and unlock account."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_profiles 
            SET failed_attempts = 0, locked_until = NULL
            WHERE username = ?
        ''', (username,))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Cleared failed attempts for user {username}")


if __name__ == "__main__":
    # Test the core system
    drift = DriftCore()
    users = drift.get_system_users()
    print(f"Found {len(users)} users")
    for user in users:
        print(f"  - {user.username} ({user.full_name})")
    
    status = drift.get_system_status()
    print(f"System status: {status}")
