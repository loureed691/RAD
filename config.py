"""
Configuration management for the KuCoin Futures Trading Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for trading bot"""
    
    # API Configuration
    API_KEY = os.getenv('KUCOIN_API_KEY', '')
    API_SECRET = os.getenv('KUCOIN_API_SECRET', '')
    API_PASSPHRASE = os.getenv('KUCOIN_API_PASSPHRASE', '')
    
    # Trading Configuration
    LEVERAGE = int(os.getenv('LEVERAGE', '10'))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '1000'))
    RISK_PER_TRADE = float(os.getenv('RISK_PER_TRADE', '0.02'))
    MIN_PROFIT_THRESHOLD = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.005'))
    
    # Bot Parameters
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))
    TRAILING_STOP_PERCENTAGE = float(os.getenv('TRAILING_STOP_PERCENTAGE', '0.02'))
    MAX_OPEN_POSITIONS = int(os.getenv('MAX_OPEN_POSITIONS', '3'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    
    # Machine Learning
    RETRAIN_INTERVAL = int(os.getenv('RETRAIN_INTERVAL', '86400'))
    ML_MODEL_PATH = os.getenv('ML_MODEL_PATH', 'models/signal_model.pkl')
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is set"""
        if not cls.API_KEY or not cls.API_SECRET or not cls.API_PASSPHRASE:
            raise ValueError("KuCoin API credentials are required. Please set them in .env file")
        return True
