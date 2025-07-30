#!/usr/bin/env python3
"""
Marina Daemons Status Module for py3status

A Dynamic Island-style status bar module that displays Marina's daemon states
with natural language ticker messages and expandable daemon overview.

🧠 Features:
- Real-time daemon state monitoring with emoji indicators
- Natural language ticker scrolling across the bar
- Dynamic expansion showing detailed daemon information
- Click-to-expand and auto-collapse functionality
- Priority-based daemon highlighting
- Smooth animations and visual feedback

Usage in i3 config:
    status_command py3status -c ~/.config/py3status/config
"""

import sys
from pathlib import Path
import os
import logging

# Set up logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - Marina Daemons - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/marina_daemons.log'),
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
from datetime import datetime, timedelta


class Py3status:
    """
    Marina Daemons Status Module
    
    Displays Marina daemon states in a Dynamic Island style with:
    - Compact view: Priority daemon status + ticker message
    - Expanded view: Full daemon tree with capabilities and controls
    """

    # Configuration options
    format_compact = "{priority_status} | {ticker}"
    format_expanded = "{daemon_tree}"
    cache_timeout = 1
    
    # Color scheme
    color_good = "#4CAF50"      # Green for running daemons
    color_bad = "#F44336"       # Red for inactive/error
    color_degraded = "#FF9800"  # Orange for starting/stopping
    color_inactive = "#9E9E9E"  # Gray for suspended/unknown
    
    # Animation settings
    expand_animation_duration = 0.3
    ticker_scroll_speed = 1
    
    # State
    def __init__(self):
        self.marina_core = None
        self.expanded = False
        self.last_click_time = None
        self.ticker_offset = 0
        self.expansion_start_time = None
        
    def marina_daemons(self):
        """Main status bar method"""
        try:
            # Initialize Marina core if needed
            if not self.marina_core:
                self.marina_core = get_marina_bar_core()
            
            # Get current data from Marina core
            data = self.marina_core.get_py3status_data()
            
            # Update expansion state
            self.expanded = data.get("expanded", False)
            expansion_level = data.get("expansion_level", 0.0)
            
            if self.expanded:
                return self._render_expanded_view(data, expansion_level)
            else:
                return self._render_compact_view(data)
                
        except Exception as e:
            return {
                'full_text': f"❌ Marina Status Error: {str(e)[:50]}",
                'color': self.color_bad,
                'cached_until': time.time() + self.cache_timeout
            }
    
    def _render_compact_view(self, data):
        """Render compact view with priority daemons and ticker"""
        priority_daemons = data.get("priority_daemons", {})
        ticker_message = data.get("ticker_message", "Marina operating normally")
        system_status = data.get("system_status", {})
        
        # Build priority daemon status
        priority_parts = []
        overall_color = self.color_good
        
        for daemon_name in ["vision", "sonic", "thermal", "email", "rcs"]:
            daemon_info = priority_daemons.get(daemon_name)
            if daemon_info:
                emoji = daemon_info["emoji"]
                state_emoji = daemon_info["state"]
                
                # Determine color based on state
                if state_emoji == "🟢":
                    color = self.color_good
                elif state_emoji == "🔴":
                    color = self.color_bad
                    overall_color = self.color_bad
                elif state_emoji in ["🟡", "🟠"]:
                    color = self.color_degraded
                    if overall_color == self.color_good:
                        overall_color = self.color_degraded
                else:
                    color = self.color_inactive
                
                priority_parts.append(f"{emoji}{state_emoji}")
        
        priority_status = " ".join(priority_parts) if priority_parts else "🌊"
        
        # Create scrolling ticker
        if len(ticker_message) > 50:
            # Scroll long messages
            self.ticker_offset = (self.ticker_offset + self.ticker_scroll_speed) % (len(ticker_message) + 10)
            if self.ticker_offset <= 50:
                displayed_ticker = ticker_message[:50]
            else:
                start_pos = self.ticker_offset - 50
                displayed_ticker = ticker_message[start_pos:start_pos + 50]
        else:
            displayed_ticker = ticker_message
        
        # System status indicator
        system_emoji = system_status.get("emoji", "🟢")
        
        full_text = f"{priority_status} │ {displayed_ticker} {system_emoji}"
        
        return {
            'full_text': full_text,
            'color': overall_color,
            'cached_until': time.time() + self.cache_timeout,
            'separator': False,
            'separator_block_width': 20
        }
    
    def _render_expanded_view(self, data, expansion_level):
        """Render expanded view with full daemon information"""
        priority_daemons = data.get("priority_daemons", {})
        daemon_counts = data.get("daemon_counts", {})
        active_daemons = data.get("active_daemons", 0)
        total_daemons = data.get("total_daemons", 0)
        system_status = data.get("system_status", {})
        
        # Build expanded daemon tree
        daemon_sections = []
        
        # High priority daemons (always shown)
        high_priority = []
        for daemon_name in ["vision", "sonic", "thermal"]:
            daemon_info = priority_daemons.get(daemon_name)
            if daemon_info:
                emoji = daemon_info["emoji"]
                state_emoji = daemon_info["state"]
                name = daemon_info["name"]
                
                status_text = f"{emoji} {state_emoji}"
                if expansion_level > 0.5:  # Show names when more expanded
                    status_text += f" {name[:8]}"
                
                high_priority.append(status_text)
        
        if high_priority:
            daemon_sections.append(" ".join(high_priority))
        
        # Medium priority daemons (show when expanded)
        if expansion_level > 0.3:
            medium_priority = []
            for daemon_name in ["email", "rcs", "identity"]:
                daemon_info = priority_daemons.get(daemon_name)
                if daemon_info:
                    emoji = daemon_info["emoji"]
                    state_emoji = daemon_info["state"]
                    medium_priority.append(f"{emoji}{state_emoji}")
            
            if medium_priority:
                daemon_sections.append(" ".join(medium_priority))
        
        # System info (show when fully expanded)
        if expansion_level > 0.7:
            system_parts = []
            
            # CPU and Memory
            cpu = system_status.get("cpu", 0)
            memory = system_status.get("memory", 0)
            system_parts.append(f"⚙️{cpu:.0f}%")
            system_parts.append(f"🧠{memory:.0f}%")
            
            # Battery
            battery = system_status.get("battery")
            if battery is not None:
                if battery < 20:
                    battery_emoji = "🔋"
                elif battery < 80:
                    battery_emoji = "🔋"
                else:
                    battery_emoji = "🔋"
                system_parts.append(f"{battery_emoji}{battery}%")
            
            # Network
            if system_status.get("network"):
                ssid = system_status.get("ssid")
                if ssid and len(ssid) <= 8:
                    system_parts.append(f"📶{ssid}")
                else:
                    system_parts.append("📶")
            else:
                system_parts.append("📡")
            
            daemon_sections.append(" ".join(system_parts))
        
        # Summary counts
        if expansion_level > 0.4:
            daemon_sections.append(f"[{active_daemons}/{total_daemons}]")
        
        # Collapse indicator
        if expansion_level > 0.8:
            daemon_sections.append("⤬")
        
        full_text = " ║ ".join(daemon_sections)
        
        # Color based on overall system health
        if active_daemons >= total_daemons * 0.8:
            color = self.color_good
        elif active_daemons >= total_daemons * 0.6:
            color = self.color_degraded
        else:
            color = self.color_bad
        
        return {
            'full_text': full_text,
            'color': color,
            'cached_until': time.time() + self.cache_timeout,
            'separator': False,
            'separator_block_width': 25
        }
    
    def on_click(self, event):
        """Handle mouse clicks for expansion/contraction and mini-menu interactions"""
        try:
            if not self.marina_core:
                return
            
            current_time = time.time()
            button = event.get('button', 1)
            
            # Handle different click types
            if button == 1:  # Left click
                # Check if click was on a specific daemon icon
                clicked_daemon = self._get_clicked_daemon(event)
                
                if clicked_daemon:
                    # Toggle mini-menu for the clicked daemon
                    self.marina_core.toggle_mini_menu(clicked_daemon)
                    self.last_click_time = current_time
                else:
                    # General bar click - toggle expansion
                    if self.expanded:
                        self.marina_core._trigger_contraction("left_click")
                    else:
                        self.marina_core._trigger_expansion("left_click")
            
            elif button == 2:  # Middle click
                # Force refresh of daemon states
                self._refresh_daemon_states()
            
            elif button == 3:  # Right click
                # Show context menu or detailed status
                clicked_daemon = self._get_clicked_daemon(event)
                if clicked_daemon:
                    self._show_daemon_context_menu(clicked_daemon, event)
                else:
                    self._show_daemon_details()
            
        except Exception as e:
            # Log error but don't crash the status bar
            logger.error(f"Error in on_click: {e}")
    
    def _get_clicked_daemon(self, event):
        """Determine which daemon was clicked based on event position"""
        # This is a simplified approach - in reality, you'd need to
        # analyze the click position relative to the rendered text
        # For now, we'll return None (general click)
        return None
    
    def _refresh_daemon_states(self):
        """Force refresh of all daemon states"""
        try:
            if self.marina_core:
                # Trigger a manual state check
                for daemon_name in self.marina_core.daemon_info.keys():
                    old_state = self.marina_core.daemon_info[daemon_name].state
                    new_state = self.marina_core._check_daemon_state(daemon_name)
                    if new_state != old_state:
                        self.marina_core.daemon_info[daemon_name].state = new_state
                        self.marina_core._handle_daemon_state_change(daemon_name, old_state, new_state)
                
                # Show refresh notification
                import subprocess
                try:
                    subprocess.run([
                        'notify-send',
                        '🔄 Marina Refresh',
                        'Daemon states refreshed',
                        '--timeout=2000'
                    ], check=False)
                except:
                    pass
        except Exception as e:
            logger.error(f"Error refreshing daemon states: {e}")
    
    def _show_daemon_context_menu(self, daemon_name, event):
        """Show context menu for a specific daemon"""
        try:
            if not self.marina_core or daemon_name not in self.marina_core.daemon_info:
                return
            
            daemon_info = self.marina_core.daemon_info[daemon_name]
            menu_items = self.marina_core.bar_state.mini_menu_items.get(daemon_name, [])
            
            # Build context menu text
            menu_text = [f"🎛️ {daemon_info.display_name} Menu:", ""]
            
            for item in menu_items[:5]:  # Show first 5 items
                if item["action"] == "separator":
                    menu_text.append("---")
                elif item["enabled"]:
                    menu_text.append(f"{item['icon']} {item['label']}")
                else:
                    menu_text.append(f"⚫ {item['label']} (disabled)")
            
            if len(menu_items) > 5:
                menu_text.append(f"... and {len(menu_items) - 5} more")
            
            # Show context menu as notification
            import subprocess
            try:
                subprocess.run([
                    'notify-send',
                    f'{daemon_info.emoji} {daemon_info.display_name}',
                    '\n'.join(menu_text),
                    '--timeout=8000'
                ], check=False)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error showing daemon context menu: {e}")
    
    def _show_daemon_details(self):
        """Show detailed daemon information in a notification"""
        try:
            if not self.marina_core:
                return
            
            data = self.marina_core.get_py3status_data()
            priority_daemons = data.get("priority_daemons", {})
            mini_menu_data = data.get("mini_menu_data", {})
            
            # Build detailed status message
            details = ["🌊 Marina Daemon Status:"]
            
            for daemon_name, daemon_info in priority_daemons.items():
                emoji = daemon_info["emoji"]
                state_emoji = daemon_info["state"]
                name = daemon_info["name"]
                has_menu = daemon_info.get("has_mini_menu", False)
                
                state_text = "Running" if state_emoji == "🟢" else "Inactive"
                menu_indicator = " 🎛️" if has_menu else ""
                details.append(f"  {emoji} {name}: {state_text}{menu_indicator}")
            
            # Active mini-menu info
            active_menu = mini_menu_data.get("active_menu")
            if active_menu:
                details.append(f"\n📋 Active Menu: {active_menu}")
                menu_items = mini_menu_data.get("menu_items", [])
                for item in menu_items[:3]:  # Show first 3 menu items
                    if item["action"] != "separator":
                        status = "✓" if item["enabled"] else "✗"
                        details.append(f"  {status} {item['icon']} {item['label']}")
            
            # System status
            system_status = data.get("system_status", {})
            cpu = system_status.get("cpu", 0)
            memory = system_status.get("memory", 0)
            details.append(f"\n⚙️ CPU: {cpu:.1f}%")
            details.append(f"🧠 Memory: {memory:.1f}%")
            
            # Show notification
            import subprocess
            try:
                subprocess.run([
                    'notify-send', 
                    '🌊 Marina Status', 
                    '\n'.join(details),
                    '--timeout=8000'
                ], check=False)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error showing daemon details: {e}")
    
    def kill(self):
        """Cleanup when module is killed"""
        if self.marina_core:
            try:
                # Don't actually stop the core as other modules might use it
                pass
            except:
                pass

if __name__ == "__main__":
    # Test the module
    module = Py3status()
    
    try:
        while True:
            result = module.marina_daemons()
            print(f"Status: {result['full_text']}")
            print(f"Color: {result['color']}")
            time.sleep(1)
    except KeyboardInterrupt:
        module.kill()
