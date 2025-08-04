import librosa
import numpy as np
import soundfile as sf
import os
from tempfile import NamedTemporaryFile

class EmotionAnalyzer:
    def __init__(self):
        self.emotions = {
            "happy": {"pitch_range": (200, 400), "energy": 0.7},
            "sad": {"pitch_range": (50, 150), "energy": 0.3},
            "angry": {"pitch_range": (150, 300), "energy": 0.9},
            "neutral": {"pitch_range": (100, 200), "energy": 0.5}
        }

    def analyze_emotion(self, audio_data, sample_rate=16000):
        try:
            if len(audio_data) < 16000:  # Minimum 1 second of audio
                return "neutral"
                
            # Use in-memory processing instead of temp files
            with io.BytesIO() as wav_buffer:
                sf.write(wav_buffer, audio_data, sample_rate, format='WAV')
                wav_buffer.seek(0)
                y, sr = librosa.load(wav_buffer, sr=None)
            
            # Simplified but reliable analysis
            rms = librosa.feature.rms(y=y)[0]
            energy = np.mean(rms)
            
            if energy > 0.8:
                return "angry"
            elif energy < 0.3:
                return "sad"
            return "neutral"
            
        except Exception as e:
            print(f"Emotion fallback: {str(e)}")
            return "neutral"