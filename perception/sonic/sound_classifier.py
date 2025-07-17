"""
Sound Classification Module
Detect and classify different sound types using ML models
"""

import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from typing import List, Tuple
import librosa
import pickle
import logging

class SoundClassifier:
    """Sound classification engine using pre-trained SVM models"""

    def __init__(self):
        # Setup logging first
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Load pre-trained model and scaler
        self.model = self._load_model("sound_classifier_model.pkl")
        self.scaler = StandardScaler()  # Assume scaler used during training (dummy example)
        
        # Fallback to basic rule-based classification if model not available
        self.use_fallback = self.model is None

    def _load_model(self, model_path: str):
        """Load SVM model from file"""
        try:
            with open(model_path, 'rb') as model_file:
                return pickle.load(model_file)
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return None

    def extract_features(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Extract features suitable for classification"""
        # Extract MFCC features
        mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
        features = np.mean(mfccs, axis=1)

        # Normalize features using the same scaler used during training
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        return features_scaled

    def _fallback_classify(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """Basic rule-based classification when model is not available"""
        try:
            # Calculate basic audio features
            rms = np.sqrt(np.mean(audio_data**2))
            zero_crossing_rate = np.sum(np.abs(np.diff(np.sign(audio_data)))) / (2 * len(audio_data))
            
            # Simple classification based on amplitude and zero crossing rate
            if rms < 0.01:  # Very quiet
                return "silence"
            elif rms > 0.5:  # Very loud
                return "loud_sound"
            elif zero_crossing_rate > 0.1:  # High frequency content
                return "speech_or_music"
            else:
                return "ambient"
        except Exception as e:
            self.logger.error(f"Fallback classification failed: {e}")
            return "unknown"
    
    def classify(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """Classify sound type based on features"""
        if self.use_fallback:
            return self._fallback_classify(audio_data, sample_rate)
            
        try:
            # Extract features
            features = self.extract_features(audio_data, sample_rate)

            if self.model is not None:
                # Predict sound type
                sound_type = self.model.predict(features)
                return sound_type[0]
            else:
                return self._fallback_classify(audio_data, sample_rate)
        except Exception as e:
            self.logger.error(f"Classification failed: {e}")
            return self._fallback_classify(audio_data, sample_rate)

    def classify_batch(self, audio_segments: List[Tuple[np.ndarray, int]]) -> List[str]:
        """Classify a batch of audio segments"""
        return [self.classify(data, sr) for data, sr in audio_segments]
