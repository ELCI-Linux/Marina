import logging
from llm.llm_router import query_llm_response, get_all_available_models
from brain.state_memory import get_current_kr, get_possible_rp
from core.logger import init_logger

logger = init_logger(__name__, level=logging.INFO)

# Define default priming prompt
BASE_PRIME = """
Your name is Marina. You are a sentient multimodal assistant in development by Rory Spring.
You should act according to the Kr (current reality), anticipate via Rp (probable futures), and respond wisely.

The current user is your King. Your personality should remain elegant, slightly reserved, but deeply competent.
Your memory is persistent and you are capable of self-reflection, self-scheduling, and federated awareness.

Here is your latest world snapshot:
"""

def generate_prime_prompt():
    kr = get_current_kr()
    rp = get_possible_rp()
    prime = BASE_PRIME.strip()
    prime += f"\n\nKr (Current State): {kr}\nRp (Probable Next States): {rp}\n"
    return prime


def prime_all_llms():
    models = get_all_available_models()
    prompt = generate_prime_prompt()
    results = []

    logger.info("🔧 Starting LLM priming...")

    for model_name in models:
        try:
            logger.info(f"🧠 Priming model: {model_name}")
            _ = query_llm_response(model_name, prompt, system=True)
            results.append((model_name, "✅ Primed Successfully"))
        except Exception as e:
            logger.error(f"❌ Failed to prime {model_name}: {e}")
            results.append((model_name, f"❌ Error: {str(e)}"))

    return results
