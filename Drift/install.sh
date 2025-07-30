#!/bin/bash
"""
Drift Installation Script
Install Marina-integrated Login Manager

Author: Marina AI Assistant
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DRIFT_DIR="/opt/marina/drift"
CONFIG_DIR="/etc/drift"
DATA_DIR="/var/lib/drift"
LOG_DIR="/var/log/drift"
SERVICE_NAME="drift-login.service"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # GTK4 development libraries
    if ! python3 -c "import gi; gi.require_version('Gtk', '4.0')" 2>/dev/null; then
        print_warning "GTK4 Python bindings not found. Installing..."
        
        # Detect package manager and install
        if command -v apt &> /dev/null; then
            apt update
            apt install -y python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
        elif command -v dnf &> /dev/null; then
            dnf install -y python3-gobject gtk4-devel libadwaita-devel
        elif command -v pacman &> /dev/null; then
            pacman -S --noconfirm python-gobject gtk4 libadwaita
        else
            print_error "Unable to install GTK4 dependencies. Please install manually."
            exit 1
        fi
    fi
    
    # PAM development libraries
    if ! python3 -c "import pam" 2>/dev/null; then
        print_warning "Python PAM module not found. Installing..."
        pip3 install python-pam
    fi
    
    print_success "Dependencies checked"
}

# Create directories
create_directories() {
    print_status "Creating directories..."
    
    mkdir -p "$DRIFT_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    
    # Set permissions
    chmod 755 "$DRIFT_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 700 "$DATA_DIR"
    chmod 755 "$LOG_DIR"
    
    print_success "Directories created"
}

# Install Drift files
install_files() {
    print_status "Installing Drift files..."
    
    # Copy Python files
    cp drift_core.py "$DRIFT_DIR/"
    cp drift_gui.py "$DRIFT_DIR/"
    cp driftctl "$DRIFT_DIR/"
    
    # Make driftctl executable
    chmod +x "$DRIFT_DIR/driftctl"
    
    # Create symlink in /usr/local/bin
    ln -sf "$DRIFT_DIR/driftctl" /usr/local/bin/driftctl
    
    # Copy service file
    cp "$SERVICE_NAME" /etc/systemd/system/
    
    # Create default configuration
    if [[ ! -f "$CONFIG_DIR/drift.conf" ]]; then
        cat > "$CONFIG_DIR/drift.conf" << EOF
{
    "marina_path": "/home/adminx/Marina",
    "database_path": "$DATA_DIR/drift.db",
    "log_file": "$LOG_DIR/drift.log",
    "voice_auth_enabled": false,
    "face_auth_enabled": false,
    "marina_integration_enabled": true,
    "auto_start_marina_daemons": true,
    "session_timeout": 3600,
    "max_failed_attempts": 3,
    "lockout_duration": 300,
    "guest_enabled": true,
    "default_theme": "marina_dark",
    "themes": {
        "marina_dark": {
            "background": "#1a1a1a",
            "foreground": "#ffffff",
            "accent": "#00d4aa"
        },
        "marina_light": {
            "background": "#f5f5f5",
            "foreground": "#333333",
            "accent": "#0099cc"
        }
    }
}
EOF
    fi
    
    print_success "Files installed"
}

# Setup systemd service
setup_service() {
    print_status "Setting up systemd service..."
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service (but don't start yet)
    systemctl enable "$SERVICE_NAME"
    
    print_success "Service configured"
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Run drift_core to initialize database
    cd "$DRIFT_DIR"
    python3 -c "from drift_core import DriftCore; DriftCore()"
    
    print_success "Database initialized"
}

# Create PAM configuration
setup_pam() {
    print_status "Setting up PAM configuration..."
    
    # Create PAM configuration for Drift
    cat > /etc/pam.d/drift << EOF
#%PAM-1.0
auth       required     pam_unix.so
auth       required     pam_env.so
account    required     pam_unix.so
password   required     pam_unix.so
session    required     pam_unix.so
session    required     pam_env.so
EOF
    
    print_success "PAM configuration created"
}

# Show installation summary
show_summary() {
    print_success "Drift installation completed!"
    echo
    echo "Installation Summary:"
    echo "  - Drift installed to: $DRIFT_DIR"
    echo "  - Configuration: $CONFIG_DIR/drift.conf"
    echo "  - Database: $DATA_DIR/drift.db"
    echo "  - Logs: $LOG_DIR/drift.log"
    echo "  - Service: $SERVICE_NAME"
    echo
    echo "Next steps:"
    echo "1. Configure your display manager to disable default login screen"
    echo "2. Start Drift service: systemctl start $SERVICE_NAME"
    echo "3. Test login functionality: driftctl gui"
    echo "4. Configure users: driftctl list-users"
    echo
    echo "Common commands:"
    echo "  driftctl status           # Show system status"
    echo "  driftctl list-users       # List available users"
    echo "  driftctl gui              # Start GUI (for testing)"
    echo "  driftctl enable-voice <user> <phrase>  # Enable voice auth"
    echo "  driftctl set-persona <user> <persona>  # Set Marina persona"
    echo
    print_warning "Remember to backup your Marina configuration before enabling Drift!"
}

# Main installation
main() {
    echo "🌊 Drift - Marina-integrated Login Manager Installer"
    echo "=================================================="
    echo
    
    check_root
    check_dependencies
    create_directories
    install_files
    setup_service
    init_database
    setup_pam
    show_summary
}

# Run installation
main "$@"
