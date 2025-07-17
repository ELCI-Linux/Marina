import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

class Task:
    def __init__(self, name: str, description: str = "", due_date: Optional[datetime] = None, dependencies: Optional[List[str]] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.due_date = due_date
        self.dependencies = dependencies or []
        self.status = "pending"  # pending, in_progress, completed, blocked
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def update_status(self, new_status: str):
        if new_status not in ["pending", "in_progress", "completed", "blocked"]:
            raise ValueError(f"Invalid status: {new_status}")
        self.status = new_status
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "dependencies": self.dependencies,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class Milestone:
    def __init__(self, name: str, description: str = "", due_date: Optional[datetime] = None, tasks: Optional[List[str]] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.due_date = due_date
        self.tasks = tasks or []  # List of task IDs
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tasks": self.tasks,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class Planner:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.milestones: Dict[str, Milestone] = {}
        self.goals: List[str] = []
        self.constraints: Dict[str, Any] = {}

    def add_goal(self, goal: str):
        self.goals.append(goal)

    def add_constraint(self, key: str, value: Any):
        self.constraints[key] = value

    def create_task(self, name: str, description: str = "", due_date: Optional[datetime] = None, dependencies: Optional[List[str]] = None) -> str:
        task = Task(name, description, due_date, dependencies)
        self.tasks[task.id] = task
        return task.id

    def create_milestone(self, name: str, description: str = "", due_date: Optional[datetime] = None, tasks: Optional[List[str]] = None) -> str:
        milestone = Milestone(name, description, due_date, tasks)
        self.milestones[milestone.id] = milestone
        return milestone.id

    def assign_task_to_milestone(self, task_id: str, milestone_id: str):
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found")
        if milestone_id not in self.milestones:
            raise KeyError(f"Milestone {milestone_id} not found")
        milestone = self.milestones[milestone_id]
        if task_id not in milestone.tasks:
            milestone.tasks.append(task_id)
            milestone.updated_at = datetime.now()

    def update_task_status(self, task_id: str, status: str):
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found")
        self.tasks[task_id].update_status(status)

    def get_plan_overview(self) -> Dict[str, Any]:
        return {
            "goals": self.goals,
            "constraints": self.constraints,
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "milestones": {mid: m.to_dict() for mid, m in self.milestones.items()}
        }

    def upcoming_tasks(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        now = datetime.now()
        future_limit = now + timedelta(days=days_ahead)
        upcoming = []
        for task in self.tasks.values():
            if task.due_date and now <= task.due_date <= future_limit and task.status != "completed":
                upcoming.append(task.to_dict())
        return upcoming

    def tasks_blocked_by(self, task_id: str) -> List[Dict[str, Any]]:
        blocked = []
        for task in self.tasks.values():
            if task_id in task.dependencies and task.status != "completed":
                blocked.append(task.to_dict())
        return blocked
