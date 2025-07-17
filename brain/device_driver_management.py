import os
import platform
import subprocess
import json

class DeviceDriverManager:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.devices = {}

    def detect_devices(self):
        if self.os_type == "linux":
            return self._detect_linux_devices()
        elif self.os_type == "windows":
            return self._detect_windows_devices()
        else:
            return {"error": f"{self.os_type} not supported yet"}

    def _detect_linux_devices(self):
        try:
            usb = subprocess.check_output("lsusb", shell=True).decode()
            audio = subprocess.check_output("arecord -l", shell=True).decode()
            video = subprocess.check_output("v4l2-ctl --list-devices", shell=True).decode()
            self.devices = {
                "usb": usb.strip().split('\n'),
                "audio": audio.strip().split('\n'),
                "video": video.strip().split('\n')
            }
            return self.devices
        except Exception as e:
            return {"error": str(e)}

    def _detect_windows_devices(self):
        # Future expansion using WMI or PowerShell
        return {"windows": "device detection not implemented yet"}

    def enable_device(self, device_name):
        # Stub: OS-specific logic to re-enable or reload a device
        return f"Enable command issued for {device_name}"

    def disable_device(self, device_name):
        # Stub: OS-specific logic to disable or unbind a driver
        return f"Disable command issued for {device_name}"

    def list_available(self):
        return self.devices or self.detect_devices()

    def export_json(self, path="~/Marina/memory/devices.json"):
        try:
            path = os.path.expanduser(path)
            with open(path, "w") as f:
                json.dump(self.devices, f, indent=2)
            return f"Exported to {path}"
        except Exception as e:
            return f"Export error: {e}"
