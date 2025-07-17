"""
Spectra Core - Main Integration Layer for Marina's Autonomous Browser System

This module serves as the central orchestration engine that integrates all Spectra components
into a unified, intelligent autonomous browsing system with advanced coordination and control.
"""

import json
import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid
import os
import signal
import sys
import threading
from contextlib import asynccontextmanager
import traceback

# Import all Spectra components
from .navigation_core import NavigatorCore, NavigationMode
from .action_validator import ActionValidator, ValidationResult
from .media_perception import MediaPerceptionEngine, MediaAnalysis, MediaType
from .intent_compiler import IntentCompiler, Intent, IntentType, ExecutionStatus
from .session_manager import SessionManager, BrowsingSession, SessionType, SessionStatus

# Core dependencies
import yaml
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# Optional dependencies
try:
    import prometheus_client
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


class SpectraMode(Enum):
    """Operating modes for Spectra."""
    AUTONOMOUS = "autonomous"
    SUPERVISED = "supervised"
    INTERACTIVE = "interactive"
    TESTING = "testing"
    HEADLESS = "headless"


class ComponentStatus(Enum):
    """Status of individual components."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"
    INITIALIZING = "initializing"


class ExecutionPriority(Enum):
    """Priority levels for execution."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


@dataclass
class ComponentHealth:
    """Health status of a component."""
    name: str
    status: ComponentStatus
    last_check: datetime
    error_count: int = 0
    last_error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ExecutionContext:
    """Context for action execution."""
    session_id: str
    intent_id: str
    user_id: Optional[str] = None
    priority: ExecutionPriority = ExecutionPriority.MEDIUM
    timeout: float = 300.0
    retry_count: int = 3
    validate_actions: bool = True
    analyze_media: bool = True
    save_screenshots: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of intent execution."""
    intent_id: str
    session_id: str
    success: bool
    execution_time: float
    actions_performed: int
    validation_results: List[ValidationResult] = field(default_factory=list)
    media_analyses: List[MediaAnalysis] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpectraConfig:
    """Configuration for Spectra system."""
    # Core settings
    mode: SpectraMode = SpectraMode.AUTONOMOUS
    max_concurrent_sessions: int = 10
    default_timeout: float = 300.0
    
    # Component settings
    navigation_backend: NavigationMode = NavigationMode.PLAYWRIGHT
    enable_media_perception: bool = True
    enable_action_validation: bool = True
    enable_session_persistence: bool = True
    
    # Storage settings
    storage_dir: str = "./spectra_data"
    session_timeout: int = 3600
    encrypt_sessions: bool = True
    
    # Performance settings
    max_memory_usage: int = 4096  # MB
    max_cpu_usage: float = 80.0   # %
    cleanup_interval: int = 300   # seconds
    
    # Security settings
    sandbox_mode: bool = True
    allow_file_access: bool = False
    allow_microphone: bool = False
    allow_camera: bool = False
    
    # Monitoring settings
    enable_metrics: bool = True
    enable_logging: bool = True
    log_level: str = "INFO"
    
    # Integration settings
    webhook_url: Optional[str] = None
    api_key: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)


class SpectraCore:
    """
    Main integration layer orchestrating all Spectra components.
    Provides unified interface for autonomous browsing with intelligent coordination.
    """
    
    def __init__(self, config: Optional[SpectraConfig] = None):
        self.config = config or SpectraConfig()
        self.logger = self._setup_logging()
        
        # Component instances
        self.navigation_engine: Optional[NavigatorCore] = None
        self.action_validator: Optional[ActionValidator] = None
        self.media_perception: Optional[MediaPerceptionEngine] = None
        self.intent_compiler: Optional[IntentCompiler] = None
        self.session_manager: Optional[SessionManager] = None
        
        # System state
        self._component_health: Dict[str, ComponentHealth] = {}
        self._active_executions: Dict[str, ExecutionContext] = {}
        self._execution_queue: asyncio.Queue = asyncio.Queue()
        self._shutdown_event = asyncio.Event()
        
        # Browser instances
        self._playwright = None
        self._browsers: Dict[str, Browser] = {}
        self._browser_contexts: Dict[str, BrowserContext] = {}
        
        # Performance monitoring
        self._start_time = time.time()
        self._performance_metrics = {
            'total_intents': 0,
            'successful_intents': 0,
            'failed_intents': 0,
            'average_execution_time': 0.0,
            'total_sessions': 0,
            'active_sessions': 0,
            'memory_usage': 0.0,
            'cpu_usage': 0.0
        }
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Initialize system
        self._initialize_system()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging configuration."""
        logger = logging.getLogger('spectra')
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        if not logger.handlers:
            # Create formatters
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
            )
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(logging.INFO)
            logger.addHandler(console_handler)
            
            # File handler
            try:
                log_dir = os.path.join(self.config.storage_dir, 'logs')
                os.makedirs(log_dir, exist_ok=True)
                file_handler = logging.FileHandler(
                    os.path.join(log_dir, 'spectra.log'),
                    mode='a',
                    encoding='utf-8'
                )
                file_handler.setFormatter(file_formatter)
                file_handler.setLevel(logging.DEBUG)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Failed to setup file logging: {e}")
            
            # Error handler for critical issues
            try:
                error_handler = logging.FileHandler(
                    os.path.join(log_dir, 'errors.log'),
                    mode='a',
                    encoding='utf-8'
                )
                error_handler.setFormatter(file_formatter)
                error_handler.setLevel(logging.ERROR)
                logger.addHandler(error_handler)
            except Exception as e:
                logger.warning(f"Failed to setup error logging: {e}")
        
        return logger
    
    def _initialize_system(self):
        """Initialize the Spectra system."""
        try:
            # Setup directories
            os.makedirs(self.config.storage_dir, exist_ok=True)
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Initialize monitoring
            if PROMETHEUS_AVAILABLE and self.config.enable_metrics:
                self._setup_prometheus_metrics()
            
            if SENTRY_AVAILABLE and self.config.api_key:
                sentry_sdk.init(dsn=self.config.api_key)
            
            self.logger.info("Spectra system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system: {e}")
            raise
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics collection."""
        try:
            self._metrics = {
                'intents_total': prometheus_client.Counter(
                    'spectra_intents_total',
                    'Total number of intents processed',
                    ['status', 'intent_type']
                ),
                'execution_time': prometheus_client.Histogram(
                    'spectra_execution_time_seconds',
                    'Intent execution time in seconds',
                    ['intent_type']
                ),
                'active_sessions': prometheus_client.Gauge(
                    'spectra_active_sessions',
                    'Number of active browsing sessions'
                ),
                'component_health': prometheus_client.Enum(
                    'spectra_component_health',
                    'Health status of components',
                    ['component'],
                    states=['healthy', 'degraded', 'failed', 'disabled']
                )
            }
            
            # Start metrics server
            prometheus_client.start_http_server(8000)
            self.logger.info("Prometheus metrics server started on port 8000")
            
        except Exception as e:
            self.logger.warning(f"Failed to setup Prometheus metrics: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.shutdown())
    
    async def initialize(self):
        """Initialize all components asynchronously."""
        try:
            self.logger.info("Initializing Spectra components...")
            
            # Initialize browser engine
            await self._initialize_browser_engine()
            
            # Initialize components in dependency order
            await self._initialize_session_manager()
            await self._initialize_navigation_engine()
            await self._initialize_action_validator()
            await self._initialize_media_perception()
            await self._initialize_intent_compiler()
            
            # Setup component callbacks
            self._setup_component_callbacks()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Health check
            await self._perform_health_check()
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            raise
    
    async def _initialize_browser_engine(self):
        """Initialize the browser engine with robust error handling."""
        self.logger.info("Initializing browser engine...")
        
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                if self.config.navigation_backend == NavigationMode.PLAYWRIGHT:
                    self.logger.debug("Starting Playwright...")
                    self._playwright = await async_playwright().start()
                    
                    # Launch browsers with fallback strategy
                    browser_configs = [
                        {
                            'name': 'chromium',
                            'launcher': self._playwright.chromium.launch,
                            'args': self._get_chromium_args()
                        },
                        {
                            'name': 'firefox',
                            'launcher': self._playwright.firefox.launch,
                            'args': self._get_firefox_args()
                        }
                    ]
                    
                    successful_browsers = 0
                    for config in browser_configs:
                        try:
                            self.logger.debug(f"Launching {config['name']} browser...")
                            browser = await config['launcher'](**config['args'])
                            
                            # Test browser functionality
                            await self._test_browser_functionality(browser)
                            
                            self._browsers[config['name']] = browser
                            successful_browsers += 1
                            self.logger.info(f"Successfully initialized {config['name']} browser")
                            
                        except Exception as e:
                            self.logger.warning(f"Failed to initialize {config['name']}: {e}")
                            if config['name'] in self._browsers:
                                try:
                                    await self._browsers[config['name']].close()
                                except:
                                    pass
                                del self._browsers[config['name']]
                    
                    if successful_browsers == 0:
                        raise RuntimeError("Failed to initialize any browser")
                    
                    if successful_browsers < len(browser_configs):
                        self._update_component_health('browser_engine', ComponentStatus.DEGRADED)
                        self.logger.warning(f"Only {successful_browsers}/{len(browser_configs)} browsers initialized")
                    else:
                        self._update_component_health('browser_engine', ComponentStatus.HEALTHY)
                    
                    return  # Success
                    
                else:
                    # Selenium fallback
                    self.logger.info("Using Selenium backend")
                    await self._initialize_selenium_backend()
                    self._update_component_health('browser_engine', ComponentStatus.HEALTHY)
                    return
                    
            except Exception as e:
                self.logger.error(f"Browser initialization attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self._update_component_health('browser_engine', ComponentStatus.FAILED, str(e))
                    raise RuntimeError(f"Failed to initialize browser engine after {max_retries} attempts: {e}")
    
    def _get_chromium_args(self) -> Dict[str, Any]:
        """Get Chromium launch arguments."""
        args = {
            'headless': self.config.mode == SpectraMode.HEADLESS,
            'args': [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows'
            ]
        }
        
        if not self.config.sandbox_mode:
            args['args'].extend([
                '--disable-web-security',
                '--allow-running-insecure-content'
            ])
        
        return args
    
    def _get_firefox_args(self) -> Dict[str, Any]:
        """Get Firefox launch arguments."""
        return {
            'headless': self.config.mode == SpectraMode.HEADLESS,
            'args': [
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        }
    
    async def _test_browser_functionality(self, browser: Browser):
        """Test basic browser functionality."""
        try:
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto('about:blank')
            await page.title()
            await context.close()
            self.logger.debug("Browser functionality test passed")
        except Exception as e:
            self.logger.error(f"Browser functionality test failed: {e}")
            raise
    
    async def _initialize_selenium_backend(self):
        """Initialize Selenium as fallback browser backend."""
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.firefox.service import Service as FirefoxService
            
            # Try Chrome first
            try:
                chrome_options = ChromeOptions()
                if self.config.mode == SpectraMode.HEADLESS:
                    chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                
                driver = webdriver.Chrome(options=chrome_options)
                driver.get('about:blank')
                self.selenium_driver = driver
                self.logger.info("Selenium Chrome driver initialized")
                return
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize Selenium Chrome: {e}")
            
            # Try Firefox as fallback
            try:
                firefox_options = FirefoxOptions()
                if self.config.mode == SpectraMode.HEADLESS:
                    firefox_options.add_argument('--headless')
                
                driver = webdriver.Firefox(options=firefox_options)
                driver.get('about:blank')
                self.selenium_driver = driver
                self.logger.info("Selenium Firefox driver initialized")
                return
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize Selenium Firefox: {e}")
                
            raise RuntimeError("Failed to initialize any Selenium driver")
            
        except ImportError as e:
            self.logger.error(f"Selenium not available: {e}")
            raise
    
    async def _initialize_session_manager(self):
        """Initialize the session manager."""
        try:
            session_config = {
                'storage_dir': os.path.join(self.config.storage_dir, 'sessions'),
                'session_timeout': self.config.session_timeout,
                'encrypt_sessions': self.config.encrypt_sessions,
                'max_sessions': self.config.max_concurrent_sessions
            }
            
            self.session_manager = SessionManager(session_config)
            self._update_component_health('session_manager', ComponentStatus.HEALTHY)
            
        except Exception as e:
            self._update_component_health('session_manager', ComponentStatus.FAILED, str(e))
            raise
    
    async def _initialize_navigation_engine(self):
        """Initialize the navigation engine."""
        try:
            # NavigatorCore constructor takes mode, headless, and user_agent
            self.navigation_engine = NavigatorCore(
                mode=self.config.navigation_backend,
                headless=self.config.mode == SpectraMode.HEADLESS,
                user_agent=None  # Will use default
            )
            
            # Set additional configuration
            self.navigation_engine.default_timeout = self.config.default_timeout
            
            await self.navigation_engine.initialize()
            
            self._update_component_health('navigation_engine', ComponentStatus.HEALTHY)
            
        except Exception as e:
            self._update_component_health('navigation_engine', ComponentStatus.FAILED, str(e))
            if self.config.mode != SpectraMode.TESTING:
                raise
    
    async def _initialize_action_validator(self):
        """Initialize the action validator."""
        try:
            if self.config.enable_action_validation and self.navigation_engine:
                # ActionValidator requires NavigatorCore instance
                self.action_validator = ActionValidator(self.navigation_engine)
                await self.action_validator.initialize()
                self._update_component_health('action_validator', ComponentStatus.HEALTHY)
            else:
                self._update_component_health('action_validator', ComponentStatus.DISABLED)
                
        except Exception as e:
            self._update_component_health('action_validator', ComponentStatus.FAILED, str(e))
    
    async def _initialize_media_perception(self):
        """Initialize the media perception engine."""
        try:
            if self.config.enable_media_perception:
                media_config = {
                    'cache_max_size': 1000,
                    'enable_ocr': True,
                    'enable_face_detection': False,  # Privacy consideration
                    'enable_audio_processing': False
                }
                
                self.media_perception = MediaPerceptionEngine(media_config)
                self._update_component_health('media_perception', ComponentStatus.HEALTHY)
            else:
                self._update_component_health('media_perception', ComponentStatus.DISABLED)
                
        except Exception as e:
            self._update_component_health('media_perception', ComponentStatus.FAILED, str(e))
    
    async def _initialize_intent_compiler(self):
        """Initialize the intent compiler."""
        try:
            compiler_config = {
                'enable_ml_classification': False,  # Disable to speed up initialization
                'enable_entity_extraction': True,
                'cache_compiled_intents': True
            }
            
            self.intent_compiler = IntentCompiler(compiler_config)
            self._update_component_health('intent_compiler', ComponentStatus.HEALTHY)
            
        except Exception as e:
            self._update_component_health('intent_compiler', ComponentStatus.FAILED, str(e))
            raise
    
    def _setup_component_callbacks(self):
        """Setup callbacks between components."""
        if self.intent_compiler and self.navigation_engine:
            self.intent_compiler.set_navigation_callback(self._navigation_callback)
        
        if self.intent_compiler and self.media_perception:
            self.intent_compiler.set_media_analysis_callback(self._media_analysis_callback)
        
        if self.intent_compiler and self.action_validator:
            self.intent_compiler.set_action_validation_callback(self._action_validation_callback)
    
    async def _start_background_tasks(self):
        """Start background maintenance tasks."""
        tasks = [
            self._execution_processor(),
            self._health_monitor(),
            self._performance_monitor(),
            self._cleanup_task()
        ]
        
        for task_func in tasks:
            task = asyncio.create_task(task_func)
            self._background_tasks.append(task)
    
    async def _execution_processor(self):
        """Process execution queue."""
        while not self._shutdown_event.is_set():
            try:
                # Get next execution context
                context = await asyncio.wait_for(
                    self._execution_queue.get(), 
                    timeout=1.0
                )
                
                # Process the intent
                await self._process_intent_execution(context)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Execution processor error: {e}")
                await asyncio.sleep(1)
    
    async def _health_monitor(self):
        """Monitor component health."""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_health_check()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _performance_monitor(self):
        """Monitor system performance."""
        while not self._shutdown_event.is_set():
            try:
                await self._update_performance_metrics()
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                self.logger.error(f"Performance monitor error: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_task(self):
        """Cleanup expired resources."""
        while not self._shutdown_event.is_set():
            try:
                await self._cleanup_expired_resources()
                await asyncio.sleep(self.config.cleanup_interval)
                
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")
                await asyncio.sleep(60)
    
    async def execute_intent(self, intent_text: str, 
                           session_id: Optional[str] = None,
                           user_id: Optional[str] = None,
                           priority: ExecutionPriority = ExecutionPriority.MEDIUM,
                           timeout: float = None) -> ExecutionResult:
        """
        Execute a natural language intent.
        
        Args:
            intent_text: Natural language description of the intent
            session_id: Optional existing session ID
            user_id: Optional user identifier
            priority: Execution priority
            timeout: Execution timeout in seconds
            
        Returns:
            ExecutionResult with execution details
        """
        start_time = time.time()
        
        try:
            # Create or get session
            if session_id:
                session = await self.session_manager.get_session(session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")
            else:
                session = await self.session_manager.create_session(
                    name=f"Intent: {intent_text[:50]}...",
                    user_id=user_id
                )
                session_id = session.id
            
            # Compile intent
            intent = await self.intent_compiler.compile_intent(intent_text)
            
            # Create execution context
            context = ExecutionContext(
                session_id=session_id,
                intent_id=intent.id,
                user_id=user_id,
                priority=priority,
                timeout=timeout or self.config.default_timeout,
                validate_actions=self.config.enable_action_validation,
                analyze_media=self.config.enable_media_perception
            )
            
            # Queue for execution
            await self._execution_queue.put(context)
            
            # Wait for completion (in a real implementation, this would be async)
            result = await self._wait_for_execution_completion(context)
            
            # Update metrics
            execution_time = time.time() - start_time
            self._performance_metrics['total_intents'] += 1
            
            if result.success:
                self._performance_metrics['successful_intents'] += 1
            else:
                self._performance_metrics['failed_intents'] += 1
            
            # Update average execution time
            total = self._performance_metrics['total_intents']
            current_avg = self._performance_metrics['average_execution_time']
            self._performance_metrics['average_execution_time'] = (
                (current_avg * (total - 1) + execution_time) / total
            )
            
            # Update Prometheus metrics
            if hasattr(self, '_metrics'):
                self._metrics['intents_total'].labels(
                    status='success' if result.success else 'failed',
                    intent_type=intent.intent_type.value
                ).inc()
                
                self._metrics['execution_time'].labels(
                    intent_type=intent.intent_type.value
                ).observe(execution_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Intent execution failed: {e}")
            self._performance_metrics['failed_intents'] += 1
            
            return ExecutionResult(
                intent_id=intent.id if 'intent' in locals() else str(uuid.uuid4()),
                session_id=session_id or "unknown",
                success=False,
                execution_time=time.time() - start_time,
                actions_performed=0,
                error_message=str(e)
            )
    
    async def _process_intent_execution(self, context: ExecutionContext):
        """Process intent execution with full coordination."""
        try:
            self._active_executions[context.intent_id] = context
            
            # Get session and intent
            session = await self.session_manager.get_session(context.session_id)
            intent = self.intent_compiler.get_active_intents().get(context.intent_id)
            
            if not session or not intent:
                raise ValueError("Session or intent not found")
            
            # Create browser context
            browser_context = await self._create_browser_context(session)
            
            # Execute goals sequentially
            validation_results = []
            media_analyses = []
            screenshots = []
            actions_performed = 0
            
            for goal in intent.goals:
                for sequence in goal.action_sequences:
                    for action in sequence.actions:
                        try:
                            # Execute action
                            await self._execute_action(action, browser_context, session)
                            actions_performed += 1
                            
                            # Validate action if enabled
                            if context.validate_actions and self.action_validator:
                                validation_result = await self.action_validator.validate_action(
                                    action, browser_context
                                )
                                validation_results.append(validation_result)
                            
                            # Analyze media if enabled
                            if context.analyze_media and self.media_perception:
                                page = browser_context.pages[0] if browser_context.pages else None
                                if page:
                                    screenshot = await page.screenshot()
                                    analysis = await self.media_perception.analyze_media(
                                        screenshot, MediaType.SCREENSHOT
                                    )
                                    media_analyses.append(analysis)
                            
                            # Take screenshot if enabled
                            if context.save_screenshots:
                                screenshot_path = await self._save_screenshot(browser_context, action.id)
                                screenshots.append(screenshot_path)
                            
                        except Exception as e:
                            self.logger.error(f"Action execution failed: {e}")
                            if not sequence.continue_on_error:
                                raise
            
            # Update session state
            if browser_context.pages:
                page = browser_context.pages[0]
                await self._update_session_browser_state(session, page)
            
            # Create successful result
            result = ExecutionResult(
                intent_id=context.intent_id,
                session_id=context.session_id,
                success=True,
                execution_time=time.time() - context.metadata.get('start_time', time.time()),
                actions_performed=actions_performed,
                validation_results=validation_results,
                media_analyses=media_analyses,
                screenshots=screenshots
            )
            
            # Store result
            context.metadata['result'] = result
            
            # Update intent status
            self.intent_compiler.update_intent_status(context.intent_id, ExecutionStatus.COMPLETED)
            
        except Exception as e:
            self.logger.error(f"Intent execution failed: {e}")
            
            # Create failed result
            result = ExecutionResult(
                intent_id=context.intent_id,
                session_id=context.session_id,
                success=False,
                execution_time=time.time() - context.metadata.get('start_time', time.time()),
                actions_performed=actions_performed,
                error_message=str(e)
            )
            
            context.metadata['result'] = result
            self.intent_compiler.update_intent_status(context.intent_id, ExecutionStatus.FAILED)
        
        finally:
            # Clean up
            if context.intent_id in self._active_executions:
                del self._active_executions[context.intent_id]
    
    async def _create_browser_context(self, session: BrowsingSession) -> BrowserContext:
        """Create browser context for session."""
        if session.id not in self._browser_contexts:
            # Get browser
            browser = self._browsers.get('chromium') or self._browsers.get('firefox')
            if not browser:
                raise RuntimeError("No browser available")
            
            # Create context
            context = await browser.new_context(
                viewport=session.browser_state.viewport,
                user_agent=session.browser_state.user_agent,
                locale=session.browser_state.language,
                timezone_id=session.browser_state.timezone
            )
            
            # Restore cookies
            if session.browser_state.cookies:
                cookies = []
                for cookie in session.browser_state.cookies:
                    cookies.append({
                        'name': cookie.name,
                        'value': cookie.value,
                        'domain': cookie.domain,
                        'path': cookie.path,
                        'secure': cookie.secure,
                        'httpOnly': cookie.http_only,
                        'sameSite': cookie.same_site
                    })
                await context.add_cookies(cookies)
            
            # Create page
            page = await context.new_page()
            
            # Navigate to current URL
            if session.browser_state.url != "about:blank":
                await page.goto(session.browser_state.url)
            
            self._browser_contexts[session.id] = context
        
        return self._browser_contexts[session.id]
    
    async def _execute_action(self, action, browser_context: BrowserContext, session: BrowsingSession):
        """Execute individual action."""
        if not self.navigation_engine:
            raise RuntimeError("Navigation engine not available")
        
        page = browser_context.pages[0] if browser_context.pages else None
        if not page:
            page = await browser_context.new_page()
        
        # Execute action using navigation engine
        await self.navigation_engine.execute_action(action, page)
    
    async def _update_session_browser_state(self, session: BrowsingSession, page: Page):
        """Update session browser state from page."""
        # Get current state
        url = page.url
        title = await page.title()
        
        # Update browser state
        session.browser_state.url = url
        session.browser_state.title = title
        
        # Get cookies
        cookies = await page.context.cookies()
        session.browser_state.cookies = []
        for cookie in cookies:
            session.browser_state.cookies.append({
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie['domain'],
                'path': cookie['path'],
                'secure': cookie.get('secure', False),
                'httpOnly': cookie.get('httpOnly', False),
                'sameSite': cookie.get('sameSite', 'Lax')
            })
        
        # Update session
        await self.session_manager.update_session_state(session.id, session.browser_state)
    
    async def _save_screenshot(self, browser_context: BrowserContext, action_id: str) -> str:
        """Save screenshot for action."""
        page = browser_context.pages[0] if browser_context.pages else None
        if not page:
            return ""
        
        screenshot_dir = os.path.join(self.config.storage_dir, 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        
        screenshot_path = os.path.join(screenshot_dir, f"{action_id}.png")
        await page.screenshot(path=screenshot_path)
        
        return screenshot_path
    
    async def _wait_for_execution_completion(self, context: ExecutionContext) -> ExecutionResult:
        """Wait for execution completion."""
        timeout = context.timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if context.intent_id not in self._active_executions:
                # Execution completed
                return context.metadata.get('result')
            
            await asyncio.sleep(0.1)
        
        # Timeout
        return ExecutionResult(
            intent_id=context.intent_id,
            session_id=context.session_id,
            success=False,
            execution_time=timeout,
            actions_performed=0,
            error_message="Execution timeout"
        )
    
    async def _navigation_callback(self, action, result):
        """Callback for navigation actions."""
        self.logger.debug(f"Navigation action completed: {action.type.value}")
    
    async def _media_analysis_callback(self, media_data, analysis):
        """Callback for media analysis."""
        self.logger.debug(f"Media analysis completed: {analysis.media_type.value}")
    
    async def _action_validation_callback(self, action, validation_result):
        """Callback for action validation."""
        self.logger.debug(f"Action validation completed: {validation_result.success}")
    
    def _update_component_health(self, component: str, status: ComponentStatus, error: str = None):
        """Update component health status."""
        health = self._component_health.get(component, ComponentHealth(
            name=component,
            status=ComponentStatus.INITIALIZING,
            last_check=datetime.now()
        ))
        
        health.status = status
        health.last_check = datetime.now()
        
        if error:
            health.error_count += 1
            health.last_error = error
        
        self._component_health[component] = health
        
        # Update Prometheus metrics
        if hasattr(self, '_metrics'):
            self._metrics['component_health'].labels(component=component).state(status.value)
    
    async def _perform_health_check(self):
        """Perform comprehensive health check."""
        try:
            # Check each component
            for component_name, health in self._component_health.items():
                if health.status == ComponentStatus.FAILED:
                    self.logger.warning(f"Component {component_name} is in failed state")
                elif health.status == ComponentStatus.DEGRADED:
                    self.logger.warning(f"Component {component_name} is degraded")
            
            # Check system resources
            await self._check_system_resources()
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
    
    async def _check_system_resources(self):
        """Check system resource usage."""
        try:
            import psutil
            
            # Check memory usage
            memory_info = psutil.virtual_memory()
            memory_usage_mb = memory_info.used / (1024 * 1024)
            
            if memory_usage_mb > self.config.max_memory_usage:
                self.logger.warning(f"High memory usage: {memory_usage_mb:.1f}MB")
            
            # Check CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage > self.config.max_cpu_usage:
                self.logger.warning(f"High CPU usage: {cpu_usage:.1f}%")
            
            # Update metrics
            self._performance_metrics['memory_usage'] = memory_usage_mb
            self._performance_metrics['cpu_usage'] = cpu_usage
            
        except ImportError:
            self.logger.debug("psutil not available, skipping resource monitoring")
        except Exception as e:
            self.logger.error(f"Resource check failed: {e}")
    
    async def _update_performance_metrics(self):
        """Update performance metrics."""
        try:
            # Update session metrics
            if self.session_manager:
                stats = self.session_manager.get_performance_stats()
                self._performance_metrics['total_sessions'] = stats.get('total_sessions', 0)
                self._performance_metrics['active_sessions'] = stats.get('active_sessions', 0)
                
                # Update Prometheus metrics
                if hasattr(self, '_metrics'):
                    self._metrics['active_sessions'].set(stats.get('active_sessions', 0))
            
            # Update component metrics
            for component_name, health in self._component_health.items():
                if hasattr(self, '_metrics'):
                    self._metrics['component_health'].labels(component=component_name).state(health.status.value)
            
        except Exception as e:
            self.logger.error(f"Performance metrics update failed: {e}")
    
    async def _cleanup_expired_resources(self):
        """Clean up expired resources."""
        try:
            # Clean up browser contexts
            expired_contexts = []
            for session_id, context in self._browser_contexts.items():
                try:
                    # Check if session still exists
                    session = await self.session_manager.get_session(session_id)
                    if not session or session.status != SessionStatus.ACTIVE:
                        expired_contexts.append(session_id)
                except:
                    expired_contexts.append(session_id)
            
            for session_id in expired_contexts:
                try:
                    context = self._browser_contexts.pop(session_id)
                    await context.close()
                    self.logger.debug(f"Cleaned up browser context for session {session_id}")
                except Exception as e:
                    self.logger.error(f"Failed to clean up context {session_id}: {e}")
            
            # Clean up completed executions
            current_time = time.time()
            expired_executions = []
            
            for intent_id, context in self._active_executions.items():
                if current_time - context.metadata.get('start_time', current_time) > context.timeout:
                    expired_executions.append(intent_id)
            
            for intent_id in expired_executions:
                del self._active_executions[intent_id]
                self.logger.debug(f"Cleaned up expired execution {intent_id}")
            
        except Exception as e:
            self.logger.error(f"Resource cleanup failed: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'uptime': time.time() - self._start_time,
            'mode': self.config.mode.value,
            'component_health': {
                name: {
                    'status': health.status.value,
                    'last_check': health.last_check.isoformat(),
                    'error_count': health.error_count,
                    'last_error': health.last_error
                }
                for name, health in self._component_health.items()
            },
            'performance_metrics': self._performance_metrics.copy(),
            'active_executions': len(self._active_executions),
            'queue_size': self._execution_queue.qsize(),
            'browser_contexts': len(self._browser_contexts)
        }
    
    async def get_session_list(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of active sessions."""
        if not self.session_manager:
            return []
        
        sessions = await self.session_manager.list_sessions(user_id=user_id)
        return [
            {
                'id': session.id,
                'name': session.name,
                'type': session.session_type.value,
                'status': session.status.value,
                'created_at': session.created_at.isoformat(),
                'last_accessed': session.last_accessed.isoformat(),
                'page_views': session.page_views,
                'actions_performed': session.actions_performed,
                'current_url': session.browser_state.url,
                'current_title': session.browser_state.title
            }
            for session in sessions
        ]
    
    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a specific session."""
        if not self.session_manager:
            return False
        
        # Close browser context
        if session_id in self._browser_contexts:
            try:
                context = self._browser_contexts.pop(session_id)
                await context.close()
            except Exception as e:
                self.logger.error(f"Failed to close browser context: {e}")
        
        # Terminate session
        return await self.session_manager.terminate_session(session_id)
    
    async def shutdown(self):
        """Shutdown the Spectra system gracefully."""
        self.logger.info("Initiating Spectra shutdown...")
        
        try:
            # Set shutdown event
            self._shutdown_event.set()
            
            # Cancel background tasks
            for task in self._background_tasks:
                task.cancel()
            
            # Wait for background tasks to complete
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
            # Close browser contexts
            for context in self._browser_contexts.values():
                try:
                    await context.close()
                except Exception as e:
                    self.logger.error(f"Failed to close browser context: {e}")
            
            # Close browsers
            for browser in self._browsers.values():
                try:
                    await browser.close()
                except Exception as e:
                    self.logger.error(f"Failed to close browser: {e}")
            
            # Close playwright
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception as e:
                    self.logger.error(f"Failed to stop playwright: {e}")
            
            # Shutdown components
            if self.session_manager:
                # Session manager cleanup is handled by its own destructor
                pass
            
            self.logger.info("Spectra shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Shutdown failed: {e}")
    
    def __del__(self):
        """Cleanup on destruction."""
        if hasattr(self, '_shutdown_event') and not self._shutdown_event.is_set():
            # Force shutdown if not already done
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.shutdown())
            except:
                pass


# Configuration loading utility
def load_config(config_path: str) -> SpectraConfig:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Convert dict to SpectraConfig
        return SpectraConfig(**config_data)
        
    except FileNotFoundError:
        logging.warning(f"Config file {config_path} not found, using defaults")
        return SpectraConfig()
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return SpectraConfig()


# Main entry point
async def main():
    """Main entry point for Spectra."""
    # Load configuration
    config = load_config('spectra_config.yaml')
    
    # Create and initialize Spectra
    spectra = SpectraCore(config)
    
    try:
        await spectra.initialize()
        
        # Example usage
        result = await spectra.execute_intent(
            "Navigate to https://example.com and take a screenshot",
            priority=ExecutionPriority.HIGH
        )
        
        print(f"Execution result: {result.success}")
        print(f"Actions performed: {result.actions_performed}")
        print(f"Execution time: {result.execution_time:.2f}s")
        
        # Get system status
        status = await spectra.get_system_status()
        print(f"System status: {status}")
        
    except KeyboardInterrupt:
        print("Received interrupt signal")
    except Exception as e:
        print(f"Spectra error: {e}")
        traceback.print_exc()
    finally:
        await spectra.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
