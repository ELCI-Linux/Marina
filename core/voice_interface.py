# voice_interface.py - Scaffold placeholder
# core/voice_interface.py
import speech_recognition as sr

def listen_and_transcribe():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
    return r.recognize_google(audio)
