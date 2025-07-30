# 🌊 Drift - Marina-integrated Login Manager

**Where Marina drifts in as your system awakens**

Drift is a lightweight, intelligent, and secure login manager specifically designed for Marina's agent-based ecosystem. It provides a beautiful, Marina-themed login experience with advanced authentication methods and seamless integration with Marina's daemons and services.

## ✨ Features

### 🎨 Beautiful Interface
- **Marina-themed Design**: Liquid-glass ripple effects with Marina's signature colors
- **Responsive Layout**: Adapts to different screen sizes and resolutions
- **Real-time Status**: Live system monitoring and Marina daemon status
- **Mood-aware Theming**: Automatic theme switching based on time of day

### 🔐 Advanced Authentication
- **Multi-method Login**: Password, voice, face, Marina token, and guest sessions
- **Voice Authentication**: Using faster-whisper (respecting user preferences)
- **Face Recognition**: Local face detection and matching
- **Marina Token Auth**: Integration with Marina's secure token system
- **Account Lockout**: Intelligent lockout policies with user-friendly feedback

### 🤖 Marina Integration
- **Daemon Startup**: Automatic Marina daemon launching on successful login
- **Persona Switching**: Detect and load user-specific Marina personas
- **Context Awareness**: Login screen shows Marina system status
- **Session Types**: Support for Wayland, X11, and Marina's custom shell
- **User Profiles**: Marina-specific user configuration and preferences

### 🛡️ Security & Reliability
- **PAM Integration**: Standard Linux authentication backend
- **Secure Storage**: Encrypted user data and authentication logs
- **Audit Trail**: Comprehensive login attempt logging
- **Fail-safe Mode**: System still works even if Marina components fail
- **Sandboxed Operation**: Isolated file access and privilege separation

## 🚀 Quick Start

### Prerequisites
- **Linux System**: Pop!_OS, Ubuntu, Fedora, or Arch Linux
- **Python 3.8+**: With pip and development headers
- **GTK4**: For the graphical interface
- **Marina**: Existing Marina installation

### Installation

1. **Clone or copy the Drift directory to your Marina installation**:
   ```bash
   cd /home/adminx/Marina
   # Drift directory should already be present
   ```

2. **Run the installation script**:
   ```bash
   cd Drift
   sudo chmod +x install.sh
   sudo ./install.sh
   ```

3. **Configure your display manager** (optional):
   ```bash
   # Disable GDM (if using GNOME)
   sudo systemctl disable gdm
   
   # Or disable LightDM
   sudo systemctl disable lightdm
   ```

4. **Start Drift**:
   ```bash
   sudo systemctl start drift-login.service
   ```

### Testing (Without Replacing System Login)

You can test Drift without replacing your system login manager:

```bash
# Test the GUI in windowed mode
DRIFT_FULLSCREEN=0 driftctl gui

# Test authentication
driftctl test-auth adminx password

# Check system status
driftctl status
```

## 🎛️ Configuration

### Main Configuration File
Edit `/etc/drift/drift.conf`:

```json
{
    "marina_path": "/home/adminx/Marina",
    "voice_auth_enabled": true,
    "face_auth_enabled": true,
    "marina_integration_enabled": true,
    "auto_start_marina_daemons": true,
    "session_timeout": 3600,
    "max_failed_attempts": 3,
    "lockout_duration": 300,
    "guest_enabled": true,
    "default_theme": "marina_dark"
}
```

### User Configuration

```bash
# Set Marina persona for a user
driftctl set-persona adminx "developer"

# Enable voice authentication
driftctl enable-voice adminx "marina open system"

# View user information
driftctl list-users
```

## 🔧 CLI Usage

Drift comes with a powerful command-line interface:

### User Management
```bash
# List all users
driftctl list-users

# Show detailed user information with Marina context
driftctl status

# Unlock a locked user account
driftctl unlock username
```

### Authentication Testing
```bash
# Test different authentication methods
driftctl test-auth adminx password
driftctl test-auth adminx voice
driftctl test-auth adminx face
driftctl test-auth adminx token
```

### Marina Integration
```bash
# Set Marina persona
driftctl set-persona adminx "assistant"
driftctl set-persona jane "researcher"
driftctl set-persona dev "developer"

# Enable advanced authentication
driftctl enable-voice adminx "marina authenticate user"
```

### System Monitoring
```bash
# Show system and Marina status
driftctl status

# View login history
driftctl history --user adminx --days 30

# Show recent logs
driftctl logs --lines 100

# Clean up old data
driftctl cleanup --days 30
```

## 🏗️ Architecture

### Core Components

1. **`drift_core.py`**: Core authentication and Marina integration logic
2. **`drift_gui.py`**: GTK4-based graphical user interface
3. **`driftctl`**: Command-line interface and management tool

### Authentication Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  Authentication  │───▶│ Marina Session  │
│                 │    │     Engine       │    │     Startup     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  GUI Interface  │    │   PAM/Security   │    │  Session Launch │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Database Schema

Drift uses SQLite to store:
- **User Profiles**: Marina personas, authentication preferences
- **Login Attempts**: Audit trail with timestamps and results
- **Marina Sessions**: Active daemon tracking and session data

## 🎨 Themes

### Marina Dark (Default)
- **Background**: Deep gradient from #1a1a1a to #0d1421
- **Accent**: Marina teal (#00d4aa)
- **Text**: Clean white and light gray

### Marina Light
- **Background**: Light gradient with warm tones
- **Accent**: Marina blue (#0099cc)
- **Text**: Dark gray on light background

### Custom Themes
Add custom themes in the configuration file:

```json
{
  "themes": {
    "custom_theme": {
      "background": "#your_color",
      "foreground": "#text_color",
      "accent": "#accent_color"
    }
  }
}
```

## 🔌 Marina Integration Details

### Daemon Startup Sequence
1. **Authentication Success**: User credentials validated
2. **Marina Identity**: Initialize Marina identity system
3. **Daemon Launch**: Start Marina daemons with proper user context
4. **Persona Loading**: Apply user-specific Marina configuration
5. **Session Handoff**: Launch selected session type

### Supported Session Types
- **Wayland**: Modern display protocol with Marina integration
- **X11**: Traditional X Window System with Marina overlay
- **Marina Shell**: Custom Marina-native desktop environment
- **Custom**: User-defined session configuration

### Context Awareness
- **System Status**: Real-time monitoring of system resources
- **Marina Daemons**: Live status of Marina background services
- **User History**: Login patterns and Marina usage statistics
- **Environment**: Automatic configuration based on time, weather, etc.

## 🛠️ Development

### Project Structure
```
Drift/
├── drift_core.py          # Core authentication logic
├── drift_gui.py           # GTK4 user interface
├── driftctl               # CLI management tool
├── drift-login.service    # Systemd service file
├── install.sh             # Installation script
└── README.md              # This documentation
```

### Adding Authentication Methods

To add a new authentication method:

1. **Add enum value** in `drift_core.py`:
   ```python
   class AuthMethod(Enum):
       NEW_METHOD = "new_method"
   ```

2. **Implement authentication logic**:
   ```python
   def _authenticate_new_method(self, username: str, data: str) -> Tuple[bool, str]:
       # Your authentication logic here
       return success, error_message
   ```

3. **Add GUI controls** in `drift_gui.py`
4. **Update CLI** in `driftctl`

### Contributing

1. Follow Marina's coding standards
2. Test with multiple user accounts
3. Ensure Marina integration works correctly
4. Update documentation for new features

## 🐛 Troubleshooting

### Common Issues

**Q: Drift GUI doesn't start**
```bash
# Check GTK4 installation
python3 -c "import gi; gi.require_version('Gtk', '4.0')"

# Check logs
journalctl -u drift-login.service -f
```

**Q: Authentication fails**
```bash
# Test PAM configuration
driftctl test-auth username password

# Check user database
driftctl list-users
```

**Q: Marina daemons don't start**
```bash
# Check Marina path in configuration
driftctl status

# Test Marina wake script
sudo -u username python3 /home/adminx/Marina/wake.py
```

**Q: Voice authentication not working**
```bash
# Check faster-whisper installation
python3 -c "from faster_whisper import WhisperModel"

# Test audio recording
driftctl test-auth username voice
```

### Debug Mode

Enable debug logging:
```bash
# Set debug environment
export DRIFT_DEBUG=1

# View detailed logs
tail -f /var/log/drift/drift.log
```

## 📋 Roadmap

### v1.1 (Next Release)
- [ ] **Biometric Integration**: Fingerprint scanner support
- [ ] **Multi-factor Auth**: Combine authentication methods
- [ ] **Remote Access**: Marina token authentication via mobile app
- [ ] **Session Recording**: Optional session activity logging

### v1.2 (Future)
- [ ] **AI-powered UX**: Intelligent user pattern recognition
- [ ] **Voice Commands**: Login via voice commands
- [ ] **Gesture Control**: Hand gesture authentication
- [ ] **Marina Sync**: Cross-device Marina state synchronization

### v2.0 (Long-term)
- [ ] **Distributed Auth**: Multi-machine Marina ecosystem login
- [ ] **Quantum Security**: Post-quantum cryptography support
- [ ] **AR/VR Interface**: Immersive login environments
- [ ] **Neural Integration**: Direct brain-computer interface support

## 📄 License

Drift is part of the Marina ecosystem and follows Marina's licensing terms.

## 🙏 Acknowledgments

- **Marina Team**: For the incredible AI assistant platform
- **GTK Project**: For the beautiful UI toolkit
- **faster-whisper**: For efficient speech recognition
- **PAM**: For secure authentication infrastructure

---

**🌊 Drift - Where your system awakens with Marina's intelligence**

*Built with ❤️ for the Marina ecosystem*
