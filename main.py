# Enhanced main.py - nick (Enhanced Learning Assistant) with Memory
import json
import tempfile
import speech_recognition as sr
import pyttsx3
import time
import random
import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import logging
from pathlib import Path
import numpy as np
import sys
import os

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import existing modules (with error handling)
try:
    from commands.basic_commands import handle_basic_command
except ImportError:
    def handle_basic_command(text):
        return None

try:
    from commands.groq_chat import GroqChat
except ImportError:
    class GroqChat:
        def chat(self, text):
            return "I'm nick, your personal assistant. How can I help you today?"

try:
    from models.wake_word import WakeWordDetector
except ImportError:
    class WakeWordDetector:
        def listen_for_wake_word(self):
            return ""

try:
    from emotion_analyzer import EmotionAnalyzer
except ImportError:
    class EmotionAnalyzer:
        def analyze_emotion(self, audio_data):
            return "neutral"
try:
    from Levenshtein import ratio as fuzz_ratio
except ImportError:
    def fuzz_ratio(a, b):
        """Simple fallback similarity ratio"""
        if not a or not b:
            return 0
        a, b = a.lower(), b.lower()
        if a == b:
            return 100
        return 0

def calc_fuzz_ratio(a, b):
    try:
        res = fuzz_ratio(a, b)
        if isinstance(res, float) and res <= 1.0:
            return res * 100
        return res
    except Exception:
        return 0
# Import new system utilities (with error handling)
try:
    from commands.system_commands import SystemController
    from config.config_manager import ConfigManager
    from utils.knowledge_manager import KnowledgeManager
    from config.automation_manager import AutomationManager
    from config.plugin_manager import PluginManager
    from utils.speech_utils import TTSManager
    ENHANCED_FEATURES = True
except ImportError:
    from utils.speech_utils import TTSManager
    ENHANCED_FEATURES = False
    print("Enhanced features not available, running in basic mode")

class PersonalMemory:
    """Enhanced personal memory system for nick with persistent profile tracking"""
    def __init__(self):
        self.memory_file = "data/nick_memory.json"
        self.memory = self.load_memory()
    
    def load_memory(self):
        """Load personal memory from file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "personal_info" not in data:
                        data["personal_info"] = {"name": "", "preferences": {}, "important_facts": []}
                    return data
            except Exception as e:
                print(f"Error loading memory: {e}")
        
        return {
            "personal_info": {
                "name": "Nikhita",
                "age": "24",
                "preferences": {},
                "important_facts": []
            },
            "conversations": [],
            "learned_patterns": {},
            "last_updated": str(datetime.now())
        }
    
    def save_memory(self):
        """Save memory to file"""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            self.memory["last_updated"] = str(datetime.now())
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
    def remember_name(self, name):
        """Remember user's name"""
        self.memory["personal_info"]["name"] = name
        self.save_memory()
        print(f"📝 Remembered: User's name is {name}")
    
    def get_name(self):
        """Get user's name"""
        return self.memory["personal_info"].get("name", "")
    
    def add_important_fact(self, fact):
        """Add an important fact to memory"""
        facts = self.memory["personal_info"].setdefault("important_facts", [])
        if not any(f.get("fact") == fact if isinstance(f, dict) else f == fact for f in facts):
            facts.append({
                "fact": fact,
                "timestamp": str(datetime.now())
            })
            self.save_memory()
            print(f"📝 Remembered important fact: {fact}")
    
    def get_important_facts(self):
        """Get all important facts"""
        return self.memory["personal_info"].get("important_facts", [])

    def get_summary_context(self) -> str:
        """Build a comprehensive context summary for the LLM"""
        info = self.memory.get("personal_info", {})
        summary = []
        
        name = info.get("name")
        if name:
            summary.append(f"User's Name: {name}")
        
        age = info.get("age")
        if age:
            summary.append(f"User's Age: {age}")
            
        prefs = info.get("preferences", {})
        if prefs:
            prefs_str = ", ".join([f"{k}: {v}" for k, v in prefs.items()])
            summary.append(f"Preferences: {prefs_str}")

        facts = info.get("important_facts", [])
        if facts:
            facts_list = [f.get("fact", "") if isinstance(f, dict) else str(f) for f in facts]
            summary.append("Remembered facts: " + "; ".join(facts_list))
            
        return " | ".join(summary)

    def extract_and_store_user_info(self, text: str):
        """Automatically extract user details like name, age, interests from chat text"""
        text_lower = text.lower().strip()
        
        # 1. Age extraction
        age_match = re.search(r"\b(my age is|i am|i'm|age) (\d{1,2})\b", text_lower)
        if age_match:
            age_val = age_match.group(2)
            self.memory["personal_info"]["age"] = age_val
            self.add_important_fact(f"User's age is {age_val}")

        # 2. Key interests / facts extraction
        if any(kw in text_lower for kw in ['i like to', 'i love to', 'i make', 'i sell', 'my hobby', 'instagram']):
            if not text_lower.startswith(('what', 'how', 'why', 'can you', 'do you')):
                self.add_important_fact(text.strip())

    def get_recent_conversations(self, limit: int = 10):
        """Get recent conversation pairs for LLM context restoration"""
        convs = self.memory.get("conversations", [])
        return convs[-limit:]
    
    def add_conversation(self, user_input, assistant_response):
        """Add conversation to memory"""
        self.memory.setdefault("conversations", []).append({
            "user": user_input,
            "assistant": assistant_response,
            "timestamp": str(datetime.now())
        })
        
        if len(self.memory["conversations"]) > 50:
            self.memory["conversations"] = self.memory["conversations"][-50:]
        
        self.save_memory()

class Enhancednick:
    def __init__(self):
        """Initialize Enhanced nick (Enhanced Learning Assistant)"""
        print("🔧 Initializing nick (Enhanced Learning Assistant)...")
        
        self.setup_directories()
        self.setup_logging()
        
        # Initialize personal memory
        self.memory = PersonalMemory()
        
        # Initialize existing components
        print("🎤 Setting up voice components...")
        self.tts_manager = TTSManager(voice_name="en-US-AvaNeural")
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        
         # Enhanced microphone testing
        print("🔊 Testing microphone setup...")
        if not self.debug_microphone():
            print("⚠️  Microphone issues detected. Trying alternative setup...")
            self.setup_alternative_microphone()
        
        self.groq_chat = GroqChat()
        self.groq_chat.load_history_from_memory(self.memory.get_recent_conversations())
        self.wake_detector = WakeWordDetector()
        self.emotion_analyzer = EmotionAnalyzer()
        
        # Initialize new core components if available
        if ENHANCED_FEATURES:
            print("🔧 Loading enhanced features...")
            self.config_manager = ConfigManager()
            self.system_controller = SystemController()
            self.knowledge_manager = KnowledgeManager()
            self.automation_manager = AutomationManager(self.config_manager, self.system_controller)
            self.plugin_manager = PluginManager()
            self.plugin_manager.load_plugins()
        else:
            print("📦 Running in basic mode...")
        
        # State variables
        self.is_running = False
        self.conversation_active = False
        self.conversation_context = {}
        self.last_command_time = 0
        
        # Configure voice settings for nick
        self._configure_voice()
        
        # Greet user with their name if known
        self._greet_user()
        
        print("✅ nick initialized successfully!")
        
    def _greet_user(self):
        """Greet user with their name if known"""
        user_name = self.memory.get_name()
        if user_name:
            print(f"👋 Welcome back, {user_name}!")
        else:
            print("👋 Hello! I'm nick, your personal assistant.")
        
    def debug_microphone(self) -> bool:
        """Debug and test microphone configuration"""
        try:
            mic_list = sr.Microphone.list_microphone_names()
            print(f"🎙️ Available microphones: {len(mic_list)}")
            return self.test_microphone()
        except Exception as e:
            print(f"❌ Microphone debug error: {e}")
            return False

    def test_microphone(self) -> bool:
        """Test if microphone is working"""
        try:
            with sr.Microphone() as source:
                print("🎤 Testing microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                print("✅ Microphone test passed!")
                return True
        except Exception as e:
            print(f"❌ Microphone test failed: {e}")
            print("Please check your microphone connection and permissions.")
            return False
        
    def setup_directories(self):
        """Create necessary directories"""
        directories = ['config', 'data', 'logs', 'plugins', 'backups']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/nick.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('nick')
    
    def _configure_voice(self):
        """Configure voice settings for nick (female voice if available)"""
        try:
            # Set voice rate (slightly faster for more natural conversation)
            self.engine.setProperty('rate', 190)
            # Set voice volume
            self.engine.setProperty('volume', 0.9)
            
            # Try to set a female voice
            voices = self.engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if any(keyword in voice.name.lower() for keyword in ['female', 'zira', 'hazel', 'susan']):
                        self.engine.setProperty('voice', voice.id)
                        print(f"🎵 Using voice: {voice.name}")
                        break
                else:
                    print("🎵 Using default voice")
        except Exception as e:
            print(f"Voice configuration error: {e}")
    
    def speak(self, text):
        """Enhanced speak function using Edge Neural TTS (with pyttsx3 fallback)"""
        try:
            self.tts_manager.speak(text)
        except Exception as e:
            print(f"Speech error: {e}")
    
    def simple_listen_for_wake_word(self):
        """Enhanced wake word detection for nick"""
        wake_phrases = ["hello nick", "hey nick", "nick", "wake up nick", "hi nick", "okay nick"]
        
        with sr.Microphone() as source:
            try:
                print("👂 Listening for wake word... (Say clearly: 'Hello nick' or 'Hey nick')")
                
                # Better audio adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                print("✅ Ambient noise adjusted")
                
                # Listen with better parameters
                audio = self.recognizer.listen(
                    source, 
                    timeout=3, 
                    phrase_time_limit=3
                )
                
                try:
                    # Try multiple recognition services for better accuracy
                    text = self.recognizer.recognize_google(audio).lower().strip()
                    print(f"🎯 Raw recognition: '{text}'")
                    
                    # Check if any wake phrase matches exactly or closely
                    for phrase in wake_phrases:
                        # More flexible matching
                        if (phrase in text or 
                            text.startswith(phrase) or 
                            text.endswith(phrase) or
                            calc_fuzz_ratio(phrase, text) > 70):  # Fuzzy matching if available
                            print(f"✅ Wake word detected: '{phrase}' in '{text}'")
                            return True
                    
                    print(f"❌ No wake phrase found in: '{text}'")
                    
                except sr.UnknownValueError:
                    print("❓ Couldn't understand audio - this is normal")
                except sr.RequestError as e:
                    print(f"❌ Speech recognition error: {e}")
                    
            except sr.WaitTimeoutError:
                # Timeout is normal when waiting for wake word
                pass
            except Exception as e:
                print(f"❌ Wake word detection error: {e}")
        
        return False
    def setup_alternative_microphone(self):
        """Try alternative microphone setup if primary fails"""
        try:
            # Try different microphone indices
            for i in range(3):  # Try first 3 microphones
                try:
                    with sr.Microphone(device_index=i) as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=1)
                        print(f"✅ Using microphone device {i}")
                        break
                except:
                    continue
        except Exception as e:
            print(f"❌ Alternative microphone setup failed: {e}")
    def listen(self):
        """Enhanced listen function with better error handling"""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("👂 Listening...")
            try:
                timeout = 10 if self.conversation_active else 5
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
                
                try:
                    text = self.recognizer.recognize_google(audio)
                    print(f"🎯 You said: '{text}'")
                    
                    # Try emotion analysis if available (with better error handling)
                    try:
                        audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
                        if len(audio_data) >= 16000:
                            emotion = self.emotion_analyzer.analyze_emotion(audio_data)
                        else:
                            emotion = "neutral"
                    except Exception as e:
                        print(f"Emotion analysis error: {e}")
                        emotion = "neutral"
                    
                    return {"text": text, "emotion": emotion}
                    
                except sr.UnknownValueError:
                    print("❓ Sorry, I couldn't understand that. Could you repeat?")
                    return {"text": "", "emotion": "neutral"}
                except sr.RequestError as e:
                    print(f"❌ Speech recognition service error: {e}")
                    return {"text": "", "emotion": "neutral"}
                    
            except sr.WaitTimeoutError:
                if self.conversation_active:
                    print("⏰ No speech detected. Say something or say 'stop' to end conversation.")
                return {"text": "", "emotion": "neutral"}
            except Exception as e:
                print(f"❌ Listening error: {e}")
                return {"text": "", "emotion": "neutral"}
    
    def is_stop_command(self, text):
        """Check if the user wants to stop the conversation"""
        stop_phrases = [
            'stop', 'exit', 'quit', 'goodbye', 'bye', 'end conversation', 
            'that\'s all', 'thank you', 'thanks', 'go to sleep', 'sleep now',
            'stop listening', 'end session', 'see you later', 'good night'
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in stop_phrases)

    def extract_name_from_text(self, text):
        """Extract a newly introduced user name from natural language."""
        text_lower = text.lower().strip()

        patterns = [
            r"\bmy name is\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})",
            r"\bcall me\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})",
            r"\bi'm\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})",
            r"\bname is\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})"
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)

            if match:
                name = match.group(1).strip()

                # Remove trailing conversational words
                name = re.split(
                    r"\b(?:and|but|because|so|please|now|from|to)\b",
                    name,
                    maxsplit=1
                )[0].strip()

                words = name.split()

                if 1 <= len(words) <= 3:
                    if not any(
                        word in name.lower()
                        for word in ["not", "the", "and", "but", "because"]
                    ):
                        return name.title()

        return None    

    def change_user_name(self, text):
            """
            Detect commands such as:
            - change my name to Nikhita
            - change my name from Just Developing You to Nikhita
            - call me Nikhita instead
            """

            text_lower = text.lower().strip()

            patterns = [
                # "change my name from X to Y"
                r"\bchange\s+my\s+name\s+from\s+.+?\s+to\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})",

                # "change my name to Y"
                r"\bchange\s+my\s+name\s+to\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})",

                # "change the name to Y"
                r"\bchange\s+(?:the\s+)?name\s+to\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})",

                # "call me Y instead"
                r"\bcall\s+me\s+([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})(?:\s+instead)?"
            ]

            for pattern in patterns:
                match = re.search(pattern, text_lower)

                if match:
                    name = match.group(1).strip()

                    # Remove common trailing speech-recognition words
                    name = re.split(
                        r"\b(?:please|now|instead|from|to)\b",
                        name,
                        maxsplit=1
                    )[0].strip()

                    words = name.split()

                    if 1 <= len(words) <= 3:
                        return name.title()

            return None

    def detect_important_info(self, text):
            """Detect if the user is explicitly asking to remember information"""
            text_lower = text.lower()
            explicit_phrases = [
                'remember that', 'please remember', 'note that', 'take a note',
                'don\'t forget that', 'keep in mind that', 'save this fact'
            ]
            return any(phrase in text_lower for phrase in explicit_phrases)

    def process_command(self, command_data):
        """Enhanced command processing with memory, LLM intelligence, and personality"""
        if not command_data["text"].strip():
            if self.conversation_active:
                user_name = self.memory.get_name()
                name_part = f", {user_name}" if user_name else ""
                responses = [
                    f"I'm still listening{name_part}. What would you like to know?",
                    f"I'm here{name_part}. What can I help you with?",
                    f"Still listening{name_part}. Go ahead!"
                ]
                self.speak(random.choice(responses))
            return
        
        text = command_data["text"]
        emotion = command_data["emotion"]
        text_lower = text.lower().strip()
        
        print(f"🔄 Processing: '{text}' (emotion: {emotion})")
        
        # 1. Check for stop command first
        if self.is_stop_command(text_lower):
            user_name = self.memory.get_name()
            name_part = f", {user_name}" if user_name else ""
            goodbye_messages = [
                f"Alright{name_part}, I'll go back to sleep. Say 'Hello nick' to wake me up again!",
                f"Going back to sleep mode{name_part}. Wake me up anytime!",
                f"See you later{name_part}! Just say 'Hello nick' when you need me."
            ]
            self.speak(random.choice(goodbye_messages))
            self.conversation_active = False
            return
        
        # Automatically extract & store info (age, name, preferences) from chat text
        self.memory.extract_and_store_user_info(text)
        
        # 2. Extract and remember name
        # 2. Handle explicit name changes FIRST
        new_name = self.change_user_name(text)

        if new_name:
            old_name = self.memory.get_name()

            self.memory.remember_name(new_name)

            if old_name:
                self.speak(
                    f"Of course! I've changed your name from "
                    f"{old_name} to {new_name}. I'll call you {new_name} from now on."
                )
            else:
                self.speak(
                    f"Of course! I'll call you {new_name} from now on."
                )

            return


        # 3. Extract a newly introduced name
        extracted_name = self.extract_name_from_text(text)

        if extracted_name:
            self.memory.remember_name(extracted_name)
            self.speak(
                f"Nice to meet you, {extracted_name}! I'll remember your name."
            )
            return
        
        # 3. Check if user is asking about their name
        if any(phrase in text_lower for phrase in ['my name', 'what is my name', 'do you know my name', 'who am i']):
            user_name = self.memory.get_name()
            if user_name:
                self.speak(f"Of course! Your name is {user_name}.")
            else:
                self.speak("I don't know your name yet. Could you tell me what it is?")
            return
        
        # 4. Explicit memory save
        if self.detect_important_info(text):
            self.memory.add_important_fact(text)
            self.speak("I've noted that down and saved it in my memory.")
            return
        
        # 5. Handle memory-related questions
        if any(phrase in text_lower for phrase in ['what do you remember', 'what do you know about me', 'tell me about myself', 'know about me']):
            memory_summary = self.memory.get_summary_context()
            if memory_summary:
                self.speak(f"Here is what I remember about you: {memory_summary}")
            else:
                self.speak("I don't have much information saved about you yet. Tell me more about yourself!")
            return
        
        # Emotional acknowledgment (non-blocking)
        if emotion == "sad":
            user_name = self.memory.get_name()
            name_part = f" {user_name}" if user_name else ""
            print(f"User sounds sad{name_part}")
        elif emotion == "angry":
            print("User sounds frustrated")
        
        # 6. Try system commands with strict intent matching
        if ENHANCED_FEATURES:
            try:
                system_handled, system_response = self._handle_system_commands(text)
                if system_handled:
                    self.speak(system_response)
                    self.memory.add_conversation(text, system_response)
                    return
            except Exception as e:
                print(f"System command error: {e}")
        
        # 7. Try strict basic commands
        try:
            basic_response = handle_basic_command(text_lower)
            if basic_response:
                self.speak(basic_response)
                self.memory.add_conversation(text, basic_response)
                return
        except Exception as e:
            print(f"Basic command error: {e}")
        
        # 8. Try plugin commands if available
        if ENHANCED_FEATURES:
            try:
                plugin_response = self._handle_plugin_commands(text)
                if plugin_response[0]:
                    self.speak(plugin_response[1])
                    self.memory.add_conversation(text, plugin_response[1])
                    return
            except Exception as e:
                print(f"Plugin command error: {e}")
        
        # 9. Smart AI Chat via Groq LLM
        try:
            user_name = self.memory.get_name()
            memory_summary = self.memory.get_summary_context()
            system_context = f"Current time: {datetime.now().strftime('%I:%M %p, %A, %B %d, %Y')}"
            
            ai_response = self.groq_chat.chat(
                user_input=text,
                user_name=user_name,
                memory_summary=memory_summary,
                system_context=system_context
            )
            
            self.speak(ai_response)
            self.memory.add_conversation(text, ai_response)
            
        except Exception as e:
            print(f"Chat error: {e}")
            user_name = self.memory.get_name()
            name_part = f" {user_name}" if user_name else ""
            self.speak(f"I'm having trouble processing that right now{name_part}. Could you try rephrasing?")
    
    def _handle_system_commands(self, command: str) -> Tuple[bool, str]:
        """Handle system-level commands with strict intent matching"""
        command_lower = command.lower().strip()
        user_name = self.memory.get_name()
        name_part = f" {user_name}" if user_name else ""
        
        # Strict time queries
        if re.search(r"\b(what time is it|what's the time|current time|tell me the time)\b", command_lower):
            current_time = datetime.now().strftime("%I:%M %p")
            return True, f"It's currently {current_time}{name_part}."
        
        # Strict date queries
        if re.search(r"\b(what('s| is) (today's|the) date|what date is it)\b", command_lower):
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            return True, f"Today is {current_date}{name_part}."
        
        return False, ""
    
    def _handle_plugin_commands(self, command: str) -> Tuple[bool, str]:
        """Handle plugin commands"""
        if not ENHANCED_FEATURES:
            return False, ""
        # Plugin handling would go here
        return False, ""
    
    def conversation_loop(self):
        """Continuous conversation loop"""
        self.conversation_active = True
        user_name = self.memory.get_name()
        
        if user_name:
            welcome_messages = [
                f"Great to chat with you again, {user_name}! What can I help you with?",
                f"Hello {user_name}! I'm ready for our conversation.",
                f"Hi {user_name}! What would you like to talk about today?"
            ]
        else:
            welcome_messages = [
                "Great! I'm ready for our conversation. Ask me anything, or say 'stop' when you're done.",
                "Perfect! Let's chat. What would you like to talk about?",
                "I'm all ears! What can I help you with today?"
            ]
            
        self.speak(random.choice(welcome_messages))
        
        consecutive_empty_responses = 0
        max_empty_responses = 3
        
        while self.conversation_active:
            try:
                command = self.listen()
                
                if command["text"]:
                    consecutive_empty_responses = 0
                    self.process_command(command)
                    
                    # Natural conversation flow
                    time.sleep(0.5)
                    
                    # Occasionally prompt for more input
                    if self.conversation_active and random.random() < 0.25:
                        user_name = self.memory.get_name()
                        if user_name:
                            prompts = [
                                f"Anything else I can help with, {user_name}?",
                                f"What else would you like to know, {user_name}?",
                                f"Is there anything else, {user_name}?"
                            ]
                        else:
                            prompts = [
                                "Anything else I can help with?",
                                "What else would you like to know?",
                                "Is there anything else?"
                            ]
                        time.sleep(1)
                        self.speak(random.choice(prompts))
                else:
                    consecutive_empty_responses += 1
                    if consecutive_empty_responses >= max_empty_responses:
                        user_name = self.memory.get_name()
                        name_part = f" {user_name}" if user_name else ""
                        self.speak(f"I haven't heard from you in a while{name_part}. Say something or say 'stop' to end our conversation.")
                        consecutive_empty_responses = 0
                    
            except KeyboardInterrupt:
                self.speak("Conversation interrupted. Going back to sleep mode.")
                self.conversation_active = False
                break
            except Exception as e:
                print(f"❌ Conversation loop error: {e}")
                self.speak("Sorry, I had a technical issue. I'm still listening though.")
                time.sleep(1)
    
    def main_loop(self):
        """Enhanced main loop for nick"""
        print("\n🚀 Starting nick's main loop...")
        # Start with a microphone test
        print("🔊 Running final microphone check...")
        self.debug_microphone()
    
        # Start automation if available
        if ENHANCED_FEATURES:
            try:
                self.automation_manager.start_scheduler()
                print("⚡ Automation scheduler started")
            except Exception as e:
                print(f"Automation error: {e}")

        user_name = self.memory.get_name()
        if user_name:
            self.speak(f"Hello {user_name}! I'm nick, ready to help you. Say 'Hello nick' to start a conversation.")
        else:
            self.speak("Hello! I'm nick, your personal assistant. Say 'Hello nick' to start chatting with me.")

        while True:
            try:
                # Only listen for wake word when not in conversation
                if not self.conversation_active:
                    # Use simplified wake word detection
                    if self.simple_listen_for_wake_word():
                        # Prevent rapid re-triggers
                        if time.time() - self.last_command_time > 2:
                            user_name = self.memory.get_name()
                            if user_name:
                                activation_responses = [
                                    f"Yes {user_name}, I'm here! How can I help you today?",
                                    f"Hello {user_name}! I'm ready to assist you!",
                                    f"Hi {user_name}! What can I do for you?",
                                    f"I'm listening, {user_name}! How can I help?"
                                ]
                            else:
                                activation_responses = [
                                    "Yes, I'm here! How can I help you today?",
                                    "Hello! I'm ready to assist you!",
                                    "Hi there! What can I do for you?",
                                    "I'm listening! How can I help?"
                                ]
                            
                            self.speak(random.choice(activation_responses))
                            
                            # Start continuous conversation
                            self.conversation_loop()
                            
                            self.last_command_time = time.time()
                else:
                    # This shouldn't happen, but just in case
                    time.sleep(0.1)

            except KeyboardInterrupt:
                print("\n👋 Shutting down nick...")
                user_name = self.memory.get_name()
                if user_name:
                    self.speak(f"Goodbye {user_name}! See you soon!")
                else:
                    self.speak("Goodbye! See you soon!")
                
                if ENHANCED_FEATURES:
                    try:
                        self.automation_manager.stop_scheduler()
                    except:
                        pass
                break
            except Exception as e:
                print(f"❌ Main loop error: {e}")
                self.speak("I encountered an error, but I'm still running.")
                time.sleep(2)

# Initialize global instance
nick_instance = None

if __name__ == "__main__":
    try:
        print("🔄 Starting nick...")
        nick_instance = Enhancednick()
        nick_instance.main_loop()
    except Exception as e:
        print(f"❌ Failed to initialize Enhanced nick: {e}")
        print("🔄 Starting basic nick...")
        
        # Basic fallback version
        basic_tts = TTSManager(voice_name="en-US-AvaNeural")
        recognizer = sr.Recognizer()
        memory = PersonalMemory()
        
        def speak_basic(text):
            basic_tts.speak(text)
        
        def listen_basic():
            with sr.Microphone() as source:
                print("👂 Listening...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                try:
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)
                    text = recognizer.recognize_google(audio)
                    print(f"🎯 You said: '{text}'")
                    return text
                except Exception as e:
                    print(f"Listening error: {e}")
                    return ""
        
        def basic_wake_word_listen():
            wake_phrases = ["hello nick", "hey nick", "nick", "hi nick"]
            with sr.Microphone() as source:
                try:
                    print("👂 Listening for 'Hello nick' or 'Hey nick'...")
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    audio = recognizer.listen(source, timeout=3, phrase_time_limit=4)
                    text = recognizer.recognize_google(audio).lower()
                    print(f"🎯 Heard: '{text}'")
                    return any(phrase in text for phrase in wake_phrases)
                except:
                    return False
        
        user_name = memory.get_name()
        if user_name:
            speak_basic(f"Hello {user_name}! I'm nick, ready to help. Say 'Hello nick' to chat!")
        else:
            speak_basic("Hello! I'm nick, your assistant. Say 'Hello nick' to start chatting!")
        
        conversation_active = False
        
        while True:
            try:
                if not conversation_active:
                    if basic_wake_word_listen():
                        user_name = memory.get_name()
                        if user_name:
                            speak_basic(f"Hi {user_name}! Let's chat!")
                        else:
                            speak_basic("I'm here! Let's chat!")
                        conversation_active = True
                else:
                    text = listen_basic()
                    
                    if not text.strip():
                        continue
                    
                    # Check for stop command
                    stop_phrases = ['stop', 'exit', 'quit', 'goodbye', 'bye', 'end conversation']
                    if any(phrase in text.lower() for phrase in stop_phrases):
                        user_name = memory.get_name()
                        if user_name:
                            speak_basic(f"Goodbye {user_name}! Say 'Hello nick' when you need me.")
                        else:
                            speak_basic("Goodbye! Say 'Hello nick' when you need me.")
                        conversation_active = False
                        continue
                    
                    # Name extraction
                    name_match = re.search(r"(my name is|called|call me) ([a-zA-Z]+)", text.lower())
                    if name_match:
                        name = name_match.group(2).title()
                        memory.remember_name(name)
                        speak_basic(f"Nice to meet you, {name}! I'll remember that.")
                        continue
                    
                    # Name recall
                    if any(phrase in text.lower() for phrase in ['my name', 'what is my name']):
                        user_name = memory.get_name()
                        if user_name:
                            speak_basic(f"Your name is {user_name}.")
                        else:
                            speak_basic("I don't know your name yet. Could you tell me?")
                        continue
                    
                    # Memory query
                    if any(phrase in text.lower() for phrase in ['what do you remember', 'what do you know about me']):
                        user_name = memory.get_name()
                        if user_name:
                            speak_basic(f"I remember your name is {user_name}. Tell me more about yourself so I can remember more!")
                        else:
                            speak_basic("I don't know much about you yet. Tell me your name and other important things!")
                        continue
                    
                    # Important fact detection
                    if any(word in text.lower() for word in ['remember', 'important', 'note']):
                        memory.add_important_fact(text)
                        speak_basic("I'll remember that for you.")
                        continue
                    
                    # Time/date queries
                    if 'time' in text.lower():
                        current_time = datetime.now().strftime("%I:%M %p")
                        speak_basic(f"It's {current_time}.")
                        continue
                        
                    if 'date' in text.lower():
                        current_date = datetime.now().strftime("%A, %B %d, %Y")
                        speak_basic(f"Today is {current_date}.")
                        continue
                    
                    # Default response
                    user_name = memory.get_name()
                    if user_name:
                        responses = [
                            f"I understand, {user_name}. What else can I help with?",
                            f"That's interesting, {user_name}. Tell me more.",
                            f"I'm listening, {user_name}. What else would you like to talk about?"
                        ]
                    else:
                        responses = [
                            "I understand. What else can I help with?",
                            "That's interesting. Tell me more.",
                            "I'm listening. What else would you like to talk about?"
                        ]
                    speak_basic(random.choice(responses))
                    
            except KeyboardInterrupt:
                speak_basic("Goodbye! See you soon!")
                break
            except Exception as e:
                print(f"Error: {e}")
                speak_basic("Sorry, I had trouble understanding that. Could you repeat?")
                continue