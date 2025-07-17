import enum
from typing import List, Dict, Callable, Any

# Define Strategy Enum
class CycleStrategy(enum.Enum):
    BLITZ = "blitz"
    SPECIALISE_DELEGATE = "specialise_delegate"
    TOP_DOWN_EXHAUSTION = "top_down_exhaustion"
    BOTTOM_UP_EXHAUSTION = "bottom_up_exhaustion"

# Define mock LLM pool for demonstration
LLM_POOL = [
    {"name": "gpt-4o", "strength": 4, "tokens": 128000},
    {"name": "gpt-4", "strength": 3, "tokens": 32000},
    {"name": "gpt-3.5-turbo", "strength": 2, "tokens": 16000},
    {"name": "llama-3-8b", "strength": 1, "tokens": 8000}
]

# Define routing strategies
def blitz_strategy(prompt: str, llms: List[Dict]) -> Dict[str, Any]:
    return {
        "strategy": "BLITZ",
        "description": "Every LLM gets the same prompt. Useful for short, creative, or brainstorming tasks.",
        "routing": [{ "llm": llm["name"], "prompt": prompt } for llm in llms]
    }

def specialise_delegate_strategy(task_description: str, llms: List[Dict]) -> Dict[str, Any]:
    # Placeholder for intelligent task decomposition (would need semantic parsing)
    subtasks = [
        {"task": "data formatting", "strength_required": 1},
        {"task": "summarization", "strength_required": 2},
        {"task": "insight generation", "strength_required": 4}
    ]
    return {
        "strategy": "SPECIALISE_AND_DELEGATE",
        "description": "Assign subtasks to models best suited for them, optionally breaking down tasks for weaker models.",
        "routing": [
            {
                "llm": next(llm["name"] for llm in llms if llm["strength"] >= sub["strength_required"]),
                "subtask": sub["task"]
            } for sub in subtasks
        ]
    }

def top_down_exhaustion_strategy(prompt: str, llms: List[Dict]) -> Dict[str, Any]:
    return {
        "strategy": "TOP_DOWN_EXHAUSTION",
        "description": "Use the best model first. If it fails or exceeds token limits, defer downward.",
        "routing_order": [llm["name"] for llm in sorted(llms, key=lambda x: -x["strength"])],
        "initial_prompt": prompt
    }

def bottom_up_exhaustion_strategy(prompt: str, llms: List[Dict]) -> Dict[str, Any]:
    return {
        "strategy": "BOTTOM_UP_EXHAUSTION",
        "description": "Start from weakest LLM to build a rough stem, improving it up the chain.",
        "routing_order": [llm["name"] for llm in sorted(llms, key=lambda x: x["strength"])],
        "initial_prompt": prompt
    }

# Strategy dispatcher
STRATEGY_MAP: Dict[CycleStrategy, Callable[..., Dict[str, Any]]] = {
    CycleStrategy.BLITZ: blitz_strategy,
    CycleStrategy.SPECIALISE_DELEGATE: specialise_delegate_strategy,
    CycleStrategy.TOP_DOWN_EXHAUSTION: top_down_exhaustion_strategy,
    CycleStrategy.BOTTOM_UP_EXHAUSTION: bottom_up_exhaustion_strategy
}

# Central strategy resolver
def resolve_strategy(strategy: CycleStrategy, prompt_or_description: str, llms=LLM_POOL) -> Dict[str, Any]:
    return STRATEGY_MAP[strategy](prompt_or_description, llms)

# Example test call
if __name__ == "__main__":
    test_prompt = "Generate a risk analysis for Expositin-1 testing based on recent memory logs."
    
    print(">> Blitz Strategy:\n", resolve_strategy(CycleStrategy.BLITZ, test_prompt))
    print("\n>> Specialise & Delegate Strategy:\n", resolve_strategy(CycleStrategy.SPECIALISE_DELEGATE, test_prompt))
    print("\n>> Top Down Exhaustion Strategy:\n", resolve_strategy(CycleStrategy.TOP_DOWN_EXHAUSTION, test_prompt))
    print("\n>> Bottom Up Exhaustion Strategy:\n", resolve_strategy(CycleStrategy.BOTTOM_UP_EXHAUSTION, test_prompt))
