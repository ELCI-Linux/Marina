# watch_folder.py
from mrmr_memory import MRMRMemory
from macro_suggester import MacroSuggester

import os
import json
import time
import threading
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_CONFIG_PATH = Path.home() / "Marina" / ".watching"

class MarinaFolderEventHandler(FileSystemEventHandler):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.actions = config.get("on_event", {})
        self.folder = config["folder"]
        self.memory = MRMRMemory()
        self.suggester = MacroSuggester(self.memory)

    def handle_action(self, event_type, file_path):
        actions = self.actions.get(event_type, [])
        
        # Log Kr
        self.memory.log_kr_event(event_type, file_path)
        
        # Update Rp
        node_key = f"{Path(file_path).suffix}:{event_type}"
        self.memory.update_rp_tree(node_key, {"file": str(file_path)})
        
        # Suggest macro?
        suggestions = self.suggester.suggest_macros()
        for s in suggestions:
            print(f"[🤔] Marina Suggests: {s['action']} (confidence {s['confidence']:.2f})")
        
        for action in actions:
            if action["type"] == "run_macro":
                macro_name = action["macro"]
                subprocess.Popen(["python3", "replay_macro.py", macro_name])
            elif action["type"] == "log":
                print(f"[LOG] {event_type.upper()}: {file_path}")
            elif action["type"] == "move":
                dest = Path(action["destination"]).expanduser()
                dest.mkdir(parents=True, exist_ok=True)
                new_path = dest / Path(file_path).name
                os.rename(file_path, new_path)
                print(f"[MOVE] {file_path} → {new_path}")
            elif action["type"] == "run_command":
                cmd = action["command"].replace("{file}", file_path)
                subprocess.Popen(cmd, shell=True)
            else:
                print(f"[⚠️] Unknown action type: {action['type']}")

    def on_created(self, event):
        if not event.is_directory:
            self.handle_action("created", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.handle_action("modified", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.handle_action("deleted", event.src_path)


def load_watch_configs():
    configs = []
    if not WATCH_CONFIG_PATH.exists():
        print(f"[⚠️] No watch configs found at {WATCH_CONFIG_PATH}")
        return configs

    for json_file in WATCH_CONFIG_PATH.glob("*.json"):
        try:
            with open(json_file) as f:
                config = json.load(f)
                required_keys = ["folder", "on_event"]
                if all(k in config for k in required_keys):
                    configs.append(config)
                else:
                    print(f"[⚠️] Invalid config in {json_file.name}")
        except Exception as e:
            print(f"[❌] Failed to load {json_file.name}: {e}")
    return configs


def start_watch(config):
    folder = Path(config["folder"]).expanduser()
    if not folder.exists():
        print(f"[⚠️] Folder does not exist: {folder}")
        return

    print(f"[👁️] Watching: {folder}")
    event_handler = MarinaFolderEventHandler(config)
    observer = Observer()
    observer.schedule(event_handler, str(folder), recursive=True)
    observer.start()

    return observer


def main():
    observers = []
    configs = load_watch_configs()

    for config in configs:
        observer = start_watch(config)
        if observer:
            observers.append(observer)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[🛑] Stopping all watchers...")
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()
        print("[✅] All watchers stopped.")


if __name__ == "__main__":
    main()
