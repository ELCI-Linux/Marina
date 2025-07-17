#!/usr/bin/env python3
"""
Navigator Core - The heart of Marina's autonomous web navigation

Handles page traversal, DOM state tracking, intelligent form completion,
and semantic element understanding for autonomous web interaction.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urljoin, urlparse
import json
import re

try:
    from playwright.async_api import async_playwright, Page, BrowserContext, Browser
    from playwright.async_api import ElementHandle, Locator
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    import requests
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

class NavigationMode(Enum):
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    HYBRID = "hybrid"

class ElementType(Enum):
    BUTTON = "button"
    LINK = "link"
    INPUT = "input"
    FORM = "form"
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    UNKNOWN = "unknown"

class InteractionType(Enum):
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    HOVER = "hover"
    SUBMIT = "submit"
    WAIT = "wait"
    EXTRACT = "extract"

@dataclass
class ElementInfo:
    """Information about a DOM element"""
    selector: str
    element_type: ElementType
    text: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)
    position: Tuple[int, int] = (0, 0)
    size: Tuple[int, int] = (0, 0)
    is_visible: bool = True
    is_clickable: bool = False
    semantic_label: str = ""
    confidence: float = 0.0

@dataclass
class NavigationAction:
    """Represents a navigation action"""
    action_type: InteractionType
    target: Union[str, ElementInfo]
    value: Optional[str] = None
    timeout: float = 10.0
    wait_for_load: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PageState:
    """Current state of a web page"""
    url: str
    title: str
    dom_hash: str
    screenshot_hash: str = ""
    elements: List[ElementInfo] = field(default_factory=list)
    forms: List[Dict[str, Any]] = field(default_factory=list)
    media: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    load_time: float = 0.0
    is_loaded: bool = False
    errors: List[str] = field(default_factory=list)

class NavigatorCore:
    """
    Core navigation engine for Marina's autonomous web browsing
    """
    
    def __init__(self, mode: NavigationMode = NavigationMode.PLAYWRIGHT, 
                 headless: bool = False, user_agent: str = None):
        self.mode = mode
        self.headless = headless
        self.user_agent = user_agent or self._get_default_user_agent()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Browser instances
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.selenium_driver = None
        
        # State tracking
        self.current_state = None
        self.navigation_history = []
        self.action_history = []
        
        # Configuration
        self.default_timeout = 30.0
        self.default_wait_time = 1.0
        self.max_retries = 3
        
        # Element selectors for common patterns
        self.common_selectors = {
            'login_form': ['form[action*="login"]', 'form[id*="login"]', 'form[class*="login"]'],
            'search_input': ['input[type="search"]', 'input[name*="search"]', 'input[placeholder*="search"]'],
            'submit_button': ['button[type="submit"]', 'input[type="submit"]'],
            'next_button': ['button:contains("Next")', 'a:contains("Next")', '[aria-label*="next"]'],
            'captcha': ['[class*="captcha"]', '[id*="captcha"]', 'iframe[src*="captcha"]'],
        }
        
        # Semantic understanding patterns
        self.semantic_patterns = {
            'navigation': ['nav', 'menu', 'breadcrumb', 'pagination'],
            'content': ['article', 'main', 'content', 'post'],
            'form': ['form', 'input', 'textarea', 'select', 'button'],
            'media': ['img', 'video', 'audio', 'canvas'],
            'interactive': ['button', 'a', 'input', 'select', 'textarea']
        }
        
    def _get_default_user_agent(self) -> str:
        """Get a realistic user agent string"""
        return ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    async def initialize(self):
        """Initialize the browser engine"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                await self._init_playwright()
            elif self.mode == NavigationMode.SELENIUM:
                await self._init_selenium()
            elif self.mode == NavigationMode.HYBRID:
                await self._init_playwright()
                await self._init_selenium()
                
            self.logger.info(f"NavigatorCore initialized in {self.mode.value} mode")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize NavigatorCore: {e}")
            raise
    
    async def _init_playwright(self):
        """Initialize Playwright browser"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not available")
            
        self.playwright = await async_playwright().start()
        
        # Launch browser with optimal settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-default-apps',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--no-first-run',
                '--no-default-browser-check',
                '--password-store=basic',
                '--use-mock-keychain'
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation', 'notifications'],
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        # Create page
        self.page = await self.context.new_page()
        
        # Add stealth measures
        await self._add_stealth_measures()
        
    async def _init_selenium(self):
        """Initialize Selenium WebDriver"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is not available")
            
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless')
            
        options.add_argument(f'--user-agent={self.user_agent}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.selenium_driver = webdriver.Chrome(options=options)
        self.selenium_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    async def _add_stealth_measures(self):
        """Add stealth measures to avoid detection"""
        if not self.page:
            return
            
        # Override navigator properties
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
        """)
        
    async def navigate_to(self, url: str, wait_for_load: bool = True) -> PageState:
        """Navigate to a URL and return page state"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Navigating to: {url}")
            
            if self.mode == NavigationMode.PLAYWRIGHT:
                response = await self.page.goto(url, wait_until='networkidle')
                
                if wait_for_load:
                    await self.page.wait_for_load_state('networkidle')
                    
            elif self.mode == NavigationMode.SELENIUM:
                self.selenium_driver.get(url)
                
                if wait_for_load:
                    WebDriverWait(self.selenium_driver, self.default_timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
            
            # Capture page state
            state = await self._capture_page_state(url)
            state.load_time = time.time() - start_time
            
            self.current_state = state
            self.navigation_history.append(state)
            
            self.logger.info(f"Navigation completed in {state.load_time:.2f}s")
            return state
            
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            raise
    
    async def _capture_page_state(self, url: str) -> PageState:
        """Capture current page state"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                title = await self.page.title()
                dom_content = await self.page.content()
                
                # Take screenshot for hash
                screenshot = await self.page.screenshot()
                screenshot_hash = hash(screenshot)
                
            elif self.mode == NavigationMode.SELENIUM:
                title = self.selenium_driver.title
                dom_content = self.selenium_driver.page_source
                screenshot_hash = ""
            
            # Create DOM hash
            dom_hash = hash(dom_content)
            
            # Extract elements
            elements = await self._extract_elements()
            
            # Extract forms
            forms = await self._extract_forms()
            
            # Extract media
            media = await self._extract_media()
            
            state = PageState(
                url=url,
                title=title,
                dom_hash=str(dom_hash),
                screenshot_hash=str(screenshot_hash),
                elements=elements,
                forms=forms,
                media=media,
                is_loaded=True
            )
            
            return state
            
        except Exception as e:
            self.logger.error(f"Failed to capture page state: {e}")
            return PageState(url=url, title="", dom_hash="", is_loaded=False, errors=[str(e)])
    
    async def _extract_elements(self) -> List[ElementInfo]:
        """Extract and analyze page elements"""
        elements = []
        
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                # Extract interactive elements
                selectors = [
                    'button', 'a', 'input', 'textarea', 'select',
                    '[onclick]', '[role="button"]', '[tabindex]'
                ]
                
                for selector in selectors:
                    element_handles = await self.page.query_selector_all(selector)
                    
                    for handle in element_handles:
                        element_info = await self._analyze_element(handle, selector)
                        if element_info:
                            elements.append(element_info)
                            
        except Exception as e:
            self.logger.error(f"Element extraction failed: {e}")
            
        return elements
    
    async def _analyze_element(self, element_handle: ElementHandle, selector: str) -> Optional[ElementInfo]:
        """Analyze a single element"""
        try:
            # Get element properties
            tag_name = await element_handle.evaluate('el => el.tagName.toLowerCase()')
            text = await element_handle.inner_text()
            attributes = await element_handle.evaluate('el => Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]))')
            
            # Get position and size
            bbox = await element_handle.bounding_box()
            position = (int(bbox['x']), int(bbox['y'])) if bbox else (0, 0)
            size = (int(bbox['width']), int(bbox['height'])) if bbox else (0, 0)
            
            # Check visibility and clickability
            is_visible = await element_handle.is_visible()
            is_clickable = await element_handle.is_enabled() and is_visible
            
            # Determine element type
            element_type = self._classify_element(tag_name, attributes, text)
            
            # Generate semantic label
            semantic_label = self._generate_semantic_label(tag_name, attributes, text)
            
            # Calculate confidence
            confidence = self._calculate_element_confidence(element_type, attributes, text, is_visible)
            
            return ElementInfo(
                selector=selector,
                element_type=element_type,
                text=text.strip(),
                attributes=attributes,
                position=position,
                size=size,
                is_visible=is_visible,
                is_clickable=is_clickable,
                semantic_label=semantic_label,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Element analysis failed: {e}")
            return None
    
    def _classify_element(self, tag_name: str, attributes: Dict[str, str], text: str) -> ElementType:
        """Classify element type based on tag and attributes"""
        tag_name = tag_name.lower()
        
        if tag_name == 'button' or attributes.get('type') == 'submit':
            return ElementType.BUTTON
        elif tag_name == 'a':
            return ElementType.LINK
        elif tag_name in ['input', 'textarea', 'select']:
            return ElementType.INPUT
        elif tag_name == 'form':
            return ElementType.FORM
        elif tag_name in ['img', 'picture']:
            return ElementType.IMAGE
        elif tag_name == 'video':
            return ElementType.VIDEO
        elif tag_name == 'audio':
            return ElementType.AUDIO
        elif tag_name in ['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return ElementType.TEXT
        else:
            return ElementType.UNKNOWN
    
    def _generate_semantic_label(self, tag_name: str, attributes: Dict[str, str], text: str) -> str:
        """Generate semantic label for element"""
        labels = []
        
        # Add role-based labels
        if 'aria-label' in attributes:
            labels.append(attributes['aria-label'])
        
        if 'title' in attributes:
            labels.append(attributes['title'])
            
        if 'placeholder' in attributes:
            labels.append(f"placeholder: {attributes['placeholder']}")
            
        # Add text content
        if text:
            labels.append(text[:50])
            
        # Add type information
        if 'type' in attributes:
            labels.append(f"type: {attributes['type']}")
            
        return " | ".join(labels) if labels else f"{tag_name} element"
    
    def _calculate_element_confidence(self, element_type: ElementType, attributes: Dict[str, str], 
                                    text: str, is_visible: bool) -> float:
        """Calculate confidence score for element classification"""
        confidence = 0.5  # Base confidence
        
        # Boost for visible elements
        if is_visible:
            confidence += 0.2
            
        # Boost for elements with clear attributes
        if 'aria-label' in attributes or 'title' in attributes:
            confidence += 0.1
            
        # Boost for elements with text content
        if text.strip():
            confidence += 0.1
            
        # Boost for specific element types
        if element_type in [ElementType.BUTTON, ElementType.LINK, ElementType.INPUT]:
            confidence += 0.1
            
        return min(confidence, 1.0)
    
    async def _extract_forms(self) -> List[Dict[str, Any]]:
        """Extract form information from page"""
        forms = []
        
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                form_handles = await self.page.query_selector_all('form')
                
                for form_handle in form_handles:
                    form_info = await self._analyze_form(form_handle)
                    if form_info:
                        forms.append(form_info)
                        
        except Exception as e:
            self.logger.error(f"Form extraction failed: {e}")
            
        return forms
    
    async def _analyze_form(self, form_handle: ElementHandle) -> Optional[Dict[str, Any]]:
        """Analyze a form element"""
        try:
            # Get form attributes
            attributes = await form_handle.evaluate('''
                form => ({
                    action: form.action,
                    method: form.method,
                    name: form.name,
                    id: form.id,
                    class: form.className
                })
            ''')
            
            # Get form inputs
            inputs = await form_handle.query_selector_all('input, textarea, select')
            input_info = []
            
            for input_handle in inputs:
                input_data = await input_handle.evaluate('''
                    input => ({
                        type: input.type,
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder,
                        required: input.required,
                        value: input.value
                    })
                ''')
                input_info.append(input_data)
            
            return {
                'attributes': attributes,
                'inputs': input_info,
                'input_count': len(input_info)
            }
            
        except Exception as e:
            self.logger.error(f"Form analysis failed: {e}")
            return None
    
    async def _extract_media(self) -> List[Dict[str, Any]]:
        """Extract media elements from page"""
        media = []
        
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                # Extract images
                images = await self.page.query_selector_all('img')
                for img in images:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt')
                    if src:
                        media.append({
                            'type': 'image',
                            'src': src,
                            'alt': alt or '',
                            'full_url': urljoin(self.current_state.url if self.current_state else '', src)
                        })
                
                # Extract videos
                videos = await self.page.query_selector_all('video')
                for video in videos:
                    src = await video.get_attribute('src')
                    if not src:
                        source = await video.query_selector('source')
                        if source:
                            src = await source.get_attribute('src')
                    
                    if src:
                        media.append({
                            'type': 'video',
                            'src': src,
                            'full_url': urljoin(self.current_state.url if self.current_state else '', src)
                        })
                
                # Extract audio
                audios = await self.page.query_selector_all('audio')
                for audio in audios:
                    src = await audio.get_attribute('src')
                    if not src:
                        source = await audio.query_selector('source')
                        if source:
                            src = await source.get_attribute('src')
                    
                    if src:
                        media.append({
                            'type': 'audio',
                            'src': src,
                            'full_url': urljoin(self.current_state.url if self.current_state else '', src)
                        })
                        
        except Exception as e:
            self.logger.error(f"Media extraction failed: {e}")
            
        return media
    
    async def execute_action(self, action: NavigationAction) -> bool:
        """Execute a navigation action"""
        try:
            self.logger.info(f"Executing action: {action.action_type.value} on {action.target}")
            
            success = False
            
            if action.action_type == InteractionType.CLICK:
                success = await self._click_element(action.target, action.timeout)
            elif action.action_type == InteractionType.TYPE:
                success = await self._type_text(action.target, action.value, action.timeout)
            elif action.action_type == InteractionType.SCROLL:
                success = await self._scroll_page(action.value, action.timeout)
            elif action.action_type == InteractionType.HOVER:
                success = await self._hover_element(action.target, action.timeout)
            elif action.action_type == InteractionType.SUBMIT:
                success = await self._submit_form(action.target, action.timeout)
            elif action.action_type == InteractionType.WAIT:
                success = await self._wait_for_element(action.target, action.timeout)
            elif action.action_type == InteractionType.EXTRACT:
                success = await self._extract_element_data(action.target, action.timeout)
            
            # Record action
            self.action_history.append({
                'action': action,
                'success': success,
                'timestamp': time.time()
            })
            
            # Wait for page changes if requested
            if action.wait_for_load and success:
                await self._wait_for_page_stability()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Action execution failed: {e}")
            return False
    
    async def _click_element(self, target: Union[str, ElementInfo], timeout: float) -> bool:
        """Click on an element"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                if isinstance(target, str):
                    await self.page.click(target, timeout=timeout * 1000)
                else:
                    await self.page.click(target.selector, timeout=timeout * 1000)
                return True
                
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False
    
    async def _type_text(self, target: Union[str, ElementInfo], text: str, timeout: float) -> bool:
        """Type text into an element"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                if isinstance(target, str):
                    await self.page.fill(target, text, timeout=timeout * 1000)
                else:
                    await self.page.fill(target.selector, text, timeout=timeout * 1000)
                return True
                
        except Exception as e:
            self.logger.error(f"Type failed: {e}")
            return False
    
    async def _scroll_page(self, direction: str, timeout: float) -> bool:
        """Scroll the page"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                if direction == "down":
                    await self.page.keyboard.press("PageDown")
                elif direction == "up":
                    await self.page.keyboard.press("PageUp")
                elif direction == "top":
                    await self.page.keyboard.press("Home")
                elif direction == "bottom":
                    await self.page.keyboard.press("End")
                return True
                
        except Exception as e:
            self.logger.error(f"Scroll failed: {e}")
            return False
    
    async def _hover_element(self, target: Union[str, ElementInfo], timeout: float) -> bool:
        """Hover over an element"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                if isinstance(target, str):
                    await self.page.hover(target, timeout=timeout * 1000)
                else:
                    await self.page.hover(target.selector, timeout=timeout * 1000)
                return True
                
        except Exception as e:
            self.logger.error(f"Hover failed: {e}")
            return False
    
    async def _submit_form(self, target: Union[str, ElementInfo], timeout: float) -> bool:
        """Submit a form"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                if isinstance(target, str):
                    await self.page.press(target, "Enter")
                else:
                    await self.page.press(target.selector, "Enter")
                return True
                
        except Exception as e:
            self.logger.error(f"Submit failed: {e}")
            return False
    
    async def _wait_for_element(self, target: Union[str, ElementInfo], timeout: float) -> bool:
        """Wait for an element to appear"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                if isinstance(target, str):
                    await self.page.wait_for_selector(target, timeout=timeout * 1000)
                else:
                    await self.page.wait_for_selector(target.selector, timeout=timeout * 1000)
                return True
                
        except Exception as e:
            self.logger.error(f"Wait failed: {e}")
            return False
    
    async def _extract_element_data(self, target: Union[str, ElementInfo], timeout: float) -> bool:
        """Extract data from an element"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                if isinstance(target, str):
                    element = await self.page.wait_for_selector(target, timeout=timeout * 1000)
                    text = await element.inner_text()
                    self.logger.info(f"Extracted text: {text}")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Extract failed: {e}")
            return False
    
    async def _wait_for_page_stability(self, timeout: float = 5.0):
        """Wait for page to stabilize after action"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                await self.page.wait_for_load_state('networkidle', timeout=timeout * 1000)
                
        except Exception as e:
            self.logger.debug(f"Page stability wait timeout: {e}")
    
    async def find_elements_by_text(self, text: str, element_type: str = None) -> List[ElementInfo]:
        """Find elements containing specific text"""
        elements = []
        
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                # Build selector based on element type
                if element_type:
                    selector = f"{element_type}:has-text('{text}')"
                else:
                    selector = f":has-text('{text}')"
                
                element_handles = await self.page.query_selector_all(selector)
                
                for handle in element_handles:
                    element_info = await self._analyze_element(handle, selector)
                    if element_info:
                        elements.append(element_info)
                        
        except Exception as e:
            self.logger.error(f"Text search failed: {e}")
            
        return elements
    
    async def find_form_by_purpose(self, purpose: str) -> Optional[Dict[str, Any]]:
        """Find form by purpose (login, search, contact, etc.)"""
        if not self.current_state:
            return None
            
        purpose = purpose.lower()
        
        for form in self.current_state.forms:
            # Check form action
            action = form.get('attributes', {}).get('action', '').lower()
            if purpose in action:
                return form
                
            # Check form inputs
            for input_info in form.get('inputs', []):
                input_name = input_info.get('name', '').lower()
                input_type = input_info.get('type', '').lower()
                input_placeholder = input_info.get('placeholder', '').lower()
                
                if (purpose in input_name or 
                    purpose in input_placeholder or
                    (purpose == 'login' and input_type == 'password') or
                    (purpose == 'search' and input_type == 'search')):
                    return form
                    
        return None
    
    async def intelligent_form_fill(self, form_data: Dict[str, str]) -> bool:
        """Intelligently fill out a form"""
        try:
            if not self.current_state:
                return False
                
            # Find the best matching form
            target_form = None
            for form in self.current_state.forms:
                # Score form based on input types
                score = 0
                for input_info in form.get('inputs', []):
                    input_name = input_info.get('name', '').lower()
                    input_type = input_info.get('type', '').lower()
                    
                    # Check if we have matching data
                    for key in form_data.keys():
                        if key.lower() in input_name or key.lower() in input_type:
                            score += 1
                            
                if score > 0:
                    target_form = form
                    break
            
            if not target_form:
                self.logger.warning("No suitable form found")
                return False
            
            # Fill form inputs
            filled_count = 0
            for input_info in target_form.get('inputs', []):
                input_name = input_info.get('name', '')
                input_type = input_info.get('type', '')
                input_id = input_info.get('id', '')
                
                # Find matching data
                value = None
                for key, val in form_data.items():
                    if (key.lower() in input_name.lower() or 
                        key.lower() in input_type.lower() or 
                        key.lower() in input_id.lower()):
                        value = val
                        break
                
                if value and input_name:
                    # Fill the input
                    selector = f'[name="{input_name}"]'
                    action = NavigationAction(
                        action_type=InteractionType.TYPE,
                        target=selector,
                        value=value,
                        wait_for_load=False
                    )
                    
                    if await self.execute_action(action):
                        filled_count += 1
                        
            self.logger.info(f"Filled {filled_count} form fields")
            return filled_count > 0
            
        except Exception as e:
            self.logger.error(f"Form filling failed: {e}")
            return False
    
    async def get_current_url(self) -> str:
        """Get current page URL"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                return self.page.url
            elif self.mode == NavigationMode.SELENIUM:
                return self.selenium_driver.current_url
        except Exception as e:
            self.logger.error(f"Failed to get current URL: {e}")
            return ""
    
    async def take_screenshot(self, filename: str = None) -> bytes:
        """Take a screenshot of current page"""
        try:
            if self.mode == NavigationMode.PLAYWRIGHT:
                return await self.page.screenshot(path=filename)
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return b""
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
                
            if self.context:
                await self.context.close()
                
            if self.browser:
                await self.browser.close()
                
            if self.playwright:
                await self.playwright.stop()
                
            if self.selenium_driver:
                self.selenium_driver.quit()
                
            self.logger.info("NavigatorCore cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    def get_navigation_history(self) -> List[PageState]:
        """Get navigation history"""
        return self.navigation_history.copy()
    
    def get_action_history(self) -> List[Dict[str, Any]]:
        """Get action history"""
        return self.action_history.copy()
    
    def get_current_state(self) -> Optional[PageState]:
        """Get current page state"""
        return self.current_state
