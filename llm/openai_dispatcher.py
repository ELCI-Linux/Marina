import os
import sys
import openai
import requests

# Add the parent directory to the path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import key_env_loader

# Load environment variables from key files
key_env_loader.load_env_keys(verbose=False)

def run_task_ollama(prompt, model="llama3.2:3b", temperature=0.7):
    """Run task using local Ollama model."""
    try:
        url = 'http://localhost:11434/api/generate'
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get('response', '').strip()
    except Exception as e:
        return f"[ERROR] Local Ollama failed: {e}"

def run_task(prompt, model="gpt-4", temperature=0.7, max_tokens=1000):
    # First try OpenAI API
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        # If OpenAI fails, try local Ollama
        print(f"[OPENAI] API failed ({e}), trying local model...")
        return run_task_ollama(prompt, temperature=temperature)
    
    # If no API key, go straight to local
    print("[OPENAI] No API key, using local model...")
    return run_task_ollama(prompt, temperature=temperature)
