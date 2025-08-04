import json
import tempfile
import speech_recognition as sr
import pyttsx3
import time 
from commands.basic_commands import handle_basic_command
from commands.groq_chat import GroqChat
from models.wake_word import WakeWordDetector
from emotion_analyzer import EmotionAnalyzer
import numpy as np

# Initialize components
engine = pyttsx3.init()
recognizer = sr.Recognizer()
groq_chat = GroqChat()
wake_detector = WakeWordDetector()
emotion_analyzer = EmotionAnalyzer()

def speak(text):
    print(f"JARVIS: {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
            
            # Validate audio length
            if len(audio_data) < 16000:  # At least 1 second of audio
                return {"text": "", "emotion": "neutral"}
                
            return {
                "text": recognizer.recognize_google(audio),
                "emotion": emotion_analyzer.analyze_emotion(audio_data)
            }
        except Exception as e:
            print(f"Listening error: {str(e)}")
            return {"text": "", "emotion": "neutral"}

def process_command(command_data):
    if not command_data["text"].strip():
        speak("I didn't catch that. Could you repeat?")
        return
        
    # Emotional response
    if command_data["emotion"] == "sad":
        speak("You sound upset. How can I help?")
    elif command_data["emotion"] == "angry":
        speak("I sense frustration. Let me assist calmly.")
    
    # Process command
    basic_response = handle_basic_command(command_data["text"])
    if basic_response:
        speak(basic_response)
    else:
        speak(groq_chat.chat(command_data["text"]))
def process_command(command_data):
    if not command_data["text"]:
        return
    
    # Emotional response
    if command_data["emotion"] == "sad":
        speak("I notice you sound down. How can I help?")
    elif command_data["emotion"] == "angry":
        speak("I sense frustration. Let's resolve this calmly.")
    
    # Command processing
    text = command_data["text"].lower()
    basic_response = handle_basic_command(text)
    if basic_response:
        speak(basic_response)
    else:
        try:
            groq_response = groq_chat.chat(text)
            speak(groq_response)
        except Exception as e:
            speak("Sorry, I encountered an error processing your request.")
def main_loop():
    wake_phrases = ["hello bro", "hey jarvis", "wake up"]  # Multiple options
    last_command_time = 0
    
    while True:
        try:
            current_phrase = wake_detector.listen_for_wake_word()
            if current_phrase.lower() in wake_phrases:
                if time.time() - last_command_time > 5:  # Prevent rapid re-triggers
                    speak(random.choice(["Yes?", "How can I help?", "Listening"]))
                    command = listen()
                    process_command(command)
                    last_command_time = time.time()
                    
        except KeyboardInterrupt:
            speak("Going to sleep. Goodbye!")
            break
        except Exception as e:
            print(f"Main loop error: {e}")
            time.sleep(1)  # Prevent tight error loops
if __name__ == "__main__":
    speak("Initializing Jarvis. Say 'Hello Bro' to activate.")
    while True:
        if wake_detector.listen_for_wake_word():
            speak("How can I help?")
            command = listen()
            process_command(command)