#!/usr/bin/env python3
"""
Uber Scheduler
Manages appointment-based ride scheduling with calendar integration
"""

import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import calendar

@dataclass
class ScheduledRide:
    id: str
    appointment_time: datetime
    origin: Tuple[float, float]
    destination: Tuple[float, float]
    buffer_minutes: int = 5
    ride_type: str = "UberX"
    calendar_event_id: Optional[str] = None
    auto_confirm: bool = False
    active: bool = True
    created_at: datetime = None
    processed: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class UberScheduler:
    """
    Manages scheduled Uber requests based on appointments and calendar events
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.calendar_integration = config.get("calendar_integration", True)
        self.default_buffer_minutes = config.get("default_buffer_minutes", 5)
        self.early_arrival_minutes = config.get("early_arrival_minutes", 2)
        
        # Scheduled rides
        self.scheduled_rides: Dict[str, ScheduledRide] = {}
        self.ready_requests: List[Dict] = []
        
        # Calendar integration
        self.calendar_sources = []
        self.last_calendar_sync = None
        
        # Threading
        self.running = False
        self.scheduler_thread = None
        self.calendar_thread = None
        self.lock = threading.Lock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize calendar sources
        self._init_calendar_sources()
        
        # Load persisted schedules
        self._load_scheduled_rides()
    
    def _init_calendar_sources(self):
        """Initialize calendar integration sources"""
        if self.calendar_integration:
            self.calendar_sources = [
                self._sync_google_calendar,
                self._sync_outlook_calendar, 
                self._sync_local_calendar,
                self._sync_marina_tasks  # Marina's internal task system
            ]
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            self.logger.warning("Scheduler already running")
            return
            
        self.running = True
        
        # Start main scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # Start calendar sync thread if enabled
        if self.calendar_integration:
            self.calendar_thread = threading.Thread(target=self._calendar_loop, daemon=True)
            self.calendar_thread.start()
        
        self.logger.info("Uber scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        if self.calendar_thread:
            self.calendar_thread.join(timeout=5)
            
        # Save scheduled rides
        self._save_scheduled_rides()
        
        self.logger.info("Uber scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler processing loop"""
        while self.running:
            try:
                with self.lock:
                    self._process_scheduled_rides()
                    self._cleanup_old_rides()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _calendar_loop(self):
        """Calendar synchronization loop"""
        while self.running:
            try:
                self._sync_calendars()
                time.sleep(1800)  # Sync every 30 minutes
                
            except Exception as e:
                self.logger.error(f"Error in calendar sync: {e}")
                time.sleep(3600)  # Wait 1 hour on error
    
    def _process_scheduled_rides(self):
        """Process scheduled rides and check if any should be triggered"""
        now = datetime.now()
        
        for ride_id, ride in list(self.scheduled_rides.items()):
            if not ride.active or ride.processed:
                continue
                
            # Calculate when to trigger the ride
            trigger_time = self._calculate_trigger_time(ride)
            
            if now >= trigger_time:
                self.logger.info(f"Scheduling ride {ride_id} for appointment at {ride.appointment_time}")
                
                # Create request data for the daemon
                request_data = {
                    "id": f"scheduled_{ride_id}",
                    "trigger_mode": "ORDER_TO_APPOINTMENT",
                    "origin": ride.origin,
                    "destination": ride.destination,
                    "appointment_time": ride.appointment_time,
                    "buffer_minutes": ride.buffer_minutes,
                    "preferred_ride_type": ride.ride_type,
                    "auto_confirm": ride.auto_confirm
                }
                
                # Add to ready requests
                self.ready_requests.append(request_data)
                
                # Mark as processed
                ride.processed = True
    
    def _calculate_trigger_time(self, ride: ScheduledRide) -> datetime:
        """Calculate when to trigger a ride request"""
        # For now, trigger 15 minutes before appointment
        # In production, this would use real-time estimates
        trigger_offset = timedelta(minutes=15)
        return ride.appointment_time - trigger_offset
    
    def _sync_calendars(self):
        """Sync with all calendar sources"""
        if not self.calendar_sources:
            return
            
        for source in self.calendar_sources:
            try:
                events = source()
                if events:
                    self._process_calendar_events(events)
            except Exception as e:
                self.logger.debug(f"Calendar source {source.__name__} failed: {e}")
        
        self.last_calendar_sync = datetime.now()
    
    def _sync_google_calendar(self) -> List[Dict]:
        """Sync with Google Calendar"""
        # This would integrate with Google Calendar API
        # For now, return empty list
        return []
    
    def _sync_outlook_calendar(self) -> List[Dict]:
        """Sync with Outlook Calendar"""
        # This would integrate with Microsoft Graph API
        # For now, return empty list
        return []
    
    def _sync_local_calendar(self) -> List[Dict]:
        """Sync with local calendar files (ICS)"""
        try:
            # Look for calendar files in common locations
            import os
            calendar_paths = [
                os.path.expanduser("~/.local/share/evolution/calendar/"),
                os.path.expanduser("~/.thunderbird/*/calendar-data/"),
                os.path.expanduser("~/Calendar/")
            ]
            
            events = []
            for path in calendar_paths:
                if os.path.exists(path):
                    events.extend(self._parse_ics_files(path))
            
            return events
            
        except Exception as e:
            self.logger.debug(f"Local calendar sync failed: {e}")
            return []
    
    def _sync_marina_tasks(self) -> List[Dict]:
        """Sync with Marina's internal task/appointment system"""
        try:
            import os
            # Check Marina's task files
            marina_tasks_path = "/home/adminx/Marina/brain/tasks.json"
            if os.path.exists(marina_tasks_path):
                with open(marina_tasks_path, 'r') as f:
                    tasks = json.load(f)
                
                events = []
                for task in tasks.get("tasks", []):
                    if "appointment_time" in task and "location" in task:
                        events.append({
                            "id": task.get("id"),
                            "title": task.get("title", "Task"),
                            "start_time": task["appointment_time"],
                            "location": task["location"],
                            "description": task.get("description", "")
                        })
                
                return events
                
        except Exception as e:
            self.logger.debug(f"Marina tasks sync failed: {e}")
            return []
    
    def _parse_ics_files(self, directory: str) -> List[Dict]:
        """Parse ICS calendar files"""
        # This would use a library like icalendar to parse ICS files
        # For now, return empty list
        return []
    
    def _process_calendar_events(self, events: List[Dict]):
        """Process calendar events and create ride schedules"""
        for event in events:
            try:
                # Check if event needs transportation
                if not self._should_schedule_ride(event):
                    continue
                
                # Extract location information
                origin, destination = self._extract_locations(event)
                if not origin or not destination:
                    continue
                
                # Create scheduled ride
                ride_id = f"cal_{event.get('id', int(time.time()))}"
                
                if ride_id not in self.scheduled_rides:
                    ride = ScheduledRide(
                        id=ride_id,
                        appointment_time=datetime.fromisoformat(event["start_time"]),
                        origin=origin,
                        destination=destination,
                        calendar_event_id=event.get("id"),
                        buffer_minutes=self.default_buffer_minutes
                    )
                    
                    with self.lock:
                        self.scheduled_rides[ride_id] = ride
                    
                    self.logger.info(f"Scheduled ride for calendar event: {event.get('title', 'Untitled')}")
                    
            except Exception as e:
                self.logger.error(f"Error processing calendar event: {e}")
    
    def _should_schedule_ride(self, event: Dict) -> bool:
        """Determine if a calendar event should trigger a ride"""
        title = event.get("title", "").lower()
        description = event.get("description", "").lower()
        location = event.get("location", "").lower()
        
        # Keywords that suggest transportation is needed
        transport_keywords = [
            "meeting", "appointment", "interview", "conference",
            "restaurant", "dinner", "lunch", "coffee", "hotel",
            "airport", "flight", "train", "station"
        ]
        
        # Keywords that suggest no transportation needed
        skip_keywords = [
            "zoom", "video call", "phone call", "online",
            "webinar", "virtual", "home", "remote"
        ]
        
        # Check for skip keywords first
        for keyword in skip_keywords:
            if keyword in title or keyword in description:
                return False
        
        # Check for transport keywords
        for keyword in transport_keywords:
            if keyword in title or keyword in description or keyword in location:
                return True
        
        # If location is specified and not at home, probably needs transport
        if location and "home" not in location:
            return True
        
        return False
    
    def _extract_locations(self, event: Dict) -> Tuple[Optional[Tuple[float, float]], Optional[Tuple[float, float]]]:
        """Extract origin and destination from calendar event"""
        # This would geocode addresses from calendar events
        # For now, return mock coordinates
        
        location_str = event.get("location", "")
        if not location_str:
            return None, None
        
        # Mock geocoding - in production, this would use a geocoding API
        destination = self._mock_geocode(location_str)
        
        # Use home as origin
        home_location = tuple(self.config.get("home_location", [37.7749, -122.4194]))
        
        return home_location, destination
    
    def _mock_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Mock geocoding function"""
        # Common locations for testing
        locations = {
            "office": (37.7849, -122.4094),
            "downtown": (37.7749, -122.4194),
            "airport": (37.6213, -122.3790),
            "station": (37.7955, -122.3937),
            "restaurant": (37.7649, -122.4194),
            "hotel": (37.7849, -122.4294)
        }
        
        address_lower = address.lower()
        for keyword, coords in locations.items():
            if keyword in address_lower:
                return coords
        
        # Default location if no match
        return (37.7749, -122.4194)
    
    def _cleanup_old_rides(self):
        """Clean up old scheduled rides"""
        now = datetime.now()
        cutoff_time = now - timedelta(hours=24)
        
        old_rides = [
            ride_id for ride_id, ride in self.scheduled_rides.items()
            if ride.appointment_time < cutoff_time
        ]
        
        for ride_id in old_rides:
            del self.scheduled_rides[ride_id]
    
    def _load_scheduled_rides(self):
        """Load scheduled rides from file"""
        try:
            rides_file = "/home/adminx/Marina/autouber/scheduled_rides.json"
            with open(rides_file, 'r') as f:
                data = json.load(f)
            
            for ride_data in data.get("rides", []):
                # Convert datetime strings back to datetime objects
                ride_data["appointment_time"] = datetime.fromisoformat(ride_data["appointment_time"])
                ride_data["created_at"] = datetime.fromisoformat(ride_data["created_at"])
                
                ride = ScheduledRide(**ride_data)
                self.scheduled_rides[ride.id] = ride
                
            self.logger.info(f"Loaded {len(self.scheduled_rides)} scheduled rides")
            
        except FileNotFoundError:
            self.logger.info("No existing scheduled rides file found")
        except Exception as e:
            self.logger.error(f"Error loading scheduled rides: {e}")
    
    def _save_scheduled_rides(self):
        """Save scheduled rides to file"""
        try:
            rides_file = "/home/adminx/Marina/autouber/scheduled_rides.json"
            
            # Convert to serializable format
            rides_data = []
            for ride in self.scheduled_rides.values():
                ride_dict = asdict(ride)
                ride_dict["appointment_time"] = ride.appointment_time.isoformat()
                ride_dict["created_at"] = ride.created_at.isoformat()
                rides_data.append(ride_dict)
            
            data = {
                "last_saved": datetime.now().isoformat(),
                "rides": rides_data
            }
            
            with open(rides_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info(f"Saved {len(rides_data)} scheduled rides")
            
        except Exception as e:
            self.logger.error(f"Error saving scheduled rides: {e}")
    
    # Public API methods
    
    def schedule_ride(self, appointment_time: datetime, origin: Tuple[float, float],
                     destination: Tuple[float, float], **kwargs) -> str:
        """Schedule a ride for a specific appointment"""
        ride_id = f"manual_{int(time.time())}"
        
        ride = ScheduledRide(
            id=ride_id,
            appointment_time=appointment_time,
            origin=origin,
            destination=destination,
            **kwargs
        )
        
        with self.lock:
            self.scheduled_rides[ride_id] = ride
        
        self.logger.info(f"Scheduled ride {ride_id} for {appointment_time}")
        return ride_id
    
    def cancel_scheduled_ride(self, ride_id: str) -> bool:
        """Cancel a scheduled ride"""
        with self.lock:
            if ride_id in self.scheduled_rides:
                del self.scheduled_rides[ride_id]
                self.logger.info(f"Cancelled scheduled ride {ride_id}")
                return True
            return False
    
    def get_scheduled_rides(self) -> List[ScheduledRide]:
        """Get all scheduled rides"""
        with self.lock:
            return list(self.scheduled_rides.values())
    
    def get_ready_requests(self) -> List[Dict]:
        """Get requests ready to be processed by the daemon"""
        with self.lock:
            ready = self.ready_requests.copy()
            self.ready_requests.clear()
            return ready
    
    def update_calendar_integration(self, enabled: bool):
        """Enable or disable calendar integration"""
        self.calendar_integration = enabled
        self.logger.info(f"Calendar integration {'enabled' if enabled else 'disabled'}")
    
    def force_calendar_sync(self):
        """Force immediate calendar synchronization"""
        if self.calendar_integration:
            self._sync_calendars()
            self.logger.info("Forced calendar sync completed")

if __name__ == "__main__":
    # Test the scheduler
    import os
    
    config = {
        "calendar_integration": True,
        "default_buffer_minutes": 5,
        "early_arrival_minutes": 2,
        "home_location": [37.7749, -122.4194]
    }
    
    scheduler = UberScheduler(config)
    scheduler.start()
    
    # Schedule a test ride
    test_time = datetime.now() + timedelta(minutes=30)
    ride_id = scheduler.schedule_ride(
        appointment_time=test_time,
        origin=(37.7749, -122.4194),
        destination=(37.7849, -122.4094),
        auto_confirm=True
    )
    
    print(f"Scheduled test ride: {ride_id}")
    
    try:
        # Monitor for 60 seconds
        for i in range(60):
            ready = scheduler.get_ready_requests()
            if ready:
                print(f"Ready requests: {ready}")
            
            scheduled = scheduler.get_scheduled_rides()
            print(f"Scheduled rides: {len(scheduled)}")
            
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
