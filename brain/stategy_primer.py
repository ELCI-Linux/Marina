strategy_context = {
    "strategy": "consensus",  # Options: consensus, hierarchy, solo, chained
    "llm_hierarchy": {
        "gemini": {"weight": 0.4, "can_next_prompt": True},
        "openchat": {"weight": 0.3, "can_next_prompt": False},
        "mistral": {"weight": 0.2, "can_next_prompt": False},
        "claude": {"weight": 0.1, "can_next_prompt": True}
    },
    "priority_rules": {
        "next_prompt_supremacy": "gemini",  # or "rotate", "fastest", "highest_score"
        "fallback_if_idle": "openchat"
    },
    "max_recursion_depth": 4,
    "timeout_sec": 60
}
