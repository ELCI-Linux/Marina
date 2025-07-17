# macro_recording.py

import json
import datetime
from pathlib import Path


class MacroRecorder:
    def __init__(self, macro_dir="~/.marina_macros/"):
        self.actions = []
        self.recording = False
        self.macro_dir = Path(macro_dir).expanduser()
        self.macro_dir.mkdir(parents=True, exist_ok=True)

    def start(self):
        self.actions = []
        self.recording = True
        print("[🎙️] Macro recording started.")

    def record_action(self, action: str, params: dict):
        if self.recording:
            timestamp = datetime.datetime.utcnow().isoformat()
            self.actions.append({
                "timestamp": timestamp,
                "action": action,
                "params": params
            })
            print(f"[➕] Recorded action: {action} {params}")

    def stop(self):
        self.recording = False
        print("[🛑] Macro recording stopped.")

    def save(self, name=None):
        if not name:
            name = f"macro_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filepath = self.macro_dir / f"{name}.json"
        with open(filepath, "w") as f:
            json.dump(self.actions, f, indent=2)
        print(f"[💾] Macro saved to: {filepath}")
        return filepath

    def load(self, name):
        filepath = self.macro_dir / f"{name}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"Macro '{name}' not found in {self.macro_dir}")
        with open(filepath, "r") as f:
            self.actions = json.load(f)
        print(f"[📂] Macro '{name}' loaded.")
        return self.actions

    def replay(self, controller):
        print("[▶️] Replaying macro...")
        for action in self.actions:
            method = getattr(controller, action["action"], None)
            if method:
                method(**action["params"])
                print(f"[✅] Executed {action['action']} with {action['params']}")
            else:
                print(f"[⚠️] Unknown action: {action['action']}")
