import os
import subprocess
import json
import tempfile
import traceback
from typing import List, Dict

# Replace this with your real LLM call
def call_llm_generate_test(module_path: str, module_code: str) -> str:
    """Stub for generating a unit test via LLM."""
    return f'''import unittest\nfrom {os.path.basename(module_path)[:-3]} import *\n\nclass TestGenerated(unittest.TestCase):\n    def test_placeholder(self):\n        self.assertTrue(True)\n\nif __name__ == "__main__":\n    unittest.main()\n'''

class AutomatedTester:
    def __init__(self, test_dir="tests"):
        self.test_dir = os.path.abspath(test_dir)
        os.makedirs(self.test_dir, exist_ok=True)

    def generate_test_for_module(self, module_path: str) -> str:
        """Create a unit test file for the given module using LLM."""
        with open(module_path, "r", encoding="utf-8") as f:
            code = f.read()

        test_code = call_llm_generate_test(module_path, code)
        test_file_path = os.path.join(self.test_dir, f"test_{os.path.basename(module_path)}")

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        return test_file_path

    def run_tests(self, test_file_path: str) -> Dict[str, any]:
        """Run a single test file and return result summary."""
        result = {
            "passed": False,
            "errors": None,
            "stdout": "",
            "stderr": ""
        }

        try:
            process = subprocess.run(
                ["python3", test_file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["passed"] = process.returncode == 0
        except Exception as e:
            result["errors"] = traceback.format_exc()

        return result

    def test_module(self, module_path: str) -> Dict[str, any]:
        test_file = self.generate_test_for_module(module_path)
        result = self.run_tests(test_file)
        return {
            "module": module_path,
            "test_file": test_file,
            "result": result
        }

    def test_multiple_modules(self, module_paths: List[str]) -> List[Dict[str, any]]:
        return [self.test_module(p) for p in module_paths]

    def clean_tests(self):
        for f in os.listdir(self.test_dir):
            if f.startswith("test_") and f.endswith(".py"):
                os.remove(os.path.join(self.test_dir, f))
