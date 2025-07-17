import tkinter as tk
from tkinter import font

try:
    import enchant  # For spellcheck dictionary
    SPELLCHECK_AVAILABLE = True
except ImportError:
    SPELLCHECK_AVAILABLE = False


class ChatInput(tk.Text):
    def __init__(self, master, send_callback, **kwargs):
        super().__init__(master, wrap="word", height=1, **kwargs)

        self.send_callback = send_callback
        self.max_height = 10  # max number of lines before scrollbar needed

        # Configure fonts and tags for formatting
        self.base_font = font.Font(font=self['font'])
        self.bold_font = font.Font(self, self.base_font)
        self.bold_font.configure(weight="bold")
        self.italic_font = font.Font(self, self.base_font)
        self.italic_font.configure(slant="italic")
        self.underline_font = font.Font(self, self.base_font)
        self.underline_font.configure(underline=1)

        self.tag_configure("bold", font=self.bold_font)
        self.tag_configure("italic", font=self.italic_font)
        self.tag_configure("underline", font=self.underline_font)

        # Bind keys
        self.bind("<Return>", self.on_return)
        self.bind("<Shift-Return>", self.on_shift_return)
        self.bind("<Control-b>", self.toggle_bold)
        self.bind("<Control-i>", self.toggle_italic)
        self.bind("<Control-u>", self.toggle_underline)

        # Dynamic resizing
        self.bind("<<Modified>>", self.on_text_modified)

        # Spellcheck setup
        if SPELLCHECK_AVAILABLE:
            self.spell_dict = enchant.Dict("en_US")
            self.bind("<KeyRelease>", self.on_key_release)
        else:
            self.spell_dict = None

    def on_return(self, event):
        # Send text on Enter
        text = self.get("1.0", "end-1c").strip()
        if text:
            self.send_callback(text)
            self.delete("1.0", tk.END)
            self.reset_height()
        return "break"  # Prevent default newline on Enter

    def on_shift_return(self, event):
        # Insert newline on Shift+Enter
        self.insert(tk.INSERT, "\n")
        return "break"

    def toggle_tag(self, tag_name):
        try:
            start = self.index("sel.first")
            end = self.index("sel.last")
        except tk.TclError:
            return  # No selection

        if tag_name in self.tag_names("sel.first"):
            self.tag_remove(tag_name, start, end)
        else:
            self.tag_add(tag_name, start, end)

    def toggle_bold(self, event):
        self.toggle_tag("bold")
        return "break"

    def toggle_italic(self, event):
        self.toggle_tag("italic")
        return "break"

    def toggle_underline(self, event):
        self.toggle_tag("underline")
        return "break"

    def on_text_modified(self, event):
        # Dynamically resize height based on number of lines
        self.edit_modified(False)  # reset modified flag
        line_count = int(self.index('end-1c').split('.')[0])
        new_height = min(max(1, line_count), self.max_height)
        self.config(height=new_height)

    def reset_height(self):
        self.config(height=1)

    def on_key_release(self, event):
        # Basic spellcheck underline logic
        self.remove_spell_tags()
        if not SPELLCHECK_AVAILABLE:
            return

        words = self.get("1.0", "end-1c").split()
        start_index = "1.0"
        for word in words:
            if not self.spell_dict.check(word):
