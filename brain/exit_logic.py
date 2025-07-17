import enum
from typing import Dict, Any, Callable, Optional

# Exit condition categories
class ExitMode(enum.Enum):
    MANUAL = "manual"  # Human intervention required
    SATISFACTION = "satisfaction"  # Success criteria met
    TIME_LIMIT = "time_limit"  # Timeout reached
    TOKEN_LIMIT = "token_limit"  # Token/compute budget reached
    ERROR = "error"  # Error too critical to continue
    STALE_LOOP = "stale_loop"  # No progress detected
    QUALITY_THRESHOLD = "quality_threshold"  # Output rated "good enough"
    TASK_REPLACED = "task_replaced"  # Superseded by higher priority task

# Core logic
class ExitLogic:
    def __init__(self):
        self.task_start_time = None
        self.max_runtime_sec = 300  # 5 minutes default
        self.token_budget = 100000
        self.min_quality_score = 0.85  # Arbitrary self-evaluation threshold
        self.max_attempts = 5
        self.attempt_counter = 0
        self.last_output_hash = None
        self.stale_loop_counter = 0

    def should_exit(
        self,
        quality_score: Optional[float] = None,
        tokens_used: Optional[int] = 0,
        new_output_hash: Optional[str] = None,
        task_superseded: bool = False,
        error_occurred: bool = False,
        manual_override: bool = False,
        time_elapsed_sec: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluates all conditions to determine whether the task should be stopped.
        Returns a dict with `should_exit` and reason.
        """

        # Manual override
        if manual_override:
            return {"should_exit": True, "mode": ExitMode.MANUAL.value}

        # Error occurred
        if error_occurred:
            return {"should_exit": True, "mode": ExitMode.ERROR.value}

        # Superseded by another task
        if task_superseded:
            return {"should_exit": True, "mode": ExitMode.TASK_REPLACED.value}

        # Time limit
        if time_elapsed_sec and time_elapsed_sec > self.max_runtime_sec:
            return {"should_exit": True, "mode": ExitMode.TIME_LIMIT.value}

        # Token budget exceeded
        if tokens_used and tokens_used > self.token_budget:
            return {"should_exit": True, "mode": ExitMode.TOKEN_LIMIT.value}

        # Quality threshold
        if quality_score is not None and quality_score >= self.min_quality_score:
            return {"should_exit": True, "mode": ExitMode.SATISFACTION.value}

        # Stale loop detection (same output multiple times)
        if new_output_hash and new_output_hash == self.last_output_hash:
            self.stale_loop_counter += 1
        else:
            self.stale_loop_counter = 0
            self.last_output_hash = new_output_hash

        if self.stale_loop_counter >= 3:
            return {"should_exit": True, "mode": ExitMode.STALE_LOOP.value}

        # Attempt counter
        self.attempt_counter += 1
        if self.attempt_counter >= self.max_attempts:
            return {"should_exit": True, "mode": ExitMode.QUALITY_THRESHOLD.value}

        return {"should_exit": False}

# Example
if __name__ == "__main__":
    el = ExitLogic()

    # Simulate progress
    output = el.should_exit(quality_score=0.9, tokens_used=4000)
    print("✅ Exit Check:", output)

    # Simulate token overflow
    output = el.should_exit(quality_score=0.5, tokens_used=120000)
    print("🚨 Token Overflow:", output)

    # Simulate loop stagnation
    for _ in range(4):
        print("🔁 Loop Check:", el.should_exit(new_output_hash="deadbeef"))
