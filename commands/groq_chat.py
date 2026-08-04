import requests
import os
from dotenv import load_dotenv

load_dotenv()

class GroqChat:
    def __init__(self, assistant_name: str = "nick"):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.assistant_name = assistant_name
        self.models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ]
        self.history = []  # Rolling conversation history
        self.max_history_turns = 10

    def load_history_from_memory(self, conversations: list):
        """Restore conversation history from persistent storage"""
        self.history.clear()
        for turn in conversations[-5:]:
            if isinstance(turn, dict) and "user" in turn and "assistant" in turn:
                self.history.append({"role": "user", "content": turn["user"]})
                self.history.append({"role": "assistant", "content": turn["assistant"]})

    def get_system_prompt(self, user_name: str = "", memory_summary: str = "", system_context: str = "") -> str:
        prompt = f"You are {self.assistant_name}, a smart, helpful, articulate, and friendly personal AI assistant.\n"
        prompt += "Rules:\n"
        prompt += "1. Give clear, sensible, and accurate responses suitable for a voice assistant.\n"
        prompt += "2. Keep answers concise (1-3 sentences) for simple questions, but provide thorough explanations when asked for details.\n"
        prompt += "3. Be polite, natural, and conversational.\n"
        
        if memory_summary:
            prompt += f"4. User Memory Context: {memory_summary}\n"
        elif user_name:
            prompt += f"4. The user's name is {user_name}.\n"

        if system_context:
            prompt += f"5. Additional context: {system_context}\n"
            
        return prompt

    def chat(self, user_input: str, user_name: str = "", memory_summary: str = "", system_context: str = "") -> str:
        if not user_input or not user_input.strip():
            return "I didn't hear that clearly. Could you repeat?"

        system_prompt = self.get_system_prompt(user_name, memory_summary, system_context)
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.history[-self.max_history_turns:])
        messages.append({"role": "user", "content": user_input})

        # Try models in order of priority
        for model_to_use in self.models:
            payload = {
                "messages": messages,
                "model": model_to_use,
                "max_tokens": 300,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=12
                )
                
                if response.status_code == 200:
                    answer = response.json()["choices"][0]["message"]["content"].strip()
                    # Append to rolling history
                    self.history.append({"role": "user", "content": user_input})
                    self.history.append({"role": "assistant", "content": answer})
                    return answer
                else:
                    error_json = response.json().get("error", {})
                    error_msg = error_json.get("message", "Unknown error")
                    print(f"Groq API Notice ({model_to_use}): {response.status_code} - {error_msg}")
                    if response.status_code in [400, 404]:
                        continue
                    else:
                        break
            except requests.exceptions.RequestException as e:
                print(f"Connection error with model {model_to_use}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error with model {model_to_use}: {e}")
                break

        return "I'm having trouble connecting to my AI network right now. Please try again in a moment."

    def clear_history(self):
        """Reset conversation history"""
        self.history.clear()