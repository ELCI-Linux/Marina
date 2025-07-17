import tkinter as tk
from tkinter import ttk

# LLM identifiers
LLMS = ["GPT-4", "Claude", "Gemini", "DeepSeek", "Mistral", "LLaMA", "Local"]

class LLMGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-LLM Interface")

        self.mode = tk.StringVar(value="wide")
        self.selected_llm = tk.StringVar(value=LLMS[0])
        self.text_widgets = {}

        self.build_controls()
        self.build_panes()
        self.update_panes()

    def build_controls(self):
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", pady=5)

        ttk.Label(control_frame, text="Mode:").pack(side="left", padx=5)
        mode_switch = ttk.Combobox(control_frame, textvariable=self.mode, values=["wide", "focused"], state="readonly")
        mode_switch.pack(side="left")
        mode_switch.bind("<<ComboboxSelected>>", lambda e: self.update_panes())

        ttk.Label(control_frame, text="LLM:").pack(side="left", padx=5)
        llm_selector = ttk.Combobox(control_frame, textvariable=self.selected_llm, values=LLMS, state="readonly")
        llm_selector.pack(side="left")
        llm_selector.bind("<<ComboboxSelected>>", lambda e: self.update_panes())

        run_button = ttk.Button(control_frame, text="Run Query", command=self.query_llms)
        run_button.pack(side="right", padx=5)

    def build_panes(self):
        self.panes_frame = ttk.Frame(self.root)
        self.panes_frame.pack(fill="both", expand=True)

        for llm in LLMS:
            frame = ttk.LabelFrame(self.panes_frame, text=llm)
            frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

            text = tk.Text(frame, wrap="word", font=("Courier", 10))
            text.pack(fill="both", expand=True)
            self.text_widgets[llm] = text

    def update_panes(self):
        mode = self.mode.get()
        selected = self.selected_llm.get()

        for llm, widget in self.text_widgets.items():
            parent = widget.master
            if mode == "wide" or llm == selected:
                parent.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            else:
                parent.pack_forget()

    def query_llms(self):
        query = self.get_input_prompt()

        for llm in LLMS:
            if self.mode.get() == "focused" and llm != self.selected_llm.get():
                continue
            response = self.query_llm(llm, query)
            self.text_widgets[llm].delete(1.0, tk.END)
            self.text_widgets[llm].insert(tk.END, response)

    def get_input_prompt(self):
        # Replace with your actual query input logic if needed
        return "What is gravity?"

    def query_llm(self, llm_name, prompt):
        # ✨ PLUG YOUR llm_router HERE ✨
        # Return mock output for now
        return f"[{llm_name}] Response to: '{prompt}'"

if __name__ == "__main__":
    root = tk.Tk()
    app = LLMGuiApp(root)
    root.mainloop()
