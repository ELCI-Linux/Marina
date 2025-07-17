# Speech Detection and Translation Features

This document describes the new speech detection and translation capabilities added to the Marina Audio Analysis widget.

## Overview

The enhanced song display widget now includes three modes:
1. **🎵 Song Recognition** - Identifies songs using Shazam-like technology
2. **🌊 Soundscape Analysis** - Analyzes environmental sounds
3. **👂 Speech Detection** - Detects speech, identifies languages, and provides live translation

## Features

### Speech Detection
- **Real-time speech vs music classification** using advanced audio analysis
- **Acoustic feature extraction** including spectral, rhythm, and harmonic features
- **Vocal characteristics analysis** with formant detection and pitch analysis
- **Confidence scoring** for reliable detection

### Language Detection
- **Multi-language support** with 70+ languages and flag emojis
- **Whisper-based detection** using OpenAI's Whisper or faster-whisper
- **Fallback heuristic detection** when Whisper models are unavailable
- **Visual language indicators** with country flags

### Live Translation
- **Real-time translation** using 5-second audio clips
- **Google Translate integration** for high-quality translations
- **Translation history** with timestamps and confidence scores
- **Clickable ear button** (👂) to activate/deactivate translation

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements_speech.txt
```

2. For optimal performance, install CUDA-enabled PyTorch (optional):
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Usage

### Navigation
- Use the **◀** and **▶** buttons to navigate between modes
- The center indicator shows the current mode

### Speech Detection Mode
1. Navigate to the **👂 Speech Detection** mode
2. The widget will automatically start monitoring audio
3. When speech is detected, it will show:
   - Language flag and name
   - Confidence percentage
   - "Click the ear to start translation" prompt

### Live Translation
1. In speech detection mode, click the **👂** button
2. The button changes to **👂🔴** indicating active translation
3. Speak into the microphone in any supported language
4. View real-time translations in the display
5. Click the button again to stop translation

## Supported Languages

The system supports 70+ languages including:
- 🇺🇸 English
- 🇪🇸 Spanish
- 🇫🇷 French
- 🇩🇪 German
- 🇮🇹 Italian
- 🇵🇹 Portuguese
- 🇷🇺 Russian
- 🇨🇳 Chinese
- 🇯🇵 Japanese
- 🇰🇷 Korean
- 🇸🇦 Arabic
- 🇮🇳 Hindi
- And many more...

## Technical Details

### Audio Processing
- **Sample Rate**: 16kHz (optimized for speech recognition)
- **Chunk Size**: 1024 samples
- **Buffer Duration**: 5 seconds for translation
- **Audio Format**: 16-bit PCM

### Models Used
- **Speech Recognition**: Whisper (base model by default)
- **Translation**: Google Translate API
- **Speech Detection**: Custom ML pipeline with scikit-learn

### Performance
- **Language Detection**: ~1-2 seconds
- **Translation**: ~2-3 seconds per 5-second clip
- **Speech Detection**: Real-time (<100ms)

## Configuration

### Model Selection
You can configure the Whisper model size in the language detector:
```python
language_detector = LanguageDetector(model_size="small")  # tiny, base, small, medium, large
```

### Translation Languages
Set target translation language:
```python
live_translator = LiveTranslator(target_language='es')  # Spanish
```

### Confidence Thresholds
Adjust detection sensitivity:
```python
speech_detector.speech_confidence_threshold = 0.7  # Default: 0.6
```

## Troubleshooting

### Common Issues

1. **PyAudio Installation Issues**
   - On Ubuntu/Debian: `sudo apt-get install portaudio19-dev`
   - On macOS: `brew install portaudio`
   - On Windows: PyAudio should install automatically

2. **Whisper Model Download**
   - Models are downloaded automatically on first use
   - Check internet connection if download fails
   - Models are cached in `~/.cache/whisper/`

3. **Translation Errors**
   - Ensure internet connection for Google Translate
   - Check if googletrans version is compatible
   - Fallback to local translation if available

4. **Audio Device Issues**
   - Check microphone permissions
   - Verify audio device is not in use by other applications
   - Try different sample rates if issues persist

### Debug Mode
Enable debug logging for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Reference

### SpeechDetector
```python
detector = SpeechDetector()
result = detector.detect_speech(audio_data, sample_rate)
# Returns: {'is_speech': bool, 'confidence': float, ...}
```

### LanguageDetector
```python
detector = LanguageDetector()
result = detector.detect_language(audio_data, sample_rate)
# Returns: {'language_code': str, 'flag': str, 'confidence': float, ...}
```

### LiveTranslator
```python
translator = LiveTranslator(target_language='en')
translator.add_translation_callback(callback_function)
translator.start_translation()
translator.add_audio_clip(audio_data, sample_rate)
```

## Future Enhancements

- **Offline Translation**: Local translation models
- **Speaker Recognition**: Identify different speakers
- **Emotion Detection**: Analyze emotional content in speech
- **Conversation History**: Save and export translation sessions
- **Custom Models**: Support for domain-specific language models

## Contributing

To contribute to the speech features:
1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Submit a pull request

## License

This feature is part of the Marina project and follows the same licensing terms.
