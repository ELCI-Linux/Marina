# exo_engine.py
"""
External observation engine for capturing video streams or webcam input.
Enhanced with periodic environmental snapshots, lighting analysis, and user recognition.
"""

import cv2
import time
import threading
import numpy as np
import json
import pickle
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from observation_engine import ObservationEngine, ObservationType, ObservationResult, ImageAnalyzer


class ExternalObservationEngine(ObservationEngine):
    def __init__(self, camera_index=0):
        super().__init__(name="ExternalObservation", observation_type=ObservationType.EXTERNAL)
        self.camera_index = camera_index
        self._capture = None
        self._capture_thread = None

    def start_observation(self):
        """Start observation process with periodic snapshot, lighting, and user recognition"""
        self.snapshot_interval = 300  # Snapshot every 300 seconds
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.recognizer_model_path = 'user_recognizer_model.xml'
        self.load_recognizer_model()
        if not self.is_running:
            self.is_running = True
            self._capture = cv2.VideoCapture(self.camera_index)
            self._capture_thread = threading.Thread(target=self._run)
            self._capture_thread.start()

    def stop_observation(self):
        if self.is_running:
            self.is_running = False
            if self._capture:
                self._capture.release()
            if self._capture_thread:
                self._capture_thread.join()

    def _run(self):
        while self.is_running:
            current_time = time.time()
            ret, frame = self._capture.read()
            
            if current_time % self.snapshot_interval == 0:
                snapshot_result = self._get_snapshot(frame)
                self._notify_callbacks(snapshot_result)
            if not ret:
                self.logger.error("Failed to capture frame")
                continue

            observation_result = self._analyze_frame(frame)

            # Notify all callbacks
            self._notify_callbacks(observation_result)

            # Simulate a delay for capturing
            time.sleep(0.1)

    def _analyze_frame(self, frame: np.ndarray) -> ObservationResult:
        # Analyze the frame
        brightness = np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        lighting_condition = 'bright' if brightness > 150 else 'dim'
        
        objects = ImageAnalyzer.detect_objects(frame)
        features = ImageAnalyzer.calculate_image_features(frame)

        # Construct result
        result = ObservationResult(
            timestamp=time.time(),
            observation_type=ObservationType.EXTERNAL,
            source="camera_{}".format(self.camera_index),
            confidence=0.9,  # Mocked confidence
            data={
                'objects': objects,
                'features': features,
                'lighting': lighting_condition,
                'recognized_user': self._recognize_user(frame)
            },
            metadata={
                'resolution': frame.shape
            }
        )
        return result

    def get_current_observation(self) -> Optional[ObservationResult]:
        # For simplicity, return None (a real implementation might return current state)
        return None
    
    def load_recognizer_model(self):
        """Load or initialize the face recognizer model"""
        if os.path.exists(self.recognizer_model_path):
            try:
                self.face_recognizer.read(self.recognizer_model_path)
                self.logger.info("Face recognizer model loaded successfully")
            except Exception as e:
                self.logger.warning(f"Failed to load face recognizer model: {e}")
                self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        else:
            self.logger.info("No existing face recognizer model found. Starting fresh.")
    
    def save_recognizer_model(self):
        """Save the face recognizer model"""
        try:
            self.face_recognizer.write(self.recognizer_model_path)
            self.logger.info("Face recognizer model saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save face recognizer model: {e}")
    
    def _get_snapshot(self, frame: np.ndarray) -> ObservationResult:
        """Get a comprehensive environmental snapshot"""
        timestamp = time.time()
        
        # Analyze lighting conditions with deductive reasoning
        lighting_analysis = self._analyze_lighting_conditions(frame)
        
        # Detect and analyze faces
        face_analysis = self._analyze_faces(frame)
        
        # Environmental analysis
        environmental_features = self._analyze_environment(frame)
        
        # Save snapshot image
        snapshot_filename = f"snapshot_{datetime.fromtimestamp(timestamp).strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(snapshot_filename, frame)
        
        return ObservationResult(
            timestamp=timestamp,
            observation_type=ObservationType.EXTERNAL,
            source="environmental_snapshot",
            confidence=0.95,
            data={
                'lighting_analysis': lighting_analysis,
                'face_analysis': face_analysis,
                'environmental_features': environmental_features,
                'snapshot_file': snapshot_filename
            },
            metadata={
                'resolution': frame.shape,
                'capture_time': datetime.fromtimestamp(timestamp).isoformat()
            }
        )
    
    def _analyze_lighting_conditions(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyze lighting conditions using deductive reasoning"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Basic metrics
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # Histogram analysis
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Deductive reasoning for lighting conditions
        conditions = []
        
        # Brightness analysis
        if mean_brightness < 50:
            conditions.append("very_dark")
        elif mean_brightness < 100:
            conditions.append("dark")
        elif mean_brightness < 150:
            conditions.append("moderate")
        elif mean_brightness < 200:
            conditions.append("bright")
        else:
            conditions.append("very_bright")
        
        # Contrast analysis
        if std_brightness < 20:
            conditions.append("low_contrast")
        elif std_brightness > 60:
            conditions.append("high_contrast")
        
        # Lighting uniformity
        quarters = [
            gray[:gray.shape[0]//2, :gray.shape[1]//2],
            gray[:gray.shape[0]//2, gray.shape[1]//2:],
            gray[gray.shape[0]//2:, :gray.shape[1]//2],
            gray[gray.shape[0]//2:, gray.shape[1]//2:]
        ]
        quarter_means = [np.mean(q) for q in quarters]
        lighting_variance = np.var(quarter_means)
        
        if lighting_variance < 100:
            conditions.append("uniform_lighting")
        else:
            conditions.append("uneven_lighting")
        
        # Time-based deduction (if available)
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 8 or 18 <= current_hour <= 20:
            conditions.append("golden_hour")
        elif 12 <= current_hour <= 14:
            conditions.append("noon_lighting")
        elif current_hour < 6 or current_hour > 20:
            conditions.append("artificial_lighting_likely")
        
        return {
            'mean_brightness': float(mean_brightness),
            'std_brightness': float(std_brightness),
            'lighting_variance': float(lighting_variance),
            'conditions': conditions,
            'histogram': hist.flatten().tolist()[:50],  # First 50 bins
            'deduced_lighting_type': self._deduce_lighting_type(conditions, mean_brightness)
        }
    
    def _deduce_lighting_type(self, conditions: List[str], brightness: float) -> str:
        """Deduce the type of lighting based on analysis"""
        if "artificial_lighting_likely" in conditions and brightness > 100:
            return "artificial_indoor"
        elif "golden_hour" in conditions:
            return "natural_golden"
        elif "noon_lighting" in conditions and brightness > 150:
            return "natural_direct_sunlight"
        elif "uniform_lighting" in conditions and brightness > 120:
            return "artificial_office"
        elif "very_dark" in conditions:
            return "minimal_ambient"
        else:
            return "natural_diffuse"
    
    def _analyze_faces(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyze faces in the frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        
        face_data = []
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            face_data.append({
                'bbox': (int(x), int(y), int(w), int(h)),
                'area': int(w * h),
                'position': 'center' if x > frame.shape[1]//3 and x < 2*frame.shape[1]//3 else 'side'
            })
        
        return {
            'face_count': len(faces),
            'faces': face_data,
            'primary_user_present': len(faces) > 0
        }
    
    def _recognize_user(self, frame: np.ndarray) -> Dict[str, Any]:
        """Recognize the user in the frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        
        if len(faces) == 0:
            return {'user_present': False, 'confidence': 0.0, 'user_id': None}
        
        # For now, simple presence detection
        # In a real implementation, you would use the trained face recognizer
        face_area = max([w * h for (x, y, w, h) in faces])
        
        return {
            'user_present': True,
            'confidence': min(0.95, face_area / 10000),  # Simple confidence based on face size
            'user_id': 'primary_user',  # Placeholder
            'face_count': len(faces)
        }
    
    def _analyze_environment(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyze environmental features"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Color analysis
        dominant_colors = self._get_dominant_colors(frame)
        
        # Motion detection (simplified)
        motion_score = np.std(frame)  # Placeholder for motion detection
        
        # Scene classification (basic)
        scene_type = self._classify_scene(frame)
        
        return {
            'dominant_colors': dominant_colors,
            'motion_score': float(motion_score),
            'scene_type': scene_type,
            'timestamp': time.time()
        }
    
    def _get_dominant_colors(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Get dominant colors in the frame"""
        # Reshape frame to be a list of pixels
        data = frame.reshape((-1, 3))
        data = np.float32(data)
        
        # Apply k-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        k = 3
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert centers to integers
        centers = np.uint8(centers)
        
        # Get color percentages
        unique_labels, counts = np.unique(labels, return_counts=True)
        percentages = counts / len(labels)
        
        dominant_colors = []
        for i, (center, percentage) in enumerate(zip(centers, percentages)):
            dominant_colors.append({
                'color_bgr': center.tolist(),
                'percentage': float(percentage),
                'rank': i + 1
            })
        
        return dominant_colors
    
    def _classify_scene(self, frame: np.ndarray) -> str:
        """Basic scene classification"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Simple heuristics for scene classification
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        brightness = np.mean(gray)
        
        if edge_density > 0.1 and brightness > 100:
            return "office_workspace"
        elif edge_density < 0.05 and brightness < 80:
            return "dimly_lit_room"
        elif brightness > 180:
            return "bright_outdoor"
        else:
            return "indoor_general"
    
    def train_user_recognition(self, user_images: List[np.ndarray], user_labels: List[int]):
        """Train the face recognizer with user images"""
        if not user_images:
            self.logger.warning("No user images provided for training")
            return
        
        try:
            self.face_recognizer.train(user_images, np.array(user_labels))
            self.save_recognizer_model()
            self.logger.info(f"User recognition model trained with {len(user_images)} samples")
        except Exception as e:
            self.logger.error(f"Failed to train user recognition model: {e}")

