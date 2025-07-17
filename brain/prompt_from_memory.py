import sys
import os

# Replace with your actual deduction LLM call (Rabbit R1 or OpenAI)
def query_deduction_llm(system_prompt, content):
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",  # Replace with Rabbit R1 if needed
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()

def load_deduction_output(file_path="deduction_output.md"):
    if not os.path.exists(file_path):
        print(f"❌ Deduction output file '{file_path}' not found.")
        sys.exit(1)
    with open(file_path, "r") as f:
        return f.read()

def main():
    deduction_output = load_deduction_output()

    system_prompt = (
        "You are an intelligent task router embedded in an autonomous agent. "
        "Given the structured project deductions (goals, milestones, keypoints, variables, etc.), "
        "you must now determine the most useful and timely next prompt for the agent to pursue. "
        "Only return a single, highly relevant prompt — do not include explanation.\n\n"
        "This prompt will be passed directly into the agent's reasoning module."
    )

    next_prompt = query_deduction_llm(system_prompt, deduction_output)
    print(f"\n🔮 Suggested Next Prompt:\n{next_prompt}\n")

if __name__ == "__main__":
    main()
