from flask import Flask, jsonify
import os
import json
from pathlib import Path

app = Flask(__name__)

STATUS_FILE = Path.home() / "Marina" / "logs" / "status.json"
LOGS_DIR = Path.home() / "Marina" / "logs"

def load_status():
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as f:
            return json.load(f)
    return {"status": "unknown", "tasks": []}

def load_recent_logs(limit=10):
    logs = []
    if LOGS_DIR.exists():
        files = sorted(LOGS_DIR.glob("*.log"), reverse=True)[:limit]
        for file in files:
            with open(file) as f:
                logs.append({"file": file.name, "content": f.read()[:200]})
    return logs

@app.route("/api/status")
def status():
    return jsonify(load_status())

@app.route("/api/logs")
def logs():
    return jsonify(load_recent_logs())

if __name__ == "__main__":
    app.run(debug=True)
