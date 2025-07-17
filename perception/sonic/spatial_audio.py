"""
Spatial Audio Processing Module
3D sound localization and spatial audio analysis
"""

import numpy as np
import scipy.signal
from typing import Dict, Tuple, List, Optional
import logging

class SpatialAudioProcessor:
    """Advanced spatial audio processing and sound localization"""
    
    def __init__(self, mic_array_config: Optional[Dict] = None):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Default microphone array configuration (square array)
        self.mic_array = mic_array_config or {
            'positions': np.array([
                [0.0, 0.0, 0.0],      # Center microphone
                [0.05, 0.0, 0.0],     # Right microphone
                [-0.05, 0.0, 0.0],    # Left microphone
                [0.0, 0.05, 0.0],     # Front microphone
                [0.0, -0.05, 0.0]     # Back microphone
            ]),
            'num_mics': 5
        }
        
        # Sound speed in air (m/s)
        self.sound_speed = 343.0
        
    def calculate_tdoa(self, audio_channels: List[np.ndarray], 
                      sample_rate: int) -> Dict[str, np.ndarray]:
        """Calculate Time Difference of Arrival (TDOA) between microphones"""
        if len(audio_channels) < 2:
            raise ValueError("Need at least 2 audio channels for TDOA calculation")
        
        # Use first channel as reference
        ref_channel = audio_channels[0]
        tdoa_results = {}
        
        for i, channel in enumerate(audio_channels[1:], 1):
            # Cross-correlation to find delay
            correlation = scipy.signal.correlate(channel, ref_channel, mode='full')
            delay_samples = np.argmax(correlation) - len(ref_channel) + 1
            delay_time = delay_samples / sample_rate
            
            tdoa_results[f'mic_{i}_delay'] = delay_time
            
        return tdoa_results
    
    def estimate_direction_of_arrival(self, tdoa_results: Dict[str, float], 
                                    sample_rate: int) -> Dict[str, float]:
        """Estimate direction of arrival using TDOA measurements"""
        # Simplified 2D direction estimation
        # In practice, this would use more sophisticated algorithms like MUSIC or ESPRIT
        
        if len(tdoa_results) < 2:
            return {'azimuth': 0.0, 'elevation': 0.0, 'confidence': 0.0}
        
        # Extract delays
        delays = list(tdoa_results.values())
        
        # Simple triangulation (simplified for demonstration)
        # Real implementation would use proper geometric calculations
        avg_delay = np.mean(delays)
        delay_variation = np.std(delays)
        
        # Estimate azimuth based on left-right delay difference
        lr_delay = delays[0] if len(delays) > 0 else 0
        azimuth = np.arctan2(lr_delay * self.sound_speed, 0.1) * 180 / np.pi
        
        # Estimate elevation (simplified)
        elevation = 0.0  # Assume horizontal for now
        
        # Confidence based on delay consistency
        confidence = 1.0 / (1.0 + delay_variation * 100)
        
        return {
            'azimuth': azimuth,
            'elevation': elevation,
            'confidence': confidence
        }
    
    def beamforming(self, audio_channels: List[np.ndarray], 
                   target_direction: Tuple[float, float]) -> np.ndarray:
        """Apply beamforming to enhance audio from specific direction"""
        if len(audio_channels) != self.mic_array['num_mics']:
            raise ValueError(f"Expected {self.mic_array['num_mics']} channels, got {len(audio_channels)}")
        
        azimuth, elevation = target_direction
        
        # Calculate weights for each microphone based on target direction
        weights = self._calculate_beamforming_weights(azimuth, elevation)
        
        # Apply weights to each channel
        beamformed_audio = np.zeros_like(audio_channels[0])
        for i, channel in enumerate(audio_channels):
            beamformed_audio += weights[i] * channel
        
        return beamformed_audio
    
    def _calculate_beamforming_weights(self, azimuth: float, 
                                     elevation: float) -> np.ndarray:
        """Calculate beamforming weights for target direction"""
        # Convert angles to radians
        azimuth_rad = np.radians(azimuth)
        elevation_rad = np.radians(elevation)
        
        # Target direction vector
        target_dir = np.array([
            np.cos(elevation_rad) * np.cos(azimuth_rad),
            np.cos(elevation_rad) * np.sin(azimuth_rad),
            np.sin(elevation_rad)
        ])
        
        # Calculate weights based on microphone positions
        weights = np.zeros(self.mic_array['num_mics'])
        for i, mic_pos in enumerate(self.mic_array['positions']):
            # Simple delay-and-sum beamforming
            dot_product = np.dot(mic_pos, target_dir)
            weights[i] = np.exp(-abs(dot_product))
        
        # Normalize weights
        weights = weights / np.sum(weights)
        
        return weights
    
    def detect_sound_events_spatial(self, audio_channels: List[np.ndarray], 
                                   sample_rate: int) -> List[Dict]:
        """Detect sound events with spatial information"""
        events = []
        
        # Calculate TDOA for each time window
        window_size = int(0.1 * sample_rate)  # 100ms windows
        hop_size = int(0.05 * sample_rate)    # 50ms hop
        
        for start in range(0, len(audio_channels[0]) - window_size, hop_size):
            # Extract windows from all channels
            windows = [channel[start:start + window_size] 
                      for channel in audio_channels]
            
            # Calculate energy in each channel
            energies = [np.sum(window**2) for window in windows]
            max_energy = max(energies)
            
            # Only process if there's significant energy
            if max_energy > 0.001:
                # Calculate TDOA
                tdoa = self.calculate_tdoa(windows, sample_rate)
                
                # Estimate direction
                direction = self.estimate_direction_of_arrival(tdoa, sample_rate)
                
                # Create event
                event = {
                    'timestamp': start / sample_rate,
                    'duration': window_size / sample_rate,
                    'energy': max_energy,
                    'direction': direction,
                    'tdoa': tdoa
                }
                
                events.append(event)
        
        return events
    
    def create_spatial_audio_map(self, events: List[Dict]) -> Dict:
        """Create a spatial map of detected audio events"""
        spatial_map = {
            'events_by_direction': {},
            'hotspots': [],
            'total_events': len(events)
        }
        
        # Group events by direction (quantized to 30-degree sectors)
        for event in events:
            azimuth = event['direction']['azimuth']
            sector = int(azimuth // 30) * 30
            
            if sector not in spatial_map['events_by_direction']:
                spatial_map['events_by_direction'][sector] = []
            
            spatial_map['events_by_direction'][sector].append(event)
        
        # Identify hotspots (directions with high activity)
        for sector, sector_events in spatial_map['events_by_direction'].items():
            if len(sector_events) > 3:  # Threshold for hotspot
                total_energy = sum(event['energy'] for event in sector_events)
                spatial_map['hotspots'].append({
                    'direction': sector,
                    'event_count': len(sector_events),
                    'total_energy': total_energy,
                    'avg_confidence': np.mean([event['direction']['confidence'] 
                                             for event in sector_events])
                })
        
        return spatial_map
    
    def adaptive_noise_cancellation(self, audio_channels: List[np.ndarray], 
                                  noise_reference: np.ndarray) -> List[np.ndarray]:
        """Apply adaptive noise cancellation using reference noise"""
        filtered_channels = []
        
        for channel in audio_channels:
            # Simple adaptive filter using LMS algorithm
            filtered_channel = self._lms_filter(channel, noise_reference)
            filtered_channels.append(filtered_channel)
        
        return filtered_channels
    
    def _lms_filter(self, signal: np.ndarray, noise_ref: np.ndarray, 
                   mu: float = 0.01, filter_order: int = 32) -> np.ndarray:
        """Least Mean Squares adaptive filter"""
        # Ensure same length
        min_length = min(len(signal), len(noise_ref))
        signal = signal[:min_length]
        noise_ref = noise_ref[:min_length]
        
        # Initialize filter coefficients
        w = np.zeros(filter_order)
        filtered_signal = np.zeros_like(signal)
        
        # Apply LMS algorithm
        for n in range(filter_order, len(signal)):
            # Input vector
            x = noise_ref[n-filter_order:n][::-1]
            
            # Filter output
            y = np.dot(w, x)
            
            # Error signal
            e = signal[n] - y
            
            # Update coefficients
            w = w + mu * e * x
            
            # Store filtered output
            filtered_signal[n] = e
        
        return filtered_signal
