#!/usr/bin/env python3
"""
Geolocation Service for Marina
Provides accurate location detection using various methods
"""

import requests
import json
import os
import subprocess
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta


class GeolocationService:
    def __init__(self):
        self.cached_location = None
        self.cache_timestamp = None
        self.cache_duration = timedelta(hours=1)  # Cache location for 1 hour
        
    def get_location(self) -> Optional[Dict[str, Any]]:
        """Get current location using multiple methods"""
        # Check cache first
        if self._is_cache_valid():
            return self.cached_location
            
        # Try multiple methods in order of preference
        location = (
            self._get_location_from_ip() or
            self._get_location_from_system() or
            self._get_default_location()
        )
        
        if location:
            self._cache_location(location)
            
        return location
    
    def get_coordinates(self) -> Optional[Tuple[float, float]]:
        """Get latitude and longitude coordinates"""
        location = self.get_location()
        if location:
            return location.get('lat'), location.get('lon')
        return None
    
    def _get_location_from_ip(self) -> Optional[Dict[str, Any]]:
        """Get location using IP-based geolocation"""
        try:
            # Try multiple IP geolocation services
            services = [
                'http://ip-api.com/json/',
                'https://ipapi.co/json/',
                'https://freegeoip.app/json/'
            ]
            
            for service_url in services:
                try:
                    response = requests.get(service_url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Parse different API response formats
                        if 'lat' in data and 'lon' in data:
                            # ip-api.com format
                            return {
                                'lat': float(data['lat']),
                                'lon': float(data['lon']),
                                'city': data.get('city', 'Unknown'),
                                'region': data.get('regionName', data.get('region', 'Unknown')),
                                'country': data.get('country', 'Unknown'),
                                'timezone': data.get('timezone', 'Unknown'),
                                'source': 'ip_geolocation'
                            }
                        elif 'latitude' in data and 'longitude' in data:
                            # ipapi.co format
                            return {
                                'lat': float(data['latitude']),
                                'lon': float(data['longitude']),
                                'city': data.get('city', 'Unknown'),
                                'region': data.get('region', 'Unknown'),
                                'country': data.get('country_name', 'Unknown'),
                                'timezone': data.get('timezone', 'Unknown'),
                                'source': 'ip_geolocation'
                            }
                except Exception as e:
                    print(f"Error with geolocation service {service_url}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error getting location from IP: {e}")
            
        return None
    
    def _get_location_from_system(self) -> Optional[Dict[str, Any]]:
        """Get location using system-specific methods"""
        try:
            # Try to get location from system timezone
            timezone_info = self._get_timezone_info()
            if timezone_info:
                return timezone_info
                
        except Exception as e:
            print(f"Error getting location from system: {e}")
            
        return None
    
    def _get_timezone_info(self) -> Optional[Dict[str, Any]]:
        """Get approximate location from system timezone"""
        try:
            # Get system timezone
            result = subprocess.run(['timedatectl', 'show', '--property=Timezone'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                timezone_line = result.stdout.strip()
                if '=' in timezone_line:
                    timezone = timezone_line.split('=')[1]
                    
                    # Map common timezones to approximate coordinates
                    timezone_coords = {
                        'America/New_York': (40.7128, -74.0060, 'New York', 'New York', 'USA'),
                        'America/Los_Angeles': (34.0522, -118.2437, 'Los Angeles', 'California', 'USA'),
                        'America/Chicago': (41.8781, -87.6298, 'Chicago', 'Illinois', 'USA'),
                        'America/Denver': (39.7392, -104.9903, 'Denver', 'Colorado', 'USA'),
                        'Europe/London': (51.5074, -0.1278, 'London', 'England', 'UK'),
                        'Europe/Paris': (48.8566, 2.3522, 'Paris', 'Île-de-France', 'France'),
                        'Europe/Berlin': (52.5200, 13.4050, 'Berlin', 'Berlin', 'Germany'),
                        'Asia/Tokyo': (35.6762, 139.6503, 'Tokyo', 'Tokyo', 'Japan'),
                        'Asia/Shanghai': (31.2304, 121.4737, 'Shanghai', 'Shanghai', 'China'),
                        'Asia/Kolkata': (28.7041, 77.1025, 'New Delhi', 'Delhi', 'India'),
                        'Australia/Sydney': (-33.8688, 151.2093, 'Sydney', 'NSW', 'Australia'),
                    }
                    
                    if timezone in timezone_coords:
                        lat, lon, city, region, country = timezone_coords[timezone]
                        return {
                            'lat': lat,
                            'lon': lon,
                            'city': city,
                            'region': region,
                            'country': country,
                            'timezone': timezone,
                            'source': 'system_timezone'
                        }
                        
        except Exception as e:
            print(f"Error getting timezone info: {e}")
            
        return None
    
    def _get_default_location(self) -> Dict[str, Any]:
        """Return default location (New York) as fallback"""
        return {
            'lat': 40.7128,
            'lon': -74.0060,
            'city': 'New York',
            'region': 'New York',
            'country': 'USA',
            'timezone': 'America/New_York',
            'source': 'default'
        }
    
    def _is_cache_valid(self) -> bool:
        """Check if cached location is still valid"""
        if not self.cached_location or not self.cache_timestamp:
            return False
            
        return datetime.now() - self.cache_timestamp < self.cache_duration
    
    def _cache_location(self, location: Dict[str, Any]) -> None:
        """Cache the location data"""
        self.cached_location = location
        self.cache_timestamp = datetime.now()
    
    def refresh_location(self) -> Optional[Dict[str, Any]]:
        """Force refresh of location data"""
        self.cached_location = None
        self.cache_timestamp = None
        return self.get_location()
    
    def get_location_string(self) -> str:
        """Get a formatted location string"""
        location = self.get_location()
        if location:
            city = location.get('city', 'Unknown')
            region = location.get('region', '')
            country = location.get('country', '')
            
            parts = [city]
            if region and region != city:
                parts.append(region)
            if country and country not in parts:
                parts.append(country)
                
            return ', '.join(parts)
        
        return 'Unknown Location'
    
    def save_location_to_file(self, filepath: str = None) -> bool:
        """Save current location to a file"""
        if not filepath:
            filepath = os.path.join(os.path.expanduser('~'), 'Marina', '.cache', 'location.json')
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            location = self.get_location()
            if location:
                location['cached_at'] = datetime.now().isoformat()
                
                with open(filepath, 'w') as f:
                    json.dump(location, f, indent=2)
                    
                return True
                
        except Exception as e:
            print(f"Error saving location to file: {e}")
            
        return False
    
    def load_location_from_file(self, filepath: str = None) -> Optional[Dict[str, Any]]:
        """Load location from a file"""
        if not filepath:
            filepath = os.path.join(os.path.expanduser('~'), 'Marina', '.cache', 'location.json')
            
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    location = json.load(f)
                    
                # Check if cached location is still valid
                if 'cached_at' in location:
                    cached_time = datetime.fromisoformat(location['cached_at'])
                    if datetime.now() - cached_time < self.cache_duration:
                        return location
                        
        except Exception as e:
            print(f"Error loading location from file: {e}")
            
        return None
