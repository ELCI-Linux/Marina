"""
Kinetic Coordinator - Integrates internal and external kinetic perception engines
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from endo.internal_kinetic_engine import InternalKineticEngine
from exo.external_kinetic_engine import ExternalKineticEngine


class KineticCoordinator:
    """
    Coordinates between internal (endo) and external (exo) kinetic perception engines
    to provide unified kinetic awareness for the Marina system.
    """
    
    def __init__(self):
        self.internal_engine = InternalKineticEngine()
        self.external_engine = ExternalKineticEngine()
    
    def process_unified_kinetic_data(self, internal_data, external_data):
        """
        Process both internal and external kinetic data to create unified perception
        """
        internal_result = self.internal_engine.process_data(internal_data)
        external_result = self.external_engine.process_data(external_data)
        
        return {
            'internal': internal_result,
            'external': external_result,
            'unified': f"Unified perception: {internal_result} + {external_result}"
        }
    
    def get_kinetic_status(self):
        """
        Get the current status of both kinetic perception engines
        """
        return {
            'internal_engine': 'Active',
            'external_engine': 'Active',
            'coordination': 'Synchronized'
        }
