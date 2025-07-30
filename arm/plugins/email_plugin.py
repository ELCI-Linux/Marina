"""
Email plugin for the ARM system
Handles email normalization and response
"""

import email
import smtplib
import hashlib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr
from typing import Any, Dict, Optional
import json
import os
from pathlib import Path

from .base_plugin import BasePlugin
from ..core.message_types import (
    NormalizedMessage, 
    ResponseMessage, 
    MessageAttachment, 
    MessageMetadata, 
    MessagePriority,
    MessageStatus
)


class EmailPlugin(BasePlugin):
    """Email plugin for ARM system"""
    
    def __init__(self, credentials_dir: str = "/home/adminx/Marina/.email"):
        self.credentials_dir = Path(credentials_dir)
        self.smtp_configs = {}
        self._load_credentials()
    
    def _load_credentials(self):
        """Load SMTP credentials for outgoing email"""
        if not self.credentials_dir.exists():
            return
            
        for cred_file in self.credentials_dir.iterdir():
            if cred_file.is_file() and not cred_file.name.startswith('.'):
                try:
                    with open(cred_file, 'r') as f:
                        content = f.read().strip()
                        if ';' in content:
                            email_addr, password = content.split(';', 1)
                            self.smtp_configs[email_addr] = {
                                'password': password,
                                'smtp_server': self._get_smtp_server(email_addr),
                                'smtp_port': 587
                            }
                except Exception as e:
                    print(f"Warning: Failed to load credentials from {cred_file}: {e}")
    
    def _get_smtp_server(self, email_addr: str) -> str:
        """Get SMTP server based on email domain"""
        domain = email_addr.split('@')[1].lower()
        
        smtp_map = {
            'gmail.com': 'smtp.gmail.com',
            'outlook.com': 'smtp.outlook.com',
            'hotmail.com': 'smtp.outlook.com',
            'yahoo.com': 'smtp.mail.yahoo.com',
            'icloud.com': 'smtp.mail.me.com'
        }
        
        return smtp_map.get(domain, f'smtp.{domain}')
    
    def normalize(self, raw_email: Any) -> NormalizedMessage:
        """
        Convert raw email message to NormalizedMessage
        :param raw_email: email.message.EmailMessage or dict with email data
        """
        if isinstance(raw_email, dict):
            # Handle dict format (from email ingestion system)
            message_id = raw_email.get('message_id', self._generate_message_id(raw_email))
            sender = raw_email.get('from', '')
            recipient = raw_email.get('to', '')
            subject = raw_email.get('subject', '')
            content = raw_email.get('body', raw_email.get('content', ''))
            timestamp = self._parse_timestamp(raw_email.get('date'))
            
            # Extract attachments if present
            attachments = []
            if 'attachments' in raw_email:
                for att_data in raw_email['attachments']:
                    attachment = MessageAttachment(
                        filename=att_data.get('filename', 'unknown'),
                        content_type=att_data.get('content_type', 'application/octet-stream'),
                        size_bytes=att_data.get('size', 0),
                        content=att_data.get('content'),
                        url=att_data.get('url')
                    )
                    attachments.append(attachment)
            
            # Create metadata
            metadata = MessageMetadata(
                thread_id=raw_email.get('thread_id'),
                reply_to=raw_email.get('reply_to'),
                in_reply_to=raw_email.get('in_reply_to'),
                channel_specific={
                    'message_id': raw_email.get('message_id'),
                    'headers': raw_email.get('headers', {}),
                    'detected_verification_email_from': raw_email.get('detected_verification_email_from')
                },
                verification_status=raw_email.get('verification_status', 'unknown')
            )
            
        else:
            # Handle email.message.EmailMessage format
            message_id = raw_email.get('Message-ID', self._generate_message_id({'subject': raw_email.get('Subject', '')}))
            sender = parseaddr(raw_email.get('From', ''))[1]
            recipient = parseaddr(raw_email.get('To', ''))[1]
            subject = raw_email.get('Subject', '')
            
            # Extract body content
            content = ""
            if raw_email.is_multipart():
                for part in raw_email.walk():
                    if part.get_content_type() == "text/plain":
                        content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                content = raw_email.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            timestamp = self._parse_timestamp(raw_email.get('Date'))
            
            # Extract attachments
            attachments = []
            if raw_email.is_multipart():
                for part in raw_email.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename() or 'unknown'
                        content_type = part.get_content_type()
                        payload = part.get_payload(decode=True)
                        
                        attachment = MessageAttachment(
                            filename=filename,
                            content_type=content_type,
                            size_bytes=len(payload) if payload else 0,
                            content=payload
                        )
                        attachments.append(attachment)
            
            # Create metadata
            metadata = MessageMetadata(
                thread_id=raw_email.get('Thread-Index'),
                reply_to=raw_email.get('Reply-To'),
                in_reply_to=raw_email.get('In-Reply-To'),
                channel_specific={
                    'message_id': raw_email.get('Message-ID'),
                    'headers': dict(raw_email.items()),
                    'return_path': raw_email.get('Return-Path')
                }
            )
        
        # Determine priority based on subject/content keywords
        priority = self._determine_priority(subject, content)
        
        return NormalizedMessage(
            message_id=message_id,
            channel="email",
            sender=sender,
            recipient=recipient,
            subject=subject,
            content=content,
            content_type="text/plain",
            timestamp=timestamp,
            priority=priority,
            status=MessageStatus.RECEIVED,
            attachments=attachments,
            metadata=metadata
        )
    
    def respond(self, message: NormalizedMessage, response: ResponseMessage):
        """
        Send email response
        :param message: Original normalized message
        :param response: Response to send
        """
        sender_email = message.recipient  # We're replying from the recipient
        recipient_email = message.sender  # Reply to original sender
        
        if sender_email not in self.smtp_configs:
            raise ValueError(f"No SMTP configuration found for {sender_email}")
        
        config = self.smtp_configs[sender_email]
        
        # Create email message
        msg = MIMEMultipart() if response.attachments else MIMEText(response.content)
        
        if isinstance(msg, MIMEMultipart):
            msg.attach(MIMEText(response.content, 'plain'))
            
            # Add attachments if present
            for attachment in response.attachments:
                if attachment.content:
                    part = MIMEText(attachment.content.decode('utf-8', errors='ignore'))
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{attachment.filename}"'
                    )
                    msg.attach(part)
        
        # Set headers
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = response.subject or f"Re: {message.subject}"
        
        # Add reply headers
        if message.metadata.channel_specific and 'message_id' in message.metadata.channel_specific:
            msg['In-Reply-To'] = message.metadata.channel_specific['message_id']
            msg['References'] = message.metadata.channel_specific['message_id']
        
        # Send email
        try:
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls()
                server.login(sender_email, config['password'])
                server.send_message(msg)
            
            print(f"✅ ARM: Email response sent to {recipient_email}")
            
        except Exception as e:
            print(f"❌ ARM: Failed to send email response: {e}")
            raise
    
    def _generate_message_id(self, email_data: Dict) -> str:
        """Generate a unique message ID from email data"""
        content = f"{email_data.get('subject', '')}{email_data.get('from', '')}{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _parse_timestamp(self, date_str: Optional[str]) -> datetime:
        """Parse email date string to datetime"""
        if not date_str:
            return datetime.utcnow()
        
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            # Fallback to current time if parsing fails
            return datetime.utcnow()
    
    def _determine_priority(self, subject: str, content: str) -> MessagePriority:
        """Determine message priority based on content"""
        urgent_keywords = ['urgent', 'emergency', 'asap', 'immediately', 'critical']
        high_keywords = ['important', 'priority', 'time sensitive', 'deadline']
        
        text = f"{subject} {content}".lower()
        
        for keyword in urgent_keywords:
            if keyword in text:
                return MessagePriority.URGENT
        
        for keyword in high_keywords:
            if keyword in text:
                return MessagePriority.HIGH
        
        return MessagePriority.NORMAL
