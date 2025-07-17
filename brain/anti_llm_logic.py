from typing import Optional, Dict, Callable, Any

class AntiLLMLogic:
    def __init__(self):
        self.registry: Dict[str, Dict[str, Any]] = self._default_registry()

    def _default_registry(self) -> Dict[str, Dict[str, Any]]:
        return {
            "file_io": {
                "reason": "Basic read/write operations are deterministic, faster and safer to handle via Python.",
                "prefer": "builtin",
            },
            "datetime_calculation": {
                "reason": "Use `datetime`, `timedelta`, or `pytz` for timezone-safe, reliable operations.",
                "prefer": "programmatic",
            },
            "json_manipulation": {
                "reason": "Structured parsing and validation should use `json` module, not language generation.",
                "prefer": "builtin",
            },
            "regex_parsing": {
                "reason": "LLMs may hallucinate patterns. Regex is safer for deterministic text parsing.",
                "prefer": "re",
            },
            "math_computation": {
                "reason": "Use native math libraries for speed and reliability. LLMs may miscalculate.",
                "prefer": "math, numpy",
            },
            "sorting_filtering": {
                "reason": "Programmatic logic is more efficient and debuggable.",
                "prefer": "lambda/map/filter/sort",
            },
            "env_management": {
                "reason": "Security-critical. Do not use LLMs to generate or modify environment settings.",
                "prefer": "os.environ, dotenv",
            },
            "simple conditionals": {
                "reason": "Avoid LLMs for if/else logic. They're slow, ambiguous, and overkill.",
                "prefer": "native logic",
            },
            "looping_structure": {
                "reason": "Iterative logic should be coded explicitly. LLMs are unreliable in loop construction.",
                "prefer": "for/while",
            },
            "path handling": {
                "reason": "Use `os`, `pathlib` to manage file paths portably and safely.",
                "prefer": "standard lib",
            },
        }

    def should_avoid_llm(self, task: str) -> Optional[Dict[str, Any]]:
        """Returns reasoning and preferred alternative if task should avoid LLMs."""
        return self.registry.get(task)

    def register_task(self, task: str, reason: str, prefer: str):
        self.registry[task] = {
            "reason": reason,
            "prefer": prefer
        }

    def get_registry(self) -> Dict[str, Dict[str, Any]]:
        return self.registry

    def suggest_replacement(self, task: str) -> Optional[str]:
        entry = self.registry.get(task)
        if entry:
            return f"For '{task}', avoid LLMs. Use: {entry['prefer']} — {entry['reason']}"
        return None
