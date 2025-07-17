"""
Environment Thermal Sensor
Monitors environmental temperature from weather data and external sensors
"""

import requests
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import subprocess
from pathlib import Path


@dataclass
class EnvironmentThermalReading:
    """Environmental thermal reading data structure"""
    timestamp: float
    temperature: float
    humidity: Optional[float] = None
    source: str = "unknown"
    location: Optional[str] = None
    feels_like: Optional[float] = None
    heat_index: Optional[float] = None


class EnvironmentThermalSensor:
    """Environmental thermal sensor for monitoring ambient temperature"""
    
    def __init__(self, update_interval: float = 300.0):  # 5 minutes default
        self.update_interval = update_interval
        self.readings_history: List[EnvironmentThermalReading] = []
        self.max_history_size = 1000
        self.weather_api_key = None
        self.location = None
        self.external_sensors = []
        
    def set_weather_api_key(self, api_key: str):
        """Set weather API key for external weather data"""
        self.weather_api_key = api_key
        
    def set_location(self, location: str):
        """Set location for weather data"""
        self.location = location
        
    def add_external_sensor(self, sensor_config: Dict):
        """Add external sensor configuration"""
        self.external_sensors.append(sensor_config)
        
    def get_weather_temperature(self) -> Optional[EnvironmentThermalReading]:
        """Get temperature from weather API"""
        if not self.weather_api_key or not self.location:
            return None
            
        try:
            # Using OpenWeatherMap API as an example
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': self.location,
                'appid': self.weather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                temperature = data['main']['temp']
                humidity = data['main']['humidity']
                feels_like = data['main']['feels_like']
                
                reading = EnvironmentThermalReading(
                    timestamp=time.time(),
                    temperature=temperature,
                    humidity=humidity,
                    source="weather_api",
                    location=self.location,
                    feels_like=feels_like
                )
                
                return reading
                
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            
        return None
    
    def get_local_weather(self) -> Optional[EnvironmentThermalReading]:
        """Get local weather using command line tools"""
        try:
            # Try using wttr.in service
            result = subprocess.run(['curl', '-s', 'wttr.in/?format=j1'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                current = data['current_condition'][0]
                
                temp_c = float(current['temp_C'])
                humidity = float(current['humidity'])
                feels_like = float(current['FeelsLikeC'])
                
                reading = EnvironmentThermalReading(
                    timestamp=time.time(),
                    temperature=temp_c,
                    humidity=humidity,
                    source="wttr.in",
                    feels_like=feels_like
                )
                
                return reading
                
        except Exception as e:
            print(f"Error fetching local weather: {e}")
            
        return None
    
    def get_sensor_temperatures(self) -> List[EnvironmentThermalReading]:
        """Get temperatures from external sensors"""
        readings = []
        
        for sensor_config in self.external_sensors:
            try:
                sensor_type = sensor_config.get('type', 'unknown')
                
                if sensor_type == 'dht22':
                    reading = self._read_dht22_sensor(sensor_config)
                elif sensor_type == 'ds18b20':
                    reading = self._read_ds18b20_sensor(sensor_config)
                elif sensor_type == 'file':
                    reading = self._read_file_sensor(sensor_config)
                elif sensor_type == 'command':
                    reading = self._read_command_sensor(sensor_config)
                else:
                    continue
                    
                if reading:
                    readings.append(reading)
                    
            except Exception as e:
                print(f"Error reading sensor {sensor_config}: {e}")
                continue
                
        return readings
    
    def _read_dht22_sensor(self, config: Dict) -> Optional[EnvironmentThermalReading]:
        """Read DHT22 temperature/humidity sensor"""
        # This would require appropriate GPIO libraries
        # Placeholder implementation
        return None
    
    def _read_ds18b20_sensor(self, config: Dict) -> Optional[EnvironmentThermalReading]:
        """Read DS18B20 temperature sensor"""
        try:
            sensor_id = config.get('sensor_id')
            if not sensor_id:
                return None
                
            sensor_path = Path(f"/sys/bus/w1/devices/{sensor_id}/w1_slave")
            
            if sensor_path.exists():
                content = sensor_path.read_text()
                
                if 'YES' in content:
                    temp_line = content.split('t=')[-1]
                    temp_millicelsius = int(temp_line.strip())
                    temp_celsius = temp_millicelsius / 1000.0
                    
                    reading = EnvironmentThermalReading(
                        timestamp=time.time(),
                        temperature=temp_celsius,
                        source=f"ds18b20_{sensor_id}",
                        location=config.get('location', 'unknown')
                    )
                    
                    return reading
                    
        except Exception as e:
            print(f"Error reading DS18B20 sensor: {e}")
            
        return None
    
    def _read_file_sensor(self, config: Dict) -> Optional[EnvironmentThermalReading]:
        """Read temperature from a file"""
        try:
            file_path = Path(config.get('path', ''))
            
            if file_path.exists():
                content = file_path.read_text().strip()
                
                # Try to parse temperature
                try:
                    temperature = float(content)
                except ValueError:
                    # Try to extract temperature from formatted text
                    import re
                    temp_match = re.search(r'(-?\d+\.?\d*)', content)
                    if temp_match:
                        temperature = float(temp_match.group(1))
                    else:
                        return None
                
                reading = EnvironmentThermalReading(
                    timestamp=time.time(),
                    temperature=temperature,
                    source=f"file_{file_path.name}",
                    location=config.get('location', 'unknown')
                )
                
                return reading
                
        except Exception as e:
            print(f"Error reading file sensor: {e}")
            
        return None
    
    def _read_command_sensor(self, config: Dict) -> Optional[EnvironmentThermalReading]:
        """Read temperature from command output"""
        try:
            command = config.get('command', [])
            if not command:
                return None
                
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                
                # Try to parse temperature
                try:
                    temperature = float(output)
                except ValueError:
                    # Try to extract temperature from formatted text
                    import re
                    temp_match = re.search(r'(-?\d+\.?\d*)', output)
                    if temp_match:
                        temperature = float(temp_match.group(1))
                    else:
                        return None
                
                reading = EnvironmentThermalReading(
                    timestamp=time.time(),
                    temperature=temperature,
                    source=f"command_{' '.join(command)}",
                    location=config.get('location', 'unknown')
                )
                
                return reading
                
        except Exception as e:
            print(f"Error reading command sensor: {e}")
            
        return None
    
    def get_environment_temperatures(self) -> List[EnvironmentThermalReading]:
        """Get all available environmental temperature readings"""
        readings = []
        
        # Try weather API first
        weather_reading = self.get_weather_temperature()
        if weather_reading:
            readings.append(weather_reading)
        else:
            # Fallback to local weather
            local_weather = self.get_local_weather()
            if local_weather:
                readings.append(local_weather)
        
        # Get external sensor readings
        sensor_readings = self.get_sensor_temperatures()
        readings.extend(sensor_readings)
        
        return readings
    
    def get_current_reading(self) -> Optional[EnvironmentThermalReading]:
        """Get the most recent environmental temperature reading"""
        readings = self.get_environment_temperatures()
        if readings:
            # Return the most recent reading
            return max(readings, key=lambda r: r.timestamp)
        return None
    
    def get_thermal_state(self) -> Dict:
        """Get current environmental thermal state assessment"""
        readings = self.get_environment_temperatures()
        
        if not readings:
            return {
                'status': 'no_data',
                'temperature': None,
                'state': 'unknown'
            }
            
        # Use the most recent reading
        current_reading = max(readings, key=lambda r: r.timestamp)
        temp = current_reading.temperature
        
        # Determine environmental thermal state
        if temp > 35:
            state = 'very_hot'
        elif temp > 30:
            state = 'hot'
        elif temp > 25:
            state = 'warm'
        elif temp > 15:
            state = 'comfortable'
        elif temp > 5:
            state = 'cool'
        elif temp > -5:
            state = 'cold'
        else:
            state = 'very_cold'
            
        return {
            'status': 'active',
            'temperature': temp,
            'state': state,
            'humidity': current_reading.humidity,
            'feels_like': current_reading.feels_like,
            'source': current_reading.source,
            'location': current_reading.location,
            'num_sensors': len(readings),
            'readings': readings
        }
    
    def add_reading_to_history(self, reading: EnvironmentThermalReading):
        """Add a reading to the history"""
        self.readings_history.append(reading)
        
        # Maintain history size
        if len(self.readings_history) > self.max_history_size:
            self.readings_history.pop(0)
    
    def get_temperature_trend(self, window_size: int = 5) -> str:
        """Get temperature trend over recent readings"""
        if len(self.readings_history) < window_size:
            return 'insufficient_data'
            
        recent_temps = [r.temperature for r in self.readings_history[-window_size:]]
        
        if len(recent_temps) < 2:
            return 'stable'
            
        # Simple trend analysis
        increasing = sum(1 for i in range(1, len(recent_temps)) 
                        if recent_temps[i] > recent_temps[i-1])
        decreasing = sum(1 for i in range(1, len(recent_temps)) 
                        if recent_temps[i] < recent_temps[i-1])
        
        if increasing > decreasing:
            return 'increasing'
        elif decreasing > increasing:
            return 'decreasing'
        else:
            return 'stable'
