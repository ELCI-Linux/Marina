#!/usr/bin/env python3
"""
Marina Status Bar Core - Dynamic Island Edition 🌊

A next-generation status bar that provides natural language insights into Marina's
daemon states with Dynamic Island-style expansion and contraction based on activity.

🧠 Key Features:
- Natural language status ticker with human-friendly daemon descriptions
- Dynamic expansion/contraction based on Marina daemon activity
- Emoji-rich status indicators for all modules
- Direct action controls for system toggles
- Hierarchical daemon tree awareness
- Real-time IPC integration with Marina subsystems

Architecture:
- Core controller manages state and coordinates modules
- Template engine generates natural language from daemon states
- IPC bridge communicates with Marina daemons
- Animation engine handles Dynamic Island transitions
"""

import json
import time
import threading
import subprocess
import os
import signal
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import socket
import queue
import pickle

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class DaemonState(Enum):
    """Marina daemon states with corresponding colors and emojis"""
    RUNNING = ("🟢", "running", "#4CAF50")
    STARTING = ("🟡", "starting", "#FF9800")
    STOPPING = ("🟠", "stopping", "#FF5722")
    INACTIVE = ("🔴", "inactive", "#F44336")
    ERROR = ("❌", "error", "#E91E63")
    SUSPENDED = ("⏸️", "suspended", "#9E9E9E")
    UNKNOWN = ("❓", "unknown", "#607D8B")

@dataclass
class DaemonInfo:
    """Information about a Marina daemon"""
    name: str
    display_name: str
    emoji: str
    state: DaemonState
    capabilities: List[str]
    last_activity: Optional[datetime]
    process_id: Optional[int]
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    automation_enabled: bool = False
    priority: int = 1  # 1=highest, 5=lowest

@dataclass
class SystemStatus:
    """Overall system status information"""
    cpu_usage: float
    memory_usage: float
    battery_percentage: Optional[int]
    battery_status: str
    network_connected: bool
    network_ssid: Optional[str]
    volume_level: int
    brightness_level: int
    bluetooth_enabled: bool
    time_now: datetime

@dataclass
class BarState:
    """Current state of the status bar"""
    expanded: bool = False
    expansion_level: float = 0.0  # 0.0 = collapsed, 1.0 = fully expanded
    last_interaction: Optional[datetime] = None
    active_notifications: List[Dict] = None
    ticker_messages: List[str] = None
    animation_active: bool = False
    active_mini_menu: Optional[str] = None  # Which daemon has an active mini-menu
    mini_menu_items: Dict[str, List[Dict]] = None  # Mini-menu items for each daemon
    
    def __post_init__(self):
        if self.active_notifications is None:
            self.active_notifications = []
        if self.ticker_messages is None:
            self.ticker_messages = []
        if self.mini_menu_items is None:
            self.mini_menu_items = {}

class MarinaBarCore:
    """
    Core controller for Marina's Dynamic Island status bar
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # State management
        self.bar_state = BarState()
        self.daemon_info: Dict[str, DaemonInfo] = {}
        self.system_status = SystemStatus(
            cpu_usage=0.0, memory_usage=0.0, battery_percentage=None,
            battery_status="unknown", network_connected=False, network_ssid=None,
            volume_level=0, brightness_level=0, bluetooth_enabled=False,
            time_now=datetime.now()
        )
        
        # Configuration
        self.config = self._load_config()
        
        # Message queues for IPC
        self.daemon_queue = queue.Queue()
        self.system_queue = queue.Queue()
        self.ui_queue = queue.Queue()
        
        # Threading
        self.running = False
        self.threads: List[threading.Thread] = []
        
        # Template engine
        self.template_engine = MarinaTemplateEngine(self.config_dir / "templates")
        
        # IPC bridge
        self.ipc_bridge = MarinaIPCBridge(self.daemon_queue, self.system_queue)
        
        # System updater integration
        try:
            from brain.nala_system_updater import NalaSystemUpdater
            self.nala_updater = NalaSystemUpdater()
            self.update_status = {"updates_available": 0, "last_check": None, "is_updating": False}
            print("🔄 Nala System Updater integrated")
        except ImportError:
            self.nala_updater = None
            self.update_status = None
            print("⚠️ Nala System Updater not available")
        
        # Initialize daemon discovery
        self._discover_marina_daemons()
        
        # Initialize mini-menu items for each daemon
        self._initialize_mini_menus()
        
        logger.info("🌊 Marina Bar Core initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config_file = self.config_dir / "marina_bar_config.json"
        default_config = {
            "update_interval": 1.0,
            "expansion_timeout": 8.0,
            "animation_duration": 0.3,
            "max_ticker_messages": 5,
            "daemon_discovery_paths": [
                "/home/adminx/Marina/perception",
                "/home/adminx/Marina/brain",
                "/home/adminx/Marina/web",
                "/home/adminx/Marina/devices"
            ],
            "ipc_socket_path": "/tmp/marina_bar.sock",
            "enable_notifications": True,
            "enable_natural_language": True,
            "ticker_scroll_speed": 50,
            "priority_daemons": ["vision", "sonic", "thermal", "email", "rcs"]
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def _discover_marina_daemons(self):
        """Discover Marina daemons from the filesystem"""
        discovered_daemons = {
            # Perception daemons
            "vision": DaemonInfo(
                name="vision", display_name="Vision Perception", emoji="👁️",
                state=DaemonState.UNKNOWN, capabilities=["object_detection", "face_recognition", "screen_analysis"],
                last_activity=None, process_id=None, priority=1
            ),
            "sonic": DaemonInfo(
                name="sonic", display_name="Sonic Perception", emoji="🎧",
                state=DaemonState.UNKNOWN, capabilities=["audio_processing", "speech_detection", "song_recognition"],
                last_activity=None, process_id=None, priority=1
            ),
            "thermal": DaemonInfo(
                name="thermal", display_name="Thermal Perception", emoji="🌡️",
                state=DaemonState.UNKNOWN, capabilities=["temperature_monitoring", "thermal_analysis"],
                last_activity=None, process_id=None, priority=2
            ),
            
            # Communication daemons  
            "email": DaemonInfo(
                name="email", display_name="Email Monitor", emoji="📧",
                state=DaemonState.UNKNOWN, capabilities=["email_scanning", "attachment_processing"],
                last_activity=None, process_id=None, priority=2
            ),
            "rcs": DaemonInfo(
                name="rcs", display_name="RCS Messages", emoji="💬",
                state=DaemonState.UNKNOWN, capabilities=["message_processing", "remote_commands"],
                last_activity=None, process_id=None, priority=2
            ),
            "wa_business": DaemonInfo(
                name="wa_business", display_name="WhatsApp Business", emoji="💼",
                state=DaemonState.UNKNOWN, capabilities=["business_messaging"],
                last_activity=None, process_id=None, priority=3
            ),
            
            # Brain daemons
            "identity": DaemonInfo(
                name="identity", display_name="Identity Core", emoji="🧠",
                state=DaemonState.UNKNOWN, capabilities=["identity_management", "authentication"],
                last_activity=None, process_id=None, priority=1
            ),
            "corpus": DaemonInfo(
                name="corpus", display_name="Corpus Analysis", emoji="📚",
                state=DaemonState.UNKNOWN, capabilities=["text_analysis", "knowledge_base"],
                last_activity=None, process_id=None, priority=3
            ),
            
            # Device monitors
            "bluetooth": DaemonInfo(
                name="bluetooth", display_name="Bluetooth Monitor", emoji="🔵",
                state=DaemonState.UNKNOWN, capabilities=["device_monitoring", "connection_management"],
                last_activity=None, process_id=None, priority=4
            ),
            "network": DaemonInfo(
                name="network", display_name="Network Monitor", emoji="📶",
                state=DaemonState.UNKNOWN, capabilities=["connectivity_monitoring", "network_analysis"],
                last_activity=None, process_id=None, priority=4
            ),
            
            # Screen monitoring
            "screen_monitor": DaemonInfo(
                name="screen_monitor", display_name="Screen Monitor", emoji="🖥️",
                state=DaemonState.UNKNOWN, capabilities=["screen_capture", "streaming"],
                last_activity=None, process_id=None, priority=3
            ),
            
            # System updater
            "nala_updater": DaemonInfo(
                name="nala_updater", display_name="System Updater", emoji="📦",
                state=DaemonState.UNKNOWN, capabilities=["package_management", "system_updates"],
                last_activity=None, process_id=None, priority=1
            )
        }
        
        self.daemon_info.update(discovered_daemons)
        logger.info(f"🔍 Discovered {len(discovered_daemons)} Marina daemons")
    
    def _initialize_mini_menus(self):
        """Initialize mini-menu items for each daemon"""
        for daemon_name, daemon_info in self.daemon_info.items():
            menu_items = self._generate_daemon_menu_items(daemon_name, daemon_info)
            self.bar_state.mini_menu_items[daemon_name] = menu_items
        
        logger.debug(f"🎛️ Initialized mini-menus for {len(self.bar_state.mini_menu_items)} daemons")
    
    def _generate_daemon_menu_items(self, daemon_name: str, daemon_info: DaemonInfo) -> List[Dict]:
        """Generate mini-menu items for a specific daemon"""
        base_items = [
            {"icon": "🔄", "label": "Restart", "action": "restart", "enabled": True},
            {"icon": "⏸️", "label": "Pause", "action": "pause", "enabled": daemon_info.state == DaemonState.RUNNING},
            {"icon": "▶️", "label": "Start", "action": "start", "enabled": daemon_info.state != DaemonState.RUNNING},
            {"icon": "⏹️", "label": "Stop", "action": "stop", "enabled": daemon_info.state == DaemonState.RUNNING},
            {"icon": "📊", "label": "Status", "action": "status", "enabled": True},
            {"icon": "📋", "label": "Logs", "action": "logs", "enabled": True}
        ]
        
        # Add daemon-specific menu items based on capabilities
        specific_items = []
        
        if daemon_name == "vision":
            specific_items.extend([
                {"icon": "👁️", "label": "Live View", "action": "live_view", "enabled": daemon_info.state == DaemonState.RUNNING},
                {"icon": "📸", "label": "Screenshot", "action": "screenshot", "enabled": True},
                {"icon": "🔍", "label": "Analyze Screen", "action": "analyze", "enabled": daemon_info.state == DaemonState.RUNNING}
            ])
        
        elif daemon_name == "sonic":
            specific_items.extend([
                {"icon": "🎧", "label": "Audio Monitor", "action": "audio_monitor", "enabled": daemon_info.state == DaemonState.RUNNING},
                {"icon": "🎵", "label": "Song Recognition", "action": "song_recognize", "enabled": daemon_info.state == DaemonState.RUNNING},
                {"icon": "🗣️", "label": "Speech Detection", "action": "speech_detect", "enabled": daemon_info.state == DaemonState.RUNNING}
            ])
        
        elif daemon_name == "thermal":
            specific_items.extend([
                {"icon": "🌡️", "label": "Temperature", "action": "show_temp", "enabled": True},
                {"icon": "🔥", "label": "Thermal Map", "action": "thermal_map", "enabled": daemon_info.state == DaemonState.RUNNING}
            ])
        
        elif daemon_name == "email":
            specific_items.extend([
                {"icon": "📧", "label": "Check Mail", "action": "check_mail", "enabled": daemon_info.state == DaemonState.RUNNING},
                {"icon": "📨", "label": "Compose", "action": "compose", "enabled": True},
                {"icon": "📬", "label": "Inbox", "action": "show_inbox", "enabled": True}
            ])
        
        elif daemon_name == "rcs":
            specific_items.extend([
                {"icon": "💬", "label": "Messages", "action": "show_messages", "enabled": True},
                {"icon": "✉️", "label": "Send Message", "action": "send_message", "enabled": daemon_info.state == DaemonState.RUNNING}
            ])
        
        elif daemon_name == "network":
            specific_items.extend([
                {"icon": "📶", "label": "Connection Info", "action": "connection_info", "enabled": True},
                {"icon": "🔍", "label": "Network Scan", "action": "network_scan", "enabled": daemon_info.state == DaemonState.RUNNING}
            ])
        
        elif daemon_name == "bluetooth":
            specific_items.extend([
                {"icon": "🔵", "label": "Device List", "action": "device_list", "enabled": True},
                {"icon": "🔍", "label": "Scan Devices", "action": "scan_devices", "enabled": daemon_info.state == DaemonState.RUNNING}
            ])
        
        elif daemon_name == "nala_updater":
            specific_items.extend([
                {"icon": "🔍", "label": "Check Updates", "action": "check_updates", "enabled": True},
                {"icon": "📦", "label": "Install Updates", "action": "install_updates", "enabled": True},
                {"icon": "📊", "label": "Update History", "action": "update_history", "enabled": True},
                {"icon": "🔄", "label": "Update Status", "action": "update_status", "enabled": True}
            ])
        
        # Combine base and specific items
        all_items = specific_items + [{"icon": "---", "label": "---", "action": "separator", "enabled": False}] + base_items
        
        return all_items
    
    def toggle_mini_menu(self, daemon_name: str):
        """Toggle mini-menu for a specific daemon"""
        if self.bar_state.active_mini_menu == daemon_name:
            # Close currently active menu
            self.bar_state.active_mini_menu = None
            logger.debug(f"🎛️ Closed mini-menu for {daemon_name}")
        else:
            # Open new menu
            self.bar_state.active_mini_menu = daemon_name
            self.bar_state.last_interaction = datetime.now()
            
            # Update menu items based on current daemon state
            if daemon_name in self.daemon_info:
                updated_items = self._generate_daemon_menu_items(daemon_name, self.daemon_info[daemon_name])
                self.bar_state.mini_menu_items[daemon_name] = updated_items
            
            logger.debug(f"🎛️ Opened mini-menu for {daemon_name}")
    
    def execute_menu_action(self, daemon_name: str, action: str):
        """Execute a mini-menu action for a daemon"""
        if daemon_name not in self.daemon_info:
            logger.warning(f"Unknown daemon: {daemon_name}")
            return False
        
        daemon_info = self.daemon_info[daemon_name]
        
        try:
            if action == "restart":
                return self._restart_daemon(daemon_name)
            elif action == "start":
                return self._start_daemon(daemon_name)
            elif action == "stop":
                return self._stop_daemon(daemon_name)
            elif action == "pause":
                return self._pause_daemon(daemon_name)
            elif action == "status":
                return self._show_daemon_status(daemon_name)
            elif action == "logs":
                return self._show_daemon_logs(daemon_name)
            
            # Daemon-specific actions
            elif daemon_name == "vision":
                if action == "live_view":
                    return self._open_vision_live_view()
                elif action == "screenshot":
                    return self._take_screenshot()
                elif action == "analyze":
                    return self._analyze_screen()
            
            elif daemon_name == "sonic":
                if action == "audio_monitor":
                    return self._open_audio_monitor()
                elif action == "song_recognize":
                    return self._recognize_song()
                elif action == "speech_detect":
                    return self._toggle_speech_detection()
            
            elif daemon_name == "thermal":
                if action == "show_temp":
                    return self._show_temperature()
                elif action == "thermal_map":
                    return self._show_thermal_map()
            
            elif daemon_name == "email":
                if action == "check_mail":
                    return self._check_email()
                elif action == "compose":
                    return self._compose_email()
                elif action == "show_inbox":
                    return self._show_inbox()
            
            elif daemon_name == "rcs":
                if action == "show_messages":
                    return self._show_rcs_messages()
                elif action == "send_message":
                    return self._send_rcs_message()
            
            elif daemon_name == "network":
                if action == "connection_info":
                    return self._show_network_info()
                elif action == "network_scan":
                    return self._scan_network()
            
            elif daemon_name == "bluetooth":
                if action == "device_list":
                    return self._show_bluetooth_devices()
                elif action == "scan_devices":
                    return self._scan_bluetooth_devices()
            
            elif daemon_name == "nala_updater":
                if action == "check_updates":
                    return self._check_system_updates()
                elif action == "install_updates":
                    return self._install_system_updates()
                elif action == "update_history":
                    return self._show_update_history()
                elif action == "update_status":
                    return self._show_update_status()
            
            else:
                logger.warning(f"Unknown action: {action} for daemon: {daemon_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing action {action} for {daemon_name}: {e}")
            return False
    
    # Daemon control methods
    def _restart_daemon(self, daemon_name: str) -> bool:
        """Restart a specific daemon"""
        logger.info(f"🔄 Restarting {daemon_name} daemon")
        # Implementation would send restart command to daemon
        return True
    
    def _start_daemon(self, daemon_name: str) -> bool:
        """Start a specific daemon"""
        logger.info(f"▶️ Starting {daemon_name} daemon")
        # Implementation would start the daemon process
        return True
    
    def _stop_daemon(self, daemon_name: str) -> bool:
        """Stop a specific daemon"""
        logger.info(f"⏹️ Stopping {daemon_name} daemon")
        # Implementation would stop the daemon process
        return True
    
    def _pause_daemon(self, daemon_name: str) -> bool:
        """Pause a specific daemon"""
        logger.info(f"⏸️ Pausing {daemon_name} daemon")
        # Implementation would pause daemon activity
        return True
    
    def _show_daemon_status(self, daemon_name: str) -> bool:
        """Show detailed status for a daemon"""
        daemon_info = self.daemon_info[daemon_name]
        status_info = [
            f"🎛️ {daemon_info.display_name} Status",
            f"State: {daemon_info.state.value[1].title()}",
            f"Process ID: {daemon_info.process_id or 'N/A'}",
            f"Priority: {daemon_info.priority}",
            f"Last Activity: {daemon_info.last_activity.strftime('%H:%M:%S') if daemon_info.last_activity else 'Never'}",
            f"Capabilities: {', '.join(daemon_info.capabilities)}"
        ]
        
        try:
            subprocess.run([
                'notify-send',
                f'{daemon_info.emoji} {daemon_info.display_name}',
                '\n'.join(status_info),
                '--timeout=8000'
            ], check=False)
        except:
            pass
        
        return True
    
    def _show_daemon_logs(self, daemon_name: str) -> bool:
        """Show logs for a specific daemon"""
        logger.info(f"📋 Showing logs for {daemon_name} daemon")
        # Implementation would open log viewer
        return True
    
    # Vision daemon specific actions
    def _open_vision_live_view(self) -> bool:
        """Open live vision monitoring interface"""
        logger.info("👁️ Opening vision live view")
        try:
            subprocess.run(['notify-send', '👁️ Vision Live View', 'Opening visual monitoring interface...'], check=False)
            # Implementation would launch vision monitoring GUI
        except:
            pass
        return True
    
    def _take_screenshot(self) -> bool:
        """Take a screenshot using vision system"""
        logger.info("📸 Taking screenshot")
        try:
            result = subprocess.run(['scrot', '/tmp/marina_screenshot.png'], capture_output=True)
            if result.returncode == 0:
                subprocess.run(['notify-send', '📸 Screenshot', 'Screenshot saved to /tmp/marina_screenshot.png'], check=False)
            else:
                subprocess.run(['notify-send', '📸 Screenshot', 'Failed to take screenshot'], check=False)
        except:
            pass
        return True
    
    def _analyze_screen(self) -> bool:
        """Analyze current screen content"""
        logger.info("🔍 Analyzing screen")
        try:
            subprocess.run(['notify-send', '🔍 Screen Analysis', 'Analyzing current screen content...'], check=False)
            # Implementation would trigger screen analysis
        except:
            pass
        return True
    
    # Sonic daemon specific actions
    def _open_audio_monitor(self) -> bool:
        """Open audio monitoring interface"""
        logger.info("🎧 Opening audio monitor")
        try:
            subprocess.run(['notify-send', '🎧 Audio Monitor', 'Opening audio monitoring interface...'], check=False)
            # Implementation would launch audio monitoring GUI
        except:
            pass
        return True
    
    def _recognize_song(self) -> bool:
        """Trigger song recognition"""
        logger.info("🎵 Recognizing song")
        try:
            subprocess.run(['notify-send', '🎵 Song Recognition', 'Listening for music to identify...'], check=False)
            # Implementation would trigger song recognition
        except:
            pass
        return True
    
    def _toggle_speech_detection(self) -> bool:
        """Toggle speech detection on/off"""
        logger.info("🗣️ Toggling speech detection")
        try:
            subprocess.run(['notify-send', '🗣️ Speech Detection', 'Toggling speech detection mode...'], check=False)
            # Implementation would toggle speech detection
        except:
            pass
        return True
    
    # Thermal daemon specific actions
    def _show_temperature(self) -> bool:
        """Show current system temperature"""
        logger.info("🌡️ Showing temperature")
        try:
            # Get CPU temperature
            temp_info = []
            try:
                result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Core' in line and '°C' in line:
                            temp_info.append(line.strip())
            except:
                temp_info = ['Temperature sensors not available']
            
            if not temp_info:
                temp_info = ['No temperature data available']
            
            subprocess.run([
                'notify-send',
                '🌡️ System Temperature',
                '\n'.join(temp_info[:5]),  # Show first 5 temperature readings
                '--timeout=6000'
            ], check=False)
        except:
            pass
        return True
    
    def _show_thermal_map(self) -> bool:
        """Show thermal mapping interface"""
        logger.info("🔥 Showing thermal map")
        try:
            subprocess.run(['notify-send', '🔥 Thermal Map', 'Opening thermal mapping interface...'], check=False)
            # Implementation would show thermal visualization
        except:
            pass
        return True
    
    # Email daemon specific actions
    def _check_email(self) -> bool:
        """Manually trigger email check"""
        logger.info("📧 Checking email")
        try:
            subprocess.run(['notify-send', '📧 Email Check', 'Checking for new emails...'], check=False)
            # Implementation would trigger email check
        except:
            pass
        return True
    
    def _compose_email(self) -> bool:
        """Open email composition interface"""
        logger.info("📨 Opening email composer")
        try:
            subprocess.run(['notify-send', '📨 Compose Email', 'Opening email composition interface...'], check=False)
            # Implementation would open email composer
        except:
            pass
        return True
    
    def _show_inbox(self) -> bool:
        """Show email inbox"""
        logger.info("📬 Showing inbox")
        try:
            subprocess.run(['notify-send', '📬 Email Inbox', 'Opening email inbox interface...'], check=False)
            # Implementation would show email inbox
        except:
            pass
        return True
    
    # RCS daemon specific actions
    def _show_rcs_messages(self) -> bool:
        """Show RCS messages interface"""
        logger.info("💬 Showing RCS messages")
        try:
            subprocess.run(['notify-send', '💬 RCS Messages', 'Opening RCS messages interface...'], check=False)
            # Implementation would show RCS messages
        except:
            pass
        return True
    
    def _send_rcs_message(self) -> bool:
        """Open RCS message composition"""
        logger.info("✉️ Opening RCS composer")
        try:
            subprocess.run(['notify-send', '✉️ Send RCS Message', 'Opening RCS message composer...'], check=False)
            # Implementation would open RCS composer
        except:
            pass
        return True
    
    # Network daemon specific actions
    def _show_network_info(self) -> bool:
        """Show detailed network information"""
        logger.info("📶 Showing network info")
        try:
            network_info = []
            
            # Get network interface info
            try:
                result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'inet' in line and not '127.0.0.1' in line:
                            network_info.append(line.strip())
            except:
                pass
            
            # Get WiFi info
            try:
                result = subprocess.run(['iwconfig'], capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'ESSID' in line:
                            network_info.append(line.strip())
            except:
                pass
            
            if not network_info:
                network_info = ['Network information not available']
            
            subprocess.run([
                'notify-send',
                '📶 Network Information',
                '\n'.join(network_info[:5]),
                '--timeout=8000'
            ], check=False)
        except:
            pass
        return True
    
    def _scan_network(self) -> bool:
        """Scan for available networks"""
        logger.info("🔍 Scanning networks")
        try:
            subprocess.run(['notify-send', '🔍 Network Scan', 'Scanning for available networks...'], check=False)
            # Implementation would scan for networks
        except:
            pass
        return True
    
    # Bluetooth daemon specific actions
    def _show_bluetooth_devices(self) -> bool:
        """Show paired Bluetooth devices"""
        logger.info("🔵 Showing Bluetooth devices")
        try:
            device_info = []
            
            try:
                result = subprocess.run(['bluetoothctl', 'devices'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            device_info.append(line.strip())
            except:
                device_info = ['Bluetooth devices not available']
            
            if not device_info:
                device_info = ['No Bluetooth devices found']
            
            subprocess.run([
                'notify-send',
                '🔵 Bluetooth Devices',
                '\n'.join(device_info[:5]),
                '--timeout=8000'
            ], check=False)
        except:
            pass
        return True
    
    def _scan_bluetooth_devices(self) -> bool:
        """Scan for available Bluetooth devices"""
        logger.info("🔍 Scanning Bluetooth devices")
        try:
            subprocess.run(['notify-send', '🔍 Bluetooth Scan', 'Scanning for Bluetooth devices...'], check=False)
            # Implementation would scan for Bluetooth devices
        except:
            pass
        return True
    
    # Nala updater specific actions
    def _check_system_updates(self) -> bool:
        """Check for available system updates"""
        logger.info("🔍 Checking for system updates")
        try:
            if self.nala_updater:
                packages, has_critical = self.nala_updater.check_for_updates()
                self.update_status["updates_available"] = len(packages)
                self.update_status["last_check"] = datetime.now()
                
                if packages:
                    critical_count = sum(1 for pkg in packages if pkg.severity.value == "critical")
                    message = f"Found {len(packages)} updates ({critical_count} critical)"
                    if has_critical:
                        subprocess.run(['notify-send', '🚨 Critical Updates', message, '--timeout=10000'], check=False)
                    else:
                        subprocess.run(['notify-send', '📦 Updates Available', message, '--timeout=8000'], check=False)
                else:
                    subprocess.run(['notify-send', '✅ System Up to Date', 'No updates available'], check=False)
            else:
                subprocess.run(['notify-send', '❌ Update Error', 'Nala updater not available'], check=False)
        except Exception as e:
            subprocess.run(['notify-send', '❌ Update Check Failed', f'Error: {str(e)}'], check=False)
        return True
    
    def _install_system_updates(self) -> bool:
        """Install available system updates"""
        logger.info("📦 Installing system updates")
        try:
            if self.nala_updater:
                if self.update_status["is_updating"]:
                    subprocess.run(['notify-send', '⚠️ Update in Progress', 'System update already running'], check=False)
                    return False
                
                self.update_status["is_updating"] = True
                subprocess.run(['notify-send', '🚀 Starting Updates', 'System update initiated...'], check=False)
                
                # Run update in background thread
                import threading
                update_thread = threading.Thread(target=self._run_system_update, daemon=True)
                update_thread.start()
            else:
                subprocess.run(['notify-send', '❌ Update Error', 'Nala updater not available'], check=False)
        except Exception as e:
            subprocess.run(['notify-send', '❌ Update Failed', f'Error: {str(e)}'], check=False)
        return True
    
    def _run_system_update(self):
        """Run system update in background"""
        try:
            # Check for updates first
            packages, _ = self.nala_updater.check_for_updates()
            
            if packages:
                # Perform update
                session = self.nala_updater.perform_system_update(packages)
                
                if session.status.value == "complete":
                    message = f"✅ Update completed successfully! Updated {len(packages)} packages."
                    if session.system_health_after:
                        message += f" System health: {session.system_health_after:.1f}/100"
                    subprocess.run(['notify-send', '✅ Update Complete', message, '--timeout=10000'], check=False)
                elif session.status.value == "failed":
                    subprocess.run(['notify-send', '❌ Update Failed', f'Error: {session.error_message}', '--timeout=10000'], check=False)
                elif session.status.value == "rolled_back":
                    subprocess.run(['notify-send', '🔄 Update Rolled Back', 'System health declined, rolled back to previous state', '--timeout=10000'], check=False)
            else:
                subprocess.run(['notify-send', '✅ No Updates', 'System is already up to date'], check=False)
                
        except Exception as e:
            subprocess.run(['notify-send', '❌ Update Error', f'Update failed: {str(e)}', '--timeout=10000'], check=False)
        finally:
            self.update_status["is_updating"] = False
    
    def _show_update_history(self) -> bool:
        """Show system update history"""
        logger.info("📊 Showing update history")
        try:
            if self.nala_updater:
                status = self.nala_updater.get_update_status()
                recent_sessions = status.get("recent_sessions", [])
                
                if recent_sessions:
                    history_info = []
                    for session in recent_sessions[-3:]:  # Last 3 sessions
                        start_time = datetime.fromisoformat(session["start_time"]).strftime("%m/%d %H:%M")
                        status_emoji = {
                            "complete": "✅",
                            "failed": "❌", 
                            "rolled_back": "🔄"
                        }.get(session["status"], "❓")
                        history_info.append(f"{status_emoji} {start_time}: {len(session['packages'])} packages")
                    
                    subprocess.run([
                        'notify-send',
                        '📊 Update History',
                        '\n'.join(history_info),
                        '--timeout=10000'
                    ], check=False)
                else:
                    subprocess.run(['notify-send', '📊 Update History', 'No update history available'], check=False)
            else:
                subprocess.run(['notify-send', '❌ History Error', 'Nala updater not available'], check=False)
        except Exception as e:
            subprocess.run(['notify-send', '❌ History Error', f'Error: {str(e)}'], check=False)
        return True
    
    def _show_update_status(self) -> bool:
        """Show current update status"""
        logger.info("🔄 Showing update status")
        try:
            if self.nala_updater:
                status = self.nala_updater.get_update_status()
                
                status_info = [
                    f"Updates Available: {self.update_status['updates_available']}",
                    f"Currently Updating: {'Yes' if status['is_updating'] else 'No'}",
                    f"Total Sessions: {status['update_history_count']}",
                ]
                
                if self.update_status['last_check']:
                    last_check = self.update_status['last_check'].strftime("%m/%d %H:%M")
                    status_info.append(f"Last Check: {last_check}")
                
                if status['system_health']:
                    health = status['system_health']['current_metrics']['health_score']
                    status_info.append(f"System Health: {health:.1f}/100")
                
                subprocess.run([
                    'notify-send',
                    '🔄 Update Status',
                    '\n'.join(status_info),
                    '--timeout=8000'
                ], check=False)
            else:
                subprocess.run(['notify-send', '❌ Status Error', 'Nala updater not available'], check=False)
        except Exception as e:
            subprocess.run(['notify-send', '❌ Status Error', f'Error: {str(e)}'], check=False)
        return True
    
    def start(self):
        """Start the Marina status bar core"""
        if self.running:
            logger.warning("Marina Bar Core already running")
            return
        
        self.running = True
        
        # Start background threads
        self.threads = [
            threading.Thread(target=self._daemon_monitor_loop, daemon=True),
            threading.Thread(target=self._system_monitor_loop, daemon=True),
            threading.Thread(target=self._ui_update_loop, daemon=True),
            threading.Thread(target=self._ipc_listener_loop, daemon=True),
            threading.Thread(target=self._expansion_manager_loop, daemon=True),
            threading.Thread(target=self._update_monitor_loop, daemon=True)
        ]
        
        for thread in self.threads:
            thread.start()
        
        # Start IPC bridge
        self.ipc_bridge.start()
        
        logger.info("🚀 Marina Bar Core started")
    
    def stop(self):
        """Stop the Marina status bar core"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop IPC bridge
        self.ipc_bridge.stop()
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2)
        
        logger.info("⏹️ Marina Bar Core stopped")
    
    def _daemon_monitor_loop(self):
        """Monitor Marina daemon states"""
        while self.running:
            try:
                # Check daemon states using process monitoring
                for daemon_name, daemon_info in self.daemon_info.items():
                    old_state = daemon_info.state
                    new_state = self._check_daemon_state(daemon_name)
                    
                    if new_state != old_state:
                        daemon_info.state = new_state
                        self._handle_daemon_state_change(daemon_name, old_state, new_state)
                
                time.sleep(self.config["update_interval"])
                
            except Exception as e:
                logger.error(f"Error in daemon monitor loop: {e}")
                time.sleep(5)
    
    def _system_monitor_loop(self):
        """Monitor system status"""
        while self.running:
            try:
                # Update system status
                self.system_status.cpu_usage = self._get_cpu_usage()
                self.system_status.memory_usage = self._get_memory_usage()
                self.system_status.battery_percentage, self.system_status.battery_status = self._get_battery_info()
                self.system_status.network_connected, self.system_status.network_ssid = self._get_network_info()
                self.system_status.volume_level = self._get_volume_level()
                self.system_status.brightness_level = self._get_brightness_level()
                self.system_status.bluetooth_enabled = self._get_bluetooth_status()
                self.system_status.time_now = datetime.now()
                
                time.sleep(self.config["update_interval"] * 2)  # Update system info less frequently
                
            except Exception as e:
                logger.error(f"Error in system monitor loop: {e}")
                time.sleep(5)
    
    def _ui_update_loop(self):
        """Update UI elements and manage ticker messages"""
        while self.running:
            try:
                # Generate natural language messages
                if self.config["enable_natural_language"]:
                    self._update_ticker_messages()
                
                # Update expansion state based on activity
                self._update_expansion_state()
                
                time.sleep(self.config["update_interval"])
                
            except Exception as e:
                logger.error(f"Error in UI update loop: {e}")
                time.sleep(5)
    
    def _ipc_listener_loop(self):
        """Listen for IPC messages from Marina daemons"""
        while self.running:
            try:
                # Process daemon messages
                while not self.daemon_queue.empty():
                    message = self.daemon_queue.get_nowait()
                    self._process_daemon_message(message)
                
                # Process system messages
                while not self.system_queue.empty():
                    message = self.system_queue.get_nowait()
                    self._process_system_message(message)
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in IPC listener loop: {e}")
                time.sleep(1)
    
    def _expansion_manager_loop(self):
        """Manage Dynamic Island expansion and contraction"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check for expansion triggers
                should_expand = self._should_expand()
                
                if should_expand and not self.bar_state.expanded:
                    self._trigger_expansion("activity_detected")
                elif not should_expand and self.bar_state.expanded:
                    # Check timeout
                    if (self.bar_state.last_interaction and 
                        current_time - self.bar_state.last_interaction > 
                        timedelta(seconds=self.config["expansion_timeout"])):
                        self._trigger_contraction("timeout")
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in expansion manager loop: {e}")
                time.sleep(1)
    
    def _update_monitor_loop(self):
        """Monitor for system updates periodically"""
        while self.running:
            try:
                if self.nala_updater and self.update_status:
                    # Check for updates every hour
                    current_time = datetime.now()
                    if (not self.update_status["last_check"] or 
                        current_time - self.update_status["last_check"] > timedelta(hours=1)):
                        
                        # Run update check in background
                        try:
                            packages, has_critical = self.nala_updater.check_for_updates()
                            self.update_status["updates_available"] = len(packages)
                            self.update_status["last_check"] = current_time
                            
                            # Update daemon state based on availability
                            if self.update_status["updates_available"] > 0:
                                if "nala_updater" in self.daemon_info:
                                    self.daemon_info["nala_updater"].state = DaemonState.RUNNING
                                    self.daemon_info["nala_updater"].last_activity = current_time
                                
                                # Generate ticker message
                                if has_critical:
                                    msg = f"🚨 {self.update_status['updates_available']} updates available (critical updates found!)"
                                else:
                                    msg = f"📦 {self.update_status['updates_available']} updates available"
                                
                                if msg not in self.bar_state.ticker_messages:
                                    self.bar_state.ticker_messages.append(msg)
                                    if len(self.bar_state.ticker_messages) > self.config["max_ticker_messages"]:
                                        self.bar_state.ticker_messages.pop(0)
                                
                                # Trigger expansion for critical updates
                                if has_critical:
                                    self._trigger_expansion("critical_updates")
                            else:
                                if "nala_updater" in self.daemon_info:
                                    self.daemon_info["nala_updater"].state = DaemonState.INACTIVE
                        
                        except Exception as e:
                            logger.error(f"Error checking updates: {e}")
                    
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in update monitor loop: {e}")
                time.sleep(60)
    
    def _check_daemon_state(self, daemon_name: str) -> DaemonState:
        """Check the current state of a Marina daemon"""
        try:
            # Try to find process by name patterns
            process_patterns = {
                "vision": ["ocular_perception_daemon", "visual_sampling_daemon"],
                "sonic": ["sonic_perception_daemon", "ate_daemon"],
                "thermal": ["thermal_perception_daemon"],
                "email": ["email_daemon"],
                "rcs": ["rcs_daemon"],
                "wa_business": ["wa_business_daemon"],
                "identity": ["identity/daemon"],
                "bluetooth": ["marina-bluetooth-monitor"],
                "network": ["marina-network-monitor"],
                "screen_monitor": ["screen_monitor/daemon"],
                "nala_updater": ["nala_system_updater"]
            }
            
            patterns = process_patterns.get(daemon_name, [daemon_name])
            
            for pattern in patterns:
                result = subprocess.run(
                    ["pgrep", "-f", pattern],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    if pids and pids[0]:
                        # Update process ID
                        if daemon_name in self.daemon_info:
                            self.daemon_info[daemon_name].process_id = int(pids[0])
                            self.daemon_info[daemon_name].last_activity = datetime.now()
                        return DaemonState.RUNNING
            
            return DaemonState.INACTIVE
            
        except Exception as e:
            logger.debug(f"Error checking daemon {daemon_name}: {e}")
            return DaemonState.UNKNOWN
    
    def _handle_daemon_state_change(self, daemon_name: str, old_state: DaemonState, new_state: DaemonState):
        """Handle daemon state changes"""
        daemon_info = self.daemon_info.get(daemon_name)
        if not daemon_info:
            return
        
        # Generate natural language message
        message = self.template_engine.generate_daemon_message(daemon_name, daemon_info, new_state)
        
        # Add to ticker
        if message:
            self.bar_state.ticker_messages.append(message)
            if len(self.bar_state.ticker_messages) > self.config["max_ticker_messages"]:
                self.bar_state.ticker_messages.pop(0)
        
        # Trigger expansion for priority daemons
        if daemon_name in self.config["priority_daemons"] or daemon_info.priority <= 2:
            self._trigger_expansion(f"daemon_change_{daemon_name}")
        
        logger.info(f"🔄 {daemon_name}: {old_state.value[1]} → {new_state.value[1]}")
    
    def _should_expand(self) -> bool:
        """Determine if the bar should expand"""
        # Check for recent daemon activity
        recent_threshold = datetime.now() - timedelta(seconds=30)
        
        for daemon_info in self.daemon_info.values():
            if (daemon_info.last_activity and 
                daemon_info.last_activity > recent_threshold and
                daemon_info.priority <= 2):
                return True
        
        # Check for system alerts
        if (self.system_status.battery_percentage and 
            self.system_status.battery_percentage < 20):
            return True
        
        # Check for pending notifications
        if self.bar_state.active_notifications:
            return True
        
        return False
    
    def _trigger_expansion(self, reason: str):
        """Trigger Dynamic Island expansion"""
        if self.bar_state.expanded:
            return
        
        self.bar_state.expanded = True
        self.bar_state.last_interaction = datetime.now()
        self.bar_state.animation_active = True
        
        logger.debug(f"🔍 Expanding bar: {reason}")
    
    def _trigger_contraction(self, reason: str):
        """Trigger Dynamic Island contraction"""
        if not self.bar_state.expanded:
            return
        
        self.bar_state.expanded = False
        self.bar_state.animation_active = True
        
        logger.debug(f"🔍 Contracting bar: {reason}")
    
    def _update_ticker_messages(self):
        """Update ticker messages with current daemon states"""
        # Generate status summary
        active_daemons = [name for name, info in self.daemon_info.items() 
                         if info.state == DaemonState.RUNNING]
        
        if active_daemons:
            priority_active = [name for name in active_daemons 
                             if self.daemon_info[name].priority <= 2]
            
            if priority_active:
                message = self.template_engine.generate_summary_message(
                    priority_active, self.system_status
                )
                if message and message not in self.bar_state.ticker_messages:
                    self.bar_state.ticker_messages.append(message)
    
    def _update_expansion_state(self):
        """Update expansion level for smooth animations"""
        target_level = 1.0 if self.bar_state.expanded else 0.0
        current_level = self.bar_state.expansion_level
        
        if abs(target_level - current_level) > 0.01:
            # Smooth animation towards target
            animation_speed = 1.0 / self.config["animation_duration"]
            step = animation_speed * self.config["update_interval"]
            
            if target_level > current_level:
                self.bar_state.expansion_level = min(target_level, current_level + step)
            else:
                self.bar_state.expansion_level = max(target_level, current_level - step)
        else:
            self.bar_state.expansion_level = target_level
            if self.bar_state.animation_active:
                self.bar_state.animation_active = False
    
    def _process_daemon_message(self, message: Dict[str, Any]):
        """Process incoming daemon messages"""
        daemon_name = message.get("daemon")
        if daemon_name and daemon_name in self.daemon_info:
            daemon_info = self.daemon_info[daemon_name]
            
            # Update activity timestamp
            daemon_info.last_activity = datetime.now()
            
            # Process specific message types
            msg_type = message.get("type")
            if msg_type == "state_change":
                new_state = DaemonState(message.get("state", DaemonState.UNKNOWN))
                old_state = daemon_info.state
                daemon_info.state = new_state
                self._handle_daemon_state_change(daemon_name, old_state, new_state)
            
            elif msg_type == "activity":
                # Add activity-specific message
                activity_msg = self.template_engine.generate_activity_message(
                    daemon_name, daemon_info, message.get("data", {})
                )
                if activity_msg:
                    self.bar_state.ticker_messages.append(activity_msg)
    
    def _process_system_message(self, message: Dict[str, Any]):
        """Process system-level messages"""
        msg_type = message.get("type")
        
        if msg_type == "notification":
            self.bar_state.active_notifications.append({
                "title": message.get("title", ""),
                "message": message.get("message", ""),
                "timestamp": datetime.now(),
                "priority": message.get("priority", 3)
            })
            self._trigger_expansion("notification")
    
    # System monitoring helper methods
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            result = subprocess.run(
                ["top", "-bn1"], capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.split('\n'):
                if 'Cpu(s)' in line:
                    # Extract CPU usage from top output
                    usage_str = line.split(',')[0].split(':')[1].strip()
                    return float(usage_str.split('%')[0])
        except:
            pass
        return 0.0
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            result = subprocess.run(
                ["free"], capture_output=True, text=True, timeout=3
            )
            lines = result.stdout.split('\n')
            mem_line = lines[1]  # Memory line
            values = mem_line.split()
            total = int(values[1])
            used = int(values[2])
            return (used / total) * 100
        except:
            pass
        return 0.0
    
    def _get_battery_info(self) -> tuple[Optional[int], str]:
        """Get battery percentage and status"""
        try:
            result = subprocess.run(
                ["acpi", "-b"], capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if "Battery" in output:
                    # Parse battery info
                    parts = output.split(',')
                    percentage = int(parts[1].strip().rstrip('%'))
                    status = parts[0].split(':')[1].strip()
                    return percentage, status
        except:
            pass
        return None, "unknown"
    
    def _get_network_info(self) -> tuple[bool, Optional[str]]:
        """Get network connection status and SSID"""
        try:
            # Check if connected
            result = subprocess.run(
                ["ping", "-c", "1", "8.8.8.8"], 
                capture_output=True, timeout=3
            )
            connected = result.returncode == 0
            
            ssid = None
            if connected:
                # Try to get SSID
                result = subprocess.run(
                    ["iwgetid", "-r"], capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0:
                    ssid = result.stdout.strip()
            
            return connected, ssid
        except:
            return False, None
    
    def _get_volume_level(self) -> int:
        """Get current volume level"""
        try:
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                # Parse volume from output
                output = result.stdout
                if '%' in output:
                    volume_str = output.split('%')[0].split()[-1]
                    return int(volume_str)
        except:
            pass
        return 0
    
    def _get_brightness_level(self) -> int:
        """Get current brightness level"""
        try:
            brightness_file = Path("/sys/class/backlight/intel_backlight/brightness")
            max_brightness_file = Path("/sys/class/backlight/intel_backlight/max_brightness")
            
            if brightness_file.exists() and max_brightness_file.exists():
                current = int(brightness_file.read_text().strip())
                maximum = int(max_brightness_file.read_text().strip())
                return int((current / maximum) * 100)
        except:
            pass
        return 0
    
    def _get_bluetooth_status(self) -> bool:
        """Get Bluetooth enabled status"""
        try:
            result = subprocess.run(
                ["bluetoothctl", "show"], capture_output=True, text=True, timeout=3
            )
            return "Powered: yes" in result.stdout
        except:
            return False
    
    def get_py3status_data(self) -> Dict[str, Any]:
        """Generate data for py3status modules"""
        # Count active daemons by priority
        priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for daemon_info in self.daemon_info.values():
            if daemon_info.state == DaemonState.RUNNING:
                priority_counts[daemon_info.priority] += 1
        
        # Generate current ticker message
        current_ticker = ""
        if self.bar_state.ticker_messages:
            current_ticker = self.bar_state.ticker_messages[-1]
        
        # System status summary
        system_emoji = "🟢"
        if self.system_status.cpu_usage > 80 or self.system_status.memory_usage > 90:
            system_emoji = "🔴"
        elif self.system_status.cpu_usage > 60 or self.system_status.memory_usage > 75:
            system_emoji = "🟡"
        
        return {
            "expanded": self.bar_state.expanded,
            "expansion_level": self.bar_state.expansion_level,
            "daemon_counts": priority_counts,
            "active_daemons": len([d for d in self.daemon_info.values() if d.state == DaemonState.RUNNING]),
            "total_daemons": len(self.daemon_info),
            "ticker_message": current_ticker,
            "system_status": {
                "emoji": system_emoji,
                "cpu": self.system_status.cpu_usage,
                "memory": self.system_status.memory_usage,
                "battery": self.system_status.battery_percentage,
                "network": self.system_status.network_connected,
                "ssid": self.system_status.network_ssid
            },
            "priority_daemons": {
                name: {
                    "emoji": info.emoji,
                    "state": info.state.value[0],
                    "name": info.display_name,
                    "has_mini_menu": name in self.bar_state.mini_menu_items
                }
                for name, info in self.daemon_info.items()
                if name in self.config["priority_daemons"]
            },
            "mini_menu_data": {
                "active_menu": self.bar_state.active_mini_menu,
                "menu_items": self.bar_state.mini_menu_items.get(self.bar_state.active_mini_menu, []) if self.bar_state.active_mini_menu else []
            },
            "all_daemons": {
                name: {
                    "emoji": info.emoji,
                    "state": info.state.value[0],
                    "name": info.display_name,
                    "priority": info.priority,
                    "has_mini_menu": name in self.bar_state.mini_menu_items
                }
                for name, info in self.daemon_info.items()
            }
        }

class MarinaTemplateEngine:
    """Natural language template engine for Marina status messages"""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load message templates"""
        default_templates = {
            "daemon_running": "{emoji} {name} is now active.",
            "daemon_stopped": "{emoji} {name} has gone dormant.",
            "daemon_error": "{emoji} {name} encountered an issue.",
            "daemon_starting": "{emoji} {name} is initializing...",
            "activity_vision": "👁️ Visual processing: {activity}",
            "activity_sonic": "🎧 Audio detected: {activity}",
            "activity_email": "📧 {count} new emails processed",
            "system_summary": "System running smoothly - {active_count} active modules",
            "battery_low": "🔋 Battery at {percentage}% - consider charging",
            "network_connected": "📶 Connected to {ssid}",
            "network_disconnected": "📡 Network connection lost"
        }
        
        template_file = self.templates_dir / "messages.json"
        if template_file.exists():
            try:
                with open(template_file, 'r') as f:
                    user_templates = json.load(f)
                default_templates.update(user_templates)
            except Exception as e:
                logger.error(f"Error loading templates: {e}")
        
        return default_templates
    
    def generate_daemon_message(self, daemon_name: str, daemon_info: DaemonInfo, state: DaemonState) -> str:
        """Generate natural language message for daemon state change"""
        template_key = f"daemon_{state.value[1]}"
        template = self.templates.get(template_key, "{emoji} {name} state: {state}")
        
        return template.format(
            emoji=daemon_info.emoji,
            name=daemon_info.display_name,
            state=state.value[1],
            daemon=daemon_name
        )
    
    def generate_activity_message(self, daemon_name: str, daemon_info: DaemonInfo, activity_data: Dict) -> str:
        """Generate activity-specific message"""
        template_key = f"activity_{daemon_name}"
        template = self.templates.get(template_key)
        
        if template:
            return template.format(
                emoji=daemon_info.emoji,
                name=daemon_info.display_name,
                **activity_data
            )
        
        return f"{daemon_info.emoji} {daemon_info.display_name} activity detected"
    
    def generate_summary_message(self, active_daemons: List[str], system_status: SystemStatus) -> str:
        """Generate system summary message"""
        template = self.templates.get("system_summary", "Marina operating normally")
        
        return template.format(
            active_count=len(active_daemons),
            daemons=", ".join(active_daemons[:3]),
            time=system_status.time_now.strftime("%H:%M")
        )

class MarinaIPCBridge:
    """IPC bridge for communication with Marina daemons"""
    
    def __init__(self, daemon_queue: queue.Queue, system_queue: queue.Queue):
        self.daemon_queue = daemon_queue
        self.system_queue = system_queue
        self.socket_path = "/tmp/marina_bar.sock"
        self.server_socket = None
        self.running = False
        self.clients = []
    
    def start(self):
        """Start IPC server"""
        try:
            # Remove existing socket
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server_socket.bind(self.socket_path)
            self.server_socket.listen(5)
            
            self.running = True
            
            # Start server thread
            server_thread = threading.Thread(target=self._server_loop, daemon=True)
            server_thread.start()
            
            logger.info(f"🔌 IPC server listening on {self.socket_path}")
            
        except Exception as e:
            logger.error(f"Failed to start IPC server: {e}")
    
    def stop(self):
        """Stop IPC server"""
        self.running = False
        
        # Close client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Remove socket file
        try:
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
        except:
            pass
    
    def _server_loop(self):
        """Main server loop"""
        while self.running:
            try:
                if self.server_socket:
                    client_socket, _ = self.server_socket.accept()
                    self.clients.append(client_socket)
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(client_socket,), 
                        daemon=True
                    )
                    client_thread.start()
                    
            except Exception as e:
                if self.running:
                    logger.error(f"Error in IPC server loop: {e}")
                break
    
    def _handle_client(self, client_socket):
        """Handle individual client connection"""
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    message = pickle.loads(data)
                    self._route_message(message)
                except Exception as e:
                    logger.error(f"Error processing client message: {e}")
                
        except Exception as e:
            logger.debug(f"Client disconnected: {e}")
        finally:
            try:
                client_socket.close()
                self.clients.remove(client_socket)
            except:
                pass
    
    def _route_message(self, message: Dict[str, Any]):
        """Route incoming message to appropriate queue"""
        msg_type = message.get("type", "")
        
        if msg_type.startswith("daemon_"):
            self.daemon_queue.put(message)
        elif msg_type.startswith("system_"):
            self.system_queue.put(message)
        else:
            # Default to system queue
            self.system_queue.put(message)

# Global instance for py3status integration
_marina_bar_core = None

def get_marina_bar_core() -> MarinaBarCore:
    """Get or create global Marina bar core instance"""
    global _marina_bar_core
    if _marina_bar_core is None:
        _marina_bar_core = MarinaBarCore()
        _marina_bar_core.start()
    return _marina_bar_core

def cleanup_marina_bar_core():
    """Cleanup global Marina bar core instance"""
    global _marina_bar_core
    if _marina_bar_core:
        _marina_bar_core.stop()
        _marina_bar_core = None

# Signal handler for cleanup
def signal_handler(signum, frame):
    cleanup_marina_bar_core()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    # Test run
    core = MarinaBarCore()
    core.start()
    
    try:
        while True:
            print(f"Marina Bar Status: {len(core.daemon_info)} daemons tracked")
            data = core.get_py3status_data()
            print(f"Active: {data['active_daemons']}/{data['total_daemons']}")
            print(f"Ticker: {data['ticker_message']}")
            print(f"Expanded: {data['expanded']} ({data['expansion_level']:.1f})")
            print("-" * 50)
            time.sleep(5)
    except KeyboardInterrupt:
        core.stop()
