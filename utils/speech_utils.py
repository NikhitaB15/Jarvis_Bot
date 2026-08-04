import os
import time
import tempfile
import asyncio
import pyttsx3

try:
    import edge_tts
    import pygame
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

class TTSManager:
    """Advanced Text-to-Speech manager supporting Edge Neural TTS with pyttsx3 fallback"""
    def __init__(self, voice_name: str = "en-US-AvaNeural"):
        self.voice_name = voice_name
        self.pyttsx3_engine = None
        self._init_pyttsx3()
        
        if EDGE_TTS_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"Pygame mixer init warning: {e}")

    def _init_pyttsx3(self):
        try:
            self.pyttsx3_engine = pyttsx3.init()
            self.pyttsx3_engine.setProperty('rate', 180)
            self.pyttsx3_engine.setProperty('volume', 0.9)
            voices = self.pyttsx3_engine.getProperty('voices')
            if voices:
                for v in voices:
                    if any(kw in v.name.lower() for kw in ['female', 'zira', 'hazel', 'susan', 'david']):
                        self.pyttsx3_engine.setProperty('voice', v.id)
                        break
        except Exception as e:
            print(f"pyttsx3 initialization warning: {e}")

    def set_voice(self, voice_name: str):
        """Set Neural TTS voice name (e.g., 'en-US-AvaNeural', 'en-IN-NeerjaNeural')"""
        self.voice_name = voice_name

    def speak(self, text: str):
        """Speak given text using Edge Neural TTS (or pyttsx3 fallback)"""
        if not text or not text.strip():
            return
        
        try:
            print(f"💜 nick: {text}")
        except UnicodeEncodeError:
            print(f"[nick]: {text}")
        
        # Try Edge Neural TTS first if available
        if EDGE_TTS_AVAILABLE:
            try:
                success = self._speak_edge(text)
                if success:
                    return
            except Exception as e:
                print(f"Edge TTS fallback notice: {e}")

        # Fallback to local pyttsx3
        self._speak_pyttsx3(text)

    def _speak_edge(self, text: str) -> bool:
        temp_path = os.path.join(tempfile.gettempdir(), f"nick_tts_{int(time.time()*1000)}.mp3")
        try:
            async def generate():
                communicate = edge_tts.Communicate(text, self.voice_name)
                await communicate.save(temp_path)
            
            asyncio.run(generate())
            
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                pygame.mixer.music.unload()
                
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return True
        except Exception as e:
            print(f"Edge TTS error: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
        return False

    def _speak_pyttsx3(self, text: str):
        try:
            if self.pyttsx3_engine:
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
        except Exception as e:
            print(f"pyttsx3 speak error: {e}")


def configure_voice(engine, config):
    """Legacy helper function for backwards compatibility"""
    try:
        engine.setProperty('rate', config['voice']['rate'])
        engine.setProperty('volume', config['voice']['volume'])
        voices = engine.getProperty('voices')
        if len(voices) > config['voice']['voice_id']:
            engine.setProperty('voice', voices[config['voice']['voice_id']].id)
    except Exception as e:
        print(f"Error configuring voice: {e}")