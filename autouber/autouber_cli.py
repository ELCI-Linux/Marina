#!/usr/bin/env python3
"""
Auto-Uber CLI
Command-line interface for Marina's Auto-Uber system
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Tuple

from auto_uber_daemon import AutoUberDaemon, TriggerMode

class AutoUberCLI:
    """Command-line interface for Auto-Uber"""
    
    def __init__(self):
        self.daemon = None
        
    def connect_daemon(self):
        """Connect to the running daemon"""
        try:
            self.daemon = AutoUberDaemon()
            return True
        except Exception as e:
            print(f"Error connecting to daemon: {e}")
            return False
    
    def parse_coordinates(self, coord_str: str) -> Tuple[float, float]:
        """Parse coordinate string like '37.7749,-122.4194'"""
        try:
            lat, lon = map(float, coord_str.split(','))
            return (lat, lon)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid coordinates format: {coord_str}")
    
    def parse_datetime(self, dt_str: str) -> datetime:
        """Parse datetime string"""
        try:
            return datetime.fromisoformat(dt_str)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Invalid datetime format: {dt_str}")
    
    def cmd_start(self, args):
        """Start the Auto-Uber daemon"""
        if not self.connect_daemon():
            return 1
            
        self.daemon.start()
        print("Auto-Uber daemon started successfully")
        return 0
    
    def cmd_stop(self, args):
        """Stop the Auto-Uber daemon"""
        if not self.connect_daemon():
            return 1
            
        self.daemon.stop()
        print("Auto-Uber daemon stopped successfully")
        return 0
    
    def cmd_status(self, args):
        """Show daemon status"""
        if not self.connect_daemon():
            return 1
        
        # Show active requests
        active_requests = self.daemon.get_active_requests()
        print(f"Active requests: {len(active_requests)}")
        
        for request in active_requests:
            print(f"  - {request.id}: {request.trigger_mode.value}")
            print(f"    Origin: {request.origin}")
            print(f"    Destination: {request.destination}")
            if request.appointment_time:
                print(f"    Appointment: {request.appointment_time}")
            print()
        
        # Show request history
        history = self.daemon.get_request_history()
        print(f"Recent history: {len(history)} completed requests")
        
        return 0
    
    def cmd_on_arrival(self, args):
        """Set up order-on-arrival trigger"""
        if not self.connect_daemon():
            return 1
        
        request_id = self.daemon.order_on_arrival(
            location=args.location,
            destination=args.destination,
            radius_m=args.radius,
            auto_confirm=args.auto_confirm
        )
        
        print(f"Set up order-on-arrival trigger: {request_id}")
        print(f"Will order Uber when you arrive at {args.location}")
        print(f"Destination: {args.destination}")
        return 0
    
    def cmd_on_approach(self, args):
        """Set up order-on-approach trigger"""
        if not self.connect_daemon():
            return 1
        
        request_id = self.daemon.order_on_approach(
            location=args.location,
            destination=args.destination,
            radius_m=args.radius,
            auto_confirm=args.auto_confirm
        )
        
        print(f"Set up order-on-approach trigger: {request_id}")
        print(f"Will order Uber when you approach {args.location}")
        print(f"Destination: {args.destination}")
        return 0
    
    def cmd_to_appointment(self, args):
        """Set up order-to-appointment trigger"""
        if not self.connect_daemon():
            return 1
        
        request_id = self.daemon.order_to_appointment(
            origin=args.origin,
            destination=args.destination,
            appointment_time=args.appointment_time,
            buffer_minutes=args.buffer,
            auto_confirm=args.auto_confirm
        )
        
        print(f"Set up order-to-appointment trigger: {request_id}")
        print(f"Will order Uber to get you from {args.origin} to {args.destination}")
        print(f"For appointment at: {args.appointment_time}")
        return 0
    
    def cmd_cancel(self, args):
        """Cancel an active request"""
        if not self.connect_daemon():
            return 1
        
        success = self.daemon.remove_request(args.request_id)
        if success:
            print(f"Cancelled request: {args.request_id}")
        else:
            print(f"Request not found: {args.request_id}")
            return 1
        return 0
    
    def cmd_list(self, args):
        """List all requests"""
        if not self.connect_daemon():
            return 1
        
        # Show active requests
        active_requests = self.daemon.get_active_requests()
        if active_requests:
            print("Active Requests:")
            for request in active_requests:
                print(f"  {request.id}: {request.trigger_mode.value}")
                print(f"    Created: {request.created_at}")
                print(f"    Origin: {request.origin}")
                print(f"    Destination: {request.destination}")
                if request.appointment_time:
                    print(f"    Appointment: {request.appointment_time}")
                print()
        else:
            print("No active requests")
        
        # Show history if requested
        if args.history:
            history = self.daemon.get_request_history()
            if history:
                print("Request History:")
                for request in history[-10:]:  # Show last 10
                    print(f"  {request.id}: {request.trigger_mode.value} (completed)")
                    print(f"    Created: {request.created_at}")
                    print()
        
        return 0
    
    def cmd_config(self, args):
        """Show or update configuration"""
        if not self.connect_daemon():
            return 1
        
        config_file = "/home/adminx/Marina/autouber/config.json"
        
        if args.show:
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(json.dumps(config, indent=2))
            except Exception as e:
                print(f"Error reading config: {e}")
                return 1
        
        # Could add config update functionality here
        return 0
    
    def run(self):
        """Main CLI entry point"""
        parser = argparse.ArgumentParser(
            description="Marina Auto-Uber CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Start the daemon
  autouber start
  
  # Order Uber when arriving at the theater
  autouber on-arrival 37.7749,-122.4194 37.7849,-122.4094
  
  # Order Uber when approaching the bar
  autouber on-approach 37.7749,-122.4194 37.7849,-122.4094 --radius 100
  
  # Order Uber for 8pm appointment
  autouber to-appointment 37.7749,-122.4194 37.7849,-122.4094 "2024-01-20T20:00:00"
  
  # Show status
  autouber status
  
  # List all requests
  autouber list --history
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Start command
        start_parser = subparsers.add_parser('start', help='Start the Auto-Uber daemon')
        
        # Stop command
        stop_parser = subparsers.add_parser('stop', help='Stop the Auto-Uber daemon')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show daemon status')
        
        # On-arrival command
        arrival_parser = subparsers.add_parser('on-arrival', help='Order Uber when arriving at location')
        arrival_parser.add_argument('location', type=self.parse_coordinates, 
                                  help='Trigger location (lat,lon)')
        arrival_parser.add_argument('destination', type=self.parse_coordinates,
                                   help='Uber destination (lat,lon)')
        arrival_parser.add_argument('--radius', type=int, default=200,
                                   help='Trigger radius in meters (default: 200)')
        arrival_parser.add_argument('--auto-confirm', action='store_true',
                                   help='Auto-confirm without asking')
        
        # On-approach command
        approach_parser = subparsers.add_parser('on-approach', help='Order Uber when approaching location')
        approach_parser.add_argument('location', type=self.parse_coordinates,
                                    help='Trigger location (lat,lon)')
        approach_parser.add_argument('destination', type=self.parse_coordinates,
                                    help='Uber destination (lat,lon)')
        approach_parser.add_argument('--radius', type=int, default=200,
                                    help='Trigger radius in meters (default: 200)')
        approach_parser.add_argument('--auto-confirm', action='store_true',
                                    help='Auto-confirm without asking')
        
        # To-appointment command
        appointment_parser = subparsers.add_parser('to-appointment', help='Order Uber for appointment')
        appointment_parser.add_argument('origin', type=self.parse_coordinates,
                                       help='Pickup location (lat,lon)')
        appointment_parser.add_argument('destination', type=self.parse_coordinates,
                                       help='Drop-off location (lat,lon)')
        appointment_parser.add_argument('appointment_time', type=self.parse_datetime,
                                       help='Appointment time (ISO format)')
        appointment_parser.add_argument('--buffer', type=int, default=5,
                                       help='Buffer minutes before appointment (default: 5)')
        appointment_parser.add_argument('--auto-confirm', action='store_true',
                                       help='Auto-confirm without asking')
        
        # Cancel command
        cancel_parser = subparsers.add_parser('cancel', help='Cancel an active request')
        cancel_parser.add_argument('request_id', help='Request ID to cancel')
        
        # List command
        list_parser = subparsers.add_parser('list', help='List requests')
        list_parser.add_argument('--history', action='store_true',
                                help='Include request history')
        
        # Config command
        config_parser = subparsers.add_parser('config', help='Configuration management')
        config_parser.add_argument('--show', action='store_true',
                                  help='Show current configuration')
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return 1
        
        # Map commands to methods
        command_map = {
            'start': self.cmd_start,
            'stop': self.cmd_stop,
            'status': self.cmd_status,
            'on-arrival': self.cmd_on_arrival,
            'on-approach': self.cmd_on_approach,
            'to-appointment': self.cmd_to_appointment,
            'cancel': self.cmd_cancel,
            'list': self.cmd_list,
            'config': self.cmd_config,
        }
        
        if args.command in command_map:
            return command_map[args.command](args)
        else:
            print(f"Unknown command: {args.command}")
            return 1

if __name__ == "__main__":
    cli = AutoUberCLI()
    exit_code = cli.run()
    sys.exit(exit_code)
