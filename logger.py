"""
Logging configuration and utilities for the trading bot
"""
import logging
import os
from datetime import datetime

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
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level))
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
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
