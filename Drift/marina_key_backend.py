#!/usr/bin/env python3
"""
Marina Key Backend Engine
Secure key generation and email delivery system for Marina password recovery

This backend allows any networked Marina instance to generate recovery keys
and email them for password reset functionality.

Author: Marina AI Assistant
"""

import os
import sys
import json
import time
import hmac
import base64
import hashlib
import secrets
import socket
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

# Add Marina path for imports
sys.path.append('/home/adminx/Marina')

# Try to import Marina components
try:
    from drift_core import DriftCore
    DRIFT_AVAILABLE = True
except ImportError:
    DRIFT_AVAILABLE = False

# Cryptographic imports
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Network discovery
try:
    import netifaces
    import requests
    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False


@dataclass
class MarinaKey:
    """Marina recovery key data structure."""
    key_id: str
    user_id: str
    key_hash: str
    created_at: datetime
    expires_at: datetime
    usage_count: int
    max_usage: int
    marina_instance: str
    network_address: str
    is_active: bool = True


@dataclass
class EmailConfig:
    """Email configuration for key delivery."""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    sender_name: str = "Marina AI Assistant"


@dataclass
class NetworkNode:
    """Networked Marina instance information."""
    instance_id: str
    hostname: str
    ip_address: str
    port: int
    last_seen: datetime
    marina_version: str
    capabilities: List[str]


class MarinaKeyBackend:
    """Backend engine for Marina key generation and management."""
    
    def __init__(self, config_path: str = None):
        """Initialize the Marina key backend."""
        self.config_path = config_path or "/etc/marina/key_backend.conf"
        self.database_path = "/var/lib/marina/keys.db"
        self.network_port = 8887  # Marina Key Service port
        self.discovery_port = 8888  # Network discovery port
        
        # Use local paths if not running as root
        if os.geteuid() != 0:
            base_dir = os.path.dirname(__file__)
            self.config_path = os.path.join(base_dir, "marina_key_config.json")
            self.database_path = os.path.join(base_dir, "marina_keys.db")
        
        self.config = self.load_config()
        self.active_keys: Dict[str, MarinaKey] = {}
        self.network_nodes: Dict[str, NetworkNode] = {}
        self.running = False
        
        # Initialize database
        self.init_database()
        
        # Load existing keys
        self.load_keys()
        
        print(f"🔑 Marina Key Backend initialized")
        print(f"   Config: {self.config_path}")
        print(f"   Database: {self.database_path}")
        print(f"   Network port: {self.network_port}")
    
    def load_config(self) -> Dict[str, Any]:
        """Load backend configuration."""
        default_config = {
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "use_tls": True,
                "sender_name": "Marina AI Assistant",
                "recipient_email": "user@example.com"
            },
            "security": {
                "key_length": 32,
                "key_lifetime_hours": 24,
                "max_usage_per_key": 1,
                "require_network_auth": True,
                "allowed_networks": ["192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12"]
            },
            "network": {
                "discovery_enabled": True,
                "discovery_interval": 300,
                "auto_trust_local": True,
                "require_marina_signature": True
            },
            "marina": {
                "instance_id": "",
                "hostname": socket.gethostname(),
                "version": "1.0.0"
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
                return config
            except Exception as e:
                print(f"⚠️  Error loading config: {e}")
        
        # Create default config
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def init_database(self):
        """Initialize the key database."""
        # For simplicity, using JSON file. In production, use SQLite or PostgreSQL
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        if not os.path.exists(self.database_path):
            with open(self.database_path, 'w') as f:
                json.dump({"keys": {}, "nodes": {}, "metadata": {"created": datetime.now().isoformat()}}, f)
    
    def load_keys(self):
        """Load existing keys from database."""
        try:
            if os.path.exists(self.database_path):
                with open(self.database_path, 'r') as f:
                    data = json.load(f)
                    
                for key_id, key_data in data.get("keys", {}).items():
                    # Convert datetime strings back to datetime objects
                    key_data["created_at"] = datetime.fromisoformat(key_data["created_at"])
                    key_data["expires_at"] = datetime.fromisoformat(key_data["expires_at"])
                    self.active_keys[key_id] = MarinaKey(**key_data)
                
                for node_id, node_data in data.get("nodes", {}).items():
                    node_data["last_seen"] = datetime.fromisoformat(node_data["last_seen"])
                    self.network_nodes[node_id] = NetworkNode(**node_data)
                
                # Clean up expired keys
                self.cleanup_expired_keys()
                print(f"📂 Loaded {len(self.active_keys)} active keys and {len(self.network_nodes)} network nodes")
        except Exception as e:
            print(f"⚠️  Error loading keys: {e}")
    
    def save_keys(self):
        """Save keys to database."""
        try:
            data = {
                "keys": {},
                "nodes": {},
                "metadata": {
                    "updated": datetime.now().isoformat(),
                    "total_keys_generated": len(self.active_keys)
                }
            }
            
            for key_id, key in self.active_keys.items():
                key_dict = asdict(key)
                key_dict["created_at"] = key.created_at.isoformat()
                key_dict["expires_at"] = key.expires_at.isoformat()
                data["keys"][key_id] = key_dict
            
            for node_id, node in self.network_nodes.items():
                node_dict = asdict(node)
                node_dict["last_seen"] = node.last_seen.isoformat()
                data["nodes"][node_id] = node_dict
            
            with open(self.database_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving keys: {e}")
    
    def generate_recovery_key(self, user_id: str, requester_ip: str = None) -> Tuple[str, str]:
        """Generate a new Marina recovery key."""
        if not self.is_authorized_request(requester_ip):
            raise PermissionError("Unauthorized network request")
        
        # Generate secure key
        key_bytes = secrets.token_bytes(self.config["security"]["key_length"])
        recovery_key = base64.urlsafe_b64encode(key_bytes).decode('utf-8')
        
        # Create key hash for storage
        key_hash = hashlib.sha256(recovery_key.encode()).hexdigest()
        
        # Generate unique key ID
        key_id = f"MRK_{int(time.time())}_{secrets.token_hex(8)}"
        
        # Set expiration
        lifetime_hours = self.config["security"]["key_lifetime_hours"]
        expires_at = datetime.now() + timedelta(hours=lifetime_hours)
        
        # Create Marina key object
        marina_key = MarinaKey(
            key_id=key_id,
            user_id=user_id,
            key_hash=key_hash,
            created_at=datetime.now(),
            expires_at=expires_at,
            usage_count=0,
            max_usage=self.config["security"]["max_usage_per_key"],
            marina_instance=self.config["marina"]["instance_id"] or socket.gethostname(),
            network_address=requester_ip or "local",
            is_active=True
        )
        
        # Store key
        self.active_keys[key_id] = marina_key
        self.save_keys()
        
        print(f"🔑 Generated recovery key {key_id} for user {user_id}")
        return key_id, recovery_key
    
    def validate_recovery_key(self, key_id: str, recovery_key: str, user_id: str = None) -> bool:
        """Validate a Marina recovery key."""
        if key_id not in self.active_keys:
            return False
        
        marina_key = self.active_keys[key_id]
        
        # Check if key is active and not expired
        if not marina_key.is_active or datetime.now() > marina_key.expires_at:
            return False
        
        # Check usage limit
        if marina_key.usage_count >= marina_key.max_usage:
            return False
        
        # Verify key hash
        key_hash = hashlib.sha256(recovery_key.encode()).hexdigest()
        if key_hash != marina_key.key_hash:
            return False
        
        # Check user ID if provided
        if user_id and marina_key.user_id != user_id:
            return False
        
        # Increment usage count
        marina_key.usage_count += 1
        
        # Deactivate if max usage reached
        if marina_key.usage_count >= marina_key.max_usage:
            marina_key.is_active = False
        
        self.save_keys()
        print(f"✅ Validated recovery key {key_id} for user {user_id or marina_key.user_id}")
        return True
    
    def send_recovery_email(self, user_id: str, recovery_key: str, key_id: str) -> bool:
        """Send recovery key via email."""
        try:
            email_config = self.config["email"]
            
            if not email_config["username"] or not email_config["password"]:
                print("⚠️  Email credentials not configured")
                return False
            
            # Create email message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Marina Password Recovery Key"
            msg["From"] = f"{email_config['sender_name']} <{email_config['username']}>"
            msg["To"] = email_config["recipient_email"]
            
            # Create email content
            html_content = self.create_recovery_email_html(user_id, recovery_key, key_id)
            text_content = self.create_recovery_email_text(user_id, recovery_key, key_id)
            
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
                if email_config["use_tls"]:
                    server.starttls(context=context)
                server.login(email_config["username"], email_config["password"])
                server.send_message(msg)
            
            print(f"📧 Recovery email sent for user {user_id}")
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to send recovery email: {e}")
            return False
    
    def create_recovery_email_html(self, user_id: str, recovery_key: str, key_id: str) -> str:
        """Create HTML email content for recovery key."""
        marina_instance = self.config["marina"]["hostname"]
        expires_hours = self.config["security"]["key_lifetime_hours"]
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #1a1a1a; color: #ffffff; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #0d1421; padding: 30px; border-radius: 10px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .logo {{ color: #00d4aa; font-size: 24px; font-weight: bold; }}
                .key-box {{ background-color: #333333; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #00d4aa; }}
                .key {{ font-family: monospace; font-size: 16px; word-break: break-all; color: #00d4aa; }}
                .warning {{ background-color: #ffaa00; color: #000000; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #cccccc; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🌊 Marina Password Recovery</div>
                </div>
                
                <p>Hello,</p>
                
                <p>A password recovery key has been generated for user <strong>{user_id}</strong> on Marina instance <strong>{marina_instance}</strong>.</p>
                
                <div class="key-box">
                    <strong>Recovery Key:</strong><br>
                    <div class="key">{recovery_key}</div>
                </div>
                
                <p><strong>Key ID:</strong> {key_id}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Expires:</strong> {expires_hours} hours from generation</p>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong><br>
                    • This key can only be used once<br>
                    • It will expire automatically in {expires_hours} hours<br>
                    • Do not share this key with anyone<br>
                    • Use it immediately for password recovery
                </div>
                
                <p>To use this key:</p>
                <ol>
                    <li>Go to your Marina login screen</li>
                    <li>Click "Forgot Password" or use recovery option</li>
                    <li>Enter the recovery key above</li>
                    <li>Follow the prompts to reset your password</li>
                </ol>
                
                <div class="footer">
                    <p>This email was automatically generated by Marina Key Backend Engine<br>
                    Instance: {marina_instance} | Network: {socket.gethostname()}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def create_recovery_email_text(self, user_id: str, recovery_key: str, key_id: str) -> str:
        """Create plain text email content for recovery key."""
        marina_instance = self.config["marina"]["hostname"]
        expires_hours = self.config["security"]["key_lifetime_hours"]
        
        return f"""
🌊 Marina Password Recovery

Hello,

A password recovery key has been generated for user {user_id} on Marina instance {marina_instance}.

Recovery Key: {recovery_key}

Key ID: {key_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Expires: {expires_hours} hours from generation

⚠️ Security Notice:
• This key can only be used once
• It will expire automatically in {expires_hours} hours  
• Do not share this key with anyone
• Use it immediately for password recovery

To use this key:
1. Go to your Marina login screen
2. Click "Forgot Password" or use recovery option
3. Enter the recovery key above
4. Follow the prompts to reset your password

This email was automatically generated by Marina Key Backend Engine
Instance: {marina_instance} | Network: {socket.gethostname()}
        """
    
    def is_authorized_request(self, requester_ip: str) -> bool:
        """Check if request is from authorized network."""
        if not self.config["security"]["require_network_auth"]:
            return True
        
        if not requester_ip:
            return True  # Local request
        
        # Check against allowed networks
        # For simplicity, basic IP range checking
        allowed_networks = self.config["security"]["allowed_networks"]
        for network in allowed_networks:
            if self.ip_in_network(requester_ip, network):
                return True
        
        return False
    
    def ip_in_network(self, ip: str, network: str) -> bool:
        """Check if IP is in network range (basic implementation)."""
        try:
            import ipaddress
            return ipaddress.ip_address(ip) in ipaddress.ip_network(network, strict=False)
        except:
            # Fallback to simple check
            if network.startswith("192.168.") and ip.startswith("192.168."):
                return True
            if network.startswith("10.") and ip.startswith("10."):
                return True
            if network.startswith("172.16.") and ip.startswith("172."):
                return True
            return False
    
    def discover_marina_nodes(self) -> List[NetworkNode]:
        """Discover other Marina instances on the network."""
        if not NETWORK_AVAILABLE:
            print("⚠️  Network discovery unavailable (missing dependencies)")
            return []
        
        discovered_nodes = []
        
        try:
            # Get local network interfaces
            interfaces = netifaces.interfaces()
            
            for interface in interfaces:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr_info in addrs[netifaces.AF_INET]:
                        ip = addr_info.get('addr')
                        if ip and not ip.startswith('127.'):
                            # Scan local network
                            network_nodes = self.scan_network_for_marina(ip)
                            discovered_nodes.extend(network_nodes)
            
            # Update our node registry
            for node in discovered_nodes:
                self.network_nodes[node.instance_id] = node
            
            self.save_keys()
            print(f"🌐 Discovered {len(discovered_nodes)} Marina nodes")
            
        except Exception as e:
            print(f"⚠️  Network discovery error: {e}")
        
        return discovered_nodes
    
    def scan_network_for_marina(self, local_ip: str) -> List[NetworkNode]:
        """Scan network segment for Marina instances."""
        nodes = []
        base_ip = '.'.join(local_ip.split('.')[:-1]) + '.'
        
        # Scan common Marina ports on local network
        for i in range(1, 255):
            target_ip = base_ip + str(i)
            if target_ip == local_ip:
                continue
            
            try:
                # Quick port check for Marina services
                response = requests.get(
                    f"http://{target_ip}:{self.network_port}/marina/info",
                    timeout=1
                )
                if response.status_code == 200:
                    info = response.json()
                    node = NetworkNode(
                        instance_id=info.get('instance_id', f'marina_{target_ip}'),
                        hostname=info.get('hostname', target_ip),
                        ip_address=target_ip,
                        port=self.network_port,
                        last_seen=datetime.now(),
                        marina_version=info.get('version', 'unknown'),
                        capabilities=info.get('capabilities', ['key_service'])
                    )
                    nodes.append(node)
            except:
                pass  # Node not responding or not Marina
        
        return nodes
    
    def request_key_from_network(self, user_id: str) -> Optional[Tuple[str, str]]:
        """Request recovery key from any available Marina node."""
        if not self.network_nodes:
            self.discover_marina_nodes()
        
        for node_id, node in self.network_nodes.items():
            try:
                response = requests.post(
                    f"http://{node.ip_address}:{node.port}/marina/generate_key",
                    json={"user_id": user_id, "requester": socket.gethostname()},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    key_id = data.get('key_id')
                    recovery_key = data.get('recovery_key')
                    
                    if key_id and recovery_key:
                        print(f"🔑 Received recovery key from {node.hostname}")
                        return key_id, recovery_key
                        
            except Exception as e:
                print(f"⚠️  Failed to get key from {node.hostname}: {e}")
        
        return None
    
    def cleanup_expired_keys(self):
        """Remove expired keys from memory and database."""
        now = datetime.now()
        expired_keys = []
        
        for key_id, key in self.active_keys.items():
            if now > key.expires_at:
                expired_keys.append(key_id)
        
        for key_id in expired_keys:
            del self.active_keys[key_id]
        
        if expired_keys:
            self.save_keys()
            print(f"🧹 Cleaned up {len(expired_keys)} expired keys")
    
    def start_network_service(self):
        """Start the network service for key requests."""
        def service_handler():
            try:
                from http.server import HTTPServer, BaseHTTPRequestHandler
                import urllib.parse
                
                class MarinaKeyHandler(BaseHTTPRequestHandler):
                    def do_POST(self):
                        if self.path == '/marina/generate_key':
                            content_length = int(self.headers['Content-Length'])
                            post_data = self.rfile.read(content_length)
                            data = json.loads(post_data.decode('utf-8'))
                            
                            user_id = data.get('user_id')
                            requester = data.get('requester')
                            
                            if user_id:
                                try:
                                    key_id, recovery_key = self.server.backend.generate_recovery_key(
                                        user_id, self.client_address[0]
                                    )
                                    
                                    # Send recovery email
                                    email_sent = self.server.backend.send_recovery_email(
                                        user_id, recovery_key, key_id
                                    )
                                    
                                    response = {
                                        'status': 'success',
                                        'key_id': key_id,
                                        'recovery_key': recovery_key,
                                        'email_sent': email_sent,
                                        'expires_hours': self.server.backend.config['security']['key_lifetime_hours']
                                    }
                                    
                                    self.send_response(200)
                                    self.send_header('Content-Type', 'application/json')
                                    self.end_headers()
                                    self.wfile.write(json.dumps(response).encode())
                                    
                                except Exception as e:
                                    self.send_error(500, f"Key generation failed: {e}")
                            else:
                                self.send_error(400, "Missing user_id")
                        else:
                            self.send_error(404)
                    
                    def do_GET(self):
                        if self.path == '/marina/info':
                            info = {
                                'instance_id': self.server.backend.config['marina']['instance_id'] or socket.gethostname(),
                                'hostname': socket.gethostname(),
                                'version': self.server.backend.config['marina']['version'],
                                'capabilities': ['key_service', 'email_delivery', 'network_discovery']
                            }
                            
                            self.send_response(200)
                            self.send_header('Content-Type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps(info).encode())
                        else:
                            self.send_error(404)
                
                server = HTTPServer(('0.0.0.0', self.network_port), MarinaKeyHandler)
                server.backend = self
                print(f"🌐 Marina Key Service started on port {self.network_port}")
                server.serve_forever()
                
            except Exception as e:
                print(f"⚠️  Network service error: {e}")
        
        thread = threading.Thread(target=service_handler, daemon=True)
        thread.start()
    
    def start(self):
        """Start the Marina Key Backend service."""
        self.running = True
        
        # Start network service
        self.start_network_service()
        
        # Start discovery if enabled
        if self.config["network"]["discovery_enabled"]:
            def discovery_loop():
                while self.running:
                    self.discover_marina_nodes()
                    time.sleep(self.config["network"]["discovery_interval"])
            
            discovery_thread = threading.Thread(target=discovery_loop, daemon=True)
            discovery_thread.start()
        
        # Cleanup loop
        def cleanup_loop():
            while self.running:
                self.cleanup_expired_keys()
                time.sleep(3600)  # Cleanup every hour
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        
        print("🚀 Marina Key Backend service started")
    
    def stop(self):
        """Stop the backend service."""
        self.running = False
        print("🛑 Marina Key Backend service stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get backend status information."""
        return {
            "running": self.running,
            "active_keys": len(self.active_keys),
            "network_nodes": len(self.network_nodes),
            "config_path": self.config_path,
            "database_path": self.database_path,
            "network_port": self.network_port,
            "email_configured": bool(self.config["email"]["username"]),
            "instance_id": self.config["marina"]["instance_id"] or socket.gethostname(),
            "capabilities": ["key_generation", "email_delivery", "network_discovery", "key_validation"]
        }


def main():
    """Main entry point for Marina Key Backend."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Marina Key Backend Engine")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--generate", help="Generate key for user")
    parser.add_argument("--validate", nargs=2, metavar=("KEY_ID", "RECOVERY_KEY"), help="Validate recovery key")
    parser.add_argument("--status", action="store_true", help="Show backend status")
    parser.add_argument("--discover", action="store_true", help="Discover Marina nodes")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon service")
    
    args = parser.parse_args()
    
    # Initialize backend
    backend = MarinaKeyBackend(args.config)
    
    if args.generate:
        try:
            key_id, recovery_key = backend.generate_recovery_key(args.generate)
            email_sent = backend.send_recovery_email(args.generate, recovery_key, key_id)
            
            print(f"✅ Generated recovery key for {args.generate}")
            print(f"Key ID: {key_id}")
            print(f"Recovery Key: {recovery_key}")
            print(f"Email sent: {'Yes' if email_sent else 'No'}")
            
        except Exception as e:
            print(f"❌ Error generating key: {e}")
    
    elif args.validate:
        key_id, recovery_key = args.validate
        if backend.validate_recovery_key(key_id, recovery_key):
            print(f"✅ Recovery key {key_id} is valid")
        else:
            print(f"❌ Recovery key {key_id} is invalid or expired")
    
    elif args.status:
        status = backend.get_status()
        print("📊 Marina Key Backend Status:")
        for key, value in status.items():
            print(f"   {key}: {value}")
    
    elif args.discover:
        nodes = backend.discover_marina_nodes()
        print(f"🌐 Discovered {len(nodes)} Marina nodes:")
        for node in nodes:
            print(f"   {node.hostname} ({node.ip_address}:{node.port}) - {node.marina_version}")
    
    elif args.daemon:
        print("🚀 Starting Marina Key Backend daemon...")
        backend.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            backend.stop()
    
    else:
        print("🔑 Marina Key Backend Engine")
        print("Use --help for available commands")
        status = backend.get_status()
        print(f"Status: {len(status['active_keys'])} active keys, {len(status['network_nodes'])} network nodes")


if __name__ == "__main__":
    main()
