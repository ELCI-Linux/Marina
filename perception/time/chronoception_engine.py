#!/usr/bin/env python3
"""
Chronoception Engine for Marina
==============================

This engine provides Marina with the ability to perceive time across multiple dimensions:
- Absolute time (system clock)
- Relative time (durations, intervals)
- Subjective time (processing load effects)
- Rhythmic time (patterns, cycles)
- Predictive time (anticipation)
"""

import time
import threading
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from collections import deque
import psutil
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TimePerception:
    """Represents a moment in Marina's time perception"""
    timestamp: float
    system_time: datetime
    subjective_time: float  # Time as perceived by Marina (affected by processing load)
    attention_coefficient: float  # How much attention Marina is paying to time
    processing_load: float  # Current CPU/memory usage affecting time perception
    context: str  # What Marina is doing when this perception occurred
    rhythmic_phase: float  # Position in any detected rhythmic patterns
    prediction_confidence: float  # How confident Marina is about near-future time

@dataclass
class TimeInterval:
    """Represents an interval of time with contextual information"""
    start_time: float
    end_time: float
    duration: float
    context: str
    subjective_duration: float
    attention_level: float

class ChronoceptionEngine:
    def __init__(self):
        self.start_time = time.time()
        self.perceptions: deque = deque(maxlen=10000)  # Ring buffer for time perceptions
        self.intervals: List[TimeInterval] = []
        self.rhythmic_patterns: Dict[str, List[float]] = {}
        self.attention_focus = 1.0
        self.running = False
        self.perception_thread = None
        
        # Time dilation factors
        self.base_tick_rate = 10  # Hz - base perception frequency
        self.current_tick_rate = self.base_tick_rate
        
        # Subjective time tracking
        self.subjective_time_offset = 0.0
        self.last_system_time = time.time()
        
        # Pattern detection
        self.pattern_detector = PatternDetector()
        
        # Predictive time model
        self.time_predictor = TimePredictor()
        
    def start(self):
        """Start the chronoception engine"""
        self.running = True
        self.perception_thread = threading.Thread(target=self._perception_loop, daemon=True)
        self.perception_thread.start()
        logger.info("Chronoception engine started")
        
    def stop(self):
        """Stop the chronoception engine"""
        self.running = False
        if self.perception_thread:
            self.perception_thread.join()
        logger.info("Chronoception engine stopped")
        
    def _perception_loop(self):
        """Main perception loop that runs continuously"""
        while self.running:
            try:
                perception = self._generate_time_perception()
                self.perceptions.append(perception)
                
                # Update patterns
                self.pattern_detector.update(perception)
                
                # Update predictions
                self.time_predictor.update(perception)
                
                # Adaptive tick rate based on processing load
                self._adapt_tick_rate(perception.processing_load)
                
                # Sleep until next perception
                sleep_time = 1.0 / self.current_tick_rate
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in perception loop: {e}")
                time.sleep(0.1)
                
    def _generate_time_perception(self) -> TimePerception:
        """Generate a single time perception snapshot"""
        current_time = time.time()
        system_time = datetime.now()
        
        # Calculate subjective time (affected by processing load)
        processing_load = self._get_processing_load()
        time_dilation = self._calculate_time_dilation(processing_load)
        
        delta_real = current_time - self.last_system_time
        delta_subjective = delta_real * time_dilation
        self.subjective_time_offset += delta_subjective
        
        # Get rhythmic phase
        rhythmic_phase = self.pattern_detector.get_current_phase()
        
        # Get prediction confidence
        prediction_confidence = self.time_predictor.get_confidence()
        
        perception = TimePerception(
            timestamp=current_time,
            system_time=system_time,
            subjective_time=self.subjective_time_offset,
            attention_coefficient=self.attention_focus,
            processing_load=processing_load,
            context=self._get_current_context(),
            rhythmic_phase=rhythmic_phase,
            prediction_confidence=prediction_confidence
        )
        
        self.last_system_time = current_time
        return perception
        
    def _get_processing_load(self) -> float:
        """Get current system processing load"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            return (cpu_percent + memory_percent) / 200.0  # Normalize to 0-1
        except:
            return 0.5  # Default moderate load
            
    def _calculate_time_dilation(self, processing_load: float) -> float:
        """Calculate time dilation factor based on processing load"""
        # When processing load is high, time feels slower (more detail perceived)
        # When processing load is low, time feels faster (less detail perceived)
        base_dilation = 1.0
        load_factor = 1.0 - (processing_load * 0.3)  # Max 30% time dilation
        attention_factor = self.attention_focus
        
        return base_dilation * load_factor * attention_factor
        
    def _adapt_tick_rate(self, processing_load: float):
        """Adapt perception tick rate based on processing load"""
        if processing_load > 0.8:
            self.current_tick_rate = self.base_tick_rate * 0.5  # Slow down when overloaded
        elif processing_load < 0.2:
            self.current_tick_rate = self.base_tick_rate * 1.5  # Speed up when idle
        else:
            self.current_tick_rate = self.base_tick_rate
            
    def _get_current_context(self) -> str:
        """Get current context/activity"""
        # This could be expanded to integrate with other Marina systems
        return "time_perception"
        
    def set_attention_focus(self, focus_level: float):
        """Set how much attention Marina is paying to time (0.0 to 2.0)"""
        self.attention_focus = max(0.1, min(2.0, focus_level))
        
    def get_current_perception(self) -> Optional[TimePerception]:
        """Get the most recent time perception"""
        return self.perceptions[-1] if self.perceptions else None
        
    def get_time_since_start(self) -> float:
        """Get time elapsed since engine started"""
        return time.time() - self.start_time
        
    def get_subjective_time_since_start(self) -> float:
        """Get subjective time elapsed since engine started"""
        return self.subjective_time_offset
        
    def mark_interval_start(self, context: str) -> str:
        """Mark the start of a time interval"""
        interval_id = f"{context}_{len(self.intervals)}"
        # Store interval start info for later completion
        setattr(self, f"_interval_start_{interval_id}", {
            'start_time': time.time(),
            'context': context,
            'attention_level': self.attention_focus
        })
        return interval_id
        
    def mark_interval_end(self, interval_id: str) -> Optional[TimeInterval]:
        """Mark the end of a time interval"""
        start_info = getattr(self, f"_interval_start_{interval_id}", None)
        if not start_info:
            return None
            
        end_time = time.time()
        duration = end_time - start_info['start_time']
        
        # Calculate subjective duration
        subjective_duration = duration * self.attention_focus
        
        interval = TimeInterval(
            start_time=start_info['start_time'],
            end_time=end_time,
            duration=duration,
            context=start_info['context'],
            subjective_duration=subjective_duration,
            attention_level=start_info['attention_level']
        )
        
        self.intervals.append(interval)
        delattr(self, f"_interval_start_{interval_id}")
        
        return interval
        
    def get_time_statistics(self) -> Dict[str, Any]:
        """Get comprehensive time perception statistics"""
        if not self.perceptions:
            return {}
            
        recent_perceptions = list(self.perceptions)[-100:]  # Last 100 perceptions
        
        avg_processing_load = sum(p.processing_load for p in recent_perceptions) / len(recent_perceptions)
        avg_attention = sum(p.attention_coefficient for p in recent_perceptions) / len(recent_perceptions)
        
        return {
            'uptime_seconds': self.get_time_since_start(),
            'subjective_uptime_seconds': self.get_subjective_time_since_start(),
            'time_dilation_ratio': self.get_subjective_time_since_start() / self.get_time_since_start(),
            'current_tick_rate': self.current_tick_rate,
            'average_processing_load': avg_processing_load,
            'average_attention_coefficient': avg_attention,
            'total_perceptions': len(self.perceptions),
            'total_intervals': len(self.intervals),
            'detected_patterns': len(self.pattern_detector.patterns),
            'prediction_confidence': self.time_predictor.get_confidence()
        }

class PatternDetector:
    """Detects rhythmic patterns in time perception"""
    
    def __init__(self):
        self.patterns: Dict[str, List[float]] = {}
        self.phase_history: deque = deque(maxlen=1000)
        
    def update(self, perception: TimePerception):
        """Update pattern detection with new perception"""
        self.phase_history.append(perception.timestamp)
        
        # Simple pattern detection - could be enhanced with FFT, etc.
        if len(self.phase_history) > 10:
            self._detect_periodic_patterns()
            
    def _detect_periodic_patterns(self):
        """Detect periodic patterns in the phase history"""
        # Simple autocorrelation-based pattern detection
        # This is a placeholder for more sophisticated pattern detection
        pass
        
    def get_current_phase(self) -> float:
        """Get current phase in detected patterns"""
        if not self.phase_history:
            return 0.0
            
        # Simple sine wave phase based on time
        current_time = self.phase_history[-1]
        return math.sin(current_time * 2 * math.pi / 60)  # 1-minute cycle

class TimePredictor:
    """Predicts future time-related events"""
    
    def __init__(self):
        self.confidence = 0.5
        self.prediction_history: deque = deque(maxlen=100)
        
    def update(self, perception: TimePerception):
        """Update predictions with new perception"""
        self.prediction_history.append(perception)
        
        # Simple confidence calculation based on pattern stability
        if len(self.prediction_history) > 10:
            self._update_confidence()
            
    def _update_confidence(self):
        """Update prediction confidence based on recent patterns"""
        # Simple confidence based on processing load stability
        recent_loads = [p.processing_load for p in list(self.prediction_history)[-10:]]
        load_variance = sum((x - sum(recent_loads)/len(recent_loads))**2 for x in recent_loads) / len(recent_loads)
        
        # Lower variance = higher confidence
        self.confidence = max(0.1, min(0.9, 1.0 - load_variance))
        
    def get_confidence(self) -> float:
        """Get current prediction confidence"""
        return self.confidence

# Example usage and testing
if __name__ == "__main__":
    # Create and start the chronoception engine
    engine = ChronoceptionEngine()
    engine.start()
    
    try:
        # Run for a few seconds to demonstrate
        time.sleep(5)
        
        # Test interval marking
        interval_id = engine.mark_interval_start("test_task")
        time.sleep(2)
        interval = engine.mark_interval_end(interval_id)
        
        # Get statistics
        stats = engine.get_time_statistics()
        print("Time Perception Statistics:")
        print(json.dumps(stats, indent=2))
        
        # Get current perception
        current = engine.get_current_perception()
        if current:
            print(f"\nCurrent Perception:")
            print(f"  System Time: {current.system_time}")
            print(f"  Subjective Time: {current.subjective_time:.3f}")
            print(f"  Processing Load: {current.processing_load:.3f}")
            print(f"  Attention: {current.attention_coefficient:.3f}")
            
    finally:
        engine.stop()
