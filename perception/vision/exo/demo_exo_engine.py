#!/usr/bin/env python3
"""
Demo script for the enhanced External Observation Engine
"""

import time
import sys
import os
import cv2
import numpy as np
from exo_engine import ExternalObservationEngine
from observation_engine import ObservationResult


def observation_callback(result: ObservationResult):
    """Callback function to handle observation results"""
    print(f"\n=== Observation Result ===")
    print(f"Timestamp: {result.timestamp}")
    print(f"Source: {result.source}")
    print(f"Confidence: {result.confidence}")
    
    if result.source == "environmental_snapshot":
        print("=== ENVIRONMENTAL SNAPSHOT ===")
        lighting = result.data.get('lighting_analysis', {})
        print(f"Lighting Type: {lighting.get('deduced_lighting_type', 'unknown')}")
        print(f"Brightness: {lighting.get('mean_brightness', 0):.2f}")
        print(f"Conditions: {lighting.get('conditions', [])}")
        
        face_analysis = result.data.get('face_analysis', {})
        print(f"Faces detected: {face_analysis.get('face_count', 0)}")
        print(f"User present: {face_analysis.get('primary_user_present', False)}")
        
        env_features = result.data.get('environmental_features', {})
        print(f"Scene type: {env_features.get('scene_type', 'unknown')}")
        print(f"Motion score: {env_features.get('motion_score', 0):.2f}")
        
    else:
        # Regular frame analysis
        user_data = result.data.get('recognized_user', {})
        print(f"User present: {user_data.get('user_present', False)}")
        print(f"User confidence: {user_data.get('confidence', 0):.2f}")
        print(f"Lighting: {result.data.get('lighting', 'unknown')}")
        print(f"Objects detected: {len(result.data.get('objects', []))}")


def main():
    """Main demo function"""
    print("Starting Enhanced External Observation Engine Demo")
    print("This demo will:")
    print("- Capture webcam feed continuously")
    print("- Take environmental snapshots every 300 seconds")
    print("- Analyze lighting conditions using deductive reasoning")
    print("- Recognize users in the frame")
    print("- Classify scenes and detect environmental features")
    print("\nPress Ctrl+C to stop the demo\n")
    
    # Create the observation engine
    engine = ExternalObservationEngine(camera_index=0)
    
    # Add our callback
    engine.add_callback(observation_callback)
    
    try:
        # Start observation
        engine.start_observation()
        
        # Let it run for a while
        print("Engine started. Observing...")
        
        # For demo purposes, let's simulate some training data
        # In a real implementation, you would collect actual user images
        print("\nTo train user recognition, you would:")
        print("1. Collect multiple face images of the user")
        print("2. Extract face regions using OpenCV")
        print("3. Call engine.train_user_recognition(images, labels)")
        
        # Keep the demo running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping observation engine...")
        engine.stop_observation()
        print("Demo completed.")
    
    except Exception as e:
        print(f"Error during demo: {e}")
        engine.stop_observation()


if __name__ == "__main__":
    main()
