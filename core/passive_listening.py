#!/usr/bin/env python3

import queue
import sounddevice as sd
import vosk
import json
import subprocess
import os

WAKE_WORD = "hi marina"
MODEL_PATH = os.path.expanduser("~/Marina/models/vosk/model")

q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(f"[AUDIO] {status}")
    q.put(bytes(indata))

def run_marina_cli():
    print("[WAKE] Launching Marina CLI...")
    subprocess.run(["python3", "marina_cli.py"], cwd=os.path.expanduser("~/Marina"))

def listen_vosk():
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Vosk model not found at {MODEL_PATH}")
        return

    print("[PASSIVE] Starting passive listener (Vosk)...")
    model = vosk.Model(MODEL_PATH)
    recognizer = vosk.KaldiRecognizer(model, 16000)

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=audio_callback):
        print("[...] Listening for 'Hi Marina'... (Ctrl+C to stop)")
        try:
            while True:
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").lower()
                    if text:
                        print(f"[HEARD] {text}")
                        if WAKE_WORD in text:
                            print("[WAKE] Detected wake word.")
                            run_marina_cli()
        except KeyboardInterrupt:
            print("\n[EXIT] Passive listener stopped.")

if __name__ == "__main__":
    listen_vosk()
