# llm_manager.py
import sys
import os
import threading
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from llm.llm_router import query_llm_response, get_local_ollama_models
from gui.themes.themes import LLMS
from gui.components.priming_manager import PrimingManager

class LLMManager:
    def __init__(self, chat_feed, priming_manager, log_callback=None):
        self.chat_feed = chat_feed
        self.priming_manager = priming_manager
        self.log_callback = log_callback
        self.llm_failed = {llm: False for llm in LLMS}
        self.llm_failure_reasons = {llm: None for llm in LLMS}
        self.loading_indicators = {}
        
    def log_message(self, message):
        """Log a message if callback is available"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(f"[LLM] {message}")
    
    def query_llm(self, llm_name, prompt, attachments=None):
        """Query a specific LLM with error handling"""
        try:
            # Create a primed prompt using PrimingManager
            primed_prompt = self.priming_manager.create_primed_prompt(prompt)
            
            # Add attachment information to the prompt if attachments exist
            if attachments:
                attachment_info = "\n\n--- Attached Files ---\n"
                for attachment in attachments:
                    attachment_info += f"File: {attachment['name']} ({attachment['size']})\n"
                    if attachment['type'] == 'text':
                        try:
                            with open(attachment['path'], 'r', encoding='utf-8') as f:
                                content = f.read()
                                attachment_info += f"Content:\n{content}\n\n"
                        except Exception as e:
                            attachment_info += f"Error reading file: {str(e)}\n\n"
                    else:
                        attachment_info += f"Type: {attachment['type']} (binary file - content not shown)\n\n"
                        
                primed_prompt += attachment_info

            self.log_message(f"Querying {llm_name} with primed prompt: {primed_prompt[:50]}...")
            
            # Call the existing LLM router
            response = query_llm_response(llm_name, primed_prompt)
            
            # Check if response indicates failure
            if response.startswith('[ERROR]') or 'error' in response.lower() or 'failed' in response.lower():
                self.handle_llm_failure(llm_name, response)
                return response
            
            # If we get here, the LLM succeeded - clear any previous failure state
            if self.llm_failed[llm_name]:
                self.clear_llm_failure(llm_name)
            
            self.log_message(f"{llm_name} responded successfully")
            return response
            
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            self.handle_llm_failure(llm_name, error_msg)
            return f"[ERROR] {error_msg}"
    
    def handle_llm_failure(self, llm_name, error_message):
        """Handle an individual LLM failure"""
        # Mark the LLM as failed
        self.llm_failed[llm_name] = True
        self.llm_failure_reasons[llm_name] = error_message
        
        # Log the failure
        self.log_message(f"{llm_name} failed: {error_message}")
        
        # Add failure message to chat
        self.chat_feed.append_chat("System", f"⚠️ {llm_name} failed: {error_message[:150]}...", "action")
        
    def clear_llm_failure(self, llm_name):
        """Clear failure state for an LLM after it succeeds"""
        self.llm_failed[llm_name] = False
        self.llm_failure_reasons[llm_name] = None
        
        # Log the successful reactivation
        self.log_message(f"{llm_name} failure cleared")
        
    def query_multiple_llms(self, llm_names, prompt, attachments=None, callback=None):
        """Query multiple LLMs in parallel"""
        results = {}
        threads = []
        
        def query_single_llm(llm_name):
            # Show processing message
            self.chat_feed.append_chat(f"→ {llm_name}", "Processing...", "prompt")
            
            # Query the LLM
            response = self.query_llm(llm_name, prompt, attachments)
            results[llm_name] = response
            
            # Display the response
            self.chat_feed.append_chat(llm_name, response, llm_name)
            
            # Call callback if provided
            if callback:
                callback(llm_name, response)
        
        # Start threads for each LLM
        for llm_name in llm_names:
            thread = threading.Thread(target=query_single_llm, args=(llm_name,))
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete (optional - they run in background)
        # for thread in threads:
        #     thread.join()
        
        return results
    
    def get_llm_status(self, llm_name):
        """Get the current status of an LLM"""
        if self.llm_failed[llm_name]:
            return "failed", self.llm_failure_reasons[llm_name]
        else:
            return "ready", None
    
    def get_available_local_models(self):
        """Get list of available local models"""
        try:
            return get_local_ollama_models()
        except Exception as e:
            self.log_message(f"Failed to get local models: {e}")
            return []
    
    def test_llm_connection(self, llm_name):
        """Test connection to a specific LLM"""
        test_prompt = "Hello, please respond with 'OK' if you can hear me."
        
        self.log_message(f"Testing connection to {llm_name}...")
        response = self.query_llm(llm_name, test_prompt)
        
        if response.startswith('[ERROR]'):
            return False, response
        else:
            return True, response
    
    def get_supported_llms(self):
        """Get list of supported LLMs with their implementation status"""
        llm_mapping = {
            "GPT-4": "gpt",
            "Claude": "claude",  # Not implemented yet
            "Gemini": "gemini",
            "DeepSeek": "deepseek",
            "Mistral": "mistral",  # Not implemented yet
            "LLaMA": "llama",  # Not implemented yet
            "Local": "local"  # Not implemented yet
        }
        
        supported = []
        for llm_name, internal_name in llm_mapping.items():
            if internal_name in ["gpt", "gemini", "deepseek"]:
                supported.append((llm_name, "implemented"))
            else:
                supported.append((llm_name, "not_implemented"))
        
        return supported
