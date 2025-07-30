"""
Core message types for the ARM system
Provides normalized message format across all channels
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class MessagePriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageStatus(Enum):
    RECEIVED = "received"
    PROCESSED = "processed"
    RESPONDED = "responded"
    HELD = "held"
    BLOCKED = "blocked"
    ERROR = "error"


@dataclass
class MessageAttachment:
    """Represents an attachment in a normalized way"""
    filename: str
    content_type: str
    size_bytes: int
    content: Optional[bytes] = None
    url: Optional[str] = None  # For cloud-based attachments


@dataclass
class MessageMetadata:
    """Additional metadata about the message"""
    thread_id: Optional[str] = None
    reply_to: Optional[str] = None
    in_reply_to: Optional[str] = None
    channel_specific: Optional[Dict[str, Any]] = None  # Plugin-specific metadata
    encryption_status: Optional[str] = None
    verification_status: Optional[str] = None  # DKIM, SPF, etc.
    

@dataclass
class NormalizedMessage:
    """
    Normalized message format that works across all channels
    Plugins convert their native format to this
    """
    # Core identification
    message_id: str
    channel: str  # email, sms, slack, etc.
    sender: str   # email address, phone number, user ID, etc.
    recipient: str  # who the message was sent to
    
    # Content
    subject: Optional[str] = None
    content: str = ""
    content_type: str = "text/plain"
    
    # Temporal
    timestamp: datetime = None
    received_at: datetime = None
    
    # Classification
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.RECEIVED
    
    # Additional data
    attachments: List[MessageAttachment] = None
    metadata: MessageMetadata = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.received_at is None:
            self.received_at = datetime.utcnow()
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = MessageMetadata()
    
    def get_sender_identifier(self) -> str:
        """Get a normalized sender identifier for lookup purposes"""
        return self.sender.lower().strip()
    
    def is_urgent(self) -> bool:
        """Check if message requires urgent handling"""
        return self.priority in [MessagePriority.HIGH, MessagePriority.URGENT]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            "message_id": self.message_id,
            "channel": self.channel,
            "sender": self.sender,
            "recipient": self.recipient,
            "subject": self.subject,
            "content": self.content,
            "content_type": self.content_type,
            "timestamp": self.timestamp.isoformat(),
            "received_at": self.received_at.isoformat(),
            "priority": self.priority.value,
            "status": self.status.value,
            "attachments": [
                {
                    "filename": att.filename,
                    "content_type": att.content_type,
                    "size_bytes": att.size_bytes,
                    "has_content": att.content is not None,
                    "url": att.url
                } for att in self.attachments
            ],
            "metadata": {
                "thread_id": self.metadata.thread_id,
                "reply_to": self.metadata.reply_to,
                "in_reply_to": self.metadata.in_reply_to,
                "channel_specific": self.metadata.channel_specific,
                "encryption_status": self.metadata.encryption_status,
                "verification_status": self.metadata.verification_status
            }
        }


@dataclass
class ResponseMessage:
    """Response message to be sent back through the channel"""
    content: str
    content_type: str = "text/plain"
    subject: Optional[str] = None
    attachments: List[MessageAttachment] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}
