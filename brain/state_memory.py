import json
import os
from datetime import datetime

MEMORY_FILE = "brain/memory_store.json"

default_memory = {
    "Kr": {"mode": "idle", "focus": "none"},
    "Rp": [],
    "Ks": [],
    "M": [],
    "modal_collapse_log": []
}


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        save_memory(default_memory)
    with open(MEMORY_FILE, 'r') as f:
        return json.load(f)


def save_memory(mem):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(mem, f, indent=2)


def get_current_kr():
    return load_memory()["Kr"]

def get_possible_rp():
    return load_memory()["Rp"]

def get_possible_ks():
    return load_memory()["Ks"]

def get_last_modal_collapse_time():
    mem = load_memory()
    log = mem.get("modal_collapse_log", [])
    if not log:
        return datetime.utcnow()
    return datetime.fromisoformat(log[-1])


def update_kr(new_kr):
    mem = load_memory()
    old_kr = mem["Kr"]
    mem["Kr"] = new_kr
    mem["M"].append(old_kr)
    mem["modal_collapse_log"].append(datetime.utcnow().isoformat())
    save_memory(mem)


def update_rp(new_rp_list):
    mem = load_memory()
    mem["Rp"] = new_rp_list
    save_memory(mem)


def update_ks(new_ks_list):
    mem = load_memory()
    mem["Ks"] = new_ks_list
    save_memory(mem)
