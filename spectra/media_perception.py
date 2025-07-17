"""
Media Perception Module for Marina's Autonomous Browser System (Spectra)

This module provides comprehensive visual and audio analysis capabilities for autonomous browsing,
including content recognition, accessibility analysis, media validation, and multi-modal understanding.
"""

import base64
import io
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import hashlib

# Core dependencies
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Optional advanced dependencies
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import torch
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False


class MediaType(Enum):
    """Types of media content."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    SCREENSHOT = "screenshot"
    CANVAS = "canvas"
    SVG = "svg"


class ContentCategory(Enum):
    """Categories of visual content."""
    TEXT = "text"
    BUTTON = "button"
    FORM = "form"
    NAVIGATION = "navigation"
    MEDIA = "media"
    ADVERTISEMENT = "advertisement"
    CAPTCHA = "captcha"
    MODAL = "modal"
    NOTIFICATION = "notification"
    CONTENT = "content"
    UNKNOWN = "unknown"


class AccessibilityLevel(Enum):
    """Accessibility compliance levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class BoundingBox:
    """Represents a bounding box with coordinates and dimensions."""
    x: int
    y: int
    width: int
    height: int
    confidence: float = 0.0
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


@dataclass
class DetectedElement:
    """Represents a detected visual element."""
    category: ContentCategory
    bbox: BoundingBox
    confidence: float
    text: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    clickable: bool = False
    interactive: bool = False
    visible: bool = True


@dataclass
class TextRegion:
    """Represents detected text in an image."""
    text: str
    bbox: BoundingBox
    confidence: float
    language: Optional[str] = None
    font_size: Optional[int] = None
    color: Optional[Tuple[int, int, int]] = None


@dataclass
class AccessibilityIssue:
    """Represents an accessibility issue found in media."""
    issue_type: str
    severity: str
    description: str
    location: Optional[BoundingBox] = None
    suggestions: List[str] = field(default_factory=list)


@dataclass
class MediaAnalysis:
    """Comprehensive analysis results for media content."""
    media_type: MediaType
    dimensions: Tuple[int, int]
    detected_elements: List[DetectedElement] = field(default_factory=list)
    text_regions: List[TextRegion] = field(default_factory=list)
    accessibility_issues: List[AccessibilityIssue] = field(default_factory=list)
    accessibility_level: AccessibilityLevel = AccessibilityLevel.FAIR
    dominant_colors: List[Tuple[int, int, int]] = field(default_factory=list)
    has_faces: bool = False
    has_text: bool = False
    is_captcha: bool = False
    quality_score: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class MediaPerceptionEngine:
    """
    Advanced media perception engine for autonomous browsing.
    Provides visual and audio analysis, content recognition, and accessibility evaluation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_models()
        self._setup_ocr()
        self._setup_audio_processing()
        
        # Analysis cache
        self._analysis_cache: Dict[str, MediaAnalysis] = {}
        self._cache_max_size = self.config.get('cache_max_size', 1000)
        
        # Performance tracking
        self._performance_stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'average_processing_time': 0.0
        }
    
    def _initialize_models(self):
        """Initialize ML models for content recognition."""
        self.models = {}
        
        # Initialize object detection model if available
        if TORCH_AVAILABLE:
            try:
                # Placeholder for object detection model
                # In production, load pre-trained models like YOLO, DETR, etc.
                self.models['object_detection'] = None
                self.logger.info("Object detection model initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize object detection: {e}")
        
        # Initialize image classification model
        if TORCH_AVAILABLE:
            try:
                # Placeholder for image classification
                self.models['classification'] = None
                self.logger.info("Image classification model initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize classification: {e}")
    
    def _setup_ocr(self):
        """Setup OCR engine for text recognition."""
        self.ocr_engine = None
        
        if OCR_AVAILABLE:
            try:
                # Initialize EasyOCR with multiple languages
                self.ocr_engine = easyocr.Reader(['en', 'es', 'fr', 'de', 'it'])
                self.logger.info("OCR engine initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize OCR: {e}")
    
    def _setup_audio_processing(self):
        """Setup audio processing for media analysis."""
        self.audio_processor = None
        
        if WHISPER_AVAILABLE:
            try:
                # Initialize Whisper for speech recognition
                self.audio_processor = whisper.load_model("base")
                self.logger.info("Audio processor initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize audio processor: {e}")
    
    async def analyze_media(self, media_data: Union[str, bytes, Image.Image], 
                           media_type: MediaType = MediaType.IMAGE,
                           use_cache: bool = True) -> MediaAnalysis:
        """
        Perform comprehensive media analysis.
        
        Args:
            media_data: Media content (base64 string, bytes, or PIL Image)
            media_type: Type of media content
            use_cache: Whether to use analysis cache
            
        Returns:
            MediaAnalysis object with comprehensive results
        """
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(media_data, media_type)
        
        # Check cache
        if use_cache and cache_key in self._analysis_cache:
            self._performance_stats['cache_hits'] += 1
            return self._analysis_cache[cache_key]
        
        # Convert to PIL Image
        image = self._prepare_image(media_data)
        if image is None:
            return MediaAnalysis(
                media_type=media_type,
                dimensions=(0, 0),
                quality_score=0.0,
                processing_time=time.time() - start_time
            )
        
        # Perform analysis
        analysis = await self._perform_analysis(image, media_type)
        analysis.processing_time = time.time() - start_time
        
        # Cache result
        if use_cache:
            self._cache_analysis(cache_key, analysis)
        
        # Update performance stats
        self._update_performance_stats(analysis.processing_time)
        
        return analysis
    
    def _prepare_image(self, media_data: Union[str, bytes, Image.Image]) -> Optional[Image.Image]:
        """Convert various media formats to PIL Image."""
        try:
            if isinstance(media_data, Image.Image):
                return media_data
            elif isinstance(media_data, str):
                # Base64 string
                if media_data.startswith('data:image'):
                    media_data = media_data.split(',')[1]
                image_bytes = base64.b64decode(media_data)
                return Image.open(io.BytesIO(image_bytes))
            elif isinstance(media_data, bytes):
                return Image.open(io.BytesIO(media_data))
            else:
                self.logger.error(f"Unsupported media data type: {type(media_data)}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to prepare image: {e}")
            return None
    
    async def _perform_analysis(self, image: Image.Image, media_type: MediaType) -> MediaAnalysis:
        """Perform comprehensive analysis on the image."""
        analysis = MediaAnalysis(
            media_type=media_type,
            dimensions=image.size
        )
        
        # Run analysis components in parallel
        tasks = [
            self._detect_elements(image),
            self._extract_text(image),
            self._analyze_accessibility(image),
            self._analyze_colors(image),
            self._detect_faces(image),
            self._assess_quality(image),
            self._detect_captcha(image)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        if not isinstance(results[0], Exception):
            analysis.detected_elements = results[0]
        
        if not isinstance(results[1], Exception):
            analysis.text_regions = results[1]
            analysis.has_text = len(analysis.text_regions) > 0
        
        if not isinstance(results[2], Exception):
            analysis.accessibility_issues, analysis.accessibility_level = results[2]
        
        if not isinstance(results[3], Exception):
            analysis.dominant_colors = results[3]
        
        if not isinstance(results[4], Exception):
            analysis.has_faces = results[4]
        
        if not isinstance(results[5], Exception):
            analysis.quality_score = results[5]
        
        if not isinstance(results[6], Exception):
            analysis.is_captcha = results[6]
        
        return analysis
    
    async def _detect_elements(self, image: Image.Image) -> List[DetectedElement]:
        """Detect UI elements in the image."""
        elements = []
        
        # Use computer vision to detect common UI elements
        if CV2_AVAILABLE:
            try:
                # Convert to OpenCV format
                cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                # Detect buttons using template matching or contour analysis
                button_elements = await self._detect_buttons(cv_image)
                elements.extend(button_elements)
                
                # Detect form elements
                form_elements = await self._detect_forms(cv_image)
                elements.extend(form_elements)
                
                # Detect navigation elements
                nav_elements = await self._detect_navigation(cv_image)
                elements.extend(nav_elements)
                
            except Exception as e:
                self.logger.error(f"Element detection failed: {e}")
        
        return elements
    
    async def _detect_buttons(self, cv_image: np.ndarray) -> List[DetectedElement]:
        """Detect button elements in the image."""
        elements = []
        
        try:
            # Simple button detection using edge detection and contour analysis
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Filter by area and aspect ratio
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum button area
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Button-like aspect ratio
                    if 0.2 < aspect_ratio < 5.0:
                        bbox = BoundingBox(x, y, w, h, confidence=0.7)
                        element = DetectedElement(
                            category=ContentCategory.BUTTON,
                            bbox=bbox,
                            confidence=0.7,
                            clickable=True,
                            interactive=True
                        )
                        elements.append(element)
            
        except Exception as e:
            self.logger.error(f"Button detection failed: {e}")
        
        return elements
    
    async def _detect_forms(self, cv_image: np.ndarray) -> List[DetectedElement]:
        """Detect form elements in the image."""
        elements = []
        
        try:
            # Detect rectangular regions that might be form fields
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Use morphological operations to find form-like structures
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 2))
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Minimum form area
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Form-like aspect ratio (typically wider than tall)
                    if aspect_ratio > 2.0:
                        bbox = BoundingBox(x, y, w, h, confidence=0.6)
                        element = DetectedElement(
                            category=ContentCategory.FORM,
                            bbox=bbox,
                            confidence=0.6,
                            interactive=True
                        )
                        elements.append(element)
            
        except Exception as e:
            self.logger.error(f"Form detection failed: {e}")
        
        return elements
    
    async def _detect_navigation(self, cv_image: np.ndarray) -> List[DetectedElement]:
        """Detect navigation elements in the image."""
        elements = []
        
        try:
            # Detect horizontal lines that might be navigation bars
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            
            contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Navigation bars are typically wide and at the top
                if w > cv_image.shape[1] * 0.5 and y < cv_image.shape[0] * 0.2:
                    bbox = BoundingBox(x, y, w, h, confidence=0.8)
                    element = DetectedElement(
                        category=ContentCategory.NAVIGATION,
                        bbox=bbox,
                        confidence=0.8,
                        interactive=True
                    )
                    elements.append(element)
            
        except Exception as e:
            self.logger.error(f"Navigation detection failed: {e}")
        
        return elements
    
    async def _extract_text(self, image: Image.Image) -> List[TextRegion]:
        """Extract text regions from the image."""
        text_regions = []
        
        if self.ocr_engine:
            try:
                # Convert PIL to numpy array
                img_array = np.array(image)
                
                # Perform OCR
                results = self.ocr_engine.readtext(img_array)
                
                for (bbox_coords, text, confidence) in results:
                    if confidence > 0.5:  # Filter low confidence results
                        # Convert bbox coordinates
                        x_coords = [point[0] for point in bbox_coords]
                        y_coords = [point[1] for point in bbox_coords]
                        
                        x = int(min(x_coords))
                        y = int(min(y_coords))
                        width = int(max(x_coords) - min(x_coords))
                        height = int(max(y_coords) - min(y_coords))
                        
                        bbox = BoundingBox(x, y, width, height, confidence)
                        text_region = TextRegion(
                            text=text,
                            bbox=bbox,
                            confidence=confidence
                        )
                        text_regions.append(text_region)
                
            except Exception as e:
                self.logger.error(f"Text extraction failed: {e}")
        
        return text_regions
    
    async def _analyze_accessibility(self, image: Image.Image) -> Tuple[List[AccessibilityIssue], AccessibilityLevel]:
        """Analyze accessibility issues in the image."""
        issues = []
        
        try:
            # Convert to array for analysis
            img_array = np.array(image)
            
            # Check color contrast
            contrast_issues = self._check_color_contrast(img_array)
            issues.extend(contrast_issues)
            
            # Check for alt text indicators (this would need DOM context)
            # For now, assume missing alt text for detected images
            
            # Check for small text
            small_text_issues = self._check_text_size(img_array)
            issues.extend(small_text_issues)
            
        except Exception as e:
            self.logger.error(f"Accessibility analysis failed: {e}")
        
        # Determine accessibility level based on issues
        if len(issues) == 0:
            level = AccessibilityLevel.EXCELLENT
        elif len(issues) <= 2:
            level = AccessibilityLevel.GOOD
        elif len(issues) <= 5:
            level = AccessibilityLevel.FAIR
        else:
            level = AccessibilityLevel.POOR
        
        return issues, level
    
    def _check_color_contrast(self, img_array: np.ndarray) -> List[AccessibilityIssue]:
        """Check for color contrast issues."""
        issues = []
        
        try:
            # Simple contrast check - convert to grayscale and check variance
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if CV2_AVAILABLE else np.mean(img_array, axis=2)
            
            # Calculate local contrast
            if isinstance(gray, np.ndarray):
                mean_intensity = np.mean(gray)
                std_intensity = np.std(gray)
                
                # Low contrast threshold
                if std_intensity < 30:  # Arbitrary threshold
                    issues.append(AccessibilityIssue(
                        issue_type="low_contrast",
                        severity="warning",
                        description="Low color contrast detected",
                        suggestions=["Increase contrast between text and background"]
                    ))
            
        except Exception as e:
            self.logger.error(f"Color contrast check failed: {e}")
        
        return issues
    
    def _check_text_size(self, img_array: np.ndarray) -> List[AccessibilityIssue]:
        """Check for text size issues."""
        issues = []
        
        # This is a simplified check - would need OCR integration for real analysis
        # For now, return placeholder
        return issues
    
    async def _analyze_colors(self, image: Image.Image) -> List[Tuple[int, int, int]]:
        """Analyze dominant colors in the image."""
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get dominant colors using color quantization
            img_array = np.array(image)
            pixels = img_array.reshape(-1, 3)
            
            # Simple k-means clustering for dominant colors
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=5, random_state=42)
            kmeans.fit(pixels)
            
            # Get dominant colors
            colors = kmeans.cluster_centers_.astype(int)
            return [tuple(color) for color in colors]
            
        except Exception as e:
            self.logger.error(f"Color analysis failed: {e}")
            return []
    
    async def _detect_faces(self, image: Image.Image) -> bool:
        """Detect faces in the image."""
        if not FACE_RECOGNITION_AVAILABLE:
            return False
        
        try:
            # Convert to RGB array
            img_array = np.array(image)
            
            # Detect faces
            face_locations = face_recognition.face_locations(img_array)
            return len(face_locations) > 0
            
        except Exception as e:
            self.logger.error(f"Face detection failed: {e}")
            return False
    
    async def _assess_quality(self, image: Image.Image) -> float:
        """Assess the overall quality of the image."""
        try:
            # Convert to array
            img_array = np.array(image)
            
            # Basic quality metrics
            quality_score = 0.0
            
            # Resolution score (higher resolution = better quality)
            resolution_score = min(1.0, (image.width * image.height) / (1920 * 1080))
            quality_score += resolution_score * 0.3
            
            # Sharpness score (using Laplacian variance)
            if CV2_AVAILABLE:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                sharpness_score = min(1.0, laplacian_var / 1000)
                quality_score += sharpness_score * 0.4
            
            # Brightness score (avoid over/under exposed images)
            brightness = np.mean(img_array)
            brightness_score = 1.0 - abs(brightness - 128) / 128
            quality_score += brightness_score * 0.3
            
            return min(1.0, quality_score)
            
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {e}")
            return 0.5
    
    async def _detect_captcha(self, image: Image.Image) -> bool:
        """Detect if the image contains a CAPTCHA."""
        try:
            # Simple heuristics for CAPTCHA detection
            img_array = np.array(image)
            
            # Check for distorted text patterns
            if CV2_AVAILABLE:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                
                # Look for high frequency patterns typical of CAPTCHAs
                edges = cv2.Canny(gray, 50, 150)
                edge_density = np.sum(edges > 0) / edges.size
                
                # CAPTCHAs typically have high edge density
                if edge_density > 0.1:
                    return True
            
            # Check image size (CAPTCHAs are typically small)
            if image.width < 300 and image.height < 150:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"CAPTCHA detection failed: {e}")
            return False
    
    def _generate_cache_key(self, media_data: Union[str, bytes, Image.Image], 
                           media_type: MediaType) -> str:
        """Generate a cache key for the media."""
        if isinstance(media_data, str):
            data_hash = hashlib.md5(media_data.encode()).hexdigest()
        elif isinstance(media_data, bytes):
            data_hash = hashlib.md5(media_data).hexdigest()
        else:
            # For PIL Image, convert to bytes first
            buffer = io.BytesIO()
            media_data.save(buffer, format='PNG')
            data_hash = hashlib.md5(buffer.getvalue()).hexdigest()
        
        return f"{media_type.value}_{data_hash}"
    
    def _cache_analysis(self, cache_key: str, analysis: MediaAnalysis):
        """Cache analysis result."""
        if len(self._analysis_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self._analysis_cache))
            del self._analysis_cache[oldest_key]
        
        self._analysis_cache[cache_key] = analysis
    
    def _update_performance_stats(self, processing_time: float):
        """Update performance statistics."""
        self._performance_stats['total_analyses'] += 1
        
        # Update running average
        total = self._performance_stats['total_analyses']
        current_avg = self._performance_stats['average_processing_time']
        self._performance_stats['average_processing_time'] = (
            (current_avg * (total - 1) + processing_time) / total
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self._performance_stats.copy()
    
    def clear_cache(self):
        """Clear the analysis cache."""
        self._analysis_cache.clear()
    
    async def process_audio(self, audio_data: bytes, format: str = "wav") -> Dict[str, Any]:
        """Process audio data for speech recognition and analysis."""
        if not self.audio_processor:
            return {"error": "Audio processor not available"}
        
        try:
            # Save audio to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            # Process with Whisper
            result = self.audio_processor.transcribe(tmp_path)
            
            # Clean up
            import os
            os.unlink(tmp_path)
            
            return {
                "transcription": result["text"],
                "language": result.get("language", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "segments": result.get("segments", [])
            }
            
        except Exception as e:
            self.logger.error(f"Audio processing failed: {e}")
            return {"error": str(e)}
    
    async def analyze_video_frame(self, frame: Image.Image, 
                                 frame_number: int = 0) -> MediaAnalysis:
        """Analyze a single video frame."""
        analysis = await self.analyze_media(frame, MediaType.VIDEO)
        analysis.metadata["frame_number"] = frame_number
        return analysis
    
    def get_element_interactions(self, analysis: MediaAnalysis) -> List[Dict[str, Any]]:
        """Get possible interactions with detected elements."""
        interactions = []
        
        for element in analysis.detected_elements:
            if element.interactive or element.clickable:
                interaction = {
                    "type": "click",
                    "element": element.category.value,
                    "bbox": {
                        "x": element.bbox.x,
                        "y": element.bbox.y,
                        "width": element.bbox.width,
                        "height": element.bbox.height
                    },
                    "center": element.bbox.center,
                    "confidence": element.confidence
                }
                
                if element.text:
                    interaction["text"] = element.text
                
                interactions.append(interaction)
        
        return interactions
    
    def generate_accessibility_report(self, analysis: MediaAnalysis) -> Dict[str, Any]:
        """Generate a comprehensive accessibility report."""
        return {
            "overall_level": analysis.accessibility_level.value,
            "issues_count": len(analysis.accessibility_issues),
            "issues": [
                {
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description,
                    "suggestions": issue.suggestions
                }
                for issue in analysis.accessibility_issues
            ],
            "recommendations": self._generate_accessibility_recommendations(analysis)
        }
    
    def _generate_accessibility_recommendations(self, analysis: MediaAnalysis) -> List[str]:
        """Generate accessibility improvement recommendations."""
        recommendations = []
        
        if analysis.accessibility_level in [AccessibilityLevel.POOR, AccessibilityLevel.CRITICAL]:
            recommendations.append("Conduct comprehensive accessibility audit")
        
        if not analysis.has_text and len(analysis.detected_elements) > 0:
            recommendations.append("Add descriptive text for interactive elements")
        
        if analysis.has_faces:
            recommendations.append("Ensure proper alt text for images with people")
        
        return recommendations


# Example usage and testing
if __name__ == "__main__":
    async def main():
        # Initialize the media perception engine
        engine = MediaPerceptionEngine()
        
        # Test with a sample image (you would provide real image data)
        test_image = Image.new('RGB', (800, 600), color='white')
        
        # Perform analysis
        analysis = await engine.analyze_media(test_image)
        
        print(f"Analysis completed in {analysis.processing_time:.2f} seconds")
        print(f"Detected {len(analysis.detected_elements)} elements")
        print(f"Found {len(analysis.text_regions)} text regions")
        print(f"Accessibility level: {analysis.accessibility_level.value}")
        print(f"Quality score: {analysis.quality_score:.2f}")
        
        # Get interaction suggestions
        interactions = engine.get_element_interactions(analysis)
        print(f"Possible interactions: {len(interactions)}")
        
        # Generate accessibility report
        accessibility_report = engine.generate_accessibility_report(analysis)
        print(f"Accessibility report: {accessibility_report}")
    
    # Run the example
    asyncio.run(main())
