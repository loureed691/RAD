"""
Logging configuration and utilities for the trading bot
"""
import logging
import os
import sys
from datetime import datetime

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
        
        # Format with colors and icon
        # Time in dim, icon and level in color, message in default
        parts = message.split(' - ', 2)
        if len(parts) >= 3:
            time_part = parts[0]
            level_part = parts[1]
            msg_part = parts[2]
            
            formatted = f"{dim}{time_part}{reset} {color}{icon} {level_part}{reset} {msg_part}"
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
        
        # Prevent propagation to root logger to avoid duplicate messages
        logger.propagate = False
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler (plain text, detailed)
        # Use UTF-8 encoding to properly handle Unicode characters in log files
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level))
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
    def get_logger():
        """Get the trading bot logger"""
        return logging.getLogger('TradingBot')
