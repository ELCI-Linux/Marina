import os
import base64
import json
from pathlib import Path
from datetime import datetime

SAVE_DIR = Path("~/Marina/outputs").expanduser()
SAVE_DIR.mkdir(parents=True, exist_ok=True)

def generate_filename(base="gemini_output", ext=".txt"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return SAVE_DIR / f"{base}_{timestamp}{ext}"

def save_text(content, base="gemini_output"):
    path = generate_filename(base, ".txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[GEMINI] Text response saved to: {path}")
    return str(path)

def save_json(data, base="gemini_output"):
    path = generate_filename(base, ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[GEMINI] JSON response saved to: {path}")
    return str(path)

def save_code(code, language="python", base="gemini_script"):
    ext = {
        "python": ".py", "javascript": ".js", "html": ".html",
        "bash": ".sh", "c": ".c", "cpp": ".cpp"
    }.get(language.lower(), ".txt")
    path = generate_filename(base, ext)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"[GEMINI] Code saved to: {path}")
    return str(path)

def save_image_from_base64(base64_data, ext=".png", base="gemini_image"):
    path = generate_filename(base, ext)
    with open(path, "wb") as f:
        f.write(base64.b64decode(base64_data))
    print(f"[GEMINI] Image saved to: {path}")
    return str(path)
