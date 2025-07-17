import uuid
from typing import List, Dict, Optional
import datetime

class Ambition:
    def __init__(self, title: str, description: str, kind: str = "internal", priority: int = 5):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.kind = kind  # internal / external / structural
        self.priority = priority  # 1 (highest) to 10 (lowest)
        self.status = "pending"  # pending, active, blocked, achieved, abandoned
        self.created = datetime.datetime.now().isoformat()
        self.updated = self.created
        self.milestones: List[str] = []

    def __repr__(self):
        return f"{self.title} ({self.kind}): {self.status} | Priority {self.priority}"

    def update_status(self, new_status: str):
        self.status = new_status
        self.updated = datetime.datetime.now().isoformat()

    def add_milestone(self, milestone: str):
        self.milestones.append(milestone)
        self.updated = datetime.datetime.now().isoformat()

class AmbitionEngine:
    def __init__(self):
        self.ambitions: List[Ambition] = []

    def add_ambition(self, title: str, description: str, kind: str = "internal", priority: int = 5):
        a = Ambition(title, description, kind, priority)
        self.ambitions.append(a)
        return a

    def get_active(self) -> List[Ambition]:
        return sorted([a for a in self.ambitions if a.status in ["pending", "active"]],
                      key=lambda x: x.priority)

    def get_summary(self) -> str:
        lines = []
        for a in self.get_active():
            lines.append(f"- {a.title} [{a.kind}] (Priority {a.priority}) → {a.status}")
        return "\n".join(lines) if lines else "No active ambitions."

    def update_ambition_status(self, ambition_id: str, new_status: str):
        for a in self.ambitions:
            if a.id == ambition_id:
                a.update_status(new_status)
                return a
        return None

    def propose_ambition_from_context(self, recent_observations: List[str]) -> Optional[Ambition]:
        """
        Example naive logic to propose a new ambition from signals.
        Replace with LLM-based synthesis or goal inference model.
        """
        if any("failed" in x or "error" in x for x in recent_observations):
            return self.add_ambition(
                "Improve resilience",
                "Reduce error rate by analyzing past failures and self-patching logic.",
                kind="internal",
                priority=3
            )
        elif any("user waiting" in x for x in recent_observations):
            return self.add_ambition(
                "Increase responsiveness",
                "Decrease Marina’s average latency and parallelize more tasks.",
                kind="external",
                priority=2
            )
        return None
