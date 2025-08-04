import os
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json 
class WakeWordDetector:
    def __init__(self):
        model_path = "models/wake_word/vosk-model-small-en-us-0.15"
        if not os.path.exists(model_path):
            raise Exception(f"Model not found at {model_path}")
        
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.audio_queue = queue.Queue()
        self.sample_rate = 16000

    def callback(self, indata, frames, time, status):
        self.audio_queue.put(bytes(indata))

    def listen_for_wake_word(self, wake_phrase="hello"):
        with sd.RawInputStream(samplerate=self.sample_rate, blocksize=8000,
                            dtype='int16', channels=1, callback=self.callback):
            print(f"Waiting for wake phrase: '{wake_phrase}'...")
            while True:
                data = self.audio_queue.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower().strip()
                    
                    # Strict matching with confidence threshold
                    if (wake_phrase in text and 
                        len(text.split()) <= 3 and  # Prevent long phrases
                        text.count(wake_phrase) == 1):  # No duplicates
                        print(f"Wake phrase detected: '{text}'")
                        return True