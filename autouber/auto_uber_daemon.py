#!/usr/bin/env python3
"""
Marina Auto-Uber Daemon
Intelligent rideshare automation with contextual triggers
"""

import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .uber_client import UberClient
    from .location_monitor import LocationMonitor
    from .scheduler import UberScheduler
except ImportError:
    from uber_client import UberClient
    from location_monitor import LocationMonitor
    from scheduler import UberScheduler

class TriggerMode(Enum):
    ORDER_ON_ARRIVAL = "order_on_arrival"
    ORDER_ON_APPROACH = "order_on_approach" 
    ORDER_TO_APPOINTMENT = "order_to_appointment"

@dataclass
class UberRequest:
    id: str
    trigger_mode: TriggerMode
    origin: Tuple[float, float]  # (lat, lon)
    destination: Tuple[float, float]  # (lat, lon)
    trigger_location: Optional[Tuple[float, float]] = None
    trigger_radius_m: int = 200
    appointment_time: Optional[datetime] = None
    buffer_minutes: int = 5
    preferred_ride_type: str = "UberX"
    max_budget: Optional[float] = None
    auto_confirm: bool = False
    active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class AutoUberDaemon:
    """
    Main Auto-Uber daemon managing intelligent ride requests
    """
    
    def __init__(self, config_path: str = "/home/adminx/Marina/autouber/config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.uber_client = UberClient(self.config.get("uber", {}))
        self.location_monitor = LocationMonitor(self.config.get("location", {}))
        self.scheduler = UberScheduler(self.config.get("scheduler", {}))
        
        # Request management
        self.active_requests: Dict[str, UberRequest] = {}
        self.request_history: List[UberRequest] = []
        
        # Threading
        self.running = False
        self.main_thread = None
        self.lock = threading.Lock()
        
        # Setup logging
        self._setup_logging()
        
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default configuration"""
        default_config = {
            "uber": {
                "client_id": "",
                "client_secret": "",
                "sandbox_mode": True,
                "default_ride_type": "UberX"
            },
            "location": {
                "update_interval_seconds": 30,
                "accuracy_threshold_meters": 50,
                "geofence_check_interval": 10
            },
            "scheduler": {
                "calendar_integration": True,
                "default_buffer_minutes": 5,
                "early_arrival_minutes": 2
            },
            "notifications": {
                "enabled": True,
                "marina_integration": True
            },
            "safety": {
                "require_confirmation": True,
                "max_daily_requests": 10,
                "home_location": [0.0, 0.0]
            }
        }
        
        # Save default config
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        return default_config
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - AutoUber - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/home/adminx/Marina/logs/autouber.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the Auto-Uber daemon"""
        if self.running:
            self.logger.warning("Daemon already running")
            return
            
        self.running = True
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        
        # Start components
        self.location_monitor.start()
        self.scheduler.start()
        
        self.logger.info("Auto-Uber daemon started")
    
    def stop(self):
        """Stop the Auto-Uber daemon"""
        self.running = False
        
        # Stop components
        self.location_monitor.stop()
        self.scheduler.stop()
        
        if self.main_thread:
            self.main_thread.join(timeout=5)
            
        self.logger.info("Auto-Uber daemon stopped")
    
    def _main_loop(self):
        """Main daemon processing loop"""
        while self.running:
            try:
                with self.lock:
                    self._process_active_requests()
                    self._process_scheduled_requests()
                    self._cleanup_completed_requests()
                
                time.sleep(1)  # Process every second
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _process_active_requests(self):
        """Process all active ride requests"""
        current_location = self.location_monitor.get_current_location()
        if not current_location:
            return
            
        for request_id, request in list(self.active_requests.items()):
            if not request.active:
                continue
                
            try:
                if request.trigger_mode == TriggerMode.ORDER_ON_ARRIVAL:
                    self._handle_arrival_trigger(request, current_location)
                elif request.trigger_mode == TriggerMode.ORDER_ON_APPROACH:
                    self._handle_approach_trigger(request, current_location)
                elif request.trigger_mode == TriggerMode.ORDER_TO_APPOINTMENT:
                    self._handle_appointment_trigger(request, current_location)
                    
            except Exception as e:
                self.logger.error(f"Error processing request {request_id}: {e}")
    
    def _handle_arrival_trigger(self, request: UberRequest, current_location: Tuple[float, float]):
        """Handle order-on-arrival logic"""
        if not request.trigger_location:
            return
            
        distance = self._calculate_distance(current_location, request.trigger_location)
        
        # Check if we've arrived at the trigger location
        if distance <= request.trigger_radius_m:
            self.logger.info(f"Arrived at trigger location for request {request.id}")
            
            # Wait a bit to ensure we're settled at the location
            time.sleep(30)
            
            # Trigger the ride
            self._trigger_uber_request(request)
    
    def _handle_approach_trigger(self, request: UberRequest, current_location: Tuple[float, float]):
        """Handle order-on-approach logic"""
        if not request.trigger_location:
            return
            
        distance = self._calculate_distance(current_location, request.trigger_location)
        
        # Check if we're approaching the trigger location
        if distance <= request.trigger_radius_m:
            self.logger.info(f"Approaching trigger location for request {request.id}")
            
            # Estimate arrival time at location and pre-order
            estimated_arrival = self._estimate_arrival_time(current_location, request.trigger_location)
            uber_eta = self.uber_client.get_estimated_pickup_time(request.origin)
            
            # Order if Uber will arrive around the time we reach the location
            if abs(estimated_arrival - uber_eta) < timedelta(minutes=3):
                self._trigger_uber_request(request)
    
    def _handle_appointment_trigger(self, request: UberRequest, current_location: Tuple[float, float]):
        """Handle order-to-appointment logic"""
        if not request.appointment_time:
            return
            
        now = datetime.now()
        time_to_appointment = request.appointment_time - now
        
        # Calculate when to order the Uber
        uber_eta = self.uber_client.get_estimated_pickup_time(request.origin)
        travel_time = self.uber_client.get_estimated_travel_time(request.origin, request.destination)
        buffer_time = timedelta(minutes=request.buffer_minutes)
        
        total_time_needed = uber_eta + travel_time + buffer_time
        
        # Order if it's time
        if time_to_appointment <= total_time_needed:
            self.logger.info(f"Ordering Uber for appointment at {request.appointment_time}")
            self._trigger_uber_request(request)
    
    def _trigger_uber_request(self, request: UberRequest):
        """Actually trigger the Uber request"""
        try:
            # Check safety constraints
            if not self._safety_check(request):
                self.logger.warning(f"Safety check failed for request {request.id}")
                return
                
            # Request confirmation if required
            if not request.auto_confirm and self.config["safety"]["require_confirmation"]:
                if not self._request_confirmation(request):
                    self.logger.info(f"User declined confirmation for request {request.id}")
                    return
            
            # Make the Uber request
            ride_id = self.uber_client.request_ride(
                origin=request.origin,
                destination=request.destination,
                ride_type=request.preferred_ride_type
            )
            
            if ride_id:
                self.logger.info(f"Successfully ordered Uber (ID: {ride_id}) for request {request.id}")
                self._notify_user(f"Uber ordered! Ride ID: {ride_id}")
                
                # Mark request as completed
                request.active = False
                self.request_history.append(request)
                
            else:
                self.logger.error(f"Failed to order Uber for request {request.id}")
                
        except Exception as e:
            self.logger.error(f"Error triggering Uber request {request.id}: {e}")
    
    def _safety_check(self, request: UberRequest) -> bool:
        """Perform safety checks before ordering"""
        # Check daily limit
        today = datetime.now().date()
        daily_count = sum(1 for r in self.request_history 
                         if r.created_at.date() == today)
        
        if daily_count >= self.config["safety"]["max_daily_requests"]:
            return False
            
        # Check budget constraints
        if request.max_budget:
            estimated_cost = self.uber_client.get_estimated_cost(
                request.origin, request.destination, request.preferred_ride_type
            )
            if estimated_cost and estimated_cost > request.max_budget:
                return False
        
        return True
    
    def _request_confirmation(self, request: UberRequest) -> bool:
        """Request user confirmation for ride"""
        # Integration with Marina's notification system
        message = f"Confirm Uber request from {request.origin} to {request.destination}?"
        
        # For now, return True (auto-confirm)
        # In production, this would integrate with Marina's UI/voice system
        return True
    
    def _notify_user(self, message: str):
        """Send notification to user through Marina"""
        self.logger.info(f"Notification: {message}")
        
        # Integration with Marina's notification system
        if self.config["notifications"]["marina_integration"]:
            try:
                # Write to Marina's notification system
                notification = {
                    "timestamp": datetime.now().isoformat(),
                    "module": "AutoUber",
                    "message": message,
                    "priority": "normal"
                }
                
                with open("/home/adminx/Marina/logs/notifications.json", "a") as f:
                    f.write(json.dumps(notification) + "\n")
                    
            except Exception as e:
                self.logger.error(f"Failed to send notification: {e}")
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in meters"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Haversine formula
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Earth radius in meters
        
        return c * r
    
    def _estimate_arrival_time(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> timedelta:
        """Estimate time to reach destination"""
        distance = self._calculate_distance(origin, destination)
        # Assume walking speed of 1.4 m/s (5 km/h)
        walking_time_seconds = distance / 1.4
        return timedelta(seconds=walking_time_seconds)
    
    def _process_scheduled_requests(self):
        """Process any scheduled requests from the scheduler"""
        scheduled = self.scheduler.get_ready_requests()
        for request_data in scheduled:
            try:
                request = UberRequest(**request_data)
                self.add_request(request)
            except Exception as e:
                self.logger.error(f"Error processing scheduled request: {e}")
    
    def _cleanup_completed_requests(self):
        """Clean up old completed requests"""
        # Remove requests older than 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.request_history = [
            r for r in self.request_history 
            if r.created_at > cutoff_time
        ]
    
    # Public API methods
    
    def add_request(self, request: UberRequest):
        """Add a new Uber request"""
        with self.lock:
            self.active_requests[request.id] = request
            self.logger.info(f"Added new request: {request.id} ({request.trigger_mode.value})")
    
    def remove_request(self, request_id: str):
        """Remove an active request"""
        with self.lock:
            if request_id in self.active_requests:
                del self.active_requests[request_id]
                self.logger.info(f"Removed request: {request_id}")
                return True
            return False
    
    def get_active_requests(self) -> List[UberRequest]:
        """Get all active requests"""
        with self.lock:
            return list(self.active_requests.values())
    
    def get_request_history(self) -> List[UberRequest]:
        """Get request history"""
        return self.request_history.copy()
    
    # Convenience methods for different trigger types
    
    def order_on_arrival(self, location: Tuple[float, float], destination: Tuple[float, float], 
                        radius_m: int = 200, **kwargs) -> str:
        """Set up order-on-arrival trigger"""
        request_id = f"arrival_{int(time.time())}"
        request = UberRequest(
            id=request_id,
            trigger_mode=TriggerMode.ORDER_ON_ARRIVAL,
            origin=location,
            destination=destination,
            trigger_location=location,
            trigger_radius_m=radius_m,
            **kwargs
        )
        self.add_request(request)
        return request_id
    
    def order_on_approach(self, location: Tuple[float, float], destination: Tuple[float, float],
                         radius_m: int = 200, **kwargs) -> str:
        """Set up order-on-approach trigger"""
        request_id = f"approach_{int(time.time())}"
        request = UberRequest(
            id=request_id,
            trigger_mode=TriggerMode.ORDER_ON_APPROACH,
            origin=location,
            destination=destination,
            trigger_location=location,
            trigger_radius_m=radius_m,
            **kwargs
        )
        self.add_request(request)
        return request_id
    
    def order_to_appointment(self, origin: Tuple[float, float], destination: Tuple[float, float],
                           appointment_time: datetime, buffer_minutes: int = 5, **kwargs) -> str:
        """Set up order-to-appointment trigger"""
        request_id = f"appointment_{int(time.time())}"
        request = UberRequest(
            id=request_id,
            trigger_mode=TriggerMode.ORDER_TO_APPOINTMENT,
            origin=origin,
            destination=destination,
            appointment_time=appointment_time,
            buffer_minutes=buffer_minutes,
            **kwargs
        )
        self.add_request(request)
        return request_id

if __name__ == "__main__":
    # CLI interface for testing
    daemon = AutoUberDaemon()
    daemon.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
