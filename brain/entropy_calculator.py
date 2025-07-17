from datetime import datetime
import math
from brain.state_memory import get_last_modal_collapse_time

def entropy_distance(kr, rp):
    """Deviation of current state from probabilistic reality"""
    if not rp:
        return 1.0
    mismatches = 0
    total = len(rp)
    for p in rp:
        for key in kr:
            if key in p and p[key] != kr[key]:
                mismatches += 1
    return mismatches / (total * len(kr)) if total else 0

def entropy_ks_gap(rp, ks):
    if not ks:
        return 0.0
    return (len(ks) - len(rp)) / len(ks)

def entropy_time_delta():
    delta = datetime.utcnow() - get_last_modal_collapse_time()
    return delta.total_seconds() / 60.0  # in minutes

def estimate_entropy(kr, rp, ks):
    eta_1, eta_2, eta_3 = 0.4, 0.3, 0.3

    d_kr_rp = entropy_distance(kr, rp)
    gap_ks = entropy_ks_gap(rp, ks)
    delta_t = entropy_time_delta()
    normalized_time = 1 - math.exp(-delta_t / 10)

    entropy_score = (
        eta_1 * d_kr_rp +
        eta_2 * gap_ks +
        eta_3 * normalized_time
    )
    return round(entropy_score, 4)
