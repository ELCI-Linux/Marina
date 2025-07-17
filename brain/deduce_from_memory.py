import json
import os
import sys

# Dummy function to simulate Rabbit R1 interaction
# Replace this with your actual Rabbit R1 call logic
def query_rabbit_r1(system_prompt, content):
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY')
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # Replace with Rabbit R1 endpoint/model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def load_memory(memory_file="marina_memory_log.json"):
    if not os.path.exists(memory_file):
        print("Memory file not found.")
        sys.exit(1)
    with open(memory_file, "r") as f:
        return json.load(f)

def extract_relevant_content(memory):
    return "\n".join(
        f"[{entry['origin'].upper()}] {entry['prompt']}" +
        (f"\n[RESPONSE] {entry['response']}" if 'response' in entry else '')
        for entry in memory
    )

def main():
    memory = load_memory()
    conversation_history = extract_relevant_content(memory)

    system_prompt = (
        "You are an expert system analyst. Your task is to read through this memory transcript "
        "and extract structured project intelligence. From the historical interactions, identify and list:\n"
        "- Primary goals\n"
        "- Milestones\n"
        "- Key decision points\n"
        "- Project constraints\n"
        "- Fixed constants\n"
        "- Tracked or dynamic variables\n"
        "- Relationships between different project assets (tools, files, concepts, teams)\n\n"
        "Format your response clearly using markdown-style headings."
    )

    result = query_rabbit_r1(system_prompt, conversation_history)
    print(result)

if __name__ == "__main__":
    main()
