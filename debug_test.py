#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk

def test_basic_widgets():
    print("Creating root window...")
    root = tk.Tk()
    root.title("Debug Test")
    root.geometry("400x300")
    
    print("Creating frame...")
    frame = ttk.Frame(root)
    frame.pack(fill="x", padx=5, pady=5)
    
    print("Creating StringVar...")
    test_var = tk.StringVar(value="test")
    
    print("Creating ttk.Combobox...")
    try:
        combo = ttk.Combobox(
            frame,
            textvariable=test_var,
            values=["option1", "option2", "option3"],
            state="readonly",
            width=20
        )
        print("Combobox created successfully")
        combo.pack(side="left")
        print("Combobox packed successfully")
    except Exception as e:
        print(f"Error creating combobox: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("Creating other widgets...")
    
    # Test other ttk widgets
    try:
        label = ttk.Label(frame, text="Test Label")
        label.pack(side="left", padx=10)
        print("Label created successfully")
    except Exception as e:
        print(f"Error creating label: {e}")
        import traceback
        traceback.print_exc()
        return
    
    try:
        button = ttk.Button(frame, text="Test Button")
        button.pack(side="left", padx=10)
        print("Button created successfully")
    except Exception as e:
        print(f"Error creating button: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("All widgets created successfully. Starting mainloop...")
    root.mainloop()

if __name__ == "__main__":
    test_basic_widgets()
