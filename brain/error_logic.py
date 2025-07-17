import os
import traceback
import datetime
import json
import hashlib

# ============ CONFIG ============
ERROR_LOG_FILE = "marina_error_log.json"
DEDUCTION_MODEL = "gpt-4o"  # Replace if using Rabbit R1
MAX_CONTEXT_LINES = 30

# ============ LOGGING ============
def ensure_log_file():
    if not os.path.exists(ERROR_LOG_FILE):
        with open(ERROR_LOG_FILE, "w") as f:
            json.dump([], f, indent=2)

def log_error(error_type, message, trace, file_path=None):
    ensure_log_file()
    error_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "error_type": error_type,
        "message": message,
        "trace": trace,
        "file": file_path,
        "error_hash": hashlib.sha256((error_type + message).encode()).hexdigest()
    }
    with open(ERROR_LOG_FILE, "r+") as f:
        data = json.load(f)
        data.append(error_entry)
        f.seek(0)
        json.dump(data, f, indent=2)
    return error_entry

# ============ DEDUCTION ============
def extract_code_context(file_path, trace):
    if not file_path or not os.path.exists(file_path):
        return "No source file available."
    
    try:
        with open(file_path, "r") as f:
            code_lines = f.readlines()
        
        # Try to extract the most relevant traceback line with a line number
        relevant_line = next((line for line in trace.split('\n') if file_path in line), None)
        if not relevant_line:
            return "Unable to locate exact line in file."

        line_no = int(relevant_line.strip().split(", line ")[1].split(",")[0])
        start = max(0, line_no - MAX_CONTEXT_LINES // 2)
        end = min(len(code_lines), line_no + MAX_CONTEXT_LINES // 2)
        context = "".join(code_lines[start:end])
        return context
    except Exception as e:
        return f"Failed to extract context: {str(e)}"

def query_deduction_llm(error_summary: str, code_context: str) -> str:
    from openai import OpenAI
    client = OpenAI()
    messages = [
        {"role": "system", "content": "You are an expert Python debugger and recovery strategist."},
        {"role": "user", "content": (
            f"An error occurred:\n\n"
            f"### Error Summary:\n{error_summary}\n\n"
            f"### Code Context:\n```python\n{code_context}\n```"
            f"\n\nPlease summarize the root cause, suggest a fix, and describe how the agent should adapt to avoid this failure type in future."
        )}
    ]
    response = client.chat.completions.create(
        model=DEDUCTION_MODEL,
        messages=messages,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# ============ ADAPTATION FRAMEWORK ============
def get_adaptation_directive(error_entry):
    trace = error_entry['trace']
    file_path = error_entry['file']
    summary = f"{error_entry['error_type']}: {error_entry['message']}"
    context = extract_code_context(file_path, trace)
    deduction = query_deduction_llm(summary, context)
    return deduction

# ============ HANDLER ============
def handle_exception(exc: Exception, file_path: str = None):
    error_type = type(exc).__name__
    message = str(exc)
    trace = traceback.format_exc()
    entry = log_error(error_type, message, trace, file_path)
    directive = get_adaptation_directive(entry)
    
    print("\n🛠️ Marina Error Summary:\n")
    print(directive)
    return directive

# ============ TEST ============
if __name__ == "__main__":
    try:
        # Simulate faulty code
        result = 1 / 0
    except Exception as e:
        handle_exception(e, file_path=__file__)
