# llm/llm_router.py
def route_task(task, token_estimate):
    if token_estimate < 500:
        return "deepseek"
    elif token_estimate > 8000:
        return "gemini"
    else:
        return "gpt"# router.py - Scaffold placeholder
