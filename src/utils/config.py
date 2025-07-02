"""
Configuration management for PeripheralShare application.
Handles loading, saving, and accessing application settings with validation and defaults.

This is the foundation of our app - it manages all user preferences, network settings,
security options, and device configurations in a JSON file that persists between sessions.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import logging
import platform

class Config:
    """
    Configuration manager for application settings.
    
    This class handles:
    - Loading settings from JSON file
    - Providing default values for missing settings  
    - Validating setting values
    - Saving changes back to file
    - Cross-platform compatibility
    """
    
    # Default configuration - this is what gets used on first run
    DEFAULT_CONFIG = {
        "application": {
            "name": "PeripheralShare",
            "version": "1.0.0",
            "auto_start": False,
            "first_run": True
        },
        "network": {
            "port": 8888,                    # Primary communication port
            "discovery_port": 8889,          # Service discovery port  
            "max_connections": 5,            # Max simultaneous connections
            "timeout": 30,                   # Connection timeout in seconds
            "encryption_enabled": True,      # Encrypt all communication
            "buffer_size": 4096             # Network buffer size
        },
        "input": {
            "mouse_enabled": True,           # Enable mouse sharing
            "keyboard_enabled": True,        # Enable keyboard sharing
            "hotkey_switch": "ctrl+alt+s",   # Switch between devices
            "hotkey_toggle": "ctrl+alt+t",   # Toggle sharing on/off
            "edge_threshold": 5,             # Pixels to edge for switching
            "sensitivity": 1.0,              # Mouse sensitivity multiplier
            "smooth_mouse": True,            # Smooth mouse movement
            "capture_delay": 0.01           # Delay between input captures (seconds)
        },
        "display": {
            "show_cursor_trail": True,       # Visual feedback for mouse
            "show_notifications": True,      # System notifications
            "minimize_to_tray": True,        # Hide to system tray
            "window_position": [100, 100],   # Last window position
            "window_size": [800, 600],       # Last window size
            "theme": "default"               # UI theme
        },
        "audio": {
            "enabled": True,                 # Enable audio sharing
            "quality": "high",               # Audio quality: low/medium/high
            "buffer_size": 1024,             # Audio buffer size
            "sample_rate": 44100,            # Audio sample rate
            "auto_switch": True              # Auto-switch audio devices
        },
        "file_transfer": {
            "enabled": True,                 # Enable file sharing
            "max_file_size": 100 * 1024 * 1024,  # 100MB max file size
            "allowed_extensions": [          # Allowed file types
                ".txt", ".jpg", ".jpeg", ".png", ".gif", ".pdf", 
                ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar"
            ],
            "temp_directory": None,          # Temp folder (auto-detect if None)
            "auto_accept": False             # Auto-accept file transfers
        },
        "security": {
            "require_authentication": True,  # Require device pairing
            "trusted_devices": [],           # List of trusted device IDs
            "device_name": None,             # This device's name (auto-generate if None)
            "encryption_key": None,          # Encryption key (auto-generate)
            "session_timeout": 3600          # Session timeout in seconds
        },
        "logging": {
            "level": "INFO",                 # Log level: DEBUG, INFO, WARNING, ERROR
            "log_to_file": True,             # Save logs to file
            "max_log_files": 5,              # Number of log files to keep
            "max_log_size": 10 * 1024 * 1024  # 10MB max log file size
        }
    }
    
    def __init__(self):
        """Initialize with default configuration."""
        self._config = {
            "network": {
                "port": 8888,
                "discovery_port": 8889,
                "max_connections": 5,
                "timeout": 30
            },
            "input": {
                "mouse_enabled": True,
                "keyboard_enabled": True,
                "sensitivity": 1.0
            },
            "security": {
                "device_name": self._generate_device_name()
            },
            "logging": {
                "level": "INFO"
            }
        }
        
        # Set up basic logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Configuration initialized successfully")
    
    def _generate_device_name(self):
        """Generate a device name based on hostname and OS."""
        try:
            hostname = platform.node() or "Unknown"
            system = platform.system()
            hostname = hostname.split('.')[0]  # Remove domain
            return f"{hostname} ({system})"
        except:
            return "PeripheralShare Device"
    
    def get(self, key, default=None):
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config_ref = self._config
        
        # Navigate to parent keys, creating dictionaries as needed
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
        
        # Set the final value
        config_ref[keys[-1]] = value
    
    def save(self):
        """Save configuration (placeholder for now)."""
        pass
    
    @property
    def all(self):
        """Get all configuration as dictionary."""
        return self._config.copy()
    
    def _get_config_directory(self) -> Path:
        """
        Get the appropriate configuration directory for the current platform.
        
        Returns:
            Path: Platform-specific config directory
        """
        system = platform.system()
        
        if system == 'Windows':
            # Windows: %APPDATA%\PeripheralShare\
            config_dir = Path(os.environ.get('APPDATA', '')) / 'PeripheralShare'
        elif system == 'Darwin':  # macOS
            # macOS: ~/Library/Application Support/PeripheralShare/
            config_dir = Path.home() / 'Library' / 'Application Support' / 'PeripheralShare'
        else:  # Linux and others
            # Linux: ~/.config/PeripheralShare/
            config_dir = Path.home() / '.config' / 'PeripheralShare'
        
        return config_dir
    
    def load(self):
        """
        Load configuration from file.
        
        If file doesn't exist, uses default configuration.
        If file is corrupted, backs it up and uses defaults.
        """
        try:
            if self._get_config_directory() / "config.json".exists():
                with open(self._get_config_directory() / "config.json", 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # Merge with default config (adds any missing keys)
                self._config = self._merge_configs(self.DEFAULT_CONFIG.copy(), file_config)
                self.logger.info(f"Configuration loaded from {self._get_config_directory() / 'config.json'}")
            else:
                # First run - use defaults
                self._config = self.DEFAULT_CONFIG.copy()
                self.save()  # Save default config
                self.logger.info("Created default configuration")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Configuration file corrupted: {e}")
            # Backup corrupted file
            backup_file = self._get_config_directory() / "config.json.backup"
            self._get_config_directory() / "config.json".rename(backup_file)
            self.logger.info(f"Corrupted config backed up to {backup_file}")
            
            # Use defaults
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._config = self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """
        Recursively merge configuration dictionaries.
        
        This ensures that if we add new default settings in future versions,
        they get added to existing user configs automatically.
        
        Args:
            base: Base configuration (with defaults)
            override: User configuration (loaded from file)
            
        Returns:
            Merged configuration
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                base[key] = self._merge_configs(base[key], value)
            else:
                # Override with user value
                base[key] = value
        return base
    
    def validate(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate network settings
            port = self.get('network.port')
            if not isinstance(port, int) or not (1024 <= port <= 65535):
                self.logger.warning(f"Invalid port {port}, resetting to default")
                self.set('network.port', self.DEFAULT_CONFIG['network']['port'])
                return False
            
            # Validate file size limit
            max_size = self.get('file_transfer.max_file_size')
            if not isinstance(max_size, int) or max_size < 0:
                self.logger.warning("Invalid max file size, resetting to default")
                self.set('file_transfer.max_file_size', self.DEFAULT_CONFIG['file_transfer']['max_file_size'])
                return False
            
            # Add more validation as needed...
            
            return True
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"Config(file={self._get_config_directory() / 'config.json'}, sections={list(self._config.keys())})" 