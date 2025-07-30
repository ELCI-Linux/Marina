#!/usr/bin/env python3
"""
STAVE Delta Specification System
Defines the ContinuumDelta format and validation logic for semantic audio transformations.
"""

import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import re

class DeltaType(Enum):
    """Core delta operation types"""
    MODULATION = "modulation"      # Basic audio parameter changes
    WARP = "warp"                  # Time/pitch warping
    INTENT = "intent"              # Semantic intention-based changes
    OVERLAY = "overlay"            # Layer additional content
    EMOTIVE = "emotive"            # Emotional tone adjustments
    PROSODY = "prosody"            # Speech pattern modifications
    ENERGY = "energy"              # Dynamic intensity changes
    MORPH = "morph"                # Transition between states
    GENERATE = "generate"          # AI-created content insertion

class CurveType(Enum):
    """Delta application curves"""
    LINEAR = "linear"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    CUSTOM = "custom"

class DeltaSource(Enum):
    """Source of delta creation"""
    USER = "user"
    AGENT = "agent"
    AI = "ai"
    INFERRED = "inferred"
    COLLABORATIVE = "collaborative"
    MARINA = "marina"

@dataclass
class DeltaTarget:
    """Target specification for delta application"""
    asset: str                     # Asset ID or hash
    region: str = "full"           # Time region (start:end or selector)
    parameter: str = "volume"      # Target parameter
    channel: Optional[str] = None  # Audio channel (L/R/M/S)
    
    def validate(self) -> bool:
        """Validate target specification"""
        if not self.asset:
            return False
        
        # Validate region format (HH:MM:SS.mmm:HH:MM:SS.mmm or "full")
        if self.region != "full":
            time_pattern = r'^\d{2}:\d{2}:\d{2}\.\d{3}:\d{2}:\d{2}:\d{2}\.\d{3}$'
            if not re.match(time_pattern, self.region):
                return False
        
        return True

@dataclass 
class DeltaOperation:
    """Core delta operation data"""
    value: Union[float, str, Dict[str, Any]]  # Operation value
    curve: CurveType = CurveType.LINEAR       # Application curve
    confidence: float = 1.0                   # Confidence level (0.0-1.0)
    source: DeltaSource = DeltaSource.USER    # Source of delta
    duration: Optional[float] = None          # Duration for time-based ops
    
    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

@dataclass
class DeltaMetadata:
    """Metadata for delta operations"""
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))
    author: str = "system"
    context: Dict[str, Any] = field(default_factory=dict)
    parent_delta: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def add_context(self, key: str, value: Any):
        """Add context information"""
        self.context[key] = value
    
    def add_tag(self, tag: str):
        """Add metadata tag"""
        if tag not in self.tags:
            self.tags.append(tag)

@dataclass
class Delta:
    """Complete delta specification"""
    delta_type: DeltaType
    target: DeltaTarget  
    operation: DeltaOperation
    metadata: DeltaMetadata = field(default_factory=DeltaMetadata)
    schema_version: str = "1.0"
    delta_id: str = field(default="")
    
    def __post_init__(self):
        if not self.delta_id:
            self.delta_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique delta ID"""
        content = f"{self.delta_type.value}_{self.target.asset}_{self.metadata.timestamp}"
        hash_obj = hashlib.md5(content.encode())
        return f"delta_{hash_obj.hexdigest()[:12]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert delta to dictionary representation"""
        return {
            "schema_version": self.schema_version,
            "delta_id": self.delta_id,
            "type": self.delta_type.value,
            "target": {
                "asset": self.target.asset,
                "region": self.target.region,
                "parameter": self.target.parameter,
                "channel": self.target.channel
            },
            "operation": {
                "value": self.operation.value,
                "curve": self.operation.curve.value,
                "confidence": self.operation.confidence,
                "source": self.operation.source.value,
                "duration": self.operation.duration
            },
            "metadata": {
                "timestamp": self.metadata.timestamp,
                "author": self.metadata.author,
                "context": self.metadata.context,
                "parent_delta": self.metadata.parent_delta,
                "tags": self.metadata.tags
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Delta':
        """Create delta from dictionary representation"""
        target = DeltaTarget(
            asset=data["target"]["asset"],
            region=data["target"].get("region", "full"),
            parameter=data["target"].get("parameter", "volume"),
            channel=data["target"].get("channel")
        )
        
        operation = DeltaOperation(
            value=data["operation"]["value"],
            curve=CurveType(data["operation"].get("curve", "linear")),
            confidence=data["operation"].get("confidence", 1.0),
            source=DeltaSource(data["operation"].get("source", "user")),
            duration=data["operation"].get("duration")
        )
        
        metadata = DeltaMetadata(
            timestamp=data["metadata"].get("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ")),
            author=data["metadata"].get("author", "system"),
            context=data["metadata"].get("context", {}),
            parent_delta=data["metadata"].get("parent_delta"),
            tags=data["metadata"].get("tags", [])
        )
        
        return cls(
            delta_type=DeltaType(data["type"]),
            target=target,
            operation=operation,
            metadata=metadata,
            schema_version=data.get("schema_version", "1.0"),
            delta_id=data.get("delta_id", "")
        )
    
    def validate(self) -> bool:
        """Validate delta specification"""
        try:
            # Validate target
            if not self.target.validate():
                return False
            
            # Validate operation confidence
            if not 0.0 <= self.operation.confidence <= 1.0:
                return False
            
            # Validate schema version
            if not self.schema_version in ["1.0"]:
                return False
            
            return True
            
        except Exception:
            return False

class DeltaValidator:
    """Delta validation utilities"""
    
    SUPPORTED_PARAMETERS = {
        "audio": ["pitch", "volume", "tempo", "eq.low", "eq.mid", "eq.high", "pan"],
        "emotive": ["intensity", "tone", "energy", "stability", "warmth"],
        "prosody": ["pace", "emphasis", "pause_duration", "intonation"],
        "spatial": ["reverb", "delay", "width", "position"]
    }
    
    @classmethod
    def validate_delta(cls, delta: Delta) -> Dict[str, Any]:
        """Comprehensive delta validation"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Basic validation
        if not delta.validate():
            result["valid"] = False
            result["errors"].append("Basic delta validation failed")
        
        # Parameter validation
        if not cls._validate_parameter(delta.target.parameter):
            result["warnings"].append(f"Unusual parameter: {delta.target.parameter}")
        
        # Value validation based on parameter type
        validation_result = cls._validate_parameter_value(
            delta.target.parameter, 
            delta.operation.value
        )
        if not validation_result["valid"]:
            result["valid"] = False
            result["errors"].extend(validation_result["errors"])
        
        return result
    
    @classmethod
    def _validate_parameter(cls, parameter: str) -> bool:
        """Check if parameter is in supported list"""
        for category, params in cls.SUPPORTED_PARAMETERS.items():
            if parameter in params:
                return True
        return False
    
    @classmethod
    def _validate_parameter_value(cls, parameter: str, value: Any) -> Dict[str, Any]:
        """Validate parameter value based on type"""
        result = {"valid": True, "errors": []}
        
        # Numeric parameters
        numeric_params = ["pitch", "volume", "tempo", "intensity"]
        if any(param in parameter for param in numeric_params):
            if not isinstance(value, (int, float)):
                result["valid"] = False
                result["errors"].append(f"Parameter {parameter} requires numeric value")
        
        # Special handling for prosody parameters (can be complex objects)
        if "prosody" in parameter:
            if isinstance(value, dict):
                # Valid prosody delta with complex structure
                pass
            elif not isinstance(value, (int, float)):
                result["valid"] = False
                result["errors"].append(f"Parameter {parameter} requires numeric value or structured object")
        
        # Bounded parameters (0.0-1.0)
        bounded_params = ["intensity", "energy", "stability", "warmth"]
        if parameter in bounded_params:
            if isinstance(value, (int, float)) and not 0.0 <= value <= 1.0:
                result["valid"] = False
                result["errors"].append(f"Parameter {parameter} must be between 0.0 and 1.0")
        
        return result

class DeltaLibrary:
    """Library of common delta operations"""
    
    @staticmethod
    def create_pitch_shift(asset_id: str, semitones: float, 
                          region: str = "full") -> Delta:
        """Create pitch shift delta"""
        return Delta(
            delta_type=DeltaType.MODULATION,
            target=DeltaTarget(asset=asset_id, region=region, parameter="pitch"),
            operation=DeltaOperation(value=semitones, source=DeltaSource.USER),
            metadata=DeltaMetadata(author="stave_library", tags=["pitch", "modulation"])
        )
    
    @staticmethod
    def create_emotional_shift(asset_id: str, emotion: str, intensity: float,
                              region: str = "full") -> Delta:
        """Create emotional tone shift delta"""
        return Delta(
            delta_type=DeltaType.EMOTIVE,
            target=DeltaTarget(asset=asset_id, region=region, parameter="emotion.tone"),
            operation=DeltaOperation(
                value={"emotion": emotion, "intensity": intensity},
                curve=CurveType.EASE_IN_OUT,
                source=DeltaSource.AI
            ),
            metadata=DeltaMetadata(
                author="stave_library", 
                tags=["emotion", "semantic"],
                context={"emotion_type": emotion}
            )
        )
    
    @staticmethod
    def create_prosody_adjustment(asset_id: str, pace_change: float,
                                 emphasis_words: List[str] = None) -> Delta:
        """Create prosody adjustment delta"""
        return Delta(
            delta_type=DeltaType.PROSODY,
            target=DeltaTarget(asset=asset_id, parameter="prosody.pace"),
            operation=DeltaOperation(
                value={
                    "pace_multiplier": pace_change,
                    "emphasis_targets": emphasis_words or []
                },
                curve=CurveType.LINEAR,
                source=DeltaSource.MARINA
            ),
            metadata=DeltaMetadata(
                author="marina_prosody",
                tags=["prosody", "speech", "marina"],
                context={"pace_change": pace_change}
            )
        )

# Schema validation patterns
DELTA_SCHEMA_V1 = {
    "type": "object",
    "required": ["schema_version", "delta_id", "type", "target", "operation", "metadata"],
    "properties": {
        "schema_version": {"type": "string", "enum": ["1.0"]},
        "delta_id": {"type": "string", "pattern": "^delta_[a-f0-9]{12}$"},
        "type": {"type": "string", "enum": [t.value for t in DeltaType]},
        "target": {
            "type": "object",
            "required": ["asset", "parameter"],
            "properties": {
                "asset": {"type": "string"},
                "region": {"type": "string"},
                "parameter": {"type": "string"},
                "channel": {"type": ["string", "null"]}
            }
        },
        "operation": {
            "type": "object", 
            "required": ["value", "confidence"],
            "properties": {
                "value": {},  # Can be any type
                "curve": {"type": "string", "enum": [c.value for c in CurveType]},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "source": {"type": "string", "enum": [s.value for s in DeltaSource]},
                "duration": {"type": ["number", "null"]}
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "timestamp": {"type": "string"},
                "author": {"type": "string"},
                "context": {"type": "object"},
                "parent_delta": {"type": ["string", "null"]},
                "tags": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
}

if __name__ == "__main__":
    # Test delta creation and validation
    print("🎵 STAVE Delta Specification Test")
    print("=" * 50)
    
    # Create test delta
    test_delta = DeltaLibrary.create_pitch_shift("test_vocal.wav", +2.5, "00:01:30.000:00:02:15.000")
    print(f"✅ Created delta: {test_delta.delta_id}")
    
    # Validate delta
    validation = DeltaValidator.validate_delta(test_delta)
    print(f"🔍 Validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
    
    if validation['errors']:
        print(f"❌ Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"⚠️  Warnings: {validation['warnings']}")
    
    # Test serialization
    delta_dict = test_delta.to_dict()
    print(f"📄 Serialized delta keys: {list(delta_dict.keys())}")
    
    # Test deserialization
    reconstructed = Delta.from_dict(delta_dict)
    print(f"🔄 Reconstructed delta ID: {reconstructed.delta_id}")
    
    print("\n🎯 Delta specification system ready!")
