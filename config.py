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
    
    # Trading Configuration - will be auto-configured if not set in .env
    LEVERAGE = None  # Will be set by auto_configure_from_balance()
    MAX_POSITION_SIZE = None  # Will be set by auto_configure_from_balance()
    RISK_PER_TRADE = None  # Will be set by auto_configure_from_balance()
    MIN_PROFIT_THRESHOLD = None  # Will be set by auto_configure_from_balance()
    
    # Store user overrides from environment if provided
    _LEVERAGE_OVERRIDE = os.getenv('LEVERAGE')
    _MAX_POSITION_SIZE_OVERRIDE = os.getenv('MAX_POSITION_SIZE')
    _RISK_PER_TRADE_OVERRIDE = os.getenv('RISK_PER_TRADE')
    _MIN_PROFIT_THRESHOLD_OVERRIDE = os.getenv('MIN_PROFIT_THRESHOLD')
    _TRAILING_STOP_PERCENTAGE_OVERRIDE = os.getenv('TRAILING_STOP_PERCENTAGE')
    _MAX_OPEN_POSITIONS_OVERRIDE = os.getenv('MAX_OPEN_POSITIONS')
    
    # Bot Parameters - will be auto-configured if not set in .env
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))
    TRAILING_STOP_PERCENTAGE = None  # Will be set by auto_configure_from_balance()
    MAX_OPEN_POSITIONS = None  # Will be set by auto_configure_from_balance()
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    
    # Machine Learning
    RETRAIN_INTERVAL = int(os.getenv('RETRAIN_INTERVAL', '86400'))
    ML_MODEL_PATH = os.getenv('ML_MODEL_PATH', 'models/signal_model.pkl')
    
    @classmethod
    def auto_configure_from_balance(cls, available_balance: float):
        """
        Automatically configure trading parameters based on available balance
        
        This method intelligently sets optimal values for LEVERAGE, MAX_POSITION_SIZE,
        RISK_PER_TRADE, MIN_PROFIT_THRESHOLD, TRAILING_STOP_PERCENTAGE, and 
        MAX_OPEN_POSITIONS based on the account balance.
        
        Balance tiers:
        - Micro ($10-$100): Very conservative settings for learning
        - Small ($100-$1000): Conservative settings for small accounts
        - Medium ($1000-$10000): Balanced settings for growing accounts
        - Large ($10000-$100000): Aggressive settings for experienced traders
        - Very Large ($100000+): Professional settings with higher leverage
        
        Args:
            available_balance: Current USDT balance in account
        """
        from logger import Logger
        logger = Logger.get_logger()
        
        # Apply user overrides if provided, otherwise calculate smart defaults
        if cls._LEVERAGE_OVERRIDE:
            cls.LEVERAGE = int(cls._LEVERAGE_OVERRIDE)
            logger.info(f"📌 Using user-defined LEVERAGE: {cls.LEVERAGE}x")
        else:
            # Smart leverage based on balance (smaller accounts = lower leverage for safety)
            if available_balance < 100:
                cls.LEVERAGE = 5  # Micro account - very conservative
            elif available_balance < 1000:
                cls.LEVERAGE = 7  # Small account - conservative
            elif available_balance < 10000:
                cls.LEVERAGE = 10  # Medium account - balanced
            elif available_balance < 100000:
                cls.LEVERAGE = 12  # Large account - moderate-aggressive
            else:
                cls.LEVERAGE = 15  # Very large account - aggressive
            logger.info(f"🤖 Auto-configured LEVERAGE: {cls.LEVERAGE}x (balance: ${available_balance:.2f})")
        
        if cls._MAX_POSITION_SIZE_OVERRIDE:
            cls.MAX_POSITION_SIZE = float(cls._MAX_POSITION_SIZE_OVERRIDE)
            logger.info(f"📌 Using user-defined MAX_POSITION_SIZE: ${cls.MAX_POSITION_SIZE:.2f}")
        else:
            # Max position size as percentage of balance
            # Smaller accounts use smaller percentage to preserve capital
            if available_balance < 100:
                cls.MAX_POSITION_SIZE = available_balance * 0.3  # 30% max for micro accounts
            elif available_balance < 1000:
                cls.MAX_POSITION_SIZE = available_balance * 0.4  # 40% max for small accounts
            elif available_balance < 10000:
                cls.MAX_POSITION_SIZE = available_balance * 0.5  # 50% max for medium accounts
            else:
                cls.MAX_POSITION_SIZE = available_balance * 0.6  # 60% max for large accounts
            
            # Ensure reasonable min/max bounds
            cls.MAX_POSITION_SIZE = max(10, min(cls.MAX_POSITION_SIZE, 50000))
            logger.info(f"🤖 Auto-configured MAX_POSITION_SIZE: ${cls.MAX_POSITION_SIZE:.2f} (balance: ${available_balance:.2f})")
        
        if cls._RISK_PER_TRADE_OVERRIDE:
            cls.RISK_PER_TRADE = float(cls._RISK_PER_TRADE_OVERRIDE)
            logger.info(f"📌 Using user-defined RISK_PER_TRADE: {cls.RISK_PER_TRADE:.2%}")
        else:
            # Risk per trade - smaller for larger accounts (relative risk management)
            if available_balance < 100:
                cls.RISK_PER_TRADE = 0.01  # 1% risk for micro accounts (be very careful)
            elif available_balance < 1000:
                cls.RISK_PER_TRADE = 0.015  # 1.5% risk for small accounts
            elif available_balance < 10000:
                cls.RISK_PER_TRADE = 0.02  # 2% risk for medium accounts
            elif available_balance < 100000:
                cls.RISK_PER_TRADE = 0.025  # 2.5% risk for large accounts
            else:
                cls.RISK_PER_TRADE = 0.03  # 3% risk for very large accounts
            logger.info(f"🤖 Auto-configured RISK_PER_TRADE: {cls.RISK_PER_TRADE:.2%} (balance: ${available_balance:.2f})")
        
        if cls._MIN_PROFIT_THRESHOLD_OVERRIDE:
            cls.MIN_PROFIT_THRESHOLD = float(cls._MIN_PROFIT_THRESHOLD_OVERRIDE)
            logger.info(f"📌 Using user-defined MIN_PROFIT_THRESHOLD: {cls.MIN_PROFIT_THRESHOLD:.2%}")
        else:
            # Min profit threshold - higher for smaller accounts to offset fees
            if available_balance < 100:
                cls.MIN_PROFIT_THRESHOLD = 0.008  # 0.8% min profit for micro accounts
            elif available_balance < 1000:
                cls.MIN_PROFIT_THRESHOLD = 0.006  # 0.6% min profit for small accounts
            else:
                cls.MIN_PROFIT_THRESHOLD = 0.005  # 0.5% min profit for medium+ accounts
            logger.info(f"🤖 Auto-configured MIN_PROFIT_THRESHOLD: {cls.MIN_PROFIT_THRESHOLD:.2%} (balance: ${available_balance:.2f})")
        
        if cls._TRAILING_STOP_PERCENTAGE_OVERRIDE:
            cls.TRAILING_STOP_PERCENTAGE = float(cls._TRAILING_STOP_PERCENTAGE_OVERRIDE)
            logger.info(f"📌 Using user-defined TRAILING_STOP_PERCENTAGE: {cls.TRAILING_STOP_PERCENTAGE:.2%}")
        else:
            # Trailing stop percentage - tighter for smaller accounts, wider for larger accounts
            # Smaller accounts need tighter stops to preserve capital
            # Larger accounts can afford wider stops to avoid premature exits
            if available_balance < 100:
                cls.TRAILING_STOP_PERCENTAGE = 0.015  # 1.5% for micro accounts (tighter)
            elif available_balance < 1000:
                cls.TRAILING_STOP_PERCENTAGE = 0.018  # 1.8% for small accounts
            elif available_balance < 10000:
                cls.TRAILING_STOP_PERCENTAGE = 0.02   # 2.0% for medium accounts (standard)
            elif available_balance < 100000:
                cls.TRAILING_STOP_PERCENTAGE = 0.025  # 2.5% for large accounts
            else:
                cls.TRAILING_STOP_PERCENTAGE = 0.03   # 3.0% for very large accounts (wider)
            logger.info(f"🤖 Auto-configured TRAILING_STOP_PERCENTAGE: {cls.TRAILING_STOP_PERCENTAGE:.2%} (balance: ${available_balance:.2f})")
        
        if cls._MAX_OPEN_POSITIONS_OVERRIDE:
            cls.MAX_OPEN_POSITIONS = int(cls._MAX_OPEN_POSITIONS_OVERRIDE)
            logger.info(f"📌 Using user-defined MAX_OPEN_POSITIONS: {cls.MAX_OPEN_POSITIONS}")
        else:
            # Max open positions - fewer for smaller accounts to manage risk
            # More for larger accounts to diversify
            if available_balance < 100:
                cls.MAX_OPEN_POSITIONS = 1  # Micro accounts: focus on one trade at a time
            elif available_balance < 1000:
                cls.MAX_OPEN_POSITIONS = 2  # Small accounts: max 2 positions
            elif available_balance < 10000:
                cls.MAX_OPEN_POSITIONS = 3  # Medium accounts: max 3 positions (standard)
            elif available_balance < 100000:
                cls.MAX_OPEN_POSITIONS = 4  # Large accounts: max 4 positions
            else:
                cls.MAX_OPEN_POSITIONS = 5  # Very large accounts: max 5 positions for diversification
            logger.info(f"🤖 Auto-configured MAX_OPEN_POSITIONS: {cls.MAX_OPEN_POSITIONS} (balance: ${available_balance:.2f})")
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is set"""
        if not cls.API_KEY or not cls.API_SECRET or not cls.API_PASSPHRASE:
            raise ValueError("KuCoin API credentials are required. Please set them in .env file")
        return True
