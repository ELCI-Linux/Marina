"""
Frequency Analysis Module
Perform spectral and frequency domain analysis of audio
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
from typing import Dict, Tuple
import logging

class FrequencyAnalyzer:
    """Handle complex frequency analysis tasks"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def perform_fft(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, np.ndarray]:
        """Perform Fast Fourier Transform on audio"""
        # Perform FFT
        N = len(audio_data)
        yf = fft(audio_data)
        xf = fftfreq(N, 1 / sample_rate)

        return {
            "frequency": xf,
            "amplitude": np.abs(yf)
        }

    def plot_spectrum(self, fft_data: Dict[str, np.ndarray], title: str = "Frequency Spectrum"):
        """Plot frequency spectrum using matplotlib"""
        plt.figure(figsize=(10, 6))
        plt.plot(fft_data["frequency"], fft_data["amplitude"])
        plt.title(title)
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Amplitude")
        plt.grid(True)
        plt.xlim(0, 5000)
        plt.show()

    def spectral_analysis(self, audio_data: np.ndarray, sample_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Conduct and plot spectral analysis"""
        fft_data = self.perform_fft(audio_data, sample_rate)
        self.plot_spectrum(fft_data)
        return fft_data["frequency"], fft_data["amplitude"]
