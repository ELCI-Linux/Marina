#!/usr/bin/env python3
"""
Marina-Powered Browser Widgets for Spectra

This module creates Chromium browser widgets that are powered by Marina's AI capabilities
and can be loaded within the Spectra browser window. These widgets provide enhanced
browsing experiences with AI-powered features.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import os
import base64
from pathlib import Path

# Core dependencies
from playwright.async_api import Page, BrowserContext
import aiohttp
import websockets
from jinja2 import Template

# Marina components
from .spectra_core import SpectraCore
from .memory_optimizer import get_memory_optimizer, lazy_import

# Lazy imports for heavy dependencies
cv2 = lazy_import("cv2")
numpy = lazy_import("numpy")


class WidgetType(Enum):
    """Types of browser widgets."""
    AI_ASSISTANT = "ai_assistant"
    PAGE_ANALYZER = "page_analyzer"
    FORM_FILLER = "form_filler"
    CONTENT_SUMMARIZER = "content_summarizer"
    TRANSLATION_TOOL = "translation_tool"
    ACCESSIBILITY_CHECKER = "accessibility_checker"
    PERFORMANCE_MONITOR = "performance_monitor"
    SECURITY_SCANNER = "security_scanner"
    SHOPPING_ASSISTANT = "shopping_assistant"
    SOCIAL_MEDIA_MANAGER = "social_media_manager"


class WidgetPosition(Enum):
    """Widget positioning options."""
    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"
    CENTER = "center"
    FLOATING = "floating"
    SIDEBAR_LEFT = "sidebar-left"
    SIDEBAR_RIGHT = "sidebar-right"


@dataclass
class WidgetConfig:
    """Configuration for a browser widget."""
    id: str
    type: WidgetType
    title: str
    position: WidgetPosition
    width: int = 300
    height: int = 400
    resizable: bool = True
    minimizable: bool = True
    closable: bool = True
    transparent: bool = False
    always_on_top: bool = False
    auto_hide: bool = False
    keyboard_shortcuts: Dict[str, str] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WidgetState:
    """Current state of a widget."""
    id: str
    visible: bool = True
    minimized: bool = False
    x: int = 0
    y: int = 0
    width: int = 300
    height: int = 400
    z_index: int = 1000
    last_interaction: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)


class BrowserWidget:
    """Base class for Marina-powered browser widgets."""
    
    def __init__(self, config: WidgetConfig, marina_core: SpectraCore):
        self.config = config
        self.marina = marina_core
        self.state = WidgetState(id=config.id)
        self.logger = logging.getLogger(f"{__name__}.{config.type.value}")
        
        # Widget-specific setup
        self.websocket_server = None
        self.message_handlers: Dict[str, Callable] = {}
        self.periodic_tasks: List[asyncio.Task] = []
        
        # Setup message handlers
        self._setup_message_handlers()
    
    def _setup_message_handlers(self):
        """Setup message handlers for widget communication."""
        self.message_handlers = {
            'get_state': self._handle_get_state,
            'set_state': self._handle_set_state,
            'execute_action': self._handle_execute_action,
            'get_page_content': self._handle_get_page_content,
            'analyze_page': self._handle_analyze_page,
            'close_widget': self._handle_close_widget,
            'minimize_widget': self._handle_minimize_widget,
            'resize_widget': self._handle_resize_widget,
        }
    
    async def initialize(self):
        """Initialize the widget."""
        try:
            # Start WebSocket server for communication
            await self._start_websocket_server()
            
            # Start periodic tasks
            await self._start_periodic_tasks()
            
            self.logger.info(f"Widget {self.config.id} initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize widget {self.config.id}: {e}")
            raise
    
    async def _start_websocket_server(self):
        """Start WebSocket server for widget communication."""
        async def handler(websocket, path):
            try:
                async for message in websocket:
                    data = json.loads(message)
                    response = await self._handle_message(data)
                    await websocket.send(json.dumps(response))
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
        
        # Start server on a dynamic port
        self.websocket_server = await websockets.serve(
            handler, "localhost", 0
        )
        port = self.websocket_server.sockets[0].getsockname()[1]
        self.websocket_port = port
        
        self.logger.info(f"Widget WebSocket server started on port {port}")
    
    async def _start_periodic_tasks(self):
        """Start periodic background tasks."""
        # Override in subclasses for widget-specific tasks
        pass
    
    async def _handle_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages from the widget UI."""
        try:
            action = data.get('action')
            handler = self.message_handlers.get(action)
            
            if handler:
                return await handler(data)
            else:
                return {'error': f'Unknown action: {action}'}
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            return {'error': str(e)}
    
    async def _handle_get_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get state request."""
        return {
            'state': {
                'id': self.state.id,
                'visible': self.state.visible,
                'minimized': self.state.minimized,
                'x': self.state.x,
                'y': self.state.y,
                'width': self.state.width,
                'height': self.state.height,
                'data': self.state.data
            }
        }
    
    async def _handle_set_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle set state request."""
        state_data = data.get('state', {})
        
        for key, value in state_data.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        
        self.state.last_interaction = datetime.now()
        return {'success': True}
    
    async def _handle_execute_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execute action request."""
        action_data = data.get('action_data', {})
        
        # Execute action using Marina
        try:
            result = await self.marina.execute_intent(
                action_data.get('intent', ''),
                session_id=action_data.get('session_id'),
                user_id=action_data.get('user_id')
            )
            
            return {
                'success': result.success,
                'execution_time': result.execution_time,
                'actions_performed': result.actions_performed,
                'error_message': result.error_message
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _handle_get_page_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get page content request."""
        # This would be implemented by the widget manager
        return {'content': 'Page content not available'}
    
    async def _handle_analyze_page(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analyze page request."""
        # This would be implemented by the widget manager
        return {'analysis': 'Page analysis not available'}
    
    async def _handle_close_widget(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle close widget request."""
        self.state.visible = False
        return {'success': True}
    
    async def _handle_minimize_widget(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle minimize widget request."""
        self.state.minimized = not self.state.minimized
        return {'success': True, 'minimized': self.state.minimized}
    
    async def _handle_resize_widget(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resize widget request."""
        self.state.width = data.get('width', self.state.width)
        self.state.height = data.get('height', self.state.height)
        return {'success': True}
    
    def get_html(self) -> str:
        """Get the HTML content for the widget."""
        # Override in subclasses
        return self._get_base_html()
    
    def _get_base_html(self) -> str:
        """Get base HTML template for widgets."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body {
                    margin: 0;
                    padding: 10px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #f5f5f5;
                }
                .widget-container {
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                }
                .widget-header {
                    background: #2c3e50;
                    color: white;
                    padding: 8px 12px;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 4px 4px 0 0;
                    cursor: move;
                    user-select: none;
                }
                .widget-content {
                    flex: 1;
                    background: white;
                    border: 1px solid #ddd;
                    border-top: none;
                    border-radius: 0 0 4px 4px;
                    overflow: auto;
                    padding: 10px;
                }
                .widget-controls {
                    position: absolute;
                    top: 5px;
                    right: 5px;
                    display: flex;
                    gap: 5px;
                }
                .widget-btn {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    width: 20px;
                    height: 20px;
                    border-radius: 3px;
                    cursor: pointer;
                    font-size: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .widget-btn:hover {
                    background: rgba(255,255,255,0.3);
                }
            </style>
        </head>
        <body>
            <div class="widget-container">
                <div class="widget-header">
                    {{ title }}
                    <div class="widget-controls">
                        <button class="widget-btn" onclick="minimizeWidget()">–</button>
                        <button class="widget-btn" onclick="closeWidget()">×</button>
                    </div>
                </div>
                <div class="widget-content" id="widget-content">
                    <!-- Widget content goes here -->
                </div>
            </div>
            
            <script>
                const ws = new WebSocket('ws://localhost:{{ websocket_port }}');
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                };
                
                function sendMessage(action, data = {}) {
                    ws.send(JSON.stringify({action, ...data}));
                }
                
                function minimizeWidget() {
                    sendMessage('minimize_widget');
                }
                
                function closeWidget() {
                    sendMessage('close_widget');
                }
                
                function handleMessage(data) {
                    // Override in widget implementations
                    console.log('Received:', data);
                }
                
                // Make widget draggable
                let isDragging = false;
                let dragOffset = {x: 0, y: 0};
                
                document.querySelector('.widget-header').addEventListener('mousedown', function(e) {
                    isDragging = true;
                    dragOffset.x = e.clientX;
                    dragOffset.y = e.clientY;
                });
                
                document.addEventListener('mousemove', function(e) {
                    if (isDragging) {
                        const deltaX = e.clientX - dragOffset.x;
                        const deltaY = e.clientY - dragOffset.y;
                        
                        // Update widget position
                        sendMessage('set_state', {
                            state: {
                                x: deltaX,
                                y: deltaY
                            }
                        });
                        
                        dragOffset.x = e.clientX;
                        dragOffset.y = e.clientY;
                    }
                });
                
                document.addEventListener('mouseup', function() {
                    isDragging = false;
                });
            </script>
        </body>
        </html>
        """
    
    async def shutdown(self):
        """Shutdown the widget."""
        try:
            # Cancel periodic tasks
            for task in self.periodic_tasks:
                task.cancel()
            
            # Close WebSocket server
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            
            self.logger.info(f"Widget {self.config.id} shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during widget shutdown: {e}")


class AIAssistantWidget(BrowserWidget):
    """AI Assistant widget for intelligent browsing help."""
    
    def __init__(self, config: WidgetConfig, marina_core: SpectraCore):
        super().__init__(config, marina_core)
        self.conversation_history: List[Dict[str, str]] = []
    
    async def _start_periodic_tasks(self):
        """Start AI assistant specific tasks."""
        # Start context monitoring
        task = asyncio.create_task(self._monitor_context())
        self.periodic_tasks.append(task)
    
    async def _monitor_context(self):
        """Monitor browsing context for proactive assistance."""
        while True:
            try:
                # Monitor for forms, errors, or other assistance opportunities
                await asyncio.sleep(5)
                
                # This would analyze the current page context
                # and provide proactive suggestions
                
            except Exception as e:
                self.logger.error(f"Context monitoring error: {e}")
                await asyncio.sleep(30)
    
    def get_html(self) -> str:
        """Get AI Assistant widget HTML."""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body {
                    margin: 0;
                    padding: 10px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #f5f5f5;
                }
                .chat-container {
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                }
                .chat-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 10px;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-bottom: 10px;
                }
                .message {
                    margin-bottom: 10px;
                    padding: 8px 12px;
                    border-radius: 8px;
                    max-width: 80%;
                }
                .message.user {
                    background: #007bff;
                    color: white;
                    margin-left: auto;
                }
                .message.ai {
                    background: #e9ecef;
                    color: #333;
                }
                .chat-input {
                    display: flex;
                    gap: 10px;
                }
                .chat-input input {
                    flex: 1;
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                }
                .chat-input button {
                    padding: 8px 16px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                }
                .chat-input button:hover {
                    background: #0056b3;
                }
                .suggestions {
                    margin-bottom: 10px;
                }
                .suggestion {
                    display: inline-block;
                    padding: 4px 8px;
                    margin: 2px;
                    background: #e9ecef;
                    border-radius: 12px;
                    font-size: 12px;
                    cursor: pointer;
                }
                .suggestion:hover {
                    background: #dee2e6;
                }
            </style>
        </head>
        <body>
            <div class="chat-container">
                <div class="suggestions" id="suggestions">
                    <div class="suggestion" onclick="sendSuggestion('Help me fill this form')">Fill Form</div>
                    <div class="suggestion" onclick="sendSuggestion('Summarize this page')">Summarize</div>
                    <div class="suggestion" onclick="sendSuggestion('Find similar products')">Find Similar</div>
                    <div class="suggestion" onclick="sendSuggestion('Check for better prices')">Price Check</div>
                </div>
                <div class="chat-messages" id="messages"></div>
                <div class="chat-input">
                    <input type="text" id="messageInput" placeholder="Ask me anything about this page..." 
                           onkeypress="handleKeyPress(event)">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <script>
                const ws = new WebSocket('ws://localhost:{{ websocket_port }}');
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleResponse(data);
                };
                
                function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const message = input.value.trim();
                    if (message) {
                        addMessage(message, 'user');
                        input.value = '';
                        
                        // Send to AI assistant
                        ws.send(JSON.stringify({
                            action: 'chat_message',
                            message: message
                        }));
                    }
                }
                
                function sendSuggestion(suggestion) {
                    addMessage(suggestion, 'user');
                    ws.send(JSON.stringify({
                        action: 'chat_message',
                        message: suggestion
                    }));
                }
                
                function handleKeyPress(event) {
                    if (event.key === 'Enter') {
                        sendMessage();
                    }
                }
                
                function addMessage(text, sender) {
                    const messages = document.getElementById('messages');
                    const message = document.createElement('div');
                    message.className = `message ${sender}`;
                    message.textContent = text;
                    messages.appendChild(message);
                    messages.scrollTop = messages.scrollHeight;
                }
                
                function handleResponse(data) {
                    if (data.response) {
                        addMessage(data.response, 'ai');
                    }
                }
                
                // Initial greeting
                addMessage('Hello! I\'m your AI browsing assistant. How can I help you with this page?', 'ai');
            </script>
        </body>
        </html>
        """)
        
        return template.render(
            title=self.config.title,
            websocket_port=self.websocket_port
        )


class PageAnalyzerWidget(BrowserWidget):
    """Page analyzer widget for analyzing web page content."""
    
    def get_html(self) -> str:
        """Get Page Analyzer widget HTML."""
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body {
                    margin: 0;
                    padding: 10px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #f5f5f5;
                }
                .analyzer-container {
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                }
                .analyzer-controls {
                    display: flex;
                    gap: 10px;
                    margin-bottom: 10px;
                }
                .analyzer-btn {
                    padding: 8px 16px;
                    background: #28a745;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                }
                .analyzer-btn:hover {
                    background: #218838;
                }
                .analyzer-results {
                    flex: 1;
                    overflow-y: auto;
                    padding: 10px;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                .result-section {
                    margin-bottom: 20px;
                }
                .result-title {
                    font-weight: bold;
                    font-size: 16px;
                    margin-bottom: 10px;
                    color: #333;
                }
                .result-item {
                    margin-bottom: 8px;
                    padding: 8px;
                    background: #f8f9fa;
                    border-radius: 4px;
                }
                .loading {
                    text-align: center;
                    padding: 20px;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="analyzer-container">
                <div class="analyzer-controls">
                    <button class="analyzer-btn" onclick="analyzeContent()">Analyze Content</button>
                    <button class="analyzer-btn" onclick="analyzeSEO()">SEO Analysis</button>
                    <button class="analyzer-btn" onclick="analyzePerformance()">Performance</button>
                    <button class="analyzer-btn" onclick="analyzeAccessibility()">Accessibility</button>
                </div>
                <div class="analyzer-results" id="results">
                    <div class="loading">Click a button above to start analysis</div>
                </div>
            </div>
            
            <script>
                const ws = new WebSocket('ws://localhost:{{ websocket_port }}');
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    displayResults(data);
                };
                
                function analyzeContent() {
                    showLoading('Analyzing page content...');
                    ws.send(JSON.stringify({
                        action: 'analyze_content'
                    }));
                }
                
                function analyzeSEO() {
                    showLoading('Analyzing SEO metrics...');
                    ws.send(JSON.stringify({
                        action: 'analyze_seo'
                    }));
                }
                
                function analyzePerformance() {
                    showLoading('Analyzing performance metrics...');
                    ws.send(JSON.stringify({
                        action: 'analyze_performance'
                    }));
                }
                
                function analyzeAccessibility() {
                    showLoading('Analyzing accessibility...');
                    ws.send(JSON.stringify({
                        action: 'analyze_accessibility'
                    }));
                }
                
                function showLoading(message) {
                    const results = document.getElementById('results');
                    results.innerHTML = `<div class="loading">${message}</div>`;
                }
                
                function displayResults(data) {
                    const results = document.getElementById('results');
                    let html = '';
                    
                    if (data.analysis) {
                        for (const [section, items] of Object.entries(data.analysis)) {
                            html += `<div class="result-section">`;
                            html += `<div class="result-title">${section.replace('_', ' ').toUpperCase()}</div>`;
                            
                            if (Array.isArray(items)) {
                                items.forEach(item => {
                                    html += `<div class="result-item">${item}</div>`;
                                });
                            } else {
                                html += `<div class="result-item">${JSON.stringify(items, null, 2)}</div>`;
                            }
                            
                            html += `</div>`;
                        }
                    }
                    
                    results.innerHTML = html || '<div class="loading">No results available</div>';
                }
            </script>
        </body>
        </html>
        """)
        
        return template.render(
            title=self.config.title,
            websocket_port=self.websocket_port
        )


class WidgetManager:
    """Manager for browser widgets within Spectra."""
    
    def __init__(self, marina_core: SpectraCore):
        self.marina = marina_core
        self.logger = logging.getLogger(__name__)
        self.widgets: Dict[str, BrowserWidget] = {}
        self.widget_classes = {
            WidgetType.AI_ASSISTANT: AIAssistantWidget,
            WidgetType.PAGE_ANALYZER: PageAnalyzerWidget,
            # Add more widget types as needed
        }
        
        # Memory optimization
        self.memory_optimizer = get_memory_optimizer()
        self.widget_cache = self.memory_optimizer.create_cache("widget_cache", max_size=50)
    
    async def create_widget(self, widget_type: WidgetType, config: Optional[WidgetConfig] = None) -> str:
        """Create a new widget instance."""
        try:
            # Generate widget ID
            widget_id = f"{widget_type.value}_{uuid.uuid4().hex[:8]}"
            
            # Create config if not provided
            if config is None:
                config = WidgetConfig(
                    id=widget_id,
                    type=widget_type,
                    title=widget_type.value.replace('_', ' ').title(),
                    position=WidgetPosition.TOP_RIGHT
                )
            
            # Get widget class
            widget_class = self.widget_classes.get(widget_type)
            if not widget_class:
                raise ValueError(f"Unknown widget type: {widget_type}")
            
            # Create widget instance
            widget = widget_class(config, self.marina)
            
            # Initialize widget
            await widget.initialize()
            
            # Store widget
            self.widgets[widget_id] = widget
            
            self.logger.info(f"Created widget {widget_id} of type {widget_type.value}")
            return widget_id
            
        except Exception as e:
            self.logger.error(f"Failed to create widget: {e}")
            raise
    
    async def inject_widget(self, page: Page, widget_id: str) -> bool:
        """Inject a widget into a browser page."""
        try:
            widget = self.widgets.get(widget_id)
            if not widget:
                raise ValueError(f"Widget {widget_id} not found")
            
            # Get widget HTML
            widget_html = widget.get_html()
            
            # Escape backticks in HTML to prevent template literal issues
            escaped_html = widget_html.replace('`', '\\`')
            
            # Inject widget into page
            await page.evaluate(f"""
                (function() {{
                    // Create widget container
                    const widgetContainer = document.createElement('div');
                    widgetContainer.id = 'marina-widget-{widget_id}';
                    widgetContainer.style.cssText = `
                        position: fixed;
                        top: {widget.state.y}px;
                        left: {widget.state.x}px;
                        width: {widget.state.width}px;
                        height: {widget.state.height}px;
                        z-index: {widget.state.z_index};
                        background: white;
                        border: 1px solid #ccc;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        overflow: hidden;
                        resize: both;
                    `;
                    
                    // Create iframe for widget content
                    const iframe = document.createElement('iframe');
                    iframe.style.cssText = `
                        width: 100%;
                        height: 100%;
                        border: none;
                    `;
                    
                    // Set widget HTML
                    iframe.srcdoc = `{escaped_html}`;
                    
                    widgetContainer.appendChild(iframe);
                    document.body.appendChild(widgetContainer);
                    
                    console.log('Marina widget {widget_id} injected successfully');
                }})();
            """)
            
            self.logger.info(f"Injected widget {widget_id} into page")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to inject widget {widget_id}: {e}")
            return False
    
    async def remove_widget(self, page: Page, widget_id: str) -> bool:
        """Remove a widget from a browser page."""
        try:
            await page.evaluate(f"""
                (function() {{
                    const widget = document.getElementById('marina-widget-{widget_id}');
                    if (widget) {{
                        widget.remove();
                        console.log('Marina widget {widget_id} removed');
                    }}
                }})();
            """)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove widget {widget_id}: {e}")
            return False
    
    async def get_widget_list(self) -> List[Dict[str, Any]]:
        """Get list of available widgets."""
        widget_list = []
        
        for widget_id, widget in self.widgets.items():
            widget_list.append({
                'id': widget_id,
                'type': widget.config.type.value,
                'title': widget.config.title,
                'position': widget.config.position.value,
                'visible': widget.state.visible,
                'minimized': widget.state.minimized
            })
        
        return widget_list
    
    async def shutdown_widget(self, widget_id: str) -> bool:
        """Shutdown a specific widget."""
        try:
            widget = self.widgets.get(widget_id)
            if widget:
                await widget.shutdown()
                del self.widgets[widget_id]
                self.logger.info(f"Shutdown widget {widget_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to shutdown widget {widget_id}: {e}")
            return False
    
    async def shutdown_all_widgets(self):
        """Shutdown all widgets."""
        for widget_id in list(self.widgets.keys()):
            await self.shutdown_widget(widget_id)
    
    def get_widget_html_template(self) -> str:
        """Get the HTML template for widget injection."""
        return """
        <!-- Marina Widget Container -->
        <div id="marina-widget-container" style="display: none;">
            <div id="marina-widget-toolbar" style="
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 10000;
                background: #2c3e50;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-family: sans-serif;
                font-size: 14px;
                cursor: pointer;
                user-select: none;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            ">
                🤖 Marina Widgets
                <div id="marina-widget-menu" style="
                    display: none;
                    position: absolute;
                    top: 100%;
                    right: 0;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    min-width: 200px;
                    margin-top: 5px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                ">
                    <div class="widget-menu-item" onclick="createWidget('ai_assistant')" style="
                        padding: 10px 15px;
                        color: #333;
                        cursor: pointer;
                        border-bottom: 1px solid #eee;
                    ">🤖 AI Assistant</div>
                    <div class="widget-menu-item" onclick="createWidget('page_analyzer')" style="
                        padding: 10px 15px;
                        color: #333;
                        cursor: pointer;
                        border-bottom: 1px solid #eee;
                    ">📊 Page Analyzer</div>
                    <div class="widget-menu-item" onclick="createWidget('form_filler')" style="
                        padding: 10px 15px;
                        color: #333;
                        cursor: pointer;
                        border-bottom: 1px solid #eee;
                    ">📝 Form Filler</div>
                    <div class="widget-menu-item" onclick="createWidget('translation_tool')" style="
                        padding: 10px 15px;
                        color: #333;
                        cursor: pointer;
                    ">🌐 Translator</div>
                </div>
            </div>
        </div>
        
        <script>
            // Marina Widget System
            (function() {
                const toolbar = document.getElementById('marina-widget-toolbar');
                const menu = document.getElementById('marina-widget-menu');
                const container = document.getElementById('marina-widget-container');
                
                // Show widget container
                container.style.display = 'block';
                
                // Toggle menu
                toolbar.addEventListener('click', function(e) {
                    e.stopPropagation();
                    menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
                });
                
                // Close menu when clicking outside
                document.addEventListener('click', function() {
                    menu.style.display = 'none';
                });
                
                // Widget creation function
                window.createWidget = function(widgetType) {
                    // Send message to Marina to create widget
                    console.log('Creating widget:', widgetType);
                    
                    // This would be implemented by the Spectra system
                    // to communicate with the widget manager
                    
                    menu.style.display = 'none';
                };
                
                // Add hover effects to menu items
                const menuItems = document.querySelectorAll('.widget-menu-item');
                menuItems.forEach(item => {
                    item.addEventListener('mouseenter', function() {
                        this.style.backgroundColor = '#f8f9fa';
                    });
                    item.addEventListener('mouseleave', function() {
                        this.style.backgroundColor = 'white';
                    });
                });
            })();
        </script>
        """


# Example usage
async def main():
    """Example usage of the widget system."""
    from spectra import SpectraCore, SpectraConfig
    
    # Initialize Marina core
    config = SpectraConfig(
        enable_media_perception=True,
        enable_action_validation=True
    )
    marina = SpectraCore(config)
    await marina.initialize()
    
    # Create widget manager
    widget_manager = WidgetManager(marina)
    
    # Create AI assistant widget
    ai_widget_id = await widget_manager.create_widget(WidgetType.AI_ASSISTANT)
    
    # Create page analyzer widget
    analyzer_widget_id = await widget_manager.create_widget(WidgetType.PAGE_ANALYZER)
    
    print(f"Created AI Assistant widget: {ai_widget_id}")
    print(f"Created Page Analyzer widget: {analyzer_widget_id}")
    
    # Get widget list
    widgets = await widget_manager.get_widget_list()
    print(f"Active widgets: {widgets}")
    
    # Cleanup
    await widget_manager.shutdown_all_widgets()
    await marina.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
