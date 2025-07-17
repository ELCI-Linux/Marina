"""
CPU Thermal Sensor
Monitors CPU temperature and thermal state
"""

import psutil
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CPUThermalReading:
    """CPU thermal reading data structure"""
    timestamp: float
    temperature: float
    core_id: Optional[int] = None
    label: Optional[str] = None
    critical_temp: Optional[float] = None
    high_temp: Optional[float] = None


class CPUThermalSensor:
    """CPU thermal sensor for monitoring CPU temperature"""
    
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.readings_history: List[CPUThermalReading] = []
        self.max_history_size = 1000
        
    def get_cpu_temperatures(self) -> List[CPUThermalReading]:
        """Get current CPU temperatures"""
        readings = []
        timestamp = time.time()
        
        try:
            # Try psutil first
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                
                if 'coretemp' in temps:
                    for temp in temps['coretemp']:
                        reading = CPUThermalReading(
                            timestamp=timestamp,
                            temperature=temp.current,
                            label=temp.label,
                            critical_temp=temp.critical,
                            high_temp=temp.high
                        )
                        readings.append(reading)
                        
                elif 'cpu_thermal' in temps:
                    for temp in temps['cpu_thermal']:
                        reading = CPUThermalReading(
                            timestamp=timestamp,
                            temperature=temp.current,
                            label=temp.label,
                            critical_temp=temp.critical,
                            high_temp=temp.high
                        )
                        readings.append(reading)
                        
            # Fallback to manual thermal zone reading
            if not readings:
                readings = self._read_thermal_zones()
                
        except Exception as e:
            print(f"Error reading CPU temperatures: {e}")
            
        return readings
    
    def _read_thermal_zones(self) -> List[CPUThermalReading]:
        """Read thermal zones directly from /sys/class/thermal/"""
        readings = []
        timestamp = time.time()
        thermal_path = Path("/sys/class/thermal/")
        
        if not thermal_path.exists():
            return readings
            
        for zone_dir in thermal_path.glob("thermal_zone*"):
            try:
                type_file = zone_dir / "type"
                temp_file = zone_dir / "temp"
                
                if not (type_file.exists() and temp_file.exists()):
                    continue
                    
                zone_type = type_file.read_text().strip()
                temp_millicelsius = int(temp_file.read_text().strip())
                temp_celsius = temp_millicelsius / 1000.0
                
                # Look for CPU-related thermal zones
                if any(cpu_indicator in zone_type.lower() for cpu_indicator in 
                       ['cpu', 'core', 'package', 'x86_pkg_temp']):
                    
                    reading = CPUThermalReading(
                        timestamp=timestamp,
                        temperature=temp_celsius,
                        label=zone_type
                    )
                    readings.append(reading)
                    
            except Exception as e:
                continue
                
        return readings
    
    def get_current_reading(self) -> Optional[CPUThermalReading]:
        """Get the most recent CPU temperature reading"""
        readings = self.get_cpu_temperatures()
        if readings:
            # Return the highest temperature reading
            return max(readings, key=lambda r: r.temperature)
        return None
    
    def get_thermal_state(self) -> Dict:
        """Get current thermal state assessment"""
        readings = self.get_cpu_temperatures()
        
        if not readings:
            return {
                'status': 'unknown',
                'temperature': None,
                'state': 'no_data'
            }
            
        max_temp = max(readings, key=lambda r: r.temperature)
        avg_temp = sum(r.temperature for r in readings) / len(readings)
        
        # Determine thermal state
        if max_temp.temperature > 85:
            state = 'critical'
        elif max_temp.temperature > 75:
            state = 'hot'
        elif max_temp.temperature > 65:
            state = 'warm'
        elif max_temp.temperature > 50:
            state = 'normal'
        else:
            state = 'cool'
            
        return {
            'status': 'active',
            'max_temperature': max_temp.temperature,
            'avg_temperature': avg_temp,
            'num_sensors': len(readings),
            'state': state,
            'readings': readings
        }
    
    def start_monitoring(self):
        """Start continuous monitoring (placeholder for future implementation)"""
        pass
    
    def stop_monitoring(self):
        """Stop continuous monitoring (placeholder for future implementation)"""
        pass
    
    def add_reading_to_history(self, reading: CPUThermalReading):
        """Add a reading to the history"""
        self.readings_history.append(reading)
        
        # Maintain history size
        if len(self.readings_history) > self.max_history_size:
            self.readings_history.pop(0)
    
    def get_temperature_trend(self, window_size: int = 10) -> str:
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
        
        if increasing > decreasing * 1.5:
            return 'increasing'
        elif decreasing > increasing * 1.5:
            return 'decreasing'
        else:
            return 'stable'
