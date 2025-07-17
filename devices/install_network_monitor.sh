#!/bin/bash
# Installation script for Marina Network Monitor

set -e

echo "🚀 Installing Marina Network Monitor..."

# Check if running as root for system service installation
if [[ $EUID -eq 0 ]]; then
    echo "❌ Don't run this script as root. It will prompt for sudo when needed."
    exit 1
fi

# Check if network tools are available and install if needed
echo "🔧 Checking network tools..."

# Check for arp-scan
if ! command -v arp-scan &> /dev/null; then
    echo "📦 Installing arp-scan..."
    sudo apt update
    sudo apt install -y arp-scan
fi

# Check for nmap
if ! command -v nmap &> /dev/null; then
    echo "📦 Installing nmap..."
    sudo apt update
    sudo apt install -y nmap
fi

# Check for ip command (usually pre-installed)
if ! command -v ip &> /dev/null; then
    echo "📦 Installing iproute2..."
    sudo apt update
    sudo apt install -y iproute2
fi

# Add user to netdev group (if it exists)
if getent group netdev > /dev/null 2>&1; then
    echo "👤 Adding user to netdev group..."
    sudo usermod -a -G netdev $USER
fi

# Copy service file to systemd directory
echo "📁 Installing systemd service..."
sudo cp marina-network-monitor.service /etc/systemd/system/

# Reload systemd and enable the service
echo "🔄 Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable marina-network-monitor.service

# Test the script
echo "🧪 Testing network monitor script..."
python3 network_monitor.py --test

echo "✅ Installation complete!"
echo ""
echo "To start the service:"
echo "  sudo systemctl start marina-network-monitor"
echo ""
echo "To check status:"
echo "  sudo systemctl status marina-network-monitor"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u marina-network-monitor -f"
echo ""
echo "To stop the service:"
echo "  sudo systemctl stop marina-network-monitor"
echo ""
echo "⚠️  You may need to log out and back in for group changes to take effect."
