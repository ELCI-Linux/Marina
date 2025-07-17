# priming_manager.py
import sys
import os
import json
import subprocess
import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from brain.prime import build_directory_structure, get_neofetch_output, get_installed_applications, compose_priming_message

class PrimingManager:
    def __init__(self, chat_feed=None, log_callback=None):
        self.chat_feed = chat_feed
        self.log_callback = log_callback
        self.priming_text = None
        self.last_updated = None
        self.marina_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
    def log_message(self, message):
        """Log a message if callback is available"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(f"[PRIMING] {message}")
    
    def get_priming_text(self, force_refresh=False):
        """Get the priming text, either from cache or by regenerating"""
        if self.priming_text is None or force_refresh:
            self.log_message("Generating priming text...")
            self.priming_text = self.generate_priming_text()
            self.last_updated = datetime.datetime.now()
            self.log_message("Priming text generated successfully")
        
        return self.priming_text
    
    def generate_priming_text(self):
        """Generate the complete priming text using the prime.py module"""
        try:
            # Build directory structure
            dir_json = build_directory_structure(self.marina_root)
            
            # Generate the priming message
            priming_message = compose_priming_message(dir_json)
            
            return priming_message
            
        except Exception as e:
            self.log_message(f"Error generating priming text: {e}")
            return f"[PRIMING ERROR] Could not generate priming text: {str(e)}"
    
    def display_priming_info(self):
        """Display priming information in the chat feed"""
        if not self.chat_feed:
            return
        
        # Get the priming text
        priming_text = self.get_priming_text()
        
        # Split the priming text into logical sections for better display
        sections = priming_text.split('\n\n')
        
        for section in sections:
            if not section.strip():
                continue
                
            # Determine the appropriate tag based on content
            if section.startswith('You are being activated'):
                tag = "prompt"
                sender = "Priming"
            elif 'SYSTEM INFORMATION:' in section:
                tag = "action"
                sender = "System"
            elif section.startswith('Below is a full JSON'):
                tag = "action"
                sender = "System"
                # Truncate file structure for display
                if len(section) > 500:
                    section = section[:500] + "...\n[File structure truncated for display]"
            elif 'ACTION ENGINE SYNTAX:' in section:
                tag = "action"
                sender = "Action Engine"
            elif section.startswith('From this point on:'):
                tag = "prompt"
                sender = "Instructions"
            elif section.startswith('IMPORTANT - RESPONSE GUIDELINES:'):
                tag = "prompt"
                sender = "Guidelines"
            else:
                tag = "prompt"
                sender = "Priming"
            
            # Add to chat feed
            self.chat_feed.append_chat(sender, section.strip(), tag)
    
    def get_system_info(self):
        """Get just the system information part"""
        try:
            neofetch_output = get_neofetch_output()
            applications_info = get_installed_applications()
            
            system_info = f"""SYSTEM INFORMATION:
{neofetch_output}
{applications_info}"""
            
            return system_info
            
        except Exception as e:
            self.log_message(f"Error getting system info: {e}")
            return f"[SYSTEM INFO ERROR] Could not retrieve system information: {str(e)}"
    
    def get_file_structure(self):
        """Get just the file structure part"""
        try:
            dir_json = build_directory_structure(self.marina_root)
            return json.dumps(dir_json, indent=2)
            
        except Exception as e:
            self.log_message(f"Error getting file structure: {e}")
            return f"[FILE STRUCTURE ERROR] Could not retrieve file structure: {str(e)}"
    
    def get_action_engine_syntax(self):
        """Get the action engine syntax documentation"""
        return """ACTION ENGINE SYNTAX:
You have direct access to the host system through the action_engine module. To execute shell commands, use the following syntax:

[action] <command>

Examples:
- [action] ls -la
- [action] pwd
- [action] cd /home/user/documents
- [action] git status
- [action] python3 script.py
- [action] pip install requests
- [action] cat file.txt
- [action] mkdir new_folder
- [action] rm unwanted_file.txt

Command Aliases (automatically normalized):
- dir → ls
- list → ls
- remove → rm
- copy → cp
- move → mv
- make → mkdir
- clone → git clone
- update → apt update
- install → apt install
- who → whoami
- where → pwd

Important Notes:
- Commands are executed in the current working directory
- Use absolute paths when needed
- The 'cd' command will change the working directory for subsequent commands
- Output (stdout) and errors (stderr) are captured and displayed
- Commands run with your current user permissions
- Be mindful of system security and only execute safe commands"""
    
    def get_priming_summary(self):
        """Get a summary of the priming information"""
        try:
            file_count = len(self.get_file_structure().split('\n'))
            
            summary = f"""Marina Priming Summary:
- Framework: Marina Agentic Intelligence Framework
- Type: Decentralized, modular AI system
- Capabilities: GUI, CLI, autonomous daemon loops
- File Structure: {file_count} lines of directory structure
- Action Engine: Direct system access via [action] syntax
- Last Updated: {self.last_updated.strftime('%Y-%m-%d %H:%M:%S') if self.last_updated else 'Not generated'}
- Root Directory: {self.marina_root}"""
            
            return summary
            
        except Exception as e:
            return f"Priming Summary Error: {str(e)}"
    
    def refresh_priming(self):
        """Force refresh the priming text"""
        self.log_message("Refreshing priming text...")
        self.priming_text = None
        return self.get_priming_text(force_refresh=True)
    
    def create_primed_prompt(self, user_input, previous_responses=None):
        """Create a primed prompt by combining priming text with user input and previous responses"""
        priming_text = self.get_priming_text()
        
        if previous_responses and len(previous_responses) > 0:
            # Add previous LLM responses
            llm_reactions = "\n\n".join([
                f"[{name} response to previous prompt]:\n{resp}" 
                for name, resp in previous_responses.items()
            ])
            
            primed_prompt = f"{priming_text}\n\n{llm_reactions}\n\nUser: {user_input}"
        else:
            # First prompt
            primed_prompt = f"{priming_text}\n\nUser: {user_input}"
        
        return primed_prompt
