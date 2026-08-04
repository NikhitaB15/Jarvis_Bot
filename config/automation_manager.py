import schedule
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any
import json

class AutomationManager:
    def __init__(self, config_manager, system_controller):
        self.config_manager = config_manager
        self.system_controller = system_controller
        self.running = False
        self.scheduler_thread = None
        self.custom_functions = {}
        
        # Load automation rules
        self.load_automation_rules()
    
    def load_automation_rules(self):
        """Load automation rules from config"""
        rules = self.config_manager.get('automation', default={})
        
        # Clear existing scheduled jobs
        schedule.clear()
        
        # Set up morning routine
        morning = rules.get('morning_routine', {})
        if morning.get('enabled', False):
            schedule.every().day.at(morning.get('time', '08:00')).do(
                self._execute_routine, 'morning', morning.get('actions', [])
            )
        
        # Set up evening routine
        evening = rules.get('evening_routine', {})
        if evening.get('enabled', False):
            schedule.every().day.at(evening.get('time', '20:00')).do(
                self._execute_routine, 'evening', evening.get('actions', [])
            )
        
        # Set up custom schedules
        custom_schedules = rules.get('custom_schedules', [])
        for custom in custom_schedules:
            if custom.get('enabled', False):
                self._setup_custom_schedule(custom)
    
    def _setup_custom_schedule(self, schedule_config: Dict):
        """Set up a custom schedule"""
        schedule_type = schedule_config.get('type', 'daily')
        time_str = schedule_config.get('time', '12:00')
        actions = schedule_config.get('actions', [])
        name = schedule_config.get('name', 'custom')
        
        if schedule_type == 'daily':
            schedule.every().day.at(time_str).do(self._execute_routine, name, actions)
        elif schedule_type == 'weekly':
            day = schedule_config.get('day', 'monday')
            getattr(schedule.every(), day.lower()).at(time_str).do(self._execute_routine, name, actions)
        elif schedule_type == 'interval':
            interval = schedule_config.get('interval', 60)  # minutes
            schedule.every(interval).minutes.do(self._execute_routine, name, actions)
    
    def _execute_routine(self, routine_name: str, actions: List[str]):
        """Execute a routine with given actions"""
        print(f"Executing {routine_name} routine...")
        
        for action in actions:
            try:
                if action == 'weather':
                    self._get_weather_update()
                elif action == 'calendar':
                    self._get_calendar_events()
                elif action == 'news':
                    self._get_news_summary()
                elif action == 'system_status':
                    self._get_system_status()
                elif action == 'backup_data':
                    self._backup_user_data()
                elif action.startswith('open_'):
                    app_name = action.replace('open_', '')
                    self.system_controller.open_application(app_name)
                elif action.startswith('custom_'):
                    # Execute custom function
                    func_name = action.replace('custom_', '')
                    if func_name in self.custom_functions:
                        self.custom_functions[func_name]()
                else:
                    print(f"Unknown action: {action}")
            except Exception as e:
                print(f"Error executing action {action}: {e}")
    
    def _get_weather_update(self):
        """Get weather update (placeholder - integrate with weather API)"""
        print("Weather update: Partly cloudy, 22°C")
    
    def _get_calendar_events(self):
        """Get calendar events (placeholder - integrate with calendar API)"""
        print("Calendar: You have 2 meetings today")
    
    def _get_news_summary(self):
        """Get news summary (placeholder - integrate with news API)"""
        print("News: Here are today's top headlines...")
    
    def _get_system_status(self):
        """Get system status"""
        info = self.system_controller.get_system_info()
        cpu_usage = info.get('cpu', {}).get('usage', 0)
        memory_usage = info.get('memory', {}).get('percentage', 0)
        print(f"System Status: CPU {cpu_usage}%, Memory {memory_usage}%")
    
    def _backup_user_data(self):
        """Backup user data"""
        print("Backing up user data...")
        # Implement backup logic here
    
    def register_custom_function(self, name: str, func: Callable):
        """Register a custom function for automation"""
        self.custom_functions[name] = func
    
    def start_scheduler(self):
        """Start the automation scheduler"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            print("Automation scheduler started")
    
    def stop_scheduler(self):
        """Stop the automation scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        print("Automation scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def add_schedule(self, name: str, schedule_config: Dict):
        """Add a new schedule dynamically"""
        # Add to config
        automation_config = self.config_manager.get('automation')
        if 'custom_schedules' not in automation_config:
            automation_config['custom_schedules'] = []
        
        schedule_config['name'] = name
        automation_config['custom_schedules'].append(schedule_config)
        
        self.config_manager.set('automation', 'custom_schedules', automation_config['custom_schedules'])
        
        # Set up the schedule
        self._setup_custom_schedule(schedule_config)
        
        return True, f"Schedule '{name}' added successfully"
    
    def remove_schedule(self, name: str):
        """Remove a schedule"""
        automation_config = self.config_manager.get('automation')
        custom_schedules = automation_config.get('custom_schedules', [])
        
        # Remove from config
        updated_schedules = [s for s in custom_schedules if s.get('name') != name]
        automation_config['custom_schedules'] = updated_schedules
        
        self.config_manager.set('automation', 'custom_schedules', updated_schedules)
        
        # Reload all rules (this will clear and recreate schedules)
        self.load_automation_rules()
        
        return True, f"Schedule '{name}' removed successfully"
