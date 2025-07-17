#!/bin/bash
# Combined installation script for Marina Device Monitors

set -e

echo "🚀 Installing Marina Device Monitors..."

# Check if running as root for system service installation
if [[ $EUID -eq 0 ]]; then
    echo "❌ Don't run this script as root. It will prompt for sudo when needed."
    exit 1
fi

# Update package lists
echo "📦 Updating package lists..."
sudo apt update

# Install Bluetooth tools
echo "🔵 Installing Bluetooth tools..."
if ! command -v bluetoothctl &> /dev/null; then
    sudo apt install -y bluetooth bluez-tools
fi

# Install network tools
echo "🌐 Installing network tools..."
if ! command -v arp-scan &> /dev/null; then
    sudo apt install -y arp-scan
fi

if ! command -v nmap &> /dev/null; then
    sudo apt install -y nmap
fi

if ! command -v ip &> /dev/null; then
    sudo apt install -y iproute2
fi

# Add user to required groups
echo "👤 Adding user to required groups..."
sudo usermod -a -G bluetooth $USER

if getent group netdev > /dev/null 2>&1; then
    sudo usermod -a -G netdev $USER
fi

# Install systemd services
echo "📁 Installing systemd services..."
sudo cp marina-bluetooth-monitor.service /etc/systemd/system/
sudo cp marina-network-monitor.service /etc/systemd/system/

# Reload systemd and enable services
echo "🔄 Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable marina-bluetooth-monitor.service
sudo systemctl enable marina-network-monitor.service

# Test the scripts
echo "🧪 Testing monitor scripts..."
echo "Testing Bluetooth monitor..."
python3 bluetooth_monitor.py --test

echo "Testing network monitor..."
python3 network_monitor.py --test

echo "✅ Installation complete!"
echo ""
echo "🔵 Bluetooth Monitor Commands:"
echo "  sudo systemctl start marina-bluetooth-monitor"
echo "  sudo systemctl status marina-bluetooth-monitor"
echo "  sudo journalctl -u marina-bluetooth-monitor -f"
echo ""
echo "🌐 Network Monitor Commands:"
echo "  sudo systemctl start marina-network-monitor"
echo "  sudo systemctl status marina-network-monitor"
echo "  sudo journalctl -u marina-network-monitor -f"
echo ""
echo "🚀 Start both monitors:"
echo "  sudo systemctl start marina-bluetooth-monitor marina-network-monitor"
echo ""
echo "🛑 Stop both monitors:"
echo "  sudo systemctl stop marina-bluetooth-monitor marina-network-monitor"
echo ""
echo "📊 Check status of both:"
echo "  sudo systemctl status marina-bluetooth-monitor marina-network-monitor"
echo ""
echo "⚠️  You may need to log out and back in for group changes to take effect."
