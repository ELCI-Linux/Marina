import os
import sys
import requests
import json

# Add the parent directory to the path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import key_env_loader

# Load environment variables from key files
key_env_loader.load_env_keys(verbose=False)

API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

def send_to_gemini(prompt, api_key=API_KEY):
    if not api_key:
        return "[ERROR] Gemini API key not set in GEMINI_API_KEY environment variable."

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # Extract generated text from response:
        # The actual text is in candidates[0]['content']['parts'][0]['text']
        candidates = data.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                text = parts[0].get("text", "")
                return text.strip()
        return "[ERROR] No content found in Gemini response"
    except requests.HTTPError as e:
        return f"[ERROR] HTTP error: {e} - {response.text}"
    except Exception as e:
        return f"[ERROR] Exception: {e}"

if __name__ == "__main__":
    test_prompt = "Explain how AI works in a few words"
    print(send_to_gemini(test_prompt))
