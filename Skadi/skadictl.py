#!/usr/bin/env python3
"""
❄️ SkadiCtl - Command Line Interface for Skadi Power Management
The Cold Dominion's ritual interface for energy governance

Commands speak in the ancient tongue of runes and thermal discipline.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import psutil

# Nordic runes for display
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

class SkadiClient:
    """Client for interacting with Skadi power daemon"""
    
    def __init__(self, base_path: str = "/home/adminx/Marina/Skadi"):
        self.base_path = Path(base_path)
        self.config_file = self.base_path / "config.json"
        self.frost_tomes_path = self.base_path / "frost_tomes"
        
    def load_config(self) -> Dict[str, Any]:
        """Load Skadi configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❄️ Error reading Skadi configuration: {e}")
            return {}
    
    def get_system_entropy(self) -> Dict[str, float]:
        """Get current system entropy metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
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
            
            # Calculate entropy in Eᛞ units
            thermal_entropy = min(cpu_temp / 65.0 * 50, 50) if cpu_temp > 0 else 0
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
                'timestamp': time.time()
            }
        except Exception as e:
            print(f"❄️ Error calculating entropy: {e}")
            return {'total_entropy': 0, 'timestamp': time.time()}
    
    def get_stance_from_entropy(self, entropy_metrics: Dict[str, float]) -> str:
        """Determine stance based on entropy"""
        current_hour = datetime.now().hour
        
        # Night hours (22-6)
        if current_hour >= 22 or current_hour <= 6:
            if entropy_metrics['battery_percent'] < 30:
                return "GLACIER"
            else:
                return "SNOWBLIND"
                
        # Thermal emergency
        if entropy_metrics['cpu_temp'] > 65:
            return "GLACIER"
            
        # Battery critical
        if entropy_metrics['battery_percent'] < 15:
            return "GLACIER"
            
        # High load situations
        if entropy_metrics['cpu_percent'] > 80 and entropy_metrics['battery_percent'] > 50:
            return "STORMBIRTH"
            
        # Default balanced mode
        return "RIDGEWATCH"
    
    def whisper_status(self):
        """Show Skadi's current status with mythological flair"""
        print("🌨️  ═══ SKADI - THE COLD DOMINION ═══")
        
        # Display custom Skadi ASCII art
        skadi_art = """
        ❄️        ⛄        ❄️
      ⚡   ╔═══════════╗   ⚡
         ║  ❄️ SKADI ❄️  ║
         ║ ⚔️ GODDESS ⚔️ ║
         ╚═══════════╝
        🏔️       🌨️       🏔️
        """
        print(skadi_art)
        
        print("    Goddess of Power, Entropy Suppression, and Thermal Harmony")
        print()
        
        # Get current entropy
        entropy_metrics = self.get_system_entropy()
        stance = self.get_stance_from_entropy(entropy_metrics)
        
        # Generate poetic status
        if stance == "GLACIER":
            status_msg = "❄️  The system sleeps beneath the ice. All is preserved."
        elif stance == "SNOWBLIND":
            status_msg = "🌫️  Silent strength holds longest."
        elif stance == "STORMBIRTH":
            status_msg = "⛈️  You summon the mountain. Prepare for the climb."
        elif stance == "POWERBANK":
            status_msg = "🔋 Conservation mode: Only USB and keyboard remain. Press ENTER 5x to awaken."
        else:
            status_msg = "🏔️  Balanced on the ridgeline. Watching."
        
        print(f"📿 Status: {status_msg}")
        print(f"🥶 Stance: {stance}")
        print()
        print("🌀 Entropy Measurements:")
        print(f"   ⚡ Total Entropy: {entropy_metrics['total_entropy']:.1f} Eᛞ")
        print(f"   🔥 Thermal: {entropy_metrics['thermal_entropy']:.1f} Eᛞ ({entropy_metrics['cpu_temp']:.1f}°C)")
        print(f"   💻 Compute: {entropy_metrics['compute_entropy']:.1f} Eᛞ ({entropy_metrics['cpu_percent']:.1f}%)")
        print(f"   🧠 Memory: {entropy_metrics['memory_entropy']:.1f} Eᛞ ({entropy_metrics['memory_percent']:.1f}%)")
        print(f"   🔋 Battery: {entropy_metrics['battery_percent']:.1f}%")
        print()
        
        # Show thermal discipline
        try:
            high_cpu_procs = []
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                try:
                    if proc.info['cpu_percent'] > 15:  # High CPU usage
                        high_cpu_procs.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if high_cpu_procs:
                print("⚔️  Processes Under Watch:")
                for proc in sorted(high_cpu_procs, key=lambda x: x['cpu_percent'], reverse=True)[:5]:
                    print(f"   🔍 {proc['name']}: {proc['cpu_percent']:.1f}% CPU")
            else:
                print("✨ All processes in thermal harmony")
        except:
            pass
            
        print()
    
    def show_frost_tomes(self, hours_back: int = 6):
        """Display entries from the Frost Tomes (entropy logs)"""
        print("📚 ═══ FROST TOMES - ENTROPY ARCHIVE ═══")
        print(f"    Showing events from the last {hours_back} hours")
        print()
        
        events = []
        cutoff_time = datetime.now(timezone.utc).timestamp() - (hours_back * 3600)
        
        if not self.frost_tomes_path.exists():
            print("❄️ No Frost Tomes found. Skadi has not yet awakened.")
            return
        
        # Read from tome files
        for tome_file in self.frost_tomes_path.glob("frost_tome_*.json"):
            try:
                with open(tome_file, 'r') as f:
                    tome_data = json.load(f)
                    for event in tome_data.get('events', []):
                        event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                        if event_time >= cutoff_time:
                            events.append(event)
            except (json.JSONDecodeError, KeyError):
                continue
        
        if not events:
            print("🌫️  Silence reigns. No recent entropy events recorded.")
            return
        
        # Sort by timestamp
        events.sort(key=lambda x: x['timestamp'])
        
        event_emojis = {
            'skadi_awakening': '🌨️',
            'stance_change': '🔄',
            'entropy_measurement': '📊',
            'contract_created': '📜',
            'contract_revoked': '🗡️',
            'thermal_banishment': '❄️',
            'skadi_dormancy': '💤'
        }
        
        for event in events[-20:]:  # Show last 20 events
            emoji = event_emojis.get(event['event_type'], '⚡')
            timestamp = datetime.fromisoformat(event['timestamp']).strftime('%H:%M:%S')
            event_type = event['event_type'].replace('_', ' ').title()
            
            print(f"{emoji} {timestamp} - {event_type}")
            
            # Show relevant data
            data = event.get('data', {})
            if event['event_type'] == 'stance_change':
                print(f"    {data.get('old_stance', '?')} → {data.get('new_stance', '?')}")
            elif event['event_type'] == 'entropy_measurement':
                entropy = data.get('total_entropy', 0)
                temp = data.get('cpu_temp', 0)
                print(f"    Entropy: {entropy:.1f} Eᛞ, Temp: {temp:.1f}°C")
            elif event['event_type'] == 'thermal_banishment':
                process = data.get('process', 'unknown')
                cpu = data.get('cpu_percent', 0)
                print(f"    Process '{process}' banished ({cpu:.1f}% CPU)")
        
        print()
    
    def invoke_ritual(self, ritual_name: str):
        """Invoke a Skadi ritual (if daemon is running)"""
        print(f"🔮 Invoking ritual: {ritual_name}")
        
        ritual_descriptions = {
            'containment': 'Constrains sudden thermal surges',
            'crystal-silence': 'Enter deep freeze mode',
            'ice-mirror': 'Mirror power behavior of another config',
            'storm-knot': 'Full system burst mode (timed)'
        }
        
        if ritual_name in ritual_descriptions:
            print(f"📿 Purpose: {ritual_descriptions[ritual_name]}")
            print("⚠️  Note: This requires Skadi daemon to be running")
            print("💡 Use 'cetoctl start skadi_power_daemon' to awaken Skadi")
        else:
            print(f"❄️ Unknown ritual: {ritual_name}")
            print("Available rituals: containment, crystal-silence, ice-mirror, storm-knot")
    
    def show_runic_contracts(self):
        """Show information about runic contracts"""
        print("📜 ═══ RUNIC CONTRACTS - ENERGY GOVERNANCE ═══")
        print()
        print("Skadi governs system energy through formal contracts:")
        print()
        
        for rune, meaning in RUNES.items():
            print(f"  {rune}  {meaning.replace('_', ' ').title()}")
        
        print()
        print("🔮 Contract Types:")
        print("  ᚢᚷᚺ  High-entropy compute tasks")
        print("  ᛞᚢ   Background deferred processes")  
        print("  ᛇᚢᚷ  Emergency operations")
        print("  ᚠᛞ   Efficient maintenance tasks")
        print()
        print("💡 Contracts are automatically created when Skadi daemon runs")
    
    def daemon_control(self, action: str):
        """Control Skadi daemon through Ceto"""
        print(f"🐚 {action.title()}ing Skadi through Ceto...")
        
        try:
            ceto_path = Path("/home/adminx/Marina/Ceto")
            result = subprocess.run([
                "python3", str(ceto_path / "cetoctl.py"), 
                action, "skadi_power_daemon"
            ], capture_output=True, text=True, cwd=ceto_path)
            
            if result.returncode == 0:
                print(f"✅ Skadi daemon {action} request submitted")
                if result.stdout.strip():
                    print(result.stdout.strip())
            else:
                print(f"❌ Error {action}ing Skadi:")
                if result.stderr.strip():
                    print(result.stderr.strip())
                    
        except Exception as e:
            print(f"❄️ Error controlling daemon: {e}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="❄️ SkadiCtl - Command the Cold Dominion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🌨️  Skadi Commands:
  status        Show current entropy state and thermal discipline
  tomes         View the Frost Tomes (entropy event log)
  contracts     Display runic contract information
  ritual        Invoke a power management ritual
  start         Awaken Skadi daemon
  stop          Send Skadi to dormancy
  restart       Restart Skadi daemon

❄️  Examples:
  skadictl status                    # Check current thermal state
  skadictl tomes --hours 12          # View 12 hours of entropy logs
  skadictl ritual containment        # Invoke thermal containment
  skadictl start                     # Awaken the Cold Dominion
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show Skadi status and entropy')
    
    # Frost Tomes command
    tomes_parser = subparsers.add_parser('tomes', help='View entropy event logs')
    tomes_parser.add_argument('--hours', type=int, default=6, 
                             help='Hours of history to show (default: 6)')
    
    # Contracts command
    contracts_parser = subparsers.add_parser('contracts', help='Show runic contract info')
    
    # Ritual command
    ritual_parser = subparsers.add_parser('ritual', help='Invoke a Skadi ritual')
    ritual_parser.add_argument('name', choices=['containment', 'crystal-silence', 'ice-mirror', 'storm-knot'],
                              help='Ritual to invoke')
    
    # Daemon control commands
    start_parser = subparsers.add_parser('start', help='Start Skadi daemon')
    stop_parser = subparsers.add_parser('stop', help='Stop Skadi daemon')
    restart_parser = subparsers.add_parser('restart', help='Restart Skadi daemon')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create client
    client = SkadiClient()
    
    # Execute command
    try:
        if args.command == 'status':
            client.whisper_status()
        elif args.command == 'tomes':
            client.show_frost_tomes(args.hours)
        elif args.command == 'contracts':
            client.show_runic_contracts()
        elif args.command == 'ritual':
            client.invoke_ritual(args.name)
        elif args.command == 'start':
            client.daemon_control('start')
        elif args.command == 'stop':
            client.daemon_control('stop')
        elif args.command == 'restart':
            client.daemon_control('restart')
        else:
            print(f"❄️ Unknown command: {args.command}")
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n❄️ Skadi command cancelled")
    except Exception as e:
        print(f"🌨️ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
