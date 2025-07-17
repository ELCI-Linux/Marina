import os
import time
import random
import logging
from datetime import datetime

from brain.state_manager import get_current_kr, get_possible_rp
from brain.entropy_calculator import estimate_entropy
from brain.task_queue import fetch_pending_tasks, execute_task
from core.logger import init_logger
from llm.llm_router import query_llm_response
from brain.entropy_calculator import estimate_entropy

kr = get_current_kr()
rp = get_possible_rp()
ks = get_possible_ks()

entropy = estimate_entropy(kr, rp, ks)

# Initialize Marina’s logger
logger = init_logger(__name__, level=logging.INFO)

# Constants
THINK_INTERVAL_SECONDS = int(os.getenv("MARINA_THINK_INTERVAL", 600))  # default: 10 minutes
MIN_ENTROPY_THRESHOLD = float(os.getenv("MARINA_ENTROPY_THRESHOLD", 0.3))  # triggers high alert
MAX_TASKS_PER_TICK = int(os.getenv("MARINA_TASK_BUDGET", 5))


def tick():
    logger.info("🤖 Marina Think Loop Activated")

    # 1. Fetch current state
    kr = get_current_kr()
    rp = get_possible_rp()
    entropy = estimate_entropy(kr, rp)
    logger.info(f"🧠 Current Kr: {kr}")
    logger.info(f"📈 Entropy estimate: {entropy:.3f}")

    # 2. Check tasks
    tasks = fetch_pending_tasks()
    logger.info(f"📋 Found {len(tasks)} pending tasks")

    # 3. Decide priority
    if entropy >= MIN_ENTROPY_THRESHOLD or len(tasks) > 0:
        logger.info("⚡ Conditions warrant action")

        task_budget = min(MAX_TASKS_PER_TICK, len(tasks))
        selected_tasks = tasks[:task_budget]

        for task in selected_tasks:
            try:
                logger.info(f"🚀 Executing task: {task['description']}")
                execute_task(task)
            except Exception as e:
                logger.error(f"❌ Task failed: {e}")

    else:
        logger.info("🌙 Low entropy and low load. Marina remains in passive watch.")

    # 4. Optional: Reflect or self-query
    if random.random() < 0.2:  # occasional curiosity burst
        try:
            prompt = f"What should I learn or monitor given the current state Kr={kr} and entropy={entropy:.2f}?"
            suggestion = query_llm_response("gemini", prompt)
            logger.info(f"🧠 Self-query suggestion: {suggestion}")
        except Exception as e:
            logger.warning(f"Gemini self-query failed: {e}")

    logger.info("🕰️ Marina think loop tick completed.")


def run_loop():
    logger.info("🔄 Starting persistent Marina think loop...")
    while True:
        tick()
        logger.info(f"⏳ Sleeping for {THINK_INTERVAL_SECONDS} seconds...")
        time.sleep(THINK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_loop()
