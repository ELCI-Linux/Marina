#!/usr/bin/env python3
"""
Marina Browser Launcher

This script opens a Chromium browser window with Marina's AI-powered widgets
enabled and rendered. It integrates with the Spectra browser system to provide
an enhanced browsing experience.
"""

import asyncio
import subprocess
import sys
import os
import tempfile
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import shutil

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import Marina components
from spectra import SpectraCore, SpectraConfig, SpectraMode
from spectra.browser_widgets import WidgetManager, WidgetType, WidgetPosition, WidgetConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarinaBrowserLauncher:
    """Launcher for Marina-powered Chromium browser with widgets."""
    
    def __init__(self):
        self.temp_dir = None
        self.extension_dir = None
        self.marina_core = None
        self.widget_manager = None
        self.chromium_process = None
        
    async def initialize(self):
        """Initialize Marina core and widget system."""
        try:
            # Create Spectra configuration
            config = SpectraConfig(
                mode=SpectraMode.AUTONOMOUS,
                max_concurrent_sessions=3,
                default_timeout=300.0,
                enable_media_perception=True,
                enable_action_validation=True,
                enable_session_persistence=True,
                storage_dir="./spectra_data",
                encrypt_sessions=True,
                sandbox_mode=True
            )
            
            # Initialize Marina core
            self.marina_core = SpectraCore(config)
            await self.marina_core.initialize()
            
            # Initialize widget manager
            self.widget_manager = WidgetManager(self.marina_core)
            
            logger.info("Marina core initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Marina core: {e}")
            raise
    
    def create_browser_extension(self):
        """Create a browser extension for Marina widgets."""
        try:
            # Create temporary directory for the extension
            self.temp_dir = tempfile.mkdtemp(prefix="marina_extension_")
            self.extension_dir = Path(self.temp_dir) / "marina_extension"
            self.extension_dir.mkdir(exist_ok=True)
            
            # Path to existing marina_extension directory
            existing_extension_dir = Path(__file__).parent.parent / "marina_extension"
            
            # Copy existing icon files if they exist
            for icon_file in ["icon16.png", "icon48.png", "icon128.png"]:
                src_icon = existing_extension_dir / icon_file
                dst_icon = self.extension_dir / icon_file
                if src_icon.exists():
                    shutil.copy2(src_icon, dst_icon)
                    logger.info(f"Copied {icon_file} from existing extension")
                else:
                    # Create a minimal PNG file as fallback
                    self._create_placeholder_icon(dst_icon)
            
            # Copy other necessary files from existing extension
            for file_name in ["options.html", "sidepanel.html", "sidepanel.js", "popup.js", "options.js"]:
                src_file = existing_extension_dir / file_name
                dst_file = self.extension_dir / file_name
                if src_file.exists():
                    shutil.copy2(src_file, dst_file)
                    logger.info(f"Copied {file_name} from existing extension")
            
            # Create manifest.json with enhanced permissions
            manifest = {
                "manifest_version": 3,
                "name": "Marina AI Browser Assistant",
                "version": "1.0.0",
                "description": "AI-powered browser widgets for enhanced browsing experience",
                "permissions": [
                    "activeTab",
                    "storage",
                    "scripting",
                    "tabs",
                    "contextMenus",
                    "bookmarks",
                    "history",
                    "downloads"
                ],
                "host_permissions": ["http://*/*", "https://*/*"],
                "content_scripts": [{
                    "matches": ["http://*/*", "https://*/*"],
                    "js": ["content.js"],
                    "css": ["styles.css"],
                    "run_at": "document_end"
                }],
                "background": {
                    "service_worker": "background.js"
                },
                "action": {
                    "default_popup": "popup.html",
                    "default_title": "Marina AI Assistant",
                    "default_icon": {
                        "16": "icon16.png",
                        "48": "icon48.png",
                        "128": "icon128.png"
                    }
                },
                "options_page": "options.html",
                "side_panel": {
                    "default_path": "sidepanel.html"
                },
                "icons": {
                    "16": "icon16.png",
                    "48": "icon48.png",
                    "128": "icon128.png"
                }
            }
            
            with open(self.extension_dir / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)
            
            # Create minimal content script
            content_script = '''
// Marina Browser Widget Content Script
(function() {
    'use strict';
    
    console.log('Marina AI Browser Assistant loaded');
    
    // Create the main Marina toolbar
    const toolbar = document.createElement('div');
    toolbar.id = 'marina-toolbar';
    toolbar.innerHTML = `
        <div style="position: fixed; top: 20px; right: 20px; z-index: 10001; background: #2c3e50; color: white; padding: 10px 15px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500; box-shadow: 0 2px 10px rgba(0,0,0,0.2); user-select: none; transition: all 0.3s ease; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
            🤖 Marina AI
        </div>
    `;
    
    document.body.appendChild(toolbar);
    
    // Add click handler
    toolbar.addEventListener('click', () => {
        alert('Marina AI Browser Assistant is active!');
    });
})();
'''
            
            with open(self.extension_dir / "content.js", "w") as f:
                f.write(content_script)
            
            # Create minimal CSS
            css_content = '''
/* Marina AI Browser Assistant Styles */
#marina-toolbar {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10001;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
'''
            
            with open(self.extension_dir / "styles.css", "w") as f:
                f.write(css_content)
            
            # Create minimal background script
            background_script = '''
// Marina Browser Extension Background Script
chrome.runtime.onInstalled.addListener(() => {
    console.log('Marina AI Browser Assistant installed');
});
'''
            
            with open(self.extension_dir / "background.js", "w") as f:
                f.write(background_script)
            
            # Create minimal popup HTML
            popup_html = '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            width: 300px;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            text-align: center;
        }
        .logo {
            font-size: 24px;
            margin-bottom: 10px;
        }
        .title {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .status {
            padding: 10px;
            background: #e8f5e8;
            border-radius: 4px;
            font-size: 12px;
            color: #2d5a2d;
        }
    </style>
</head>
<body>
    <div class="logo">🤖</div>
    <div class="title">Marina AI</div>
    <div class="status">Marina AI is active and ready</div>
</body>
</html>
'''
            
            with open(self.extension_dir / "popup.html", "w") as f:
                f.write(popup_html)
            
            logger.info(f"Created browser extension at {self.extension_dir}")
            return str(self.extension_dir)
            
        except Exception as e:
            logger.error(f"Failed to create browser extension: {e}")
            raise
    
    def _create_placeholder_icon(self, path: Path):
        """Create a minimal PNG file as a placeholder icon."""
        with open(path, "wb") as f:
            f.write(b"")

    def find_chromium_executable(self) -> Optional[str]:
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

    async def launch_chromium(self, extension_path: str):
        """Launch Chromium with the Marina extension."""
        try:
            chromium_path = self.find_chromium_executable()
            if not chromium_path:
                raise RuntimeError("Chromium not found on system")
            
            # Prepare launch arguments
            args = [
                chromium_path,
                f"--load-extension={extension_path}",
                "--disable-extensions-except=" + extension_path,
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "--enable-experimental-web-platform-features",
                "--allow-running-insecure-content",
                "--disable-web-security",  # For development only
                "--user-data-dir=" + str(Path(self.temp_dir) / "chrome_profile"),
                "https://www.google.com"  # Default starting page
            ]
            
            logger.info(f"Launching Chromium with Marina extension: {chromium_path}")
            
            # Launch Chromium
            self.chromium_process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info("Chromium launched successfully with Marina widgets")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch Chromium: {e}")
            return False

    async def create_default_widgets(self):
        """Create default Marina widgets."""
        try:
            # Create AI Assistant widget
            ai_config = WidgetConfig(
                id="default_ai_assistant",
                type=WidgetType.AI_ASSISTANT,
                title="Marina AI Assistant",
                position=WidgetPosition.TOP_RIGHT,
                width=350,
                height=500
            )
            
            ai_widget_id = await self.widget_manager.create_widget(
                WidgetType.AI_ASSISTANT, ai_config
            )
            
            # Create Page Analyzer widget
            analyzer_config = WidgetConfig(
                id="default_page_analyzer",
                type=WidgetType.PAGE_ANALYZER,
                title="Page Analyzer",
                position=WidgetPosition.BOTTOM_RIGHT,
                width=400,
                height=300
            )
            
            analyzer_widget_id = await self.widget_manager.create_widget(
                WidgetType.PAGE_ANALYZER, analyzer_config
            )
            
            logger.info(f"Created default widgets: {ai_widget_id}, {analyzer_widget_id}")
            
        except Exception as e:
            logger.error(f"Failed to create default widgets: {e}")

    async def run(self):
        """Main entry point to launch Marina browser."""
        try:
            logger.info("Starting Marina Browser Launcher...")
            
            # Initialize Marina core
            await self.initialize()
            
            # Create browser extension
            extension_path = self.create_browser_extension()
            
            # Create default widgets
            await self.create_default_widgets()
            
            # Launch Chromium with extension
            success = await self.launch_chromium(extension_path)
            
            if success:
                logger.info("Marina browser launched successfully!")
                logger.info("You can now use Marina AI widgets in your browser:")
                logger.info("- Click the Marina AI button in the top-right corner")
                logger.info("- Select widgets from the menu")
                logger.info("- Use the browser extension popup for quick access")
                
                # Keep the script running while Chromium is open
                if self.chromium_process:
                    self.chromium_process.wait()
                    logger.info("Chromium closed")
            else:
                logger.error("Failed to launch Marina browser")
                
        except Exception as e:
            logger.error(f"Error in Marina browser launcher: {e}")
            raise
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up resources."""
        try:
            # Shutdown widget manager
            if self.widget_manager:
                await self.widget_manager.shutdown_all_widgets()
            
            # Shutdown Marina core
            if self.marina_core:
                await self.marina_core.shutdown()
            
            # Clean up temporary files
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary files")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def main():
    """Main function."""
    try:
        launcher = MarinaBrowserLauncher()
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        logger.info("Marina browser launcher interrupted by user")
    except Exception as e:
        logger.error(f"Marina browser launcher failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
