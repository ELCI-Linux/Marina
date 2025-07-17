#!/usr/bin/env python3
"""
Network Device Monitor for Marina Agentic Intelligence Framework

This script monitors network devices/connections and sends
new device information to the Marina brain system for processing.
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

class NetworkMonitor:
    def __init__(self, scan_interval=20):
        self.scan_interval = scan_interval
        self.known_devices: Set[str] = set()
        self.device_history: List[Dict] = []
        self.running = False
        
        # Initialize known devices with current scan
        self._initialize_known_devices()
    
    def _initialize_known_devices(self):
        """Initialize the known devices set with current network connections"""
        print("🔍 Initializing known network devices...")
        current_devices = self._scan_network_devices()
        self.known_devices = {dev['ip'] for dev in current_devices}
        print(f"✅ Initialized with {len(self.known_devices)} known devices")
    
    def _scan_network_devices(self) -> List[Dict]:
        """Scan for available network devices using multiple methods"""
        devices = []
        
        # Method 1: ARP scan (preferred)
        devices.extend(self._arp_scan())
        
        # Method 2: Nmap scan (fallback)
        if not devices:
            devices.extend(self._nmap_scan())
        
        # Method 3: ARP table scan (fallback)
        if not devices:
            devices.extend(self._arp_table_scan())
        
        # Remove duplicates based on IP
        unique_devices = []
        seen_ips = set()
        for device in devices:
            if device['ip'] not in seen_ips:
                unique_devices.append(device)
                seen_ips.add(device['ip'])
        
        return unique_devices
    
    def _arp_scan(self) -> List[Dict]:
        """Scan using arp-scan command"""
        devices = []
        
        try:
            result = subprocess.run(['arp-scan', '--localnet'], 
                                  capture_output=True, text=True, timeout=20)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Skip header and footer lines
                for line in lines[2:-4]:
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        ip = parts[0].strip()
                        mac = parts[1].strip()
                        name = parts[2].strip()
                        
                        devices.append({
                            'ip': ip,
                            'mac': mac,
                            'name': name,
                            'timestamp': datetime.now().isoformat(),
                            'method': 'arp-scan'
                        })
        except subprocess.TimeoutExpired:
            print("⚠️  ARP scan timed out")
        except FileNotFoundError:
            print("⚠️  arp-scan not found, trying alternative methods")
        except Exception as e:
            print(f"⚠️  ARP scan error: {e}")
        
        return devices
    
    def _nmap_scan(self) -> List[Dict]:
        """Scan using nmap command"""
        devices = []
        
        try:
            # Get network range
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Extract network interface
                lines = result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split()
                    if 'dev' in parts:
                        dev_index = parts.index('dev')
                        if dev_index + 1 < len(parts):
                            interface = parts[dev_index + 1]
                            
                            # Get network range for interface
                            result = subprocess.run(['ip', 'addr', 'show', interface], 
                                                  capture_output=True, text=True, timeout=10)
                            
                            if result.returncode == 0:
                                lines = result.stdout.split('\n')
                                for line in lines:
                                    if 'inet ' in line and not '127.0.0.1' in line:
                                        parts = line.strip().split()
                                        if len(parts) >= 2:
                                            network = parts[1]
                                            
                                            # Run nmap scan
                                            result = subprocess.run(['nmap', '-sn', network], 
                                                                  capture_output=True, text=True, timeout=30)
                                            
                                            if result.returncode == 0:
                                                lines = result.stdout.split('\n')
                                                current_ip = None
                                                for line in lines:
                                                    if 'Nmap scan report for' in line:
                                                        parts = line.split()
                                                        if len(parts) >= 5:
                                                            current_ip = parts[4]
                                                    elif 'MAC Address:' in line and current_ip:
                                                        parts = line.split()
                                                        if len(parts) >= 3:
                                                            mac = parts[2]
                                                            name = ' '.join(parts[3:]).strip('()')
                                                            
                                                            devices.append({
                                                                'ip': current_ip,
                                                                'mac': mac,
                                                                'name': name,
                                                                'timestamp': datetime.now().isoformat(),
                                                                'method': 'nmap'
                                                            })
                                                            current_ip = None
                                                break
        except subprocess.TimeoutExpired:
            print("⚠️  Nmap scan timed out")
        except FileNotFoundError:
            print("⚠️  nmap not found")
        except Exception as e:
            print(f"⚠️  Nmap scan error: {e}")
        
        return devices
    
    def _arp_table_scan(self) -> List[Dict]:
        """Scan using system ARP table"""
        devices = []
        
        try:
            result = subprocess.run(['arp', '-a'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        # Parse line like: hostname (192.168.1.1) at aa:bb:cc:dd:ee:ff [ether] on eth0
                        parts = line.split()
                        if len(parts) >= 4:
                            name = parts[0] if parts[0] != '?' else 'Unknown'
                            ip_part = parts[1]
                            if ip_part.startswith('(') and ip_part.endswith(')'):
                                ip = ip_part[1:-1]
                                
                                # Find MAC address
                                mac = 'Unknown'
                                for part in parts:
                                    if ':' in part and len(part) == 17:
                                        mac = part
                                        break
                                
                                devices.append({
                                    'ip': ip,
                                    'mac': mac,
                                    'name': name,
                                    'timestamp': datetime.now().isoformat(),
                                    'method': 'arp-table'
                                })
        except subprocess.TimeoutExpired:
            print("⚠️  ARP table scan timed out")
        except Exception as e:
            print(f"⚠️  ARP table scan error: {e}")
        
        return devices
    
    def _send_to_brain(self, device_data: Dict):
        """Send new device information to Marina's brain system"""
        if not MARINA_AVAILABLE:
            print("📤 Marina brain system not available - logging device data locally")
            self._log_device_locally(device_data)
            return
        
        try:
            # Prepare the prompt for Marina's brain
            prompt = f"""NEW NETWORK DEVICE DETECTED - PROMPT n+1

Device Information:
- IP Address: {device_data['ip']}
- MAC Address: {device_data['mac']}
- Device Name: {device_data['name']}
- Detection Time: {device_data['timestamp']}

Context: This is a new network device that has appeared in the local network. This could indicate:
1. A new device connecting to the network
2. A device changing IP address
3. A potential unauthorized access

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
        log_file = "network_devices.log"
        
        try:
            with open(log_file, 'a') as f:
                f.write(f"{json.dumps(device_data)}\\n")
            print(f"📝 Device logged to {log_file}")
        except Exception as e:
            print(f"❌ Error logging device: {e}")
    
    def _log_interaction(self, device_data: Dict, model: str, response: str):
        """Log the interaction with Marina's brain system"""
        interaction_log = "marina_network_interactions.log"
        
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
        """Check for new network devices and process them"""
        print("🔍 Scanning for network devices...")
        
        current_devices = self._scan_network_devices()
        new_devices = []
        
        for device in current_devices:
            if device['ip'] not in self.known_devices:
                new_devices.append(device)
                self.known_devices.add(device['ip'])
                self.device_history.append(device)
        
        if new_devices:
            print(f"🆕 Found {len(new_devices)} new device(s)")
            
            for device in new_devices:
                print(f"🌐 New device: {device['name']} ({device['ip']})")
                self._send_to_brain(device)
        else:
            print("✅ No new devices detected")
    
    def start_monitoring(self):
        """Start the continuous monitoring loop"""
        self.running = True
        print(f"🚀 Starting network monitoring (interval: {self.scan_interval}s)")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while self.running:
                self._check_for_new_devices()
                
                print(f"⏳ Waiting {self.scan_interval} seconds...")
                time.sleep(self.scan_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            self.running = False
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            self.running = False
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        print("🛑 Stopping network monitoring")
    
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
    """Main entry point for the network monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Network Device Monitor for Marina')
    parser.add_argument('--interval', type=int, default=20, 
                       help='Scan interval in seconds (default: 20)')
    parser.add_argument('--status', action='store_true',
                       help='Show current status and exit')
    parser.add_argument('--test', action='store_true',
                       help='Run a single scan test and exit')
    
    args = parser.parse_args()
    
    monitor = NetworkMonitor(scan_interval=args.interval)
    
    if args.status:
        status = monitor.get_status()
        print("📊 Network Monitor Status:")
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
