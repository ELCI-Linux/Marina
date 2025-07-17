# Marina Device Monitors

A comprehensive device monitoring system integrated with the Marina Agentic Intelligence Framework. This system includes both Bluetooth and Network device monitors that continuously scan for new devices every 20 seconds and send device information to Marina's brain system for intelligent analysis and response.

## Features

- 🔍 **Continuous Monitoring**: Scans for new Bluetooth and network devices every 20 seconds
- 🧠 **Marina Integration**: Sends device data to Marina's brain system via LLM router
- 📱 **Device Intelligence**: Collects detailed device information including capabilities and services
- 🔄 **Automatic Recovery**: Handles Bluetooth/network errors and service interruptions gracefully
- 📊 **Comprehensive Logging**: Logs all device detections and Marina interactions
- 🛡️ **Security Aware**: Considers security implications of new device detections
- 🚀 **Systemd Service**: Can run as a system daemon for continuous operation
- 🌐 **Multiple Scan Methods**: Uses ARP scan, nmap, and ARP table for network discovery

## Files

### Bluetooth Monitor
- `bluetooth_monitor.py` - Bluetooth device monitoring script
- `marina-bluetooth-monitor.service` - Systemd service file for Bluetooth monitor
- `install_bluetooth_monitor.sh` - Installation script for Bluetooth monitor

### Network Monitor
- `network_monitor.py` - Network device monitoring script
- `marina-network-monitor.service` - Systemd service file for network monitor
- `install_network_monitor.sh` - Installation script for network monitor

### Combined
- `install_all_monitors.sh` - Installation script for both monitors
- `README.md` - This documentation

## Installation

### Install Both Monitors (Recommended)
```bash
./install_all_monitors.sh
```

### Install Individual Monitors

**Bluetooth Monitor:**
```bash
./install_bluetooth_monitor.sh
```

**Network Monitor:**
```bash
./install_network_monitor.sh
```

The installation scripts will:
- Install required tools (Bluetooth tools, arp-scan, nmap)
- Add your user to appropriate groups
- Install systemd services
- Test the monitors

**Note:** Log out and back in for group changes to take effect

## Usage

### Manual Testing

**Bluetooth Monitor:**
```bash
python3 bluetooth_monitor.py --test
python3 bluetooth_monitor.py --status
python3 bluetooth_monitor.py --interval 30
```

**Network Monitor:**
```bash
python3 network_monitor.py --test
python3 network_monitor.py --status
python3 network_monitor.py --interval 30
```

### System Services

**Start both monitors:**
```bash
sudo systemctl start marina-bluetooth-monitor marina-network-monitor
```

**Check status:**
```bash
sudo systemctl status marina-bluetooth-monitor marina-network-monitor
```

**View logs:**
```bash
sudo journalctl -u marina-bluetooth-monitor -f
sudo journalctl -u marina-network-monitor -f
```

**Stop services:**
```bash
sudo systemctl stop marina-bluetooth-monitor marina-network-monitor
```

## Integration with Marina

The monitor integrates with Marina's brain system by:

1. **Device Detection**: When a new Bluetooth device is detected, it collects:
   - Device MAC address
   - Device name
   - Detection timestamp
   - Detailed device information (services, capabilities, etc.)

2. **Brain Processing**: The device information is sent to Marina's LLM router as a structured prompt containing:
   - Device details
   - Security context
   - Suggested analysis points

3. **Intelligent Response**: Marina's brain system analyzes the device and can:
   - Assess potential security implications
   - Determine if action is needed
   - Log the device in Marina's memory system
   - Trigger other Marina subsystems if appropriate

## Output Files

### Bluetooth Monitor
- `bluetooth_devices.log` - Raw Bluetooth device detection log (fallback when Marina unavailable)
- `marina_bluetooth_interactions.log` - Complete log of Marina brain interactions for Bluetooth devices

### Network Monitor
- `network_devices.log` - Raw network device detection log (fallback when Marina unavailable)
- `marina_network_interactions.log` - Complete log of Marina brain interactions for network devices

## Requirements

- Linux system with network interface and optionally Bluetooth support
- Python 3.6+
- **Bluetooth Monitor**: `bluetoothctl` (bluez-tools package)
- **Network Monitor**: `arp-scan`, `nmap`, `ip` command (iproute2 package)
- Marina Agentic Intelligence Framework
- Systemd (for service mode)

## Security Considerations

The monitor is designed with security in mind:

- **Privilege Separation**: Runs as regular user, not root
- **Group Permissions**: Uses bluetooth group for device access
- **Error Handling**: Graceful handling of Bluetooth failures
- **Logging**: All activities are logged for audit purposes
- **Marina Integration**: Leverages Marina's security protocols

## Troubleshooting

### Bluetooth Service Issues
```bash
sudo systemctl start bluetooth
sudo systemctl enable bluetooth
```

### Permission Issues
```bash
sudo usermod -a -G bluetooth $USER
# Log out and back in
```

### Marina Import Issues
- Ensure Marina is properly installed in the parent directory
- Check that the PYTHONPATH includes Marina's root directory

### Service Not Starting
```bash
sudo systemctl daemon-reload
sudo systemctl enable marina-bluetooth-monitor
```

## Customization

### Scan Interval
Change the scan interval by modifying the service file or using command line arguments:
```bash
python3 bluetooth_monitor.py --interval 10  # 10 second intervals
```

### Marina Prompt Customization
Edit the `_send_to_brain()` method in `bluetooth_monitor.py` to customize how device information is presented to Marina's brain system.

## Example Output

```
🚀 Starting Bluetooth monitoring (interval: 20s)
🔍 Initializing known Bluetooth devices...
✅ Initialized with 3 known devices
🔍 Scanning for Bluetooth devices...
🆕 Found 1 new device(s)
📱 New device: John's iPhone (AA:BB:CC:DD:EE:FF)
🧠 Sent device info to Marina brain via gpt-4o
📝 Marina's analysis: This appears to be a personal mobile device. Based on naming convention and device type, this likely belongs to...
```

## License

This script is part of the Marina Agentic Intelligence Framework and follows the same licensing terms.
