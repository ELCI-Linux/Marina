#!/usr/bin/env python3
"""
STAVE Delta Stack Management
Handles collections of deltas with branching, merging, and conflict resolution.
"""

import json
import time
import copy
from typing import Dict, List, Optional, Any, Iterator, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from .delta_spec import Delta, DeltaType, DeltaValidator

class StackMergeStrategy(Enum):
    """Strategies for merging delta stacks"""
    APPEND = "append"              # Simply append new deltas
    OVERWRITE = "overwrite"        # Overwrite conflicting deltas
    COLLABORATIVE = "collaborative" # Merge with conflict resolution
    PRIORITY = "priority"          # Use source priority to resolve conflicts

class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    TAKE_NEWER = "take_newer"      # Use the newer delta
    TAKE_HIGHER_CONFIDENCE = "take_higher_confidence"  # Use higher confidence delta
    AVERAGE = "average"             # Average conflicting values
    USER_CHOOSE = "user_choose"     # Require user intervention

@dataclass
class DeltaConflict:
    """Represents a conflict between two deltas"""
    existing_delta: Delta
    incoming_delta: Delta
    conflict_type: str
    resolution_suggestion: Optional[str] = None
    
    def describe(self) -> str:
        """Human-readable conflict description"""
        return (f"Conflict: {self.conflict_type} between "
               f"{self.existing_delta.delta_id} and {self.incoming_delta.delta_id}")

@dataclass
class StackSnapshot:
    """Snapshot of stack state for branching/versioning"""
    snapshot_id: str
    timestamp: str
    delta_count: int
    stack_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class DeltaStack:
    """
    Manages collections of deltas with advanced operations.
    Like Git for audio transformations.
    """
    
    def __init__(self, name: str = "untitled", asset_id: str = ""):
        self.name = name
        self.asset_id = asset_id
        self.deltas: List[Delta] = []
        self.creation_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.last_modified = self.creation_time
        self.snapshots: List[StackSnapshot] = []
        self.metadata = {
            "version": "1.0",
            "author": "stave",
            "tags": []
        }
        
        # Conflict tracking
        self.conflicts: List[DeltaConflict] = []
        self.merge_strategy = StackMergeStrategy.COLLABORATIVE
        
        print(f"[DELTA_STACK] Created stack '{name}' for asset {asset_id}")
    
    def add_delta(self, delta: Delta) -> bool:
        """Add a delta to the stack with validation"""
        # Validate delta
        validation = DeltaValidator.validate_delta(delta)
        if not validation["valid"]:
            print(f"[DELTA_STACK] Invalid delta rejected: {validation['errors']}")
            return False
        
        # Check for conflicts
        conflicts = self._detect_conflicts(delta)
        if conflicts:
            self.conflicts.extend(conflicts)
            print(f"[DELTA_STACK] Added delta with {len(conflicts)} conflicts")
        
        # Add delta
        self.deltas.append(delta)
        self._update_modified_time()
        
        print(f"[DELTA_STACK] Added delta {delta.delta_id} (total: {len(self.deltas)})")
        return True
    
    def remove_delta(self, delta_id: str) -> bool:
        """Remove a delta by ID"""
        for i, delta in enumerate(self.deltas):
            if delta.delta_id == delta_id:
                removed = self.deltas.pop(i)
                self._update_modified_time()
                print(f"[DELTA_STACK] Removed delta {delta_id}")
                return True
        
        print(f"[DELTA_STACK] Delta {delta_id} not found")
        return False
    
    def get_delta(self, delta_id: str) -> Optional[Delta]:
        """Get a delta by ID"""
        for delta in self.deltas:
            if delta.delta_id == delta_id:
                return delta
        return None
    
    def get_deltas_by_type(self, delta_type: DeltaType) -> List[Delta]:
        """Get all deltas of a specific type"""
        return [d for d in self.deltas if d.delta_type == delta_type]
    
    def get_deltas_by_parameter(self, parameter: str) -> List[Delta]:
        """Get all deltas affecting a specific parameter"""
        return [d for d in self.deltas if d.target.parameter == parameter]
    
    def get_deltas_in_region(self, start_time: str, end_time: str) -> List[Delta]:
        """Get deltas that affect a specific time region"""
        # Simplified implementation - in reality would parse time regions properly
        region_deltas = []
        for delta in self.deltas:
            if delta.target.region != "full":
                # Would parse and compare time regions
                region_deltas.append(delta)
        return region_deltas
    
    def _detect_conflicts(self, new_delta: Delta) -> List[DeltaConflict]:
        """Detect conflicts with existing deltas"""
        conflicts = []
        
        for existing_delta in self.deltas:
            conflict = self._check_delta_conflict(existing_delta, new_delta)
            if conflict:
                conflicts.append(conflict)
        
        return conflicts
    
    def _check_delta_conflict(self, delta1: Delta, delta2: Delta) -> Optional[DeltaConflict]:
        """Check if two deltas conflict"""
        # Same parameter on same asset at overlapping time
        if (delta1.target.asset == delta2.target.asset and
            delta1.target.parameter == delta2.target.parameter):
            
            # Check time region overlap (simplified)
            if self._regions_overlap(delta1.target.region, delta2.target.region):
                return DeltaConflict(
                    existing_delta=delta1,
                    incoming_delta=delta2,
                    conflict_type="parameter_overlap",
                    resolution_suggestion="average_values"
                )
        
        return None
    
    def _regions_overlap(self, region1: str, region2: str) -> bool:
        """Check if two time regions overlap"""
        # Simplified - assume regions overlap if both are "full" or specific
        if region1 == "full" or region2 == "full":
            return True
        
        # Would implement proper time region overlap detection
        return False
    
    def resolve_conflicts(self, resolution: ConflictResolution = ConflictResolution.TAKE_NEWER):
        """Resolve all pending conflicts"""
        resolved_count = 0
        
        for conflict in self.conflicts:
            if self._resolve_conflict(conflict, resolution):
                resolved_count += 1
        
        # Clear resolved conflicts
        self.conflicts = [c for c in self.conflicts if not hasattr(c, '_resolved')]
        
        print(f"[DELTA_STACK] Resolved {resolved_count} conflicts")
        self._update_modified_time()
    
    def _resolve_conflict(self, conflict: DeltaConflict, resolution: ConflictResolution) -> bool:
        """Resolve a specific conflict"""
        try:
            if resolution == ConflictResolution.TAKE_NEWER:
                # Compare timestamps and keep newer
                existing_time = conflict.existing_delta.metadata.timestamp
                incoming_time = conflict.incoming_delta.metadata.timestamp
                
                if incoming_time > existing_time:
                    # Replace existing with incoming
                    self._replace_delta(conflict.existing_delta.delta_id, conflict.incoming_delta)
                # Otherwise keep existing (already in stack)
                
            elif resolution == ConflictResolution.TAKE_HIGHER_CONFIDENCE:
                existing_conf = conflict.existing_delta.operation.confidence
                incoming_conf = conflict.incoming_delta.operation.confidence
                
                if incoming_conf > existing_conf:
                    self._replace_delta(conflict.existing_delta.delta_id, conflict.incoming_delta)
                    
            elif resolution == ConflictResolution.AVERAGE:
                # Create averaged delta (simplified)
                averaged_delta = self._average_deltas(conflict.existing_delta, conflict.incoming_delta)
                if averaged_delta:
                    self._replace_delta(conflict.existing_delta.delta_id, averaged_delta)
            
            # Mark as resolved
            setattr(conflict, '_resolved', True)
            return True
            
        except Exception as e:
            print(f"[DELTA_STACK] Error resolving conflict: {e}")
            return False
    
    def _replace_delta(self, old_delta_id: str, new_delta: Delta):
        """Replace a delta in the stack"""
        for i, delta in enumerate(self.deltas):
            if delta.delta_id == old_delta_id:
                self.deltas[i] = new_delta
                break
    
    def _average_deltas(self, delta1: Delta, delta2: Delta) -> Optional[Delta]:
        """Create an averaged delta from two conflicting deltas"""
        # Simplified implementation - would need complex logic for different value types
        if (isinstance(delta1.operation.value, (int, float)) and 
            isinstance(delta2.operation.value, (int, float))):
            
            averaged_delta = copy.deepcopy(delta1)
            averaged_delta.operation.value = (delta1.operation.value + delta2.operation.value) / 2
            averaged_delta.operation.confidence = min(delta1.operation.confidence, delta2.operation.confidence)
            averaged_delta.metadata.author = "conflict_resolution"
            averaged_delta.metadata.add_tag("averaged")
            
            # Generate new ID
            averaged_delta.delta_id = ""
            averaged_delta._generate_id()
            
            return averaged_delta
        
        return None
    
    def create_snapshot(self, name: str = "", metadata: Dict[str, Any] = None) -> str:
        """Create a snapshot of current stack state"""
        snapshot_id = f"snapshot_{int(time.time())}_{len(self.snapshots)}"
        stack_hash = self._compute_stack_hash()
        
        snapshot = StackSnapshot(
            snapshot_id=snapshot_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            delta_count=len(self.deltas),
            stack_hash=stack_hash,
            metadata=metadata or {}
        )
        
        if name:
            snapshot.metadata["name"] = name
        
        self.snapshots.append(snapshot)
        print(f"[DELTA_STACK] Created snapshot {snapshot_id}")
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore stack to a previous snapshot"""
        # This would require storing delta states with snapshots
        # Simplified implementation
        print(f"[DELTA_STACK] Snapshot restoration not fully implemented")
        return False
    
    def _compute_stack_hash(self) -> str:
        """Compute hash of current stack state"""
        content = ""
        for delta in sorted(self.deltas, key=lambda d: d.delta_id):
            content += f"{delta.delta_id}_{delta.metadata.timestamp}"
        
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def merge_stack(self, other_stack: 'DeltaStack', 
                   strategy: StackMergeStrategy = StackMergeStrategy.COLLABORATIVE) -> bool:
        """Merge another stack into this one"""
        print(f"[DELTA_STACK] Merging stack '{other_stack.name}' with strategy {strategy.value}")
        
        conflicts_before = len(self.conflicts)
        
        if strategy == StackMergeStrategy.APPEND:
            # Simply append all deltas
            for delta in other_stack.deltas:
                self.add_delta(delta)
                
        elif strategy == StackMergeStrategy.COLLABORATIVE:
            # Add with conflict detection
            for delta in other_stack.deltas:
                self.add_delta(delta)
            
            # Auto-resolve simple conflicts
            if len(self.conflicts) > conflicts_before:
                self.resolve_conflicts(ConflictResolution.TAKE_HIGHER_CONFIDENCE)
        
        self._update_modified_time()
        return True
    
    def fork_stack(self, name: str = "") -> 'DeltaStack':
        """Create a fork (copy) of this stack"""
        fork_name = name or f"{self.name}_fork_{int(time.time())}"
        forked_stack = DeltaStack(fork_name, self.asset_id)
        
        # Deep copy all deltas
        forked_stack.deltas = [copy.deepcopy(delta) for delta in self.deltas]
        forked_stack.metadata = copy.deepcopy(self.metadata)
        forked_stack.metadata["forked_from"] = self.name
        
        print(f"[DELTA_STACK] Forked stack as '{fork_name}'")
        return forked_stack
    
    def optimize_stack(self) -> int:
        """Optimize stack by removing redundant deltas"""
        original_count = len(self.deltas)
        
        # Remove duplicate deltas
        seen_ids = set()
        optimized_deltas = []
        
        for delta in self.deltas:
            if delta.delta_id not in seen_ids:
                optimized_deltas.append(delta)
                seen_ids.add(delta.delta_id)
        
        # Could add more optimization logic:
        # - Combine sequential deltas on same parameter
        # - Remove deltas with very low confidence
        # - Merge overlapping time regions
        
        self.deltas = optimized_deltas
        removed_count = original_count - len(self.deltas)
        
        if removed_count > 0:
            print(f"[DELTA_STACK] Optimized stack: removed {removed_count} redundant deltas")
            self._update_modified_time()
        
        return removed_count
    
    def get_stack_stats(self) -> Dict[str, Any]:
        """Get statistics about the stack"""
        if not self.deltas:
            return {"total_deltas": 0, "types": {}, "parameters": {}}
        
        type_counts = {}
        param_counts = {}
        confidence_sum = 0
        
        for delta in self.deltas:
            # Count by type
            type_name = delta.delta_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
            # Count by parameter
            param_counts[delta.target.parameter] = param_counts.get(delta.target.parameter, 0) + 1
            
            # Sum confidence
            confidence_sum += delta.operation.confidence
        
        return {
            "total_deltas": len(self.deltas),
            "types": type_counts,
            "parameters": param_counts,
            "average_confidence": confidence_sum / len(self.deltas),
            "conflicts": len(self.conflicts),
            "snapshots": len(self.snapshots),
            "last_modified": self.last_modified
        }
    
    def _update_modified_time(self):
        """Update last modified timestamp"""
        self.last_modified = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize stack to dictionary"""
        return {
            "name": self.name,
            "asset_id": self.asset_id,
            "creation_time": self.creation_time,
            "last_modified": self.last_modified,
            "metadata": self.metadata,
            "deltas": [delta.to_dict() for delta in self.deltas],
            "conflicts": len(self.conflicts),
            "snapshots": len(self.snapshots)
        }
    
    def save_to_file(self, filepath: str):
        """Save stack to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"[DELTA_STACK] Saved stack to {filepath}")
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'DeltaStack':
        """Load stack from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        stack = cls(data["name"], data["asset_id"])
        stack.creation_time = data["creation_time"]
        stack.last_modified = data["last_modified"] 
        stack.metadata = data["metadata"]
        
        # Load deltas
        for delta_data in data["deltas"]:
            delta = Delta.from_dict(delta_data)
            stack.deltas.append(delta)
        
        print(f"[DELTA_STACK] Loaded stack '{stack.name}' with {len(stack.deltas)} deltas")
        return stack
    
    def __len__(self) -> int:
        return len(self.deltas)
    
    def __iter__(self) -> Iterator[Delta]:
        return iter(self.deltas)
    
    def __getitem__(self, index: int) -> Delta:
        return self.deltas[index]

if __name__ == "__main__":
    # Test delta stack functionality
    print("🎵 STAVE Delta Stack Test")
    print("=" * 50)
    
    from .delta_spec import DeltaLibrary
    
    # Create test stack
    stack = DeltaStack("test_stack", "vocal_001.wav")
    
    # Add some deltas
    delta1 = DeltaLibrary.create_pitch_shift("vocal_001.wav", +2.0)
    delta2 = DeltaLibrary.create_emotional_shift("vocal_001.wav", "excitement", 0.7)
    delta3 = DeltaLibrary.create_prosody_adjustment("vocal_001.wav", 1.2, ["amazing", "brilliant"])
    
    stack.add_delta(delta1)
    stack.add_delta(delta2)
    stack.add_delta(delta3)
    
    # Get stats
    stats = stack.get_stack_stats()
    print(f"📊 Stack stats: {stats}")
    
    # Create snapshot
    snapshot_id = stack.create_snapshot("before_optimization")
    print(f"📸 Created snapshot: {snapshot_id}")
    
    # Test optimization
    removed = stack.optimize_stack()
    print(f"🔧 Optimization removed {removed} deltas")
    
    # Test forking
    forked = stack.fork_stack("experimental_fork")
    print(f"🍴 Forked stack: {forked.name}")
    
    print("\n🎯 Delta stack system ready!")
