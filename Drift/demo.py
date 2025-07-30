#!/usr/bin/env python3
"""
Drift Demo - Showcase Marina-integrated Login Manager
Interactive demonstration of Drift's features

Author: Marina AI Assistant
"""

import os
import sys
import time
from drift_core import DriftCore, AuthMethod, SessionType


def print_banner():
    """Print the Drift banner."""
    print("🌊" * 20)
    print("         DRIFT DEMO")
    print("   Marina-integrated Login Manager")
    print("🌊" * 20)
    print()


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}\n")


def demo_core_functionality():
    """Demonstrate core Drift functionality."""
    print_section("Core System Initialization")
    
    # Initialize with local test config
    test_config = './test_drift.conf'
    drift = DriftCore(config_path=test_config)
    
    print("✅ Drift Core initialized")
    print(f"   Marina Integration: {'Available' if hasattr(drift, 'marina_identity') else 'Fallback mode'}")
    print(f"   Voice Auth: {'Available' if drift.whisper_model else 'Not available'}")
    print(f"   Database: {drift.db_path}")
    
    return drift


def demo_user_management(drift):
    """Demonstrate user management features."""
    print_section("User Management")
    
    users = drift.get_system_users()
    print(f"Found {len(users)} system users:")
    
    for user in users:
        print(f"  👤 {user.username} ({user.full_name})")
        print(f"     UID: {user.uid}, Home: {user.home_dir}")
        print(f"     Shell: {user.shell}")
        if user.marina_persona:
            print(f"     🤖 Marina Persona: {user.marina_persona}")
        if user.voice_print:
            print(f"     🎤 Voice Auth: Enabled")
        print()


def demo_system_status(drift):
    """Demonstrate system status monitoring."""
    print_section("System Status Monitoring")
    
    status = drift.get_system_status()
    if status:
        uptime_hours = status.get('uptime_hours', 0)
        uptime_str = f"{int(uptime_hours)}h {int((uptime_hours % 1) * 60)}m"
        
        print(f"🖥️  System Uptime: {uptime_str}")
        print(f"⚡ Load Average: {', '.join(status.get('load_average', ['N/A']))}")
        print(f"💾 Memory Usage: {status.get('memory_usage_percent', 0):.1f}%")
        
        daemons = status.get('marina_daemons_active', [])
        print(f"🌊 Marina Daemons: {len(daemons)} active")
        if daemons:
            for i, daemon in enumerate(daemons[:3]):
                print(f"   Process {daemon}")
            if len(daemons) > 3:
                print(f"   ... and {len(daemons) - 3} more")
    else:
        print("❌ Could not retrieve system status")


def demo_authentication(drift):
    """Demonstrate authentication methods."""
    print_section("Authentication Methods")
    
    # Test guest authentication
    print("🔓 Testing Guest Authentication:")
    success, error = drift.authenticate_user("guest", "", AuthMethod.GUEST)
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    if error:
        print(f"   Error: {error}")
    
    print()
    
    # Test Marina token authentication
    print("🔐 Testing Marina Token Authentication:")
    test_token = "marina_test_token_abcdef123456789012345678"
    success, error = drift.authenticate_user("adminx", test_token, AuthMethod.TOKEN)
    print(f"   Token: {test_token[:20]}...")
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    if error:
        print(f"   Error: {error}")
    
    print()
    
    # Test voice authentication (if available)
    print("🎤 Voice Authentication Status:")
    if drift.whisper_model:
        print("   ✅ faster-whisper model loaded")
        print("   🔊 Ready for voice commands")
    else:
        print("   ⚠️  faster-whisper not available")
        print("   💡 Install with: pip install faster-whisper")


def demo_marina_integration(drift):
    """Demonstrate Marina-specific features."""
    print_section("Marina Integration Features")
    
    print("🤖 Marina Ecosystem Integration:")
    print(f"   Marina Path: {drift.marina_path}")
    print(f"   Integration: {'✅ Enabled' if drift.config.get('marina_integration_enabled') else '❌ Disabled'}")
    print(f"   Auto-start Daemons: {'✅ Yes' if drift.config.get('auto_start_marina_daemons') else '❌ No'}")
    
    # Check if Marina wake script exists
    wake_script = os.path.join(drift.marina_path, 'wake.py')
    print(f"   Wake Script: {'✅ Found' if os.path.exists(wake_script) else '❌ Not found'}")
    
    print()
    print("🎨 Marina Theming:")
    themes = drift.config.get('themes', {})
    for theme_name, theme_config in themes.items():
        print(f"   {theme_name}:")
        print(f"     Background: {theme_config.get('background', 'N/A')}")
        print(f"     Accent: {theme_config.get('accent', 'N/A')}")


def demo_session_types(drift):
    """Demonstrate session type support."""
    print_section("Session Type Support")
    
    print("🖥️  Supported Session Types:")
    for session_type in SessionType:
        print(f"   {session_type.value.title()}: ", end="")
        
        if session_type == SessionType.WAYLAND:
            print("✅ Modern display protocol with Marina integration")
        elif session_type == SessionType.X11:
            print("✅ Traditional X Window System with Marina overlay")
        elif session_type == SessionType.MARINA_SHELL:
            marina_gui = os.path.join(drift.marina_path, 'gui', 'main_gui.py')
            if os.path.exists(marina_gui):
                print("✅ Custom Marina desktop environment")
            else:
                print("⚠️  Marina GUI not found")
        else:
            print("🔧 User-defined session configuration")


def demo_security_features(drift):
    """Demonstrate security features."""
    print_section("Security Features")
    
    config = drift.config
    
    print("🔒 Security Configuration:")
    print(f"   Max Failed Attempts: {config.get('max_failed_attempts', 3)}")
    print(f"   Lockout Duration: {config.get('lockout_duration', 300)} seconds")
    print(f"   Session Timeout: {config.get('session_timeout', 3600)} seconds")
    print(f"   Guest Login: {'✅ Enabled' if config.get('guest_enabled', True) else '❌ Disabled'}")
    
    print()
    print("🗃️  Database Security:")
    print(f"   Database Path: {drift.db_path}")
    print("   ✅ SQLite with encrypted sensitive data")
    print("   ✅ Comprehensive audit trail")
    print("   ✅ User profile isolation")


def interactive_demo():
    """Run an interactive demonstration."""
    print_banner()
    
    # Initialize system
    drift = demo_core_functionality()
    
    # Wait for user
    input("\nPress Enter to continue to User Management...")
    demo_user_management(drift)
    
    input("\nPress Enter to continue to System Status...")
    demo_system_status(drift)
    
    input("\nPress Enter to continue to Authentication...")
    demo_authentication(drift)
    
    input("\nPress Enter to continue to Marina Integration...")
    demo_marina_integration(drift)
    
    input("\nPress Enter to continue to Session Types...")
    demo_session_types(drift)
    
    input("\nPress Enter to continue to Security Features...")
    demo_security_features(drift)
    
    print_section("Demo Complete!")
    print("🌊 Drift - Where Marina drifts in as your system awakens")
    print()
    print("Next steps:")
    print("  1. Install Drift: sudo ./install.sh")
    print("  2. Configure users: ./driftctl set-persona <user> <persona>")
    print("  3. Test authentication: ./driftctl test-auth <user> <method>")
    print("  4. Launch GUI: ./driftctl gui")
    print()
    print("For more information, see README.md")


if __name__ == "__main__":
    try:
        interactive_demo()
    except KeyboardInterrupt:
        print("\n\n🌊 Demo interrupted. Thanks for checking out Drift!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("Please check that all dependencies are installed.")
