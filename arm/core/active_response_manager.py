"""
Marina Active Response Manager (ARM) - Core orchestration engine
Handles incoming messages across all channels and manages automated responses
"""

import json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

from .message_types import NormalizedMessage, ResponseMessage, MessageStatus
from ..plugins.base_plugin import BasePlugin


class LogicProfile:
    """Represents a sender-specific logic profile"""
    
    def __init__(self, profile_data: Dict[str, Any]):
        self.tone = profile_data.get("tone", "professional")
        self.action = profile_data.get("action", "acknowledge")
        self.footer = profile_data.get("footer", "")
        self.allow_auto_send = profile_data.get("allow_auto_send", False)
        self.allowed_hours = profile_data.get("allowed_hours", {"start": 0, "end": 23})
        self.custom_prompt = profile_data.get("custom_prompt", "")
        self.require_approval = profile_data.get("require_approval", True)
        self.max_daily_responses = profile_data.get("max_daily_responses", 5)


class PermissionManager:
    """Handles file access permissions per sender"""
    
    def __init__(self, permissions_file: str):
        self.permissions_file = Path(permissions_file)
        self.permissions = {}
        self._load_permissions()
    
    def _load_permissions(self):
        """Load permissions from JSON file"""
        if self.permissions_file.exists():
            try:
                with open(self.permissions_file, 'r') as f:
                    self.permissions = json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load permissions: {e}")
                self.permissions = {}
    
    def can_access_path(self, sender: str, path: str) -> bool:
        """Check if sender can access a specific path"""
        sender_perms = self.permissions.get(sender, {})
        allowed_paths = sender_perms.get("allowed_paths", [])
        restricted_patterns = sender_perms.get("restricted_patterns", [])
        
        # Check if path is in allowed paths
        path_allowed = False
        for allowed_path in allowed_paths:
            expanded_path = os.path.expanduser(allowed_path)
            if path.startswith(expanded_path):
                path_allowed = True
                break
        
        if not path_allowed:
            return False
        
        # Check against restricted patterns
        for pattern in restricted_patterns:
            if re.search(pattern, path):
                return False
        
        return True
    
    def get_allowed_paths(self, sender: str) -> List[str]:
        """Get list of allowed paths for a sender"""
        return self.permissions.get(sender, {}).get("allowed_paths", [])


class ActiveResponseManager:
    """
    Core ARM engine that orchestrates automated responses
    """
    
    def __init__(self, config_dir: str = "/home/adminx/Marina/arm"):
        self.config_dir = Path(config_dir)
        self.plugins: Dict[str, BasePlugin] = {}
        
        # Initialize paths
        self.whitelist_file = self.config_dir / "email" / ".whitelist"
        self.blacklist_file = self.config_dir / "email" / ".blacklist"
        self.logic_profiles_dir = self.config_dir / "email" / "logic_profiles"
        self.permissions_file = self.config_dir / "permissions" / "email_access.json"
        self.logs_dir = self.config_dir / "email" / "logs"
        self.pending_dir = self.config_dir / "email" / "pending"
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        # Initialize components
        self.permission_manager = PermissionManager(str(self.permissions_file))
        self.whitelist = self._load_list_file(self.whitelist_file)
        self.blacklist = self._load_list_file(self.blacklist_file)
        
        # Response tracking
        self.daily_response_counts: Dict[str, Dict[str, int]] = {}
        
        # Setup logging
        self._setup_logging()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        directories = [
            self.config_dir / "email",
            self.config_dir / "permissions",
            self.logic_profiles_dir,
            self.logs_dir,
            self.pending_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create default files if they don't exist
        if not self.whitelist_file.exists():
            self.whitelist_file.write_text("# Add email addresses that can trigger auto-responses\\n")
        
        if not self.blacklist_file.exists():
            self.blacklist_file.write_text("# Add email addresses to block\\n")
        
        # Create default logic profile
        default_logic = self.logic_profiles_dir / "default.logic.json"
        if not default_logic.exists():
            default_profile = {
                "tone": "professional",
                "action": "acknowledge_and_forward",
                "footer": "This is an automated response from Marina. Rory will reply personally soon.",
                "allow_auto_send": False,
                "require_approval": True,
                "max_daily_responses": 3,
                "allowed_hours": {"start": 8, "end": 18}
            }
            with open(default_logic, 'w') as f:
                json.dump(default_profile, f, indent=2)
        
        # Create default permissions
        if not self.permissions_file.exists():
            default_perms = {
                "example@domain.com": {
                    "allowed_paths": ["~/Documents/Public"],
                    "restricted_patterns": ["*.key", "*.env", "*/private/*"]
                }
            }
            with open(self.permissions_file, 'w') as f:
                json.dump(default_perms, f, indent=2)
    
    def _setup_logging(self):
        """Setup ARM logging"""
        log_file = self.logs_dir / "arm.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ARM')
    
    def register_plugin(self, channel: str, plugin: BasePlugin):
        """Register a channel plugin"""
        self.plugins[channel] = plugin
        self.logger.info(f"Registered plugin for channel: {channel}")
    
    def _load_list_file(self, file_path: Path) -> set:
        """Load email addresses from whitelist/blacklist file"""
        if not file_path.exists():
            return set()
        
        addresses = set()
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        addresses.add(line.lower())
        except Exception as e:
            self.logger.warning(f"Failed to load {file_path}: {e}")
        
        return addresses
    
    def _load_logic_profile(self, sender: str) -> LogicProfile:
        """Load logic profile for a sender"""
        sender_file = self.logic_profiles_dir / f"{sender.replace('@', '_at_').replace('.', '_')}.logic.json"
        
        # Try sender-specific profile first
        if sender_file.exists():
            try:
                with open(sender_file, 'r') as f:
                    return LogicProfile(json.load(f))
            except Exception as e:
                self.logger.warning(f"Failed to load profile for {sender}: {e}")
        
        # Fallback to default profile
        default_file = self.logic_profiles_dir / "default.logic.json"
        try:
            with open(default_file, 'r') as f:
                return LogicProfile(json.load(f))
        except Exception as e:
            self.logger.error(f"Failed to load default profile: {e}")
            # Return minimal default
            return LogicProfile({})
    
    def _should_respond(self, message: NormalizedMessage) -> bool:
        """Check if we should respond to this message"""
        sender = message.get_sender_identifier()
        
        # Check blacklist first
        if sender in self.blacklist:
            self.logger.info(f"Sender {sender} is blacklisted - skipping response")
            return False
        
        # Check whitelist (if whitelist is empty, allow all)
        if self.whitelist and sender not in self.whitelist:
            self.logger.info(f"Sender {sender} not in whitelist - skipping response")
            return False
        
        # Check daily response limits
        today = datetime.now().strftime('%Y-%m-%d')
        if sender not in self.daily_response_counts:
            self.daily_response_counts[sender] = {}
        
        daily_count = self.daily_response_counts[sender].get(today, 0)
        logic_profile = self._load_logic_profile(sender)
        
        if daily_count >= logic_profile.max_daily_responses:
            self.logger.info(f"Daily response limit reached for {sender}")
            return False
        
        # Check time restrictions
        current_hour = datetime.now().hour
        if not (logic_profile.allowed_hours['start'] <= current_hour <= logic_profile.allowed_hours['end']):
            self.logger.info(f"Outside allowed hours for {sender}")
            return False
        
        return True
    
    def _generate_response(self, message: NormalizedMessage, logic_profile: LogicProfile) -> ResponseMessage:
        """Generate LLM response based on logic profile"""
        # This is where we'd integrate with the LLM router
        # For now, providing a basic template response
        
        prompt_template = f"""
You are Marina, an AI assistant for Rory Spring.

Message Details:
- From: {message.sender}
- Subject: {message.subject}
- Content: {message.content}

Response Guidelines:
- Tone: {logic_profile.tone}
- Action: {logic_profile.action}
- Custom instructions: {logic_profile.custom_prompt}

Generate a helpful, {logic_profile.tone} response that {logic_profile.action}s appropriately.
"""
        
        # TODO: Integrate with actual LLM router
        # For now, return a template response
        response_content = f"""Hi {message.sender.split('@')[0]},

Thank you for your message regarding "{message.subject}".

I'm Marina, Rory's AI assistant. I've received your message and will make sure Rory sees it promptly.

{logic_profile.footer}

Best regards,
Marina
"""
        
        return ResponseMessage(
            content=response_content,
            subject=f"Re: {message.subject}",
            metadata={"generated_by": "ARM", "logic_profile_used": logic_profile.tone}
        )
    
    def _log_interaction(self, message: NormalizedMessage, response: ResponseMessage, auto_sent: bool):
        """Log the interaction for audit purposes"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        sender_safe = message.sender.replace('@', '_at_').replace('.', '_')
        
        log_file = self.logs_dir / f"{timestamp}-{sender_safe}.log"
        
        log_data = {
            "timestamp": timestamp,
            "message": message.to_dict(),
            "response": {
                "content": response.content,
                "subject": response.subject,
                "auto_sent": auto_sent
            },
            "metadata": {
                "processing_time": datetime.utcnow().isoformat(),
                "auto_response": auto_sent
            }
        }
        
        try:
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to log interaction: {e}")
    
    def _increment_response_count(self, sender: str):
        """Increment daily response count for sender"""
        today = datetime.now().strftime('%Y-%m-%d')
        if sender not in self.daily_response_counts:
            self.daily_response_counts[sender] = {}
        
        self.daily_response_counts[sender][today] = self.daily_response_counts[sender].get(today, 0) + 1
    
    def handle_message(self, channel: str, raw_payload: Any) -> Dict[str, Any]:
        """
        Main entry point for handling incoming messages
        """
        if channel not in self.plugins:
            raise ValueError(f"No plugin registered for channel: {channel}")
        
        plugin = self.plugins[channel]
        
        try:
            # Normalize the message
            message = plugin.normalize(raw_payload)
            self.logger.info(f"Processing message from {message.sender} via {channel}")
            
            # Check if we should respond
            if not self._should_respond(message):
                message.status = MessageStatus.BLOCKED
                return {"status": "blocked", "reason": "Response criteria not met"}
            
            # Load logic profile and generate response
            logic_profile = self._load_logic_profile(message.sender)
            response = self._generate_response(message, logic_profile)
            
            # Determine if we should auto-send or hold for approval
            auto_send = logic_profile.allow_auto_send and not logic_profile.require_approval
            
            if auto_send:
                # Send response immediately
                plugin.respond(message, response)
                message.status = MessageStatus.RESPONDED
                self._increment_response_count(message.sender)
                self.logger.info(f"Auto-response sent to {message.sender}")
            else:
                # Hold for manual approval
                self._save_pending_response(message, response)
                message.status = MessageStatus.HELD
                self.logger.info(f"Response held for approval: {message.sender}")
            
            # Log the interaction
            self._log_interaction(message, response, auto_send)
            
            return {
                "status": "success",
                "message_id": message.message_id,
                "auto_sent": auto_send,
                "response_preview": response.content[:100] + "..." if len(response.content) > 100 else response.content
            }
            
        except Exception as e:
            self.logger.error(f"Error handling message from {channel}: {e}")
            return {"status": "error", "error": str(e)}
    
    def _save_pending_response(self, message: NormalizedMessage, response: ResponseMessage):
        """Save response for manual approval"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        sender_safe = message.sender.replace('@', '_at_').replace('.', '_')
        
        pending_file = self.pending_dir / f"{timestamp}-{sender_safe}.json"
        
        pending_data = {
            "timestamp": timestamp,
            "message": message.to_dict(),
            "response": {
                "content": response.content,
                "subject": response.subject,
                "metadata": response.metadata
            },
            "status": "pending_approval"
        }
        
        try:
            with open(pending_file, 'w') as f:
                json.dump(pending_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save pending response: {e}")
    
    def list_pending_responses(self) -> List[Dict[str, Any]]:
        """List all pending responses awaiting approval"""
        pending_responses = []
        
        if not self.pending_dir.exists():
            return pending_responses
        
        for pending_file in self.pending_dir.glob("*.json"):
            try:
                with open(pending_file, 'r') as f:
                    data = json.load(f)
                    data['file'] = pending_file.name
                    pending_responses.append(data)
            except Exception as e:
                self.logger.warning(f"Failed to read pending file {pending_file}: {e}")
        
        return sorted(pending_responses, key=lambda x: x['timestamp'], reverse=True)
    
    def approve_response(self, filename: str) -> bool:
        """Approve and send a pending response"""
        pending_file = self.pending_dir / filename
        
        if not pending_file.exists():
            return False
        
        try:
            with open(pending_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct message and response
            message_data = data['message']
            response_data = data['response']
            
            # Find the appropriate plugin
            channel = message_data['channel']
            if channel not in self.plugins:
                self.logger.error(f"No plugin for channel {channel}")
                return False
            
            plugin = self.plugins[channel]
            
            # Create response object
            response = ResponseMessage(
                content=response_data['content'],
                subject=response_data['subject'],
                metadata=response_data.get('metadata', {})
            )
            
            # Create normalized message for context
            from datetime import datetime as dt
            message = NormalizedMessage(
                message_id=message_data['message_id'],
                channel=message_data['channel'],
                sender=message_data['sender'],
                recipient=message_data['recipient'],
                subject=message_data['subject'],
                content=message_data['content'],
                timestamp=dt.fromisoformat(message_data['timestamp'].replace('Z', '+00:00'))
            )
            
            # Send response
            plugin.respond(message, response)
            
            # Remove pending file
            pending_file.unlink()
            
            # Log approval
            self.logger.info(f"Approved and sent response to {message_data['sender']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to approve response {filename}: {e}")
            return False
    
    def reject_response(self, filename: str) -> bool:
        """Reject a pending response"""
        pending_file = self.pending_dir / filename
        
        if pending_file.exists():
            try:
                pending_file.unlink()
                self.logger.info(f"Rejected pending response: {filename}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to reject response {filename}: {e}")
        
        return False
