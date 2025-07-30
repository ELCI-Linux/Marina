#!/usr/bin/env python3
"""
Marina Natural Language Ticker Module for py3status

A Dynamic Island ticker that displays natural language descriptions of Marina's
current activities, daemon states, and system events in human-friendly format.

🧠 Features:
- Natural language descriptions of daemon activities
- Contextual system status messages
- Smooth text scrolling for long messages
- Priority-based message display
- Real-time activity streaming from Marina core

Usage in i3 config:
    order += "marina_ticker"
"""

import sys
from pathlib import Path
import os
import logging

# Set up logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - Marina Ticker - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/marina_ticker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Determine the correct path to marina_bar_core.py
current_file = Path(__file__).resolve()
logger.debug(f"Current file: {current_file}")

# If this is a symlink, get the real path
if current_file.is_symlink():
    real_file = current_file.readlink()
    if not real_file.is_absolute():
        real_file = current_file.parent / real_file
    current_file = real_file.resolve()
    logger.debug(f"Resolved symlink to: {current_file}")

# Find Marina status bar directory
marina_status_dir = None
for parent in current_file.parents:
    potential_core = parent / "marina_bar_core.py"
    if potential_core.exists():
        marina_status_dir = str(parent)
        logger.debug(f"Found marina_bar_core.py at: {potential_core}")
        break

if not marina_status_dir:
    # Fallback: try known location
    fallback_path = Path("/home/adminx/Marina/status_bar")
    if (fallback_path / "marina_bar_core.py").exists():
        marina_status_dir = str(fallback_path)
        logger.debug(f"Using fallback path: {marina_status_dir}")
    else:
        logger.error("Could not find marina_bar_core.py anywhere!")
        marina_status_dir = str(current_file.parent)

logger.debug(f"Using marina_status_dir: {marina_status_dir}")

# Add paths to sys.path
sys.path.insert(0, marina_status_dir)
marina_root_dir = str(Path(marina_status_dir).parent)
sys.path.insert(0, marina_root_dir)

logger.debug(f"Added to sys.path: {marina_status_dir}, {marina_root_dir}")

# Try to import marina_bar_core
get_marina_bar_core = None
try:
    from marina_bar_core import get_marina_bar_core
    logger.debug("Successfully imported marina_bar_core")
except ImportError as e:
    logger.error(f"Failed to import marina_bar_core: {e}")
    # Fallback: try direct import
    try:
        import importlib.util
        core_path = os.path.join(marina_status_dir, "marina_bar_core.py")
        logger.debug(f"Trying direct import from: {core_path}")
        
        if os.path.exists(core_path):
            spec = importlib.util.spec_from_file_location("marina_bar_core", core_path)
            marina_bar_core = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(marina_bar_core)
            get_marina_bar_core = marina_bar_core.get_marina_bar_core
            logger.debug("Successfully imported via direct method")
        else:
            logger.error(f"Core file does not exist at: {core_path}")
    except Exception as fallback_error:
        logger.error(f"Fallback import also failed: {fallback_error}")
import time
import textwrap
from datetime import datetime, timedelta


class Py3status:
    """
    Marina Natural Language Ticker Module
    
    Displays contextual, human-friendly status messages about Marina's current
    activities and system state. Messages scroll smoothly across the bar.
    """

    # Configuration options
    format = "Marina says: {message}"
    cache_timeout = 1
    max_message_length = 80
    scroll_speed = 2  # Characters per update
    message_timeout = 30  # Seconds before message expires
    
    # Color scheme
    color_normal = "#FFFFFF"
    color_activity = "#81C784"      # Light green for activity
    color_warning = "#FFB74D"       # Orange for warnings
    color_error = "#E57373"         # Light red for errors
    color_system = "#64B5F6"        # Light blue for system messages
    
    def __init__(self):
        self.marina_core = None
        self.current_message = ""
        self.scroll_position = 0
        self.last_message_time = None
        self.message_color = self.color_normal
        self.message_priority = 0
        
    def marina_ticker(self):
        """Main ticker method"""
        try:
            # Initialize Marina core if needed
            if not self.marina_core:
                self.marina_core = get_marina_bar_core()
            
            # Get current ticker message from Marina core
            data = self.marina_core.get_py3status_data()
            new_message = data.get("ticker_message", "")
            
            # Update message if we have a new one
            if new_message and new_message != self.current_message:
                self._set_new_message(new_message)
            
            # Check for message timeout
            if (self.last_message_time and 
                datetime.now() - self.last_message_time > timedelta(seconds=self.message_timeout)):
                self._generate_default_message(data)
            
            # Generate display text
            display_text = self._get_display_text()
            
            return {
                'full_text': display_text,
                'color': self.message_color,
                'cached_until': time.time() + self.cache_timeout,
                'separator': False,
                'separator_block_width': 30
            }
            
        except Exception as e:
            return {
                'full_text': f"Marina ticker error: {str(e)[:40]}",
                'color': self.color_error,
                'cached_until': time.time() + self.cache_timeout
            }
    
    def _set_new_message(self, message):
        """Set a new ticker message"""
        self.current_message = message
        self.scroll_position = 0
        self.last_message_time = datetime.now()
        
        # Determine message color and priority based on content
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["error", "failed", "crash", "critical"]):
            self.message_color = self.color_error
            self.message_priority = 1  # Highest priority
        elif any(word in message_lower for word in ["warning", "issue", "problem", "low"]):
            self.message_color = self.color_warning
            self.message_priority = 2
        elif any(word in message_lower for word in ["detected", "recognized", "processing", "active"]):
            self.message_color = self.color_activity
            self.message_priority = 3
        elif any(word in message_lower for word in ["system", "cpu", "memory", "network", "battery"]):
            self.message_color = self.color_system
            self.message_priority = 4
        else:
            self.message_color = self.color_normal
            self.message_priority = 5  # Lowest priority
    
    def _generate_default_message(self, data):
        """Generate a default status message when no recent activity"""
        active_daemons = data.get("active_daemons", 0)
        total_daemons = data.get("total_daemons", 0)
        priority_daemons = data.get("priority_daemons", {})
        system_status = data.get("system_status", {})
        
        # Generate contextual message based on current state
        current_time = datetime.now()
        hour = current_time.hour
        
        # Time-based greetings
        if 5 <= hour < 12:
            time_greeting = "Good morning"
        elif 12 <= hour < 17:
            time_greeting = "Good afternoon"
        elif 17 <= hour < 22:
            time_greeting = "Good evening"
        else:
            time_greeting = "Good evening"
        
        # System health summary
        if active_daemons >= total_daemons * 0.8:
            health_status = "all systems optimal"
        elif active_daemons >= total_daemons * 0.6:
            health_status = "systems running normally"
        else:
            health_status = "some systems need attention"
        
        # Highlight interesting daemon states
        status_notes = []
        
        # Check high priority daemons
        vision_info = priority_daemons.get("vision", {})
        if vision_info.get("state") == "🟢":
            status_notes.append("vision perception active")
        
        sonic_info = priority_daemons.get("sonic", {})
        if sonic_info.get("state") == "🟢":
            status_notes.append("audio processing online")
        
        # System alerts
        battery = system_status.get("battery")
        if battery and battery < 20:
            status_notes.append(f"battery at {battery}%")
        
        cpu = system_status.get("cpu", 0)
        if cpu > 80:
            status_notes.append(f"CPU usage high at {cpu:.0f}%")
        
        # Build final message
        if status_notes:
            notes_text = ", ".join(status_notes[:2])  # Limit to 2 notes
            message = f"{time_greeting} - {health_status}, {notes_text}"
        else:
            message = f"{time_greeting} - Marina is running smoothly with {health_status}"
        
        self._set_new_message(message)
    
    def _get_display_text(self):
        """Get the current display text with scrolling"""
        if not self.current_message:
            return "Marina: Ready"
        
        # Apply format
        formatted_message = self.format.format(message=self.current_message)
        
        # Handle scrolling for long messages
        if len(formatted_message) <= self.max_message_length:
            return formatted_message
        
        # Scroll long messages
        extended_message = formatted_message + "  •  "  # Add separator for seamless loop
        
        # Update scroll position
        self.scroll_position += self.scroll_speed
        if self.scroll_position >= len(extended_message):
            self.scroll_position = 0
        
        # Extract visible portion
        start_pos = self.scroll_position
        end_pos = start_pos + self.max_message_length
        
        if end_pos <= len(extended_message):
            visible_text = extended_message[start_pos:end_pos]
        else:
            # Wrap around for seamless scrolling
            part1 = extended_message[start_pos:]
            part2 = extended_message[:end_pos - len(extended_message)]
            visible_text = part1 + part2
        
        return visible_text
    
    def on_click(self, event):
        """Handle mouse clicks on ticker"""
        try:
            button = event.get('button', 1)
            
            if button == 1:  # Left click
                # Cycle through recent messages or refresh
                if self.marina_core:
                    data = self.marina_core.get_py3status_data()
                    self._generate_default_message(data)
            
            elif button == 2:  # Middle click
                # Force immediate message refresh
                self.current_message = ""
                self.last_message_time = None
                
            elif button == 3:  # Right click
                # Show detailed status in notification
                self._show_detailed_status()
        
        except Exception as e:
            pass
    
    def _show_detailed_status(self):
        """Show detailed Marina status in a notification"""
        try:
            if not self.marina_core:
                return
                
            data = self.marina_core.get_py3status_data()
            
            # Build detailed status report
            lines = ["🌊 Marina Status Report", ""]
            
            # Daemon summary
            active_daemons = data.get("active_daemons", 0)
            total_daemons = data.get("total_daemons", 0)
            lines.append(f"Active Modules: {active_daemons}/{total_daemons}")
            
            # Priority daemons
            lines.append("\nCore Systems:")
            priority_daemons = data.get("priority_daemons", {})
            for daemon_name in ["vision", "sonic", "thermal", "email", "rcs"]:
                daemon_info = priority_daemons.get(daemon_name)
                if daemon_info:
                    emoji = daemon_info["emoji"]
                    state_emoji = daemon_info["state"]
                    name = daemon_info["name"]
                    status = "Active" if state_emoji == "🟢" else "Inactive"
                    lines.append(f"  {emoji} {name}: {status}")
            
            # System status
            system_status = data.get("system_status", {})
            lines.append("\nSystem Health:")
            lines.append(f"  ⚙️ CPU: {system_status.get('cpu', 0):.1f}%")
            lines.append(f"  🧠 Memory: {system_status.get('memory', 0):.1f}%")
            
            battery = system_status.get("battery")
            if battery is not None:
                lines.append(f"  🔋 Battery: {battery}%")
            
            if system_status.get("network"):
                ssid = system_status.get("ssid", "Connected")
                lines.append(f"  📶 Network: {ssid}")
            else:
                lines.append("  📡 Network: Disconnected")
            
            # Current message
            lines.append(f"\nCurrent Message:")
            lines.append(f"  {self.current_message}")
            
            # Show notification
            import subprocess
            try:
                subprocess.run([
                    'notify-send',
                    'Marina Status Report',
                    '\n'.join(lines),
                    '--timeout=8000',
                    '--icon=info'
                ], check=False)
            except:
                pass
                
        except Exception as e:
            pass
    
    def kill(self):
        """Cleanup when module is killed"""
        # Nothing specific to cleanup for ticker
        pass

if __name__ == "__main__":
    # Test the module
    module = Py3status()
    
    try:
        while True:
            result = module.marina_ticker()
            print(f"Ticker: {result['full_text']}")
            print(f"Color: {result['color']}")
            time.sleep(1)
    except KeyboardInterrupt:
        module.kill()
