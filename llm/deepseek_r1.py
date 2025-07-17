# llm/deepseek_r1.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import key_manager

import requests

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def query_deepseek(prompt, model="deepseek-chat", temperature=0.7):
    """Query DeepSeek API with a prompt and return the response."""
    try:
        # Get API key from key manager
        api_key = key_manager.get_key("deepseek_r1")
        if not api_key:
            return "[ERROR] Missing DeepSeek API key (~/Marina/.keys/deepseek_r1_key)."
        
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
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
        
    except requests.exceptions.RequestException as e:
        return f"[ERROR] DeepSeek API request failed: {e}"
    except KeyError as e:
        return f"[ERROR] DeepSeek API response format error: {e}"
    except Exception as e:
        return f"[ERROR] DeepSeek failed: {e}"
