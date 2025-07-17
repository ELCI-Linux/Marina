import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import key_manager

import requests

def send_to_deepseek_ollama(prompt, model="deepseek-r1:7b", temperature=0.7):
    """Send a prompt to local DeepSeek via Ollama."""
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
        return f"[ERROR] Local DeepSeek failed: {e}"

def send_to_deepseek(prompt, model="deepseek-chat", temperature=0.7):
    """Send a prompt to DeepSeek API with local fallback."""
    # First try the API
    try:
        # Try to get the API key from key manager
        api_key = key_manager.get_key("deepseek_r1")
        if api_key:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result["choices"][0]["message"]["content"].strip()
            
    except requests.exceptions.RequestException as e:
        # If API fails, try local Ollama
        print(f"[DEEPSEEK] API failed ({e}), trying local model...")
        return send_to_deepseek_ollama(prompt, temperature=temperature)
    except Exception as e:
        # If API fails, try local Ollama
        print(f"[DEEPSEEK] API failed ({e}), trying local model...")
        return send_to_deepseek_ollama(prompt, temperature=temperature)
    
    # If no API key, go straight to local
    print("[DEEPSEEK] No API key, using local model...")
    return send_to_deepseek_ollama(prompt, temperature=temperature)
