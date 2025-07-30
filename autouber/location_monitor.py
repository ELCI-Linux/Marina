#!/usr/bin/env python3
"""
Location Monitor
Tracks user location and manages geofences for Auto-Uber triggers
"""

import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
import requests

@dataclass
class Geofence:
    id: str
    center: Tuple[float, float]  # (lat, lon)
    radius_m: float
    callback: Callable
    active: bool = True
    triggered: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class LocationMonitor:
    """
    Monitors user location and manages geofences
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.update_interval = config.get("update_interval_seconds", 30)
        self.accuracy_threshold = config.get("accuracy_threshold_meters", 50)
        self.geofence_check_interval = config.get("geofence_check_interval", 10)
        
        # Location tracking
        self.current_location: Optional[Tuple[float, float]] = None
        self.location_history: List[Dict] = []
        self.last_update = None
        
        # Geofencing
        self.geofences: Dict[str, Geofence] = {}
        self.location_sources = []
        
        # Threading
        self.running = False
        self.location_thread = None
        self.geofence_thread = None
        self.lock = threading.Lock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize location sources
        self._init_location_sources()
    
    def _init_location_sources(self):
        """Initialize available location sources"""
        self.location_sources = [
            self._get_gps_location,
            self._get_wifi_location,
            self._get_ip_location,
            self._get_mock_location  # For testing
        ]
    
    def start(self):
        """Start location monitoring"""
        if self.running:
            self.logger.warning("Location monitor already running")
            return
            
        self.running = True
        
        # Start location tracking thread
        self.location_thread = threading.Thread(target=self._location_loop, daemon=True)
        self.location_thread.start()
        
        # Start geofence checking thread
        self.geofence_thread = threading.Thread(target=self._geofence_loop, daemon=True)
        self.geofence_thread.start()
        
        self.logger.info("Location monitor started")
    
    def stop(self):
        """Stop location monitoring"""
        self.running = False
        
        if self.location_thread:
            self.location_thread.join(timeout=5)
        if self.geofence_thread:
            self.geofence_thread.join(timeout=5)
            
        self.logger.info("Location monitor stopped")
    
    def _location_loop(self):
        """Main location tracking loop"""
        while self.running:
            try:
                location = self._get_best_location()
                if location:
                    with self.lock:
                        self.current_location = location
                        self.last_update = datetime.now()
                        
                        # Add to history
                        self.location_history.append({
                            "location": location,
                            "timestamp": self.last_update.isoformat(),
                            "accuracy": self.accuracy_threshold
                        })
                        
                        # Keep only last 100 locations
                        if len(self.location_history) > 100:
                            self.location_history = self.location_history[-100:]
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in location loop: {e}")
                time.sleep(30)  # Wait longer on error
    
    def _geofence_loop(self):
        """Geofence checking loop"""
        while self.running:
            try:
                with self.lock:
                    current_loc = self.current_location
                    
                if current_loc:
                    self._check_geofences(current_loc)
                
                time.sleep(self.geofence_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in geofence loop: {e}")
                time.sleep(30)
    
    def _get_best_location(self) -> Optional[Tuple[float, float]]:
        """Get the best available location from all sources"""
        for source in self.location_sources:
            try:
                location = source()
                if location:
                    self.logger.debug(f"Got location from {source.__name__}: {location}")
                    return location
            except Exception as e:
                self.logger.debug(f"Location source {source.__name__} failed: {e}")
        
        return None
    
    def _get_gps_location(self) -> Optional[Tuple[float, float]]:
        """Get location from GPS (requires hardware/system integration)"""
        # This would integrate with system GPS APIs
        # For now, return None to try other sources
        return None
    
    def _get_wifi_location(self) -> Optional[Tuple[float, float]]:
        """Get location from WiFi positioning"""
        try:
            # Get nearby WiFi networks
            import subprocess
            result = subprocess.run(['iwlist', 'scan'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Parse WiFi networks and use location service
                # This is a simplified implementation
                # In production, this would use Google/Mozilla location APIs
                networks = self._parse_wifi_networks(result.stdout)
                if networks:
                    return self._lookup_wifi_location(networks)
                    
        except Exception as e:
            self.logger.debug(f"WiFi location failed: {e}")
            
        return None
    
    def _parse_wifi_networks(self, scan_output: str) -> List[Dict]:
        """Parse WiFi scan output"""
        networks = []
        lines = scan_output.split('\n')
        current_network = {}
        
        for line in lines:
            line = line.strip()
            if 'Address:' in line:
                if current_network:
                    networks.append(current_network)
                current_network = {'mac': line.split('Address: ')[1]}
            elif 'ESSID:' in line:
                current_network['ssid'] = line.split('ESSID:')[1].strip('"')
            elif 'Signal level=' in line:
                # Extract signal strength
                signal = line.split('Signal level=')[1].split()[0]
                current_network['signal'] = signal
        
        if current_network:
            networks.append(current_network)
            
        return networks[:5]  # Return top 5 networks
    
    def _lookup_wifi_location(self, networks: List[Dict]) -> Optional[Tuple[float, float]]:
        """Look up location based on WiFi networks"""
        # This would use a WiFi positioning API
        # For testing, return a mock location if networks found
        if networks:
            # Mock location based on presence of networks
            return (37.7749, -122.4194)  # San Francisco
        return None
    
    def _get_ip_location(self) -> Optional[Tuple[float, float]]:
        """Get approximate location from IP address"""
        try:
            # Use a free IP geolocation service
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    lat = data.get('lat')
                    lon = data.get('lon')
                    if lat is not None and lon is not None:
                        return (float(lat), float(lon))
                        
        except Exception as e:
            self.logger.debug(f"IP location failed: {e}")
            
        return None
    
    def _get_mock_location(self) -> Optional[Tuple[float, float]]:
        """Mock location for testing"""
        # Return a mock location that changes slightly over time
        base_lat = 37.7749  # San Francisco
        base_lon = -122.4194
        
        # Add small random variation
        import random
        offset = 0.001  # About 100 meters
        lat = base_lat + random.uniform(-offset, offset)
        lon = base_lon + random.uniform(-offset, offset)
        
        return (lat, lon)
    
    def _check_geofences(self, location: Tuple[float, float]):
        """Check if current location triggers any geofences"""
        for geofence_id, geofence in list(self.geofences.items()):
            if not geofence.active or geofence.triggered:
                continue
                
            distance = self._calculate_distance(location, geofence.center)
            
            if distance <= geofence.radius_m:
                self.logger.info(f"Geofence {geofence_id} triggered at distance {distance:.1f}m")
                
                # Mark as triggered
                geofence.triggered = True
                
                # Call the callback
                try:
                    geofence.callback(geofence_id, location, distance)
                except Exception as e:
                    self.logger.error(f"Error in geofence callback {geofence_id}: {e}")
    
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
    
    # Public API methods
    
    def get_current_location(self) -> Optional[Tuple[float, float]]:
        """Get current location"""
        with self.lock:
            return self.current_location
    
    def get_location_history(self) -> List[Dict]:
        """Get location history"""
        with self.lock:
            return self.location_history.copy()
    
    def is_location_fresh(self, max_age_seconds: int = 300) -> bool:
        """Check if current location is fresh"""
        with self.lock:
            if not self.last_update:
                return False
            age = (datetime.now() - self.last_update).total_seconds()
            return age <= max_age_seconds
    
    def add_geofence(self, geofence_id: str, center: Tuple[float, float], 
                    radius_m: float, callback: Callable) -> bool:
        """Add a geofence"""
        try:
            geofence = Geofence(
                id=geofence_id,
                center=center,
                radius_m=radius_m,
                callback=callback
            )
            
            with self.lock:
                self.geofences[geofence_id] = geofence
                
            self.logger.info(f"Added geofence {geofence_id} at {center} with radius {radius_m}m")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add geofence {geofence_id}: {e}")
            return False
    
    def remove_geofence(self, geofence_id: str) -> bool:
        """Remove a geofence"""
        with self.lock:
            if geofence_id in self.geofences:
                del self.geofences[geofence_id]
                self.logger.info(f"Removed geofence {geofence_id}")
                return True
            return False
    
    def get_geofences(self) -> Dict[str, Geofence]:
        """Get all geofences"""
        with self.lock:
            return self.geofences.copy()
    
    def set_mock_location(self, location: Tuple[float, float]):
        """Set a mock location for testing"""
        with self.lock:
            self.current_location = location
            self.last_update = datetime.now()
            
            # Add to history
            self.location_history.append({
                "location": location,
                "timestamp": self.last_update.isoformat(),
                "accuracy": 10,  # High accuracy for mock
                "source": "mock"
            })
            
        self.logger.info(f"Set mock location: {location}")
    
    def monitor_approach(self, target: Tuple[float, float], radius_m: float, 
                        callback: Callable) -> str:
        """Monitor approach to a target location"""
        geofence_id = f"approach_{int(time.time())}"
        self.add_geofence(geofence_id, target, radius_m, callback)
        return geofence_id
    
    def estimate_arrival_time(self, destination: Tuple[float, float], 
                            speed_mps: float = 1.4) -> Optional[timedelta]:
        """Estimate time to reach destination"""
        current = self.get_current_location()
        if not current:
            return None
            
        distance = self._calculate_distance(current, destination)
        time_seconds = distance / speed_mps
        return timedelta(seconds=time_seconds)

if __name__ == "__main__":
    # Test the location monitor
    config = {
        "update_interval_seconds": 5,
        "accuracy_threshold_meters": 50,
        "geofence_check_interval": 2
    }
    
    def test_callback(geofence_id, location, distance):
        print(f"Geofence {geofence_id} triggered at {location} (distance: {distance:.1f}m)")
    
    monitor = LocationMonitor(config)
    monitor.start()
    
    # Add a test geofence
    test_location = (37.7749, -122.4194)
    monitor.add_geofence("test", test_location, 100, test_callback)
    
    # Set mock location near the geofence
    monitor.set_mock_location((37.7750, -122.4195))
    
    try:
        # Monitor for 30 seconds
        for i in range(30):
            location = monitor.get_current_location()
            print(f"Current location: {location}")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop()
