#!/usr/bin/env python3
"""
Bluetooth Device Monitor for Marina Agentic Intelligence Framework

This script monitors for new Bluetooth devices every 20 seconds and sends
device information to the Marina brain system for processing.
"""

import subprocess
import time
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Set

# Add Marina's root directory to Python path for imports
MARINA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, MARINA_ROOT)

try:
    from llm import llm_router
    from brain import prime
    MARINA_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Marina modules not available: {e}")
    MARINA_AVAILABLE = False

class BluetoothMonitor:
    def __init__(self, scan_interval=20):
        self.scan_interval = scan_interval
        self.known_devices: Set[str] = set()
        self.device_history: List[Dict] = []
        self.running = False
        
        # Initialize known devices with current scan
        self._initialize_known_devices()
    
    def _initialize_known_devices(self):
        """Initialize the known devices set with current Bluetooth devices"""
        print("🔍 Initializing known Bluetooth devices...")
        current_devices = self._scan_bluetooth_devices()
        self.known_devices = {dev['address'] for dev in current_devices}
        print(f"✅ Initialized with {len(self.known_devices)} known devices")
    
    def _scan_bluetooth_devices(self) -> List[Dict]:
        """Scan for available Bluetooth devices using bluetoothctl"""
        devices = []
        
        try:
            # Start bluetooth service if not running
            subprocess.run(['sudo', 'systemctl', 'start', 'bluetooth'], 
                         capture_output=True, check=False)
            
            # Enable bluetooth adapter
            result = subprocess.run(['bluetoothctl', 'power', 'on'], 
                                  capture_output=True, text=True, timeout=10)
            
            # Start scanning
            subprocess.run(['bluetoothctl', 'scan', 'on'], 
                         capture_output=True, text=True, timeout=5)
            
            # Wait for scan to populate
            time.sleep(3)
            
            # Get list of devices
            result = subprocess.run(['bluetoothctl', 'devices'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('Device '):
                        parts = line.split(' ', 2)
                        if len(parts) >= 3:
                            address = parts[1]
                            name = parts[2] if len(parts) > 2 else "Unknown"
                            
                            # Get additional device info
                            device_info = self._get_device_info(address)
                            
                            devices.append({
                                'address': address,
                                'name': name,
                                'timestamp': datetime.now().isoformat(),
                                'info': device_info
                            })
            
            # Stop scanning to save power
            subprocess.run(['bluetoothctl', 'scan', 'off'], 
                         capture_output=True, text=True, timeout=5)
                         
        except subprocess.TimeoutExpired:
            print("⚠️  Bluetooth scan timed out")
        except Exception as e:
            print(f"❌ Error scanning Bluetooth devices: {e}")
        
        return devices
    
    def _get_device_info(self, address: str) -> Dict:
        """Get detailed information about a specific Bluetooth device"""
        info = {}
        
        try:
            result = subprocess.run(['bluetoothctl', 'info', address], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️  Could not get info for device {address}: {e}")
        
        return info
    
    def _send_to_brain(self, device_data: Dict):
        """Send new device information to Marina's brain system"""
        if not MARINA_AVAILABLE:
            print("📤 Marina brain system not available - logging device data locally")
            self._log_device_locally(device_data)
            return
        
        try:
            # Prepare the prompt for Marina's brain
            prompt = f"""NEW BLUETOOTH DEVICE DETECTED - PROMPT n+1

Device Information:
- Address: {device_data['address']}
- Name: {device_data['name']}
- Detection Time: {device_data['timestamp']}
- Device Details: {json.dumps(device_data['info'], indent=2)}

Context: This is a new Bluetooth device that has appeared in the vicinity. This could indicate:
1. A new person/device entering the area
2. A device that was previously turned off being activated
3. A device that moved within range

Please analyze this device information and determine if any action should be taken based on Marina's current objectives and security protocols."""

            # Send to Marina's LLM router for processing
            model, response = llm_router.route_task(
                prompt,
                tokens=800,
                run=True
            )
            
            print(f"🧠 Sent device info to Marina brain via {model}")
            if response:
                print(f"📝 Marina's analysis: {response[:200]}...")
                
                # Log the interaction
                self._log_interaction(device_data, model, response)
        
        except Exception as e:
            print(f"❌ Error sending to Marina brain: {e}")
            self._log_device_locally(device_data)
    
    def _log_device_locally(self, device_data: Dict):
        """Log device data locally if Marina brain is not available"""
        log_file = "bluetooth_devices.log"
        
        try:
            with open(log_file, 'a') as f:
                f.write(f"{json.dumps(device_data)}\\n")
            print(f"📝 Device logged to {log_file}")
        except Exception as e:
            print(f"❌ Error logging device: {e}")
    
    def _log_interaction(self, device_data: Dict, model: str, response: str):
        """Log the interaction with Marina's brain system"""
        interaction_log = "marina_bluetooth_interactions.log"
        
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'device': device_data,
            'model_used': model,
            'marina_response': response
        }
        
        try:
            with open(interaction_log, 'a') as f:
                f.write(f"{json.dumps(interaction)}\\n")
        except Exception as e:
            print(f"❌ Error logging interaction: {e}")
    
    def _check_for_new_devices(self):
        """Check for new Bluetooth devices and process them"""
        print("🔍 Scanning for Bluetooth devices...")
        
        current_devices = self._scan_bluetooth_devices()
        new_devices = []
        
        for device in current_devices:
            if device['address'] not in self.known_devices:
                new_devices.append(device)
                self.known_devices.add(device['address'])
                self.device_history.append(device)
        
        if new_devices:
            print(f"🆕 Found {len(new_devices)} new device(s)")
            
            for device in new_devices:
                print(f"📱 New device: {device['name']} ({device['address']})")
                self._send_to_brain(device)
        else:
            print("✅ No new devices detected")
    
    def start_monitoring(self):
        """Start the continuous monitoring loop"""
        self.running = True
        print(f"🚀 Starting Bluetooth monitoring (interval: {self.scan_interval}s)")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while self.running:
                self._check_for_new_devices()
                
                print(f"⏳ Waiting {self.scan_interval} seconds...")
                time.sleep(self.scan_interval)
                
        except KeyboardInterrupt:
            print("\\n🛑 Monitoring stopped by user")
            self.running = False
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            self.running = False
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        print("🛑 Stopping Bluetooth monitoring")
    
    def get_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'running': self.running,
            'known_devices': len(self.known_devices),
            'devices_detected': len(self.device_history),
            'scan_interval': self.scan_interval,
            'marina_available': MARINA_AVAILABLE
        }


def main():
    """Main entry point for the Bluetooth monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bluetooth Device Monitor for Marina')
    parser.add_argument('--interval', type=int, default=20, 
                       help='Scan interval in seconds (default: 20)')
    parser.add_argument('--status', action='store_true',
                       help='Show current status and exit')
    parser.add_argument('--test', action='store_true',
                       help='Run a single scan test and exit')
    
    args = parser.parse_args()
    
    monitor = BluetoothMonitor(scan_interval=args.interval)
    
    if args.status:
        status = monitor.get_status()
        print("📊 Bluetooth Monitor Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        return
    
    if args.test:
        print("🧪 Running test scan...")
        monitor._check_for_new_devices()
        return
    
    # Start continuous monitoring
    monitor.start_monitoring()


if __name__ == "__main__":
    main()
