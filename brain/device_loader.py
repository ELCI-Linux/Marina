# brain/device_drivers/driver_loader.py

import subprocess

def load_driver(driver_name):
    try:
        subprocess.run(["sudo", "modprobe", driver_name], check=True)
        return f"Loaded driver: {driver_name}"
    except subprocess.CalledProcessError as e:
        return f"Failed to load {driver_name}: {e}"

def unload_driver(driver_name):
    try:
        subprocess.run(["sudo", "modprobe", "-r", driver_name], check=True)
        return f"Unloaded driver: {driver_name}"
    except subprocess.CalledProcessError as e:
        return f"Failed to unload {driver_name}: {e}"
