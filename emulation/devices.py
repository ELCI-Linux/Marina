"""
Marina Device Emulator
======================

Emulates various device types including mobile phones, tablets, desktops, 
IoT devices, and wearables. Provides realistic device characteristics,
capabilities, and behaviors for testing and development.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random
import uuid

logger = logging.getLogger(__name__)

class DeviceType(Enum):
    """Supported device types"""
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    DESKTOP = "desktop"
    LAPTOP = "laptop"
    SMARTWATCH = "smartwatch"
    IOT_SENSOR = "iot_sensor"
    SMART_TV = "smart_tv"
    SMART_SPEAKER = "smart_speaker"
    GAMING_CONSOLE = "gaming_console"

class DeviceOS(Enum):
    """Supported operating systems"""
    ANDROID = "android"
    IOS = "ios"
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    WEAR_OS = "wear_os"
    TVOS = "tvos"
    EMBEDDED = "embedded"

@dataclass
class DeviceProfile:
    """Device profile with hardware specifications and capabilities"""
    device_id: str
    device_type: DeviceType
    os_type: DeviceOS
    os_version: str
    manufacturer: str
    model: str
    screen_resolution: Tuple[int, int]
    screen_density: int  # DPI
    cpu_cores: int
    ram_mb: int
    storage_gb: int
    battery_capacity_mah: int
    has_cellular: bool = False
    has_wifi: bool = True
    has_bluetooth: bool = True
    has_gps: bool = False
    has_camera: bool = False
    has_microphone: bool = False
    has_speakers: bool = True
    has_fingerprint: bool = False
    has_face_unlock: bool = False
    sensors: List[str] = None
    custom_properties: Dict[str, Any] = None

    def __post_init__(self):
        if self.sensors is None:
            self.sensors = []
        if self.custom_properties is None:
            self.custom_properties = {}

class EmulatedDevice:
    """Represents an emulated device instance"""
    
    def __init__(self, profile: DeviceProfile):
        self.profile = profile
        self.device_id = profile.device_id
        self.is_running = False
        self.current_state = {}
        self.battery_level = 100
        self.network_connected = True
        self.apps_running = []
        self.sensor_data = {}
        self.performance_metrics = {}
        
        # Initialize device state
        self._initialize_device_state()
    
    def _initialize_device_state(self):
        """Initialize device state based on profile"""
        self.current_state = {
            "power_on": True,
            "screen_on": True,
            "locked": False,
            "airplane_mode": False,
            "volume_level": 50,
            "brightness": 75,
            "network_type": "wifi" if self.profile.has_wifi else "none"
        }
        
        # Initialize sensor data if device has sensors
        if "accelerometer" in self.profile.sensors:
            self.sensor_data["accelerometer"] = {"x": 0.0, "y": 0.0, "z": 9.8}
        
        if "gyroscope" in self.profile.sensors:
            self.sensor_data["gyroscope"] = {"x": 0.0, "y": 0.0, "z": 0.0}
        
        if "magnetometer" in self.profile.sensors:
            self.sensor_data["magnetometer"] = {"x": 0.0, "y": 0.0, "z": 0.0}
        
        if "gps" in self.profile.sensors or self.profile.has_gps:
            self.sensor_data["gps"] = {"latitude": 37.7749, "longitude": -122.4194, "accuracy": 5.0}
    
    async def start(self):
        """Start device emulation"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info(f"Starting device emulation: {self.profile.manufacturer} {self.profile.model}")
        
        # Start background tasks
        asyncio.create_task(self._simulate_battery_drain())
        asyncio.create_task(self._simulate_sensor_updates())
        asyncio.create_task(self._monitor_performance())
    
    async def stop(self):
        """Stop device emulation"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info(f"Stopping device emulation: {self.device_id}")
    
    async def _simulate_battery_drain(self):
        """Simulate realistic battery drain"""
        while self.is_running:
            try:
                # Calculate drain rate based on usage
                base_drain = 0.1  # 0.1% per minute base drain
                screen_drain = 0.2 if self.current_state.get("screen_on") else 0
                app_drain = len(self.apps_running) * 0.05
                
                total_drain = base_drain + screen_drain + app_drain
                
                self.battery_level = max(0, self.battery_level - total_drain)
                
                # Auto-shutdown at 0%
                if self.battery_level <= 0:
                    self.current_state["power_on"] = False
                    logger.info(f"Device {self.device_id} auto-shutdown due to low battery")
                
                await asyncio.sleep(60)  # Update every minute
            except asyncio.CancelledError:
                break
    
    async def _simulate_sensor_updates(self):
        """Simulate sensor data updates"""
        while self.is_running:
            try:
                # Update accelerometer with small random variations
                if "accelerometer" in self.sensor_data:
                    self.sensor_data["accelerometer"] = {
                        "x": random.uniform(-0.5, 0.5),
                        "y": random.uniform(-0.5, 0.5),
                        "z": 9.8 + random.uniform(-0.2, 0.2)
                    }
                
                # Update gyroscope
                if "gyroscope" in self.sensor_data:
                    self.sensor_data["gyroscope"] = {
                        "x": random.uniform(-0.1, 0.1),
                        "y": random.uniform(-0.1, 0.1),
                        "z": random.uniform(-0.1, 0.1)
                    }
                
                # Slightly vary GPS if available
                if "gps" in self.sensor_data:
                    current_gps = self.sensor_data["gps"]
                    self.sensor_data["gps"] = {
                        "latitude": current_gps["latitude"] + random.uniform(-0.0001, 0.0001),
                        "longitude": current_gps["longitude"] + random.uniform(-0.0001, 0.0001),
                        "accuracy": random.uniform(3.0, 8.0)
                    }
                
                await asyncio.sleep(1)  # Update every second
            except asyncio.CancelledError:
                break
    
    async def _monitor_performance(self):
        """Monitor device performance metrics"""
        while self.is_running:
            try:
                # Simulate CPU and memory usage
                cpu_usage = random.uniform(5, 30) + len(self.apps_running) * 5
                memory_usage = random.uniform(20, 40) + len(self.apps_running) * 10
                
                self.performance_metrics = {
                    "cpu_usage_percent": min(100, cpu_usage),
                    "memory_usage_percent": min(100, memory_usage),
                    "available_memory_mb": max(0, self.profile.ram_mb * (100 - memory_usage) / 100),
                    "network_signal_strength": random.uniform(70, 100) if self.network_connected else 0,
                    "timestamp": time.time()
                }
                
                await asyncio.sleep(5)  # Update every 5 seconds
            except asyncio.CancelledError:
                break
    
    def power_on(self):
        """Power on the device"""
        if self.battery_level > 0:
            self.current_state["power_on"] = True
            logger.info(f"Device {self.device_id} powered on")
            return True
        return False
    
    def power_off(self):
        """Power off the device"""
        self.current_state["power_on"] = False
        self.current_state["screen_on"] = False
        logger.info(f"Device {self.device_id} powered off")
    
    def unlock_device(self, method: str = "swipe"):
        """Unlock the device using specified method"""
        if not self.current_state.get("power_on"):
            return False
        
        success = True
        if method == "fingerprint" and not self.profile.has_fingerprint:
            success = False
        elif method == "face" and not self.profile.has_face_unlock:
            success = False
        
        if success:
            self.current_state["locked"] = False
            self.current_state["screen_on"] = True
            logger.info(f"Device {self.device_id} unlocked using {method}")
        
        return success
    
    def launch_app(self, app_name: str):
        """Launch an application"""
        if not self.current_state.get("power_on") or self.current_state.get("locked"):
            return False
        
        if app_name not in self.apps_running:
            self.apps_running.append(app_name)
            logger.info(f"Launched app '{app_name}' on device {self.device_id}")
        
        return True
    
    def close_app(self, app_name: str):
        """Close an application"""
        if app_name in self.apps_running:
            self.apps_running.remove(app_name)
            logger.info(f"Closed app '{app_name}' on device {self.device_id}")
            return True
        return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get comprehensive device information"""
        return {
            "profile": asdict(self.profile),
            "state": self.current_state,
            "battery_level": self.battery_level,
            "running_apps": self.apps_running,
            "sensor_data": self.sensor_data,
            "performance": self.performance_metrics,
            "is_running": self.is_running
        }

class DeviceEmulator:
    """Main device emulator managing multiple device instances"""
    
    def __init__(self):
        self.devices: Dict[str, EmulatedDevice] = {}
        self.device_profiles = self._load_device_profiles()
    
    def _load_device_profiles(self) -> Dict[str, DeviceProfile]:
        """Load predefined device profiles"""
        profiles = {}
        
        # Popular smartphone profiles
        profiles["iphone_15_pro"] = DeviceProfile(
            device_id="iphone_15_pro",
            device_type=DeviceType.SMARTPHONE,
            os_type=DeviceOS.IOS,
            os_version="17.0",
            manufacturer="Apple",
            model="iPhone 15 Pro",
            screen_resolution=(1179, 2556),
            screen_density=460,
            cpu_cores=6,
            ram_mb=8192,
            storage_gb=256,
            battery_capacity_mah=3274,
            has_cellular=True,
            has_gps=True,
            has_camera=True,
            has_microphone=True,
            has_fingerprint=False,
            has_face_unlock=True,
            sensors=["accelerometer", "gyroscope", "magnetometer", "barometer", "proximity"]
        )
        
        profiles["samsung_galaxy_s24"] = DeviceProfile(
            device_id="samsung_galaxy_s24",
            device_type=DeviceType.SMARTPHONE,
            os_type=DeviceOS.ANDROID,
            os_version="14",
            manufacturer="Samsung",
            model="Galaxy S24",
            screen_resolution=(1080, 2340),
            screen_density=422,
            cpu_cores=8,
            ram_mb=8192,
            storage_gb=256,
            battery_capacity_mah=4000,
            has_cellular=True,
            has_gps=True,
            has_camera=True,
            has_microphone=True,
            has_fingerprint=True,
            has_face_unlock=True,
            sensors=["accelerometer", "gyroscope", "magnetometer", "barometer", "proximity", "heart_rate"]
        )
        
        # Tablet profile
        profiles["ipad_pro_12"] = DeviceProfile(
            device_id="ipad_pro_12",
            device_type=DeviceType.TABLET,
            os_type=DeviceOS.IOS,
            os_version="17.0",
            manufacturer="Apple",
            model="iPad Pro 12.9\"",
            screen_resolution=(2048, 2732),
            screen_density=264,
            cpu_cores=8,
            ram_mb=16384,
            storage_gb=512,
            battery_capacity_mah=10758,
            has_cellular=False,
            has_gps=False,
            has_camera=True,
            has_microphone=True,
            sensors=["accelerometer", "gyroscope", "magnetometer", "barometer"]
        )
        
        # Smartwatch profile
        profiles["apple_watch_series_9"] = DeviceProfile(
            device_id="apple_watch_series_9",
            device_type=DeviceType.SMARTWATCH,
            os_type=DeviceOS.WEAR_OS,
            os_version="10.0",
            manufacturer="Apple",
            model="Apple Watch Series 9",
            screen_resolution=(396, 484),
            screen_density=326,
            cpu_cores=2,
            ram_mb=1024,
            storage_gb=64,
            battery_capacity_mah=308,
            has_cellular=True,
            has_gps=True,
            has_camera=False,
            has_microphone=True,
            has_speakers=True,
            sensors=["accelerometer", "gyroscope", "heart_rate", "ecg", "blood_oxygen"]
        )
        
        # IoT sensor profile
        profiles["temperature_sensor"] = DeviceProfile(
            device_id="temperature_sensor",
            device_type=DeviceType.IOT_SENSOR,
            os_type=DeviceOS.EMBEDDED,
            os_version="1.0",
            manufacturer="Generic",
            model="Temperature Sensor v1",
            screen_resolution=(0, 0),
            screen_density=0,
            cpu_cores=1,
            ram_mb=16,
            storage_gb=1,
            battery_capacity_mah=2400,
            has_cellular=False,
            has_wifi=True,
            has_bluetooth=True,
            has_gps=False,
            has_camera=False,
            has_microphone=False,
            has_speakers=False,
            sensors=["temperature", "humidity", "pressure"]
        )
        
        return profiles
    
    async def create_device(self, profile_name: str, custom_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a new emulated device"""
        if profile_name not in self.device_profiles:
            logger.error(f"Device profile '{profile_name}' not found")
            return None
        
        # Create device profile
        profile = self.device_profiles[profile_name]
        
        # Apply custom configuration if provided
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
        
        # Generate unique device ID if needed
        device_id = f"{profile.device_id}_{int(time.time())}"
        profile.device_id = device_id
        
        # Create emulated device
        device = EmulatedDevice(profile)
        self.devices[device_id] = device
        
        logger.info(f"Created emulated device: {device_id} ({profile.manufacturer} {profile.model})")
        return device_id
    
    async def start_emulation(self, config) -> bool:
        """Start device emulation based on configuration"""
        try:
            # Default to smartphone if not specified
            device_type = config.custom_properties.get("device_type", "samsung_galaxy_s24")
            
            device_id = await self.create_device(device_type)
            if device_id:
                await self.devices[device_id].start()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to start device emulation: {e}")
            return False
    
    async def stop_emulation(self, session_id: str) -> bool:
        """Stop device emulation for a session"""
        try:
            # Stop all devices for this session
            devices_to_stop = [d for d in self.devices.values() if d.is_running]
            for device in devices_to_stop:
                await device.stop()
            return True
        except Exception as e:
            logger.error(f"Failed to stop device emulation: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[EmulatedDevice]:
        """Get emulated device by ID"""
        return self.devices.get(device_id)
    
    def list_devices(self) -> List[str]:
        """List all emulated device IDs"""
        return list(self.devices.keys())
    
    def list_available_profiles(self) -> List[str]:
        """List all available device profiles"""
        return list(self.device_profiles.keys())
    
    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific device"""
        device = self.devices.get(device_id)
        if device:
            return device.get_device_info()
        return None
    
    async def simulate_user_interaction(self, device_id: str, interaction: Dict[str, Any]) -> bool:
        """Simulate user interaction with a device"""
        device = self.devices.get(device_id)
        if not device or not device.is_running:
            return False
        
        interaction_type = interaction.get("type")
        
        if interaction_type == "tap":
            # Simulate screen tap
            x, y = interaction.get("coordinates", (0, 0))
            logger.info(f"Simulated tap at ({x}, {y}) on device {device_id}")
            
        elif interaction_type == "swipe":
            # Simulate swipe gesture
            start = interaction.get("start", (0, 0))
            end = interaction.get("end", (0, 0))
            logger.info(f"Simulated swipe from {start} to {end} on device {device_id}")
            
        elif interaction_type == "press_button":
            # Simulate physical button press
            button = interaction.get("button", "home")
            logger.info(f"Simulated {button} button press on device {device_id}")
            
            if button == "power":
                if device.current_state.get("power_on"):
                    device.power_off()
                else:
                    device.power_on()
            
        elif interaction_type == "launch_app":
            # Launch application
            app_name = interaction.get("app_name", "")
            return device.launch_app(app_name)
        
        return True
    
    async def update_device_sensors(self, device_id: str, sensor_data: Dict[str, Any]) -> bool:
        """Update sensor data for a specific device"""
        device = self.devices.get(device_id)
        if not device:
            return False
        
        for sensor_name, data in sensor_data.items():
            if sensor_name in device.sensor_data:
                device.sensor_data[sensor_name] = data
                logger.info(f"Updated {sensor_name} sensor data for device {device_id}")
        
        return True
