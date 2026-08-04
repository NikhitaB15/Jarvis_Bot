import io
import librosa
import numpy as np
import soundfile as sf


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
            # Convert input to NumPy array
            audio_data = np.asarray(audio_data, dtype=np.float32)

            # Flatten stereo/multichannel audio if necessary
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Minimum 1 second of audio
            if len(audio_data) < sample_rate:
                return "neutral"

            # Remove DC offset
            audio_data = audio_data - np.mean(audio_data)

            # Normalize safely
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val

            # Calculate RMS energy
            rms = librosa.feature.rms(
                y=audio_data,
                frame_length=2048,
                hop_length=512
            )[0]

            energy = float(np.mean(rms))

            # Calculate pitch
            f0, voiced_flag, voiced_prob = librosa.pyin(
                audio_data,
                fmin=50,
                fmax=500,
                sr=sample_rate
            )

            # Only use reliable pitch values
            valid_pitch = f0[
                ~np.isnan(f0)
            ]

            pitch = (
                float(np.median(valid_pitch))
                if len(valid_pitch) > 0
                else 0
            )

            # Debug information
            print(
                f"Emotion analysis -> "
                f"Energy: {energy:.3f}, "
                f"Pitch: {pitch:.1f} Hz"
            )

            # Emotion classification
            if energy > 0.35:
                if pitch > 200:
                    return "angry"
                return "angry"

            elif energy < 0.12:
                return "sad"

            elif pitch > 200 and energy > 0.18:
                return "happy"

            return "neutral"

        except Exception as e:
            print(f"Emotion fallback: {str(e)}")
            return "neutral"