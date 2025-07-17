"""
GPU Thermal Sensor
Monitors GPU temperature and thermal state
"""

import subprocess
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import re


@dataclass
class GPUThermalReading:
    """GPU thermal reading data structure"""
    timestamp: float
    temperature: float
    gpu_id: int
    gpu_name: Optional[str] = None
    utilization: Optional[float] = None
    memory_temp: Optional[float] = None
    power_draw: Optional[float] = None
    fan_speed: Optional[float] = None


class GPUThermalSensor:
    """GPU thermal sensor for monitoring GPU temperature"""
    
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.readings_history: List[GPUThermalReading] = []
        self.max_history_size = 1000
        self.nvidia_available = self._check_nvidia_smi()
        self.amd_available = self._check_amd_gpu()
        
    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available"""
        try:
            result = subprocess.run(['nvidia-smi', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_amd_gpu(self) -> bool:
        """Check if AMD GPU monitoring tools are available"""
        try:
            # Check for rocm-smi
            result = subprocess.run(['rocm-smi', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True
                
            # Check for radeontop
            result = subprocess.run(['radeontop', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_nvidia_temperatures(self) -> List[GPUThermalReading]:
        """Get NVIDIA GPU temperatures using nvidia-smi"""
        readings = []
        
        if not self.nvidia_available:
            return readings
            
        try:
            # Query nvidia-smi for GPU information
            cmd = [
                'nvidia-smi', 
                '--query-gpu=index,name,temperature.gpu,utilization.gpu,memory.total,power.draw,fan.speed',
                '--format=csv,noheader,nounits'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                timestamp = time.time()
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        
                        if len(parts) >= 3:
                            try:
                                gpu_id = int(parts[0])
                                gpu_name = parts[1]
                                temp = float(parts[2]) if parts[2] != '[N/A]' else None
                                
                                if temp is not None:
                                    utilization = float(parts[3]) if len(parts) > 3 and parts[3] != '[N/A]' else None
                                    power_draw = float(parts[5]) if len(parts) > 5 and parts[5] != '[N/A]' else None
                                    fan_speed = float(parts[6]) if len(parts) > 6 and parts[6] != '[N/A]' else None
                                    
                                    reading = GPUThermalReading(
                                        timestamp=timestamp,
                                        temperature=temp,
                                        gpu_id=gpu_id,
                                        gpu_name=gpu_name,
                                        utilization=utilization,
                                        power_draw=power_draw,
                                        fan_speed=fan_speed
                                    )
                                    readings.append(reading)
                                    
                            except (ValueError, IndexError):
                                continue
                                
        except subprocess.TimeoutExpired:
            print("nvidia-smi command timed out")
        except Exception as e:
            print(f"Error reading NVIDIA GPU temperatures: {e}")
            
        return readings
    
    def get_amd_temperatures(self) -> List[GPUThermalReading]:
        """Get AMD GPU temperatures using available tools"""
        readings = []
        
        if not self.amd_available:
            return readings
            
        try:
            # Try rocm-smi first
            result = subprocess.run(['rocm-smi', '--showtemp'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                timestamp = time.time()
                lines = result.stdout.strip().split('\n')
                
                for i, line in enumerate(lines):
                    if 'GPU' in line and 'temp' in line.lower():
                        # Parse temperature from rocm-smi output
                        temp_match = re.search(r'(\d+\.?\d*)\s*C', line)
                        if temp_match:
                            temp = float(temp_match.group(1))
                            
                            reading = GPUThermalReading(
                                timestamp=timestamp,
                                temperature=temp,
                                gpu_id=i,
                                gpu_name=f"AMD GPU {i}"
                            )
                            readings.append(reading)
                            
        except subprocess.TimeoutExpired:
            print("rocm-smi command timed out")
        except Exception as e:
            print(f"Error reading AMD GPU temperatures: {e}")
            
        return readings
    
    def get_gpu_temperatures(self) -> List[GPUThermalReading]:
        """Get GPU temperatures from all available GPUs"""
        readings = []
        
        # Try NVIDIA first
        readings.extend(self.get_nvidia_temperatures())
        
        # Try AMD
        readings.extend(self.get_amd_temperatures())
        
        return readings
    
    def get_current_reading(self) -> Optional[GPUThermalReading]:
        """Get the most recent GPU temperature reading"""
        readings = self.get_gpu_temperatures()
        if readings:
            # Return the highest temperature reading
            return max(readings, key=lambda r: r.temperature)
        return None
    
    def get_thermal_state(self) -> Dict:
        """Get current GPU thermal state assessment"""
        readings = self.get_gpu_temperatures()
        
        if not readings:
            return {
                'status': 'no_gpu_detected',
                'temperature': None,
                'state': 'no_data'
            }
            
        max_temp = max(readings, key=lambda r: r.temperature)
        avg_temp = sum(r.temperature for r in readings) / len(readings)
        
        # Determine thermal state (GPU thermal limits are typically higher than CPU)
        if max_temp.temperature > 90:
            state = 'critical'
        elif max_temp.temperature > 80:
            state = 'hot'
        elif max_temp.temperature > 70:
            state = 'warm'
        elif max_temp.temperature > 50:
            state = 'normal'
        else:
            state = 'cool'
            
        return {
            'status': 'active',
            'max_temperature': max_temp.temperature,
            'avg_temperature': avg_temp,
            'num_gpus': len(readings),
            'state': state,
            'readings': readings,
            'nvidia_available': self.nvidia_available,
            'amd_available': self.amd_available
        }
    
    def add_reading_to_history(self, reading: GPUThermalReading):
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
    
    def get_gpu_info(self) -> Dict:
        """Get general GPU information"""
        return {
            'nvidia_available': self.nvidia_available,
            'amd_available': self.amd_available,
            'monitoring_capability': self.nvidia_available or self.amd_available
        }
