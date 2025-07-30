#!/usr/bin/env python3
"""
Joan Interface - Marina's ASCII-Enhanced Terminal Assistant
Main interface module that integrates ASCII capabilities with Marina's core systems

Part of Marina AI System
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

# Add Marina's root directory to path for imports
marina_root = Path(__file__).parent.parent
sys.path.insert(0, str(marina_root))

from ascii_toolkit import ASCIIToolkit
from tplay import TPlay

class JoanInterface:
    """Joan - Marina's ASCII-Enhanced Terminal Assistant"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Joan with ASCII capabilities
        
        Args:
            config_path: Optional path to Joan's configuration file
        """
        self.ascii_toolkit = ASCIIToolkit()
        self.marina_root = marina_root
        self.config_path = config_path or self.marina_root / "Joan" / "joan_config.json"
        self.config = self._load_config()
        self.session_start = datetime.now()
        self.tplay = TPlay()
        
        # Initialize session
        self._initialize_session()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load Joan's configuration"""
        default_config = {
            "interface_width": 80,
            "default_banner_font": "standard",
            "default_box_style": "rounded",
            "show_system_status": True,
            "auto_detect_images": True,
            "marina_integration": True,
            "themes": {
                "default": {
                    "border_style": "rounded",
                    "progress_fill": "█",
                    "progress_empty": "░"
                }
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                print(f"⚠️  Warning: Could not load config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save current configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def _initialize_session(self):
        """Initialize Joan's session"""
        # Ensure Joan directory exists
        os.makedirs(self.marina_root / "Joan", exist_ok=True)
        
        # Create session log if needed
        self.session_log = []
        
    def display_welcome(self, username: str = None) -> str:
        """Display Joan's welcome screen
        
        Args:
            username: Username to display (auto-detected if None)
            
        Returns:
            Welcome screen text
        """
        if not username:
            username = os.getenv('USER', 'User')
        
        welcome_screen = self.ascii_toolkit.generate_welcome_screen(username)
        
        # Add current time and session info
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_info = f"Session started: {current_time}\\nMarina Path: {self.marina_root}"
        
        session_box = self.ascii_toolkit.create_box(
            session_info, 
            self.config["themes"]["default"]["border_style"], 
            1, 
            "Session Information"
        )
        
        full_welcome = f"{welcome_screen}\\n{session_box}"
        
        print(full_welcome)
        return full_welcome
    
    def process_command(self, command: str) -> str:
        """Process a command through Joan's interface
        
        Args:
            command: Command string to process
            
        Returns:
            Formatted response
        """
        command = command.strip().lower()
        
        # Log the command
        self.session_log.append({
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "type": "command"
        })
        
        # ASCII-specific commands
        if command.startswith("ascii"):
            return self._handle_ascii_command(command)
        elif command.startswith("banner"):
            return self._handle_banner_command(command)
        elif command.startswith("box"):
            return self._handle_box_command(command)
        elif command.startswith("tplay"):
            return self._handle_tplay_command(command)
        elif command.startswith("status"):
            return self._handle_status_command()
        elif command.startswith("config"):
            return self._handle_config_command(command)
        elif command in ["help", "?"]:
            return self._show_help()
        elif command in ["exit", "quit", "q"]:
            return self._handle_exit()
        else:
            # Try to delegate to Marina if integration is enabled
            if self.config.get("marina_integration", True):
                return self._delegate_to_marina(command)
            else:
                return self._create_error_response(f"Unknown command: {command}")
    
    def _handle_ascii_command(self, command: str) -> str:
        """Handle ASCII-related commands"""
        parts = command.split()
        
        if len(parts) < 2:
            return self._create_error_response("Usage: ascii <image_path> [width]")
        
        image_path = parts[1]
        width = int(parts[2]) if len(parts) > 2 else self.config["interface_width"]
        
        if not os.path.exists(image_path):
            return self._create_error_response(f"Image not found: {image_path}")
        
        ascii_art = self.ascii_toolkit.image_to_ascii(image_path, width)
        
        if ascii_art:
            title = f"ASCII Art: {os.path.basename(image_path)}"
            boxed_art = self.ascii_toolkit.create_box(ascii_art, "thin", 1, title)
            return boxed_art
        else:
            return self._create_error_response("Failed to convert image to ASCII")
    
    def _handle_banner_command(self, command: str) -> str:
        """Handle banner creation commands"""
        parts = command.split(maxsplit=1)
        
        if len(parts) < 2:
            return self._create_error_response("Usage: banner <text>")
        
        text = parts[1]
        banner = self.ascii_toolkit.create_text_banner(text, self.config["default_banner_font"])
        
        return banner
    
    def _handle_box_command(self, command: str) -> str:
        """Handle box creation commands"""
        parts = command.split(maxsplit=1)
        
        if len(parts) < 2:
            return self._create_error_response("Usage: box <text>")
        
        text = parts[1]
        boxed_text = self.ascii_toolkit.create_box(text, self.config["default_box_style"], 2)
        
        return boxed_text
    
    def _handle_tplay_command(self, command: str) -> str:
        """Handle tplay media player commands"""
        parts = command.split()
        if len(parts) < 2:
            return self._create_error_response("Usage: tplay <play|pause|stop|status|formats|find> [options]")

        subcommand = parts[1]
        
        if subcommand == "play":
            if len(parts) < 3:
                return self._create_error_response("Usage: tplay play <media_path> [volume]")
            media_path = parts[2]
            volume = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 80
            result = self.tplay.play(media_path, volume)
            
        elif subcommand == "pause":
            result = self.tplay.pause()
            
        elif subcommand == "stop":
            result = self.tplay.stop()
            
        elif subcommand == "status":
            result = self.tplay.status()
            
        elif subcommand == "formats":
            result = self.tplay.list_supported_formats()
            
        elif subcommand == "find":
            if len(parts) < 3:
                return self._create_error_response("Usage: tplay find <directory>")
            directory = parts[2]
            files = self.tplay.find_media_files(directory)
            if files:
                file_list = "\n".join(f"  • {os.path.basename(f)}" for f in files[:15])
                if len(files) > 15:
                    file_list += f"\n  ... and {len(files) - 15} more files"
                result = f"📁 Found {len(files)} media files in {directory}:\n{file_list}"
            else:
                result = f"📁 No media files found in {directory}"
                
        else:
            return self._create_error_response(f"Unknown tplay command: {subcommand}")
        
        # Format result in a nice box
        return self.ascii_toolkit.create_box(result, "thin", 1, "🎵 TPlay Media Player")

    def _handle_status_command(self) -> str:
        """Handle system status display"""
        try:
            # Try to get system status (simplified version)
            status_data = self._get_system_status()
            status_display = self.ascii_toolkit.display_system_status(status_data)
            
            return self.ascii_toolkit.create_box(
                status_display, 
                "double", 
                2, 
                "System Status"
            )
        except Exception as e:
            return self._create_error_response(f"Error getting system status: {e}")
    
    def _handle_config_command(self, command: str) -> str:
        """Handle configuration commands"""
        parts = command.split()
        
        if len(parts) == 1:
            # Show current config
            config_text = json.dumps(self.config, indent=2)
            return self.ascii_toolkit.create_box(config_text, "thin", 1, "Joan Configuration")
        
        elif len(parts) == 3 and parts[1] == "set":
            # Set configuration value
            key_value = parts[2]
            if '=' in key_value:
                key, value = key_value.split('=', 1)
                
                # Convert value type
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                
                self.config[key] = value
                self._save_config()
                return self._create_success_response(f"Set {key} = {value}")
            
        return self._create_error_response("Usage: config [set key=value]")
    
    def _show_help(self) -> str:
        """Show help information"""
        help_text = """Joan - Marina's ASCII Interface Assistant

Available Commands:
  ascii <image_path> [width]  - Convert image to ASCII art
  banner <text>               - Create ASCII text banner
  box <text>                  - Put text in a decorative box
  tplay play <media_path>     - Play a media file
  tplay stop                  - Stop media playback
  status                      - Show system status with ASCII visualization
  config [set key=value]      - Show or modify configuration
  help, ?                     - Show this help
  exit, quit, q               - Exit Joan

ASCII Features:
  • Image to ASCII conversion
  • Text banners and figlet-style art
  • Decorative borders and frames
  • ASCII charts and progress bars
  • System status visualization

Example Usage:
  banner "HELLO WORLD"
  ascii ~/Pictures/image.png 60
  box "This text will be in a box"
  config set interface_width=100
"""
        
        return self.ascii_toolkit.create_box(help_text, "rounded", 2, "Joan Help")
    
    def _handle_exit(self) -> str:
        """Handle exit command"""
        session_duration = datetime.now() - self.session_start
        exit_message = f"Session duration: {session_duration}\\nCommands processed: {len(self.session_log)}\\nThank you for using Joan!"
        
        goodbye_banner = self.ascii_toolkit.create_text_banner("GOODBYE", "standard")
        exit_box = self.ascii_toolkit.create_box(exit_message, "rounded", 2, "Session Summary")
        
        return f"{goodbye_banner}\\n\\n{exit_box}"
    
    def _delegate_to_marina(self, command: str) -> str:
        """Delegate command to Marina system if available"""
        try:
            # Try to use Marina's CLI if available
            marina_cli = self.marina_root / "marina_cli.py"
            if marina_cli.exists():
                result = subprocess.run(
                    [sys.executable, str(marina_cli), command],
                    capture_output=True, text=True, timeout=30
                )
                
                if result.returncode == 0:
                    response = result.stdout.strip()
                    # Check if response contains image references for ASCII conversion
                    if self.config.get("auto_detect_images", True):
                        response = self._enhance_response_with_ascii(response)
                    return response
                else:
                    return self._create_error_response(f"Marina CLI error: {result.stderr}")
            else:
                return self._create_error_response("Marina integration not available")
                
        except subprocess.TimeoutExpired:
            return self._create_error_response("Marina command timed out")
        except Exception as e:
            return self._create_error_response(f"Error delegating to Marina: {e}")
    
    def _enhance_response_with_ascii(self, response: str) -> str:
        """Enhance Marina response with ASCII art if images are detected"""
        # Look for image file references in response
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        lines = response.split('\\n')
        
        for line in lines:
            for ext in image_extensions:
                if ext in line.lower():
                    # Try to extract file path
                    words = line.split()
                    for word in words:
                        if ext in word.lower() and os.path.exists(word):
                            ascii_art = self.ascii_toolkit.image_to_ascii(word, 60)
                            if ascii_art:
                                ascii_section = f"\\n\\nASCII Preview:\\n{self.ascii_toolkit.create_separator(80, '=')}\\n{ascii_art}\\n{self.ascii_toolkit.create_separator(80, '=')}"
                                response += ascii_section
                            break
        
        return response
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get basic system status information"""
        status = {}
        
        try:
            # CPU usage (simplified)
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.read().strip().split()
                status['cpu_percent'] = min(100, float(load_avg[0]) * 25)  # Rough approximation
        except:
            status['cpu_percent'] = 0
        
        try:
            # Memory usage
            with open('/proc/meminfo', 'r') as f:
                meminfo = {}
                for line in f:
                    key, value = line.split(':')
                    meminfo[key.strip()] = int(value.strip().split()[0])
                
                total_mem = meminfo['MemTotal']
                free_mem = meminfo['MemFree'] + meminfo.get('Buffers', 0) + meminfo.get('Cached', 0)
                used_mem = total_mem - free_mem
                status['memory_percent'] = (used_mem / total_mem) * 100
        except:
            status['memory_percent'] = 0
        
        try:
            # Disk usage for root partition
            statvfs = os.statvfs('/')
            total_space = statvfs.f_frsize * statvfs.f_blocks
            free_space = statvfs.f_frsize * statvfs.f_available
            used_space = total_space - free_space
            status['disk_usage'] = {'/': (used_space / total_space) * 100}
        except:
            status['disk_usage'] = {'/': 0}
        
        return status
    
    def _create_error_response(self, message: str) -> str:
        """Create formatted error response"""
        error_text = f"❌ Error: {message}"
        return self.ascii_toolkit.create_box(error_text, "thick", 2, "Error")
    
    def _create_success_response(self, message: str) -> str:
        """Create formatted success response"""
        success_text = f"✅ {message}"
        return self.ascii_toolkit.create_box(success_text, "rounded", 2, "Success")
    
    def run_interactive_session(self):
        """Run Joan in interactive mode"""
        self.display_welcome()
        
        print("\\nType 'help' for available commands, 'exit' to quit.")
        
        while True:
            try:
                command = input("\\nJoan> ").strip()
                
                if not command:
                    continue
                
                response = self.process_command(command)
                print(f"\\n{response}")
                
                if command.lower() in ['exit', 'quit', 'q']:
                    break
                    
            except KeyboardInterrupt:
                print("\\n\\n" + self._handle_exit())
                break
            except EOFError:
                print("\\n\\n" + self._handle_exit())
                break

# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Joan - Marina's ASCII Interface Assistant")
    parser.add_argument("--config", help="Path to Joan configuration file")
    parser.add_argument("--command", help="Execute single command and exit")
    parser.add_argument("--width", type=int, default=80, help="Interface width")
    
    args = parser.parse_args()
    
    # Create Joan instance
    joan = JoanInterface(args.config)
    
    if args.width != 80:
        joan.config["interface_width"] = args.width
    
    if args.command:
        # Single command mode
        response = joan.process_command(args.command)
        print(response)
    else:
        # Interactive mode
        joan.run_interactive_session()
