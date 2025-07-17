# macro_suggester.py

from collections import Counter
from pathlib import Path

class MacroSuggester:
    def __init__(self, mrmr_memory):
        self.memory = mrmr_memory

    def suggest_macros(self):
        kr_events = self.memory.get_recent_kr(25)
        file_types = [Path(e["file"]).suffix for e in kr_events if "file" in e]

        common_ext = Counter(file_types).most_common(1)
        if not common_ext:
            return []

        ext, _ = common_ext[0]
        rp = self.memory.get_rp_tree()

        suggestions = []
        for key, node in rp.items():
            if ext in key and node["confidence"] > 0.6:
                suggestions.append({
                    "macro_type": "auto_macro",
                    "action": f"Apply macro for {ext}",
                    "node_key": key,
                    "confidence": node["confidence"]
                })

        return suggestions
