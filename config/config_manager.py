# config/config_manager.py
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.settings = {}
        self.config_files = {
            'main': 'main_config.json',
            'app_paths': 'app_paths.json',
            'voice': 'voice_config.json',
            'automation': 'automation_rules.json',
            'knowledge_base': 'knowledge_base.json'
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load all configuration files"""
        settings = {}
        
        for key, filename in self.config_files.items():
            file_path = self.config_dir / filename
            try:
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        settings[key] = json.load(f)
                else:
                    settings[key] = self._get_default_config(key)
                    self.save_config(key, settings[key])
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                settings[key] = self._get_default_config(key)
        
        return settings
    
    def _get_default_config(self, config_type: str) -> Dict[str, Any]:
        """Get default configuration for each type"""
        defaults = {
            'main': {
                'assistant_name': 'JARVIS',
                'wake_word': 'jarvis',
                'voice_enabled': True,
                'log_level': 'INFO',
                'auto_save_conversations': True,
                'theme': 'dark',
                'language': 'en-US',
                'timezone': 'UTC'
            },
            'voice': {
                'engine': 'pyttsx3',
                'voice_rate': 200,
                'voice_volume': 0.9,
                'recognition_timeout': 5,
                'microphone_index': None,
                'noise_threshold': 300
            },
            'automation': {
                'morning_routine': {
                    'enabled': False,
                    'time': '08:00',
                    'actions': ['weather', 'calendar', 'news']
                },
                'evening_routine': {
                    'enabled': False,
                    'time': '20:00',
                    'actions': ['system_status', 'backup_data']
                }
            },
            'knowledge_base': {
                'personal_facts': {},
                'preferences': {},
                'shortcuts': {},
                'learned_patterns': []
            }
        }
        return defaults.get(config_type, {})
    
    def save_config(self, config_type: str, data: Dict[str, Any]):
        """Save configuration to file"""
        filename = self.config_files.get(config_type, f"{config_type}_config.json")
        
        file_path = self.config_dir / filename
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            if hasattr(self, 'settings') and isinstance(self.settings, dict):
                self.settings[config_type] = data
        except Exception as e:
            print(f"Error saving {filename}: {e}")
    
    def get(self, config_type: str, key: str = None, default=None):
        """Get configuration value"""
        if config_type in self.settings:
            if key:
                return self.settings[config_type].get(key, default)
            return self.settings[config_type]
        return default
    
    def set(self, config_type: str, key: str, value: Any):
        """Set configuration value"""
        if config_type not in self.settings:
            self.settings[config_type] = {}
        
        self.settings[config_type][key] = value
        self.save_config(config_type, self.settings[config_type])


