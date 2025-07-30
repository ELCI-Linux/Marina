# STAVE Core Module

**Priority**: 1  
**Status**: Planned  
**Dependencies**: numpy, librosa, soundfile, scipy  

## Purpose
The core ContinuumDelta audio processing engine that handles:
- Loading and parsing audio files
- Applying delta transformations non-destructively
- Real-time audio processing with delta stacks
- Base audio management and caching

## Key Components

### 1. AudioAsset (`audio_asset.py`)
- Represents base audio files with metadata
- Handles lazy loading and memory management
- Provides hash-based identity for delta referencing

### 2. DeltaProcessor (`delta_processor.py`)
- Core engine for applying ContinuumDelta transformations
- Maintains transformation history and branching
- Supports real-time processing and preview

### 3. EffectsEngine (`effects_engine.py`)
- Semantic-aware audio effects (pitch, EQ, dynamics, etc.)
- Maps intention-based parameters to DSP operations
- Supports emotional/prosodic modulation

### 4. AudioRenderer (`audio_renderer.py`)
- Reconstructs final audio from base + delta stack
- Handles caching and optimization
- Supports real-time playback and export

## ContinuumDelta Integration
- Direct integration with Marina's continuity vectors
- Preserves prosodic and emotional context
- Maintains conversation-level audio coherence

## File Structure
```
core/
├── PLAN.md                 # This file
├── __init__.py            # Module exports
├── audio_asset.py         # Base audio file management
├── delta_processor.py     # Core delta application engine
├── effects_engine.py      # Semantic-aware effects
├── audio_renderer.py      # Final audio reconstruction
├── cache_manager.py       # Memory and disk caching
├── real_time_engine.py    # Live processing support
└── utils.py              # Shared utilities
```

## API Design Preview
```python
from stave.core import AudioAsset, DeltaProcessor

# Load base audio
asset = AudioAsset("vocals.wav")

# Create processor with delta stack
processor = DeltaProcessor(asset)

# Apply semantic transformations
processor.apply_delta({
    "timecode": "00:01:03.200",
    "type": "emotive",
    "delta": {"intensity": +0.3, "tone": "resignation"}
})

# Render result
output = processor.render()
```

## Development Tasks
1. [ ] Implement AudioAsset base class
2. [ ] Build DeltaProcessor core engine  
3. [ ] Create basic effects library
4. [ ] Add audio rendering pipeline
5. [ ] Integrate with Marina Continuum
6. [ ] Add caching and optimization
7. [ ] Implement real-time processing
8. [ ] Write comprehensive tests

## Performance Targets
- Load 48kHz/24-bit audio files under 100ms
- Apply simple deltas in real-time (<10ms latency)
- Support 32+ simultaneous delta layers
- Memory usage under 2GB for typical projects
