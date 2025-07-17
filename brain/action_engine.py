import subprocess
import shlex
import os
import sys
from io import StringIO
import contextlib

# Map common aliases to standard shell commands
COMMAND_ALIASES = {
    "dir": "ls",
    "list": "ls",
    "remove": "rm",
    "copy": "cp",
    "move": "mv",
    "make": "mkdir",
    "clone": "git clone",
    "update": "apt update",
    "install": "apt install",
    "pip install": "pip install",
    "who": "whoami",
    "where": "pwd",
    "cd": "cd",
    "run": "",  # pass-through
}


def normalize_command(command):
    tokens = shlex.split(command)
    if not tokens:
        return []

    primary = tokens[0]
    rest = tokens[1:]

    # Handle specific multi-word aliases like "pip install"
    if primary == "pip" and rest and rest[0] == "install":
        normalized = "pip install"
        rest = rest[1:]
    else:
        normalized = COMMAND_ALIASES.get(primary, primary)

    return shlex.split(normalized) + rest


def execute_command(command_line):
    normalized_command = normalize_command(command_line)

    if not normalized_command:
        return "No command provided.", ""

    # Special handling for `cd`, which doesn't persist across subprocess
    if normalized_command[0] == "cd":
        if len(normalized_command) < 2:
            return "", "Usage: cd <directory>"
        try:
            os.chdir(normalized_command[1])
            return f"Changed directory to {os.getcwd()}", ""
        except Exception as e:
            return "", f"cd error: {e}"

    try:
        result = subprocess.run(
            normalized_command,
            capture_output=True,
            text=True,
            shell=False
        )
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", f"Execution failed: {e}"


def run_action_command(command_line):
    """
    Executes a shell command string and returns (stdout, stderr).
    Designed for integration into GUIs or other apps.
    """
    stdout, stderr = execute_command(command_line)
    return stdout, stderr


# Optional CLI usage
if __name__ == "__main__":
    print("Interactive Action Engine. Type '[action] <command>' or 'exit' to quit.")
    try:
        while True:
            user_input = input(">>> ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if user_input.startswith("[action]"):
                cmd = user_input[len("[action]"):].strip()
                out, err = run_action_command(cmd)
                if out:
                    print(out)
                if err:
                    print(f"[stderr] {err}", file=sys.stderr)
            else:
                print("Ignored: not prefixed with [action]")
    except KeyboardInterrupt:
        print("\nExiting.")
