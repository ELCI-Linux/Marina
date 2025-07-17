# core/TTS.py

import wave
from google import genai
from google.genai import types

# === Setup ===
client = genai.Client()

# === Wave File Utility ===
def save_wave(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

# === Single Speaker TTS ===
def speak_single(text: str, voice_name="Kore", filename="out.wav"):
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=f"{text}",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
        ),
    )
    data = response.candidates[0].content.parts[0].inline_data.data
    save_wave(filename, data)
    return filename

# === Multi-Speaker TTS ===
def speak_conversation(script: str, speaker_voices: dict, filename="out.wav"):
    """
    script: A string where each speaker's name is clearly marked.
    speaker_voices: Dict of {speaker_name: voice_name}.
    """
    speaker_configs = [
        types.SpeakerVoiceConfig(
            speaker=speaker,
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice
                )
            ),
        )
        for speaker, voice in speaker_voices.items()
    ]

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=script,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=speaker_configs
                )
            ),
        ),
    )
    data = response.candidates[0].content.parts[0].inline_data.data
    save_wave(filename, data)
    return filename

# === Example Usage ===
if __name__ == "__main__":
    # Single speaker
    speak_single("Say cheerfully: Have a wonderful day!", voice_name="Zephyr")

    # Multi-speaker
    dialogue = """Joe: How's it going today Jane?\nJane: Not too bad, how about you?"""
    voices = {"Joe": "Kore", "Jane": "Puck"}
    speak_conversation(dialogue, voices)
