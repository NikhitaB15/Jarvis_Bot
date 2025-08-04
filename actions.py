import os
import pyautogui

def process(text):
    text = text.lower()

    if "open" in text and "chrome" in text:
        os.system("start chrome")
        return "Opening Chrome"

    elif "type" in text:
        msg = text.split("type")[-1].strip()
        pyautogui.write(msg)
        return f"Typing: {msg}"

    elif "hello" in text:
        return "Hello! How can I help you today?"

    else:
        return "Sorry, I didn't get that."