from Marina.brain.state_model import Kr
import math
import random

def compute_modal_weight(current_kr: Kr, candidate_kr: Kr) -> float:
    """
    Computes the modal weight of a candidate Kr branch relative to the current Kr.
    A higher weight means this branch is more likely, more desirable, or more ready.

    Weight is a product of:
    - readiness_score: estimated proximity to actability
    - entropy_score: how much this reduces entropy
    - utility_score: relative value improvement
    - user_alignment_score: how well it fits known user patterns (placeholder)

    Returns:
        float: modal weight (not normalized)
    """

    # --- Component 1: Readiness Score ---
    readiness = readiness_score(candidate_kr)

    # --- Component 2: Entropy Score ---
    entropy_delta = max(0.001, current_kr.entropy - candidate_kr.entropy)
    entropy_score = math.exp(-entropy_delta)  # Less entropy = higher weight

    # --- Component 3: Utility Score ---
    utility_delta = candidate_kr.utility - current_kr.utility
    utility_score = max(0.01, 1 + utility_delta)  # Slight reward for improvement

    # --- Component 4: User Alignment ---
    alignment = user_alignment_score(candidate_kr)  # Placeholder: 0.5–1.0

    # Combine scores
    combined_score = readiness * entropy_score * utility_score * alignment

    return combined_score


def readiness_score(kr: Kr) -> float:
    """
    Estimate readiness based on metadata, description, and entropy.
    Higher readiness = more structured, executable, and relevant state.
    """

    if "wait" in kr.description.lower():
        base = 0.3
    elif "trigger" in kr.description.lower() or "action" in kr.description.lower():
        base = 0.9
    else:
        base = 0.6

    # Modulate based on entropy and recency
    entropy_penalty = math.tanh(kr.entropy)  # ranges from 0 to 1
    readiness = base * (1 - 0.4 * entropy_penalty)

    return round(readiness, 4)


def user_alignment_score(kr: Kr) -> float:
    """
    Estimate how well this Kr aligns with user preference or intention.
    Placeholder: random variation + future hook into user profile model.
    """

    # TODO: Replace with actual memory/model evaluation
    if "invoice" in kr.description.lower():
        return 0.95
    elif "ping" in kr.description.lower():
        return 0.7
    else:
        return random.uniform(0.5, 0.85)
