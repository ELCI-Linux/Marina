#!/bin/bash
# Installation script for Marina Bluetooth Monitor

set -e

echo "🚀 Installing Marina Bluetooth Monitor..."

# Check if running as root for system service installation
if [[ $EUID -eq 0 ]]; then
    echo "❌ Don't run this script as root. It will prompt for sudo when needed."
    exit 1
fi

# Check if bluetoothctl is available
if ! command -v bluetoothctl &> /dev/null; then
    echo "❌ bluetoothctl not found. Installing bluetooth tools..."
    sudo apt update
    sudo apt install -y bluetooth bluez-tools
fi

# Add user to bluetooth group
echo "👤 Adding user to bluetooth group..."
sudo usermod -a -G bluetooth $USER

# Copy service file to systemd directory
echo "📁 Installing systemd service..."
sudo cp marina-bluetooth-monitor.service /etc/systemd/system/

# Reload systemd and enable the service
echo "🔄 Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable marina-bluetooth-monitor.service

# Test the script
echo "🧪 Testing Bluetooth monitor script..."
python3 bluetooth_monitor.py --test

echo "✅ Installation complete!"
echo ""
echo "To start the service:"
echo "  sudo systemctl start marina-bluetooth-monitor"
echo ""
echo "To check status:"
echo "  sudo systemctl status marina-bluetooth-monitor"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u marina-bluetooth-monitor -f"
echo ""
echo "To stop the service:"
echo "  sudo systemctl stop marina-bluetooth-monitor"
echo ""
echo "⚠️  You may need to log out and back in for group changes to take effect."
