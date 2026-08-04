import importlib.util
import inspect
from pathlib import Path
from typing import Dict, Any, List

class PluginManager:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.loaded_plugins = {}
        self.plugin_commands = {}
    
    def load_plugins(self):
        """Load all plugins from the plugins directory"""
        print("Loading plugins...")
        
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
                
            try:
                self._load_plugin(plugin_file)
            except Exception as e:
                print(f"Error loading plugin {plugin_file.name}: {e}")
    
    def _load_plugin(self, plugin_file: Path):
        """Load a single plugin file"""
        plugin_name = plugin_file.stem
        
        # Load the module
        spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin class
        plugin_class = None
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                hasattr(obj, 'plugin_name') and 
                hasattr(obj, 'execute')):
                plugin_class = obj
                break
        
        if plugin_class:
            # Instantiate plugin
            plugin_instance = plugin_class()
            self.loaded_plugins[plugin_name] = plugin_instance
            
            # Register commands
            if hasattr(plugin_instance, 'commands'):
                for command in plugin_instance.commands:
                    self.plugin_commands[command] = plugin_instance
            
            print(f"Loaded plugin: {plugin_instance.plugin_name}")
        else:
            print(f"No valid plugin class found in {plugin_file.name}")
    
    def execute_plugin_command(self, command: str, *args, **kwargs):
        """Execute a plugin command"""
        if command in self.plugin_commands:
            plugin = self.plugin_commands[command]
            return plugin.execute(command, *args, **kwargs)
        return False, f"Command '{command}' not found"
    
    def get_available_commands(self) -> List[str]:
        """Get list of available plugin commands"""
        return list(self.plugin_commands.keys())
    
    def get_plugin_info(self, plugin_name: str = None) -> Dict[str, Any]:
        """Get information about loaded plugins"""
        if plugin_name:
            if plugin_name in self.loaded_plugins:
                plugin = self.loaded_plugins[plugin_name]
                return {
                    'name': plugin.plugin_name,
                    'description': getattr(plugin, 'description', 'No description'),
                    'commands': getattr(plugin, 'commands', []),
                    'version': getattr(plugin, 'version', '1.0.0')
                }
            return {}
        
        # Return info for all plugins
        return {
            name: {
                'name': plugin.plugin_name,
                'description': getattr(plugin, 'description', 'No description'),
                'commands': getattr(plugin, 'commands', []),
                'version': getattr(plugin, 'version', '1.0.0')
            }
            for name, plugin in self.loaded_plugins.items()
        }
