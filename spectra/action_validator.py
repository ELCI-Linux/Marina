#!/usr/bin/env python3
"""
Action Validator - Validates success/failure of actions via visual and DOM changes

Detects visual or DOM changes post-interaction using perceptual hashes,
DOM state snapshots, and intelligent change detection algorithms.
"""

import asyncio
import time
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import base64
import io

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageChops, ImageDraw
    import imagehash
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from .navigation_core import NavigatorCore, PageState, NavigationAction

class ValidationResult(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

class ChangeType(Enum):
    VISUAL = "visual"
    DOM = "dom"
    URL = "url"
    NETWORK = "network"
    ELEMENT = "element"
    FORM = "form"

@dataclass
class ChangeDetection:
    """Represents a detected change"""
    change_type: ChangeType
    confidence: float
    description: str
    before_value: str = ""
    after_value: str = ""
    timestamp: float = field(default_factory=time.time)
    region: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationSnapshot:
    """Snapshot of page state for validation"""
    timestamp: float
    url: str
    title: str
    dom_hash: str
    screenshot_hash: str
    screenshot_data: bytes
    dom_content: str
    page_state: PageState
    network_requests: List[Dict[str, Any]] = field(default_factory=list)
    console_logs: List[Dict[str, Any]] = field(default_factory=list)

class ActionValidator:
    """
    Validates the success or failure of navigation actions by detecting changes
    in visual appearance, DOM structure, URL, and network activity.
    """
    
    def __init__(self, navigator: NavigatorCore):
        self.navigator = navigator
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Configuration
        self.sample_interval = 0.25  # Check every 0.25 seconds
        self.timeout = 15.0  # Maximum wait time
        self.visual_threshold = 0.85  # Similarity threshold for visual changes
        self.dom_threshold = 0.95  # Similarity threshold for DOM changes
        
        # Change detection state
        self.snapshots = []
        self.baseline_snapshot = None
        self.monitoring = False
        
        # Network monitoring
        self.network_requests = []
        self.console_logs = []
        
        # Visual change detection
        self.change_regions = []
        self.last_screenshot = None
        
    async def initialize(self):
        """Initialize the validator with network monitoring"""
        try:
            if hasattr(self.navigator, 'page') and self.navigator.page:
                # Monitor network requests
                self.navigator.page.on('request', self._on_request)
                self.navigator.page.on('response', self._on_response)
                self.navigator.page.on('requestfailed', self._on_request_failed)
                
                # Monitor console logs
                self.navigator.page.on('console', self._on_console)
                
            self.logger.info("ActionValidator initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ActionValidator: {e}")
            raise
    
    def _on_request(self, request):
        """Handle network request"""
        self.network_requests.append({
            'type': 'request',
            'url': request.url,
            'method': request.method,
            'headers': dict(request.headers),
            'timestamp': time.time()
        })
    
    def _on_response(self, response):
        """Handle network response"""
        self.network_requests.append({
            'type': 'response',
            'url': response.url,
            'status': response.status,
            'headers': dict(response.headers),
            'timestamp': time.time()
        })
    
    def _on_request_failed(self, request):
        """Handle failed network request"""
        self.network_requests.append({
            'type': 'request_failed',
            'url': request.url,
            'failure_text': request.failure,
            'timestamp': time.time()
        })
    
    def _on_console(self, msg):
        """Handle console message"""
        self.console_logs.append({
            'type': msg.type,
            'text': msg.text,
            'location': msg.location,
            'timestamp': time.time()
        })
    
    async def create_baseline_snapshot(self) -> ValidationSnapshot:
        """Create a baseline snapshot before action execution"""
        try:
            snapshot = await self._capture_snapshot()
            self.baseline_snapshot = snapshot
            
            # Clear previous monitoring data
            self.network_requests.clear()
            self.console_logs.clear()
            self.change_regions.clear()
            
            self.logger.info("Baseline snapshot created")
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Failed to create baseline snapshot: {e}")
            raise
    
    async def validate_action(self, action: NavigationAction, 
                            expected_changes: List[str] = None) -> Tuple[ValidationResult, List[ChangeDetection]]:
        """
        Validate an action by monitoring changes over time
        
        Args:
            action: The action that was executed
            expected_changes: List of expected change types
            
        Returns:
            Tuple of (result, detected_changes)
        """
        try:
            if not self.baseline_snapshot:
                self.logger.warning("No baseline snapshot available")
                return ValidationResult.UNKNOWN, []
            
            self.logger.info(f"Starting validation for action: {action.action_type.value}")
            
            # Start monitoring
            self.monitoring = True
            detected_changes = []
            
            # Monitor for changes
            start_time = time.time()
            last_check = start_time
            
            while self.monitoring and (time.time() - start_time) < self.timeout:
                await asyncio.sleep(self.sample_interval)
                
                # Capture current snapshot
                current_snapshot = await self._capture_snapshot()
                
                # Detect changes
                changes = await self._detect_changes(self.baseline_snapshot, current_snapshot)
                
                # Add new changes
                for change in changes:
                    if not self._is_duplicate_change(change, detected_changes):
                        detected_changes.append(change)
                        self.logger.info(f"Detected change: {change.change_type.value} - {change.description}")
                
                # Check if we have sufficient changes to determine success
                if self._has_sufficient_changes(detected_changes, expected_changes):
                    break
                
                last_check = time.time()
            
            # Stop monitoring
            self.monitoring = False
            
            # Determine validation result
            result = self._determine_validation_result(detected_changes, expected_changes, action)
            
            self.logger.info(f"Validation completed: {result.value} with {len(detected_changes)} changes")
            return result, detected_changes
            
        except Exception as e:
            self.logger.error(f"Action validation failed: {e}")
            return ValidationResult.FAILURE, []
    
    async def _capture_snapshot(self) -> ValidationSnapshot:
        """Capture current page state snapshot"""
        try:
            # Get current page state
            current_state = self.navigator.get_current_state()
            if not current_state:
                current_state = await self.navigator._capture_page_state(
                    await self.navigator.get_current_url()
                )
            
            # Take screenshot
            screenshot_data = await self.navigator.take_screenshot()
            screenshot_hash = hashlib.md5(screenshot_data).hexdigest()
            
            # Get DOM content
            if hasattr(self.navigator, 'page') and self.navigator.page:
                dom_content = await self.navigator.page.content()
                url = self.navigator.page.url
                title = await self.navigator.page.title()
            else:
                dom_content = ""
                url = ""
                title = ""
            
            dom_hash = hashlib.md5(dom_content.encode()).hexdigest()
            
            snapshot = ValidationSnapshot(
                timestamp=time.time(),
                url=url,
                title=title,
                dom_hash=dom_hash,
                screenshot_hash=screenshot_hash,
                screenshot_data=screenshot_data,
                dom_content=dom_content,
                page_state=current_state,
                network_requests=self.network_requests.copy(),
                console_logs=self.console_logs.copy()
            )
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Failed to capture snapshot: {e}")
            raise
    
    async def _detect_changes(self, baseline: ValidationSnapshot, 
                            current: ValidationSnapshot) -> List[ChangeDetection]:
        """Detect changes between two snapshots"""
        changes = []
        
        try:
            # URL changes
            if baseline.url != current.url:
                changes.append(ChangeDetection(
                    change_type=ChangeType.URL,
                    confidence=1.0,
                    description=f"URL changed from {baseline.url} to {current.url}",
                    before_value=baseline.url,
                    after_value=current.url
                ))
            
            # Title changes
            if baseline.title != current.title:
                changes.append(ChangeDetection(
                    change_type=ChangeType.DOM,
                    confidence=0.9,
                    description=f"Title changed from '{baseline.title}' to '{current.title}'",
                    before_value=baseline.title,
                    after_value=current.title
                ))
            
            # DOM changes
            if baseline.dom_hash != current.dom_hash:
                dom_similarity = self._calculate_dom_similarity(baseline.dom_content, current.dom_content)
                if dom_similarity < self.dom_threshold:
                    changes.append(ChangeDetection(
                        change_type=ChangeType.DOM,
                        confidence=1.0 - dom_similarity,
                        description=f"DOM structure changed (similarity: {dom_similarity:.2f})",
                        before_value=baseline.dom_hash,
                        after_value=current.dom_hash
                    ))
            
            # Visual changes
            if baseline.screenshot_hash != current.screenshot_hash:
                visual_changes = await self._detect_visual_changes(
                    baseline.screenshot_data, current.screenshot_data
                )
                changes.extend(visual_changes)
            
            # Network changes
            network_changes = self._detect_network_changes(baseline.network_requests, current.network_requests)
            changes.extend(network_changes)
            
            # Console changes
            console_changes = self._detect_console_changes(baseline.console_logs, current.console_logs)
            changes.extend(console_changes)
            
        except Exception as e:
            self.logger.error(f"Change detection failed: {e}")
            
        return changes
    
    def _calculate_dom_similarity(self, dom1: str, dom2: str) -> float:
        """Calculate similarity between two DOM contents"""
        try:
            # Simple token-based similarity
            tokens1 = set(dom1.split())
            tokens2 = set(dom2.split())
            
            if not tokens1 and not tokens2:
                return 1.0
            
            intersection = tokens1.intersection(tokens2)
            union = tokens1.union(tokens2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            self.logger.error(f"DOM similarity calculation failed: {e}")
            return 0.0
    
    async def _detect_visual_changes(self, baseline_data: bytes, 
                                   current_data: bytes) -> List[ChangeDetection]:
        """Detect visual changes between screenshots"""
        changes = []
        
        try:
            if not CV2_AVAILABLE:
                # Simple hash-based detection
                if baseline_data != current_data:
                    changes.append(ChangeDetection(
                        change_type=ChangeType.VISUAL,
                        confidence=0.8,
                        description="Visual changes detected (hash-based)",
                        before_value=hashlib.md5(baseline_data).hexdigest(),
                        after_value=hashlib.md5(current_data).hexdigest()
                    ))
                return changes
            
            # Convert to PIL Images
            baseline_img = Image.open(io.BytesIO(baseline_data))
            current_img = Image.open(io.BytesIO(current_data))
            
            # Calculate perceptual hash
            baseline_hash = imagehash.phash(baseline_img)
            current_hash = imagehash.phash(current_img)
            
            hash_diff = baseline_hash - current_hash
            
            if hash_diff > 5:  # Threshold for significant visual change
                # Find change regions
                change_regions = self._find_change_regions(baseline_img, current_img)
                
                confidence = min(1.0, hash_diff / 20.0)  # Normalize to 0-1
                
                changes.append(ChangeDetection(
                    change_type=ChangeType.VISUAL,
                    confidence=confidence,
                    description=f"Visual changes detected (hash diff: {hash_diff})",
                    before_value=str(baseline_hash),
                    after_value=str(current_hash),
                    region=change_regions[0] if change_regions else None,
                    metadata={'hash_diff': hash_diff, 'regions': change_regions}
                ))
                
        except Exception as e:
            self.logger.error(f"Visual change detection failed: {e}")
            
        return changes
    
    def _find_change_regions(self, img1: Image.Image, img2: Image.Image) -> List[Tuple[int, int, int, int]]:
        """Find regions where visual changes occurred"""
        try:
            # Ensure images are the same size
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)
            
            # Calculate difference
            diff = ImageChops.difference(img1, img2)
            
            # Convert to numpy array for processing
            diff_array = np.array(diff)
            
            # Find regions with significant differences
            gray = cv2.cvtColor(diff_array, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 10 and h > 10:  # Filter out small changes
                    regions.append((x, y, w, h))
            
            return regions
            
        except Exception as e:
            self.logger.error(f"Change region detection failed: {e}")
            return []
    
    def _detect_network_changes(self, baseline_requests: List[Dict[str, Any]], 
                              current_requests: List[Dict[str, Any]]) -> List[ChangeDetection]:
        """Detect network activity changes"""
        changes = []
        
        try:
            # Find new requests
            new_requests = current_requests[len(baseline_requests):]
            
            for request in new_requests:
                if request['type'] == 'response' and request['status'] >= 400:
                    # Error response
                    changes.append(ChangeDetection(
                        change_type=ChangeType.NETWORK,
                        confidence=0.9,
                        description=f"HTTP error {request['status']} for {request['url']}",
                        after_value=f"{request['status']} {request['url']}",
                        metadata=request
                    ))
                elif request['type'] == 'request_failed':
                    # Failed request
                    changes.append(ChangeDetection(
                        change_type=ChangeType.NETWORK,
                        confidence=0.8,
                        description=f"Request failed: {request['failure_text']}",
                        after_value=request['url'],
                        metadata=request
                    ))
                elif request['type'] == 'response' and 200 <= request['status'] < 300:
                    # Successful response
                    changes.append(ChangeDetection(
                        change_type=ChangeType.NETWORK,
                        confidence=0.7,
                        description=f"Successful request to {request['url']}",
                        after_value=f"{request['status']} {request['url']}",
                        metadata=request
                    ))
                    
        except Exception as e:
            self.logger.error(f"Network change detection failed: {e}")
            
        return changes
    
    def _detect_console_changes(self, baseline_logs: List[Dict[str, Any]], 
                              current_logs: List[Dict[str, Any]]) -> List[ChangeDetection]:
        """Detect console log changes"""
        changes = []
        
        try:
            # Find new console logs
            new_logs = current_logs[len(baseline_logs):]
            
            for log in new_logs:
                confidence = 0.6 if log['type'] == 'log' else 0.8
                
                changes.append(ChangeDetection(
                    change_type=ChangeType.DOM,
                    confidence=confidence,
                    description=f"Console {log['type']}: {log['text']}",
                    after_value=log['text'],
                    metadata=log
                ))
                
        except Exception as e:
            self.logger.error(f"Console change detection failed: {e}")
            
        return changes
    
    def _is_duplicate_change(self, change: ChangeDetection, 
                           existing_changes: List[ChangeDetection]) -> bool:
        """Check if a change is a duplicate of an existing one"""
        for existing in existing_changes:
            if (change.change_type == existing.change_type and 
                change.description == existing.description and
                change.after_value == existing.after_value):
                return True
        return False
    
    def _has_sufficient_changes(self, changes: List[ChangeDetection], 
                              expected_changes: List[str] = None) -> bool:
        """Check if we have sufficient changes to determine success"""
        if not changes:
            return False
        
        # If we have expected changes, check if we detected them
        if expected_changes:
            detected_types = {change.change_type.value for change in changes}
            return any(expected in detected_types for expected in expected_changes)
        
        # General heuristics for sufficient changes
        high_confidence_changes = [c for c in changes if c.confidence > 0.8]
        
        return (
            len(high_confidence_changes) >= 1 or
            len(changes) >= 3 or
            any(c.change_type == ChangeType.URL for c in changes)
        )
    
    def _determine_validation_result(self, changes: List[ChangeDetection], 
                                   expected_changes: List[str] = None,
                                   action: NavigationAction = None) -> ValidationResult:
        """Determine the overall validation result"""
        if not changes:
            return ValidationResult.FAILURE
        
        # Check for error indicators
        error_changes = [
            c for c in changes 
            if (c.change_type == ChangeType.NETWORK and 
                ('error' in c.description.lower() or 'failed' in c.description.lower()))
        ]
        
        if error_changes:
            return ValidationResult.FAILURE
        
        # Check for success indicators
        success_indicators = [
            c for c in changes 
            if (c.change_type == ChangeType.URL or 
                c.change_type == ChangeType.VISUAL or
                (c.change_type == ChangeType.DOM and c.confidence > 0.8))
        ]
        
        if success_indicators:
            # Check if we have expected changes
            if expected_changes:
                detected_types = {change.change_type.value for change in changes}
                if any(expected in detected_types for expected in expected_changes):
                    return ValidationResult.SUCCESS
                else:
                    return ValidationResult.PARTIAL
            else:
                return ValidationResult.SUCCESS
        
        # Partial success if we have some changes but not clear success
        if len(changes) > 1:
            return ValidationResult.PARTIAL
        
        return ValidationResult.UNKNOWN
    
    async def validate_element_interaction(self, element_selector: str, 
                                         interaction_type: str) -> ValidationResult:
        """Validate interaction with a specific element"""
        try:
            # Create baseline
            baseline = await self.create_baseline_snapshot()
            
            # Wait a moment for any immediate changes
            await asyncio.sleep(0.5)
            
            # Check if element is still present and has expected state
            if hasattr(self.navigator, 'page') and self.navigator.page:
                try:
                    element = await self.navigator.page.wait_for_selector(
                        element_selector, timeout=2000
                    )
                    
                    # Check element state based on interaction type
                    if interaction_type == 'click':
                        # For clicks, check if element is now disabled or changed
                        is_enabled = await element.is_enabled()
                        is_visible = await element.is_visible()
                        
                        if not is_enabled or not is_visible:
                            return ValidationResult.SUCCESS
                    
                    elif interaction_type == 'type':
                        # For typing, check if element has the typed value
                        value = await element.input_value()
                        if value:
                            return ValidationResult.SUCCESS
                    
                except Exception:
                    # Element might have been removed or changed
                    return ValidationResult.SUCCESS
            
            # Fall back to general validation
            result, _ = await self.validate_action(
                NavigationAction(action_type=interaction_type, target=element_selector)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Element interaction validation failed: {e}")
            return ValidationResult.FAILURE
    
    async def wait_for_page_stability(self, timeout: float = 5.0) -> bool:
        """Wait for page to become stable (no changes for a period)"""
        try:
            stable_duration = 1.0  # How long page needs to be stable
            check_interval = 0.2   # How often to check
            
            last_hash = None
            stable_start = None
            start_time = time.time()
            
            while (time.time() - start_time) < timeout:
                # Take screenshot hash
                screenshot = await self.navigator.take_screenshot()
                current_hash = hashlib.md5(screenshot).hexdigest()
                
                if current_hash == last_hash:
                    # Page is stable
                    if stable_start is None:
                        stable_start = time.time()
                    elif (time.time() - stable_start) >= stable_duration:
                        return True
                else:
                    # Page changed, reset stability timer
                    stable_start = None
                    last_hash = current_hash
                
                await asyncio.sleep(check_interval)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Page stability check failed: {e}")
            return False
    
    def get_change_summary(self, changes: List[ChangeDetection]) -> Dict[str, Any]:
        """Get a summary of detected changes"""
        summary = {
            'total_changes': len(changes),
            'change_types': {},
            'high_confidence_changes': 0,
            'visual_changes': 0,
            'dom_changes': 0,
            'network_changes': 0,
            'url_changes': 0
        }
        
        for change in changes:
            # Count by type
            change_type = change.change_type.value
            summary['change_types'][change_type] = summary['change_types'].get(change_type, 0) + 1
            
            # Count by confidence
            if change.confidence > 0.8:
                summary['high_confidence_changes'] += 1
            
            # Count specific types
            if change.change_type == ChangeType.VISUAL:
                summary['visual_changes'] += 1
            elif change.change_type == ChangeType.DOM:
                summary['dom_changes'] += 1
            elif change.change_type == ChangeType.NETWORK:
                summary['network_changes'] += 1
            elif change.change_type == ChangeType.URL:
                summary['url_changes'] += 1
        
        return summary
    
    async def cleanup(self):
        """Clean up validator resources"""
        try:
            self.monitoring = False
            self.snapshots.clear()
            self.network_requests.clear()
            self.console_logs.clear()
            self.change_regions.clear()
            
            self.logger.info("ActionValidator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"ActionValidator cleanup failed: {e}")
