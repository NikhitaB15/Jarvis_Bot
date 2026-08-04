class MyFirstPlugin:
    plugin_name = "My First Plugin"
    description = "My custom JARVIS plugin"
    version = "1.0.0"
    commands = ["hello_world", "current_user"]
    
    def execute(self, command: str, *args, **kwargs):
        if command == "hello_world":
            return True, "Hello from my first plugin!"
        
        elif command == "current_user":
            import os
            user = os.getenv('USERNAME') or os.getenv('USER') or 'Unknown'
            return True, f"Current user: {user}"
        
        return False, f"Unknown command: {command}"