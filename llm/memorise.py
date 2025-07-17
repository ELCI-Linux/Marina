import json
import os
from datetime import datetime

# File path for memory storage
MEMORY_FILE = "marina_memory_log.json"

# Ensure the file exists
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump([], f, indent=2)

def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def timestamp():
    return datetime.utcnow().isoformat() + "Z"

def record_user_prompt(prompt_text, response_text):
    """Log a user-generated prompt and Marina's response."""
    memory = load_memory()
    memory.append({
        "timestamp": timestamp(),
        "origin": "user",
        "prompt": prompt_text,
        "response": response_text
    })
    save_memory(memory)

def record_marina_prompt(prompt_text):
    """Log a self-generated Marina prompt (no user input)."""
    memory = load_memory()
    memory.append({
        "timestamp": timestamp(),
        "origin": "marina",
        "prompt": prompt_text
    })
    save_memory(memory)

