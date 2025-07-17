"""
Environmental Thermal State Manager
Manages and assesses the environmental thermal state
"""

from typing import Dict
from .environment_thermal_sensor import EnvironmentThermalSensor


class ThermalStateManager:
    """Manages and assesses the environmental thermal state"""
    
    def __init__(self):
        self.environment_sensor = EnvironmentThermalSensor()
        
    def get_environment_thermal_state(self) -> Dict:
        """Get environmental thermal state"""
        return self.environment_sensor.get_thermal_state()
    
    def get_comfort_assessment(self) -> Dict:
        """Assess environmental comfort level"""
        env_state = self.get_environment_thermal_state()
        
        if env_state['status'] == 'no_data':
            return {
                'comfort_level': 'unknown',
                'assessment': 'No environmental data available'
            }
        
        temp = env_state['temperature']
        humidity = env_state.get('humidity')
        feels_like = env_state.get('feels_like')
        
        # Assess comfort based on temperature
        if temp < 0:
            comfort_level = 'very_uncomfortable_cold'
            assessment = 'Extremely cold conditions'
        elif temp < 10:
            comfort_level = 'uncomfortable_cold'
            assessment = 'Cold conditions'
        elif temp < 18:
            comfort_level = 'slightly_cool'
            assessment = 'Cool but manageable'
        elif temp <= 24:
            comfort_level = 'comfortable'
            assessment = 'Comfortable temperature range'
        elif temp <= 28:
            comfort_level = 'slightly_warm'
            assessment = 'Warm but comfortable'
        elif temp <= 32:
            comfort_level = 'uncomfortable_warm'
            assessment = 'Warm conditions'
        else:
            comfort_level = 'very_uncomfortable_hot'
            assessment = 'Very hot conditions'
        
        # Adjust for humidity if available
        if humidity is not None:
            if humidity > 70 and temp > 25:
                comfort_level = f'{comfort_level}_humid'
                assessment += ' with high humidity'
            elif humidity < 30:
                comfort_level = f'{comfort_level}_dry'
                assessment += ' with low humidity'
        
        # Use feels_like if available
        if feels_like is not None:
            temp_diff = feels_like - temp
            if abs(temp_diff) > 3:
                assessment += f' (feels like {feels_like:.1f}°C)'
        
        return {
            'comfort_level': comfort_level,
            'assessment': assessment,
            'temperature': temp,
            'humidity': humidity,
            'feels_like': feels_like
        }
    
    def monitor_environment_thermal_state(self):
        """Continuously monitor environmental thermal state (placeholder)"""
        pass
