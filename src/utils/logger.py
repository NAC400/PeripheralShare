"""
Advanced logging system for PeripheralShare application.
Provides structured logging with file rotation, specialized loggers, and configurable levels.

This system helps us debug issues and monitor the application's behavior.
We create separate loggers for different components so we can track exactly what's happening.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import platform
import datetime

class PeripheralShareLogger:
    """
    Advanced logging system with specialized loggers for different components.
    
    Features:
    - File rotation (prevents log files from getting too large)
    - Color-coded console output (for debugging)
    - Separate loggers for different components
    - Configurable log levels per component
    - Performance monitoring capabilities
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the logging system.
        
        Args:
            config_manager: Configuration manager instance (optional)
        """
        self.config = config_manager
        self.loggers: Dict[str, logging.Logger] = {}
        self.log_directory = self._get_log_directory()
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize main logger
        self.setup_logging()
    
    def _get_log_directory(self) -> Path:
        """Get the appropriate log directory for the current platform."""
        system = platform.system()
        
        if system == 'Windows':
            # Windows: %APPDATA%\PeripheralShare\logs\
            log_dir = Path(os.environ.get('APPDATA', '')) / 'PeripheralShare' / 'logs'
        elif system == 'Darwin':  # macOS
            # macOS: ~/Library/Logs/PeripheralShare/
            log_dir = Path.home() / 'Library' / 'Logs' / 'PeripheralShare'
        else:  # Linux and others
            # Linux: ~/.local/share/PeripheralShare/logs/
            log_dir = Path.home() / '.local' / 'share' / 'PeripheralShare' / 'logs'
        
        return log_dir
    
    def setup_logging(self):
        """
        Setup the main logging configuration.
        
        This configures:
        - File rotation (max 5 files, 10MB each)
        - Console output with colors
        - Appropriate log levels
        - Structured formatting
        """
        # Get settings from config
        if self.config:
            log_level = self.config.get('logging.level', 'INFO')
            log_to_file = self.config.get('logging.log_to_file', True)
            max_files = self.config.get('logging.max_log_files', 5)
            max_size = self.config.get('logging.max_log_size', 10 * 1024 * 1024)  # 10MB
        else:
            log_level = 'INFO'
            log_to_file = True
            max_files = 5
            max_size = 10 * 1024 * 1024
        
        # Create main logger
        main_logger = logging.getLogger('PeripheralShare')
        main_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Clear any existing handlers
        main_logger.handlers.clear()
        
        # File handler with rotation
        if log_to_file:
            log_file = self.log_directory / 'peripheralshare.log'
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=max_files,
                encoding='utf-8'
            )
            
            # Detailed format for file logs
            file_formatter = logging.Formatter(
                '[{asctime}] {levelname:8} | {name:20} | {funcName:15} | {message}',
                style='{',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            main_logger.addHandler(file_handler)
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            '{levelname:8} | {name:15} | {message}',
            style='{'
        )
        console_handler.setFormatter(console_formatter)
        main_logger.addHandler(console_handler)
        
        # Store main logger
        self.loggers['main'] = main_logger
        
        # Log startup information
        main_logger.info("="*60)
        main_logger.info(f"PeripheralShare Logger initialized")
        main_logger.info(f"Platform: {platform.system()} {platform.release()}")
        main_logger.info(f"Python: {platform.python_version()}")
        main_logger.info(f"Log directory: {self.log_directory}")
        main_logger.info(f"Log level: {log_level}")
        main_logger.info("="*60)
    
    def get_logger(self, component: str) -> logging.Logger:
        """
        Get or create a specialized logger for a component.
        
        Args:
            component: Component name (e.g., 'network', 'input', 'audio')
            
        Returns:
            Logger instance for the component
            
        Example:
            network_logger = logger_manager.get_logger('network')
            network_logger.info("Server started on port 8888")
        """
        if component not in self.loggers:
            logger_name = f"PeripheralShare.{component}"
            component_logger = logging.getLogger(logger_name)
            
            # Inherit level from main logger
            main_logger = self.loggers.get('main')
            if main_logger:
                component_logger.setLevel(main_logger.level)
            
            self.loggers[component] = component_logger
        
        return self.loggers[component]
    
    def set_level(self, component: str, level: str):
        """
        Set log level for a specific component.
        
        Args:
            component: Component name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if component in self.loggers:
            self.loggers[component].setLevel(getattr(logging, level.upper(), logging.INFO))
    
    def log_performance(self, component: str, operation: str, duration: float):
        """
        Log performance metrics.
        
        Args:
            component: Component name
            operation: Operation description
            duration: Duration in seconds
        """
        logger = self.get_logger(f"{component}.performance")
        
        if duration > 1.0:
            logger.warning(f"{operation} took {duration:.3f}s (slow)")
        elif duration > 0.5:
            logger.info(f"{operation} took {duration:.3f}s")
        else:
            logger.debug(f"{operation} took {duration:.3f}s")
    
    def log_network_event(self, event_type: str, details: Dict[str, Any]):
        """
        Log network-related events with structured data.
        
        Args:
            event_type: Type of network event
            details: Event details dictionary
        """
        logger = self.get_logger('network')
        message = f"{event_type}: {details}"
        
        if event_type in ['connection_lost', 'connection_failed', 'authentication_failed']:
            logger.error(message)
        elif event_type in ['connection_established', 'device_discovered']:
            logger.info(message)
        else:
            logger.debug(message)
    
    def log_input_event(self, input_type: str, details: Dict[str, Any]):
        """
        Log input-related events.
        
        Args:
            input_type: Type of input event (mouse, keyboard)
            details: Event details
        """
        logger = self.get_logger('input')
        
        # Only log at debug level to avoid spam
        logger.debug(f"{input_type}: {details}")
    
    def log_error(self, component: str, error: Exception, context: str = ""):
        """
        Log errors with full context and stack trace.
        
        Args:
            component: Component where error occurred
            error: Exception instance
            context: Additional context information
        """
        logger = self.get_logger(component)
        
        error_msg = f"Error in {context}: {type(error).__name__}: {error}"
        logger.error(error_msg, exc_info=True)
    
    def create_session_log(self, session_id: str) -> logging.Logger:
        """
        Create a session-specific logger for tracking a connection session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Logger instance for the session
        """
        session_logger = self.get_logger(f"session.{session_id}")
        session_logger.info(f"Session {session_id} started")
        return session_logger
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Clean up old log files to prevent disk space issues.
        
        Args:
            days_to_keep: Number of days of logs to keep
        """
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
            
            for log_file in self.log_directory.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    self.get_logger('main').info(f"Cleaned up old log file: {log_file.name}")
        
        except Exception as e:
            self.get_logger('main').error(f"Failed to cleanup old logs: {e}")

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to console output.
    
    Makes it easier to spot warnings and errors during development.
    """
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[37m',       # White
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'  # Reset color
    
    def format(self, record):
        """Format log record with colors."""
        # Add color to the log level
        if record.levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            record.levelname = colored_levelname
        
        return super().format(record)

class PerformanceTimer:
    """
    Context manager for timing operations.
    
    Example:
        with PerformanceTimer(logger, "database_query"):
            result = database.query(sql)
    """
    
    def __init__(self, logger_manager: PeripheralShareLogger, component: str, operation: str):
        """
        Initialize performance timer.
        
        Args:
            logger_manager: Logger manager instance
            component: Component name
            operation: Operation description
        """
        self.logger_manager = logger_manager
        self.component = component
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = datetime.datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log duration."""
        if self.start_time:
            duration = (datetime.datetime.now() - self.start_time).total_seconds()
            self.logger_manager.log_performance(self.component, self.operation, duration)

# Global logger instance
_logger_manager: Optional[PeripheralShareLogger] = None

def initialize_logging(config_manager=None) -> PeripheralShareLogger:
    """
    Initialize the global logging system.
    
    Args:
        config_manager: Configuration manager instance
        
    Returns:
        Logger manager instance
    """
    global _logger_manager
    _logger_manager = PeripheralShareLogger(config_manager)
    return _logger_manager

def get_logger(component: str = 'main') -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        component: Component name
        
    Returns:
        Logger instance
    """
    if _logger_manager is None:
        # Initialize with defaults if not already done
        initialize_logging()
    
    return _logger_manager.get_logger(component)

def log_performance(component: str, operation: str, duration: float):
    """
    Convenience function for logging performance metrics.
    
    Args:
        component: Component name
        operation: Operation description  
        duration: Duration in seconds
    """
    if _logger_manager:
        _logger_manager.log_performance(component, operation, duration)

def timer(component: str, operation: str) -> PerformanceTimer:
    """
    Convenience function for creating performance timers.
    
    Args:
        component: Component name
        operation: Operation description
        
    Returns:
        Performance timer context manager
    """
    if _logger_manager is None:
        initialize_logging()
    
    return PerformanceTimer(_logger_manager, component, operation)

def setup_logging(level='INFO'):
    """Setup basic logging configuration."""
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Get logger for our application
    logger = logging.getLogger('PeripheralShare')
    logger.info("Logging system initialized")
    
    return logger

def get_logger(name='PeripheralShare'):
    """Get a logger instance."""
    return logging.getLogger(name) 

# Wrapper classes for backward compatibility
class NetworkLogger:
    def __init__(self):
        self.logger = get_logger("network")
    
    def info(self, message):
        self.logger.info(message)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def warning(self, message):
        self.logger.warning(message)

class InputLogger:
    def __init__(self):
        self.logger = get_logger("input")
    
    def info(self, message):
        self.logger.info(message)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def warning(self, message):
        self.logger.warning(message)

class AudioLogger:
    def __init__(self):
        self.logger = get_logger("audio")
    
    def info(self, message):
        self.logger.info(message)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def warning(self, message):
        self.logger.warning(message)


