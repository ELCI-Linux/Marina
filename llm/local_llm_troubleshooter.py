# local_llm_troubleshooter.py

import requests
import subprocess
import socket
import time

DEFAULT_PORTS = {
    "ollama": 11434,
    "deepseek": 11434,  # Adjust if using custom ports
}

TIMEOUT = 5


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(TIMEOUT)
        try:
            sock.connect((host, port))
            return True
        except (socket.timeout, ConnectionRefusedError):
            return False


def ping_llm_endpoint(name: str, port: int) -> bool:
    try:
        response = requests.get(f"http://localhost:{port}", timeout=TIMEOUT)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[{name.upper()}] Connection error: {e}")
        return False


def restart_ollama():
    print("Attempting to restart Ollama server...")
    subprocess.run(["pkill", "-f", "ollama"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    subprocess.Popen(["ollama", "serve"])
    print("Ollama restarted.")


def check_and_fix(name: str, port: int):
    print(f"\n== Checking {name.upper()} on port {port} ==")

    if not is_port_open("localhost", port):
        print(f"[ERROR] Port {port} not open for {name}.")
        if name == "ollama":
            restart_ollama()
        else:
            print(f"[FIXME] No auto-restart defined for '{name}'. Please start it manually.")
        return

    if not ping_llm_endpoint(name, port):
        print(f"[ERROR] {name} is not responding correctly on port {port}.")
        if name == "ollama":
            restart_ollama()
        else:
            print(f"[WARN] Manual check required for '{name}' (e.g., logs or misconfiguration).")
    else:
        print(f"[OK] {name} is active and responding correctly.")


def run_full_diagnostic():
    print("\n====== LOCAL LLM TROUBLESHOOTER ======")
    for name, port in DEFAULT_PORTS.items():
        check_and_fix(name, port)
    print("\n[COMPLETE] Diagnostic finished. Check logs for details.")


if __name__ == "__main__":
    run_full_diagnostic()
