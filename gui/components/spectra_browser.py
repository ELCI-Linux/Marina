#!/usr/bin/env python3
"""
Spectra Browser Component for Marina's GUI
Integrates the autonomous browser system with the main GUI interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import threading
import time
from datetime import datetime
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import Spectra components
from spectra import (
    SpectraCore, SpectraConfig, SpectraMode, ExecutionPriority, 
    ExecutionResult, quick_start, get_welcome_message
)

class SpectraBrowserWindow:
    """
    Autonomous browser window that integrates with Marina's GUI
    """
    
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme_manager = theme_manager
        self.window = None
        self.spectra_core = None
        self.is_running = False
        self.current_session_id = None
        self.execution_history = []
        
        # GUI components
        self.intent_entry = None
        self.console_output = None
        self.session_list = None
        self.status_label = None
        self.browser_button = None
        
        # Create separate event loop for async operations
        self.loop = None
        self.loop_thread = None
        
    def create_browser_window(self):
        """Create the browser control window"""
        if self.window is not None:
            self.window.lift()
            return
            
        self.window = tk.Toplevel(self.parent)
        self.window.title("🌐 Marina Spectra - Autonomous Browser")
        self.window.geometry("1000x700")
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Apply theme
        self.theme_manager.apply_theme_to_window(self.window)
        
        # Create main layout
        self.create_layout()
        
        # Start async event loop
        self.start_async_loop()
        
        # Initialize Spectra
        self.initialize_spectra()
        
    def create_layout(self):
        """Create the GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title and status
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="🚀 Marina Spectra Autonomous Browser", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side="left")
        
        self.status_label = ttk.Label(title_frame, text="Status: Initializing...", 
                                     foreground="orange")
        self.status_label.pack(side="right")
        
        # Control panel
        control_frame = ttk.LabelFrame(main_frame, text="Browser Controls", padding=10)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Intent input
        intent_frame = ttk.Frame(control_frame)
        intent_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(intent_frame, text="Intent:").pack(side="left")
        self.intent_entry = ttk.Entry(intent_frame, width=60)
        self.intent_entry.pack(side="left", padx=(10, 0), fill="x", expand=True)
        self.intent_entry.bind("<Return>", self.on_intent_submit)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill="x", pady=(5, 0))
        
        execute_btn = ttk.Button(button_frame, text="▶️ Execute Intent", 
                                command=self.execute_intent)
        execute_btn.pack(side="left", padx=(0, 5))
        
        self.browser_button = ttk.Button(button_frame, text="🌐 Open Browser", 
                                        command=self.open_browser)
        self.browser_button.pack(side="left", padx=5)
        
        stop_btn = ttk.Button(button_frame, text="⏹️ Stop", 
                             command=self.stop_execution)
        stop_btn.pack(side="left", padx=5)
        
        clear_btn = ttk.Button(button_frame, text="🗑️ Clear", 
                              command=self.clear_console)
        clear_btn.pack(side="left", padx=5)
        
        # Priority selector
        priority_frame = ttk.Frame(control_frame)
        priority_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(priority_frame, text="Priority:").pack(side="left")
        self.priority_var = tk.StringVar(value="MEDIUM")
        priority_combo = ttk.Combobox(priority_frame, textvariable=self.priority_var,
                                     values=["CRITICAL", "HIGH", "MEDIUM", "LOW", "BACKGROUND"],
                                     state="readonly", width=12)
        priority_combo.pack(side="left", padx=(10, 0))
        
        # Timeout setting
        ttk.Label(priority_frame, text="Timeout (s):").pack(side="left", padx=(20, 0))
        self.timeout_var = tk.StringVar(value="300")
        timeout_entry = ttk.Entry(priority_frame, textvariable=self.timeout_var, width=8)
        timeout_entry.pack(side="left", padx=(10, 0))
        
        # Middle section with tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(0, 10))
        
        # Console tab
        console_frame = ttk.Frame(notebook)
        notebook.add(console_frame, text="Console Output")
        
        # Console output
        console_container = ttk.Frame(console_frame)
        console_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.console_output = scrolledtext.ScrolledText(console_container, 
                                                       wrap=tk.WORD,
                                                       height=15,
                                                       state=tk.DISABLED)
        self.console_output.pack(fill="both", expand=True)
        
        # Sessions tab
        sessions_frame = ttk.Frame(notebook)
        notebook.add(sessions_frame, text="Active Sessions")
        
        sessions_container = ttk.Frame(sessions_frame)
        sessions_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Session list with scrollbar
        session_list_frame = ttk.Frame(sessions_container)
        session_list_frame.pack(fill="both", expand=True)
        
        self.session_list = ttk.Treeview(session_list_frame, 
                                        columns=("ID", "Name", "Status", "URL", "Created"),
                                        show="headings")
        
        # Configure columns
        self.session_list.heading("ID", text="Session ID")
        self.session_list.heading("Name", text="Name")
        self.session_list.heading("Status", text="Status")
        self.session_list.heading("URL", text="Current URL")
        self.session_list.heading("Created", text="Created")
        
        self.session_list.column("ID", width=200)
        self.session_list.column("Name", width=150)
        self.session_list.column("Status", width=100)
        self.session_list.column("URL", width=300)
        self.session_list.column("Created", width=120)
        
        # Scrollbar for session list
        session_scrollbar = ttk.Scrollbar(session_list_frame, orient="vertical", 
                                         command=self.session_list.yview)
        self.session_list.configure(yscrollcommand=session_scrollbar.set)
        
        self.session_list.pack(side="left", fill="both", expand=True)
        session_scrollbar.pack(side="right", fill="y")
        
        # Session control buttons
        session_btn_frame = ttk.Frame(sessions_container)
        session_btn_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(session_btn_frame, text="📋 Refresh Sessions", 
                  command=self.refresh_sessions).pack(side="left", padx=(0, 5))
        ttk.Button(session_btn_frame, text="🗑️ Terminate Session", 
                  command=self.terminate_selected_session).pack(side="left", padx=5)
        
        # History tab
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="Execution History")
        
        self.history_text = scrolledtext.ScrolledText(history_frame, 
                                                     wrap=tk.WORD,
                                                     height=15,
                                                     state=tk.DISABLED)
        self.history_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status bar
        status_bar = ttk.Frame(main_frame)
        status_bar.pack(fill="x", pady=(5, 0))
        
        self.system_status = ttk.Label(status_bar, text="System Status: Ready")
        self.system_status.pack(side="left")
        
        # Add some example intents
        self.add_example_intents()
        
    def add_example_intents(self):
        """Add example intent buttons"""
        examples_frame = ttk.LabelFrame(self.window.children['!frame'], text="Example Intents", padding=5)
        examples_frame.pack(fill="x", pady=(10, 0))
        
        examples = [
            "Navigate to https://google.com",
            "Search for 'autonomous browsing' on Google",
            "Take a screenshot of the current page",
            "Extract all links from the page",
            "Navigate to GitHub and search for 'python automation'",
            "Find the weather forecast for today"
        ]
        
        for i, example in enumerate(examples):
            btn = ttk.Button(examples_frame, text=example, 
                           command=lambda ex=example: self.set_intent(ex))
            btn.pack(side="left" if i < 3 else "right", padx=2, pady=2)
            if i == 2:  # Add a line break after 3 buttons
                ttk.Separator(examples_frame, orient="horizontal").pack(fill="x", pady=5)
        
    def set_intent(self, intent_text):
        """Set the intent text in the input field"""
        self.intent_entry.delete(0, tk.END)
        self.intent_entry.insert(0, intent_text)
        
    def start_async_loop(self):
        """Start the async event loop in a separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
            
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
    def initialize_spectra(self):
        """Initialize the Spectra core system"""
        def init_async():
            try:
                # Create Spectra configuration
                config = SpectraConfig(
                    mode=SpectraMode.AUTONOMOUS,
                    max_concurrent_sessions=5,
                    default_timeout=300.0,
                    enable_media_perception=True,
                    enable_action_validation=True,
                    enable_session_persistence=True,
                    storage_dir="./spectra_data",
                    encrypt_sessions=True,
                    sandbox_mode=True
                )
                
                # Initialize Spectra
                self.spectra_core = SpectraCore(config)
                
                # Schedule initialization
                future = asyncio.run_coroutine_threadsafe(
                    self.spectra_core.initialize(), self.loop
                )
                
                # Wait for initialization with timeout
                future.result(timeout=30)
                
                # Update status
                self.window.after(0, lambda: self.update_status("Ready", "green"))
                self.window.after(0, lambda: self.log_message("🚀 Spectra initialized successfully!"))
                self.window.after(0, lambda: self.log_message(get_welcome_message()))
                
                self.is_running = True
                
                # Start periodic updates
                self.window.after(1000, self.update_system_info)
                
            except Exception as e:
                error_msg = f"Failed to initialize Spectra: {str(e)}"
                self.window.after(0, lambda: self.update_status("Error", "red"))
                self.window.after(0, lambda: self.log_message(f"❌ {error_msg}"))
                
        # Run initialization in background
        thread = threading.Thread(target=init_async, daemon=True)
        thread.start()
        
    def update_status(self, status, color="black"):
        """Update the status label"""
        if self.status_label:
            self.status_label.config(text=f"Status: {status}", foreground=color)
            
    def log_message(self, message):
        """Log a message to the console"""
        if self.console_output:
            self.console_output.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.console_output.insert(tk.END, f"[{timestamp}] {message}\n")
            self.console_output.config(state=tk.DISABLED)
            self.console_output.see(tk.END)
            
    def on_intent_submit(self, event=None):
        """Handle intent submission via Enter key"""
        self.execute_intent()
        
    def execute_intent(self):
        """Execute the entered intent"""
        if not self.is_running or not self.spectra_core:
            messagebox.showerror("Error", "Spectra is not initialized!")
            return
            
        intent_text = self.intent_entry.get().strip()
        if not intent_text:
            messagebox.showwarning("Warning", "Please enter an intent!")
            return
            
        # Get priority and timeout
        try:
            priority = ExecutionPriority(self.priority_var.get())
            timeout = float(self.timeout_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid timeout value!")
            return
            
        # Log the intent
        self.log_message(f"🎯 Executing intent: {intent_text}")
        self.log_message(f"   Priority: {priority.value}, Timeout: {timeout}s")
        
        # Update status
        self.update_status("Executing...", "orange")
        
        # Execute asynchronously
        def execute_async():
            try:
                # Execute the intent
                future = asyncio.run_coroutine_threadsafe(
                    self.spectra_core.execute_intent(
                        intent_text,
                        priority=priority,
                        timeout=timeout
                    ), self.loop
                )
                
                # Get result
                result = future.result()
                
                # Update GUI with result
                self.window.after(0, lambda: self.handle_execution_result(result, intent_text))
                
            except Exception as e:
                error_msg = f"Execution failed: {str(e)}"
                self.window.after(0, lambda: self.log_message(f"❌ {error_msg}"))
                self.window.after(0, lambda: self.update_status("Ready", "green"))
                
        # Run in background
        thread = threading.Thread(target=execute_async, daemon=True)
        thread.start()
        
    def handle_execution_result(self, result: ExecutionResult, intent_text: str):
        """Handle execution result"""
        # Log result
        if result.success:
            self.log_message(f"✅ Intent executed successfully!")
            self.log_message(f"   Actions performed: {result.actions_performed}")
            self.log_message(f"   Execution time: {result.execution_time:.2f}s")
            
            # Log validation results
            if result.validation_results:
                self.log_message(f"   Validation results: {len(result.validation_results)} checks")
                
            # Log screenshots
            if result.screenshots:
                self.log_message(f"   Screenshots saved: {len(result.screenshots)}")
                
        else:
            self.log_message(f"❌ Intent execution failed!")
            if result.error_message:
                self.log_message(f"   Error: {result.error_message}")
                
        # Add to history
        self.execution_history.append({
            'timestamp': datetime.now(),
            'intent': intent_text,
            'result': result
        })
        
        # Update history display
        self.update_history_display()
        
        # Clear intent entry
        self.intent_entry.delete(0, tk.END)
        
        # Update status
        self.update_status("Ready", "green")
        
        # Refresh sessions
        self.refresh_sessions()
        
    def update_history_display(self):
        """Update the history display"""
        if not self.history_text:
            return
            
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        
        for entry in self.execution_history[-20:]:  # Show last 20 entries
            timestamp = entry['timestamp'].strftime("%H:%M:%S")
            intent = entry['intent']
            result = entry['result']
            
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            self.history_text.insert(tk.END, f"[{timestamp}] {status}\n")
            self.history_text.insert(tk.END, f"Intent: {intent}\n")
            
            if result.success:
                self.history_text.insert(tk.END, f"Actions: {result.actions_performed}, ")
                self.history_text.insert(tk.END, f"Time: {result.execution_time:.2f}s\n")
            else:
                self.history_text.insert(tk.END, f"Error: {result.error_message}\n")
                
            self.history_text.insert(tk.END, "-" * 50 + "\n")
            
        self.history_text.config(state=tk.DISABLED)
        self.history_text.see(tk.END)
        
    def open_browser(self):
        """Open browser with current session"""
        if not self.is_running or not self.spectra_core:
            messagebox.showerror("Error", "Spectra is not initialized!")
            return
            
        self.log_message("🌐 Opening browser window...")
        
        # For now, just execute a simple navigation intent
        intent = "Navigate to https://google.com and take a screenshot"
        self.intent_entry.delete(0, tk.END)
        self.intent_entry.insert(0, intent)
        self.execute_intent()
        
    def stop_execution(self):
        """Stop current execution"""
        self.log_message("⏹️ Stopping execution...")
        # In a real implementation, you'd cancel the running task
        self.update_status("Stopped", "red")
        
    def clear_console(self):
        """Clear the console output"""
        if self.console_output:
            self.console_output.config(state=tk.NORMAL)
            self.console_output.delete(1.0, tk.END)
            self.console_output.config(state=tk.DISABLED)
            
    def refresh_sessions(self):
        """Refresh the session list"""
        if not self.is_running or not self.spectra_core or not self.session_list:
            return
            
        def refresh_async():
            try:
                # Get session list
                future = asyncio.run_coroutine_threadsafe(
                    self.spectra_core.get_session_list(), self.loop
                )
                
                sessions = future.result(timeout=10)
                
                # Update GUI
                self.window.after(0, lambda: self.update_session_list(sessions))
                
            except Exception as e:
                self.window.after(0, lambda: self.log_message(f"Failed to refresh sessions: {e}"))
                
        thread = threading.Thread(target=refresh_async, daemon=True)
        thread.start()
        
    def update_session_list(self, sessions):
        """Update the session list display"""
        # Clear existing items
        for item in self.session_list.get_children():
            self.session_list.delete(item)
            
        # Add sessions
        for session in sessions:
            self.session_list.insert("", "end", values=(
                session['id'][:8] + "...",  # Truncate ID
                session['name'],
                session['status'],
                session['current_url'][:50] + "..." if len(session['current_url']) > 50 else session['current_url'],
                session['created_at'][:16]  # Just date and time
            ))
            
    def terminate_selected_session(self):
        """Terminate the selected session"""
        selection = self.session_list.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a session to terminate!")
            return
            
        item = self.session_list.item(selection[0])
        session_id = item['values'][0]
        
        if messagebox.askyesno("Confirm", f"Terminate session {session_id}?"):
            self.log_message(f"🗑️ Terminating session: {session_id}")
            
            def terminate_async():
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self.spectra_core.terminate_session(session_id), self.loop
                    )
                    
                    success = future.result(timeout=10)
                    
                    if success:
                        self.window.after(0, lambda: self.log_message(f"✅ Session terminated: {session_id}"))
                        self.window.after(0, self.refresh_sessions)
                    else:
                        self.window.after(0, lambda: self.log_message(f"❌ Failed to terminate session: {session_id}"))
                        
                except Exception as e:
                    self.window.after(0, lambda: self.log_message(f"❌ Error terminating session: {e}"))
                    
            thread = threading.Thread(target=terminate_async, daemon=True)
            thread.start()
            
    def update_system_info(self):
        """Update system information periodically"""
        if not self.is_running or not self.spectra_core:
            return
            
        def update_async():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.spectra_core.get_system_status(), self.loop
                )
                
                status = future.result(timeout=5)
                
                # Update system status
                uptime = int(status.get('uptime', 0))
                active_sessions = status.get('active_sessions', 0)
                queue_size = status.get('queue_size', 0)
                
                status_text = f"Uptime: {uptime}s | Sessions: {active_sessions} | Queue: {queue_size}"
                self.window.after(0, lambda: self.system_status.config(text=status_text))
                
            except Exception as e:
                pass  # Ignore errors in periodic updates
                
        thread = threading.Thread(target=update_async, daemon=True)
        thread.start()
        
        # Schedule next update
        if self.is_running:
            self.window.after(5000, self.update_system_info)
            
    def on_window_close(self):
        """Handle window closing"""
        self.is_running = False
        
        # Shutdown Spectra
        if self.spectra_core:
            def shutdown_async():
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self.spectra_core.shutdown(), self.loop
                    )
                    future.result(timeout=10)
                except Exception as e:
                    print(f"Error shutting down Spectra: {e}")
                    
            thread = threading.Thread(target=shutdown_async, daemon=True)
            thread.start()
            
        # Stop event loop
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            
        # Close window
        self.window.destroy()
        self.window = None


class SpectraBrowserManager:
    """
    Manager class for the Spectra browser integration
    """
    
    def __init__(self, theme_manager):
        self.theme_manager = theme_manager
        self.browser_window = None
        
    def open_browser(self, parent):
        """Open the browser window"""
        if self.browser_window is None:
            self.browser_window = SpectraBrowserWindow(parent, self.theme_manager)
            
        self.browser_window.create_browser_window()
        
    def is_open(self):
        """Check if browser window is open"""
        return self.browser_window is not None and self.browser_window.window is not None
        
    def close_browser(self):
        """Close the browser window"""
        if self.browser_window:
            self.browser_window.on_window_close()
            self.browser_window = None
