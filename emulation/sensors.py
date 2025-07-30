"""
Marina Sensor Emulator
=====================

Emulates various sensors commonly found in mobile devices, IoT devices, and
other hardware. Provides realistic sensor data simulation for testing and
development of sensor-dependent applications.
"""

import asyncio
import logging
import json
import time
import random
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class SensorType(Enum):
    """Types of sensors that can be emulated"""
    ACCELEROMETER = "accelerometer"
    GYROSCOPE = "gyroscope"
    MAGNETOMETER = "magnetometer"
    GPS = "gps"
    BAROMETER = "barometer"
    THERMOMETER = "thermometer"
    HUMIDITY = "humidity"
    LIGHT = "light"
    PROXIMITY = "proximity"
    HEART_RATE = "heart_rate"
    STEP_COUNTER = "step_counter"
    ORIENTATION = "orientation"
    GRAVITY = "gravity"
    LINEAR_ACCELERATION = "linear_acceleration"
    ROTATION_VECTOR = "rotation_vector"
    FINGERPRINT = "fingerprint"
    FACE_ID = "face_id"

@dataclass
class SensorSpec:
    """Sensor specification"""
    sensor_type: SensorType
    name: str
    manufacturer: str
    range_values: Tuple[float, float]
    resolution: float
    power_consumption: float  # mW
    update_rate_hz: float
    is_enabled: bool = True
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}

class EmulatedSensor:
    """Base class for emulated sensors"""
    
    def __init__(self, spec: SensorSpec):
        self.spec = spec
        self.sensor_type = spec.sensor_type
        self.name = spec.name
        self.is_active = False
        self.current_values = {}
        self.last_update = 0
        self.update_interval = 1.0 / spec.update_rate_hz
        self.listeners = []
        
    async def start(self):
        """Start sensor emulation"""
        if self.is_active:
            return
            
        self.is_active = True
        logger.info(f"Started sensor: {self.name} ({self.sensor_type.value})")
        
        # Start background data generation
        asyncio.create_task(self._generate_sensor_data())
        
    async def stop(self):
        """Stop sensor emulation"""
        self.is_active = False
        logger.info(f"Stopped sensor: {self.name}")
        
    async def _generate_sensor_data(self):
        """Generate sensor data based on sensor type"""
        while self.is_active:
            try:
                # Generate sensor-specific data
                self._update_sensor_values()
                
                # Notify listeners
                for listener in self.listeners:
                    if callable(listener):
                        listener(self.sensor_type, self.current_values)
                
                self.last_update = time.time()
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
                
    def _update_sensor_values(self):
        """Update sensor values - to be overridden by specific sensor types"""
        pass
        
    def add_listener(self, callback):
        """Add a listener for sensor data updates"""
        self.listeners.append(callback)
        
    def remove_listener(self, callback):
        """Remove a sensor data listener"""
        if callback in self.listeners:
            self.listeners.remove(callback)
            
    def get_current_values(self) -> Dict[str, Any]:
        """Get current sensor values"""
        return self.current_values.copy()
        
    def get_status(self) -> Dict[str, Any]:
        """Get sensor status"""
        return {
            "name": self.name,
            "type": self.sensor_type.value,
            "manufacturer": self.spec.manufacturer,
            "is_active": self.is_active,
            "update_rate_hz": self.spec.update_rate_hz,
            "power_consumption_mw": self.spec.power_consumption,
            "last_update": self.last_update,
            "current_values": self.current_values
        }

class AccelerometerSensor(EmulatedSensor):
    """Emulated accelerometer sensor"""
    
    def __init__(self, spec: SensorSpec):
        super().__init__(spec)
        self.base_values = {"x": 0.0, "y": 0.0, "z": 9.8}  # Static gravity
        self.motion_state = "stationary"  # stationary, walking, running, driving
        
    def _update_sensor_values(self):
        """Update accelerometer values based on motion state"""
        if self.motion_state == "stationary":
            # Small random variations around gravity
            self.current_values = {
                "x": self.base_values["x"] + random.uniform(-0.1, 0.1),
                "y": self.base_values["y"] + random.uniform(-0.1, 0.1),
                "z": self.base_values["z"] + random.uniform(-0.2, 0.2),
                "timestamp": time.time()
            }
        elif self.motion_state == "walking":
            # Simulate walking motion
            t = time.time()
            self.current_values = {
                "x": math.sin(t * 4) * 2.0 + random.uniform(-0.5, 0.5),
                "y": math.cos(t * 2) * 1.5 + random.uniform(-0.3, 0.3),
                "z": 9.8 + math.sin(t * 8) * 3.0 + random.uniform(-1.0, 1.0),
                "timestamp": t
            }
        elif self.motion_state == "running":
            # Simulate running motion
            t = time.time()
            self.current_values = {
                "x": math.sin(t * 6) * 4.0 + random.uniform(-1.0, 1.0),
                "y": math.cos(t * 3) * 3.0 + random.uniform(-0.8, 0.8),
                "z": 9.8 + math.sin(t * 12) * 6.0 + random.uniform(-2.0, 2.0),
                "timestamp": t
            }
        elif self.motion_state == "driving":
            # Simulate vehicle motion
            t = time.time()
            self.current_values = {
                "x": random.uniform(-2.0, 2.0),
                "y": 9.8 + random.uniform(-1.0, 1.0),
                "z": random.uniform(-1.0, 1.0),
                "timestamp": t
            }
    
    def set_motion_state(self, state: str):
        """Set motion state for realistic simulation"""
        if state in ["stationary", "walking", "running", "driving"]:
            self.motion_state = state
            logger.info(f"Set accelerometer motion state to: {state}")

class GyroscopeSensor(EmulatedSensor):
    """Emulated gyroscope sensor"""
    
    def __init__(self, spec: SensorSpec):
        super().__init__(spec)
        self.angular_velocity = {"x": 0.0, "y": 0.0, "z": 0.0}
        
    def _update_sensor_values(self):
        """Update gyroscope values"""
        # Simulate small random rotations
        self.current_values = {
            "x": random.uniform(-0.1, 0.1),  # rad/s
            "y": random.uniform(-0.1, 0.1),
            "z": random.uniform(-0.1, 0.1),
            "timestamp": time.time()
        }

class GPSSensor(EmulatedSensor):
    """Emulated GPS sensor"""
    
    def __init__(self, spec: SensorSpec):
        super().__init__(spec)
        # Default location (San Francisco)
        self.base_location = {"latitude": 37.7749, "longitude": -122.4194}
        self.is_moving = False
        self.speed_mps = 0.0  # meters per second
        self.bearing = 0.0  # degrees
        
    def _update_sensor_values(self):
        """Update GPS coordinates"""
        if self.is_moving and self.speed_mps > 0:
            # Simulate movement
            distance_m = self.speed_mps * self.update_interval
            
            # Convert to lat/lng delta (rough approximation)
            lat_delta = (distance_m * math.cos(math.radians(self.bearing))) / 111000
            lng_delta = (distance_m * math.sin(math.radians(self.bearing))) / (111000 * math.cos(math.radians(self.base_location["latitude"])))
            
            self.base_location["latitude"] += lat_delta
            self.base_location["longitude"] += lng_delta
        
        # Add some GPS accuracy noise
        self.current_values = {
            "latitude": self.base_location["latitude"] + random.uniform(-0.0001, 0.0001),
            "longitude": self.base_location["longitude"] + random.uniform(-0.0001, 0.0001),
            "altitude": random.uniform(10, 50),  # meters
            "accuracy": random.uniform(3.0, 15.0),  # meters
            "speed": self.speed_mps,
            "bearing": self.bearing,
            "timestamp": time.time()
        }
    
    def set_location(self, latitude: float, longitude: float):
        """Set GPS location"""
        self.base_location = {"latitude": latitude, "longitude": longitude}
        logger.info(f"Set GPS location to: {latitude}, {longitude}")
    
    def start_movement(self, speed_mps: float, bearing: float):
        """Start simulated movement"""
        self.is_moving = True
        self.speed_mps = speed_mps
        self.bearing = bearing
        logger.info(f"Started GPS movement: {speed_mps} m/s, bearing {bearing}°")
    
    def stop_movement(self):
        """Stop simulated movement"""
        self.is_moving = False
        self.speed_mps = 0.0
        logger.info("Stopped GPS movement")

class BarometerSensor(EmulatedSensor):
    """Emulated barometer sensor"""
    
    def __init__(self, spec: SensorSpec):
        super().__init__(spec)
        self.base_pressure = 1013.25  # hPa (sea level)
        
    def _update_sensor_values(self):
        """Update barometer values"""
        # Simulate small pressure variations
        self.current_values = {
            "pressure": self.base_pressure + random.uniform(-2.0, 2.0),
            "altitude": random.uniform(-5, 5),  # meters (derived from pressure)
            "timestamp": time.time()
        }

class ThermometerSensor(EmulatedSensor):
    """Emulated temperature sensor"""
    
    def __init__(self, spec: SensorSpec):
        super().__init__(spec)
        self.base_temperature = 25.0  # Celsius
        
    def _update_sensor_values(self):
        """Update temperature values"""
        # Simulate temperature variations
        self.current_values = {
            "temperature": self.base_temperature + random.uniform(-2.0, 2.0),
            "timestamp": time.time()
        }

class ProximitySensor(EmulatedSensor):
    """Emulated proximity sensor"""
    
    def __init__(self, spec: SensorSpec):
        super().__init__(spec)
        self.near_threshold = 5.0  # cm
        
    def _update_sensor_values(self):
        """Update proximity values"""
        distance = random.uniform(0, 20)  # cm
        self.current_values = {
            "distance": distance,
            "near": distance < self.near_threshold,
            "timestamp": time.time()
        }

class HeartRateSensor(EmulatedSensor):
    """Emulated heart rate sensor"""
    
    def __init__(self, spec: SensorSpec):
        super().__init__(spec)
        self.base_heart_rate = 70  # BPM
        self.activity_level = "resting"  # resting, light, moderate, vigorous
        
    def _update_sensor_values(self):
        """Update heart rate values"""
        if self.activity_level == "resting":
            heart_rate = self.base_heart_rate + random.randint(-5, 5)
        elif self.activity_level == "light":
            heart_rate = self.base_heart_rate + random.randint(20, 40)
        elif self.activity_level == "moderate":
            heart_rate = self.base_heart_rate + random.randint(50, 80)
        elif self.activity_level == "vigorous":
            heart_rate = self.base_heart_rate + random.randint(90, 120)
        else:
            heart_rate = self.base_heart_rate
            
        self.current_values = {
            "heart_rate": max(40, min(200, heart_rate)),
            "confidence": random.uniform(0.8, 1.0),
            "timestamp": time.time()
        }
    
    def set_activity_level(self, level: str):
        """Set activity level for heart rate simulation"""
        if level in ["resting", "light", "moderate", "vigorous"]:
            self.activity_level = level
            logger.info(f"Set heart rate activity level to: {level}")

class SensorEmulator:
    """Main sensor emulator managing multiple sensors"""
    
    def __init__(self):
        self.sensors: Dict[str, EmulatedSensor] = {}
        self.sensor_specs = self._create_default_sensor_specs()
        self.is_running = False
        
    def _create_default_sensor_specs(self) -> Dict[str, SensorSpec]:
        """Create default sensor specifications"""
        specs = {}
        
        # Accelerometer
        specs["accelerometer"] = SensorSpec(
            sensor_type=SensorType.ACCELEROMETER,
            name="Emulated Accelerometer",
            manufacturer="Generic",
            range_values=(-20.0, 20.0),  # m/s²
            resolution=0.01,
            power_consumption=0.5,
            update_rate_hz=50.0
        )
        
        # Gyroscope
        specs["gyroscope"] = SensorSpec(
            sensor_type=SensorType.GYROSCOPE,
            name="Emulated Gyroscope", 
            manufacturer="Generic",
            range_values=(-10.0, 10.0),  # rad/s
            resolution=0.001,
            power_consumption=0.8,
            update_rate_hz=50.0
        )
        
        # GPS
        specs["gps"] = SensorSpec(
            sensor_type=SensorType.GPS,
            name="Emulated GPS",
            manufacturer="Generic",
            range_values=(-180.0, 180.0),  # degrees
            resolution=0.0001,
            power_consumption=50.0,
            update_rate_hz=1.0
        )
        
        # Barometer
        specs["barometer"] = SensorSpec(
            sensor_type=SensorType.BAROMETER,
            name="Emulated Barometer",
            manufacturer="Generic",
            range_values=(800.0, 1200.0),  # hPa
            resolution=0.1,
            power_consumption=0.3,
            update_rate_hz=10.0
        )
        
        # Thermometer
        specs["thermometer"] = SensorSpec(
            sensor_type=SensorType.THERMOMETER,
            name="Emulated Temperature Sensor",
            manufacturer="Generic",
            range_values=(-40.0, 85.0),  # Celsius
            resolution=0.1,
            power_consumption=0.2,
            update_rate_hz=1.0
        )
        
        # Proximity
        specs["proximity"] = SensorSpec(
            sensor_type=SensorType.PROXIMITY,
            name="Emulated Proximity Sensor",
            manufacturer="Generic",
            range_values=(0.0, 20.0),  # cm
            resolution=0.1,
            power_consumption=0.1,
            update_rate_hz=10.0
        )
        
        # Heart Rate
        specs["heart_rate"] = SensorSpec(
            sensor_type=SensorType.HEART_RATE,
            name="Emulated Heart Rate Sensor",
            manufacturer="Generic",
            range_values=(40.0, 200.0),  # BPM
            resolution=1.0,
            power_consumption=5.0,
            update_rate_hz=1.0
        )
        
        return specs
        
    def _create_sensor_instance(self, sensor_type: SensorType, spec: SensorSpec) -> EmulatedSensor:
        """Create appropriate sensor instance based on type"""
        if sensor_type == SensorType.ACCELEROMETER:
            return AccelerometerSensor(spec)
        elif sensor_type == SensorType.GYROSCOPE:
            return GyroscopeSensor(spec)
        elif sensor_type == SensorType.GPS:
            return GPSSensor(spec)
        elif sensor_type == SensorType.BAROMETER:
            return BarometerSensor(spec)
        elif sensor_type == SensorType.THERMOMETER:
            return ThermometerSensor(spec)
        elif sensor_type == SensorType.PROXIMITY:
            return ProximitySensor(spec)
        elif sensor_type == SensorType.HEART_RATE:
            return HeartRateSensor(spec)
        else:
            return EmulatedSensor(spec)
            
    async def create_sensor(self, sensor_name: str) -> Optional[str]:
        """Create a sensor from specifications"""
        if sensor_name not in self.sensor_specs:
            logger.error(f"Sensor specification '{sensor_name}' not found")
            return None
            
        spec = self.sensor_specs[sensor_name]
        sensor = self._create_sensor_instance(spec.sensor_type, spec)
        self.sensors[sensor_name] = sensor
        
        logger.info(f"Created sensor: {sensor_name} ({spec.sensor_type.value})")
        return sensor_name
        
    async def start_simulation(self, config) -> bool:
        """Start sensor simulation based on configuration"""
        try:
            if not config.sensor_simulation:
                logger.info("Sensor simulation disabled in configuration")
                return True
                
            self.is_running = True
            
            # Create sensors based on target platform
            if config.target_platform in ["android", "ios"]:
                # Mobile device sensors
                sensor_list = ["accelerometer", "gyroscope", "gps", "barometer", "proximity"]
                if config.target_platform == "ios":
                    sensor_list.append("heart_rate")  # Apple Watch integration
            elif config.target_platform in ["windows", "macos", "linux"]:
                # Desktop/laptop sensors (limited)
                sensor_list = ["accelerometer", "thermometer"]
            else:
                # Default sensor set
                sensor_list = ["accelerometer", "gyroscope", "proximity"]
                
            # Create and start sensors
            for sensor_name in sensor_list:
                if sensor_name in self.sensor_specs:
                    await self.create_sensor(sensor_name)
                    await self.sensors[sensor_name].start()
                    
            logger.info("Sensor simulation started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start sensor simulation: {e}")
            return False
            
    async def stop_simulation(self, session_id: str) -> bool:
        """Stop sensor simulation for a session"""
        try:
            logger.info("Stopping sensor simulation")
            
            # Stop all sensors
            for sensor in self.sensors.values():
                await sensor.stop()
                
            self.sensors.clear()
            self.is_running = False
            
            logger.info("Sensor simulation stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop sensor simulation: {e}")
            return False
            
    def get_sensor(self, sensor_name: str) -> Optional[EmulatedSensor]:
        """Get sensor by name"""
        return self.sensors.get(sensor_name)
        
    def list_sensors(self) -> List[str]:
        """List all sensor names"""
        return list(self.sensors.keys())
        
    def list_available_sensors(self) -> List[str]:
        """List all available sensor specifications"""
        return list(self.sensor_specs.keys())
        
    def get_sensor_values(self, sensor_name: str) -> Optional[Dict[str, Any]]:
        """Get current sensor values"""
        sensor = self.sensors.get(sensor_name)
        if sensor:
            return sensor.get_current_values()
        return None
        
    def get_all_sensor_values(self) -> Dict[str, Dict[str, Any]]:
        """Get current values from all sensors"""
        values = {}
        for name, sensor in self.sensors.items():
            values[name] = sensor.get_current_values()
        return values
        
    def add_sensor_listener(self, sensor_name: str, callback):
        """Add listener for sensor data updates"""
        sensor = self.sensors.get(sensor_name)
        if sensor:
            sensor.add_listener(callback)
            return True
        return False
        
    def remove_sensor_listener(self, sensor_name: str, callback):
        """Remove sensor data listener"""
        sensor = self.sensors.get(sensor_name)
        if sensor:
            sensor.remove_listener(callback)
            return True
        return False
        
    def simulate_motion(self, motion_type: str, duration_seconds: int = 10):
        """Simulate device motion affecting relevant sensors"""
        async def motion_simulation():
            logger.info(f"Simulating {motion_type} motion for {duration_seconds} seconds")
            
            # Update accelerometer if available
            accelerometer = self.sensors.get("accelerometer")
            if accelerometer and isinstance(accelerometer, AccelerometerSensor):
                original_state = accelerometer.motion_state
                accelerometer.set_motion_state(motion_type)
                
                # Update heart rate if available  
                heart_rate = self.sensors.get("heart_rate")
                if heart_rate and isinstance(heart_rate, HeartRateSensor):
                    if motion_type in ["walking", "light"]:
                        heart_rate.set_activity_level("light")
                    elif motion_type == "running":
                        heart_rate.set_activity_level("vigorous")
                        
                await asyncio.sleep(duration_seconds)
                
                # Restore original states
                accelerometer.set_motion_state(original_state)
                if heart_rate:
                    heart_rate.set_activity_level("resting")
                    
            logger.info(f"Motion simulation completed: {motion_type}")
            
        asyncio.create_task(motion_simulation())
        
    def simulate_location_change(self, start_lat: float, start_lng: float, 
                                end_lat: float, end_lng: float, 
                                duration_seconds: int = 60):
        """Simulate GPS location change over time"""
        async def location_simulation():
            gps = self.sensors.get("gps")
            if not gps or not isinstance(gps, GPSSensor):
                logger.warning("GPS sensor not available for location simulation")
                return
                
            logger.info(f"Simulating location change from ({start_lat}, {start_lng}) to ({end_lat}, {end_lng})")
            
            # Calculate distance and bearing
            lat_diff = end_lat - start_lat
            lng_diff = end_lng - start_lng
            distance = math.sqrt(lat_diff**2 + lng_diff**2) * 111000  # rough meters
            bearing = math.degrees(math.atan2(lng_diff, lat_diff))
            speed = distance / duration_seconds
            
            # Set initial location and start movement
            gps.set_location(start_lat, start_lng)
            gps.start_movement(speed, bearing)
            
            await asyncio.sleep(duration_seconds)
            
            # Stop movement
            gps.stop_movement()
            logger.info("Location simulation completed")
            
        asyncio.create_task(location_simulation())
        
    def get_sensor_status(self) -> Dict[str, Any]:
        """Get overall sensor status"""
        status = {
            "is_running": self.is_running,
            "sensor_count": len(self.sensors),
            "total_power_consumption_mw": sum(
                spec.power_consumption for spec in self.sensor_specs.values() 
                if spec.sensor_type.value in self.sensors
            ),
            "sensors": {}
        }
        
        for name, sensor in self.sensors.items():
            status["sensors"][name] = sensor.get_status()
            
        return status
