import json
import os
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path("~/Marina/brain/memory").expanduser()
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

LATEST_PATH = MEMORY_DIR / "latest.json"

# Save a memory snapshot with optional tag

def archive_memory(snapshot: dict, tag: str = "auto"):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = MEMORY_DIR / f"{tag}_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(snapshot, f, indent=2)
    with open(LATEST_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)
    return str(filename)

# Load most recent memory

def load_latest_memory():
    if not LATEST_PATH.exists():
        return {}
    with open(LATEST_PATH) as f:
        return json.load(f)

# Search for memory snapshots matching a tag

def search_memory(tag="auto"):
    return sorted([f.name for f in MEMORY_DIR.glob(f"{tag}_*.json")])
