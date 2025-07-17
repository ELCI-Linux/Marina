def fetch_pending_tasks():
    return [{"description": "Check API limits", "type": "monitor"}]

def execute_task(task):
    print(f"Executing: {task['description']}")
