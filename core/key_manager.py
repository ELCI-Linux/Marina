import os
from pathlib import Path

KEY_DIR = Path("~/Marina/.keys").expanduser()
KEY_CACHE = {}

def load_keys():
    global KEY_CACHE
    KEY_CACHE.clear()

    if not KEY_DIR.exists():
        KEY_DIR.mkdir(parents=True, exist_ok=True)
        return

    for file in KEY_DIR.glob("*_key"):
        service = file.stem.replace("_key", "").lower()
        try:
            with open(file, 'r') as f:
                KEY_CACHE[service] = f.read().strip()
        except Exception as e:
            print(f"[KEY_MANAGER] Failed to load {file.name}: {e}")

def get_key(service_name):
    service_name = service_name.lower()
    if not KEY_CACHE:
        load_keys()
    return KEY_CACHE.get(service_name, None)
