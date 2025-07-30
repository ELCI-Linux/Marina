#!/usr/bin/env python3
"""
Demo script for Enhanced Marina Status Bar with Mini-Menus

This script demonstrates the new mini-menu functionality that allows
users to click on daemon icons to reveal contextual control menus.

🎛️ Features Demonstrated:
- Icon-based daemon status display
- Expandable mini-menus on icon clicks
- Daemon-specific action buttons
- Interactive status bar controls
- Real-time daemon state monitoring

Usage:
    python3 demo_enhanced_status_bar.py
"""

import time
import sys
from pathlib import Path

# Add the status_bar directory to the path
status_bar_dir = Path(__file__).parent
sys.path.insert(0, str(status_bar_dir))

try:
    from marina_bar_core import MarinaBarCore
    from modules.marina_daemons import Py3status as DaemonModule
    from modules.marina_mini_menu import Py3status as MiniMenuModule
except ImportError as e:
    print(f"❌ Failed to import Marina status bar modules: {e}")
    sys.exit(1)

def print_separator(title=""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*20} {title} {'='*20}")
    else:
        print("=" * 60)

def demo_core_functionality():
    """Demonstrate core Marina Bar functionality"""
    print_separator("Marina Bar Core Demo")
    
    # Initialize the core
    print("🌊 Initializing Marina Bar Core...")
    core = MarinaBarCore()
    core.start()
    
    # Show initial state
    print(f"📊 Discovered {len(core.daemon_info)} daemons")
    print(f"🎛️ Initialized {len(core.bar_state.mini_menu_items)} mini-menus")
    
    # Display daemon information
    print("\n🔍 Daemon Discovery Results:")
    for name, info in core.daemon_info.items():
        state_emoji = info.state.value[0]
        has_menu = name in core.bar_state.mini_menu_items
        menu_indicator = " 🎛️" if has_menu else ""
        print(f"  {info.emoji} {info.display_name}: {state_emoji} (Priority {info.priority}){menu_indicator}")
    
    return core

def demo_mini_menu_system(core):
    """Demonstrate the mini-menu system"""
    print_separator("Mini-Menu System Demo")
    
    # Show available mini-menus
    print("🎛️ Available Mini-Menus:")
    for daemon_name, menu_items in core.bar_state.mini_menu_items.items():
        daemon_info = core.daemon_info[daemon_name]
        enabled_count = len([item for item in menu_items if item["enabled"] and item["action"] != "separator"])
        total_count = len([item for item in menu_items if item["action"] != "separator"])
        
        print(f"  {daemon_info.emoji} {daemon_info.display_name}: {enabled_count}/{total_count} actions available")
        
        # Show first few menu items
        for i, item in enumerate(menu_items[:3]):
            if item["action"] == "separator":
                continue
            status = "✓" if item["enabled"] else "✗"
            print(f"    {status} {item['icon']} {item['label']}")
        
        if len(menu_items) > 3:
            print(f"    ... and {len(menu_items) - 3} more actions")
    
    # Demonstrate menu toggling
    print("\n🎯 Testing Menu Toggle Functionality:")
    test_daemon = "vision"
    
    print(f"📝 Opening mini-menu for {test_daemon}...")
    core.toggle_mini_menu(test_daemon)
    
    data = core.get_py3status_data()
    active_menu = data["mini_menu_data"]["active_menu"]
    print(f"✅ Active menu: {active_menu}")
    
    print(f"📝 Closing mini-menu for {test_daemon}...")
    core.toggle_mini_menu(test_daemon)
    
    data = core.get_py3status_data()
    active_menu = data["mini_menu_data"]["active_menu"]
    print(f"✅ Active menu: {active_menu}")

def demo_py3status_modules(core):
    """Demonstrate py3status module integration"""
    print_separator("py3status Module Integration Demo")
    
    # Initialize modules
    daemon_module = DaemonModule()
    mini_menu_module = MiniMenuModule()
    
    # Simulate py3status operation
    print("🔄 Simulating py3status operation...")
    
    for i in range(5):
        print(f"📊 Update {i+1}:")
        
        # Get daemon module output
        daemon_result = daemon_module.marina_daemons()
        print(f"  Daemons: {daemon_result['full_text']}")
        print(f"  Color: {daemon_result['color']}")
        
        # Get mini-menu module output
        menu_result = mini_menu_module.marina_mini_menu()
        if menu_result['full_text']:
            print(f"  Mini-Menu: {menu_result['full_text']}")
        else:
            print(f"  Mini-Menu: (hidden)")
        
        # Simulate opening a menu on iteration 3
        if i == 2:
            print("  🎛️ Simulating menu open for 'sonic' daemon...")
            core.toggle_mini_menu("sonic")
        
        # Simulate closing the menu on iteration 4
        if i == 3:
            print("  🎛️ Simulating menu close...")
            core.toggle_mini_menu("sonic")
        
        time.sleep(1)

def demo_action_execution(core):
    """Demonstrate action execution"""
    print_separator("Action Execution Demo")
    
    # Show available actions for a specific daemon
    daemon_name = "thermal"
    daemon_info = core.daemon_info[daemon_name]
    menu_items = core.bar_state.mini_menu_items[daemon_name]
    
    print(f"🌡️ Available actions for {daemon_info.display_name}:")
    for item in menu_items:
        if item["action"] == "separator":
            print("  ─────────────")
        elif item["enabled"]:
            print(f"  ✓ {item['icon']} {item['label']} -> {item['action']}")
        else:
            print(f"  ✗ {item['icon']} {item['label']} -> {item['action']} (disabled)")
    
    # Execute a test action
    print(f"\n🎯 Executing 'show_temp' action for {daemon_name}...")
    success = core.execute_menu_action(daemon_name, "show_temp")
    
    if success:
        print("✅ Action executed successfully!")
    else:
        print("❌ Action execution failed!")

def demo_system_integration():
    """Demonstrate system integration aspects"""
    print_separator("System Integration Demo")
    
    print("🔧 Marina Status Bar Integration Guide:")
    print()
    print("1. 📁 Module Files:")
    print("   - marina_bar_core.py: Core functionality")
    print("   - modules/marina_daemons.py: Main daemon display")
    print("   - modules/marina_mini_menu.py: Mini-menu display")
    print("   - modules/marina_ticker.py: Natural language ticker")
    print()
    print("2. 🎛️ py3status Configuration:")
    print("   order += \"marina_daemons\"")
    print("   order += \"marina_mini_menu\"")
    print("   order += \"marina_ticker\"")
    print()
    print("3. 🎯 User Interactions:")
    print("   - Left-click daemon icon: Toggle mini-menu")
    print("   - Right-click daemon icon: Show context menu")
    print("   - Middle-click bar: Refresh daemon states")
    print("   - Left-click mini-menu: Execute first action")
    print("   - Right-click mini-menu: Close menu")
    print()
    print("4. 🔄 Auto-Features:")
    print("   - Dynamic expansion based on daemon activity")
    print("   - Auto-collapse after timeout")
    print("   - Real-time daemon state monitoring")
    print("   - Natural language status messages")

def main():
    """Main demo function"""
    print("🌊 Marina Enhanced Status Bar Demo")
    print("===================================")
    print()
    print("This demo showcases the new mini-menu functionality")
    print("that provides contextual controls for each Marina daemon.")
    print()
    
    try:
        # Initialize and demonstrate core functionality
        core = demo_core_functionality()
        
        # Demonstrate mini-menu system
        demo_mini_menu_system(core)
        
        # Demonstrate py3status module integration
        demo_py3status_modules(core)
        
        # Demonstrate action execution
        demo_action_execution(core)
        
        # Show system integration info
        demo_system_integration()
        
        print_separator("Demo Complete")
        print("✅ All demonstrations completed successfully!")
        print()
        print("🎛️ The enhanced Marina status bar now supports:")
        print("   • Expandable mini-menus for each daemon icon")
        print("   • Contextual action buttons based on daemon state")
        print("   • Interactive click-to-execute functionality")
        print("   • Visual feedback and notifications")
        print("   • Auto-collapse and timeout management")
        print()
        print("🚀 Ready for integration with your i3/py3status setup!")
        
        # Cleanup
        core.stop()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
        if 'core' in locals():
            core.stop()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        if 'core' in locals():
            core.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
