import sys
import os
import subprocess
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import key_manager

import openai
from llm.deepseek_r1 import query_deepseek
from llm import openai_dispatcher, gemini_dispatcher, deepseek_dispatcher

OLLAMA_PORT = 11434

def get_local_ollama_models():
    """Use `ollama list --json` to get available local models."""
    try:
        result = subprocess.run(
            ["ollama", "list", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        models = json.loads(result.stdout)
        # Return list of model names only
        return [m.get("name") for m in models if "name" in m]
    except Exception as e:
        print(f"[llm_router] Failed to get local Ollama models: {e}")
        return []

def route_model(model, prompt):
    if model == "deepseek-r1":
        return query_deepseek(prompt, model="deepseek-chat")
    elif model.startswith("ollama:"):
        # Extract actual model name after 'ollama:'
        ollama_model = model.split(":", 1)[1]
        return query_ollama(prompt, ollama_model)
    # Add other model routing logic here if needed
    return None

def query_ollama(prompt, model='llama3'):
    import requests
    url = f'http://localhost:{OLLAMA_PORT}/api/generate'
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get('response', "[ERROR] No response from Ollama.")
    except Exception as e:
        return f"[ERROR] Ollama request failed: {e}"

def call_gpt(prompt):
    api_key = key_manager.get_key("gpt")
    if not api_key:
        return "[ERROR] Missing GPT key (~/Marina/.keys/gpt_key)."

    openai.api_key = api_key

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"[ERROR] Failed to contact OpenAI: {e}"

def call_gemini(prompt):
    key = key_manager.get_key("gemini")
    if not key:
        return "[ERROR] Missing Gemini API key."
    # Implement Gemini call here
    return "[ERROR] Gemini call not implemented."

def route_task(task, token_estimate, run=False, force_model=None):
    model = None
    result = None

    # Fetch local Ollama models dynamically
    local_ollama_models = get_local_ollama_models()

    # Define model priority order based on token estimate
    if force_model:
        model_priority = [force_model]
    else:
        if token_estimate < 500:
            # Prefer fast local first if available
            if local_ollama_models:
                # Use first available Ollama model with prefix 'ollama:'
                model_priority = [f"ollama:{local_ollama_models[0]}", "deepseek", "gemini", "gpt"]
            else:
                model_priority = ["deepseek", "gemini", "gpt"]
        elif token_estimate > 8000:
            model_priority = ["gemini", "gpt", "deepseek"]
        else:
            model_priority = ["gpt", "gemini", "deepseek"]

    if run:
        for attempt_model in model_priority:
            print(f"[MARINA] Trying {attempt_model}...")

            try:
                if attempt_model.startswith("ollama:"):
                    result = route_model(attempt_model, task)
                elif attempt_model == "deepseek":
                    result = deepseek_dispatcher.send_to_deepseek(task)
                elif attempt_model == "gemini":
                    result = gemini_dispatcher.send_to_gemini(task)
                elif attempt_model == "gpt":
                    result = openai_dispatcher.run_task(task)
                else:
                    continue

                if result and not result.startswith("[ERROR]"):
                    model = attempt_model
                    break
                else:
                    print(f"[MARINA] {attempt_model} failed: {result}")
                    if attempt_model == model_priority[-1]:
                        model = attempt_model
                        break
                    continue

            except Exception as e:
                print(f"[MARINA] {attempt_model} exception: {e}")
                if attempt_model == model_priority[-1]:
                    model = attempt_model
                    result = f"[ERROR] All models failed. Last error: {e}"
                    break
                continue
    else:
        model = model_priority[0] if model_priority else "gpt"

    return model, result
# --- Kr Simulation Extension ---
import asyncio
from Marina.brain.state_model import Kr

async def query_llm_with_kr(kr: Kr) -> Kr:
    """
    Given a candidate Kr state, simulate its resolution using the LLM.
    This function returns a new Kr instance representing the resolved future state.

    It uses the Kr's description as a prompt context and returns a modified Kr with:
    - An updated description
    - Possibly refined entropy / utility
    - Inherited lineage

    This function assumes you're already routing to an LLM like GPT or Claude elsewhere.
    """

    prompt = f"""You are simulating the next stage in an AI decision-making chain.
Current hypothetical state description:
\"\"\"
{kr.description}
\"\"\"

Give a single-line continuation of what happens next if the AI proceeds along this path."""

    # Use your existing LLM router — assume a function like: route_to_llm(prompt, model="gpt-4o")
    response = await route_to_llm(prompt, model="gpt-4o")

    # Construct new Kr from the LLM result
    new_description = response.strip()
    resolved_kr = Kr(
        description=new_description,
        parent_id=kr.id,
        entropy=max(0.05, kr.entropy * 0.9),  # assume simulated branches become more refined
        utility=kr.utility + 0.1,  # optimistic forward gain
        metadata={"simulated": True}
    )

    return resolved_kr

def query_llm_response(llm_name, prompt):
    """Query a specific LLM with a prompt and return the response."""
    llm_mapping = {
        "GPT-4": "gpt",
        "Claude": "claude",  # Not implemented yet
        "Gemini": "gemini",
        "DeepSeek": "deepseek",
        "Mistral": "mistral",  # Not implemented yet
        "LLaMA": "llama",  # Not implemented yet
        "Local": "local"  # Not implemented yet
    }

    internal_model = llm_mapping.get(llm_name, "gpt")

    # For now, only support implemented models
    if internal_model not in ["gpt", "gemini", "deepseek"]:
        return f"[{llm_name}] Not implemented yet."

    # Estimate token count (rough approximation)
    token_estimate = len(prompt.split()) * 1.3

    # Route the task
    model, result = route_task(prompt, token_estimate, run=True, force_model=internal_model)

    if result:
        return result
    else:
        return f"[{llm_name}] No response received."

# Example manual tests
if __name__ == "__main__":
    print("Local Ollama Models:", get_local_ollama_models())
    test_prompt = "Hello, test the LLM routing."
    print("Response:", route_task(test_prompt, len(test_prompt.split()) * 1.3, run=True))

async def route_to_llm(prompt: str, model: str = "gpt-4o") -> str:
    # Replace this with your actual LLM API call (e.g. OpenAI, Anthropic)
    # Simulated response for now:
    return "The AI detects an invoice and begins categorization."
