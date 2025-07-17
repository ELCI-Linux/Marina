# brain/device_drivers/sandbox_checker.py

import os

def evaluate_environment():
    try:
        with open("/proc/1/cgroup", "r") as f:
            data = f.read()
        if "docker" in data or "lxc" in data:
            return "Sandboxed: Docker or LXC"
        elif os.path.exists("/.dockerenv"):
            return "Sandboxed: Docker"
        else:
            return "Environment appears normal"
    except Exception as e:
        return f"Error checking sandbox status: {e}"
