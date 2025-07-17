# Enhanced External Observation Engine (Exo)

## Overview
The Enhanced External Observation Engine captures and analyzes webcam input with advanced features for environmental monitoring, lighting analysis, and user recognition.

## Key Features

### 1. Periodic Environmental Snapshots
- **Interval**: Every 300 seconds (5 minutes)
- **Purpose**: Comprehensive environmental monitoring
- **Output**: Saved snapshot images with timestamp
- **Analysis**: Full lighting, face, and environmental feature analysis

### 2. Intelligent Lighting Analysis
Uses deductive reasoning to analyze lighting conditions:

#### Brightness Classification:
- **Very Dark**: < 50
- **Dark**: 50-100
- **Moderate**: 100-150
- **Bright**: 150-200
- **Very Bright**: > 200

#### Contrast Analysis:
- **Low Contrast**: Standard deviation < 20
- **High Contrast**: Standard deviation > 60

#### Lighting Uniformity:
- Analyzes lighting variance across image quarters
- Detects uniform vs. uneven lighting

#### Time-Based Deduction:
- **Golden Hour**: 6-8 AM or 6-8 PM
- **Noon Lighting**: 12-2 PM
- **Artificial Lighting**: Before 6 AM or after 8 PM

#### Lighting Type Classification:
- `artificial_indoor`: Indoor artificial lighting
- `natural_golden`: Golden hour natural light
- `natural_direct_sunlight`: Direct sunlight
- `artificial_office`: Office/workspace lighting
- `minimal_ambient`: Very low light conditions
- `natural_diffuse`: Soft natural lighting

### 3. User Recognition System
- **Face Detection**: Using OpenCV Haar Cascades
- **Recognition Model**: LBPH (Local Binary Pattern Histograms)
- **Training**: Supports custom user training with face images
- **Persistence**: Saves/loads recognition models
- **Confidence Scoring**: Based on face size and recognition quality

### 4. Environmental Analysis
- **Dominant Colors**: K-means clustering to identify main colors
- **Motion Detection**: Basic motion scoring
- **Scene Classification**: 
  - `office_workspace`
  - `dimly_lit_room`
  - `bright_outdoor`
  - `indoor_general`

## Usage

### Basic Usage
```python
from exo_engine import ExternalObservationEngine

# Create engine
engine = ExternalObservationEngine(camera_index=0)

# Add callback to handle results
def my_callback(result):
    print(f"Observation: {result.data}")

engine.add_callback(my_callback)

# Start observation
engine.start_observation()

# Stop when done
engine.stop_observation()
```

### Training User Recognition
```python
# Collect face images (numpy arrays)
user_images = [face_image1, face_image2, ...]
user_labels = [1, 1, 1, ...]  # Same label for same user

# Train the model
engine.train_user_recognition(user_images, user_labels)
```

### Running the Demo
```bash
python demo_exo_engine.py
```

## Output Structure

### Regular Frame Analysis
```python
{
    'objects': [...],  # Detected objects
    'features': {...},  # Image features
    'lighting': 'bright',  # Simple lighting condition
    'recognized_user': {
        'user_present': True,
        'confidence': 0.85,
        'user_id': 'primary_user',
        'face_count': 1
    }
}
```

### Environmental Snapshot
```python
{
    'lighting_analysis': {
        'mean_brightness': 120.5,
        'std_brightness': 45.2,
        'conditions': ['moderate', 'uniform_lighting'],
        'deduced_lighting_type': 'artificial_office'
    },
    'face_analysis': {
        'face_count': 1,
        'faces': [{'bbox': (x, y, w, h), 'area': 12000}],
        'primary_user_present': True
    },
    'environmental_features': {
        'dominant_colors': [...],
        'motion_score': 25.3,
        'scene_type': 'office_workspace'
    },
    'snapshot_file': 'snapshot_20240717_102215.jpg'
}
```

## Dependencies
- OpenCV (cv2)
- NumPy
- Python 3.7+
- Optional: pyautogui, pytesseract (for screen capture features)

## Files Structure
```
exo/
├── exo_engine.py          # Main engine implementation
├── demo_exo_engine.py     # Demo script
├── README.md              # This file
└── snapshots/             # Generated snapshot images
```

## Notes
- The engine runs continuously in a separate thread
- Snapshots are saved with timestamps
- User recognition model is automatically saved/loaded
- All analysis uses deductive reasoning for intelligent insights
- Designed for real-time environmental monitoring applications
