"""
Thermal State Manager
Manages and assesses the system thermal state
"""

from typing import Dict

from .cpu_thermal_sensor import CPUThermalSensor
from .gpu_thermal_sensor import GPUThermalSensor


class ThermalStateManager:
    """Manages and assesses the thermal state of the system"""
    
    def __init__(self):
        self.cpu_sensor = CPUThermalSensor()
        self.gpu_sensor = GPUThermalSensor()
        
    def get_system_thermal_state(self) -> Dict:
        """Aggregate thermal state from CPU and GPU sensors"""
        cpu_state = self.cpu_sensor.get_thermal_state()
        gpu_state = self.gpu_sensor.get_thermal_state()
        
        # Combine CPU and GPU thermal data
        return {
            'cpu': cpu_state,
            'gpu': gpu_state
        }
    
    def get_overall_status(self) -> str:
        """Determine the overall thermal status"""
        system_state = self.get_system_thermal_state()
        cpu_state = system_state['cpu']['state']
        gpu_state = system_state['gpu']['state']
        
        # Determine overall system thermal status
        if 'critical' in [cpu_state, gpu_state]:
            return 'critical'
        elif 'hot' in [cpu_state, gpu_state]:
            return 'hot'
        elif 'warm' in [cpu_state, gpu_state]:
            return 'warm'
        elif 'normal' in [cpu_state, gpu_state]:
            return 'normal'
        else:
            return 'cool'
    
    def monitor_thermal_state(self):
        """Continuously monitor the thermal state (placeholder for future implementation)"""
        pass
