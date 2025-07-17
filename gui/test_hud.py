#!/usr/bin/env python3
"""
Test script to demonstrate the HUD functionality
"""

import sys
import os
import time
import threading

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from components.hearing_hud import HearingHUD
from themes.themes import ThemeManager
import tkinter as tk

def test_hud_functionality():
    """Test the HUD functionality"""
    
    # Create a test window
    root = tk.Tk()
    root.title("Test HUD Functionality")
    root.geometry("400x300")
    
    # Initialize theme manager
    theme_manager = ThemeManager(root)
    theme_manager.apply_dark_theme()
    
    # Create HUD
    hud = HearingHUD(root, theme_manager)
    
    # Create control buttons
    control_frame = tk.Frame(root)
    control_frame.pack(pady=20)
    
    # Show HUD button
    show_button = tk.Button(
        control_frame,
        text="Show HUD",
        command=hud.show_hud,
        width=15,
        height=2
    )
    show_button.pack(side="left", padx=5)
    
    # Hide HUD button
    hide_button = tk.Button(
        control_frame,
        text="Hide HUD",
        command=hud.hide_hud,
        width=15,
        height=2
    )
    hide_button.pack(side="left", padx=5)
    
    # Demo functions
    def demo_ambient_listening():
        """Demo ambient listening"""
        if hud.is_visible:
            thread = threading.Thread(target=hud.simulate_ambient_listening)
            thread.daemon = True
            thread.start()
    
    def demo_speech_input():
        """Demo speech input"""
        if hud.is_visible:
            thread = threading.Thread(target=hud.simulate_speech_input, args=("Hello Marina, can you help me with my project?",))
            thread.daemon = True
            thread.start()
    
    def demo_command_input():
        """Demo command input"""
        if hud.is_visible:
            thread = threading.Thread(target=hud.simulate_speech_input, args=("Show me the current weather and tomorrow's forecast",))
            thread.daemon = True
            thread.start()
    
    # Demo buttons
    demo_frame = tk.Frame(root)
    demo_frame.pack(pady=10)
    
    ambient_button = tk.Button(
        demo_frame,
        text="Demo Ambient",
        command=demo_ambient_listening,
        width=15,
        height=2
    )
    ambient_button.pack(side="left", padx=5)
    
    speech_button = tk.Button(
        demo_frame,
        text="Demo Speech",
        command=demo_speech_input,
        width=15,
        height=2
    )
    speech_button.pack(side="left", padx=5)
    
    command_button = tk.Button(
        demo_frame,
        text="Demo Command",
        command=demo_command_input,
        width=15,
        height=2
    )
    command_button.pack(side="left", padx=5)
    
    # Status display
    status_frame = tk.Frame(root)
    status_frame.pack(pady=20)
    
    status_label = tk.Label(status_frame, text="HUD Status: Hidden", font=("Arial", 12))
    status_label.pack()
    
    def update_status():
        """Update status display"""
        status_info = hud.get_status_info()
        status_text = f"""HUD Status: {'Visible' if status_info['is_visible'] else 'Hidden'}
Listening: {'Yes' if status_info['is_listening'] else 'No'}
Processing: {'Yes' if status_info['is_processing'] else 'No'}
Confidence: {status_info['confidence_level']:.1%}
Audio Buffer: {status_info['audio_buffer_size']} samples
Current Input: {status_info['current_input'][:50]}{'...' if len(status_info['current_input']) > 50 else ''}"""
        
        status_label.config(text=status_text)
        root.after(1000, update_status)  # Update every second
    
    # Start status updates
    update_status()
    
    # Instructions
    instructions = tk.Label(
        root,
        text="Instructions:\n1. Click 'Show HUD' to display the hearing interface\n2. Use demo buttons to test different scenarios\n3. Watch the HUD for real-time audio feedback",
        justify="left",
        font=("Arial", 10)
    )
    instructions.pack(pady=10)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    test_hud_functionality()
