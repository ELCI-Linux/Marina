# Marina Emulation Framework

A comprehensive emulation system for simulating various devices, operating systems, hardware components, and network conditions. Built for testing, development, and research purposes.

## 🎯 Overview

The Marina Emulation Framework provides realistic emulation of:

- **📱 Device Emulation**: Mobile phones, tablets, IoT devices, wearables
- **💻 OS Environment Emulation**: Android, iOS, Windows, macOS, Linux
- **🔧 Hardware Abstraction Layer**: CPU, memory, audio, video, sensors
- **🌐 Network Emulation**: WiFi, cellular, Bluetooth, ethernet with realistic conditions
- **📡 Sensor Simulation**: Accelerometer, GPS, gyroscope, heart rate, and more

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from emulation import EmulationEngine, EmulationConfig

async def main():
    # Create emulation engine
    engine = EmulationEngine()
    
    # Configure emulation
    config = EmulationConfig(
        session_id="my_test_session",
        emulation_type="all",
        target_platform="android",
        performance_profile="medium",
        resource_limits={"memory_mb": 2048, "cpu_percent": 50},
        audio_enabled=True,
        video_enabled=True,
        network_enabled=True,
        sensor_simulation=True
    )
    
    # Start emulation
    success = await engine.start_emulation(config)
    if success:
        print("🎉 Emulation started successfully!")
        
        # Your testing code here...
        await asyncio.sleep(10)
        
        # Stop emulation
        await engine.stop_emulation(config.session_id)
        print("✅ Emulation stopped")

if __name__ == "__main__":
    asyncio.run(main())
```

### Run Demo

```bash
cd /home/adminx/Marina/emulation
python3 demo.py
```

## 📱 Device Emulation

Emulate realistic device behavior with predefined profiles:

```python
from emulation.devices import DeviceEmulator

device_emulator = DeviceEmulator()

# Available profiles: iphone_15_pro, samsung_galaxy_s24, ipad_pro_12, etc.
device_id = await device_emulator.create_device("iphone_15_pro")

device = device_emulator.get_device(device_id)
await device.start()

# Simulate interactions
device.unlock_device("face")
device.launch_app("com.apple.MobilePhone")

# Get device status
status = device.get_device_info()
print(f"Battery: {status['battery_level']}%")
print(f"Running apps: {status['running_apps']}")
```

### Device Features

- **Realistic Battery Drain**: Based on screen usage, running apps, and hardware activity
- **Sensor Data**: Accelerometer, gyroscope, GPS, heart rate simulation
- **Performance Metrics**: CPU/memory usage simulation
- **App Management**: Launch, close, and manage applications
- **Hardware Controls**: Power, volume, brightness, connectivity

## 💻 OS Environment Emulation

Create isolated operating system environments:

```python
from emulation.os_environments import OSEnvironmentManager

os_manager = OSEnvironmentManager()

# Create Android 14 environment
env_id = await os_manager.create_environment("android_14")
environment = os_manager.get_environment(env_id)

await environment.start()

# File system operations
environment.file_system.create_file("test.txt", "Hello World!")
content = environment.file_system.read_file("test.txt")

# Process management
processes = environment.list_processes()
services = environment.get_service_status()
```

### Supported OS Types

- **Android**: Android 14 with realistic file system and process structure
- **iOS**: iOS 17 emulation with app sandbox structure
- **Windows**: Windows 11 with registry and service simulation
- **Linux**: Ubuntu 22.04 with systemd services
- **Embedded**: Generic embedded system environment

## 🔧 Hardware Abstraction Layer

Emulate hardware components with realistic behavior:

```python
from emulation.hardware import HardwareAbstractionLayer

hal = HardwareAbstractionLayer()
await hal.initialize(config)

# Memory operations
hal.allocate_memory(512, "my_region")
hal.free_memory("my_region")

# Audio operations
audio_data = b"sample_audio"
hal.play_audio(audio_data)
recorded = hal.record_audio(5000)  # 5 seconds

# Camera operations
photo = hal.capture_photo()
hal.start_video_recording(30)  # 30 FPS
video = hal.stop_video_recording()

# System status
status = hal.get_system_status()
power = hal.get_power_consumption()
```

### Hardware Components

- **CPU**: Multi-core simulation with dynamic frequency scaling
- **Memory**: Realistic allocation/deallocation with performance metrics
- **Audio**: Speakers and microphone with format support
- **Camera**: Photo capture and video recording simulation
- **Storage**: Read/write operations with performance characteristics

## 🌐 Network Emulation

Simulate various network conditions and interfaces:

```python
from emulation.network import NetworkEmulator

network = NetworkEmulator()
await network.start_emulation(config)

# Connect to WiFi
await network.connect_interface("wlan0", "Test Network")

# Simulate poor conditions
network.set_network_conditions(
    "wlan0",
    bandwidth_mbps=1.0,
    latency_ms=500,
    packet_loss_percent=5.0
)

# Simulate network outage
network.simulate_network_outage("wlan0", duration_seconds=10)
```

### Network Types

- **WiFi**: 2.4GHz/5GHz with various speed profiles
- **Cellular**: 3G, 4G LTE, 5G with realistic latency/bandwidth
- **Ethernet**: Gigabit and other wired connections
- **Bluetooth**: Low-energy and classic Bluetooth
- **Loopback**: Local connections

## 📡 Sensor Simulation

Realistic sensor data generation:

```python
from emulation.sensors import SensorEmulator

sensors = SensorEmulator()
await sensors.start_simulation(config)

# Get sensor values
accelerometer = sensors.get_sensor_values("accelerometer")
gps = sensors.get_sensor_values("gps")

# Simulate motion
sensors.simulate_motion("walking", duration_seconds=30)

# Simulate location change
sensors.simulate_location_change(
    start_lat=37.7749, start_lng=-122.4194,  # San Francisco
    end_lat=37.7849, end_lng=-122.4094,      # Moved north-east
    duration_seconds=60
)
```

### Available Sensors

- **Motion**: Accelerometer, gyroscope, magnetometer
- **Location**: GPS with realistic accuracy simulation
- **Environment**: Barometer, thermometer, humidity
- **Biometric**: Heart rate, step counter
- **Proximity**: Distance and presence detection
- **Orientation**: Device rotation and gravity

## ⚙️ Configuration

### Emulation Configuration

```python
config = EmulationConfig(
    session_id="unique_session_id",
    emulation_type="all",  # "device", "os", "hardware", "network", "sensor", "all"
    target_platform="android",  # "android", "ios", "windows", "macos", "linux"
    performance_profile="medium",  # "low", "medium", "high", "native"
    resource_limits={
        "memory_mb": 2048,
        "cpu_percent": 50
    },
    audio_enabled=True,
    video_enabled=True,
    network_enabled=True,
    sensor_simulation=True,
    debug_mode=False,
    log_level="INFO"
)
```

### Platform-Specific Configurations

Each target platform automatically configures appropriate:
- Device profiles (screen size, specs, capabilities)
- Sensor availability (mobile vs desktop)
- Network interfaces (cellular for mobile, ethernet for desktop)
- OS environment structure

## 🔍 Monitoring & Debugging

### Session Status

```python
status = engine.get_session_status("session_id")
print(f"State: {status['state']}")
print(f"Uptime: {status['uptime']} seconds")
print(f"CPU Usage: {status['metrics']['cpu_usage']}%")
print(f"Memory Usage: {status['metrics']['memory_usage']}%")
```

### Component Status

```python
# Device status
device_info = device.get_device_info()

# Network status
network_status = network.get_network_status()

# Sensor status
sensor_status = sensors.get_sensor_status()

# Hardware status
hardware_status = hal.get_system_status()
```

## 🎯 Use Cases

### Application Testing
- Test mobile apps across different device configurations
- Simulate various network conditions and connectivity issues
- Test sensor-dependent features like navigation or fitness tracking

### Development & Research
- Prototype IoT device behavior
- Research network protocols under different conditions
- Develop location-based services with simulated movement

### Education & Training
- Learn about mobile device internals
- Understand operating system concepts
- Practice with different hardware configurations

### Performance Testing
- Test application performance under resource constraints
- Simulate high-latency network conditions
- Test battery usage optimization

## 🛠️ Advanced Usage

### Custom Device Profiles

```python
custom_device = await device_emulator.create_device(
    "samsung_galaxy_s24",
    custom_config={
        "ram_mb": 16384,
        "battery_capacity_mah": 5000,
        "sensors": ["accelerometer", "gyroscope", "gps", "heart_rate"]
    }
)
```

### Network Condition Presets

```python
# Simulate mobile network
network.set_network_conditions("cellular0", 
    bandwidth_mbps=10.0, latency_ms=50, packet_loss_percent=1.0)

# Simulate poor WiFi
network.set_network_conditions("wlan0",
    bandwidth_mbps=2.0, latency_ms=200, packet_loss_percent=3.0)
```

### Sensor Event Listeners

```python
def on_sensor_update(sensor_type, values):
    print(f"{sensor_type}: {values}")

sensors.add_sensor_listener("accelerometer", on_sensor_update)
```

## 🔧 Requirements

- Python 3.8+
- asyncio support
- psutil (optional, for resource monitoring)
- Additional dependencies in requirements.txt

## 📝 License

Part of the Marina AI framework. See main project license for details.

## 🤝 Contributing

This emulation framework is part of Marina's AI system. Contributions should follow Marina's development guidelines and consider integration with Marina's brain, sensors, and other components.

## 🔗 Integration with Marina

The emulation framework integrates with:
- **Marina Brain**: For autonomous decision making during tests  
- **Marina Sensors**: For real-world sensor data comparison
- **Marina Memory**: For storing emulation results and patterns
- **Marina Learning**: For improving emulation accuracy

Note: Based on user preference, this framework uses faster-whisper for any audio processing needs instead of google-genai.
