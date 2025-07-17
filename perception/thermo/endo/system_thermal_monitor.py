"""
System Thermal Monitor
Comprehensive system thermal monitoring and management
"""

import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from .cpu_thermal_sensor import CPUThermalSensor
from .gpu_thermal_sensor import GPUThermalSensor
from .thermal_state_manager import ThermalStateManager


@dataclass
class ThermalAlert:
    """Thermal alert data structure"""
    timestamp: float
    component: str
    temperature: float
    threshold: float
    severity: str
    message: str


class SystemThermalMonitor:
    """Comprehensive system thermal monitoring"""
    
    def __init__(self, update_interval: float = 2.0):
        self.update_interval = update_interval
        self.cpu_sensor = CPUThermalSensor()
        self.gpu_sensor = GPUThermalSensor()
        self.thermal_manager = ThermalStateManager()
        
        self.monitoring = False
        self.monitor_thread = None
        self.alerts: List[ThermalAlert] = []
        self.alert_callbacks: List[Callable] = []
        
        # Thermal thresholds
        self.cpu_thresholds = {
            'warning': 70.0,
            'critical': 80.0,
            'emergency': 90.0
        }
        
        self.gpu_thresholds = {
            'warning': 75.0,
            'critical': 85.0,
            'emergency': 95.0
        }
        
    def add_alert_callback(self, callback: Callable):
        """Add callback for thermal alerts"""
        self.alert_callbacks.append(callback)
        
    def remove_alert_callback(self, callback: Callable):
        """Remove callback for thermal alerts"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def _trigger_alert(self, alert: ThermalAlert):
        """Trigger thermal alert"""
        self.alerts.append(alert)
        
        # Keep only recent alerts (last 100)
        if len(self.alerts) > 100:
            self.alerts.pop(0)
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")
    
    def _check_thermal_thresholds(self):
        """Check thermal thresholds and generate alerts"""
        timestamp = time.time()
        
        # Check CPU temperatures
        cpu_reading = self.cpu_sensor.get_current_reading()
        if cpu_reading:
            temp = cpu_reading.temperature
            
            if temp >= self.cpu_thresholds['emergency']:
                alert = ThermalAlert(
                    timestamp=timestamp,
                    component='CPU',
                    temperature=temp,
                    threshold=self.cpu_thresholds['emergency'],
                    severity='emergency',
                    message=f'CPU temperature critical: {temp:.1f}°C'
                )
                self._trigger_alert(alert)
                
            elif temp >= self.cpu_thresholds['critical']:
                alert = ThermalAlert(
                    timestamp=timestamp,
                    component='CPU',
                    temperature=temp,
                    threshold=self.cpu_thresholds['critical'],
                    severity='critical',
                    message=f'CPU temperature high: {temp:.1f}°C'
                )
                self._trigger_alert(alert)
                
            elif temp >= self.cpu_thresholds['warning']:
                alert = ThermalAlert(
                    timestamp=timestamp,
                    component='CPU',
                    temperature=temp,
                    threshold=self.cpu_thresholds['warning'],
                    severity='warning',
                    message=f'CPU temperature elevated: {temp:.1f}°C'
                )
                self._trigger_alert(alert)
        
        # Check GPU temperatures
        gpu_reading = self.gpu_sensor.get_current_reading()
        if gpu_reading:
            temp = gpu_reading.temperature
            
            if temp >= self.gpu_thresholds['emergency']:
                alert = ThermalAlert(
                    timestamp=timestamp,
                    component='GPU',
                    temperature=temp,
                    threshold=self.gpu_thresholds['emergency'],
                    severity='emergency',
                    message=f'GPU temperature critical: {temp:.1f}°C'
                )
                self._trigger_alert(alert)
                
            elif temp >= self.gpu_thresholds['critical']:
                alert = ThermalAlert(
                    timestamp=timestamp,
                    component='GPU',
                    temperature=temp,
                    threshold=self.gpu_thresholds['critical'],
                    severity='critical',
                    message=f'GPU temperature high: {temp:.1f}°C'
                )
                self._trigger_alert(alert)
                
            elif temp >= self.gpu_thresholds['warning']:
                alert = ThermalAlert(
                    timestamp=timestamp,
                    component='GPU',
                    temperature=temp,
                    threshold=self.gpu_thresholds['warning'],
                    severity='warning',
                    message=f'GPU temperature elevated: {temp:.1f}°C'
                )
                self._trigger_alert(alert)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Check thermal thresholds
                self._check_thermal_thresholds()
                
                # Add readings to history
                cpu_reading = self.cpu_sensor.get_current_reading()
                if cpu_reading:
                    self.cpu_sensor.add_reading_to_history(cpu_reading)
                
                gpu_reading = self.gpu_sensor.get_current_reading()
                if gpu_reading:
                    self.gpu_sensor.add_reading_to_history(gpu_reading)
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Error in thermal monitoring loop: {e}")
                time.sleep(self.update_interval)
    
    def start_monitoring(self):
        """Start thermal monitoring"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            print("System thermal monitoring started")
    
    def stop_monitoring(self):
        """Stop thermal monitoring"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            print("System thermal monitoring stopped")
    
    def get_thermal_summary(self) -> Dict:
        """Get comprehensive thermal summary"""
        system_state = self.thermal_manager.get_system_thermal_state()
        overall_status = self.thermal_manager.get_overall_status()
        
        # Get recent alerts
        recent_alerts = [alert for alert in self.alerts 
                        if time.time() - alert.timestamp < 3600]  # Last hour
        
        # Get temperature trends
        cpu_trend = self.cpu_sensor.get_temperature_trend()
        gpu_trend = self.gpu_sensor.get_temperature_trend()
        
        return {
            'timestamp': time.time(),
            'overall_status': overall_status,
            'system_state': system_state,
            'trends': {
                'cpu': cpu_trend,
                'gpu': gpu_trend
            },
            'recent_alerts': recent_alerts,
            'thresholds': {
                'cpu': self.cpu_thresholds,
                'gpu': self.gpu_thresholds
            },
            'monitoring_active': self.monitoring
        }
    
    def get_thermal_report(self) -> str:
        """Generate human-readable thermal report"""
        summary = self.get_thermal_summary()
        
        report = []
        report.append("=== System Thermal Report ===")
        report.append(f"Overall Status: {summary['overall_status'].upper()}")
        report.append("")
        
        # CPU information
        cpu_state = summary['system_state']['cpu']
        if cpu_state['status'] == 'active':
            report.append(f"CPU Temperature: {cpu_state['max_temperature']:.1f}°C ({cpu_state['state']})")
            report.append(f"CPU Trend: {summary['trends']['cpu']}")
        else:
            report.append("CPU: No data available")
        
        # GPU information
        gpu_state = summary['system_state']['gpu']
        if gpu_state['status'] == 'active':
            report.append(f"GPU Temperature: {gpu_state['max_temperature']:.1f}°C ({gpu_state['state']})")
            report.append(f"GPU Trend: {summary['trends']['gpu']}")
        else:
            report.append("GPU: No data available")
        
        # Recent alerts
        if summary['recent_alerts']:
            report.append("")
            report.append("Recent Alerts:")
            for alert in summary['recent_alerts'][-5:]:  # Last 5 alerts
                report.append(f"  - {alert.message} ({alert.severity})")
        
        report.append("")
        report.append(f"Monitoring Active: {summary['monitoring_active']}")
        
        return "\\n".join(report)
    
    def set_cpu_thresholds(self, warning: float, critical: float, emergency: float):
        """Set CPU thermal thresholds"""
        self.cpu_thresholds = {
            'warning': warning,
            'critical': critical,
            'emergency': emergency
        }
    
    def set_gpu_thresholds(self, warning: float, critical: float, emergency: float):
        """Set GPU thermal thresholds"""
        self.gpu_thresholds = {
            'warning': warning,
            'critical': critical,
            'emergency': emergency
        }
    
    def clear_alerts(self):
        """Clear thermal alerts"""
        self.alerts.clear()
    
    def get_alert_history(self) -> List[ThermalAlert]:
        """Get thermal alert history"""
        return self.alerts.copy()
