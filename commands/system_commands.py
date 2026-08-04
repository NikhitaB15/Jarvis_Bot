import os
import subprocess
import platform
import webbrowser
import json
import shutil
import psutil
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, List
import logging

class SystemController:
    def __init__(self):
        self.os_type = platform.system()
        self.app_paths = self._load_app_paths()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for system operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/system_operations.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_app_paths(self) -> dict:
        """Load custom application paths from config file"""
        config_path = Path('config/app_paths.json')
        try:
            if config_path.exists():
                with open(config_path) as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load app paths: {e}")
            
        # Return default configuration
        return {
            'windows': {
                'browser': 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                'editor': 'notepad.exe',
                'terminal': 'cmd.exe',
                'discord': '%LOCALAPPDATA%\\Discord\\Update.exe',
                'spotify': '%APPDATA%\\Spotify\\Spotify.exe',
                'steam': 'C:\\Program Files (x86)\\Steam\\steam.exe'
            },
            'darwin': {  # macOS
                'browser': '/Applications/Google Chrome.app',
                'editor': '/Applications/TextEdit.app',
                'terminal': '/Applications/Utilities/Terminal.app',
                'discord': '/Applications/Discord.app',
                'spotify': '/Applications/Spotify.app',
                'steam': '/Applications/Steam.app'
            },
            'linux': {
                'browser': 'google-chrome',
                'editor': 'gedit',
                'terminal': 'gnome-terminal',
                'discord': 'discord',
                'spotify': 'spotify',
                'steam': 'steam'
            }
        }
    
    def execute_command(self, command: str) -> Tuple[bool, str]:
        """Execute system commands with safety checks"""
        # Enhanced safety check - prevent dangerous commands
        BLACKLIST = [
            'rm -rf', 'format', 'del /f', 'shutdown', 'reboot', 'halt',
            'sudo rm', 'dd if=', 'mkfs', 'fdisk', 'parted', ':(){:|:&};:',
            'chmod 000', 'chown', 'passwd', 'userdel', 'groupdel'
        ]
        
        command_lower = command.lower()
        if any(cmd in command_lower for cmd in BLACKLIST):
            self.logger.warning(f"Blocked dangerous command: {command}")
            return False, "That operation is restricted for safety."
            
        try:
            self.logger.info(f"Executing command: {command}")
            
            if self.os_type == 'Windows':
                result = subprocess.run(
                    command, shell=True, capture_output=True, 
                    text=True, timeout=30
                )
            else:  # Linux/Mac
                result = subprocess.run(
                    command, shell=True, capture_output=True, 
                    text=True, timeout=30
                )
                
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, result.stderr.strip()
            
        except subprocess.TimeoutExpired:
            return False, "Command timed out after 30 seconds"
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return False, str(e)
    
    def open_application(self, app_name: str) -> Tuple[bool, str]:
        """Open applications with platform-specific handling"""
        app_name = app_name.lower().replace(" ", "").replace("-", "").replace("_", "")
        
        # Check custom paths first
        os_key = self.os_type.lower()
        if os_key in self.app_paths and app_name in self.app_paths[os_key]:
            path = self.app_paths[os_key][app_name]
            try:
                if self.os_type == 'Windows':
                    # Handle environment variables in Windows paths
                    path = os.path.expandvars(path)
                    subprocess.Popen([path], shell=True)
                else:
                    subprocess.Popen([path])
                    
                self.logger.info(f"Opened {app_name} from custom path")
                return True, f"Opened {app_name}"
            except Exception as e:
                self.logger.error(f"Failed to open {app_name}: {e}")
                return False, str(e)
        
        # Handle common apps with fallback methods
        app_handlers = {
            'browser': self._open_browser,
            'calculator': self._open_calculator,
            'terminal': self._open_terminal,
            'fileexplorer': self._open_file_explorer,
            'taskmanager': self._open_task_manager,
            'controlpanel': self._open_control_panel,
            'notepad': self._open_notepad,
            'paint': self._open_paint
        }
        
        if app_name in app_handlers:
            try:
                app_handlers[app_name]()
                self.logger.info(f"Opened {app_name}")
                return True, f"Opened {app_name}"
            except Exception as e:
                self.logger.error(f"Failed to open {app_name}: {e}")
                return False, str(e)
        
        # Try generic application launch
        return self._generic_app_launch(app_name)
    
    def _generic_app_launch(self, app_name: str) -> Tuple[bool, str]:
        """Generic application launcher as fallback"""
        try:
            if self.os_type == 'Windows':
                subprocess.Popen(['start', app_name], shell=True)
            elif self.os_type == 'Darwin':
                subprocess.Popen(['open', '-a', app_name])
            else:  # Linux
                subprocess.Popen([app_name])
            return True, f"Attempted to open {app_name}"
        except:
            return False, f"Could not find or open {app_name}"
    
    def _open_browser(self):
        webbrowser.open('')
    
    def _open_calculator(self):
        if self.os_type == 'Windows':
            subprocess.Popen(['calc'])
        elif self.os_type == 'Darwin':
            subprocess.Popen(['open', '-a', 'Calculator'])
        else:
            subprocess.Popen(['gnome-calculator'])
    
    def _open_terminal(self):
        if self.os_type == 'Windows':
            subprocess.Popen(['start', 'cmd'], shell=True)
        elif self.os_type == 'Darwin':
            subprocess.Popen(['open', '-a', 'Terminal'])
        else:
            subprocess.Popen(['gnome-terminal'])
    
    def _open_file_explorer(self):
        if self.os_type == 'Windows':
            subprocess.Popen(['explorer'])
        elif self.os_type == 'Darwin':
            subprocess.Popen(['open', '.'])
        else:
            subprocess.Popen(['nautilus'])
    
    def _open_task_manager(self):
        if self.os_type == 'Windows':
            subprocess.Popen(['taskmgr'])
        elif self.os_type == 'Darwin':
            subprocess.Popen(['open', '-a', 'Activity Monitor'])
        else:
            subprocess.Popen(['gnome-system-monitor'])
    
    def _open_control_panel(self):
        if self.os_type == 'Windows':
            subprocess.Popen(['control'])
        elif self.os_type == 'Darwin':
            subprocess.Popen(['open', '-a', 'System Preferences'])
        else:
            subprocess.Popen(['gnome-control-center'])
    
    def _open_notepad(self):
        if self.os_type == 'Windows':
            subprocess.Popen(['notepad'])
        elif self.os_type == 'Darwin':
            subprocess.Popen(['open', '-a', 'TextEdit'])
        else:
            subprocess.Popen(['gedit'])
    
    def _open_paint(self):
        if self.os_type == 'Windows':
            subprocess.Popen(['mspaint'])
        elif self.os_type == 'Darwin':
            subprocess.Popen(['open', '-a', 'Preview'])
        else:
            subprocess.Popen(['gimp'])
    
    def file_operations(self, operation: str, source: str, destination: str = None) -> Tuple[bool, str]:
        """Handle file operations with validation"""
        try:
            source_path = Path(source).resolve()
            
            # Validate paths to prevent dangerous operations
            if not self._is_safe_path(source_path):
                return False, "Operation on this path is not allowed for safety"
            
            if operation == 'create_file':
                source_path.touch()
                return True, f"Created file: {source_path}"
            
            elif operation == 'create_folder':
                source_path.mkdir(parents=True, exist_ok=True)
                return True, f"Created folder: {source_path}"
            
            elif operation == 'delete':
                if source_path.is_file():
                    source_path.unlink()
                    return True, f"Deleted file: {source_path}"
                elif source_path.is_dir():
                    shutil.rmtree(source_path)
                    return True, f"Deleted folder: {source_path}"
                else:
                    return False, f"Path does not exist: {source_path}"
            
            elif operation == 'copy' and destination:
                dest_path = Path(destination).resolve()
                if not self._is_safe_path(dest_path):
                    return False, "Destination path is not allowed for safety"
                
                if source_path.is_file():
                    shutil.copy2(source_path, dest_path)
                else:
                    shutil.copytree(source_path, dest_path)
                return True, f"Copied {source_path} to {dest_path}"
            
            elif operation == 'move' and destination:
                dest_path = Path(destination).resolve()
                if not self._is_safe_path(dest_path):
                    return False, "Destination path is not allowed for safety"
                
                shutil.move(str(source_path), str(dest_path))
                return True, f"Moved {source_path} to {dest_path}"
            
            else:
                return False, "Invalid operation or missing destination"
                
        except Exception as e:
            self.logger.error(f"File operation failed: {e}")
            return False, str(e)
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is safe for operations"""
        # Prevent operations on system directories
        dangerous_paths = [
            Path('/'),
            Path('/bin'),
            Path('/boot'),
            Path('/dev'),
            Path('/etc'),
            Path('/lib'),
            Path('/proc'),
            Path('/root'),
            Path('/sbin'),
            Path('/sys'),
            Path('/usr/bin'),
            Path('/usr/sbin'),
            Path('/var/log'),
            Path('C:\\Windows'),
            Path('C:\\System32'),
            Path('C:\\Program Files'),
            Path('C:\\Users\\All Users')
        ]
        
        try:
            for dangerous in dangerous_paths:
                if path.is_relative_to(dangerous):
                    return False
        except:
            pass
        
        return True
    
    def get_system_info(self) -> Dict:
        """Get comprehensive system information"""
        try:
            info = {
                'os': {
                    'system': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor()
                },
                'cpu': {
                    'count': psutil.cpu_count(),
                    'usage': psutil.cpu_percent(interval=1),
                    'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'used': psutil.virtual_memory().used,
                    'percentage': psutil.virtual_memory().percent
                },
                'disk': [],
                'network': psutil.net_io_counters()._asdict()
            }
            
            # Get disk information
            for partition in psutil.disk_partitions():
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    info['disk'].append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': partition_usage.total,
                        'used': partition_usage.used,
                        'free': partition_usage.free,
                        'percentage': (partition_usage.used / partition_usage.total) * 100
                    })
                except PermissionError:
                    continue
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {'error': str(e)}
    
    def manage_processes(self, operation: str, process_name: str = None, pid: int = None) -> Tuple[bool, str]:
        """Process management operations"""
        try:
            if operation == 'list':
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                # Sort by CPU usage
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
                return True, str(processes[:10])  # Return top 10
            
            elif operation == 'kill':
                if pid:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    return True, f"Terminated process with PID {pid}"
                elif process_name:
                    killed_count = 0
                    for proc in psutil.process_iter(['pid', 'name']):
                        if proc.info['name'].lower() == process_name.lower():
                            proc.terminate()
                            killed_count += 1
                    return True, f"Terminated {killed_count} process(es) named {process_name}"
                else:
                    return False, "Either PID or process name required"
            
            else:
                return False, "Invalid operation. Use 'list' or 'kill'"
                
        except Exception as e:
            self.logger.error(f"Process management failed: {e}")
            return False, str(e)
    
    def volume_control(self, action: str, level: int = None) -> Tuple[bool, str]:
        """Control system volume"""
        try:
            if self.os_type == 'Windows':
                if action == 'set' and level is not None:
                    # Use nircmd for Windows volume control
                    subprocess.run(['nircmd', 'setsysvolume', str(level * 655)])
                    return True, f"Volume set to {level}%"
                elif action == 'mute':
                    subprocess.run(['nircmd', 'mutesysvolume', '1'])
                    return True, "Volume muted"
                elif action == 'unmute':
                    subprocess.run(['nircmd', 'mutesysvolume', '0'])
                    return True, "Volume unmuted"
                else:
                    return False, "Invalid action or missing level"
            
            elif self.os_type == 'Darwin':  # macOS
                if action == 'set' and level is not None:
                    subprocess.run(['osascript', '-e', f'set volume output volume {level}'])
                    return True, f"Volume set to {level}%"
                elif action == 'mute':
                    subprocess.run(['osascript', '-e', 'set volume output muted true'])
                    return True, "Volume muted"
                elif action == 'unmute':
                    subprocess.run(['osascript', '-e', 'set volume output muted false'])
                    return True, "Volume unmuted"
            
            else:  # Linux
                if action == 'set' and level is not None:
                    subprocess.run(['amixer', 'sset', 'Master', f'{level}%'])
                    return True, f"Volume set to {level}%"
                elif action == 'mute':
                    subprocess.run(['amixer', 'sset', 'Master', 'mute'])
                    return True, "Volume muted"
                elif action == 'unmute':
                    subprocess.run(['amixer', 'sset', 'Master', 'unmute'])
                    return True, "Volume unmuted"
                    
        except Exception as e:
            self.logger.error(f"Volume control failed: {e}")
            return False, str(e)
    
    def power_management(self, action: str) -> Tuple[bool, str]:
        """System power management with confirmation"""
        if action not in ['sleep', 'hibernate', 'lock']:
            return False, "Only sleep, hibernate, and lock operations are allowed"
        
        try:
            if self.os_type == 'Windows':
                if action == 'sleep':
                    subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'])
                elif action == 'hibernate':
                    subprocess.run(['shutdown', '/h'])
                elif action == 'lock':
                    subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'])
                    
            elif self.os_type == 'Darwin':
                if action == 'sleep':
                    subprocess.run(['pmset', 'sleepnow'])
                elif action == 'lock':
                    subprocess.run(['/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession', '-suspend'])
                    
            else:  # Linux
                if action == 'sleep':
                    subprocess.run(['systemctl', 'suspend'])
                elif action == 'hibernate':
                    subprocess.run(['systemctl', 'hibernate'])
                elif action == 'lock':
                    subprocess.run(['gnome-screensaver-command', '--lock'])
            
            return True, f"System {action} initiated"
            
        except Exception as e:
            self.logger.error(f"Power management failed: {e}")
            return False, str(e)
    
    def cleanup_system(self) -> Tuple[bool, str]:
        """Clean up temporary files and logs"""
        try:
            cleaned_size = 0
            cleaned_files = 0
            
            # Temporary directories to clean
            temp_dirs = []
            if self.os_type == 'Windows':
                temp_dirs = [
                    os.path.expandvars('%TEMP%'),
                    os.path.expandvars('%TMP%'),
                    os.path.expandvars('%LOCALAPPDATA%\\Temp')
                ]
            else:
                temp_dirs = ['/tmp', '/var/tmp']
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                # Only clean files older than 1 day
                                if os.path.getmtime(file_path) < (time.time() - 86400):
                                    size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    cleaned_size += size
                                    cleaned_files += 1
                            except (OSError, PermissionError):
                                continue
            
            size_mb = cleaned_size / (1024 * 1024)
            return True, f"Cleaned {cleaned_files} files, freed {size_mb:.2f} MB"
            
        except Exception as e:
            self.logger.error(f"System cleanup failed: {e}")
            return False, str(e)