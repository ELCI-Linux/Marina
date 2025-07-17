#!/usr/bin/env python3
"""
Weather Service for Marina
Fetches weather data from OpenWeatherMap API
"""

import requests
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from .geolocation_service import GeolocationService

class WeatherService:
    def __init__(self):
        # Try to get API key from environment variable or file
        self.api_key = os.environ.get('OPENWEATHER_API_KEY')
        if not self.api_key:
            self.api_key = self._load_api_key_from_file()
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # Initialize geolocation service
        self.geolocation_service = GeolocationService()
        
        # Current location (will be updated from geolocation)
        self.current_location = None
        self.current_lat = None
        self.current_lon = None
        
        # Default location (fallback)
        self.default_lat = 40.7128  # New York
        self.default_lon = -74.0060
        
        # Initialize location
        self._update_location()
        
    def _load_api_key_from_file(self) -> Optional[str]:
        """Load API key from file"""
        try:
            # Try to find the API key file in common locations
            possible_paths = [
                '.keys/openweather_key',
                '../.keys/openweather_key',
                '../../.keys/openweather_key'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        return f.read().strip()
        except Exception as e:
            print(f"Error loading API key from file: {e}")
        
        return None
        
    def _update_location(self) -> None:
        """Update current location using geolocation service"""
        try:
            self.current_location = self.geolocation_service.get_location()
            if self.current_location:
                self.current_lat = self.current_location['lat']
                self.current_lon = self.current_location['lon']
                print(f"Location updated: {self.get_location_string()}")
        except Exception as e:
            print(f"Error updating location: {e}")
            
    def get_location_string(self) -> str:
        """Get formatted location string"""
        if self.current_location:
            return self.geolocation_service.get_location_string()
        return "Unknown Location"
        
    def get_current_coordinates(self) -> tuple:
        """Get current coordinates (lat, lon)"""
        if self.current_lat and self.current_lon:
            return (self.current_lat, self.current_lon)
        return (self.default_lat, self.default_lon)
        
    def refresh_location(self) -> None:
        """Refresh location data"""
        self.geolocation_service.refresh_location()
        self._update_location()
        
    def get_current_weather(self, lat: float = None, lon: float = None) -> Optional[Dict[str, Any]]:
        """Get current weather for given coordinates"""
        if not self.api_key:
            return self._get_mock_current_weather()
            
        # Use current location if available, otherwise use provided coordinates or default
        if lat is None and lon is None:
            lat, lon = self.get_current_coordinates()
        else:
            lat = lat or self.default_lat
            lon = lon or self.default_lon
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return self._get_mock_current_weather()
    
    def get_forecast(self, lat: float = None, lon: float = None) -> Optional[Dict[str, Any]]:
        """Get 5-day forecast for given coordinates"""
        if not self.api_key:
            return self._get_mock_forecast()
            
        # Use current location if available, otherwise use provided coordinates or default
        if lat is None and lon is None:
            lat, lon = self.get_current_coordinates()
        else:
            lat = lat or self.default_lat
            lon = lon or self.default_lon
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error fetching forecast: {e}")
            return self._get_mock_forecast()
    
    def _get_mock_current_weather(self) -> Dict[str, Any]:
        """Return mock current weather data"""
        return {
            'name': 'New York',
            'main': {
                'temp': 22.5,
                'feels_like': 24.2,
                'temp_min': 20.1,
                'temp_max': 25.3,
                'pressure': 1013,
                'humidity': 65
            },
            'weather': [{
                'main': 'Clear',
                'description': 'clear sky',
                'icon': '01d'
            }],
            'wind': {
                'speed': 3.6,
                'deg': 200
            },
            'visibility': 10000,
            'dt': int(datetime.now().timestamp()),
            'sys': {
                'sunrise': int(datetime.now().replace(hour=6, minute=30).timestamp()),
                'sunset': int(datetime.now().replace(hour=19, minute=45).timestamp())
            },
            'coord': {
                'lat': self.default_lat,
                'lon': self.default_lon
            }
        }
    
    def _get_mock_forecast(self) -> Dict[str, Any]:
        """Return mock forecast data"""
        import random
        
        forecast_list = []
        base_temp = 22.5
        
        for i in range(40):  # 5 days * 8 forecasts per day (3-hour intervals)
            temp_variation = random.uniform(-5, 5)
            forecast_list.append({
                'dt': int((datetime.now().timestamp() + i * 3 * 3600)),
                'main': {
                    'temp': base_temp + temp_variation,
                    'feels_like': base_temp + temp_variation + 1,
                    'temp_min': base_temp + temp_variation - 2,
                    'temp_max': base_temp + temp_variation + 2,
                    'pressure': 1013 + random.randint(-20, 20),
                    'humidity': 65 + random.randint(-15, 15)
                },
                'weather': [{
                    'main': random.choice(['Clear', 'Clouds', 'Rain', 'Snow']),
                    'description': random.choice(['clear sky', 'few clouds', 'light rain', 'snow']),
                    'icon': random.choice(['01d', '02d', '03d', '04d', '09d', '10d', '11d', '13d'])
                }],
                'wind': {
                    'speed': random.uniform(1, 10),
                    'deg': random.randint(0, 360)
                },
                'visibility': random.randint(5000, 10000),
                'dt_txt': datetime.fromtimestamp(datetime.now().timestamp() + i * 3 * 3600).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return {
            'cod': '200',
            'message': 0,
            'cnt': 40,
            'list': forecast_list,
            'city': {
                'id': 5128581,
                'name': 'New York',
                'coord': {
                    'lat': self.default_lat,
                    'lon': self.default_lon
                },
                'country': 'US',
                'population': 8175133,
                'timezone': -18000,
                'sunrise': int(datetime.now().replace(hour=6, minute=30).timestamp()),
                'sunset': int(datetime.now().replace(hour=19, minute=45).timestamp())
            }
        }
    
    def get_weather_icon_url(self, icon_code: str) -> str:
        """Get URL for weather icon"""
        return f"https://openweathermap.org/img/w/{icon_code}.png"
    
    def format_temperature(self, temp: float) -> str:
        """Format temperature with degree symbol"""
        return f"{temp:.1f}°C"
    
    def format_wind_speed(self, speed: float) -> str:
        """Format wind speed"""
        return f"{speed:.1f} m/s"
    
    def format_pressure(self, pressure: int) -> str:
        """Format pressure"""
        return f"{pressure} hPa"
    
    def format_humidity(self, humidity: int) -> str:
        """Format humidity"""
        return f"{humidity}%"
