import os
import json
import platform
import subprocess
from pathlib import Path

def get_system_info():
    try:
        output = subprocess.check_output("neofetch --stdout", shell=True).decode()
    except Exception:
        output = f"OS: {platform.system()} {platform.release()}\nProcessor: {platform.processor()}"
    return output

def scan_file_tree(base_path, mode="inferred", whitelist=None, blacklist=None):
    scanned = {}
    base_path = Path(base_path).expanduser()

    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)

        if blacklist and any(str(root_path).startswith(str(Path(b).expanduser())) for b in blacklist):
            continue
        if whitelist and not any(str(root_path).startswith(str(Path(w).expanduser())) for w in whitelist):
            continue

        if mode == "none":
            continue

        scanned[str(root_path)] = {
            "files": files if mode == "complete" else len(files),
            "dirs": dirs if mode == "complete" else len(dirs)
        }

    return scanned

def save_context(scan_data, output_path="~/Marina/context/init_context.json"):
    context = {
        "system": get_system_info(),
        "scan": scan_data
    }
    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(context, f, indent=2)

def main():
    whitelist = ["~/Documents", "~/Desktop"]
    blacklist = ["~/Downloads"]
    data = scan_file_tree("~/", mode="inferred", whitelist=whitelist, blacklist=blacklist)
    save_context(data)

if __name__ == "__main__":
    main()# contextual_engine.py - Scaffold placeholder
