#!/usr/bin/env python3
"""
Marina Browser Launcher (Permanent Extension)

This script launches Chromium with the permanent Marina extension.
"""

import subprocess
import sys
import os
import tempfile
import logging
from pathlib import Path
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarinaLauncher:
    """Launcher for Marina-powered Chromium browser using permanent extension."""
    
    def __init__(self):
        self.temp_dir = None
        self.chromium_process = None
        self.extension_dir = Path(__file__).parent.parent / "marina_extension"
        
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
    
    def launch_chromium(self):
        """Launch Chromium with the Marina extension."""
        try:
            chromium_path = self.find_chromium_executable()
            if not chromium_path:
                raise RuntimeError("Chromium not found. Please install Chromium or Google Chrome.")
            
            if not self.extension_dir.exists():
                raise RuntimeError(f"Marina extension not found at {self.extension_dir}")
            
            # Create temporary user data directory
            self.temp_dir = tempfile.mkdtemp(prefix="marina_browser_")
            user_data_dir = Path(self.temp_dir) / "chrome_profile"
            user_data_dir.mkdir(exist_ok=True)
            
            # Prepare launch arguments
            args = [
                chromium_path,
                f"--load-extension={self.extension_dir}",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-popup-blocking",
                "https://www.google.com"
            ]
            
            logger.info(f"Launching Chromium with Marina extension from {self.extension_dir}...")
            
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
            logger.info("Starting Marina Browser...")
            
            # Launch Chromium
            success = self.launch_chromium()
            
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
        launcher = MarinaLauncher()
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
