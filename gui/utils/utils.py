# utils.py
import os
import subprocess
import sys

# Utility function to set up paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Function to load environment keys
from core import key_env_loader
key_env_loader.load_env_keys(verbose=True)

# Function to detect GPU

def detect_gpu():
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            gpu_name = result.stdout.strip()
            return True, gpu_name
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return False, None

