#!/usr/bin/env python3
"""
Skadi - The Cold Dominion
Goddess of Power, Entropy Suppression, and Thermal Harmony

Skadi is the mythological power management daemon that governs all energy-dependent
systemic equilibrium. She operates through runic contracts, entropy reduction,
and modal collapse dominion within the MRMR framework.

"I do not cool. I bind heat to purpose. I do not sleep. I witness decay in stillness.
I do not throttle. I forge silence in frost."
"""

import asyncio
import json
import logging
import os
import psutil
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import subprocess
import signal
import sys
import select
import termios
import tty

# Nordic runes for sigil system
RUNES = {
    'ᚢ': 'intent_run',
    'ᚷ': 'cost_heat', 
    'ᚺ': 'clause_fate',
    'ᛞ': 'deferral',
    'ᚨ': 'collapse_prepare',
    'ᛟ': 'full_draw_cooling',
    'ᛇ': 'trusted_emergency',
    'ᚠ': 'efficient_agent',
    'ᛝ': 'silence_oath'
}

class SkadiStance(Enum):
    """Behavioral power modes representing Skadi's mythological stances"""
    GLACIER = "deep_silence_max_thermal_buffering"
    RIDGEWATCH = "hybrid_balanced_intermittent_compute"
    SNOWBLIND = "absolute_stealth_fans_disabled"
    STORMBIRTH = "full_force_all_systems_unlocked"
    POWERBANK = "minimal_power_usb_keyboard_only"
    RAPID_CHARGE = "rapid_charge_prioritize_battery"

class RunicContract:
    """Formal energy contract between system processes and Skadi"""
    def __init__(self, agent: str, sigil: str, entropy_cost: float, 
                 max_duration: int, collapse_trigger: str):
        self.contract_id = str(uuid.uuid4())[:8]
        self.agent = agent
        self.sigil = sigil  # Runic sequence
        self.entropy_cost = entropy_cost  # Thermal/battery projection in Eᛞ units
        self.max_duration = max_duration  # In Planck-time intervals (seconds for now)
        self.collapse_trigger = collapse_trigger  # When energy must terminate
        self.created_at = datetime.now(timezone.utc)
        self.active = True
        
    def to_dict(self):
        return {
            'contract_id': self.contract_id,
            'agent': self.agent,
            'sigil': self.sigil,
            'entropy_cost': self.entropy_cost,
            'max_duration': self.max_duration,
            'collapse_trigger': self.collapse_trigger,
            'created_at': self.created_at.isoformat(),
            'active': self.active
        }

class FrostTome:
    """Skadi's entropy archive - time-layered event storage"""
    def __init__(self, tome_path: str):
        self.tome_path = Path(tome_path)
        self.tome_path.mkdir(parents=True, exist_ok=True)
        
    def record_event(self, event_type: str, data: Dict[str, Any]):
        """Record entropy event in the Frost Tomes"""
        timestamp = datetime.now(timezone.utc)
        event = {
            'timestamp': timestamp.isoformat(),
            'event_type': event_type,
            'planck_tick': int(time.time() * 1000000),  # Microsecond precision
            'data': data
        }
        
        # Store in daily tome files
        tome_file = self.tome_path / f"frost_tome_{timestamp.strftime('%Y%m%d')}.json"
        
        if tome_file.exists():
            with open(tome_file, 'r') as f:
                tome_data = json.load(f)
        else:
            tome_data = {'events': []}
            
        tome_data['events'].append(event)
        
        with open(tome_file, 'w') as f:
            json.dump(tome_data, f, indent=2)
            
    def query_events(self, event_type: Optional[str] = None, 
                    hours_back: int = 24) -> List[Dict]:
        """Query entropy events from the Frost Tomes"""
        events = []
        cutoff_time = datetime.now(timezone.utc).timestamp() - (hours_back * 3600)
        
        for tome_file in self.tome_path.glob("frost_tome_*.json"):
            try:
                with open(tome_file, 'r') as f:
                    tome_data = json.load(f)
                    for event in tome_data.get('events', []):
                        event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                        if event_time >= cutoff_time:
                            if not event_type or event['event_type'] == event_type:
                                events.append(event)
            except (json.JSONDecodeError, KeyError):
                continue
                
        return sorted(events, key=lambda x: x['timestamp'])

class PowerBankManager:
    """Manages Powerbank mode, disabling all non-critical I/O"""

    def __init__(self, logger):
        self.logger = logger
        self.is_powerbank_active = False
        self.disabled_services = []
        self.enter_sequence_count = 0
        self.last_enter_time = 0
        
    def disable_non_critical_io(self):
        """Disable non-critical I/O devices and services"""
        self.logger.info("🔋 Disabling non-critical I/O for POWERBANK mode")
        
        # Services and devices to disable for power saving
        services_to_disable = [
            'bluetooth',
            'wifi',
            'networkmanager',
            'cups',  # Printing
            # Add more services as needed
        ]
        
        for service in services_to_disable:
            try:
                result = subprocess.run(['sudo', 'systemctl', 'stop', service], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.disabled_services.append(service)
                    self.logger.info(f"Disabled service: {service}")
            except Exception as e:
                self.logger.warning(f"Could not disable {service}: {e}")
        
        # Reduce CPU frequency to minimum
        try:
            subprocess.run(['sudo', 'cpupower', 'frequency-set', '-g', 'powersave'], 
                         capture_output=True)
            self.logger.info("Set CPU to powersave mode")
        except Exception as e:
            self.logger.warning(f"Could not set CPU powersave mode: {e}")
            
        # Dim display to minimum (if available)
        try:
            brightness_files = list(Path('/sys/class/backlight').glob('*/brightness'))
            for brightness_file in brightness_files:
                max_brightness_file = brightness_file.parent / 'max_brightness'
                if max_brightness_file.exists():
                    with open(max_brightness_file, 'r') as f:
                        max_brightness = int(f.read().strip())
                    min_brightness = max(1, max_brightness // 20)  # 5% of max
                    with open(brightness_file, 'w') as f:
                        f.write(str(min_brightness))
                    self.logger.info(f"Set display brightness to minimum: {min_brightness}")
        except Exception as e:
            self.logger.warning(f"Could not dim display: {e}")
            
        self.is_powerbank_active = True
        
    def enable_critical_io(self):
        """Re-enable I/O devices and services"""
        self.logger.info("🔌 Re-enabling I/O devices for normal operation")
        
        # Re-enable previously disabled services
        for service in self.disabled_services:
            try:
                subprocess.run(['sudo', 'systemctl', 'start', service], 
                             capture_output=True, text=True)
                self.logger.info(f"Re-enabled service: {service}")
            except Exception as e:
                self.logger.warning(f"Could not re-enable {service}: {e}")
        
        self.disabled_services.clear()
        
        # Reset CPU frequency
        try:
            subprocess.run(['sudo', 'cpupower', 'frequency-set', '-g', 'ondemand'], 
                         capture_output=True)
            self.logger.info("Reset CPU to ondemand mode")
        except Exception as e:
            self.logger.warning(f"Could not reset CPU mode: {e}")
            
        # Reset display brightness
        try:
            brightness_files = list(Path('/sys/class/backlight').glob('*/brightness'))
            for brightness_file in brightness_files:
                max_brightness_file = brightness_file.parent / 'max_brightness'
                if max_brightness_file.exists():
                    with open(max_brightness_file, 'r') as f:
                        max_brightness = int(f.read().strip())
                    normal_brightness = max_brightness // 2  # 50% of max
                    with open(brightness_file, 'w') as f:
                        f.write(str(normal_brightness))
                    self.logger.info(f"Reset display brightness to normal: {normal_brightness}")
        except Exception as e:
            self.logger.warning(f"Could not reset display brightness: {e}")
            
        self.is_powerbank_active = False
        self.enter_sequence_count = 0
        
    def check_deactivation_sequence(self):
        """Check for 5 consecutive enter key presses to deactivate powerbank mode"""
        if not self.is_powerbank_active:
            return False
            
        try:
            # Check if stdin has data available (non-blocking)
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                char = sys.stdin.read(1)
                current_time = time.time()
                
                # Check if it's an enter key (\n or \r)
                if char in ['\n', '\r']:
                    # Reset sequence if too much time has passed since last enter
                    if current_time - self.last_enter_time > 2.0:  # 2 second timeout
                        self.enter_sequence_count = 1
                    else:
                        self.enter_sequence_count += 1
                    
                    self.last_enter_time = current_time
                    self.logger.info(f"Enter key pressed ({self.enter_sequence_count}/5)")
                    
                    if self.enter_sequence_count >= 5:
                        self.logger.info("🔓 5 enter keys detected. Deactivating POWERBANK mode.")
                        return True
                else:
                    # Reset sequence on any other key
                    self.enter_sequence_count = 0
                    
        except Exception as e:
            # Handle any input errors gracefully
            pass
            
        return False

class SkadiDaemon:
    """The Cold Dominion - Primary Skadi daemon"""
    
    def __init__(self, config_path: str = "/home/adminx/Marina/Skadi/config.json"):
        self.config_path = Path(config_path)
        self.load_config()
        
        # Initialize Frost Tomes
        self.frost_tome = FrostTome(self.config['frost_tome_path'])
        
        # Active contracts and system state
        self.active_contracts: Dict[str, RunicContract] = {}
        self.current_stance = SkadiStance.RIDGEWATCH
        self.entropy_discipline_score = 100.0  # User's energy honor rating
        
        # System monitoring
        self.thermal_threshold = self.config.get('thermal_threshold', 65.0)  # °C
        self.battery_critical = self.config.get('battery_critical', 15.0)  # %
        
        # Planck-time tracking (using seconds for practical implementation)
        self.planck_tick = 0
        
        self.setup_logging()
        
        # Initialize PowerBank Manager
        self.powerbank_manager = PowerBankManager(self.logger)
        
        self.frost_tome.record_event('skadi_awakening', {
            'stance': self.current_stance.value,
            'thermal_threshold': self.thermal_threshold,
            'entropy_discipline': self.entropy_discipline_score
        })
        
    def load_config(self):
        """Load Skadi configuration from JSON"""
        default_config = {
            'frost_tome_path': '/home/adminx/Marina/Skadi/frost_tomes',
            'thermal_threshold': 65.0,
            'battery_critical': 15.0,
            'update_interval': 5.0,
            'silence_hours': [22, 23, 0, 1, 2, 3, 4, 5, 6],  # Night hours for auto-silence
            'trusted_processes': ['marina', 'ceto', 'siren'],
            'banished_processes': []  # Processes under thermal banishment
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except (json.JSONDecodeError, IOError):
                pass
                
        self.config = default_config
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def setup_logging(self):
        """Initialize logging for Skadi"""
        log_path = Path("/home/adminx/Marina/Skadi/logs")
        log_path.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - Skadi - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path / 'skadi.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Skadi')
        
    def get_system_entropy(self) -> Dict[str, float]:
        """Calculate current system entropy metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_temp = 0.0
            
            # Try to get CPU temperature
            try:
                temps = psutil.sensors_temperatures()
                if 'coretemp' in temps:
                    cpu_temp = max([temp.current for temp in temps['coretemp']])
                elif 'cpu_thermal' in temps:
                    cpu_temp = temps['cpu_thermal'][0].current
            except (AttributeError, KeyError):
                pass
                
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Battery metrics
            battery = psutil.sensors_battery()
            battery_percent = battery.percent if battery else 100.0
            battery_charging = battery.power_plugged if battery else False
            
            # Calculate entropy in Eᛞ units (normalized 0-100)
            thermal_entropy = min(cpu_temp / self.thermal_threshold * 50, 50)
            compute_entropy = cpu_percent * 0.3
            memory_entropy = memory.percent * 0.2
            
            total_entropy = thermal_entropy + compute_entropy + memory_entropy
            
            return {
                'total_entropy': total_entropy,
                'thermal_entropy': thermal_entropy,
                'compute_entropy': compute_entropy,
                'memory_entropy': memory_entropy,
                'cpu_temp': cpu_temp,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'battery_percent': battery_percent,
                'battery_charging': battery_charging,
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.error(f"Error calculating entropy: {e}")
            return {'total_entropy': 0, 'timestamp': time.time()}
            
    def evaluate_stance(self, entropy_metrics: Dict[str, float]) -> SkadiStance:
        """Determine appropriate stance based on current entropy"""
        current_hour = datetime.now().hour
        
        # Rapid charge when plugged in and under 80%
        if entropy_metrics.get('battery_charging') and entropy_metrics['battery_percent'] < 80:
            return SkadiStance.RAPID_CHARGE
        
        # Silence hours - auto switch to quiet modes
        if current_hour in self.config['silence_hours']:
            if entropy_metrics['battery_percent'] < 30:
                return SkadiStance.GLACIER
            else:
                return SkadiStance.SNOWBLIND
                
        # Thermal emergency
        if entropy_metrics['cpu_temp'] > self.thermal_threshold:
            return SkadiStance.GLACIER
            
        # Battery critical
        if entropy_metrics['battery_percent'] < self.battery_critical:
            return SkadiStance.GLACIER
            
        # High load situations
        if entropy_metrics['cpu_percent'] > 80 and entropy_metrics['battery_percent'] > 50:
            return SkadiStance.STORMBIRTH
            
        # Default balanced mode
        return SkadiStance.RIDGEWATCH
        
    def create_runic_contract(self, agent: str, intent: str, 
                            estimated_cost: float, duration: int) -> str:
        """Create a new runic energy contract"""
        # Generate sigil based on intent
        sigil_mapping = {
            'compute_heavy': 'ᚢᚷᚺ',  # intent + cost + fate
            'background_task': 'ᛞᚢ',   # deferral + intent
            'emergency': 'ᛇᚢᚷ',       # trusted + intent + cost
            'maintenance': 'ᚠᛞ'        # efficient + deferral
        }
        
        sigil = sigil_mapping.get(intent, 'ᚢᚷᚺ')
        
        # Determine collapse trigger
        if estimated_cost > 50:  # High entropy cost
            collapse_trigger = f"temp_core > {self.thermal_threshold}°C"
        elif duration > 3600:  # Long running
            collapse_trigger = "entropy_discipline < 80"
        else:
            collapse_trigger = f"max_duration_{duration}s"
            
        contract = RunicContract(
            agent=agent,
            sigil=sigil,
            entropy_cost=estimated_cost,
            max_duration=duration,
            collapse_trigger=collapse_trigger
        )
        
        self.active_contracts[contract.contract_id] = contract
        
        self.frost_tome.record_event('contract_created', {
            'contract': contract.to_dict(),
            'current_stance': self.current_stance.value
        })
        
        return contract.contract_id
        
    def revoke_contract(self, contract_id: str, reason: str = "completion"):
        """Revoke an active runic contract"""
        if contract_id in self.active_contracts:
            contract = self.active_contracts[contract_id]
            contract.active = False
            
            self.frost_tome.record_event('contract_revoked', {
                'contract_id': contract_id,
                'agent': contract.agent,
                'reason': reason,
                'duration_active': (datetime.now(timezone.utc) - contract.created_at).total_seconds()
            })
            
            del self.active_contracts[contract_id]
            return True
        return False
        
    def enforce_thermal_discipline(self, entropy_metrics: Dict[str, float]):
        """Enforce thermal discipline on misbehaving processes"""
        if entropy_metrics['cpu_temp'] > self.thermal_threshold * 1.1:  # 10% over threshold
            # Find high-CPU processes
            high_cpu_procs = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    if proc.info['cpu_percent'] > 20:  # High CPU usage
                        high_cpu_procs.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # Thermal banishment for repeat offenders
            for proc in high_cpu_procs:
                proc_name = proc['name']
                if proc_name not in self.config['trusted_processes']:
                    if proc_name not in self.config['banished_processes']:
                        self.config['banished_processes'].append(proc_name)
                        self.frost_tome.record_event('thermal_banishment', {
                            'process': proc_name,
                            'cpu_percent': proc['cpu_percent'],
                            'thermal_trigger': entropy_metrics['cpu_temp']
                        })
                        
                        # Attempt to throttle process (basic implementation)
                        try:
                            os.system(f"sudo renice +10 {proc['pid']}")
                        except:
                            pass
                            
    def whisper_status(self) -> str:
        """Generate Skadi's ritual status message"""
        entropy_metrics = self.get_system_entropy()
        
        # Generate poetic status based on current state
        if self.current_stance == SkadiStance.GLACIER:
            status = "The system sleeps beneath the ice. All is preserved."
        elif self.current_stance == SkadiStance.RAPID_CHARGE:
            status = "Harnessing the storm to replenish the wellspring. Charging..."
        elif self.current_stance == SkadiStance.SNOWBLIND:
            status = "Silent strength holds longest."
        elif self.current_stance == SkadiStance.STORMBIRTH:
            status = "You summon the mountain. Prepare for the climb."
        elif self.current_stance == SkadiStance.POWERBANK:
            status = "🔋 Conservation mode: Only USB and keyboard remain. Press ENTER 5x to awaken."
        else:
            status = "Balanced on the ridgeline. Watching."
            
        return {
            'status': status,
            'stance': self.current_stance.value,
            'entropy': round(entropy_metrics['total_entropy'], 2),
            'temperature': round(entropy_metrics['cpu_temp'], 1),
            'active_contracts': len(self.active_contracts),
            'discipline_score': self.entropy_discipline_score,
            'planck_tick': self.planck_tick
        }
        
    async def main_loop(self):
        """Main Skadi daemon loop"""
        self.logger.info("🌨️  Skadi awakens. The Cold Dominion begins.")
        
        try:
            while True:
                self.planck_tick += 1
                
                # Get current system entropy
                entropy_metrics = self.get_system_entropy()
                
                # Check for powerbank mode deactivation
                if self.powerbank_manager.check_deactivation_sequence():
                    self.powerbank_manager.enable_critical_io()
                    self.frost_tome.record_event('powerbank_deactivated', {
                        'deactivation_method': '5_enter_sequence',
                        'entropy_state': entropy_metrics
                    })
                    # Force stance re-evaluation after powerbank exit
                    new_stance = self.evaluate_stance(entropy_metrics)
                    if new_stance != self.current_stance:
                        old_stance = self.current_stance
                        self.current_stance = new_stance
                        self.logger.info(f"Post-powerbank stance transition: {old_stance.value} → {new_stance.value}")
                        self.frost_tome.record_event('stance_change', {
                            'old_stance': old_stance.value,
                            'new_stance': new_stance.value,
                            'trigger_entropy': entropy_metrics,
                            'post_powerbank': True
                        })
                
                # Evaluate and potentially change stance
                new_stance = self.evaluate_stance(entropy_metrics)
                if new_stance != self.current_stance:
                    old_stance = self.current_stance
                    self.current_stance = new_stance
                    
                    # Handle POWERBANK mode activation
                    if new_stance == SkadiStance.POWERBANK and not self.powerbank_manager.is_powerbank_active:
                        self.powerbank_manager.disable_non_critical_io()
                        self.frost_tome.record_event('powerbank_activated', {
                            'trigger_entropy': entropy_metrics,
                            'previous_stance': old_stance.value
                        })
                    
                    self.logger.info(f"Stance transition: {old_stance.value} → {new_stance.value}")
                    self.frost_tome.record_event('stance_change', {
                        'old_stance': old_stance.value,
                        'new_stance': new_stance.value,
                        'trigger_entropy': entropy_metrics
                    })
                    
                # Enforce thermal discipline
                self.enforce_thermal_discipline(entropy_metrics)
                
                # Check contract violations
                expired_contracts = []
                for contract_id, contract in self.active_contracts.items():
                    age = (datetime.now(timezone.utc) - contract.created_at).total_seconds()
                    if age > contract.max_duration:
                        expired_contracts.append((contract_id, "max_duration_exceeded"))
                    elif "temp_core" in contract.collapse_trigger:
                        threshold = float(contract.collapse_trigger.split('>')[1].replace('°C', '').strip())
                        if entropy_metrics['cpu_temp'] > threshold:
                            expired_contracts.append((contract_id, "thermal_threshold_violated"))
                            
                # Revoke expired contracts
                for contract_id, reason in expired_contracts:
                    self.revoke_contract(contract_id, reason)
                    
                # Record entropy state
                if self.planck_tick % 12 == 0:  # Every minute at 5-second intervals
                    self.frost_tome.record_event('entropy_measurement', entropy_metrics)
                    
                await asyncio.sleep(self.config['update_interval'])
                
        except KeyboardInterrupt:
            self.logger.info("🌨️  Skadi enters the Long Winter...")
            self.frost_tome.record_event('skadi_dormancy', {
                'final_stance': self.current_stance.value,
                'final_entropy': entropy_metrics,
                'contracts_terminated': len(self.active_contracts)
            })
            
def main():
    """Entry point for Skadi daemon"""
    daemon = SkadiDaemon()
    
    # Handle signals gracefully
    def signal_handler(signum, frame):
        daemon.logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the daemon
    asyncio.run(daemon.main_loop())

if __name__ == "__main__":
    main()
