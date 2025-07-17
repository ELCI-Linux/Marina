"""
Intent Compilation Engine for Marina's Autonomous Browser System (Spectra)

This module processes high-level user intents and compiles them into executable action sequences
for autonomous web browsing, including goal decomposition, action planning, and execution orchestration.
"""

import json
import logging
import time
import re
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime, timedelta
import uuid

# Core dependencies
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.corpus import stopwords

# Optional NLP dependencies
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class IntentType(Enum):
    """Types of user intents."""
    NAVIGATE = "navigate"
    SEARCH = "search"
    EXTRACT = "extract"
    INTERACT = "interact"
    MONITOR = "monitor"
    PURCHASE = "purchase"
    AUTHENTICATE = "authenticate"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    FORM_FILL = "form_fill"
    SOCIAL = "social"
    BOOKING = "booking"
    COMPARISON = "comparison"
    AUTOMATION = "automation"
    UNKNOWN = "unknown"


class ActionType(Enum):
    """Types of browser actions."""
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    NAVIGATE_TO = "navigate_to"
    WAIT = "wait"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_LINKS = "extract_links"
    EXTRACT_IMAGES = "extract_images"
    TAKE_SCREENSHOT = "take_screenshot"
    UPLOAD_FILE = "upload_file"
    DOWNLOAD_FILE = "download_file"
    PRESS_KEY = "press_key"
    HOVER = "hover"
    DRAG_DROP = "drag_drop"
    SWITCH_TAB = "switch_tab"
    CLOSE_TAB = "close_tab"
    REFRESH = "refresh"
    BACK = "back"
    FORWARD = "forward"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    CUSTOM = "custom"


class Priority(Enum):
    """Action priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExecutionStatus(Enum):
    """Execution status of actions and intents."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class Entity:
    """Named entity extracted from intent."""
    text: str
    label: str
    confidence: float
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionParameter:
    """Parameter for an action."""
    name: str
    value: Any
    type: str
    required: bool = True
    description: str = ""


@dataclass
class Condition:
    """Condition for conditional actions."""
    type: str  # "element_exists", "text_contains", "url_matches", etc.
    target: str
    operator: str  # "equals", "contains", "matches", etc.
    value: Any
    timeout: float = 10.0


@dataclass
class Action:
    """Individual browser action."""
    id: str
    type: ActionType
    parameters: List[ActionParameter]
    conditions: List[Condition] = field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: ExecutionStatus = ExecutionStatus.PENDING
    error_message: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class ActionSequence:
    """Sequence of actions to execute."""
    id: str
    actions: List[Action]
    parallel_execution: bool = False
    sequential_execution: bool = True
    max_parallel_actions: int = 3
    total_timeout: float = 300.0
    continue_on_error: bool = False
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Goal:
    """High-level goal decomposed from intent."""
    id: str
    description: str
    priority: Priority
    required_entities: List[str]
    action_sequences: List[ActionSequence]
    success_criteria: List[str]
    failure_criteria: List[str]
    estimated_duration: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Intent:
    """Compiled user intent."""
    id: str
    original_text: str
    intent_type: IntentType
    confidence: float
    entities: List[Entity]
    goals: List[Goal]
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    priority: Priority = Priority.MEDIUM
    estimated_duration: float = 0.0
    status: ExecutionStatus = ExecutionStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntentContext:
    """Context for intent processing."""
    user_profile: Dict[str, Any] = field(default_factory=dict)
    session_history: List[Dict[str, Any]] = field(default_factory=list)
    current_url: Optional[str] = None
    current_page_content: Optional[str] = None
    available_elements: List[Dict[str, Any]] = field(default_factory=list)
    browser_state: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)


class IntentCompiler:
    """
    Advanced intent compilation engine for autonomous browsing.
    Processes natural language intents and compiles them into executable action sequences.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize NLP components
        self._initialize_nlp()
        
        # Intent patterns and rules
        self._load_intent_patterns()
        self._load_action_templates()
        
        # Execution context
        self._active_intents: Dict[str, Intent] = {}
        self._execution_history: List[Dict[str, Any]] = []
        self._context: IntentContext = IntentContext()
        
        # Performance tracking
        self._performance_stats = {
            'total_intents': 0,
            'successful_compilations': 0,
            'failed_compilations': 0,
            'average_compilation_time': 0.0,
            'average_execution_time': 0.0
        }
        
        # Callbacks for external integration
        self._navigation_callback: Optional[Callable] = None
        self._media_analysis_callback: Optional[Callable] = None
        self._action_validation_callback: Optional[Callable] = None
    
    def _initialize_nlp(self):
        """Initialize NLP processing components."""
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            nltk.download('maxent_ne_chunker', quiet=True)
            nltk.download('words', quiet=True)
            nltk.download('stopwords', quiet=True)
            
            self.stopwords = set(stopwords.words('english'))
            
            # Initialize spaCy if available
            if SPACY_AVAILABLE:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    self.logger.info("spaCy model loaded successfully")
                except OSError:
                    self.logger.warning("spaCy model not found, using NLTK fallback")
                    self.nlp = None
            else:
                self.nlp = None
            
            # Initialize transformers if available and requested
            if TRANSFORMERS_AVAILABLE and self.config.get('enable_ml_classification', False):
                try:
                    # Use a lighter model for faster initialization
                    self.intent_classifier = pipeline(
                        "text-classification",
                        model="distilbert-base-uncased-finetuned-sst-2-english",
                        return_all_scores=True
                    )
                    self.logger.info("Intent classification model loaded (DistilBERT)")
                except Exception as e:
                    self.logger.warning(f"Failed to load intent classifier: {e}")
                    self.intent_classifier = None
            else:
                self.intent_classifier = None
                if not TRANSFORMERS_AVAILABLE:
                    self.logger.info("Transformers not available, using pattern-based classification")
                else:
                    self.logger.info("ML classification disabled, using pattern-based classification")
                
        except Exception as e:
            self.logger.error(f"NLP initialization failed: {e}")
    
    def _load_intent_patterns(self):
        """Load intent recognition patterns and rules."""
        self.intent_patterns = {
            IntentType.NAVIGATE: [
                r"go to\s+(.+)",
                r"navigate to\s+(.+)",
                r"visit\s+(.+)",
                r"open\s+(.+)",
                r"load\s+(.+)",
                r"browse to\s+(.+)"
            ],
            IntentType.SEARCH: [
                r"search for\s+(.+)",
                r"find\s+(.+)",
                r"look for\s+(.+)",
                r"search\s+(.+)",
                r"query\s+(.+)",
                r"locate\s+(.+)"
            ],
            IntentType.EXTRACT: [
                r"extract\s+(.+)",
                r"get\s+(.+)",
                r"scrape\s+(.+)",
                r"collect\s+(.+)",
                r"gather\s+(.+)",
                r"harvest\s+(.+)"
            ],
            IntentType.INTERACT: [
                r"click\s+(.+)",
                r"press\s+(.+)",
                r"tap\s+(.+)",
                r"select\s+(.+)",
                r"choose\s+(.+)",
                r"activate\s+(.+)"
            ],
            IntentType.FORM_FILL: [
                r"fill\s+(.+)",
                r"enter\s+(.+)",
                r"type\s+(.+)",
                r"input\s+(.+)",
                r"submit\s+(.+)",
                r"complete\s+(.+)"
            ],
            IntentType.PURCHASE: [
                r"buy\s+(.+)",
                r"purchase\s+(.+)",
                r"order\s+(.+)",
                r"checkout\s+(.+)",
                r"add to cart\s+(.+)",
                r"pay for\s+(.+)"
            ],
            IntentType.AUTHENTICATE: [
                r"login\s+(.+)",
                r"log in\s+(.+)",
                r"sign in\s+(.+)",
                r"authenticate\s+(.+)",
                r"login to\s+(.+)",
                r"access\s+(.+)"
            ],
            IntentType.MONITOR: [
                r"monitor\s+(.+)",
                r"watch\s+(.+)",
                r"track\s+(.+)",
                r"observe\s+(.+)",
                r"check\s+(.+)",
                r"wait for\s+(.+)"
            ],
            IntentType.BOOKING: [
                r"book\s+(.+)",
                r"reserve\s+(.+)",
                r"schedule\s+(.+)",
                r"make appointment\s+(.+)",
                r"reserve\s+(.+)",
                r"book ticket\s+(.+)"
            ]
        }
        
        # Entity patterns
        self.entity_patterns = {
            'URL': r'https?://[^\s]+',
            'EMAIL': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'PHONE': r'[\+]?[1-9]?[\d\s\-\(\)]{8,15}',
            'DATE': r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
            'TIME': r'\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?',
            'PRICE': r'\$\d+(?:\.\d{2})?',
            'QUANTITY': r'\d+(?:\s*(?:items?|pieces?|units?))?'
        }
    
    def _load_action_templates(self):
        """Load action templates for different intent types."""
        self.action_templates = {
            IntentType.NAVIGATE: [
                {
                    'type': ActionType.NAVIGATE_TO,
                    'parameters': [
                        {'name': 'url', 'type': 'string', 'required': True}
                    ],
                    'description': 'Navigate to specified URL'
                }
            ],
            IntentType.SEARCH: [
                {
                    'type': ActionType.CLICK,
                    'parameters': [
                        {'name': 'selector', 'type': 'string', 'required': True, 'value': 'input[type="search"], input[name*="search"], .search-box'}
                    ],
                    'description': 'Click search input field'
                },
                {
                    'type': ActionType.TYPE,
                    'parameters': [
                        {'name': 'text', 'type': 'string', 'required': True},
                        {'name': 'selector', 'type': 'string', 'required': True, 'value': 'input[type="search"], input[name*="search"], .search-box'}
                    ],
                    'description': 'Type search query'
                },
                {
                    'type': ActionType.PRESS_KEY,
                    'parameters': [
                        {'name': 'key', 'type': 'string', 'required': True, 'value': 'Enter'}
                    ],
                    'description': 'Submit search'
                }
            ],
            IntentType.AUTHENTICATE: [
                {
                    'type': ActionType.CLICK,
                    'parameters': [
                        {'name': 'selector', 'type': 'string', 'required': True, 'value': 'input[type="email"], input[name*="email"], input[name*="username"]'}
                    ],
                    'description': 'Click username/email field'
                },
                {
                    'type': ActionType.TYPE,
                    'parameters': [
                        {'name': 'text', 'type': 'string', 'required': True},
                        {'name': 'selector', 'type': 'string', 'required': True, 'value': 'input[type="email"], input[name*="email"], input[name*="username"]'}
                    ],
                    'description': 'Enter username/email'
                },
                {
                    'type': ActionType.CLICK,
                    'parameters': [
                        {'name': 'selector', 'type': 'string', 'required': True, 'value': 'input[type="password"], input[name*="password"]'}
                    ],
                    'description': 'Click password field'
                },
                {
                    'type': ActionType.TYPE,
                    'parameters': [
                        {'name': 'text', 'type': 'string', 'required': True},
                        {'name': 'selector', 'type': 'string', 'required': True, 'value': 'input[type="password"], input[name*="password"]'}
                    ],
                    'description': 'Enter password'
                },
                {
                    'type': ActionType.CLICK,
                    'parameters': [
                        {'name': 'selector', 'type': 'string', 'required': True, 'value': 'button[type="submit"], input[type="submit"], .login-button, .signin-button'}
                    ],
                    'description': 'Click login button'
                }
            ],
            IntentType.EXTRACT: [
                {
                    'type': ActionType.EXTRACT_TEXT,
                    'parameters': [
                        {'name': 'selector', 'type': 'string', 'required': False, 'value': 'body'},
                        {'name': 'attribute', 'type': 'string', 'required': False, 'value': 'textContent'}
                    ],
                    'description': 'Extract text content'
                }
            ],
            IntentType.PURCHASE: [
                {
                    'type': ActionType.CLICK,
                    'parameters': [
                        {'name': 'selector', 'type': 'string', 'required': True, 'value': '.add-to-cart, .buy-now, .purchase-button'}
                    ],
                    'description': 'Add to cart or purchase'
                },
                {
                    'type': ActionType.WAIT,
                    'parameters': [
                        {'name': 'duration', 'type': 'number', 'required': True, 'value': 2.0}
                    ],
                    'description': 'Wait for cart update'
                },
                {
                    'type': ActionType.CLICK,
                    'parameters': [
                        {'name': 'selector', 'type': 'string', 'required': True, 'value': '.checkout, .proceed-to-checkout'}
                    ],
                    'description': 'Proceed to checkout'
                }
            ]
        }
    
    async def compile_intent(self, intent_text: str, context: Optional[IntentContext] = None) -> Intent:
        """
        Compile a natural language intent into an executable Intent object.
        
        Args:
            intent_text: Natural language description of the intent
            context: Current browsing context
            
        Returns:
            Compiled Intent object
        """
        start_time = time.time()
        
        try:
            # Update context
            if context:
                self._context = context
            
            # Create unique intent ID
            intent_id = str(uuid.uuid4())
            
            # Step 1: Preprocess the intent text
            processed_text = self._preprocess_text(intent_text)
            
            # Step 2: Classify intent type
            intent_type, confidence = await self._classify_intent(processed_text)
            
            # Step 3: Extract entities
            entities = await self._extract_entities(processed_text)
            
            # Step 4: Decompose into goals
            goals = await self._decompose_goals(intent_type, entities, processed_text)
            
            # Step 5: Create action sequences for each goal
            for goal in goals:
                action_sequences = await self._create_action_sequences(goal, intent_type, entities)
                goal.action_sequences = action_sequences
            
            # Step 6: Estimate execution time
            estimated_duration = self._estimate_execution_time(goals)
            
            # Create the compiled intent
            intent = Intent(
                id=intent_id,
                original_text=intent_text,
                intent_type=intent_type,
                confidence=confidence,
                entities=entities,
                goals=goals,
                context=self._context.__dict__.copy(),
                estimated_duration=estimated_duration,
                priority=self._determine_priority(intent_type, entities)
            )
            
            # Track performance
            compilation_time = time.time() - start_time
            self._update_performance_stats(compilation_time, success=True)
            
            # Store active intent
            self._active_intents[intent_id] = intent
            
            self.logger.info(f"Successfully compiled intent: {intent_text[:50]}...")
            return intent
            
        except Exception as e:
            self.logger.error(f"Intent compilation failed: {e}")
            self._update_performance_stats(time.time() - start_time, success=False)
            
            # Return a fallback intent
            return Intent(
                id=str(uuid.uuid4()),
                original_text=intent_text,
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                entities=[],
                goals=[],
                status=ExecutionStatus.FAILED,
                metadata={'error': str(e)}
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess intent text for analysis."""
        # Basic text cleaning
        text = text.strip().lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize punctuation
        text = re.sub(r'[^\w\s\-\.\,\:\;\!\?\@\#\$\%\&\*\(\)]', '', text)
        
        return text
    
    async def _classify_intent(self, text: str) -> Tuple[IntentType, float]:
        """Classify the intent type from processed text."""
        # Try pattern matching first
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent_type, 0.9
        
        # Try ML classification if available
        if self.intent_classifier:
            try:
                # Create candidate labels
                candidate_labels = [intent_type.value for intent_type in IntentType if intent_type != IntentType.UNKNOWN]
                
                results = self.intent_classifier(text, candidate_labels)
                
                if results and len(results) > 0:
                    best_match = max(results, key=lambda x: x['score'])
                    intent_type = IntentType(best_match['label'])
                    return intent_type, best_match['score']
                    
            except Exception as e:
                self.logger.error(f"ML intent classification failed: {e}")
        
        # Try spaCy-based classification
        if self.nlp:
            try:
                doc = self.nlp(text)
                
                # Extract key verbs and nouns
                key_verbs = [token.lemma_ for token in doc if token.pos_ == 'VERB']
                key_nouns = [token.lemma_ for token in doc if token.pos_ == 'NOUN']
                
                # Simple rule-based classification
                if any(verb in ['go', 'navigate', 'visit', 'browse'] for verb in key_verbs):
                    return IntentType.NAVIGATE, 0.8
                elif any(verb in ['search', 'find', 'look'] for verb in key_verbs):
                    return IntentType.SEARCH, 0.8
                elif any(verb in ['click', 'press', 'tap', 'select'] for verb in key_verbs):
                    return IntentType.INTERACT, 0.8
                elif any(verb in ['extract', 'get', 'scrape'] for verb in key_verbs):
                    return IntentType.EXTRACT, 0.8
                elif any(verb in ['login', 'authenticate', 'signin'] for verb in key_verbs):
                    return IntentType.AUTHENTICATE, 0.8
                elif any(verb in ['buy', 'purchase', 'order'] for verb in key_verbs):
                    return IntentType.PURCHASE, 0.8
                elif any(verb in ['fill', 'enter', 'type', 'submit'] for verb in key_verbs):
                    return IntentType.FORM_FILL, 0.8
                elif any(verb in ['monitor', 'watch', 'track'] for verb in key_verbs):
                    return IntentType.MONITOR, 0.8
                elif any(verb in ['book', 'reserve', 'schedule'] for verb in key_verbs):
                    return IntentType.BOOKING, 0.8
                    
            except Exception as e:
                self.logger.error(f"spaCy classification failed: {e}")
        
        # Fallback to NLTK-based classification
        try:
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            # Extract verbs
            verbs = [word for word, pos in pos_tags if pos.startswith('VB')]
            
            # Simple verb-based classification
            if any(verb in ['go', 'navigate', 'visit', 'browse'] for verb in verbs):
                return IntentType.NAVIGATE, 0.7
            elif any(verb in ['search', 'find', 'look'] for verb in verbs):
                return IntentType.SEARCH, 0.7
                
        except Exception as e:
            self.logger.error(f"NLTK classification failed: {e}")
        
        return IntentType.UNKNOWN, 0.0
    
    async def _extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities from the text."""
        entities = []
        
        # Extract using regex patterns
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = Entity(
                    text=match.group(),
                    label=entity_type,
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                entities.append(entity)
        
        # Extract using spaCy if available
        if self.nlp:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    entity = Entity(
                        text=ent.text,
                        label=ent.label_,
                        confidence=0.8,
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                        metadata={'spacy_label': ent.label_}
                    )
                    entities.append(entity)
            except Exception as e:
                self.logger.error(f"spaCy entity extraction failed: {e}")
        
        # Extract using NLTK as fallback
        try:
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            chunks = ne_chunk(pos_tags)
            
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    entity_text = ' '.join([token for token, pos in chunk])
                    entity = Entity(
                        text=entity_text,
                        label=chunk.label(),
                        confidence=0.7,
                        start_pos=0,  # NLTK doesn't provide character positions
                        end_pos=len(entity_text),
                        metadata={'nltk_label': chunk.label()}
                    )
                    entities.append(entity)
        except Exception as e:
            self.logger.error(f"NLTK entity extraction failed: {e}")
        
        return entities
    
    async def _decompose_goals(self, intent_type: IntentType, entities: List[Entity], text: str) -> List[Goal]:
        """Decompose intent into actionable goals."""
        goals = []
        
        # Create primary goal based on intent type
        primary_goal = Goal(
            id=str(uuid.uuid4()),
            description=f"Execute {intent_type.value} intent",
            priority=Priority.HIGH,
            required_entities=[entity.label for entity in entities],
            action_sequences=[],
            success_criteria=[
                f"Intent type {intent_type.value} completed successfully",
                "No critical errors occurred"
            ],
            failure_criteria=[
                "Action sequence failed",
                "Required elements not found",
                "Timeout exceeded"
            ]
        )
        
        goals.append(primary_goal)
        
        # Add secondary goals based on complexity
        if intent_type == IntentType.PURCHASE:
            # Purchase intents often require multiple steps
            secondary_goals = [
                Goal(
                    id=str(uuid.uuid4()),
                    description="Navigate to product page",
                    priority=Priority.HIGH,
                    required_entities=[],
                    action_sequences=[],
                    success_criteria=["Product page loaded"],
                    failure_criteria=["Product not found"]
                ),
                Goal(
                    id=str(uuid.uuid4()),
                    description="Add item to cart",
                    priority=Priority.HIGH,
                    required_entities=[],
                    action_sequences=[],
                    success_criteria=["Item added to cart"],
                    failure_criteria=["Add to cart failed"]
                ),
                Goal(
                    id=str(uuid.uuid4()),
                    description="Complete checkout process",
                    priority=Priority.CRITICAL,
                    required_entities=["PAYMENT_INFO"],
                    action_sequences=[],
                    success_criteria=["Order placed successfully"],
                    failure_criteria=["Payment failed", "Checkout incomplete"]
                )
            ]
            goals.extend(secondary_goals)
        
        elif intent_type == IntentType.FORM_FILL:
            # Form filling often requires validation
            validation_goal = Goal(
                id=str(uuid.uuid4()),
                description="Validate form submission",
                priority=Priority.MEDIUM,
                required_entities=[],
                action_sequences=[],
                success_criteria=["Form submitted successfully"],
                failure_criteria=["Validation errors", "Submission failed"]
            )
            goals.append(validation_goal)
        
        elif intent_type == IntentType.SEARCH:
            # Search often requires result processing
            result_goal = Goal(
                id=str(uuid.uuid4()),
                description="Process search results",
                priority=Priority.MEDIUM,
                required_entities=[],
                action_sequences=[],
                success_criteria=["Search results loaded"],
                failure_criteria=["No results found", "Search failed"]
            )
            goals.append(result_goal)
        
        return goals
    
    async def _create_action_sequences(self, goal: Goal, intent_type: IntentType, entities: List[Entity]) -> List[ActionSequence]:
        """Create action sequences for a goal."""
        action_sequences = []
        
        # Get action templates for the intent type
        templates = self.action_templates.get(intent_type, [])
        
        if templates:
            # Create actions from templates
            actions = []
            
            for template in templates:
                action = self._create_action_from_template(template, entities)
                actions.append(action)
            
            # Create action sequence
            sequence = ActionSequence(
                id=str(uuid.uuid4()),
                actions=actions,
                sequential_execution=True,
                description=f"Execute {intent_type.value} actions",
                metadata={'intent_type': intent_type.value}
            )
            
            action_sequences.append(sequence)
        
        else:
            # Create generic action sequence
            generic_action = Action(
                id=str(uuid.uuid4()),
                type=ActionType.CUSTOM,
                parameters=[
                    ActionParameter(
                        name='description',
                        value=goal.description,
                        type='string'
                    )
                ],
                description=f"Custom action for {intent_type.value}",
                metadata={'intent_type': intent_type.value}
            )
            
            sequence = ActionSequence(
                id=str(uuid.uuid4()),
                actions=[generic_action],
                description=f"Generic {intent_type.value} sequence"
            )
            
            action_sequences.append(sequence)
        
        return action_sequences
    
    def _create_action_from_template(self, template: Dict[str, Any], entities: List[Entity]) -> Action:
        """Create an action from a template."""
        action_type = ActionType(template['type'])
        
        # Create parameters from template
        parameters = []
        for param_template in template['parameters']:
            param_value = param_template.get('value', '')
            
            # Try to fill parameter from entities
            if param_template['name'] in ['text', 'query', 'search_term']:
                # Use text entities for text parameters
                text_entities = [e for e in entities if e.label in ['PERSON', 'ORG', 'PRODUCT']]
                if text_entities:
                    param_value = text_entities[0].text
            
            elif param_template['name'] == 'url':
                # Use URL entities for URL parameters
                url_entities = [e for e in entities if e.label == 'URL']
                if url_entities:
                    param_value = url_entities[0].text
            
            parameter = ActionParameter(
                name=param_template['name'],
                value=param_value,
                type=param_template['type'],
                required=param_template.get('required', True),
                description=param_template.get('description', '')
            )
            parameters.append(parameter)
        
        return Action(
            id=str(uuid.uuid4()),
            type=action_type,
            parameters=parameters,
            description=template.get('description', f'Execute {action_type.value} action'),
            metadata={'from_template': True}
        )
    
    def _estimate_execution_time(self, goals: List[Goal]) -> float:
        """Estimate total execution time for goals."""
        total_time = 0.0
        
        for goal in goals:
            goal_time = 0.0
            
            for sequence in goal.action_sequences:
                sequence_time = 0.0
                
                for action in sequence.actions:
                    # Base time estimates per action type
                    base_times = {
                        ActionType.CLICK: 1.0,
                        ActionType.TYPE: 2.0,
                        ActionType.NAVIGATE_TO: 5.0,
                        ActionType.WAIT: 3.0,
                        ActionType.SCROLL: 1.5,
                        ActionType.EXTRACT_TEXT: 2.0,
                        ActionType.UPLOAD_FILE: 10.0,
                        ActionType.DOWNLOAD_FILE: 15.0,
                        ActionType.CUSTOM: 5.0
                    }
                    
                    action_time = base_times.get(action.type, 3.0)
                    action_time += action.timeout * 0.1  # Add fraction of timeout
                    
                    sequence_time += action_time
                
                if sequence.parallel_execution:
                    # Parallel execution is faster
                    goal_time += sequence_time / min(len(sequence.actions), sequence.max_parallel_actions)
                else:
                    goal_time += sequence_time
            
            goal.estimated_duration = goal_time
            total_time += goal_time
        
        return total_time
    
    def _determine_priority(self, intent_type: IntentType, entities: List[Entity]) -> Priority:
        """Determine priority based on intent type and entities."""
        # Critical intents
        if intent_type in [IntentType.PURCHASE, IntentType.AUTHENTICATE]:
            return Priority.CRITICAL
        
        # High priority intents
        if intent_type in [IntentType.FORM_FILL, IntentType.UPLOAD, IntentType.DOWNLOAD]:
            return Priority.HIGH
        
        # Medium priority intents
        if intent_type in [IntentType.SEARCH, IntentType.NAVIGATE, IntentType.INTERACT]:
            return Priority.MEDIUM
        
        # Low priority intents
        return Priority.LOW
    
    def _update_performance_stats(self, compilation_time: float, success: bool):
        """Update performance statistics."""
        self._performance_stats['total_intents'] += 1
        
        if success:
            self._performance_stats['successful_compilations'] += 1
        else:
            self._performance_stats['failed_compilations'] += 1
        
        # Update average compilation time
        total = self._performance_stats['total_intents']
        current_avg = self._performance_stats['average_compilation_time']
        self._performance_stats['average_compilation_time'] = (
            (current_avg * (total - 1) + compilation_time) / total
        )
    
    def set_navigation_callback(self, callback: Callable):
        """Set callback for navigation operations."""
        self._navigation_callback = callback
    
    def set_media_analysis_callback(self, callback: Callable):
        """Set callback for media analysis operations."""
        self._media_analysis_callback = callback
    
    def set_action_validation_callback(self, callback: Callable):
        """Set callback for action validation operations."""
        self._action_validation_callback = callback
    
    def get_active_intents(self) -> Dict[str, Intent]:
        """Get currently active intents."""
        return self._active_intents.copy()
    
    def get_intent_status(self, intent_id: str) -> Optional[ExecutionStatus]:
        """Get the status of a specific intent."""
        intent = self._active_intents.get(intent_id)
        return intent.status if intent else None
    
    def update_intent_status(self, intent_id: str, status: ExecutionStatus, error_message: Optional[str] = None):
        """Update the status of an intent."""
        if intent_id in self._active_intents:
            self._active_intents[intent_id].status = status
            if error_message:
                self._active_intents[intent_id].metadata['error'] = error_message
    
    def cancel_intent(self, intent_id: str) -> bool:
        """Cancel an active intent."""
        if intent_id in self._active_intents:
            self._active_intents[intent_id].status = ExecutionStatus.CANCELLED
            return True
        return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self._performance_stats.copy()
    
    def clear_completed_intents(self):
        """Clear completed intents from active list."""
        completed_statuses = [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]
        self._active_intents = {
            intent_id: intent for intent_id, intent in self._active_intents.items()
            if intent.status not in completed_statuses
        }
    
    def get_intent_suggestions(self, partial_text: str) -> List[str]:
        """Get intent suggestions based on partial text."""
        suggestions = []
        
        # Generate suggestions based on patterns
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                # Extract the pattern structure
                pattern_base = pattern.split('\\s+')[0]  # Get the action verb
                if pattern_base.lower() in partial_text.lower():
                    suggestions.append(f"{pattern_base.title()} [object/target]")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def validate_intent_parameters(self, intent: Intent) -> List[str]:
        """Validate intent parameters and return any issues."""
        issues = []
        
        for goal in intent.goals:
            for sequence in goal.action_sequences:
                for action in sequence.actions:
                    for param in action.parameters:
                        if param.required and not param.value:
                            issues.append(f"Missing required parameter '{param.name}' for action {action.type.value}")
        
        return issues
    
    async def optimize_intent(self, intent: Intent) -> Intent:
        """Optimize intent execution plan."""
        # Remove duplicate actions
        for goal in intent.goals:
            for sequence in goal.action_sequences:
                seen_actions = set()
                optimized_actions = []
                
                for action in sequence.actions:
                    action_signature = f"{action.type.value}_{str(action.parameters)}"
                    if action_signature not in seen_actions:
                        seen_actions.add(action_signature)
                        optimized_actions.append(action)
                
                sequence.actions = optimized_actions
        
        # Reorder actions for efficiency
        for goal in intent.goals:
            for sequence in goal.action_sequences:
                # Sort by priority and estimated execution time
                sequence.actions.sort(key=lambda a: (a.priority.value, a.timeout))
        
        # Update estimated duration after optimization
        intent.estimated_duration = self._estimate_execution_time(intent.goals)
        
        return intent


# Example usage and testing
if __name__ == "__main__":
    async def main():
        # Initialize the intent compiler
        compiler = IntentCompiler()
        
        # Test intent compilation
        test_intents = [
            "Navigate to https://example.com",
            "Search for laptop deals",
            "Login to my account with email john@example.com",
            "Buy iPhone 15 from Apple store",
            "Extract all product names from this page",
            "Fill out the contact form with my information",
            "Monitor stock price for AAPL",
            "Book a flight from NYC to LAX for next Friday"
        ]
        
        for intent_text in test_intents:
            print(f"\n--- Compiling Intent: {intent_text} ---")
            
            intent = await compiler.compile_intent(intent_text)
            
            print(f"Intent ID: {intent.id}")
            print(f"Type: {intent.intent_type.value}")
            print(f"Confidence: {intent.confidence:.2f}")
            print(f"Goals: {len(intent.goals)}")
            print(f"Estimated Duration: {intent.estimated_duration:.2f} seconds")
            print(f"Priority: {intent.priority.value}")
            
            # Show entities
            if intent.entities:
                print("Entities:")
                for entity in intent.entities:
                    print(f"  - {entity.text} ({entity.label})")
            
            # Show actions
            for i, goal in enumerate(intent.goals):
                print(f"Goal {i+1}: {goal.description}")
                for j, sequence in enumerate(goal.action_sequences):
                    print(f"  Sequence {j+1}: {len(sequence.actions)} actions")
                    for k, action in enumerate(sequence.actions):
                        print(f"    Action {k+1}: {action.type.value} - {action.description}")
        
        # Show performance stats
        print(f"\n--- Performance Stats ---")
        stats = compiler.get_performance_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
    
    # Run the example
    asyncio.run(main())
