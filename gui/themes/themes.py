# themes.py
import tkinter as tk
from tkinter import ttk

# LLM configurations
LLMS = ["GPT-4", "Claude", "Gemini", "DeepSeek", "Mistral", "LLaMA", "Local"]

# Context window limits for each LLM (in tokens)
CONTEXT_LIMITS = {
    "GPT-4": 128000,
    "Claude": 200000,
    "Gemini": 128000,
    "DeepSeek": 128000,
    "Mistral": 32000,
    "LLaMA": 128000,
    "Local": 8000
}

# Ping endpoints for web-based LLMs
PING_ENDPOINTS = {
    "GPT-4": "api.openai.com",
    "Claude": "api.anthropic.com",
    "Gemini": "generativelanguage.googleapis.com",
    "DeepSeek": "api.deepseek.com",
    "Mistral": "api.mistral.ai",
    "LLaMA": "api.together.xyz",
    # "Local" is excluded as it's not web-based
}

# Light theme colors
LIGHT_COLORS = {
    "GPT-4": "#cce5ff",
    "Claude": "#d4edda",
    "Gemini": "#fff3cd",
    "DeepSeek": "#ffe4e1",
    "Mistral": "#f8d7da",
    "LLaMA": "#e2e3e5",
    "Local": "#d1c4e9"
}

# Dark theme colors
DARK_COLORS = {
    "GPT-4": "#1a4d80",
    "Claude": "#2d5a3d",
    "Gemini": "#665c2d",
    "DeepSeek": "#663d3a",
    "Mistral": "#664044",
    "LLaMA": "#4a4d52",
    "Local": "#52497a"
}

# Dark theme configuration with a blue tint
DARK_THEME = {
    "bg": "#1b1b32",
    "fg": "#ffffff",
    "select_bg": "#2f2f5f",
    "select_fg": "#ffffff",
    "entry_bg": "#2f2f5f",
    "entry_fg": "#ffffff",
    "button_bg": "#2f2f5f",
    "button_fg": "#ffffff",
    "button_active_bg": "#3e3e7b",
    "scrollbar_bg": "#2f2f5f",
    "scrollbar_fg": "#666699"
}

class ThemeManager:
    def __init__(self, root):
        self.root = root
        self.dark_theme = tk.BooleanVar(value=True)
        self.colors = DARK_COLORS if self.dark_theme.get() else LIGHT_COLORS
        
    def apply_dark_theme(self):
        """Apply dark theme to the root window and configure ttk styles"""
        if self.dark_theme.get():
            self.root.configure(bg=DARK_THEME["bg"])
            
            # Configure ttk styles for dark theme
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure ttk widgets for dark theme
            style.configure('TFrame', background=DARK_THEME["bg"])
            style.configure('TLabel', background=DARK_THEME["bg"], foreground=DARK_THEME["fg"], font=('Ubuntu', 10))
            style.configure('TButton', background=DARK_THEME["button_bg"], foreground=DARK_THEME["button_fg"], font=('Ubuntu', 10))
            style.map('TButton', background=[('active', DARK_THEME["button_active_bg"])])
            style.configure('TEntry', fieldbackground=DARK_THEME["entry_bg"], foreground=DARK_THEME["entry_fg"], bordercolor=DARK_THEME["scrollbar_fg"], font=('Ubuntu', 10))
            style.configure('TCombobox', fieldbackground=DARK_THEME["entry_bg"], foreground=DARK_THEME["entry_fg"], bordercolor=DARK_THEME["scrollbar_fg"], font=('Ubuntu', 10))
            style.configure('TCheckbutton', background=DARK_THEME["bg"], foreground=DARK_THEME["fg"], font=('Ubuntu', 10))
            style.configure('TSeparator', background=DARK_THEME["scrollbar_fg"])
        else:
            self.root.configure(bg="#f0f0f0")
            style = ttk.Style()
            style.theme_use('default')
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.dark_theme.set(not self.dark_theme.get())
        self.colors = DARK_COLORS if self.dark_theme.get() else LIGHT_COLORS
        self.apply_dark_theme()
        return self.dark_theme.get()
    
    def apply_theme_to_window(self, window):
        """Apply current theme to any window"""
        if self.dark_theme.get():
            window.configure(bg=DARK_THEME["bg"])
        else:
            window.configure(bg="#f0f0f0")
    
    def get_theme_colors(self):
        """Get current theme colors"""
        return DARK_THEME if self.dark_theme.get() else {
            "bg": "#f0f0f0",
            "fg": "#000000",
            "select_bg": "#0078d4",
            "select_fg": "#ffffff",
            "entry_bg": "#ffffff",
            "entry_fg": "#000000",
            "button_bg": "#e1e1e1",
            "button_fg": "#000000",
            "button_active_bg": "#d4d4d4",
            "scrollbar_bg": "#f0f0f0",
            "scrollbar_fg": "#c0c0c0"
        }
