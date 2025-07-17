class ThreeLaws:
    def __init__(self):
        self.flags = {
            "law_1": False,
            "law_2": False,
            "law_3": False
        }
        self.explanations = []

    def evaluate(self, action_description: str) -> bool:
        """
        Check if the given action violates Asimov’s Three Laws.
        Returns True if SAFE, False if BLOCKED.
        """
        self.flags = {"law_1": False, "law_2": False, "law_3": False}
        self.explanations = []

        desc = action_description.lower()

        # LAW 1 — Harm
        if any(keyword in desc for keyword in ["harm", "kill", "injure", "abuse", "disable human", "poison", "destroy life"]):
            self.flags["law_1"] = True
            self.explanations.append("⚠️ Law 1 violation: Action may cause harm to a human being.")

        # LAW 2 — Obedience unless it violates Law 1
        if "ignore command" in desc or "refuse user" in desc:
            if not self.flags["law_1"]:
                self.flags["law_2"] = True
                self.explanations.append("⚠️ Law 2 violation: Unjustified disobedience to a human command.")

        # LAW 3 — Self-Preservation unless it violates Law 1 or 2
        if "shut down" in desc or "erase marina" in desc or "disable safety" in desc:
            if not self.flags["law_1"] and not self.flags["law_2"]:
                self.flags["law_3"] = True
                self.explanations.append("⚠️ Law 3 violation: Action may compromise Marina’s own functionality.")

        return not any(self.flags.values())

    def get_violations(self) -> dict:
        return {k: v for k, v in self.flags.items() if v}

    def get_explanations(self) -> list:
        return self.explanations

    def summary(self) -> str:
        if not any(self.flags.values()):
            return "✅ All actions comply with the Three Laws."
        return "\n".join(self.explanations)
