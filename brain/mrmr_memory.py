# mrmr_memory.py

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

MEMORY_PATH = Path.home() / "Marina" / ".memory"
MEMORY_PATH.mkdir(parents=True, exist_ok=True)

KR_LOG = MEMORY_PATH / "kr_log.json"
RP_TREE = MEMORY_PATH / "rp_tree.json"


class MRMRMemory:
    def __init__(self):
        self.kr = self._load(KR_LOG, [])
        self.rp = self._load(RP_TREE, {})

    def _load(self, path, default):
        if not path.exists():
            return default
        with open(path) as f:
            return json.load(f)

    def _save(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def log_kr_event(self, event_type, file_path, extra=None):
        entry = {
            "event_type": event_type,
            "file": str(file_path),
            "time": datetime.utcnow().isoformat(),
            "meta": extra or {}
        }
        self.kr.append(entry)
        self._save(KR_LOG, self.kr)

    def update_rp_tree(self, node_key, evidence):
        node = self.rp.get(node_key, {"evidence": [], "confidence": 0.5})
        node["evidence"].append(evidence)
        node["confidence"] = min(1.0, node["confidence"] + 0.05)
        self.rp[node_key] = node
        self._save(RP_TREE, self.rp)

    def get_rp_tree(self):
        return self.rp

    def get_recent_kr(self, limit=10):
        return self.kr[-limit:]
