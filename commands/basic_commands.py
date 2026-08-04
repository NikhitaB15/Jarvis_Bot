
from .system_commands import SystemController
from config.config_manager import ConfigManager

try:
    system_controller = SystemController()
    config_manager = ConfigManager()
except:
    system_controller = None
    config_manager = None

def handle_enhanced_basic_command(command):
    """Enhanced version of your basic command handler"""
    command_lower = command.lower()
    
    # Your existing basic commands
    basic_response = handle_basic_command(command_lower)
    if basic_response:
        return basic_response
    
    # New system commands
    if system_controller:
        if any(word in command_lower for word in ['open', 'launch', 'start']):
            app_name = command_lower.replace('open', '').replace('launch', '').replace('start', '').strip()
            if app_name:
                success, message = system_controller.open_application(app_name)
                return message if success else None
        
        elif 'system status' in command_lower:
            info = system_controller.get_system_info()
            if 'error' not in info:
                cpu = info.get('cpu', {}).get('usage', 0)
                memory = info.get('memory', {}).get('percentage', 0)
                return f"System Status: CPU {cpu}%, Memory {memory}%"
    
    return None      
def handle_basic_command(command):
    """Handle basic commands with strict phrase matching"""
    cmd = command.strip().lower()
    if cmd in ["hello", "hi", "hey", "hello nick", "hey nick"]:
        return "Hello! How can I assist you today?"
    elif cmd in ["how are you", "how are you doing"]:
        return "I'm functioning optimally, thank you for asking."
    elif cmd in ["what time is it", "what's the time", "current time"]:
        from datetime import datetime
        return f"The current time is {datetime.now().strftime('%I:%M %p')}."
    elif cmd in ["what is today's date", "what's today's date", "what is the date"]:
        from datetime import datetime
        return f"Today's date is {datetime.now().strftime('%B %d, %Y')}."
    elif cmd in ["thank you", "thanks"]:
        return "You're welcome!"
    return None    