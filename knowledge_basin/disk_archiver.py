# disk_archiver.py - Scaffold placeholder
import shutil
import os
from pathlib import Path
from datetime import datetime

MEMORY_PATH = Path("~/Marina/brain/memory").expanduser()
ARCHIVE_PATH = Path("~/Marina/brain/offline_archive").expanduser()
ARCHIVE_PATH.mkdir(parents=True, exist_ok=True)

def archive_to_disk(snapshot_filename: str):
    src = MEMORY_PATH / snapshot_filename
    if not src.exists():
        raise FileNotFoundError(f"Snapshot {snapshot_filename} not found.")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = ARCHIVE_PATH / f"archived_{timestamp}_{snapshot_filename}"
    shutil.copy2(src, dst)
    return f"Snapshot {snapshot_filename} archived to {dst}"

def list_archived_snapshots():
    return sorted([f.name for f in ARCHIVE_PATH.glob("*.json")])


def purge_old_archives(keep_latest=5):
    snapshots = list(ARCHIVE_PATH.glob("*.json"))
    snapshots.sort(key=os.path.getmtime, reverse=True)
    for old_file in snapshots[keep_latest:]:
        old_file.unlink()
    return f"Kept {keep_latest} most recent archives."
