import re
import subprocess
import uuid
import os
import time
import py_compile
from pathlib import Path
from datetime import datetime, timedelta

# Session history of saved files
_saved_files = []

def extract_code_blocks(text):
    pattern = r"```(?:[\w+-]*)\n(.*?)```"
    return [match.strip() for match in re.findall(pattern, text, re.DOTALL)]

def guess_extension(code):
    code_lower = code.lower()
    if "def " in code or "import " in code or "print(" in code:
        return ".py"
    elif "#include" in code or "int main" in code:
        return ".c"
    elif "<html>" in code_lower or "<!doctype html>" in code_lower:
        return ".html"
    elif "<?php" in code_lower:
        return ".php"
    elif "select " in code_lower:
        return ".sql"
    elif "function" in code_lower and "console.log" in code_lower:
        return ".js"
    else:
        return ".txt"

def detect_save_directory(text):
    """
    Detect existing directory paths mentioned in text.
    Append '.temp' suffix to avoid damaging important dirs.
    Fallback to /tmp/gpt_code.temp.
    """
    unix_path_pattern = r"(\/[\/\w\.\-\_]+)"
    windows_path_pattern = r"([a-zA-Z]:\\(?:[\\\w\.\-\_]+)+)"
    relative_path_pattern = r"(\.{1,2}\/[\w\.\-\_\/]+)"

    candidates = re.findall(unix_path_pattern, text) + \
                 re.findall(windows_path_pattern, text) + \
                 re.findall(relative_path_pattern, text)

    candidates = [c for c in candidates if len(c) > 3 and not any(ch in c for ch in ['`','<','>','|','*','?'])]

    for path in candidates:
        norm_path = os.path.expanduser(path)
        if os.path.isdir(norm_path):
            safe_path = norm_path + ".temp"
            os.makedirs(safe_path, exist_ok=True)
            return safe_path

    default_path = "/tmp/gpt_code.temp"
    os.makedirs(default_path, exist_ok=True)
    return default_path

def generate_filename(code, suffix=".txt"):
    """
    Generate human-readable filename based on code content.
    Tries to extract first function or class name.
    Fallback: uuid.
    """
    # Try extracting first def or class name
    match = re.search(r'^\s*(def|class)\s+(\w+)', code, re.MULTILINE)
    if match:
        base_name = match.group(2)
    else:
        base_name = f"code_{uuid.uuid4().hex[:8]}"
    return f"{base_name}{suffix}"

def clean_old_temp_dirs(base_dir="/tmp", days=7):
    """
    Clean temp directories older than `days` days inside base_dir.
    """
    cutoff = time.time() - days * 86400
    base_path = Path(base_dir)
    if not base_path.is_dir():
        return

    for entry in base_path.iterdir():
        if entry.is_dir() and entry.name.startswith("gpt_code") and entry.stat().st_mtime < cutoff:
            try:
                for root, dirs, files in os.walk(entry, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(entry)
                print(f"[🧠 code_detector] Cleaned old temp dir: {entry}")
            except Exception as e:
                print(f"[🧠 code_detector] Failed to clean {entry}: {e}")

def check_python_syntax(filepath):
    """
    Compile python code to check syntax.
    """
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"[🧠 code_detector] Syntax OK: {filepath}")
        return True
    except py_compile.PyCompileError as e:
        print(f"[🧠 code_detector] Syntax ERROR in {filepath}: {e}")
        return False

def save_code_to_file(code, save_dir=None, suffix=".txt"):
    """
    Save code with a generated filename in save_dir.
    """
    if save_dir is None:
        save_dir = "/tmp/gpt_code.temp"
        os.makedirs(save_dir, exist_ok=True)

    filename = generate_filename(code, suffix)
    filepath = os.path.join(save_dir, filename)
    with open(filepath, 'w') as f:
        f.write(code)

    _saved_files.append(filepath)
    return filepath

def open_in_nano(filepath):
    subprocess.run(["nano", filepath])

def interpret_code_from_response(response_text):
    """
    Main entry point.
    Extract code, clean old temp dirs, save files, validate syntax,
    open in nano, and log.
    """
    # Clean old temp dirs weekly
    clean_old_temp_dirs()

    code_blocks = extract_code_blocks(response_text)
    if not code_blocks:
        print("[🧠 code_detector] No code blocks found.")
        return

    save_dir = detect_save_directory(response_text)
    print(f"[🧠 code_detector] Using save directory: {save_dir}")

    for i, code in enumerate(code_blocks):
        suffix = guess_extension(code)
        filepath = save_code_to_file(code, save_dir=save_dir, suffix=suffix)
        print(f"[🧠 code_detector] Code block {i+1} saved to: {filepath}")

        # Syntax check if python
        if suffix == ".py":
            check_python_syntax(filepath)

        open_in_nano(filepath)

def get_saved_files():
    """
    Returns list of all saved files in current session.
    """
    return _saved_files.copy()
