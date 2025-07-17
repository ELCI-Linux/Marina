import asyncio
import json
import os
import uuid
import time
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from Marina.brain.state_model import Kr, generate_possible_krs, collapse_kr
from Marina.brain.modal_weights import compute_modal_weight
from Marina.llm.llm_router import query_llm_with_kr
from Marina.memory.rp_store import archive_rp_branch

# Configuration
MAX_PARALLEL_THREADS = 5
KR_BRANCH_DEPTH = 3
LOG_DIR = os.path.expanduser("~/Marina/logs/concurrent_thoughts/")
MEMORY_DIR = os.path.expanduser("~/Marina/memory/threads/")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=MAX_PARALLEL_THREADS)

# Utility functions
def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(LOG_DIR, "thread_log.txt"), "a") as f:
        f.write(f"[{ts}] {msg}\n")


async def simulate_branch(kr_candidate: Kr, weight: float) -> Tuple[Kr, float]:
    """Simulates a future Kr branch using the LLM and returns the resolved Kr and its modal weight."""
    try:
        log(f"Simulating branch with Kr ID {kr_candidate.id} and weight {weight:.3f}")
        resolved_kr = await query_llm_with_kr(kr_candidate)
        return resolved_kr, weight
    except Exception as e:
        log(f"Error simulating branch {kr_candidate.id}: {str(e)}")
        return kr_candidate, 0.0  # fallback: invalid weight


async def run_parallel_kr_futures(current_kr: Kr) -> Kr:
    """Forks the current Kr into possible futures and collapses to the best one."""
    kr_candidates = generate_possible_krs(current_kr, depth=KR_BRANCH_DEPTH)
    weight_map = {}

    for kr in kr_candidates:
        weight_map[kr.id] = compute_modal_weight(current_kr, kr)

    # Normalize weights
    total_weight = sum(weight_map.values())
    normalized_weights = {
        k: (v / total_weight if total_weight > 0 else 1 / len(weight_map))
        for k, v in weight_map.items()
    }

    # Run simulations
    futures = [
        simulate_branch(kr, normalized_weights[kr.id])
        for kr in kr_candidates
    ]
    resolved_kr_results = await asyncio.gather(*futures)

    # Pick best outcome
    best_kr, best_weight = max(resolved_kr_results, key=lambda x: x[1])

    log(f"Collapsed to Kr ID {best_kr.id} with weight {best_weight:.3f}")
    archive_concurrent_krs(resolved_kr_results, chosen_id=best_kr.id)
    return best_kr


def archive_concurrent_krs(results: List[Tuple[Kr, float]], chosen_id: str):
    """Store all branches in Rp memory, tagging the collapsed one."""
    archive_path = os.path.join(MEMORY_DIR, f"branches_{uuid.uuid4().hex}.json")
    payload = []
    for kr, weight in results:
        payload.append({
            "kr_id": kr.id,
            "weight": weight,
            "collapsed": (kr.id == chosen_id),
            "timestamp": time.time(),
            "kr_summary": kr.to_dict() if hasattr(kr, "to_dict") else str(kr)
        })
        archive_rp_branch(kr)  # also stores in long-term Rp archive

    with open(archive_path, "w") as f:
        json.dump(payload, f, indent=2)


# Entrypoint
async def think(current_kr: Kr) -> Kr:
    """Main entrypoint for concurrent thought simulation."""
    log(f"Starting concurrent thought thread from Kr ID {current_kr.id}")
    collapsed_kr = await run_parallel_kr_futures(current_kr)
    return collapsed_kr


# Synchronous wrapper
def think_sync(current_kr: Kr) -> Kr:
    return asyncio.run(think(current_kr))
