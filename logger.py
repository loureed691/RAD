"""
Logging configuration and utilities for the trading bot
"""
import logging
import os
import sys
from datetime import datetime

class ComponentFormatter(logging.Formatter):
    """Custom formatter that adds component tags to log messages"""
    
    def format(self, record):
        """Format log record with component tags"""
        # Extract component tag from logger name (e.g., "TradingBot.Position" -> "[POSITION]")
        component_tag = ''
        if '.' in record.name:
            component = record.name.split('.')[-1].upper()
            component_tag = f"[{component}] "
        
        # Store the original format
        original_format = self._style._fmt
        
        # Add component tag to the format if present
        if component_tag:
            self._style._fmt = original_format.replace('%(levelname)s', f'{component_tag}%(levelname)s')
        
        # Format the message
        result = super().format(record)
        
        # Restore original format
        self._style._fmt = original_format
        
        return result

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and icons for terminal output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m',     # Reset
        'BOLD': '\033[1m',      # Bold
        'DIM': '\033[2m'        # Dim
    }
    
    # Icons for different log levels
    ICONS = {
        'DEBUG': '🔍',
        'INFO': '✓',
        'WARNING': '⚠️',
        'ERROR': '✗',
        'CRITICAL': '🔥'
    }
    
    def __init__(self, *args, use_colors=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors and self._supports_color()
    
    @staticmethod
    def _supports_color():
        """Check if terminal supports colors"""
        # Check if stdout is a terminal
        if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
            return False
        
        # Check for common color-supporting terminals
        term = os.environ.get('TERM', '')
        if 'color' in term or term in ('xterm', 'xterm-256color', 'screen', 'linux'):
            return True
        
        # Windows terminal detection
        if sys.platform == 'win32':
            try:
                import colorama
                colorama.init()
                return True
            except ImportError:
                pass
        
        return False  # Default to not supporting colors
    
    def format(self, record):
        """Format log record with colors and icons"""
        # Get the base formatted message
        message = super().format(record)
        
        if not self.use_colors:
            return message
        
        levelname = record.levelname
        
        # Get color and icon for this level
        color = self.COLORS.get(levelname, '')
        icon = self.ICONS.get(levelname, '•')
        reset = self.COLORS['RESET']
        dim = self.COLORS['DIM']
        bold = self.COLORS['BOLD']
        
        # Extract component tag from logger name (e.g., "TradingBot.Position" -> "[POSITION]")
        component_tag = ''
        if '.' in record.name:
            component = record.name.split('.')[-1].upper()
            # Add specific colors for different components
            component_colors = {
                'POSITION': '\033[95m',   # Bright magenta
                'SCANNING': '\033[96m',   # Bright cyan
                'ORDER': '\033[93m',      # Bright yellow
                'STRATEGY': '\033[94m'    # Bright blue
            }
            component_color = component_colors.get(component, '\033[97m')  # Default to bright white
            component_tag = f"{component_color}[{component}]{reset} "
        
        # Format with colors and icon
        # Time in dim, component tag in color, icon and level in color, message in default
        parts = message.split(' - ', 2)
        if len(parts) >= 3:
            time_part = parts[0]
            level_part = parts[1]
            msg_part = parts[2]
            
            formatted = f"{dim}{time_part}{reset} {component_tag}{color}{icon} {level_part}{reset} {msg_part}"
            return formatted
        
        return message

class Logger:
    """Custom logger with file and console output"""
    
    @staticmethod
    def setup(log_level='INFO', log_file='logs/bot.log'):
        """Set up logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure logger
        logger = logging.getLogger('TradingBot')
        logger.setLevel(getattr(logging, log_level))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler (plain text, detailed)
        # Use UTF-8 encoding to properly handle Unicode characters in log files
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level))
        file_formatter = ComponentFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler (colored, concise)
        # Use UTF-8 encoding for console output to handle Unicode characters (emojis)
        # This is especially important on Windows where the default encoding is often cp1252
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))
        
        # Set UTF-8 encoding for the stream to handle Unicode emojis
        if hasattr(console_handler.stream, 'reconfigure'):
            # Python 3.7+ has reconfigure method
            try:
                console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass  # If reconfigure fails, continue with default encoding
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S',
            use_colors=True
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    @staticmethod
    def setup_specialized_logger(name: str, log_file: str, log_level='DEBUG'):
        """
        Set up a specialized logger that writes to the main log file with prefixes.
        This consolidates all logs into a single unified view.
        
        Args:
            name: Logger name (e.g., 'PositionLogger', 'ScanningLogger')
            log_file: Path to log file (will use main log file instead)
            log_level: Logging level for this logger
        
        Returns:
            Configured logger instance that shares the main bot logger
        """
        # Get the main TradingBot logger - all specialized loggers now use the same logger
        # but with different name prefixes for clarity
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Don't prevent propagation - let it bubble up to the main TradingBot logger
        # This way all logs go to the same file
        logger.propagate = True
        
        return logger
    
    @staticmethod
    def get_logger():
        """Get the trading bot logger"""
        return logging.getLogger('TradingBot')
    
    @staticmethod
    def get_position_logger():
        """Get the position tracking logger with [POSITION] prefix"""
        return logging.getLogger('TradingBot.Position')
    
    @staticmethod
    def get_scanning_logger():
        """Get the market scanning logger with [SCANNING] prefix"""
        return logging.getLogger('TradingBot.Scanning')
    
    @staticmethod
    def get_orders_logger():
        """Get the orders logger with [ORDER] prefix"""
        return logging.getLogger('TradingBot.Order')
    
    @staticmethod
    def get_strategy_logger():
        """Get the strategy logger with [STRATEGY] prefix"""
        return logging.getLogger('TradingBot.Strategy')
