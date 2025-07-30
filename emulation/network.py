"""
Marina Network Emulator
=======================

Emulates various network conditions, protocols, and interfaces for testing
network-dependent applications and services. Supports WiFi, cellular, 
Bluetooth, and wired connections with configurable parameters.
"""

import asyncio
import logging
import json
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class NetworkType(Enum):
    """Types of network interfaces"""
    WIFI = "wifi"
    CELLULAR = "cellular"
    ETHERNET = "ethernet"
    BLUETOOTH = "bluetooth"
    LOOPBACK = "loopback"

class NetworkState(Enum):
    """Network connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"

@dataclass
class NetworkProfile:
    """Network interface profile"""
    interface_name: str
    network_type: NetworkType
    bandwidth_mbps: float
    latency_ms: int
    packet_loss_percent: float
    jitter_ms: int
    is_enabled: bool = True
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}

class EmulatedNetworkInterface:
    """Emulated network interface"""
    
    def __init__(self, profile: NetworkProfile):
        self.profile = profile
        self.interface_name = profile.interface_name
        self.network_type = profile.network_type
        self.state = NetworkState.DISCONNECTED
        
        # Network parameters
        self.bandwidth_mbps = profile.bandwidth_mbps
        self.latency_ms = profile.latency_ms
        self.packet_loss_percent = profile.packet_loss_percent
        self.jitter_ms = profile.jitter_ms
        
        # Current statistics
        self.bytes_sent = 0
        self.bytes_received = 0
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_dropped = 0
        self.connection_time = 0
        self.signal_strength = 0  # dBm
        
        # Connection details
        self.ip_address = ""
        self.subnet_mask = ""
        self.gateway = ""
        self.dns_servers = []
        
        self.is_running = False
        
    async def start(self):
        """Start network interface emulation"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info(f"Started network interface: {self.interface_name} ({self.network_type.value})")
        
        # Start background monitoring
        asyncio.create_task(self._simulate_network_behavior())
        
    async def stop(self):
        """Stop network interface emulation"""
        self.is_running = False
        self.state = NetworkState.DISCONNECTED
        logger.info(f"Stopped network interface: {self.interface_name}")
        
    async def connect(self, network_name: str = "Default Network") -> bool:
        """Connect to a network"""
        if self.state != NetworkState.DISCONNECTED:
            return False
            
        self.state = NetworkState.CONNECTING
        logger.info(f"Connecting {self.interface_name} to {network_name}")
        
        # Simulate connection process
        await asyncio.sleep(random.uniform(1, 3))
        
        # Simulate connection success/failure
        if random.random() > 0.1:  # 90% success rate
            self.state = NetworkState.CONNECTED
            self.connection_time = time.time()
            self._assign_network_config()
            
            # Set signal strength based on network type
            if self.network_type == NetworkType.WIFI:
                self.signal_strength = random.randint(-70, -30)
            elif self.network_type == NetworkType.CELLULAR:
                self.signal_strength = random.randint(-110, -60)
            else:
                self.signal_strength = 0
                
            logger.info(f"Connected {self.interface_name} to {network_name}")
            return True
        else:
            self.state = NetworkState.ERROR
            logger.error(f"Failed to connect {self.interface_name} to {network_name}")
            return False
            
    async def disconnect(self):
        """Disconnect from network"""
        if self.state != NetworkState.CONNECTED:
            return
            
        self.state = NetworkState.DISCONNECTING
        logger.info(f"Disconnecting {self.interface_name}")
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        self.state = NetworkState.DISCONNECTED
        self.connection_time = 0
        self.signal_strength = 0
        self._clear_network_config()
        
        logger.info(f"Disconnected {self.interface_name}")
        
    def _assign_network_config(self):
        """Assign network configuration"""
        if self.network_type == NetworkType.LOOPBACK:
            self.ip_address = "127.0.0.1"
            self.subnet_mask = "255.0.0.0"
            self.gateway = ""
            self.dns_servers = []
        else:
            # Generate realistic network config
            base_ip = random.randint(1, 254)
            self.ip_address = f"192.168.1.{base_ip}"
            self.subnet_mask = "255.255.255.0"
            self.gateway = "192.168.1.1"
            self.dns_servers = ["8.8.8.8", "8.8.4.4"]
            
    def _clear_network_config(self):
        """Clear network configuration"""
        self.ip_address = ""
        self.subnet_mask = ""
        self.gateway = ""
        self.dns_servers = []
        
    async def _simulate_network_behavior(self):
        """Simulate network behavior and statistics"""
        while self.is_running:
            try:
                if self.state == NetworkState.CONNECTED:
                    # Simulate network traffic
                    sent_bytes = random.randint(100, 5000)
                    received_bytes = random.randint(500, 10000)
                    
                    self.bytes_sent += sent_bytes
                    self.bytes_received += received_bytes
                    self.packets_sent += random.randint(1, 10)
                    self.packets_received += random.randint(5, 20)
                    
                    # Simulate packet loss
                    if random.random() < (self.packet_loss_percent / 100):
                        self.packets_dropped += random.randint(1, 3)
                    
                    # Vary signal strength slightly
                    if self.signal_strength != 0:
                        variation = random.randint(-5, 5)
                        self.signal_strength = max(-120, min(-20, self.signal_strength + variation))
                        
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
                
    def send_packet(self, destination: str, data: bytes) -> bool:
        """Simulate sending a network packet"""
        if self.state != NetworkState.CONNECTED:
            return False
            
        # Simulate network delay
        actual_latency = self.latency_ms + random.randint(-self.jitter_ms, self.jitter_ms)
        
        # Simulate packet loss
        if random.random() < (self.packet_loss_percent / 100):
            self.packets_dropped += 1
            logger.debug(f"Packet dropped to {destination}")
            return False
            
        self.bytes_sent += len(data)
        self.packets_sent += 1
        
        logger.debug(f"Sent packet to {destination}: {len(data)} bytes, latency: {actual_latency}ms")
        return True
        
    def get_status(self) -> Dict[str, Any]:
        """Get network interface status"""
        uptime = time.time() - self.connection_time if self.connection_time > 0 else 0
        
        return {
            "interface_name": self.interface_name,
            "network_type": self.network_type.value,
            "state": self.state.value,
            "bandwidth_mbps": self.bandwidth_mbps,
            "latency_ms": self.latency_ms,
            "packet_loss_percent": self.packet_loss_percent,
            "jitter_ms": self.jitter_ms,
            "signal_strength_dbm": self.signal_strength,
            "ip_address": self.ip_address,
            "subnet_mask": self.subnet_mask,
            "gateway": self.gateway,
            "dns_servers": self.dns_servers,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "packets_dropped": self.packets_dropped,
            "uptime_seconds": uptime,
            "is_running": self.is_running
        }

class NetworkEmulator:
    """Main network emulator managing multiple network interfaces"""
    
    def __init__(self):
        self.interfaces: Dict[str, EmulatedNetworkInterface] = {}
        self.network_profiles = self._create_default_profiles()
        self.is_running = False
        
    def _create_default_profiles(self) -> Dict[str, NetworkProfile]:
        """Create default network profiles"""
        profiles = {}
        
        # WiFi profiles
        profiles["wifi_high_speed"] = NetworkProfile(
            interface_name="wlan0",
            network_type=NetworkType.WIFI,
            bandwidth_mbps=100.0,
            latency_ms=10,
            packet_loss_percent=0.1,
            jitter_ms=2,
            properties={"frequency": "5GHz", "encryption": "WPA3"}
        )
        
        profiles["wifi_standard"] = NetworkProfile(
            interface_name="wlan0",
            network_type=NetworkType.WIFI,
            bandwidth_mbps=25.0,
            latency_ms=20,
            packet_loss_percent=0.5,
            jitter_ms=5,
            properties={"frequency": "2.4GHz", "encryption": "WPA2"}
        )
        
        profiles["wifi_poor"] = NetworkProfile(
            interface_name="wlan0",
            network_type=NetworkType.WIFI,
            bandwidth_mbps=5.0,
            latency_ms=100,
            packet_loss_percent=2.0,
            jitter_ms=20,
            properties={"frequency": "2.4GHz", "encryption": "WPA2"}
        )
        
        # Cellular profiles
        profiles["cellular_5g"] = NetworkProfile(
            interface_name="cellular0",
            network_type=NetworkType.CELLULAR,
            bandwidth_mbps=200.0,
            latency_ms=15,
            packet_loss_percent=0.2,
            jitter_ms=3,
            properties={"technology": "5G", "carrier": "Generic Carrier"}
        )
        
        profiles["cellular_4g"] = NetworkProfile(
            interface_name="cellular0",
            network_type=NetworkType.CELLULAR,
            bandwidth_mbps=50.0,
            latency_ms=30,
            packet_loss_percent=0.8,
            jitter_ms=10,
            properties={"technology": "LTE", "carrier": "Generic Carrier"}
        )
        
        profiles["cellular_3g"] = NetworkProfile(
            interface_name="cellular0",
            network_type=NetworkType.CELLULAR,
            bandwidth_mbps=2.0,
            latency_ms=200,
            packet_loss_percent=3.0,
            jitter_ms=50,
            properties={"technology": "3G", "carrier": "Generic Carrier"}
        )
        
        # Ethernet profile
        profiles["ethernet_gigabit"] = NetworkProfile(
            interface_name="eth0",
            network_type=NetworkType.ETHERNET,
            bandwidth_mbps=1000.0,
            latency_ms=1,
            packet_loss_percent=0.01,
            jitter_ms=0,
            properties={"speed": "1Gbps", "duplex": "full"}
        )
        
        # Bluetooth profile
        profiles["bluetooth"] = NetworkProfile(
            interface_name="bt0",
            network_type=NetworkType.BLUETOOTH,
            bandwidth_mbps=2.0,
            latency_ms=50,
            packet_loss_percent=1.0,
            jitter_ms=10,
            properties={"version": "5.0", "range_meters": 10}
        )
        
        # Loopback profile
        profiles["loopback"] = NetworkProfile(
            interface_name="lo",
            network_type=NetworkType.LOOPBACK,
            bandwidth_mbps=10000.0,  # Very high for local connections
            latency_ms=0,
            packet_loss_percent=0.0,
            jitter_ms=0,
            properties={"local_only": True}
        )
        
        return profiles
        
    async def create_interface(self, profile_name: str, interface_name: str = None) -> Optional[str]:
        """Create a new network interface"""
        if profile_name not in self.network_profiles:
            logger.error(f"Network profile '{profile_name}' not found")
            return None
            
        profile = self.network_profiles[profile_name]
        
        # Use custom interface name if provided
        if interface_name:
            profile.interface_name = interface_name
            
        interface = EmulatedNetworkInterface(profile)
        self.interfaces[profile.interface_name] = interface
        
        logger.info(f"Created network interface: {profile.interface_name} ({profile.network_type.value})")
        return profile.interface_name
        
    async def start_emulation(self, config) -> bool:
        """Start network emulation based on configuration"""
        try:
            if not config.network_enabled:
                logger.info("Network emulation disabled in configuration")
                return True
                
            self.is_running = True
            
            # Create default interfaces based on target platform
            if config.target_platform == "android":
                await self.create_interface("wifi_standard")
                await self.create_interface("cellular_4g")
                await self.create_interface("bluetooth")
            elif config.target_platform == "ios":
                await self.create_interface("wifi_high_speed")
                await self.create_interface("cellular_5g")  
                await self.create_interface("bluetooth")
            elif config.target_platform in ["windows", "macos", "linux"]:
                await self.create_interface("ethernet_gigabit")
                await self.create_interface("wifi_standard")
                await self.create_interface("bluetooth")
            else:
                # Default configuration
                await self.create_interface("wifi_standard")
                
            # Always create loopback interface
            await self.create_interface("loopback")
            
            # Start all interfaces
            for interface in self.interfaces.values():
                await interface.start()
                
            # Auto-connect loopback
            loopback = self.interfaces.get("lo")
            if loopback:
                await loopback.connect("Loopback")
                
            logger.info("Network emulation started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start network emulation: {e}")
            return False
            
    async def stop_emulation(self, session_id: str) -> bool:
        """Stop network emulation for a session"""
        try:
            logger.info("Stopping network emulation")
            
            # Stop all interfaces
            for interface in self.interfaces.values():
                await interface.disconnect()
                await interface.stop()
                
            self.interfaces.clear()
            self.is_running = False
            
            logger.info("Network emulation stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop network emulation: {e}")
            return False
            
    def get_interface(self, interface_name: str) -> Optional[EmulatedNetworkInterface]:
        """Get network interface by name"""
        return self.interfaces.get(interface_name)
        
    def list_interfaces(self) -> List[str]:
        """List all network interface names"""
        return list(self.interfaces.keys())
        
    def list_available_profiles(self) -> List[str]:
        """List all available network profiles"""
        return list(self.network_profiles.keys())
        
    async def connect_interface(self, interface_name: str, network_name: str = "Default Network") -> bool:
        """Connect a network interface"""
        interface = self.interfaces.get(interface_name)
        if interface:
            return await interface.connect(network_name)
        return False
        
    async def disconnect_interface(self, interface_name: str) -> bool:
        """Disconnect a network interface"""
        interface = self.interfaces.get(interface_name)
        if interface:
            await interface.disconnect()
            return True
        return False
        
    def set_network_conditions(self, interface_name: str, **conditions) -> bool:
        """Set network conditions for an interface"""
        interface = self.interfaces.get(interface_name)
        if not interface:
            return False
            
        # Update network parameters
        if "bandwidth_mbps" in conditions:
            interface.bandwidth_mbps = conditions["bandwidth_mbps"]
            
        if "latency_ms" in conditions:
            interface.latency_ms = conditions["latency_ms"]
            
        if "packet_loss_percent" in conditions:
            interface.packet_loss_percent = conditions["packet_loss_percent"]
            
        if "jitter_ms" in conditions:
            interface.jitter_ms = conditions["jitter_ms"]
            
        logger.info(f"Updated network conditions for {interface_name}: {conditions}")
        return True
        
    def simulate_network_outage(self, interface_name: str, duration_seconds: int):
        """Simulate a network outage"""
        async def outage():
            interface = self.interfaces.get(interface_name)
            if interface and interface.state == NetworkState.CONNECTED:
                logger.info(f"Simulating network outage on {interface_name} for {duration_seconds}s")
                
                # Disconnect interface
                await interface.disconnect()
                
                # Wait for outage duration
                await asyncio.sleep(duration_seconds)
                
                # Reconnect interface
                await interface.connect("Network (Restored)")
                logger.info(f"Network outage ended on {interface_name}")
                
        asyncio.create_task(outage())
        
    def get_network_status(self) -> Dict[str, Any]:
        """Get overall network status"""
        status = {
            "is_running": self.is_running,
            "interface_count": len(self.interfaces),
            "interfaces": {}
        }
        
        for name, interface in self.interfaces.items():
            status["interfaces"][name] = interface.get_status()
            
        return status
        
    def get_interface_status(self, interface_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific interface"""
        interface = self.interfaces.get(interface_name)
        if interface:
            return interface.get_status()
        return None
