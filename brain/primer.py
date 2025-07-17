import os
import sys

from brain.advanced_contextual_memory import ContextMemory
from brain.safety_logic import SafetyLogic
from brain.three_laws import ThreeLaws
from brain.anti_llm_logic import AntiLLMLogic
from brain.ambition import AmbitionEngine
from brain.deepthink_logic import DeepThinker
from brain.planner import Planner
from brain.module_maker import ModuleMaker
from brain.llm_router import validate_llms

class MarinaPrimer:
    def __init__(self):
        self.memory = ContextMemory()
        self.safety = SafetyLogic()
        self.laws = ThreeLaws()
        self.llm_policy = AntiLLMLogic()
        self.ambitions = AmbitionEngine()
        self.deepthinker = DeepThinker()
        self.planner = Planner()
        self.module_maker = ModuleMaker()
        self.safe_mode = True

    def run_diagnostics(self):
        print("[Primer] Running startup diagnostics...")
        if not validate_llms():
            print("[FAIL] LLM routing not healthy.")
        else:
            print("[OK] LLMs online.")

        if not self.safety.check_core_integrity():
            print("[WARNING] Safety system integrity check failed.")
        else:
            print("[OK] Safety logic secure.")

        if self.memory.has_recent_crash():
            print("[Alert] Marina recovered from a prior crash.")
            self.memory.flag_event("primer", "Crash recovery invoked.")

    def preload_ambitions(self):
        print("[Primer] Loading ambition stack...")
        self.ambitions.add_ambition("Maintain memory reliability", "Ensure memory writes and pruning are stable", "internal", 2)
        self.ambitions.add_ambition("Serve user proactively", "Anticipate and support user needs without waiting", "external", 3)

    def reflect_before_start(self):
        print("[Primer] Performing initial deep reflection...")
        self.deepthinker.start_thinking("What risks or blindspots might Marina have at startup?")
        summary = self.deepthinker.summarize_chain()
        self.memory.store_event("deep_reflection", summary)

    def prepare_state(self):
        print("[Primer] Preparing internal structures...")
        self.memory.warm()
        self.planner.load_goals_from_memory(self.memory)
        self.module_maker.load_existing_modules()

    def launch(self):
        print("🧠 Marina Primer: Booting cognition stack...\n")
        self.run_diagnostics()
        self.preload_ambitions()
        self.reflect_before_start()
        self.prepare_state()
        print("\n✅ Marina is now initialized and ready.")

if __name__ == "__main__":
    primer = MarinaPrimer()
    primer.launch()
