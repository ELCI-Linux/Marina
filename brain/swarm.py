import uuid
import random
from typing import List, Dict, Callable, Optional

class MarinaAgent:
    def __init__(self, role: str, capabilities: List[str], execute_fn: Callable[[str], str]):
        self.id = str(uuid.uuid4())
        self.role = role
        self.capabilities = capabilities
        self.execute = execute_fn  # Function to perform the task
        self.active = True
        self.load = 0  # Simulated load or queue

    def can_handle(self, task_type: str) -> bool:
        return task_type in self.capabilities

    def receive_task(self, task: str, task_type: str) -> str:
        if not self.active or not self.can_handle(task_type):
            return f"[{self.role}] Rejected task: {task_type}"
        self.load += 1
        result = self.execute(task)
        self.load -= 1
        return f"[{self.role}] {result}"

class MarinaSwarm:
    def __init__(self, name: str):
        self.name = name
        self.agents: List[MarinaAgent] = []
        self.history: List[str] = []

    def add_agent(self, agent: MarinaAgent):
        self.agents.append(agent)

    def route_task(self, task: str, task_type: str) -> Optional[str]:
        # Prefer lowest load matching agent
        eligible = [a for a in self.agents if a.can_handle(task_type) and a.active]
        if not eligible:
            self.history.append(f"[{self.name}] No agents available for task: {task_type}")
            return None
        agent = sorted(eligible, key=lambda a: a.load)[0]
        response = agent.receive_task(task, task_type)
        self.history.append(response)
        return response

    def summarize(self):
        return {
            "name": self.name,
            "agent_count": len(self.agents),
            "history": self.history
        }
marina.register_model("deepseek-r1", {
    "type": "api",
    "endpoint": "https://api.deepseek.com/v1/chat/completions",
    "capabilities": ["coding", "math", "reasoning", "instruct"],
    "cost_estimate": 0.002,  # adjust based on usage tier
    "fallback_priority": 1,
})
