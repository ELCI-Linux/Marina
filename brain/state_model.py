import uuid
import random
import time
from typing import List, Dict, Optional


class Kr:
    """
    Represents a single thermodynamic or cognitive state (Kr) in Marina's reasoning loop.
    Each Kr should be atomic, represent a resolved thought/action/observation snapshot,
    and carry metadata for lineage, entropy, and utility.
    """

    def __init__(
        self,
        description: str,
        parent_id: Optional[str] = None,
        entropy: float = 1.0,
        utility: float = 0.0,
        metadata: Optional[Dict] = None
    ):
        self.id = str(uuid.uuid4())
        self.description = description
        self.timestamp = time.time()
        self.parent_id = parent_id
        self.entropy = entropy  # Uncertainty or disorder in this state
        self.utility = utility  # Expected value of reaching this state
        self.metadata = metadata or {}

    def __repr__(self):
        return f"<Kr {self.id[:8]}: {self.description[:40]}...>"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "timestamp": self.timestamp,
            "parent_id": self.parent_id,
            "entropy": self.entropy,
            "utility": self.utility,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict) -> "Kr":
        return Kr(
            description=data["description"],
            parent_id=data.get("parent_id"),
            entropy=data.get("entropy", 1.0),
            utility=data.get("utility", 0.0),
            metadata=data.get("metadata", {})
        )


def generate_possible_krs(current_kr: Kr, depth: int = 3) -> List[Kr]:
    """
    Generates a list of plausible Kr futures (forked thoughts) from the current Kr.
    These are simulated, not yet resolved, and will later be passed to the LLM for evaluation.

    Parameters:
    - current_kr: the source state
    - depth: number of branches to simulate

    Returns:
    - List of Kr instances
    """
    possibilities = []
    for i in range(depth):
        action = random.choice([
            "Investigate folder contents",
            "Wait for new data",
            "Ping user for instruction",
            "Trigger fallback logic",
            "Parse visible documents",
            "Switch context to external task"
        ])
        new_description = f"{action} (simulated from {current_kr.id[:6]})"
        new_entropy = max(0.1, current_kr.entropy * random.uniform(0.7, 1.3))
        new_utility = current_kr.utility + random.uniform(-0.2, 0.5)

        new_kr = Kr(
            description=new_description,
            parent_id=current_kr.id,
            entropy=new_entropy,
            utility=new_utility,
            metadata={"depth": i}
        )
        possibilities.append(new_kr)
    return possibilities


def collapse_kr(kr_branches: List[Kr]) -> Kr:
    """
    Selects the best Kr from a set of simulated futures.
    This is an early placeholder — in production, we defer to weighted evaluation.

    Currently selects based on highest utility, breaking ties with lowest entropy.

    Parameters:
    - kr_branches: list of resolved Kr instances

    Returns:
    - best Kr
    """
    sorted_branches = sorted(
        kr_branches,
        key=lambda k: (-k.utility, k.entropy)
    )
    return sorted_branches[0] if sorted_branches else None
