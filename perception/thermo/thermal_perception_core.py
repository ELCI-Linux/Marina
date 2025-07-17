"""
Core logic for Marina's thermal perception
Combines internal and external thermal sensing for an integrated assessment
"""

from .endo.system_thermal_monitor import SystemThermalMonitor
from .exo.thermal_state_manager import ThermalStateManager as ExoThermalManager
from typing import Dict


class ThermalPerceptionCore:
    """Core module representing Marina's comprehensive thermal perception"""

    def __init__(self):
        self.system_monitor = SystemThermalMonitor()
        self.environment_manager = ExoThermalManager()

    def start_all_monitoring(self):
        """Start monitoring system and environmental thermal states"""
        self.system_monitor.start_monitoring()
        # Environmental monitoring would be triggered separately if implemented

    def stop_all_monitoring(self):
        """Stop all thermal monitoring"""
        self.system_monitor.stop_monitoring()
        # Environmental monitoring stop would be triggered separately

    def get_thermal_overview(self) -> Dict:
        """Get an overview of the current thermal perception for the system and environment"""
        system_summary = self.system_monitor.get_thermal_summary()
        environment_summary = self.environment_manager.get_environment_thermal_state()

        return {
            "system": system_summary,
            "environment": environment_summary
        }

    def get_comprehensive_report(self) -> str:
        """Generate a comprehensive thermal report for both system and environment"""
        report = []
        report.append("=== Comprehensive Thermal Report ===")
        report.append("")

        # System Report
        system_report = self.system_monitor.get_thermal_report()
        report.append(system_report)
        report.append("")

        # Environment Report
        env_state = self.environment_manager.get_comfort_assessment()
        report.append(f"Environment Status: {env_state['comfort_level']}")
        report.append(env_state['assessment'])
        report.append("")

        return "\n".join(report)
