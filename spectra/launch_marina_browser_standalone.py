#!/usr/bin/env python3
"""
Standalone Marina Browser Launcher

This script opens a Chromium browser window with Marina's AI-powered widgets
in standalone mode (without requiring the full Marina core to be initialized).
This is used when launching from the GUI.
"""

import subprocess
import sys
import os
import tempfile
import json
import logging
from pathlib import Path
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StandaloneBrowserLauncher:
    """Standalone launcher for Marina-powered Chromium browser."""
    
    def __init__(self):
        self.temp_dir = None
        self.extension_dir = None
        self.chromium_process = None
        
    def find_chromium_executable(self):
        """Find the Chromium executable on the system."""
        possible_paths = [
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/snap/bin/chromium",
            "/opt/google/chrome/chrome",
            shutil.which("chromium-browser"),
            shutil.which("chromium"),
            shutil.which("google-chrome"),
            shutil.which("google-chrome-stable"),
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        
        return None
    
    def create_extension(self):
        """Create the Marina browser extension."""
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix="marina_browser_")
            self.extension_dir = Path(self.temp_dir) / "marina_extension"
            self.extension_dir.mkdir(exist_ok=True)
            
            # Create manifest.json
            manifest = {
                "manifest_version": 3,
                "name": "Marina AI Browser Assistant",
                "version": "1.0.0",
                "description": "AI-powered browsing assistant with intelligent widgets",
                "permissions": ["activeTab", "storage"],
                "content_scripts": [
                    {
                        "matches": ["http://*/*", "https://*/*"],
                        "js": ["content.js"],
                        "css": ["styles.css"],
                        "run_at": "document_end"
                    }
                ],
                "action": {
                    "default_popup": "popup.html",
                    "default_title": "Marina AI"
                },
                "icons": {
                    "16": "icon16.png",
                    "48": "icon48.png",
                    "128": "icon128.png"
                }
            }
            
            with open(self.extension_dir / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            # Create content script (simplified version)
            content_script = """
// Marina AI Browser Assistant - Standalone Version
console.log('Marina content script starting...');

// Simple immediate initialization
(function() {
    'use strict';
    
    console.log('Marina AI Browser Assistant loaded (standalone mode)');
    
    // Force initialization after a short delay
    function initializeMarina() {
        console.log('Initializing Marina widgets...');
        
        // Check if already initialized
        if (document.getElementById('marina-toolbar')) {
            console.log('Marina already initialized');
            return;
        }
        
        // Ensure body exists
        if (!document.body) {
            console.log('Body not ready, retrying...');
            setTimeout(initializeMarina, 100);
            return;
        }
        
        console.log('Creating Marina toolbar...');
        createMarinaToolbar();
        console.log('Marina initialization complete');
    }
    
    function createMarinaToolbar() {
        // Create toolbar directly
        const toolbar = document.createElement('div');
        toolbar.id = 'marina-toolbar';
        toolbar.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10001;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        `;
        
        const button = document.createElement('div');
        button.className = 'marina-button';
        button.textContent = '🤖 Marina AI';
        button.style.cssText = `
            background: #2c3e50;
            color: white;
            padding: 12px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            user-select: none;
            transition: all 0.3s ease;
        `;
        
        // Create menu
        const menu = document.createElement('div');
        menu.id = 'marina-menu';
        menu.style.cssText = `
            position: absolute;
            top: 100%;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            min-width: 220px;
            margin-top: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            overflow: hidden;
            display: none;
            z-index: 10002;
        `;
        
        const menuItems = [
            { icon: '💬', text: 'Chat with Marina', action: 'chat' },
            { icon: '📊', text: 'Page Analyzer', action: 'analyzer' },
            { icon: '📝', text: 'Form Assistant', action: 'forms' },
            { icon: '🔍', text: 'Smart Search', action: 'search' },
            { icon: '🌐', text: 'Page Translator', action: 'translate' },
            { icon: '📷', text: 'Screenshot Tool', action: 'screenshot' },
            { icon: '🎯', text: 'Element Selector', action: 'selector' },
            { icon: '🤖', text: 'AI Assistant', action: 'assistant' },
            { icon: '⚡', text: 'Quick Actions', action: 'actions' }
        ];
        
        menuItems.forEach(item => {
            const menuItem = document.createElement('div');
            menuItem.className = 'marina-menu-item';
            menuItem.innerHTML = `${item.icon} ${item.text}`;
            menuItem.style.cssText = `
                padding: 12px 16px;
                cursor: pointer;
                color: #333;
                border-bottom: 1px solid #f0f0f0;
                transition: background-color 0.2s ease;
                font-size: 14px;
            `;
            
            menuItem.onmouseover = function() {
                this.style.background = '#f8f9fa';
            };
            
            menuItem.onmouseout = function() {
                this.style.background = '';
            };
            
            menuItem.onclick = function() {
                window.marinaWidgets.createWidget(item.action);
                menu.style.display = 'none';
            };
            
            menu.appendChild(menuItem);
        });
        
        button.onclick = function() {
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        };
        
        toolbar.appendChild(button);
        toolbar.appendChild(menu);
        document.body.appendChild(toolbar);
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!toolbar.contains(e.target)) {
                menu.style.display = 'none';
            }
        });
        
        console.log('Marina toolbar created and added to page');
    }
    
    // Multiple initialization attempts
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeMarina);
    } else {
        initializeMarina();
    }
    
    // Backup initialization
    setTimeout(initializeMarina, 500);
    setTimeout(initializeMarina, 1000);
    setTimeout(initializeMarina, 2000);
    
    // Simple widget system
    class MarinaWidgets {
        constructor() {
            this.init();
        }
        
        init() {
            this.createToolbar();
        }
        
        createToolbar() {
            const toolbar = document.createElement('div');
            toolbar.id = 'marina-toolbar';
            toolbar.innerHTML = `
                <div class="marina-button" onclick="marinaWidgets.toggleMenu()">
                    🤖 Marina AI
                </div>
                <div class="marina-menu" id="marina-menu" style="display: none;">
                    <div class="marina-menu-item" onclick="marinaWidgets.createWidget('assistant')">
                        🤖 AI Assistant
                    </div>
                    <div class="marina-menu-item" onclick="marinaWidgets.createWidget('analyzer')">
                        📊 Page Analyzer
                    </div>
                    <div class="marina-menu-item" onclick="marinaWidgets.createWidget('forms')">
                        📝 Form Helper
                    </div>
                    <div class="marina-menu-item" onclick="marinaWidgets.createWidget('translate')">
                        🌐 Translator
                    </div>
                    <div class="marina-menu-item" onclick="marinaWidgets.createWidget('chat')">
                        💬 Chat with Marina
                    </div>
                </div>
            `;
            document.body.appendChild(toolbar);
        }
        
        toggleMenu() {
            const menu = document.getElementById('marina-menu');
            menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
        }
        
        createWidget(type) {
            const widget = document.createElement('div');
            widget.className = 'marina-widget';
            widget.innerHTML = this.getWidgetHTML(type);
            
            // Position widget
            const existingWidgets = document.querySelectorAll('.marina-widget');
            const offset = existingWidgets.length * 30;
            widget.style.cssText = `
                position: fixed;
                top: ${100 + offset}px;
                right: ${100 + offset}px;
                width: 300px;
                height: 400px;
                background: white;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                z-index: 10000;
                resize: both;
                overflow: hidden;
            `;
            
            document.body.appendChild(widget);
            this.hideMenu();
            this.makeDraggable(widget);
        }
        
        getWidgetHTML(type) {
            const widgets = {
                assistant: `
                    <div class="widget-header">
                        🤖 AI Assistant
                        <button onclick="this.closest('.marina-widget').remove()">×</button>
                    </div>
                    <div class="widget-content">
                        <div class="chat-area">
                            <div class="chat-messages">
                                <div class="ai-message">Hello! I'm your AI assistant. How can I help you browse this page?</div>
                            </div>
                            <div class="chat-input">
                                <input type="text" placeholder="Ask me anything..." onkeypress="if(event.key==='Enter') this.nextSibling.click()">
                                <button onclick="this.previousSibling.value=''; this.parentElement.previousSibling.innerHTML+='<div class=user-message>'+this.previousSibling.value+'</div><div class=ai-message>I can help you analyze this page, fill forms, or answer questions about the content.</div>'">Send</button>
                            </div>
                        </div>
                    </div>
                `,
                analyzer: `
                    <div class="widget-header">
                        📊 Page Analyzer
                        <button onclick="this.closest('.marina-widget').remove()">×</button>
                    </div>
                    <div class="widget-content">
                        <button onclick="this.nextSibling.innerHTML='<p>Page Title: '+document.title+'</p><p>Links: '+document.links.length+'</p><p>Images: '+document.images.length+'</p><p>Forms: '+document.forms.length+'</p>'">Analyze Page</button>
                        <div class="analysis-results">Click the button above to analyze this page</div>
                    </div>
                `,
                forms: `
                    <div class="widget-header">
                        📝 Form Helper
                        <button onclick="this.closest('.marina-widget').remove()">×</button>
                    </div>
                    <div class="widget-content">
                        <button onclick="this.nextSibling.innerHTML='<p>Forms found: '+document.forms.length+'</p>'; Array.from(document.forms).forEach((form,i) => this.nextSibling.innerHTML+='<p>Form '+(i+1)+': '+form.elements.length+' fields</p>')">Detect Forms</button>
                        <div class="form-info">No forms detected yet</div>
                    </div>
                `,
                translate: `
                    <div class="widget-header">
                        🌐 Translator
                        <button onclick="this.closest('.marina-widget').remove()">×</button>
                    </div>
                    <div class="widget-content">
                        <select id="lang-select">
                            <option value="es">Spanish</option>
                            <option value="fr">French</option>
                            <option value="de">German</option>
                            <option value="it">Italian</option>
                        </select>
                        <button onclick="alert('Translation feature would be implemented here')">Translate Page</button>
                    </div>
                `,
                chat: `
                    <div class="widget-header">
                        💬 Chat with Marina
                        <button onclick="this.closest('.marina-widget').remove()">×</button>
                    </div>
                    <div class="widget-content">
                        <div class="marina-chat-container">
                            <div class="marina-chat-status" id="marina-chat-status">
                                <span class="status-indicator offline">•</span>
                                Marina AI (Standalone Mode)
                            </div>
                            <div class="marina-chat-messages" id="marina-chat-messages">
                                <div class="marina-message marina-ai">
                                    <div class="message-avatar">🤖</div>
                                    <div class="message-content">
                                        <div class="message-text">Hello! I'm Marina, your AI browsing assistant. I can help you:</div>
                                        <div class="message-text">• Analyze this webpage</div>
                                        <div class="message-text">• Fill out forms</div>
                                        <div class="message-text">• Extract information</div>
                                        <div class="message-text">• Navigate websites</div>
                                        <div class="message-text">• Answer questions about content</div>
                                        <div class="message-time"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="marina-chat-input">
                                <input type="text" id="marina-chat-input" placeholder="Ask Marina anything about this page..." onkeypress="if(event.key==='Enter') this.nextElementSibling.click()">
                                <button id="marina-chat-send" onclick="window.marinaChat.sendMessage()">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M2 21L23 12L2 3V10L17 12L2 14V21Z" fill="currentColor"/>
                                    </svg>
                                </button>
                            </div>
                        </div>
                    </div>
                `,
                search: `
                    <div class="widget-header">
                        🔍 Smart Search
                        <button onclick="this.closest('.marina-widget').remove()">×</button>
                    </div>
                    <div class="widget-content">
                        <div class="search-controls">
                            <input type="text" id="search-query" placeholder="Search this page or the web..." style="width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            <div class="search-buttons">
                                <button onclick="this.closest('.widget-content').querySelector('.search-results').innerHTML = 'Searching page...'; setTimeout(() => { const query = this.closest('.widget-content').querySelector('#search-query').value; const results = document.body.innerText.toLowerCase().split(query.toLowerCase()).length - 1; this.closest('.widget-content').querySelector('.search-results').innerHTML = '<p>Found ' + results + ' matches for: ' + query + '</p>'; }, 500);">🔍 Search Page</button>
                                <button onclick="const query = this.closest('.widget-content').querySelector('#search-query').value; if(query) window.open('https://www.google.com/search?q=' + encodeURIComponent(query), '_blank');">🌐 Web Search</button>
                            </div>
                        </div>
                        <div class="search-results">Enter a search query above</div>
                    </div>
                `,
                screenshot: `
                    <div class="widget-header">
                        📷 Screenshot Tool
                        <button onclick="this.closest('.marina-widget').remove()">×</button>
                    </div>
                    <div class="widget-content">
                        <div class="screenshot-controls">
                            <button onclick="this.nextElementSibling.innerHTML = '<p>Capturing visible area...</p>'; setTimeout(() => { this.nextElementSibling.innerHTML = '<p>Screenshot captured! (In full version, this would save/download the image)</p>'; }, 1000);">📸 Capture Visible Area</button>
                            <button onclick="this.parentElement.nextElementSibling.innerHTML = '<p>Capturing full page...</p>'; setTimeout(() => { this.parentElement.nextElementSibling.innerHTML = '<p>Full page screenshot captured!</p>'; }, 1500);">📄 Full Page Screenshot</button>
                            <button onclick="this.parentElement.nextElementSibling.innerHTML = '<p>Click and drag to select an area to capture</p>';">🎯 Select Area</button>
                        </div>
                        <div class="screenshot-status">Ready to capture screenshots</div>
                    </div>
                `,
                selector: `
                    <div class="widget-header">
                        🎯 Element Selector
                        <button onclick="this.closest('.marina-widget').remove()">×</button>
                    </div>
                    <div class="widget-content">
                        <div class="selector-controls">
                            <button onclick="window.marinaSelector.toggleSelector()">🎯 Toggle Element Selector</button>
                            <button onclick="window.marinaSelector.highlightLinks()">🔗 Highlight All Links</button>
                            <button onclick="window.marinaSelector.highlightImages()">🖼️ Highlight All Images</button>
                            <button onclick="window.marinaSelector.clearHighlights()">🧹 Clear Highlights</button>
                        </div>
                        <div class="selector-info">Click elements to inspect them</div>
                    </div>
                `,
                actions: `
                    <div class="widget-header">
                        ⚡ Quick Actions
                        <button onclick="this.closest('.marina-widget').remove()">×</button>
                    </div>
                    <div class="widget-content">
                        <div class="quick-actions">
                            <button onclick="window.scrollTo(0, 0);">⬆️ Scroll to Top</button>
                            <button onclick="window.scrollTo(0, document.body.scrollHeight);">⬇️ Scroll to Bottom</button>
                            <button onclick="window.print();">🖨️ Print Page</button>
                            <button onclick="navigator.clipboard.writeText(window.location.href); alert('URL copied to clipboard!');">📋 Copy URL</button>
                            <button onclick="const title = document.title; const url = window.location.href; navigator.clipboard.writeText('[' + title + '](' + url + ')'); alert('Page info copied in markdown format!');">📝 Copy as Markdown</button>
                            <button onclick="document.querySelectorAll('img').forEach(img => img.style.display = img.style.display === 'none' ? '' : 'none');">🖼️ Toggle Images</button>
                            <button onclick="const darkMode = document.body.style.filter === 'invert(1) hue-rotate(180deg)'; document.body.style.filter = darkMode ? '' : 'invert(1) hue-rotate(180deg)';">🌙 Dark Mode</button>
                            <button onclick="const size = document.body.style.fontSize || '16px'; const current = parseInt(size); document.body.style.fontSize = (current + 2) + 'px';">🔍 Zoom In</button>
                            <button onclick="const size = document.body.style.fontSize || '16px'; const current = parseInt(size); document.body.style.fontSize = Math.max(current - 2, 10) + 'px';">🔍 Zoom Out</button>
                        </div>
                    </div>
                `
            };
            
            return widgets[type] || widgets.assistant;
        }
        
        makeDraggable(element) {
            const header = element.querySelector('.widget-header');
            let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
            
            header.onmousedown = (e) => {
                e = e || window.event;
                e.preventDefault();
                pos3 = e.clientX;
                pos4 = e.clientY;
                document.onmouseup = () => {
                    document.onmouseup = null;
                    document.onmousemove = null;
                };
                document.onmousemove = (e) => {
                    e = e || window.event;
                    e.preventDefault();
                    pos1 = pos3 - e.clientX;
                    pos2 = pos4 - e.clientY;
                    pos3 = e.clientX;
                    pos4 = e.clientY;
                    element.style.top = (element.offsetTop - pos2) + "px";
                    element.style.left = (element.offsetLeft - pos1) + "px";
                };
            };
        }
        
        hideMenu() {
            document.getElementById('marina-menu').style.display = 'none';
        }
    }
    
    // Initialize Marina widgets
    const marinaWidgets = new MarinaWidgets();
    window.marinaWidgets = marinaWidgets;
    
    // Marina Chat System
    class MarinaChat {
        constructor() {
            this.isConnected = false;
            this.conversationHistory = [];
            this.currentWidget = null;
        }
        
        init(widget) {
            this.currentWidget = widget;
            this.setupEventListeners();
            this.updateConnectionStatus();
        }
        
        setupEventListeners() {
            if (!this.currentWidget) return;
            
            const input = this.currentWidget.querySelector('#marina-chat-input');
            const sendButton = this.currentWidget.querySelector('#marina-chat-send');
            
            if (input) {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.sendMessage();
                    }
                });
            }
            
            if (sendButton) {
                sendButton.addEventListener('click', () => {
                    this.sendMessage();
                });
            }
        }
        
        sendMessage() {
            if (!this.currentWidget) return;
            
            const input = this.currentWidget.querySelector('#marina-chat-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            this.addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            this.showTypingIndicator();
            
            // Simulate AI response after delay
            setTimeout(() => {
                this.hideTypingIndicator();
                this.handleAIResponse(message);
            }, 1000 + Math.random() * 1000);
        }
        
        addMessage(text, sender) {
            if (!this.currentWidget) return;
            
            const messagesContainer = this.currentWidget.querySelector('#marina-chat-messages');
            if (!messagesContainer) return;
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `marina-message marina-${sender}`;
            
            const avatar = sender === 'user' ? '👤' : '🤖';
            const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    <div class="message-text">${text}</div>
                    <div class="message-time">${timestamp}</div>
                </div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            
            // Store in conversation history
            this.conversationHistory.push({
                text: text,
                sender: sender,
                timestamp: Date.now()
            });
        }
        
        showTypingIndicator() {
            if (!this.currentWidget) return;
            
            const messagesContainer = this.currentWidget.querySelector('#marina-chat-messages');
            if (!messagesContainer) return;
            
            const typingDiv = document.createElement('div');
            typingDiv.className = 'marina-message marina-ai typing-indicator-message';
            typingDiv.innerHTML = `
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="typing-indicator">
                        Marina is typing
                        <div class="typing-dots">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                    </div>
                </div>
            `;
            
            messagesContainer.appendChild(typingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        hideTypingIndicator() {
            if (!this.currentWidget) return;
            
            const typingIndicator = this.currentWidget.querySelector('.typing-indicator-message');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }
        
        handleAIResponse(userMessage) {
            const responses = this.generateResponse(userMessage);
            
            responses.forEach((response, index) => {
                setTimeout(() => {
                    this.addMessage(response, 'ai');
                }, index * 500);
            });
        }
        
        generateResponse(userMessage) {
            const message = userMessage.toLowerCase();
            
            // Page analysis responses
            if (message.includes('analyze') || message.includes('page') || message.includes('website')) {
                return [
                    `I'll analyze this page for you!`,
                    `Page Title: "${document.title}"`,
                    `URL: ${window.location.href}`,
                    `The page contains ${document.links.length} links, ${document.images.length} images, and ${document.forms.length} forms.`,
                    `Would you like me to analyze any specific aspect in more detail?`
                ];
            }
            
            // Form-related responses
            if (message.includes('form') || message.includes('fill')) {
                const forms = document.forms.length;
                if (forms > 0) {
                    return [
                        `I found ${forms} form(s) on this page.`,
                        `I can help you fill them out or analyze their structure.`,
                        `Would you like me to highlight the forms or provide filling assistance?`
                    ];
                } else {
                    return [`I don't see any forms on this page. Is there something specific you'd like me to help you with?`];
                }
            }
            
            // Navigation responses
            if (message.includes('navigate') || message.includes('go to') || message.includes('visit')) {
                return [
                    `I can help you navigate to different pages!`,
                    `Just tell me where you'd like to go or what you're looking for.`,
                    `I can also help you find specific elements on the current page.`
                ];
            }
            
            // Search responses
            if (message.includes('search') || message.includes('find')) {
                return [
                    `I can help you search for information on this page or navigate to search engines.`,
                    `What would you like to search for?`
                ];
            }
            
            // Help responses
            if (message.includes('help') || message.includes('what can you do')) {
                return [
                    `I'm Marina, your AI browsing assistant! I can help you with:`,
                    `• Analyzing web pages and extracting information`,
                    `• Filling out forms automatically`,
                    `• Navigating websites and finding content`,
                    `• Translating page content`,
                    `• Answering questions about what you see`,
                    `• Performing web searches and research`,
                    `What would you like to try?`
                ];
            }
            
            // Translation responses
            if (message.includes('translate') || message.includes('translation')) {
                return [
                    `I can help translate this page or selected text.`,
                    `What language would you like to translate to?`,
                    `You can also use the Translation widget for more options.`
                ];
            }
            
            // General responses
            const generalResponses = [
                `That's interesting! I can help you explore this page further.`,
                `I'm here to assist with your browsing needs. What would you like to do?`,
                `Let me know how I can help you with this webpage.`,
                `I can analyze this page, help with forms, or answer questions about the content.`,
                `Would you like me to analyze this page or help you with something specific?`
            ];
            
            return [generalResponses[Math.floor(Math.random() * generalResponses.length)]];
        }
        
        updateConnectionStatus() {
            if (!this.currentWidget) return;
            
            const statusElement = this.currentWidget.querySelector('#marina-chat-status');
            const indicator = this.currentWidget.querySelector('.status-indicator');
            
            if (statusElement && indicator) {
                if (this.isConnected) {
                    statusElement.innerHTML = '<span class="status-indicator online">•</span> Marina AI (Connected)';
                } else {
                    statusElement.innerHTML = '<span class="status-indicator offline">•</span> Marina AI (Standalone Mode)';
                }
            }
        }
    }
    
    // Element Selector System
    class MarinaSelector {
        constructor() {
            this.isActive = false;
            this.highlightedElements = [];
            this.originalStyles = new Map();
        }
        
        toggleSelector() {
            this.isActive = !this.isActive;
            
            if (this.isActive) {
                this.enableSelector();
            } else {
                this.disableSelector();
            }
        }
        
        enableSelector() {
            document.body.style.cursor = 'crosshair';
            document.addEventListener('click', this.handleElementClick.bind(this));
            document.addEventListener('mouseover', this.handleElementHover.bind(this));
            document.addEventListener('mouseout', this.handleElementOut.bind(this));
        }
        
        disableSelector() {
            document.body.style.cursor = '';
            document.removeEventListener('click', this.handleElementClick.bind(this));
            document.removeEventListener('mouseover', this.handleElementHover.bind(this));
            document.removeEventListener('mouseout', this.handleElementOut.bind(this));
        }
        
        handleElementClick(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const element = e.target;
            this.inspectElement(element);
        }
        
        handleElementHover(e) {
            if (!this.isActive) return;
            
            const element = e.target;
            if (element.closest('.marina-widget') || element.closest('#marina-toolbar')) return;
            
            element.style.outline = '2px solid #007bff';
            element.style.backgroundColor = 'rgba(0, 123, 255, 0.1)';
        }
        
        handleElementOut(e) {
            if (!this.isActive) return;
            
            const element = e.target;
            if (element.closest('.marina-widget') || element.closest('#marina-toolbar')) return;
            
            element.style.outline = '';
            element.style.backgroundColor = '';
        }
        
        inspectElement(element) {
            const tagName = element.tagName.toLowerCase();
            const id = element.id ? `#${element.id}` : '';
            const classes = element.className ? `.${element.className.split(' ').join('.')}` : '';
            const text = element.textContent ? element.textContent.substring(0, 50) + '...' : '';
            
            alert(`Element Info:\nTag: ${tagName}\nID: ${id}\nClasses: ${classes}\nText: ${text}`);
        }
        
        highlightLinks() {
            this.clearHighlights();
            const links = document.querySelectorAll('a');
            
            links.forEach(link => {
                this.originalStyles.set(link, {
                    outline: link.style.outline,
                    backgroundColor: link.style.backgroundColor
                });
                
                link.style.outline = '2px solid #28a745';
                link.style.backgroundColor = 'rgba(40, 167, 69, 0.1)';
                this.highlightedElements.push(link);
            });
        }
        
        highlightImages() {
            this.clearHighlights();
            const images = document.querySelectorAll('img');
            
            images.forEach(img => {
                this.originalStyles.set(img, {
                    outline: img.style.outline,
                    backgroundColor: img.style.backgroundColor
                });
                
                img.style.outline = '2px solid #dc3545';
                img.style.backgroundColor = 'rgba(220, 53, 69, 0.1)';
                this.highlightedElements.push(img);
            });
        }
        
        clearHighlights() {
            this.highlightedElements.forEach(element => {
                const originalStyle = this.originalStyles.get(element);
                if (originalStyle) {
                    element.style.outline = originalStyle.outline;
                    element.style.backgroundColor = originalStyle.backgroundColor;
                }
            });
            
            this.highlightedElements = [];
            this.originalStyles.clear();
        }
    }
    
    // Initialize Marina widgets
    const marinaWidgets = new MarinaWidgets();
    const marinaChat = new MarinaChat();
    const marinaSelector = new MarinaSelector();
    
    window.marinaWidgets = marinaWidgets;
    window.marinaChat = marinaChat;
    window.marinaSelector = marinaSelector;
    
    // Override widget creation to initialize chat functionality
    const originalCreateWidget = marinaWidgets.createWidget.bind(marinaWidgets);
    marinaWidgets.createWidget = function(type) {
        originalCreateWidget(type);
        
        if (type === 'chat') {
            // Find the most recently created chat widget
            const chatWidgets = document.querySelectorAll('.marina-widget');
            const latestWidget = chatWidgets[chatWidgets.length - 1];
            
            if (latestWidget && latestWidget.querySelector('#marina-chat-input')) {
                setTimeout(() => {
                    marinaChat.init(latestWidget);
                }, 100);
            }
        }
    };
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#marina-toolbar')) {
            marinaWidgets.hideMenu();
        }
    });
    
})();
"""
            
            with open(self.extension_dir / "content.js", "w") as f:
                f.write(content_script)
            
            # Create CSS styles
            css_styles = """
/* Marina AI Browser Assistant Styles */
#marina-toolbar {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10001;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.marina-button {
    background: #2c3e50;
    color: white;
    padding: 12px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    user-select: none;
    transition: all 0.3s ease;
}

.marina-button:hover {
    background: #34495e;
    transform: translateY(-1px);
}

.marina-menu {
    position: absolute;
    top: 100%;
    right: 0;
    background: white;
    border: 1px solid #ddd;
    border-radius: 6px;
    min-width: 200px;
    margin-top: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    overflow: hidden;
}

.marina-menu-item {
    padding: 12px 16px;
    cursor: pointer;
    color: #333;
    border-bottom: 1px solid #f0f0f0;
    transition: background-color 0.2s ease;
}

.marina-menu-item:hover {
    background: #f8f9fa;
}

.marina-menu-item:last-child {
    border-bottom: none;
}

.marina-widget {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.widget-header {
    background: #2c3e50;
    color: white;
    padding: 10px 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: move;
    user-select: none;
    font-weight: 600;
    font-size: 14px;
}

.widget-header button {
    background: rgba(255,255,255,0.2);
    border: none;
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    transition: background 0.2s ease;
}

.widget-header button:hover {
    background: rgba(255,255,255,0.3);
}

.widget-content {
    padding: 15px;
    height: calc(100% - 44px);
    overflow-y: auto;
    background: white;
}

.chat-area {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 4px;
    margin-bottom: 10px;
}

.ai-message, .user-message {
    margin-bottom: 10px;
    padding: 8px 12px;
    border-radius: 8px;
    max-width: 80%;
}

.ai-message {
    background: #e9ecef;
    color: #333;
}

.user-message {
    background: #007bff;
    color: white;
    margin-left: auto;
}

.chat-input {
    display: flex;
    gap: 8px;
}

.chat-input input {
    flex: 1;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.chat-input button, .widget-content button {
    padding: 8px 16px;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    transition: background 0.2s ease;
}

.chat-input button:hover, .widget-content button:hover {
    background: #0056b3;
}

.analysis-results, .form-info {
    margin-top: 10px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 4px;
    min-height: 100px;
}

select {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    margin-bottom: 10px;
}

/* Marina Chat Widget Styles */
.marina-chat-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.marina-chat-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: #f8f9fa;
    border-radius: 4px;
    margin-bottom: 12px;
    font-size: 12px;
    color: #666;
}

.status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}

.status-indicator.online {
    background: #28a745;
}

.status-indicator.offline {
    background: #dc3545;
}

.marina-chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-bottom: 12px;
    max-height: 280px;
}

.marina-message {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    animation: fadeIn 0.3s ease-in;
}

.marina-message.marina-user {
    flex-direction: row-reverse;
}

.message-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
}

.marina-ai .message-avatar {
    background: #e3f2fd;
}

.marina-user .message-avatar {
    background: #f3e5f5;
}

.message-content {
    flex: 1;
    max-width: 85%;
}

.message-text {
    background: #f8f9fa;
    padding: 8px 12px;
    border-radius: 12px;
    margin-bottom: 4px;
    line-height: 1.4;
    font-size: 14px;
    color: #333;
    word-wrap: break-word;
}

.marina-user .message-text {
    background: #007bff;
    color: white;
    margin-left: auto;
}

.message-time {
    font-size: 11px;
    color: #999;
    margin-top: 4px;
    padding-left: 12px;
}

.marina-chat-input {
    display: flex;
    gap: 8px;
    align-items: center;
}

.marina-chat-input input {
    flex: 1;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 20px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s ease;
}

.marina-chat-input input:focus {
    border-color: #007bff;
}

.marina-chat-input button {
    width: 40px;
    height: 40px;
    border: none;
    border-radius: 50%;
    background: #007bff;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s ease;
}

.marina-chat-input button:hover {
    background: #0056b3;
}

.marina-chat-input button:active {
    transform: scale(0.95);
}

.marina-chat-input button svg {
    width: 16px;
    height: 16px;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Typing indicator */
.typing-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 8px 12px;
    background: #f8f9fa;
    border-radius: 12px;
    margin-bottom: 4px;
    font-size: 14px;
    color: #666;
}

.typing-dots {
    display: flex;
    gap: 2px;
}

.typing-dot {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #999;
    animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%, 60%, 100% { opacity: 0.3; }
    30% { opacity: 1; }
}
"""
            
            with open(self.extension_dir / "styles.css", "w") as f:
                f.write(css_styles)
            
            # Create popup HTML
            popup_html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            width: 300px;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .logo {
            font-size: 24px;
            margin-bottom: 10px;
        }
        .title {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
        }
        .subtitle {
            color: #7f8c8d;
            font-size: 14px;
        }
        .info {
            background: #e8f4f8;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
        }
        .instructions {
            font-size: 14px;
            line-height: 1.5;
            color: #555;
        }
        .status {
            margin-top: 15px;
            padding: 10px;
            background: #e8f5e8;
            border-radius: 4px;
            font-size: 12px;
            text-align: center;
            color: #2d5a2d;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🤖</div>
        <div class="title">Marina AI</div>
        <div class="subtitle">Browser Assistant</div>
    </div>
    
    <div class="info">
        <div class="instructions">
            <strong>How to use:</strong><br>
            1. Look for the Marina AI button in the top-right corner of any webpage<br>
            2. Click it to open the widget menu<br>
            3. Select the widget you want to use<br>
            4. Drag widgets around by their header
        </div>
    </div>
    
    <div class="status">
        Marina AI is active and ready to help!
    </div>
</body>
</html>
"""
            
            with open(self.extension_dir / "popup.html", "w") as f:
                f.write(popup_html)
            
            # Create placeholder icon files
            icon_content = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77mgAAAABJRU5ErkJggg=="
            for size in [16, 48, 128]:
                with open(self.extension_dir / f"icon{size}.png", "wb") as f:
                    f.write(b"")  # Empty file for now
            
            logger.info(f"Created Marina extension at {self.extension_dir}")
            return str(self.extension_dir)
            
        except Exception as e:
            logger.error(f"Failed to create extension: {e}")
            raise
    
    def launch_chromium(self, extension_path):
        """Launch Chromium with the Marina extension."""
        try:
            chromium_path = self.find_chromium_executable()
            if not chromium_path:
                raise RuntimeError("Chromium not found. Please install Chromium or Google Chrome.")
            
            # Create user data directory
            user_data_dir = Path(self.temp_dir) / "chrome_profile"
            user_data_dir.mkdir(exist_ok=True)
            
            # Prepare launch arguments
            args = [
                chromium_path,
                f"--load-extension={extension_path}",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "https://www.google.com"
            ]
            
            logger.info(f"Launching Chromium with Marina extension...")
            
            # Launch Chromium
            self.chromium_process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info("Chromium launched successfully!")
            logger.info("Look for the '🤖 Marina AI' button in the top-right corner of web pages")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch Chromium: {e}")
            return False
    
    def run(self):
        """Main entry point."""
        try:
            logger.info("Starting Marina Browser (Standalone)...")
            
            # Create extension
            extension_path = self.create_extension()
            
            # Launch Chromium
            success = self.launch_chromium(extension_path)
            
            if success:
                # Wait for Chromium to close
                if self.chromium_process:
                    self.chromium_process.wait()
                    logger.info("Chromium closed")
            else:
                logger.error("Failed to launch Marina browser")
                
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
        finally:
            self.cleanup()
        
        return True
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main function."""
    try:
        launcher = StandaloneBrowserLauncher()
        success = launcher.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Marina browser interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Marina browser failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
