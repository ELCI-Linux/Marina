# observation_engine.py
"""
Core observation engine providing base functionality for both internal and external observation systems.
"""

import abc
import logging
import threading
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image


class ObservationType(Enum):
    INTERNAL = "internal"  # Screen content, documents, images
    EXTERNAL = "external"  # Webcam, live streams, real-world


@dataclass
class ObservationResult:
    """Standard observation result structure"""
    timestamp: float
    observation_type: ObservationType
    source: str
    confidence: float
    data: Dict[str, Any]
    metadata: Dict[str, Any]


class ObservationEngine(abc.ABC):
    """Base class for observation engines"""
    
    def __init__(self, name: str, observation_type: ObservationType):
        self.name = name
        self.observation_type = observation_type
        self.is_running = False
        self.logger = logging.getLogger(f"ObservationEngine.{name}")
        self.callbacks: List[Callable[[ObservationResult], None]] = []
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def add_callback(self, callback: Callable[[ObservationResult], None]):
        """Add callback to be called when observation is made"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[ObservationResult], None]):
        """Remove callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self, result: ObservationResult):
        """Notify all registered callbacks with observation result"""
        for callback in self.callbacks:
            try:
                callback(result)
            except Exception as e:
                self.logger.error(f"Error in callback: {e}")
    
    @abc.abstractmethod
    def start_observation(self):
        """Start the observation process"""
        pass
    
    @abc.abstractmethod
    def stop_observation(self):
        """Stop the observation process"""
        pass
    
    @abc.abstractmethod
    def get_current_observation(self) -> Optional[ObservationResult]:
        """Get current observation result"""
        pass


class ImageAnalyzer:
    """Common image analysis utilities"""
    
    @staticmethod
    def detect_objects(image: np.ndarray) -> List[Dict[str, Any]]:
        """Basic object detection using OpenCV"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Simple edge detection
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        objects = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Filter small objects
                x, y, w, h = cv2.boundingRect(contour)
                objects.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'type': 'unknown'
                })
        
        return objects
    
    @staticmethod
    def analyze_text_regions(image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect potential text regions"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Use morphological operations to find text regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
        
        _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 50:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                if 0.2 < aspect_ratio < 10:  # Typical text aspect ratios
                    text_regions.append({
                        'bbox': (x, y, w, h),
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
        
        return text_regions
    
    @staticmethod
    def calculate_image_features(image: np.ndarray) -> Dict[str, Any]:
        """Calculate basic image features"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Color histogram
        hist_b = cv2.calcHist([image], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([image], [1], None, [256], [0, 256])
        hist_r = cv2.calcHist([image], [2], None, [256], [0, 256])
        
        # Basic statistics
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        return {
            'brightness': float(brightness),
            'contrast': float(contrast),
            'histogram': {
                'blue': hist_b.flatten().tolist(),
                'green': hist_g.flatten().tolist(),
                'red': hist_r.flatten().tolist()
            },
            'dimensions': image.shape[:2]
        }
