import requests
import os
from dotenv import load_dotenv

load_dotenv()

class GroqChat:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")
        
        self.base_url = "https://api.groq.com/openai/v1"  # Base URL for all endpoints
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat(self, user_input):
        try:
            if not user_input.strip():
                return "I didn't hear that clearly. Could you repeat?"
                
            payload = {
    "messages": [
        {
            "role": "system",
            "content": """You are Jarvis. Respond in 1 short sentence (10-15 words max). 
                        Be direct and omit disclaimers. Never reveal you're an AI."""
        },
        {"role": "user", "content": user_input}
    ],
    "model": "llama3-70b-8192",
    "max_tokens": 50,  # Reduced from 150
    "temperature": 0.5,  # Reduced from 0.7 for more focused answers
    "top_p": 0.9,
    "frequency_penalty": 0.5,  # Discourages repetitive phrases
    "presence_penalty": 0.5    # Encourages new concepts
}
            
            response = requests.post(
                f"{self.base_url}/chat/completions",  # Correct endpoint
                headers=self.headers,
                json=payload,
                timeout=10  # Increased timeout
            )
            
            # More detailed error handling
            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                raise requests.exceptions.HTTPError(
                    f"Groq API Error {response.status_code}: {error_msg}"
                )
                
            return response.json()["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            print(f"API Error: {str(e)}")
            return "I'm having trouble connecting to my AI brain right now. Maybe try again later?"
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return "Something unexpected went wrong. Let's try that again."