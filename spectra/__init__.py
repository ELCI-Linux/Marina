#!/usr/bin/env python3
"""
Spectra - Marina's Autonomous Browser System

A comprehensive autonomous browsing system that processes natural language intents
and executes them through intelligent web automation with advanced coordination.
"""

__version__ = "1.0.0"
__codename__ = "Spectra"
__author__ = "Marina Development Team"
__description__ = "Autonomous Browser System with AI-Powered Intent Processing"

# Core components
from .spectra_core import (
    SpectraCore,
    SpectraConfig,
    SpectraMode,
    ComponentStatus,
    ExecutionPriority,
    ExecutionResult,
    ExecutionContext,
    load_config
)

# Individual modules
from .navigation_core import NavigatorCore, NavigationMode
from .action_validator import ActionValidator, ValidationResult
from .media_perception import MediaPerceptionEngine, MediaAnalysis, MediaType
from .intent_compiler import IntentCompiler, Intent, IntentType, ExecutionStatus
from .session_manager import SessionManager, BrowsingSession, SessionType, SessionStatus

# Version information
VERSION_INFO = {
    'major': 1,
    'minor': 0,
    'patch': 0,
    'pre_release': None
}

# Component status
COMPONENTS = {
    'navigation_core': 'Core web navigation and automation engine',
    'action_validator': 'Action success/failure validation system',
    'media_perception': 'Visual and audio content analysis engine',
    'intent_compiler': 'Natural language intent processing system',
    'session_manager': 'Persistent session and state management',
    'spectra_core': 'Main integration and orchestration layer'
}

# Supported browsers
SUPPORTED_BROWSERS = {
    'chromium': 'Google Chrome/Chromium',
    'firefox': 'Mozilla Firefox',
    'webkit': 'Safari/WebKit (limited support)'
}

# Feature flags
FEATURES = {
    'headless_mode': True,
    'visual_validation': True,
    'media_analysis': True,
    'session_persistence': True,
    'intent_compilation': True,
    'multi_browser_support': True,
    'stealth_mode': True,
    'proxy_support': True,
    'api_integration': True,
    'webhook_support': True,
    'metrics_collection': True
}

# Export all public APIs
__all__ = [
    # Core classes
    'SpectraCore',
    'SpectraConfig',
    'SpectraMode',
    'ComponentStatus',
    'ExecutionPriority',
    'ExecutionResult',
    'ExecutionContext',
    
    # Component classes
    'NavigatorCore',
    'ActionValidator',
    'MediaPerceptionEngine',
    'IntentCompiler',
    'SessionManager',
    
    # Enum classes
    'NavigationMode',
    'ValidationResult',
    'MediaAnalysis',
    'MediaType',
    'Intent',
    'IntentType',
    'ExecutionStatus',
    'BrowsingSession',
    'SessionType',
    'SessionStatus',
    
    # Utility functions
    'load_config',
    
    # Constants
    'VERSION_INFO',
    'COMPONENTS',
    'SUPPORTED_BROWSERS',
    'FEATURES',
    '__version__',
    '__codename__',
    '__author__',
    '__description__'
]

# Welcome message
def get_welcome_message():
    """Get the welcome message for Spectra."""
    return f"""
    🚀 Spectra v{__version__} - Marina's Autonomous Browser System
    
    Components loaded:
    {chr(10).join(f'    ✓ {name}: {desc}' for name, desc in COMPONENTS.items())}
    
    Supported browsers: {', '.join(SUPPORTED_BROWSERS.keys())}
    
    Ready for autonomous browsing! 🌐
    """

# Quick start function
def quick_start(config_path: str = None):
    """
    Quick start function to initialize Spectra with minimal configuration.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Initialized SpectraCore instance
    """
    if config_path:
        config = load_config(config_path)
    else:
        config = SpectraConfig()
    
    return SpectraCore(config)

# Initialize logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Print welcome message when imported
if __name__ != '__main__':
    print(get_welcome_message())
