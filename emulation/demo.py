#!/usr/bin/env python3
"""
Marina Emulation Framework Demo
==============================

Demonstrates the capabilities of Marina's comprehensive emulation framework.
Shows device emulation, OS environments, hardware abstraction, networking,
and sensor simulation working together.
"""

import asyncio
import logging
import json
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Marina emulation components
from .core import EmulationEngine, EmulationConfig, EmulationState

async def demo_basic_emulation():
    """Demonstrate basic emulation functionality"""
    logger.info("=== Marina Emulation Framework Demo ===")
    
    # Create emulation engine
    engine = EmulationEngine()
    
    # Create emulation configuration
    config = EmulationConfig(
        session_id="demo_session_001",
        emulation_type="all",  # Enable all emulation types
        target_platform="android",  # Emulate Android device
        performance_profile="medium",
        resource_limits={
            "memory_mb": 2048,
            "cpu_percent": 50
        },
        audio_enabled=True,
        video_enabled=True,
        network_enabled=True,
        sensor_simulation=True,
        debug_mode=True
    )
    
    # Start emulation
    logger.info("Starting emulation session...")
    success = await engine.start_emulation(config)
    
    if success:
        logger.info("✅ Emulation started successfully!")
        
        # Let it run for a while
        await asyncio.sleep(10)
        
        # Get session status
        status = engine.get_session_status(config.session_id)
        if status:
            logger.info(f"Session Status: {json.dumps(status, indent=2, default=str)}")
        
        # Stop emulation
        logger.info("Stopping emulation session...")
        await engine.stop_emulation(config.session_id)
        logger.info("✅ Emulation stopped successfully!")
        
    else:
        logger.error("❌ Failed to start emulation")

async def demo_device_emulation():
    """Demonstrate device emulation capabilities"""
    logger.info("\n=== Device Emulation Demo ===")
    
    from .devices import DeviceEmulator
    
    # Create device emulator
    device_emulator = DeviceEmulator()
    
    # List available device profiles
    profiles = device_emulator.list_available_profiles()
    logger.info(f"Available device profiles: {profiles}")
    
    # Create an iPhone emulator
    device_id = await device_emulator.create_device("iphone_15_pro")
    if device_id:
        logger.info(f"Created device: {device_id}")
        
        # Start the device
        device = device_emulator.get_device(device_id)
        if device:
            await device.start()
            
            # Simulate some interactions
            logger.info("Simulating device interactions...")
            
            # Unlock device
            device.unlock_device("face")
            
            # Launch some apps
            device.launch_app("com.apple.MobilePhone")
            device.launch_app("com.apple.MobileAddressBook")
            
            # Wait to see battery drain and performance metrics
            await asyncio.sleep(5)
            
            # Get device status
            status = device.get_device_info()
            logger.info(f"Device Status: {json.dumps(status, indent=2, default=str)}")
            
            # Stop device
            await device.stop()

async def demo_sensor_simulation():
    """Demonstrate sensor simulation"""
    logger.info("\n=== Sensor Simulation Demo ===")
    
    from .sensors import SensorEmulator
    
    # Create sensor emulator
    sensor_emulator = SensorEmulator()
    
    # Create basic configuration for mobile sensors
    class MockConfig:
        sensor_simulation = True
        target_platform = "android"
    
    config = MockConfig()
    
    # Start sensor simulation
    await sensor_emulator.start_simulation(config)
    
    # List active sensors
    sensors = sensor_emulator.list_sensors()
    logger.info(f"Active sensors: {sensors}")
    
    # Get initial sensor values
    all_values = sensor_emulator.get_all_sensor_values()
    logger.info(f"Initial sensor values: {json.dumps(all_values, indent=2, default=str)}")
    
    # Simulate walking motion
    logger.info("Simulating walking motion for 5 seconds...")
    sensor_emulator.simulate_motion("walking", 5)
    
    await asyncio.sleep(6)
    
    # Get updated sensor values
    all_values = sensor_emulator.get_all_sensor_values()
    logger.info(f"Updated sensor values: {json.dumps(all_values, indent=2, default=str)}")
    
    # Simulate location change
    logger.info("Simulating location change...")
    sensor_emulator.simulate_location_change(
        start_lat=37.7749, start_lng=-122.4194,  # San Francisco
        end_lat=37.7849, end_lng=-122.4094,      # Slightly north-east
        duration_seconds=10
    )
    
    await asyncio.sleep(12)
    
    # Get final sensor values
    all_values = sensor_emulator.get_all_sensor_values()
    logger.info(f"Final sensor values: {json.dumps(all_values, indent=2, default=str)}")
    
    # Stop sensor simulation
    await sensor_emulator.stop_simulation("demo")

async def demo_network_emulation():
    """Demonstrate network emulation"""
    logger.info("\n=== Network Emulation Demo ===")
    
    from .network import NetworkEmulator
    
    # Create network emulator
    network_emulator = NetworkEmulator()
    
    # Create mock configuration
    class MockConfig:
        network_enabled = True
        target_platform = "android"
    
    config = MockConfig()
    
    # Start network emulation
    await network_emulator.start_emulation(config)
    
    # List network interfaces
    interfaces = network_emulator.list_interfaces()
    logger.info(f"Network interfaces: {interfaces}")
    
    # Connect WiFi interface
    if "wlan0" in interfaces:
        await network_emulator.connect_interface("wlan0", "Demo WiFi Network")
        
        # Get interface status
        status = network_emulator.get_interface_status("wlan0")
        logger.info(f"WiFi Status: {json.dumps(status, indent=2, default=str)}")
        
        # Simulate poor network conditions
        logger.info("Simulating poor network conditions...")
        network_emulator.set_network_conditions(
            "wlan0", 
            bandwidth_mbps=1.0, 
            latency_ms=500, 
            packet_loss_percent=5.0
        )
        
        await asyncio.sleep(3)
        
        # Simulate network outage
        logger.info("Simulating network outage for 5 seconds...")
        network_emulator.simulate_network_outage("wlan0", 5)
        
        await asyncio.sleep(7)
    
    # Get overall network status
    network_status = network_emulator.get_network_status()
    logger.info(f"Network Status: {json.dumps(network_status, indent=2, default=str)}")
    
    # Stop network emulation
    await network_emulator.stop_emulation("demo")

async def demo_hardware_abstraction():
    """Demonstrate hardware abstraction layer"""
    logger.info("\n=== Hardware Abstraction Layer Demo ===")
    
    from .hardware import HardwareAbstractionLayer
    
    # Create HAL
    hal = HardwareAbstractionLayer()
    
    # Create mock configuration
    class MockConfig:
        audio_enabled = True
        video_enabled = True
    
    config = MockConfig()
    
    # Initialize HAL
    await hal.initialize(config)
    
    # List hardware components
    components = hal.list_components()
    logger.info(f"Hardware components: {components}")
    
    # Get system status
    system_status = hal.get_system_status()
    logger.info(f"System Status: {json.dumps(system_status, indent=2, default=str)}")
    
    # Test memory allocation
    logger.info("Testing memory allocation...")
    success = hal.allocate_memory(512, "demo_region")
    logger.info(f"Memory allocation {'successful' if success else 'failed'}")
    
    # Test audio playback
    logger.info("Testing audio playback...")
    fake_audio_data = b"fake_audio_data_here"
    success = hal.play_audio(fake_audio_data)
    logger.info(f"Audio playback {'successful' if success else 'failed'}")
    
    # Test photo capture
    logger.info("Testing photo capture...")
    photo_data = hal.capture_photo()
    if photo_data:
        logger.info(f"Photo captured: {photo_data}")
    
    # Get power consumption
    power = hal.get_power_consumption()
    logger.info(f"Total power consumption: {power}W")
    
    # Wait a bit to see hardware metrics
    await asyncio.sleep(5)
    
    # Get updated system status
    system_status = hal.get_system_status()
    logger.info(f"Updated System Status: {json.dumps(system_status, indent=2, default=str)}")
    
    # Cleanup HAL
    await hal.cleanup("demo")

async def demo_os_environment():
    """Demonstrate OS environment emulation"""
    logger.info("\n=== OS Environment Demo ===")
    
    from .os_environments import OSEnvironmentManager
    
    # Create OS environment manager
    os_manager = OSEnvironmentManager()
    
    # List available OS configurations
    configs = os_manager.list_available_configs()
    logger.info(f"Available OS configurations: {configs}")
    
    # Create Android environment
    env_id = await os_manager.create_environment("android_14")
    if env_id:
        logger.info(f"Created OS environment: {env_id}")
        
        # Start the environment
        environment = os_manager.get_environment(env_id)
        if environment:
            await environment.start()
            
            # Wait for system to boot
            await asyncio.sleep(3)
            
            # Get environment status
            status = os_manager.get_environment_status(env_id)
            logger.info(f"OS Environment Status: {json.dumps(status, indent=2, default=str)}")
            
            # Test file system operations
            if environment.file_system:
                logger.info("Testing file system operations...")
                
                # Create a test file
                success = environment.file_system.create_file("test.txt", "Hello Marina!")
                logger.info(f"File creation {'successful' if success else 'failed'}")
                
                # Read the file
                content = environment.file_system.read_file("test.txt")
                logger.info(f"File content: {content}")
                
                # List directory
                files = environment.file_system.list_directory("/")
                logger.info(f"Root directory contents: {files}")
            
            # Stop the environment
            await environment.stop()

async def main():
    """Run all demo functions"""
    try:
        # Run basic emulation demo
        await demo_basic_emulation()
        
        # Run individual component demos
        await demo_device_emulation()
        await demo_sensor_simulation()
        await demo_network_emulation()
        await demo_hardware_abstraction()
        await demo_os_environment()
        
        logger.info("\n🎉 All demos completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
