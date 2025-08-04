def handle_basic_command(command):
    """Handle basic commands"""
    if "hello" in command or "hi" in command:
        return "Hello! How can I assist you today?"
    elif "how are you" in command:
        return "I'm functioning optimally, thank you for asking."
    elif "time" in command:
        from datetime import datetime
        return f"The current time is {datetime.now().strftime('%H:%M')}"
    elif "date" in command:
        from datetime import datetime
        return f"Today's date is {datetime.now().strftime('%B %d, %Y')}"
    elif "thank you" in command:
        return "You're welcome!"
    return None