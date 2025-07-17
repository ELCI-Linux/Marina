import os
import json
from datetime import datetime

# Placeholder for your LLM interface - replace with your actual call logic
def call_llm_generate_code(prompt: str) -> str:
    # Stub example: returns a dummy function code based on prompt
    return f"# Generated code snippet based on spec:\n# {prompt}\ndef generated_func():\n    pass\n"

class ModuleMaker:
    def __init__(self, base_dir="modules"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def generate_module(self, module_name: str, spec: dict) -> str:
        """
        Generate a module based on specification dict.

        Spec example:
        {
          "description": "Handles user authentication",
          "functions": [
            {"name": "login", "inputs": ["username", "password"], "outputs": ["token"]},
            {"name": "logout", "inputs": ["token"], "outputs": []}
          ],
          "dependencies": ["hashlib", "jwt"],
          "author": "Marina AI",
        }
        """
        code_lines = []

        # Header + metadata
        code_lines.append(f'"""')
        code_lines.append(f"Module: {module_name}")
        code_lines.append(f"Description: {spec.get('description', 'No description')}")
        code_lines.append(f"Author: {spec.get('author', 'Marina AI')}")
        code_lines.append(f"Generated: {datetime.now().isoformat()}")
        code_lines.append(f'"""')
        code_lines.append("")

        # Imports
        for dep in spec.get("dependencies", []):
            code_lines.append(f"import {dep}")
        code_lines.append("")

        # Generate function stubs via LLM calls or template
        for func_spec in spec.get("functions", []):
            prompt = self._function_prompt(module_name, func_spec)
            func_code = call_llm_generate_code(prompt)
            code_lines.append(func_code)
            code_lines.append("")

        # Write module to file
        file_path = os.path.join(self.base_dir, f"{module_name}.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(code_lines))

        return file_path

    def _function_prompt(self, module_name, func_spec):
        name = func_spec.get("name", "unnamed_func")
        inputs = func_spec.get("inputs", [])
        outputs = func_spec.get("outputs", [])
        prompt = (f"Write a Python function called '{name}' "
                  f"in module '{module_name}' "
                  f"that takes inputs {inputs} and returns {outputs}. "
                  "Include type hints and docstring.")
        return prompt

    def validate_module(self, module_path):
        """
        Basic validation: syntax check by compiling
        """
        try:
            with open(module_path, "r", encoding="utf-8") as f:
                source = f.read()
            compile(source, module_path, "exec")
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def generate_and_validate(self, module_name, spec):
        path = self.generate_module(module_name, spec)
        valid, err = self.validate_module(path)
        if valid:
            print(f"[module_maker] Module '{module_name}' generated successfully at {path}")
            return path
        else:
            print(f"[module_maker] Validation error in '{module_name}': {err}")
            return None
