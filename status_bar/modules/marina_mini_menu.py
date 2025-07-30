#!/usr/bin/env python3
"""
Marina Mini-Menu Module for py3status

Displays expandable mini-menus for Marina daemon icons when clicked.
This module works in conjunction with the marina_daemons module to provide
contextual controls for each daemon.

🎛️ Features:
- Expandable mini-menus that appear below daemon icons
- Daemon-specific action buttons and controls
- Contextual menu items based on daemon state and capabilities
- Click-to-execute actions with visual feedback
- Auto-collapse after timeout or when clicking elsewhere

Usage in i3 config:
    order += "marina_mini_menu"
"""

import sys
from pathlib import Path
import os
import logging
import time
from datetime import datetime, timedelta

# Set up logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - Marina Mini Menu - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/marina_mini_menu.log'),
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


class Py3status:
    """
    Marina Mini-Menu Module
    
    Displays contextual mini-menus for Marina daemon icons with:
    - Daemon-specific action buttons
    - State-aware menu items (enabled/disabled based on daemon state)
    - Click-to-execute functionality
    - Visual feedback and notifications
    """

    # Configuration options
    cache_timeout = 0.5  # Faster updates for interactive elements
    
    # Color scheme
    color_menu_bg = "#2C3E50"        # Dark blue background
    color_menu_item = "#ECF0F1"      # Light gray text
    color_menu_disabled = "#7F8C8D"  # Gray for disabled items
    color_menu_separator = "#34495E" # Darker separator
    color_menu_active = "#3498DB"    # Blue for active/hovered items
    
    # Menu settings
    max_menu_width = 25
    menu_timeout = 10  # Seconds before auto-close
    
    def __init__(self):
        self.marina_core = None
        self.last_menu_check = None
        self.menu_display_start = None
        
    def marina_mini_menu(self):
        """Main mini-menu display method"""
        try:
            # Initialize Marina core if needed
            if not self.marina_core:
                self.marina_core = get_marina_bar_core()
            
            # Get current menu data
            data = self.marina_core.get_py3status_data()
            mini_menu_data = data.get("mini_menu_data", {})
            
            active_menu = mini_menu_data.get("active_menu")
            menu_items = mini_menu_data.get("menu_items", [])
            
            # If no active menu, return empty/hidden
            if not active_menu or not menu_items:
                return {
                    'full_text': '',
                    'color': self.color_menu_bg,
                    'cached_until': time.time() + self.cache_timeout
                }
            
            # Record when menu display started (for timeout)
            if not self.menu_display_start:
                self.menu_display_start = datetime.now()
            
            # Check for menu timeout
            if (datetime.now() - self.menu_display_start).total_seconds() > self.menu_timeout:
                self.marina_core.toggle_mini_menu(active_menu)  # Close menu
                self.menu_display_start = None
                return {
                    'full_text': '',
                    'color': self.color_menu_bg,
                    'cached_until': time.time() + self.cache_timeout
                }
            
            # Render the mini-menu
            return self._render_mini_menu(active_menu, menu_items)
            
        except Exception as e:
            logger.error(f"Error in marina_mini_menu: {e}")
            return {
                'full_text': f"🎛️ Menu Error: {str(e)[:20]}",
                'color': "#E74C3C",  # Red for errors
                'cached_until': time.time() + self.cache_timeout
            }
    
    def _render_mini_menu(self, daemon_name, menu_items):
        """Render the mini-menu display"""
        try:
            # Get daemon info for header
            daemon_info = self.marina_core.daemon_info.get(daemon_name)
            if not daemon_info:
                return {
                    'full_text': f"🎛️ {daemon_name}: Menu",
                    'color': self.color_menu_item,
                    'cached_until': time.time() + self.cache_timeout
                }
            
            # Build menu display
            menu_parts = []
            
            # Header with daemon info
            header = f"{daemon_info.emoji} {daemon_info.display_name[:10]}"
            menu_parts.append(header)
            
            # Count enabled items
            enabled_items = [item for item in menu_items if item["enabled"] and item["action"] != "separator"]
            total_items = len([item for item in menu_items if item["action"] != "separator"])
            
            # Show item count
            menu_parts.append(f"[{len(enabled_items)}/{total_items}]")
            
            # Show first few menu items (compact representation)
            displayed_items = []
            item_count = 0
            
            for item in menu_items:
                if item_count >= 3:  # Limit to 3 items in compact view
                    break
                    
                if item["action"] == "separator":
                    continue
                
                if item["enabled"]:
                    displayed_items.append(item["icon"])
                else:
                    displayed_items.append("⚫")  # Disabled item indicator
                
                item_count += 1
            
            if displayed_items:
                menu_parts.append(" ".join(displayed_items))
            
            # Add more indicator if there are additional items
            if len(menu_items) > 4:  # 3 displayed + separator
                menu_parts.append("⋯")
            
            # Join parts
            full_text = " │ ".join(menu_parts)
            
            # Limit width
            if len(full_text) > self.max_menu_width:
                full_text = full_text[:self.max_menu_width-1] + "…"
            
            return {
                'full_text': full_text,
                'color': self.color_menu_item,
                'background': self.color_menu_bg,
                'cached_until': time.time() + self.cache_timeout,
                'separator': False,
                'separator_block_width': 15
            }
            
        except Exception as e:
            logger.error(f"Error rendering mini-menu: {e}")
            return {
                'full_text': f"🎛️ Render Error",
                'color': "#E74C3C",
                'cached_until': time.time() + self.cache_timeout
            }
    
    def on_click(self, event):
        """Handle clicks on menu items"""
        try:
            if not self.marina_core:
                return
                
            # Get current menu data
            data = self.marina_core.get_py3status_data()
            mini_menu_data = data.get("mini_menu_data", {})
            
            active_menu = mini_menu_data.get("active_menu")
            menu_items = mini_menu_data.get("menu_items", [])
            
            if not active_menu or not menu_items:
                return
            
            button = event.get('button', 1)
            
            if button == 1:  # Left click
                # Execute first enabled menu item (simplified approach)
                self._execute_first_enabled_action(active_menu, menu_items)
                
            elif button == 2:  # Middle click
                # Show full menu in notification
                self._show_full_menu_notification(active_menu, menu_items)
                
            elif button == 3:  # Right click
                # Close menu
                self.marina_core.toggle_mini_menu(active_menu)
                self.menu_display_start = None
                
        except Exception as e:
            logger.error(f"Error in menu click handler: {e}")
    
    def _execute_first_enabled_action(self, daemon_name, menu_items):
        """Execute the first enabled action in the menu"""
        try:
            for item in menu_items:
                if item["enabled"] and item["action"] != "separator":
                    action = item["action"]
                    logger.debug(f"Executing action {action} for {daemon_name}")
                    
                    # Execute the action
                    success = self.marina_core.execute_menu_action(daemon_name, action)
                    
                    # Show feedback
                    import subprocess
                    if success:
                        subprocess.run([
                            'notify-send',
                            f'{item["icon"]} {item["label"]}',
                            f'Action executed for {daemon_name}',
                            '--timeout=3000'
                        ], check=False)
                    else:
                        subprocess.run([
                            'notify-send',
                            f'❌ {item["label"]}',
                            f'Action failed for {daemon_name}',
                            '--timeout=3000'
                        ], check=False)
                    
                    # Close menu after action
                    self.marina_core.toggle_mini_menu(daemon_name)
                    self.menu_display_start = None
                    break
                    
        except Exception as e:
            logger.error(f"Error executing menu action: {e}")
    
    def _show_full_menu_notification(self, daemon_name, menu_items):
        """Show full menu in a notification for selection"""
        try:
            daemon_info = self.marina_core.daemon_info.get(daemon_name)
            if not daemon_info:
                return
            
            # Build full menu text
            menu_text = [f"🎛️ {daemon_info.display_name} Menu", "", "Available Actions:"]
            
            for item in menu_items:
                if item["action"] == "separator":
                    menu_text.append("─────────────")
                elif item["enabled"]:
                    menu_text.append(f"✓ {item['icon']} {item['label']}")
                else:
                    menu_text.append(f"✗ {item['icon']} {item['label']} (disabled)")
            
            menu_text.append("")
            menu_text.append("💡 Left-click menu to execute first action")
            menu_text.append("🔄 Right-click menu to close")
            
            # Show notification
            import subprocess
            subprocess.run([
                'notify-send',
                f'{daemon_info.emoji} {daemon_info.display_name}',
                '\n'.join(menu_text),
                '--timeout=10000'
            ], check=False)
            
        except Exception as e:
            logger.error(f"Error showing full menu notification: {e}")
    
    def kill(self):
        """Cleanup when module is killed"""
        if self.marina_core:
            try:
                # Close any active menus
                data = self.marina_core.get_py3status_data()
                mini_menu_data = data.get("mini_menu_data", {})
                active_menu = mini_menu_data.get("active_menu")
                
                if active_menu:
                    self.marina_core.toggle_mini_menu(active_menu)
            except:
                pass


if __name__ == "__main__":
    # Test the module
    module = Py3status()
    
    try:
        while True:
            result = module.marina_mini_menu()
            if result['full_text']:
                print(f"Mini Menu: {result['full_text']}")
                print(f"Color: {result['color']}")
            else:
                print("No active menu")
            time.sleep(1)
    except KeyboardInterrupt:
        module.kill()
