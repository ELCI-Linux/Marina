import openai
import requests
import json
from your_local_model import run_local_model  # e.g., DeepSeek or Mistral

def send_to_llm(model, prompt, max_tokens=1024):
    if model == "gpt":
        return openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )["choices"][0]["message"]["content"]

    elif model == "claude":
        response = requests.post("https://api.anthropic.com/v1/messages", headers={
            "x-api-key": "YOUR_ANTHROPIC_KEY",
            "Content-Type": "application/json"
        }, json={
            "model": "claude-3-opus-20240229",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        })
        return response.json()["content"]

    elif model == "gemini":
        response = requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            params={"key": "YOUR_GOOGLE_API_KEY"},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

    elif model == "deepseek":
        return run_local_model(prompt)

    else:
        raise ValueError(f"Unknown model: {model}")
