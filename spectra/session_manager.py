"""
Session Management System for Marina's Autonomous Browser System (Spectra)

This module provides comprehensive session management capabilities including state persistence,
authentication handling, workflow continuity, and multi-browser session coordination.
"""

import json
import logging
import time
import hashlib
import sqlite3
import pickle
from typing import Dict, List, Optional, Any, Union, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from datetime import datetime, timedelta
import uuid
import os
import threading
from contextlib import asynccontextmanager
import weakref

# Core dependencies
import aiofiles
import aiohttp
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Optional dependencies
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class SessionStatus(Enum):
    """Status of a browsing session."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"
    CORRUPTED = "corrupted"
    RESTORING = "restoring"


class AuthenticationStatus(Enum):
    """Authentication status for a session."""
    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
    EXPIRED = "expired"
    REFRESHING = "refreshing"
    FAILED = "failed"


class SessionType(Enum):
    """Type of browsing session."""
    STANDARD = "standard"
    INCOGNITO = "incognito"
    HEADLESS = "headless"
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    TESTING = "testing"


class PersistenceLevel(Enum):
    """Level of data persistence."""
    NONE = "none"
    MEMORY = "memory"
    DISK = "disk"
    DATABASE = "database"
    DISTRIBUTED = "distributed"


@dataclass
class Cookie:
    """Browser cookie representation."""
    name: str
    value: str
    domain: str
    path: str = "/"
    expires: Optional[datetime] = None
    max_age: Optional[int] = None
    secure: bool = False
    http_only: bool = False
    same_site: str = "Lax"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LocalStorageItem:
    """Local storage item representation."""
    key: str
    value: str
    domain: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    expires: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionStorage:
    """Session storage item representation."""
    key: str
    value: str
    domain: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthenticationCredentials:
    """Authentication credentials for a domain."""
    domain: str
    username: str
    password: str  # Encrypted
    token: Optional[str] = None  # Encrypted
    refresh_token: Optional[str] = None  # Encrypted
    expires_at: Optional[datetime] = None
    two_factor_enabled: bool = False
    two_factor_backup_codes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrowserState:
    """Current browser state snapshot."""
    url: str
    title: str
    viewport: Dict[str, int]
    user_agent: str
    cookies: List[Cookie] = field(default_factory=list)
    local_storage: List[LocalStorageItem] = field(default_factory=list)
    session_storage: List[SessionStorage] = field(default_factory=list)
    tabs: List[Dict[str, Any]] = field(default_factory=list)
    history: List[str] = field(default_factory=list)
    downloads: List[Dict[str, Any]] = field(default_factory=list)
    permissions: Dict[str, bool] = field(default_factory=dict)
    geolocation: Optional[Dict[str, float]] = None
    timezone: Optional[str] = None
    language: str = "en-US"
    screenshot_data: Optional[str] = None
    dom_snapshot: Optional[str] = None
    network_logs: List[Dict[str, Any]] = field(default_factory=list)
    console_logs: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    id: str
    description: str
    action_type: str
    parameters: Dict[str, Any]
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    completed: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    """Multi-step workflow definition."""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    current_step: int = 0
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    pause_points: List[int] = field(default_factory=list)
    rollback_points: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrowsingSession:
    """Complete browsing session state."""
    id: str
    name: str
    session_type: SessionType
    status: SessionStatus
    auth_status: AuthenticationStatus
    browser_state: BrowserState
    workflows: List[Workflow] = field(default_factory=list)
    credentials: List[AuthenticationCredentials] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    total_duration: float = 0.0
    page_views: int = 0
    actions_performed: int = 0
    user_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    persistence_level: PersistenceLevel = PersistenceLevel.DISK
    encrypted: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """
    Comprehensive session management system for autonomous browsing.
    Handles state persistence, authentication, workflow continuity, and session recovery.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Session storage
        self._active_sessions: Dict[str, BrowsingSession] = {}
        self._session_locks: Dict[str, threading.Lock] = {}
        self._session_callbacks: Dict[str, List[Callable]] = {}
        
        # Database connections
        self._db_connection = None
        self._redis_client = None
        
        # Storage configuration - Initialize BEFORE encryption
        self.storage_dir = self.config.get('storage_dir', './sessions')
        self.max_sessions = self.config.get('max_sessions', 100)
        self.session_timeout = self.config.get('session_timeout', 3600)  # 1 hour
        self.cleanup_interval = self.config.get('cleanup_interval', 300)  # 5 minutes
        
        # Encryption - Initialize AFTER storage_dir is set
        self._cipher_suite = None
        self._initialize_encryption()
        
        # Initialize storage
        self._initialize_storage()
        
        # Start background tasks
        self._cleanup_task = None
        self._start_background_tasks()
        
        # Performance metrics
        self._performance_stats = {
            'total_sessions': 0,
            'active_sessions': 0,
            'successful_restorations': 0,
            'failed_restorations': 0,
            'average_session_duration': 0.0,
            'total_state_saves': 0,
            'total_state_loads': 0,
            'cache_hit_rate': 0.0
        }
    
    def _initialize_encryption(self):
        """Initialize encryption for sensitive data."""
        try:
            # Generate or load encryption key
            key_file = os.path.join(self.storage_dir, '.session_key')
            
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key
                password = self.config.get('encryption_password', 'spectra-session-key').encode()
                salt = os.urandom(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
                
                # Save key securely
                os.makedirs(os.path.dirname(key_file), exist_ok=True)
                with open(key_file, 'wb') as f:
                    f.write(key)
                os.chmod(key_file, 0o600)
            
            self._cipher_suite = Fernet(key)
            self.logger.info("Encryption initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            self._cipher_suite = None
    
    def _initialize_storage(self):
        """Initialize storage backends."""
        try:
            # Create storage directory
            os.makedirs(self.storage_dir, exist_ok=True)
            
            # Initialize SQLite database
            db_path = os.path.join(self.storage_dir, 'sessions.db')
            self._db_connection = sqlite3.connect(db_path, check_same_thread=False)
            self._create_database_tables()
            
            # Initialize Redis if available
            if REDIS_AVAILABLE and self.config.get('redis_enabled', False):
                redis_config = self.config.get('redis_config', {})
                self._redis_client = redis.Redis(**redis_config)
                self.logger.info("Redis client initialized")
            
            self.logger.info("Storage initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize storage: {e}")
    
    def _create_database_tables(self):
        """Create database tables for session storage."""
        cursor = self._db_connection.cursor()
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                session_type TEXT NOT NULL,
                status TEXT NOT NULL,
                auth_status TEXT NOT NULL,
                data BLOB,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                expires_at TIMESTAMP,
                user_id TEXT,
                tags TEXT,
                encrypted BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Workflows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                data BLOB,
                status TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        
        # Credentials table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                username TEXT NOT NULL,
                encrypted_data BLOB,
                created_at TIMESTAMP,
                last_used TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        
        # Session states table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_states (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                state_data BLOB,
                created_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_session ON workflows(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_credentials_domain ON credentials(domain)')
        
        self._db_connection.commit()
    
    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        def run_cleanup():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._cleanup_expired_sessions())
            loop.close()
        
        self._cleanup_task = threading.Timer(self.cleanup_interval, run_cleanup)
        self._cleanup_task.daemon = True
        self._cleanup_task.start()
    
    def _encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data."""
        if self._cipher_suite:
            return self._cipher_suite.encrypt(data.encode())
        return data.encode()
    
    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data."""
        if self._cipher_suite:
            return self._cipher_suite.decrypt(encrypted_data).decode()
        return encrypted_data.decode()
    
    async def create_session(self, 
                           name: str,
                           session_type: SessionType = SessionType.STANDARD,
                           user_id: Optional[str] = None,
                           persistence_level: PersistenceLevel = PersistenceLevel.DISK,
                           expires_in: Optional[int] = None) -> BrowsingSession:
        """
        Create a new browsing session.
        
        Args:
            name: Human-readable name for the session
            session_type: Type of session (standard, incognito, etc.)
            user_id: Optional user identifier
            persistence_level: Level of data persistence
            expires_in: Session expiration time in seconds
            
        Returns:
            Created BrowsingSession object
        """
        session_id = str(uuid.uuid4())
        
        # Calculate expiration time
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=expires_in)
        elif self.session_timeout:
            expires_at = datetime.now() + timedelta(seconds=self.session_timeout)
        
        # Create initial browser state
        browser_state = BrowserState(
            url="about:blank",
            title="New Tab",
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )
        
        # Create session
        session = BrowsingSession(
            id=session_id,
            name=name,
            session_type=session_type,
            status=SessionStatus.ACTIVE,
            auth_status=AuthenticationStatus.UNAUTHENTICATED,
            browser_state=browser_state,
            expires_at=expires_at,
            user_id=user_id,
            persistence_level=persistence_level,
            encrypted=self.config.get('encrypt_sessions', True)
        )
        
        # Store session
        self._active_sessions[session_id] = session
        self._session_locks[session_id] = threading.Lock()
        
        # Persist to storage
        if persistence_level != PersistenceLevel.NONE:
            await self._persist_session(session)
        
        # Update metrics
        self._performance_stats['total_sessions'] += 1
        self._performance_stats['active_sessions'] += 1
        
        self.logger.info(f"Created session: {session_id} ({name})")
        return session
    
    async def get_session(self, session_id: str) -> Optional[BrowsingSession]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            BrowsingSession object or None if not found
        """
        # Check active sessions first
        if session_id in self._active_sessions:
            session = self._active_sessions[session_id]
            session.last_accessed = datetime.now()
            return session
        
        # Try to load from storage
        session = await self._load_session(session_id)
        if session:
            # Restore to active sessions
            self._active_sessions[session_id] = session
            self._session_locks[session_id] = threading.Lock()
            session.status = SessionStatus.ACTIVE
            session.last_accessed = datetime.now()
            
            self._performance_stats['successful_restorations'] += 1
            self.logger.info(f"Restored session: {session_id}")
            return session
        
        self._performance_stats['failed_restorations'] += 1
        return None
    
    async def update_session_state(self, session_id: str, browser_state: BrowserState) -> bool:
        """
        Update the browser state for a session.
        
        Args:
            session_id: Session to update
            browser_state: New browser state
            
        Returns:
            True if successful, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        try:
            with self._session_locks[session_id]:
                session.browser_state = browser_state
                session.last_accessed = datetime.now()
                session.actions_performed += 1
                
                # Update page views if URL changed
                if browser_state.url != session.browser_state.url:
                    session.page_views += 1
                
                # Persist changes
                if session.persistence_level != PersistenceLevel.NONE:
                    await self._persist_session(session)
                
                self._performance_stats['total_state_saves'] += 1
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update session state: {e}")
            return False
    
    async def add_workflow(self, session_id: str, workflow: Workflow) -> bool:
        """
        Add a workflow to a session.
        
        Args:
            session_id: Session to add workflow to
            workflow: Workflow to add
            
        Returns:
            True if successful, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        try:
            with self._session_locks[session_id]:
                session.workflows.append(workflow)
                session.last_accessed = datetime.now()
                
                # Persist changes
                await self._persist_workflow(session_id, workflow)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to add workflow: {e}")
            return False
    
    async def update_workflow_progress(self, session_id: str, workflow_id: str, 
                                     step_index: int, result: Any = None, 
                                     error: Optional[str] = None) -> bool:
        """
        Update workflow progress.
        
        Args:
            session_id: Session containing the workflow
            workflow_id: Workflow to update
            step_index: Index of completed step
            result: Result of the step
            error: Error message if step failed
            
        Returns:
            True if successful, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        try:
            with self._session_locks[session_id]:
                # Find workflow
                workflow = None
                for w in session.workflows:
                    if w.id == workflow_id:
                        workflow = w
                        break
                
                if not workflow:
                    return False
                
                # Update step
                if 0 <= step_index < len(workflow.steps):
                    step = workflow.steps[step_index]
                    step.completed = error is None
                    step.result = result
                    step.error = error
                    step.completed_at = datetime.now()
                    
                    # Update workflow progress
                    completed_steps = sum(1 for s in workflow.steps if s.completed)
                    workflow.progress = completed_steps / len(workflow.steps)
                    workflow.current_step = step_index + 1
                    
                    # Check if workflow is complete
                    if workflow.current_step >= len(workflow.steps):
                        workflow.status = "completed"
                        workflow.completed_at = datetime.now()
                
                session.last_accessed = datetime.now()
                
                # Persist changes
                await self._persist_workflow(session_id, workflow)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update workflow progress: {e}")
            return False
    
    async def store_credentials(self, session_id: str, credentials: AuthenticationCredentials) -> bool:
        """
        Store authentication credentials for a session.
        
        Args:
            session_id: Session to store credentials for
            credentials: Authentication credentials
            
        Returns:
            True if successful, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        try:
            with self._session_locks[session_id]:
                # Encrypt sensitive data
                encrypted_credentials = AuthenticationCredentials(
                    domain=credentials.domain,
                    username=credentials.username,
                    password=self._encrypt_data(credentials.password).decode('latin-1'),
                    token=self._encrypt_data(credentials.token).decode('latin-1') if credentials.token else None,
                    refresh_token=self._encrypt_data(credentials.refresh_token).decode('latin-1') if credentials.refresh_token else None,
                    expires_at=credentials.expires_at,
                    two_factor_enabled=credentials.two_factor_enabled,
                    two_factor_backup_codes=credentials.two_factor_backup_codes,
                    metadata=credentials.metadata
                )
                
                # Remove existing credentials for the same domain
                session.credentials = [c for c in session.credentials if c.domain != credentials.domain]
                
                # Add new credentials
                session.credentials.append(encrypted_credentials)
                session.auth_status = AuthenticationStatus.AUTHENTICATED
                session.last_accessed = datetime.now()
                
                # Persist changes
                await self._persist_credentials(session_id, encrypted_credentials)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store credentials: {e}")
            return False
    
    async def get_credentials(self, session_id: str, domain: str) -> Optional[AuthenticationCredentials]:
        """
        Retrieve stored credentials for a domain.
        
        Args:
            session_id: Session to get credentials from
            domain: Domain to get credentials for
            
        Returns:
            AuthenticationCredentials object or None if not found
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        try:
            for credentials in session.credentials:
                if credentials.domain == domain:
                    # Decrypt sensitive data
                    decrypted_credentials = AuthenticationCredentials(
                        domain=credentials.domain,
                        username=credentials.username,
                        password=self._decrypt_data(credentials.password.encode('latin-1')),
                        token=self._decrypt_data(credentials.token.encode('latin-1')) if credentials.token else None,
                        refresh_token=self._decrypt_data(credentials.refresh_token.encode('latin-1')) if credentials.refresh_token else None,
                        expires_at=credentials.expires_at,
                        two_factor_enabled=credentials.two_factor_enabled,
                        two_factor_backup_codes=credentials.two_factor_backup_codes,
                        metadata=credentials.metadata
                    )
                    
                    credentials.last_used = datetime.now()
                    return decrypted_credentials
                    
        except Exception as e:
            self.logger.error(f"Failed to retrieve credentials: {e}")
        
        return None
    
    async def suspend_session(self, session_id: str) -> bool:
        """
        Suspend a session, preserving state but freeing resources.
        
        Args:
            session_id: Session to suspend
            
        Returns:
            True if successful, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        try:
            with self._session_locks[session_id]:
                session.status = SessionStatus.SUSPENDED
                session.last_accessed = datetime.now()
                
                # Calculate session duration
                duration = (datetime.now() - session.created_at).total_seconds()
                session.total_duration += duration
                
                # Persist final state
                await self._persist_session(session)
                
                # Remove from active sessions
                del self._active_sessions[session_id]
                del self._session_locks[session_id]
                
                self._performance_stats['active_sessions'] -= 1
                self.logger.info(f"Suspended session: {session_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to suspend session: {e}")
            return False
    
    async def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a session permanently.
        
        Args:
            session_id: Session to terminate
            
        Returns:
            True if successful, False otherwise
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        try:
            with self._session_locks[session_id]:
                session.status = SessionStatus.TERMINATED
                session.last_accessed = datetime.now()
                
                # Calculate final duration
                duration = (datetime.now() - session.created_at).total_seconds()
                session.total_duration += duration
                
                # Update average session duration
                total_sessions = self._performance_stats['total_sessions']
                current_avg = self._performance_stats['average_session_duration']
                self._performance_stats['average_session_duration'] = (
                    (current_avg * (total_sessions - 1) + duration) / total_sessions
                )
                
                # Persist final state
                await self._persist_session(session)
                
                # Clean up
                if session_id in self._active_sessions:
                    del self._active_sessions[session_id]
                if session_id in self._session_locks:
                    del self._session_locks[session_id]
                if session_id in self._session_callbacks:
                    del self._session_callbacks[session_id]
                
                self._performance_stats['active_sessions'] -= 1
                self.logger.info(f"Terminated session: {session_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to terminate session: {e}")
            return False
    
    async def list_sessions(self, user_id: Optional[str] = None, 
                           status: Optional[SessionStatus] = None,
                           limit: int = 100) -> List[BrowsingSession]:
        """
        List sessions with optional filtering.
        
        Args:
            user_id: Filter by user ID
            status: Filter by session status
            limit: Maximum number of sessions to return
            
        Returns:
            List of BrowsingSession objects
        """
        sessions = []
        
        try:
            # Get active sessions
            for session in self._active_sessions.values():
                if user_id and session.user_id != user_id:
                    continue
                if status and session.status != status:
                    continue
                sessions.append(session)
            
            # Get stored sessions if needed
            if len(sessions) < limit:
                stored_sessions = await self._load_sessions_from_storage(user_id, status, limit - len(sessions))
                sessions.extend(stored_sessions)
            
            # Sort by last accessed time
            sessions.sort(key=lambda s: s.last_accessed, reverse=True)
            
            return sessions[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to list sessions: {e}")
            return []
    
    async def clone_session(self, session_id: str, new_name: str) -> Optional[BrowsingSession]:
        """
        Clone an existing session.
        
        Args:
            session_id: Session to clone
            new_name: Name for the cloned session
            
        Returns:
            Cloned BrowsingSession object or None if failed
        """
        original_session = await self.get_session(session_id)
        if not original_session:
            return None
        
        try:
            # Create new session with copied state
            cloned_session = await self.create_session(
                name=new_name,
                session_type=original_session.session_type,
                user_id=original_session.user_id,
                persistence_level=original_session.persistence_level
            )
            
            # Copy browser state
            cloned_session.browser_state = BrowserState(
                url=original_session.browser_state.url,
                title=original_session.browser_state.title,
                viewport=original_session.browser_state.viewport.copy(),
                user_agent=original_session.browser_state.user_agent,
                cookies=original_session.browser_state.cookies.copy(),
                local_storage=original_session.browser_state.local_storage.copy(),
                session_storage=original_session.browser_state.session_storage.copy(),
                tabs=original_session.browser_state.tabs.copy(),
                history=original_session.browser_state.history.copy(),
                permissions=original_session.browser_state.permissions.copy(),
                geolocation=original_session.browser_state.geolocation,
                timezone=original_session.browser_state.timezone,
                language=original_session.browser_state.language,
                metadata=original_session.browser_state.metadata.copy()
            )
            
            # Copy workflows (but reset their progress)
            for workflow in original_session.workflows:
                cloned_workflow = Workflow(
                    id=str(uuid.uuid4()),
                    name=workflow.name,
                    description=workflow.description,
                    steps=workflow.steps.copy(),
                    current_step=0,
                    status="pending",
                    progress=0.0,
                    pause_points=workflow.pause_points.copy(),
                    rollback_points=workflow.rollback_points.copy(),
                    metadata=workflow.metadata.copy()
                )
                cloned_session.workflows.append(cloned_workflow)
            
            # Copy credentials
            cloned_session.credentials = original_session.credentials.copy()
            
            # Copy tags and metadata
            cloned_session.tags = original_session.tags.copy()
            cloned_session.metadata = original_session.metadata.copy()
            
            # Persist cloned session
            await self._persist_session(cloned_session)
            
            self.logger.info(f"Cloned session: {session_id} -> {cloned_session.id}")
            return cloned_session
            
        except Exception as e:
            self.logger.error(f"Failed to clone session: {e}")
            return None
    
    async def export_session(self, session_id: str, include_credentials: bool = False) -> Optional[Dict[str, Any]]:
        """
        Export session data for backup or transfer.
        
        Args:
            session_id: Session to export
            include_credentials: Whether to include credentials in export
            
        Returns:
            Dictionary containing session data or None if failed
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        try:
            # Convert session to dictionary
            session_data = asdict(session)
            
            # Remove sensitive data if requested
            if not include_credentials:
                session_data['credentials'] = []
            
            # Add export metadata
            session_data['export_metadata'] = {
                'exported_at': datetime.now().isoformat(),
                'exported_by': 'Marina Spectra Session Manager',
                'version': '1.0',
                'includes_credentials': include_credentials
            }
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"Failed to export session: {e}")
            return None
    
    async def import_session(self, session_data: Dict[str, Any], new_name: Optional[str] = None) -> Optional[BrowsingSession]:
        """
        Import session data from backup or transfer.
        
        Args:
            session_data: Dictionary containing session data
            new_name: Optional new name for imported session
            
        Returns:
            Imported BrowsingSession object or None if failed
        """
        try:
            # Generate new session ID
            new_session_id = str(uuid.uuid4())
            
            # Update session data
            session_data['id'] = new_session_id
            session_data['created_at'] = datetime.now()
            session_data['last_accessed'] = datetime.now()
            session_data['status'] = SessionStatus.ACTIVE.value
            
            if new_name:
                session_data['name'] = new_name
            
            # Remove export metadata
            session_data.pop('export_metadata', None)
            
            # Convert back to BrowsingSession object
            # Note: This is a simplified conversion - in practice, you'd need
            # proper deserialization handling for complex objects
            
            # Create new session
            imported_session = await self.create_session(
                name=session_data['name'],
                session_type=SessionType(session_data['session_type']),
                user_id=session_data.get('user_id'),
                persistence_level=PersistenceLevel(session_data['persistence_level'])
            )
            
            # Update with imported data
            # This would involve reconstructing all the dataclass objects
            # from the dictionary representation
            
            self.logger.info(f"Imported session: {new_session_id}")
            return imported_session
            
        except Exception as e:
            self.logger.error(f"Failed to import session: {e}")
            return None
    
    async def _persist_session(self, session: BrowsingSession):
        """Persist session to storage."""
        try:
            if session.persistence_level == PersistenceLevel.NONE:
                return
            
            # Serialize session data
            session_data = pickle.dumps(session)
            
            # Encrypt if enabled
            if session.encrypted:
                session_data = self._encrypt_data(session_data.decode('latin-1')).decode('latin-1')
            
            # Store in database
            cursor = self._db_connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO sessions 
                (id, name, session_type, status, auth_status, data, created_at, last_accessed, expires_at, user_id, tags, encrypted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.id,
                session.name,
                session.session_type.value,
                session.status.value,
                session.auth_status.value,
                session_data,
                session.created_at,
                session.last_accessed,
                session.expires_at,
                session.user_id,
                json.dumps(session.tags),
                session.encrypted
            ))
            self._db_connection.commit()
            
            # Store in Redis if available
            if self._redis_client:
                self._redis_client.set(f"session:{session.id}", session_data, ex=self.session_timeout)
            
        except Exception as e:
            self.logger.error(f"Failed to persist session: {e}")
    
    async def _load_session(self, session_id: str) -> Optional[BrowsingSession]:
        """Load session from storage."""
        try:
            # Try Redis first
            if self._redis_client:
                session_data = self._redis_client.get(f"session:{session_id}")
                if session_data:
                    if isinstance(session_data, bytes):
                        session_data = session_data.decode('latin-1')
                    
                    # Decrypt if encrypted
                    if session_data:
                        session_data = self._decrypt_data(session_data.encode('latin-1'))
                    
                    # Deserialize
                    session = pickle.loads(session_data.encode('latin-1'))
                    return session
            
            # Try database
            cursor = self._db_connection.cursor()
            cursor.execute('SELECT data, encrypted FROM sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            
            if row:
                session_data, encrypted = row
                
                # Decrypt if encrypted
                if encrypted:
                    session_data = self._decrypt_data(session_data.encode('latin-1'))
                
                # Deserialize
                session = pickle.loads(session_data.encode('latin-1'))
                return session
            
        except Exception as e:
            self.logger.error(f"Failed to load session: {e}")
        
        return None
    
    async def _load_sessions_from_storage(self, user_id: Optional[str], 
                                        status: Optional[SessionStatus],
                                        limit: int) -> List[BrowsingSession]:
        """Load sessions from storage with filtering."""
        sessions = []
        
        try:
            cursor = self._db_connection.cursor()
            
            # Build query
            query = 'SELECT id FROM sessions WHERE 1=1'
            params = []
            
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            if status:
                query += ' AND status = ?'
                params.append(status.value)
            
            query += ' ORDER BY last_accessed DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Load each session
            for row in rows:
                session_id = row[0]
                session = await self._load_session(session_id)
                if session:
                    sessions.append(session)
            
        except Exception as e:
            self.logger.error(f"Failed to load sessions from storage: {e}")
        
        return sessions
    
    async def _persist_workflow(self, session_id: str, workflow: Workflow):
        """Persist workflow to storage."""
        try:
            workflow_data = pickle.dumps(workflow)
            
            cursor = self._db_connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO workflows 
                (id, session_id, name, description, data, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                workflow.id,
                session_id,
                workflow.name,
                workflow.description,
                workflow_data,
                workflow.status,
                workflow.created_at
            ))
            self._db_connection.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to persist workflow: {e}")
    
    async def _persist_credentials(self, session_id: str, credentials: AuthenticationCredentials):
        """Persist credentials to storage."""
        try:
            credentials_data = pickle.dumps(credentials)
            
            cursor = self._db_connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO credentials 
                (id, session_id, domain, username, encrypted_data, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()),
                session_id,
                credentials.domain,
                credentials.username,
                credentials_data,
                credentials.created_at,
                credentials.last_used
            ))
            self._db_connection.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to persist credentials: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            current_time = datetime.now()
            expired_sessions = []
            
            # Check active sessions
            for session_id, session in self._active_sessions.items():
                if session.expires_at and session.expires_at < current_time:
                    expired_sessions.append(session_id)
            
            # Terminate expired sessions
            for session_id in expired_sessions:
                await self.terminate_session(session_id)
            
            # Clean up database
            cursor = self._db_connection.cursor()
            cursor.execute('DELETE FROM sessions WHERE expires_at < ?', (current_time,))
            self._db_connection.commit()
            
            if expired_sessions:
                self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
            # Schedule next cleanup
            self._cleanup_task = threading.Timer(self.cleanup_interval, 
                                               lambda: asyncio.create_task(self._cleanup_expired_sessions()))
            self._cleanup_task.daemon = True
            self._cleanup_task.start()
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
    
    def register_session_callback(self, session_id: str, callback: Callable):
        """Register a callback for session events."""
        if session_id not in self._session_callbacks:
            self._session_callbacks[session_id] = []
        self._session_callbacks[session_id].append(callback)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self._performance_stats.copy()
        stats['active_sessions'] = len(self._active_sessions)
        return stats
    
    def __del__(self):
        """Cleanup on destruction."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        if self._db_connection:
            self._db_connection.close()
        
        if self._redis_client:
            self._redis_client.close()


# Example usage and testing
if __name__ == "__main__":
    async def main():
        # Initialize session manager
        manager = SessionManager({
            'storage_dir': './test_sessions',
            'session_timeout': 3600,
            'encrypt_sessions': True
        })
        
        # Create a new session
        session = await manager.create_session(
            name="Test Browsing Session",
            session_type=SessionType.STANDARD,
            user_id="test_user"
        )
        
        print(f"Created session: {session.id}")
        print(f"Session name: {session.name}")
        print(f"Session type: {session.session_type.value}")
        print(f"Status: {session.status.value}")
        
        # Update browser state
        browser_state = BrowserState(
            url="https://example.com",
            title="Example Site",
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )
        
        success = await manager.update_session_state(session.id, browser_state)
        print(f"State update: {'Success' if success else 'Failed'}")
        
        # Add a workflow
        workflow = Workflow(
            id=str(uuid.uuid4()),
            name="Test Workflow",
            description="A test workflow",
            steps=[
                WorkflowStep(
                    id=str(uuid.uuid4()),
                    description="Navigate to site",
                    action_type="navigate",
                    parameters={"url": "https://example.com"}
                ),
                WorkflowStep(
                    id=str(uuid.uuid4()),
                    description="Click button",
                    action_type="click",
                    parameters={"selector": "#submit-button"}
                )
            ]
        )
        
        success = await manager.add_workflow(session.id, workflow)
        print(f"Workflow added: {'Success' if success else 'Failed'}")
        
        # Store credentials
        credentials = AuthenticationCredentials(
            domain="example.com",
            username="test_user",
            password="test_password"
        )
        
        success = await manager.store_credentials(session.id, credentials)
        print(f"Credentials stored: {'Success' if success else 'Failed'}")
        
        # Retrieve credentials
        retrieved_creds = await manager.get_credentials(session.id, "example.com")
        if retrieved_creds:
            print(f"Retrieved credentials for: {retrieved_creds.username}")
        
        # List sessions
        sessions = await manager.list_sessions(user_id="test_user")
        print(f"Found {len(sessions)} sessions")
        
        # Get performance stats
        stats = manager.get_performance_stats()
        print(f"Performance stats: {stats}")
        
        # Export session
        exported_data = await manager.export_session(session.id)
        if exported_data:
            print("Session exported successfully")
        
        # Suspend session
        success = await manager.suspend_session(session.id)
        print(f"Session suspended: {'Success' if success else 'Failed'}")
        
        # Try to restore session
        restored_session = await manager.get_session(session.id)
        if restored_session:
            print(f"Session restored: {restored_session.id}")
        
        # Terminate session
        success = await manager.terminate_session(session.id)
        print(f"Session terminated: {'Success' if success else 'Failed'}")
    
    # Run the example
    asyncio.run(main())
