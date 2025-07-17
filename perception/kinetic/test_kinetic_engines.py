#!/usr/bin/env python3
"""
Test script for the Marina kinetic perception engines
"""

from kinetic.kinetic_coordinator import KineticCoordinator
from endo.proprioceptive_monitor import ProprioceptiveMonitor
from endo.system_state_tracker import SystemStateTracker
from exo.motion_detector import MotionDetector
from exo.environmental_tracker import EnvironmentalTracker


def test_kinetic_engines():
    """Test the kinetic perception engines"""
    
    print("=== Marina Kinetic Perception Engine Test ===\n")
    
    # Initialize the kinetic coordinator
    coordinator = KineticCoordinator()
    
    # Test unified kinetic data processing
    print("1. Testing unified kinetic data processing:")
    result = coordinator.process_unified_kinetic_data(
        internal_data="Self-movement detected",
        external_data="Environmental motion detected"
    )
    
    for key, value in result.items():
        print(f"   {key}: {value}")
    print()
    
    # Test kinetic status
    print("2. Testing kinetic engine status:")
    status = coordinator.get_kinetic_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    print()
    
    # Test individual components
    print("3. Testing individual perception components:")
    
    # Internal perception components
    print("   Internal (Endo) Components:")
    proprioceptive = ProprioceptiveMonitor()
    system_tracker = SystemStateTracker()
    
    print(f"   - {proprioceptive.get_proprioceptive_input()}")
    print(f"   - {system_tracker.track_system_state()}")
    
    # External perception components
    print("   External (Exo) Components:")
    motion_detector = MotionDetector()
    env_tracker = EnvironmentalTracker()
    
    print(f"   - {motion_detector.detect_motion()}")
    print(f"   - {env_tracker.track_environment()}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    test_kinetic_engines()
