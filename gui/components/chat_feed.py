# chat_feed.py
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import sys
import os
import tempfile
import subprocess
import threading
from gui.themes.themes import DARK_THEME, LLMS

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from brain.action_engine import run_action_command

class ChatFeed:
    def __init__(self, root, theme_manager):
        self.root = root
        self.theme_manager = theme_manager
        self.message_counter = 0
        self.collapsed_messages = set()
        self.message_data = {}
        self.code_blocks = []  # Store all code blocks globally
        self.current_code_index = 0
        self.code_pane = None
        self.code_display = None
        self.code_info_label = None
        self.nav_buttons = {}
        
        # Create the chat frame and code pane
        self.build_chat_feed()
        self.build_code_pane()
        
    def build_chat_feed(self):
        """Build the chat feed widget"""
        # Configure chat frame with dark theme support
        chat_bg = DARK_THEME["bg"] if self.theme_manager.dark_theme.get() else "white"
        chat_fg = DARK_THEME["fg"] if self.theme_manager.dark_theme.get() else "black"
        
        self.chat_frame = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD, 
            font=("Ubuntu", 12),
            bg=chat_bg,
            fg=chat_fg,
            insertbackground=DARK_THEME["fg"] if self.theme_manager.dark_theme.get() else "black",
            selectbackground=DARK_THEME["select_bg"] if self.theme_manager.dark_theme.get() else "#316AC5",
            selectforeground=DARK_THEME["select_fg"] if self.theme_manager.dark_theme.get() else "white"
        )
        self.chat_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Configure text tags
        user_fg = DARK_THEME["fg"] if self.theme_manager.dark_theme.get() else "black"
        action_fg = "#87CEEB" if self.theme_manager.dark_theme.get() else "blue"
        
        self.chat_frame.tag_config("user", foreground=user_fg, font=("Ubuntu", 12, "bold"))
        for llm in LLMS:
            self.chat_frame.tag_config(llm, background=self.theme_manager.colors[llm], lmargin1=10, lmargin2=10, spacing3=6, font=("Ubuntu", 11))
        self.chat_frame.tag_config("action", foreground=action_fg, font=("Ubuntu Mono", 10))
        self.chat_frame.tag_config("prompt", foreground="#FFD700" if self.theme_manager.dark_theme.get() else "#B8860B", font=("Ubuntu", 11, "italic"))
    
    def append_chat(self, sender, message, tag):
        """Add a message to the chat feed"""
        # Store full message data
        msg_id = self.message_counter
        
        # Process message to extract code blocks if sender is an LLM
        processed_message, code_blocks = self.extract_code_blocks_from_message(message, sender)
        
        self.message_data[msg_id] = {
            'sender': sender,
            'message': processed_message,
            'original_message': message,
            'code_blocks': code_blocks,
            'tag': tag,
            'collapsed': False
        }
        
        # Create truncated version for collapsing (first 3 lines)
        lines = processed_message.split('\n')
        if len(lines) > 3 and len(processed_message) > 200:
            truncated = '\n'.join(lines[:3]) + '\n...'
            self.message_data[msg_id]['truncated'] = truncated
            self.message_data[msg_id]['is_long'] = True
        else:
            self.message_data[msg_id]['is_long'] = False
            
        self.render_message(msg_id)
        self.message_counter += 1
        self.chat_frame.see(tk.END)
        
    def extract_code_blocks_from_message(self, message, sender):
        """Extract code blocks from LLM messages and replace them with placeholder text"""
        if sender not in LLMS:
            return message, None
        
        code_blocks = []
        parts = message.split('```')
        processed_message = ""
        for i, part in enumerate(parts):
            if i % 2 == 0:
                processed_message += part
            else:
                # Enhanced code block processing
                code_info = self.analyze_code_block(part, sender)
                code_placeholder = f"[Code Block {len(code_blocks)+1}: {code_info['filename']}]"
                processed_message += code_placeholder
                code_blocks.append(code_info)
                
                # Add to global code blocks list
                self.code_blocks.append(code_info)
        
        # Update code pane if we have code blocks
        if code_blocks:
            self.update_code_pane()
        
        return processed_message, code_blocks
    
    def analyze_code_block(self, code_block, sender):
        """Analyze a code block to determine type, filename, and other metadata"""
        lines = code_block.strip().split('\n')
        
        # Extract language identifier if present
        language = None
        code_content = code_block.strip()
        
        if lines and lines[0].strip():
            first_line = lines[0].strip().lower()
            if first_line in ['python', 'py', 'bash', 'sh', 'shell', 'html', 'css', 'javascript', 'js', 'json', 'yaml', 'xml', 'sql', 'dockerfile', 'makefile']:
                language = first_line
                code_content = '\n'.join(lines[1:])
        
        # Detect code type and suggest filename
        if language:
            code_type = self.map_language_to_type(language)
        else:
            code_type = self.detect_code_type(code_content)
        
        # Generate filename and extension
        filename_info = self.generate_filename(code_content, code_type, sender)
        
        return {
            'code': code_content,
            'raw_code': code_block,
            'language': language,
            'type': code_type,
            'filename': filename_info['filename'],
            'extension': filename_info['extension'],
            'description': filename_info['description'],
            'sender': sender,
            'timestamp': self.get_timestamp()
        }
    
    def map_language_to_type(self, language):
        """Map language identifiers to code types"""
        mapping = {
            'python': 'python',
            'py': 'python',
            'bash': 'shell',
            'sh': 'shell',
            'shell': 'shell',
            'html': 'html',
            'css': 'css',
            'javascript': 'javascript',
            'js': 'javascript',
            'json': 'json',
            'yaml': 'yaml',
            'xml': 'xml',
            'sql': 'sql',
            'dockerfile': 'dockerfile',
            'makefile': 'makefile'
        }
        return mapping.get(language, 'text')
    
    def generate_filename(self, code, code_type, sender):
        """Generate appropriate filename based on code content and type"""
        # Extract meaningful names from code content
        lines = code.strip().split('\n')
        
        # Default filename components
        base_name = "code"
        extension = ".txt"
        description = "Text file"
        
        if code_type == 'python':
            extension = ".py"
            description = "Python script"
            # Look for class or function names
            for line in lines:
                if line.strip().startswith('def '):
                    func_name = line.strip().split('def ')[1].split('(')[0]
                    base_name = func_name
                    break
                elif line.strip().startswith('class '):
                    class_name = line.strip().split('class ')[1].split('(')[0].split(':')[0]
                    base_name = class_name
                    break
            
        elif code_type == 'shell':
            extension = ".sh"
            description = "Shell script"
            # Look for meaningful script purpose
            for line in lines:
                if '#!/bin/bash' in line:
                    base_name = "script"
                    break
                elif line.strip().startswith('# '):
                    comment = line.strip()[2:].strip()
                    if len(comment) < 20:
                        base_name = comment.replace(' ', '_').lower()
                        break
        
        elif code_type == 'html':
            extension = ".html"
            description = "HTML document"
            # Look for title tag
            for line in lines:
                if '<title>' in line.lower():
                    title = line.lower().split('<title>')[1].split('</title>')[0].strip()
                    base_name = title.replace(' ', '_').lower()
                    break
        
        elif code_type == 'css':
            extension = ".css"
            description = "CSS stylesheet"
            base_name = "styles"
        
        elif code_type == 'javascript':
            extension = ".js"
            description = "JavaScript file"
            # Look for function names
            for line in lines:
                if 'function ' in line:
                    func_name = line.split('function ')[1].split('(')[0].strip()
                    base_name = func_name
                    break
        
        elif code_type == 'json':
            extension = ".json"
            description = "JSON data file"
            base_name = "data"
        
        elif code_type == 'yaml':
            extension = ".yaml"
            description = "YAML configuration"
            base_name = "config"
        
        elif code_type == 'dockerfile':
            extension = ""
            description = "Docker container file"
            base_name = "Dockerfile"
        
        elif code_type == 'makefile':
            extension = ""
            description = "Build automation file"
            base_name = "Makefile"
        
        # Clean up base name
        base_name = ''.join(c for c in base_name if c.isalnum() or c in '_-').strip()
        if not base_name:
            base_name = "code"
        
        # Add timestamp suffix if generic name
        if base_name in ['code', 'script', 'data', 'config', 'styles']:
            timestamp = self.get_timestamp().replace(':', '').replace(' ', '_')
            base_name = f"{base_name}_{timestamp}"
        
        filename = f"{base_name}{extension}"
        
        return {
            'filename': filename,
            'extension': extension,
            'description': description
        }
    
    def get_timestamp(self):
        """Get current timestamp as string"""
        import datetime
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def render_message(self, msg_id):
        """Render a message in the chat frame"""
        msg_data = self.message_data[msg_id]
        sender = msg_data['sender']
        message = msg_data['message']
        tag = msg_data['tag']
        
        # Insert sender with clickable expand/collapse button if message is long
        if msg_data['is_long']:
            collapse_symbol = "▼" if not msg_data['collapsed'] else "▶"
            clickable_sender = f"{collapse_symbol} {sender}: "
            
            # Insert clickable sender
            start_pos = self.chat_frame.index(tk.END)
            self.chat_frame.insert(tk.END, clickable_sender, f"clickable_{msg_id}")
            
            # Configure clickable tag
            self.chat_frame.tag_config(f"clickable_{msg_id}", foreground="#87CEEB" if self.theme_manager.dark_theme.get() else "blue", underline=True)
            self.chat_frame.tag_bind(f"clickable_{msg_id}", "<Button-1>", lambda e: self.toggle_message_collapse(msg_id))
            
            # Insert message content
            if msg_data['collapsed']:
                display_message = msg_data['truncated']
            else:
                display_message = message
        else:
            # Regular message without collapse functionality
            self.chat_frame.insert(tk.END, f"{sender}: ", tag)
            display_message = message
            
        self.chat_frame.insert(tk.END, f"{display_message}\n", tag)
        
        # Add code block buttons if any exist
        if 'code_blocks' in msg_data and msg_data['code_blocks']:
            for i, code_block in enumerate(msg_data['code_blocks']):
                self.create_code_block_buttons(code_block, i, msg_id)
        
    def create_code_block_buttons(self, code_info, index, msg_id):
        """Create run, save buttons and info for each code block"""
        button_frame = ttk.Frame(self.chat_frame)
        button_frame.pack(anchor="w", padx=20, pady=2)

        # Run button
        run_button = ttk.Button(
            button_frame,
            text="🏃 Run",
            command=lambda: self.run_code(code_info['code']),
            width=8
        )
        run_button.pack(side="left", padx=2)

        # Save button
        save_button = ttk.Button(
            button_frame,
            text="💾 Save",
            command=lambda: self.save_code_with_info(code_info),
            width=8
        )
        save_button.pack(side="left", padx=2)
        
        # View in Code Pane button
        view_button = ttk.Button(
            button_frame,
            text="👁️ View",
            command=lambda: self.show_code_in_pane(code_info),
            width=8
        )
        view_button.pack(side="left", padx=2)
        
        # File info label
        info_text = f"📄 {code_info['filename']} ({code_info['description']})"
        info_label = ttk.Label(button_frame, text=info_text, font=("Ubuntu", 9))
        info_label.pack(side="left", padx=10)

    def toggle_message_collapse(self, msg_id):
        """Toggle the collapse state of a message"""
        if msg_id not in self.message_data:
            return
            
        msg_data = self.message_data[msg_id]
        if not msg_data['is_long']:
            return
            
        # Toggle collapse state
        msg_data['collapsed'] = not msg_data['collapsed']
        
        # Clear and re-render all messages
        self.refresh_chat_display()
        
    def refresh_chat_display(self):
        """Refresh the entire chat display"""
        # Save current scroll position
        current_position = self.chat_frame.yview()[1]
        
        # Clear the chat frame
        self.chat_frame.delete(1.0, tk.END)
        
        # Re-render all messages
        for msg_id in sorted(self.message_data.keys()):
            self.render_message(msg_id)
            
        # Restore scroll position (approximately)
        self.chat_frame.yview_moveto(current_position)

    def run_code(self, code):
        """Run the extracted code block"""
        # Clean up the code block (remove language identifier if present)
        lines = code.strip().split('\n')
        if lines and lines[0].strip() in ['python', 'bash', 'sh', 'shell', 'py', 'javascript', 'js', 'html', 'css']:
            code = '\n'.join(lines[1:])
        
        # Detect code type and run accordingly
        code_type = self.detect_code_type(code)
        
        if code_type == 'python':
            self.run_python_code(code)
        elif code_type == 'shell':
            self.run_shell_code(code)
        elif code_type == 'html':
            self.run_html_code(code)
        else:
            # Try to run as shell command by default
            self.run_shell_code(code)
    
    def detect_code_type(self, code):
        """Detect the type of code based on content"""
        code_lower = code.lower().strip()
        
        # Python indicators
        python_keywords = ['import ', 'def ', 'class ', 'if __name__', 'print(', 'from ', 'import']
        if any(keyword in code_lower for keyword in python_keywords):
            return 'python'
        
        # HTML indicators
        html_indicators = ['<html', '<head>', '<body>', '<div', '<p>', '<script', '<style']
        if any(indicator in code_lower for indicator in html_indicators):
            return 'html'
        
        # Shell indicators
        shell_indicators = ['#!/bin/bash', '#!/bin/sh', 'cd ', 'ls ', 'mkdir ', 'rm ', 'cp ', 'mv ']
        if any(indicator in code_lower for indicator in shell_indicators):
            return 'shell'
        
        # Default to shell if unclear
        return 'shell'
    
    def run_python_code(self, code):
        """Execute Python code safely"""
        self.append_chat("System", "🐍 Executing Python code...", "action")
        
        def execute_python():
            try:
                # Create a temporary file for the Python code
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code)
                    temp_file = f.name
                
                # Execute the Python file
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
                
                # Clean up the temporary file
                os.unlink(temp_file)
                
                # Display results
                if result.stdout:
                    self.append_chat("Python Output", result.stdout, "action")
                if result.stderr:
                    self.append_chat("Python Error", result.stderr, "action")
                if result.returncode != 0:
                    self.append_chat("System", f"Python script exited with code {result.returncode}", "action")
                else:
                    self.append_chat("System", "✅ Python code executed successfully", "action")
                    
            except subprocess.TimeoutExpired:
                self.append_chat("System", "❌ Python execution timed out (30s limit)", "action")
            except Exception as e:
                self.append_chat("System", f"❌ Python execution error: {str(e)}", "action")
        
        # Run in a separate thread to avoid blocking the GUI
        thread = threading.Thread(target=execute_python)
        thread.daemon = True
        thread.start()
    
    def run_shell_code(self, code):
        """Execute shell commands using the action engine"""
        self.append_chat("System", "🖥️ Executing shell command...", "action")
        
        def execute_shell():
            try:
                # Split code into individual commands
                commands = [cmd.strip() for cmd in code.split('\n') if cmd.strip() and not cmd.strip().startswith('#')]
                
                for command in commands:
                    if command:
                        self.append_chat("Shell", f"$ {command}", "action")
                        stdout, stderr = run_action_command(command)
                        
                        if stdout:
                            self.append_chat("Shell Output", stdout, "action")
                        if stderr:
                            self.append_chat("Shell Error", stderr, "action")
                
                self.append_chat("System", "✅ Shell commands executed", "action")
                
            except Exception as e:
                self.append_chat("System", f"❌ Shell execution error: {str(e)}", "action")
        
        # Run in a separate thread to avoid blocking the GUI
        thread = threading.Thread(target=execute_shell)
        thread.daemon = True
        thread.start()
    
    def run_html_code(self, code):
        """Execute HTML code by opening it in a browser"""
        self.append_chat("System", "🌐 Opening HTML in browser...", "action")
        
        def execute_html():
            try:
                # Create a temporary HTML file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    f.write(code)
                    temp_file = f.name
                
                # Open the HTML file in the default browser
                if sys.platform.startswith('linux'):
                    subprocess.run(['xdg-open', temp_file])
                elif sys.platform.startswith('darwin'):
                    subprocess.run(['open', temp_file])
                elif sys.platform.startswith('win'):
                    subprocess.run(['start', temp_file], shell=True)
                
                self.append_chat("System", f"✅ HTML opened in browser: {temp_file}", "action")
                
            except Exception as e:
                self.append_chat("System", f"❌ HTML execution error: {str(e)}", "action")
        
        # Run in a separate thread to avoid blocking the GUI
        thread = threading.Thread(target=execute_html)
        thread.daemon = True
        thread.start()

    def save_code(self, code):
        """Save the code block to a chosen file"""
        # Open a file dialog to select the file location
        file_path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt'), ('Python files', '*.py'), ('Shell scripts', '*.sh'), ('HTML files', '*.html'), ('All files', '*.*')]
        )

        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(code)
                self.append_chat("System", f"✅ Code saved to {file_path}", "action")
            except Exception as e:
                self.append_chat("System", f"❌ Error saving code: {str(e)}", "action")

    def preview_code(self, code):
        """Preview the code in a new window with syntax highlighting and editing capabilities"""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Code Preview")
        preview_window.geometry("800x600")
        
        # Apply theme to the preview window
        if self.theme_manager.dark_theme.get():
            preview_window.configure(bg=DARK_THEME["bg"])
        
        # Create a frame for the toolbar
        toolbar_frame = ttk.Frame(preview_window)
        toolbar_frame.pack(fill="x", padx=5, pady=5)
        
        # Add toolbar buttons
        run_button = ttk.Button(
            toolbar_frame,
            text="🏃 Run",
            command=lambda: self.run_code(text_widget.get(1.0, tk.END))
        )
        run_button.pack(side="left", padx=2)
        
        save_button = ttk.Button(
            toolbar_frame,
            text="💾 Save",
            command=lambda: self.save_code(text_widget.get(1.0, tk.END))
        )
        save_button.pack(side="left", padx=2)
        
        copy_button = ttk.Button(
            toolbar_frame,
            text="📋 Copy",
            command=lambda: self.copy_to_clipboard(text_widget.get(1.0, tk.END))
        )
        copy_button.pack(side="left", padx=2)
        
        # Add code type indicator
        code_type = self.detect_code_type(code)
        type_label = ttk.Label(toolbar_frame, text=f"Type: {code_type.upper()}")
        type_label.pack(side="right", padx=5)
        
        # Create text widget for code display with theme support
        text_frame = ttk.Frame(preview_window)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure text widget with theme
        text_bg = DARK_THEME["bg"] if self.theme_manager.dark_theme.get() else "white"
        text_fg = DARK_THEME["fg"] if self.theme_manager.dark_theme.get() else "black"
        
        text_widget = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=("Consolas", 11),
            bg=text_bg,
            fg=text_fg,
            insertbackground=text_fg,
            selectbackground=DARK_THEME["select_bg"] if self.theme_manager.dark_theme.get() else "#316AC5",
            selectforeground=DARK_THEME["select_fg"] if self.theme_manager.dark_theme.get() else "white",
            tabs=('1c', '2c', '3c', '4c', '5c', '6c', '7c', '8c')  # Tab stops for better code formatting
        )
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        h_scrollbar = ttk.Scrollbar(text_frame, orient="horizontal", command=text_widget.xview)
        text_widget.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and text widget
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        text_widget.pack(side="left", fill="both", expand=True)
        
        # Insert the code
        text_widget.insert(1.0, code)
        
        # Add line numbers
        self.add_line_numbers(text_widget, text_frame)
        
        # Add status bar
        status_frame = ttk.Frame(preview_window)
        status_frame.pack(fill="x", padx=5, pady=2)
        
        lines_count = len(code.split('\n'))
        chars_count = len(code)
        status_label = ttk.Label(status_frame, text=f"Lines: {lines_count} | Characters: {chars_count}")
        status_label.pack(side="left")
        
        # Add close button
        close_button = ttk.Button(
            status_frame,
            text="Close",
            command=preview_window.destroy
        )
        close_button.pack(side="right")
        
        # Focus on the text widget
        text_widget.focus_set()
        
        # Make window modal
        preview_window.transient(self.root)
        preview_window.grab_set()
        
        self.append_chat("System", "🔍 Code preview opened in new window", "action")
    
    def add_line_numbers(self, text_widget, parent_frame):
        """Add line numbers to the text widget"""
        # Create a text widget for line numbers
        line_bg = DARK_THEME["bg"] if self.theme_manager.dark_theme.get() else "#f0f0f0"
        line_fg = DARK_THEME["fg"] if self.theme_manager.dark_theme.get() else "#666666"
        
        line_numbers = tk.Text(
            parent_frame,
            width=4,
            padx=3,
            takefocus=0,
            border=0,
            state='disabled',
            wrap='none',
            bg=line_bg,
            fg=line_fg,
            font=("Consolas", 11)
        )
        
        # Pack line numbers widget
        line_numbers.pack(side="left", fill="y")
        
        # Function to update line numbers
        def update_line_numbers():
            line_numbers.config(state='normal')
            line_numbers.delete(1.0, tk.END)
            
            # Get the number of lines in the text widget
            lines = int(text_widget.index('end-1c').split('.')[0])
            
            # Insert line numbers
            for i in range(1, lines + 1):
                line_numbers.insert(tk.END, f"{i:3d}\n")
            
            line_numbers.config(state='disabled')
        
        # Initial line numbers
        update_line_numbers()
        
        # Bind scrolling to keep line numbers in sync
        def on_scroll(*args):
            line_numbers.yview_moveto(args[0])
        
        text_widget.config(yscrollcommand=lambda *args: (text_widget.master.children['!scrollbar'].set(*args), on_scroll(*args)))
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.append_chat("System", "📋 Code copied to clipboard", "action")
        except Exception as e:
            self.append_chat("System", f"❌ Error copying to clipboard: {str(e)}", "action")
    
    def save_code_with_info(self, code_info):
        """Save code with suggested filename and type"""
        # Get appropriate file types based on code type
        file_types = self.get_file_types_for_code_type(code_info['type'])
        
        file_path = filedialog.asksaveasfilename(
            initialvalue=code_info['filename'],
            defaultextension=code_info['extension'],
            filetypes=file_types
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(code_info['code'])
                self.append_chat("System", f"✅ {code_info['description']} saved to {file_path}", "action")
            except Exception as e:
                self.append_chat("System", f"❌ Error saving code: {str(e)}", "action")
    
    def get_file_types_for_code_type(self, code_type):
        """Get appropriate file types for save dialog based on code type"""
        type_mappings = {
            'python': [('Python files', '*.py'), ('All files', '*.*')],
            'shell': [('Shell scripts', '*.sh'), ('Bash scripts', '*.bash'), ('All files', '*.*')],
            'html': [('HTML files', '*.html'), ('HTM files', '*.htm'), ('All files', '*.*')],
            'css': [('CSS files', '*.css'), ('All files', '*.*')],
            'javascript': [('JavaScript files', '*.js'), ('All files', '*.*')],
            'json': [('JSON files', '*.json'), ('All files', '*.*')],
            'yaml': [('YAML files', '*.yaml'), ('YML files', '*.yml'), ('All files', '*.*')],
            'xml': [('XML files', '*.xml'), ('All files', '*.*')],
            'sql': [('SQL files', '*.sql'), ('All files', '*.*')],
            'dockerfile': [('Dockerfile', 'Dockerfile*'), ('All files', '*.*')],
            'makefile': [('Makefile', 'Makefile*'), ('All files', '*.*')]
        }
        return type_mappings.get(code_type, [('Text files', '*.txt'), ('All files', '*.*')])
    
    def build_code_pane(self):
        """Build the smart code pane for displaying and navigating code blocks"""
        # Create a separate frame for the code pane
        self.code_pane = ttk.Frame(self.root)
        self.code_pane.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Initially hide the code pane
        self.code_pane.pack_forget()
        
        # Create header frame with navigation
        header_frame = ttk.Frame(self.code_pane)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # Title label
        title_label = ttk.Label(header_frame, text="📝 Smart Code Pane", font=("Ubuntu", 14, "bold"))
        title_label.pack(side="left")
        
        # Navigation buttons
        nav_frame = ttk.Frame(header_frame)
        nav_frame.pack(side="right")
        
        self.nav_buttons['prev'] = ttk.Button(
            nav_frame,
            text="⬅️ Previous",
            command=self.show_previous_code,
            state="disabled"
        )
        self.nav_buttons['prev'].pack(side="left", padx=2)
        
        self.nav_buttons['next'] = ttk.Button(
            nav_frame,
            text="Next ➡️",
            command=self.show_next_code,
            state="disabled"
        )
        self.nav_buttons['next'].pack(side="left", padx=2)
        
        # Close button
        close_button = ttk.Button(
            nav_frame,
            text="❌ Close",
            command=self.hide_code_pane
        )
        close_button.pack(side="left", padx=5)
        
        # Info frame
        info_frame = ttk.Frame(self.code_pane)
        info_frame.pack(fill="x", padx=5, pady=2)
        
        self.code_info_label = ttk.Label(info_frame, text="No code selected", font=("Ubuntu", 10))
        self.code_info_label.pack(side="left")
        
        # Action buttons frame
        action_frame = ttk.Frame(self.code_pane)
        action_frame.pack(fill="x", padx=5, pady=2)
        
        self.action_buttons = {}
        
        self.action_buttons['run'] = ttk.Button(
            action_frame,
            text="🏃 Run Code",
            command=self.run_current_code,
            state="disabled"
        )
        self.action_buttons['run'].pack(side="left", padx=2)
        
        self.action_buttons['save'] = ttk.Button(
            action_frame,
            text="💾 Save Code",
            command=self.save_current_code,
            state="disabled"
        )
        self.action_buttons['save'].pack(side="left", padx=2)
        
        self.action_buttons['copy'] = ttk.Button(
            action_frame,
            text="📋 Copy Code",
            command=self.copy_current_code,
            state="disabled"
        )
        self.action_buttons['copy'].pack(side="left", padx=2)
        
        # Code display frame
        code_frame = ttk.Frame(self.code_pane)
        code_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure code display with theme
        code_bg = DARK_THEME["bg"] if self.theme_manager.dark_theme.get() else "white"
        code_fg = DARK_THEME["fg"] if self.theme_manager.dark_theme.get() else "black"
        
        self.code_display = tk.Text(
            code_frame,
            wrap=tk.NONE,
            font=("Consolas", 11),
            bg=code_bg,
            fg=code_fg,
            insertbackground=code_fg,
            selectbackground=DARK_THEME["select_bg"] if self.theme_manager.dark_theme.get() else "#316AC5",
            selectforeground=DARK_THEME["select_fg"] if self.theme_manager.dark_theme.get() else "white",
            tabs=('1c', '2c', '3c', '4c', '5c', '6c', '7c', '8c'),
            state="disabled"
        )
        
        # Add scrollbars for code display
        v_scrollbar = ttk.Scrollbar(code_frame, orient="vertical", command=self.code_display.yview)
        h_scrollbar = ttk.Scrollbar(code_frame, orient="horizontal", command=self.code_display.xview)
        self.code_display.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and code display
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.code_display.pack(side="left", fill="both", expand=True)
        
        # Add line numbers for code display
        self.add_line_numbers(self.code_display, code_frame)
    
    def show_code_in_pane(self, code_info):
        """Show specific code block in the smart code pane"""
        # Find the index of this code block
        for i, block in enumerate(self.code_blocks):
            if (block['code'] == code_info['code'] and 
                block['timestamp'] == code_info['timestamp']):
                self.current_code_index = i
                break
        
        self.update_code_pane()
        self.show_code_pane()
    
    def show_code_pane(self):
        """Show the smart code pane"""
        self.code_pane.pack(fill="both", expand=True, padx=8, pady=8)
    
    def hide_code_pane(self):
        """Hide the smart code pane"""
        self.code_pane.pack_forget()
    
    def update_code_pane(self):
        """Update the code pane with current code block"""
        if not self.code_blocks:
            return
        
        # Ensure current index is valid
        if self.current_code_index >= len(self.code_blocks):
            self.current_code_index = len(self.code_blocks) - 1
        elif self.current_code_index < 0:
            self.current_code_index = 0
        
        current_code = self.code_blocks[self.current_code_index]
        
        # Update info label
        info_text = (f"Code {self.current_code_index + 1} of {len(self.code_blocks)}: "
                    f"📄 {current_code['filename']} ({current_code['description']}) "
                    f"| From: {current_code['sender']} | Type: {current_code['type'].upper()}")
        self.code_info_label.config(text=info_text)
        
        # Update navigation buttons
        self.nav_buttons['prev'].config(state="normal" if self.current_code_index > 0 else "disabled")
        self.nav_buttons['next'].config(state="normal" if self.current_code_index < len(self.code_blocks) - 1 else "disabled")
        
        # Enable action buttons
        for button in self.action_buttons.values():
            button.config(state="normal")
        
        # Update code display
        self.code_display.config(state="normal")
        self.code_display.delete(1.0, tk.END)
        self.code_display.insert(1.0, current_code['code'])
        self.code_display.config(state="disabled")
    
    def show_previous_code(self):
        """Show the previous code block"""
        if self.current_code_index > 0:
            self.current_code_index -= 1
            self.update_code_pane()
    
    def show_next_code(self):
        """Show the next code block"""
        if self.current_code_index < len(self.code_blocks) - 1:
            self.current_code_index += 1
            self.update_code_pane()
    
    def run_current_code(self):
        """Run the currently displayed code"""
        if self.code_blocks and self.current_code_index < len(self.code_blocks):
            current_code = self.code_blocks[self.current_code_index]
            self.run_code(current_code['code'])
    
    def save_current_code(self):
        """Save the currently displayed code"""
        if self.code_blocks and self.current_code_index < len(self.code_blocks):
            current_code = self.code_blocks[self.current_code_index]
            self.save_code_with_info(current_code)
    
    def copy_current_code(self):
        """Copy the currently displayed code to clipboard"""
        if self.code_blocks and self.current_code_index < len(self.code_blocks):
            current_code = self.code_blocks[self.current_code_index]
            self.copy_to_clipboard(current_code['code'])
