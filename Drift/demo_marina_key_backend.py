#!/usr/bin/env python3
"""
Marina Key Backend Demo
Comprehensive demonstration of Marina password recovery system

Author: Marina AI Assistant
"""

import os
import sys
import time
import subprocess
from typing import Dict, Any

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from marina_key_backend import MarinaKeyBackend
from drift_core import DriftCore


def demo_header(title: str):
    """Print a formatted demo section header."""
    print(f"\n{'='*60}")
    print(f"🌊 {title}")
    print(f"{'='*60}")


def demo_basic_operations():
    """Demo basic Marina Key Backend operations."""
    demo_header("Marina Key Backend - Basic Operations")
    
    # Initialize backend
    print("🚀 Initializing Marina Key Backend...")
    backend = MarinaKeyBackend()
    
    # Show status
    print("\n📊 Backend Status:")
    status = backend.get_status()
    for key, value in status.items():
        if key == 'capabilities':
            print(f"   {key}: {', '.join(value)}")
        else:
            print(f"   {key}: {value}")
    
    # Generate recovery key
    print("\n🔑 Generating recovery key for user 'adminx'...")
    try:
        key_id, recovery_key = backend.generate_recovery_key('adminx')
        print(f"   ✅ Key generated successfully!")
        print(f"   Key ID: {key_id}")
        print(f"   Recovery Key: {recovery_key}")
        print(f"   Expires: 24 hours from now")
        
        # Validate the key
        print(f"\n✅ Validating recovery key...")
        if backend.validate_recovery_key(key_id, recovery_key, 'adminx'):
            print(f"   ✅ Key validation successful!")
        else:
            print(f"   ❌ Key validation failed!")
        
        # Show active keys
        print(f"\n📋 Active keys: {len(backend.active_keys)}")
        for kid, key in backend.active_keys.items():
            print(f"   {kid}: {key.user_id} (expires: {key.expires_at})")
        
        return key_id, recovery_key
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, None


def demo_network_features():
    """Demo network discovery and multi-instance features."""
    demo_header("Marina Network Discovery & Multi-Instance Support")
    
    backend = MarinaKeyBackend()
    
    # Network discovery
    print("🌐 Scanning network for Marina instances...")
    nodes = backend.discover_marina_nodes()
    
    if nodes:
        print(f"   ✅ Found {len(nodes)} Marina instances:")
        for node in nodes:
            print(f"     • {node.hostname} ({node.ip_address}:{node.port})")
            print(f"       Version: {node.marina_version}")
            print(f"       Capabilities: {', '.join(node.capabilities)}")
    else:
        print("   📡 No other Marina instances found on network")
        print("   💡 To test multi-instance features:")
        print("      1. Run 'marina-key daemon' on another Marina instance")
        print("      2. Use 'marina-key network-request <username>' to request keys")


def demo_email_integration():
    """Demo email integration for key delivery."""
    demo_header("Email Integration for Key Delivery")
    
    backend = MarinaKeyBackend()
    
    print("📧 Email Configuration:")
    email_config = backend.config['email']
    print(f"   SMTP Server: {email_config['smtp_server']}:{email_config['smtp_port']}")
    print(f"   Username: {email_config['username']}")
    print(f"   Recipient: {email_config['recipient_email']}")
    print(f"   Sender Name: {email_config['sender_name']}")
    
    if not email_config['username'] or not email_config['password']:
        print("   ⚠️  Email credentials not configured")
        print("   📝 To configure email:")
        print("      ./marina_key_manager config-email \\")
        print("        --smtp-server smtp.gmail.com \\")
        print("        --smtp-port 587 \\")
        print("        --username your-email@gmail.com \\")
        print("        --password your-app-password \\")
        print("        --recipient-email your-email@gmail.com")
    else:
        print("   ✅ Email credentials configured")
        
        # Test email sending (without actually sending)
        print("\n📤 Email template preview:")
        key_id = "MRK_DEMO_123456789"
        recovery_key = "DEMO_KEY_12345_ABCDEF"
        
        html_content = backend.create_recovery_email_html('adminx', recovery_key, key_id)
        text_content = backend.create_recovery_email_text('adminx', recovery_key, key_id)
        
        print("   📄 Text version (first 300 chars):")
        print(f"   {text_content[:300]}...")


def demo_security_features():
    """Demo security features and key management."""
    demo_header("Security Features & Key Management")
    
    backend = MarinaKeyBackend()
    
    print("🔒 Security Configuration:")
    security = backend.config['security']
    print(f"   Key length: {security['key_length']} bytes")
    print(f"   Key lifetime: {security['key_lifetime_hours']} hours")
    print(f"   Max usage per key: {security['max_usage_per_key']}")
    print(f"   Network auth required: {security['require_network_auth']}")
    print(f"   Allowed networks: {', '.join(security['allowed_networks'])}")
    
    print("\n🛡️ Key Features:")
    print("   • Cryptographically secure key generation")
    print("   • Automatic expiration (24 hours default)")
    print("   • Single-use keys (configurable)")
    print("   • Network access control")
    print("   • Audit logging")
    print("   • Multi-instance synchronization")
    
    # Generate a test key to show security features
    print("\n🧪 Security Demo:")
    print("   Generating test key...")
    key_id, recovery_key = backend.generate_recovery_key('demo_user')
    print(f"   Key ID: {key_id}")
    print(f"   Key: {recovery_key}")
    print(f"   Key entropy: {len(recovery_key) * 6} bits (base64)")
    
    # Show key hash storage
    test_key = backend.active_keys[key_id]
    print(f"   Stored as SHA256 hash: {test_key.key_hash[:16]}...")
    print(f"   Usage count: {test_key.usage_count}/{test_key.max_usage}")


def demo_drift_integration():
    """Demo integration with Drift login manager."""
    demo_header("Drift Login Manager Integration")
    
    print("🔗 Marina Key Backend is fully integrated with Drift:")
    
    # Initialize Drift with key backend
    print("   Initializing Drift Core...")
    drift = DriftCore()
    
    # Show Marina key status in Drift
    key_status = drift.get_marina_key_status()
    print(f"\n📊 Marina Key Status in Drift:")
    for key, value in key_status.items():
        print(f"   {key}: {value}")
    
    # Demo recovery key request
    print(f"\n🔑 Password Recovery Demo:")
    print("   Requesting recovery key for 'adminx'...")
    success, message = drift.request_recovery_key('adminx')
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
    
    print(f"\n🌐 Network Recovery Demo:")
    print("   Attempting network recovery for 'adminx'...")
    success, message = drift.request_network_recovery_key('adminx')
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   📡 {message}")
    
    print(f"\n💡 Integration Features:")
    print("   • Seamless password recovery from login screen")
    print("   • Network-wide key generation and validation")
    print("   • Automatic email delivery")
    print("   • Multi-modal authentication with fallback")
    print("   • Marina daemon awareness")


def demo_cli_tools():
    """Demo CLI tools and management features."""
    demo_header("CLI Tools & Management")
    
    print("🛠️ Marina Key Manager CLI:")
    print("   Available commands:")
    commands = [
        ("generate <user>", "Generate recovery key for user"),
        ("validate <key_id> <key>", "Validate a recovery key"),
        ("list", "List all active keys"),
        ("discover", "Discover Marina nodes on network"),
        ("network-request <user>", "Request key from network"),
        ("daemon", "Start key backend daemon"),
        ("status", "Show backend status"),
        ("reset-password", "Reset password with key"),
        ("config-email", "Configure email settings")
    ]
    
    for cmd, desc in commands:
        print(f"     ./marina_key_manager {cmd:<20} # {desc}")
    
    print(f"\n📋 Current Status:")
    # Run status command
    result = subprocess.run([
        'python3', 'marina_key_manager', 'status'
    ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
    
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        # Show just the status part
        status_started = False
        for line in lines:
            if '📊 Marina Key Backend Status:' in line:
                status_started = True
            if status_started:
                print(f"   {line}")


def demo_use_cases():
    """Demo real-world use cases."""
    demo_header("Real-World Use Cases")
    
    print("🎯 Marina Key Backend Use Cases:")
    
    use_cases = [
        {
            "title": "🏠 Home Network Password Recovery",
            "description": "User forgets password on their Marina workstation",
            "steps": [
                "User clicks 'Forgot Password' on Drift login screen",
                "Drift requests recovery key from any Marina instance on network",
                "Key is generated and emailed automatically",
                "User enters key and resets password"
            ]
        },
        {
            "title": "🏢 Enterprise Multi-Instance Setup",
            "description": "Corporate network with multiple Marina instances",
            "steps": [
                "Admin deploys Marina Key Backend on all instances",
                "Network discovery automatically finds all nodes",
                "Any instance can generate keys for any user",
                "Centralized audit logging and key management"
            ]
        },
        {
            "title": "🔒 Secure Remote Access",
            "description": "User needs access from untrusted device",
            "steps": [
                "User requests Marina token via email",
                "Key backend generates temporary access token",
                "Token provides limited-time Marina access",
                "User can then reset password or access files"
            ]
        },
        {
            "title": "🚨 Emergency Account Recovery",
            "description": "System admin locked out of all accounts",
            "steps": [
                "Admin uses marina_key_manager from another Marina instance",
                "Generates emergency recovery key",
                "Key is delivered via configured email",
                "Admin can recover access to locked system"
            ]
        }
    ]
    
    for i, case in enumerate(use_cases, 1):
        print(f"\n{case['title']}")
        print(f"   {case['description']}")
        print(f"   Steps:")
        for j, step in enumerate(case['steps'], 1):
            print(f"     {j}. {step}")


def main():
    """Run the comprehensive Marina Key Backend demo."""
    print("🌊 Marina Key Backend - Comprehensive Demo")
    print("=" * 60)
    print("This demo showcases the complete Marina password recovery system")
    print("integrating secure key generation, network distribution, and email delivery.")
    
    try:
        # Run all demo sections
        key_id, recovery_key = demo_basic_operations()
        demo_network_features()
        demo_email_integration()
        demo_security_features()
        demo_drift_integration()
        demo_cli_tools()
        demo_use_cases()
        
        # Final summary
        demo_header("Demo Complete - Summary")
        print("✅ Marina Key Backend Features Demonstrated:")
        print("   🔑 Secure recovery key generation and validation")
        print("   🌐 Network discovery and multi-instance support")
        print("   📧 Automated email delivery with HTML templates")
        print("   🔒 Enterprise-grade security and key management")
        print("   🔗 Seamless Drift login manager integration")
        print("   🛠️ Comprehensive CLI tools for administration")
        print("   🎯 Real-world use case implementations")
        
        print(f"\n🚀 Next Steps:")
        print("   1. Configure email credentials for full functionality")
        print("   2. Deploy on multiple Marina instances for network features")
        print("   3. Integrate with your login screen using Drift")
        print("   4. Set up monitoring and alerting for key usage")
        
        if key_id and recovery_key:
            print(f"\n🔑 Generated demo key:")
            print(f"   Key ID: {key_id}")
            print(f"   Recovery Key: {recovery_key}")
            print(f"   Use: ./marina_key_manager validate {key_id} {recovery_key}")
    
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
