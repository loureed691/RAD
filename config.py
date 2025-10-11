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
    
    # WebSocket Configuration
    ENABLE_WEBSOCKET = os.getenv('ENABLE_WEBSOCKET', 'true').lower() in ('true', '1', 'yes')
    
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
    
    # Bot Parameters
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))
    POSITION_UPDATE_INTERVAL = int(float(os.getenv('POSITION_UPDATE_INTERVAL', '1.0')))  # Minimum time between position API calls (seconds) - faster for responsive trailing stops
    LIVE_LOOP_INTERVAL = float(os.getenv('LIVE_LOOP_INTERVAL', '0.05'))  # Main loop sleep interval for live monitoring (seconds) - reduced for faster response
    TRAILING_STOP_PERCENTAGE = float(os.getenv('TRAILING_STOP_PERCENTAGE', '0.02'))
    MAX_OPEN_POSITIONS = int(os.getenv('MAX_OPEN_POSITIONS', '3'))
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '20'))  # Number of parallel workers for market scanning
    CACHE_DURATION = int(os.getenv('CACHE_DURATION', '300'))  # Cache duration in seconds (default: 5 minutes)
    STALE_DATA_MULTIPLIER = int(os.getenv('STALE_DATA_MULTIPLIER', '2'))  # Multiplier for CHECK_INTERVAL to determine max age for opportunity data
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
    POSITION_LOG_FILE = os.getenv('POSITION_LOG_FILE', 'logs/positions.log')
    SCANNING_LOG_FILE = os.getenv('SCANNING_LOG_FILE', 'logs/scanning.log')
    ORDERS_LOG_FILE = os.getenv('ORDERS_LOG_FILE', 'logs/orders.log')
    STRATEGY_LOG_FILE = os.getenv('STRATEGY_LOG_FILE', 'logs/strategy.log')
    DETAILED_LOG_LEVEL = os.getenv('DETAILED_LOG_LEVEL', 'DEBUG')  # Level for position and scanning logs
    
    # Machine Learning
    RETRAIN_INTERVAL = int(os.getenv('RETRAIN_INTERVAL', '86400'))
    ML_MODEL_PATH = os.getenv('ML_MODEL_PATH', 'models/signal_model.pkl')
    
    @classmethod
    def auto_configure_from_balance(cls, available_balance: float):
        """
        Automatically configure trading parameters based on available balance
        
        This method intelligently sets optimal values for LEVERAGE, MAX_POSITION_SIZE,
        RISK_PER_TRADE, and MIN_PROFIT_THRESHOLD based on the account balance.
        
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
            # Smart leverage based on balance - MORE CONSERVATIVE (smaller accounts = lower leverage for safety)
            if available_balance < 100:
                cls.LEVERAGE = 4  # Micro account - very conservative (was 5)
            elif available_balance < 1000:
                cls.LEVERAGE = 6  # Small account - conservative (was 7)
            elif available_balance < 10000:
                cls.LEVERAGE = 8  # Medium account - balanced (was 10)
            elif available_balance < 100000:
                cls.LEVERAGE = 10  # Large account - moderate (was 12)
            else:
                cls.LEVERAGE = 12  # Very large account - moderate-aggressive (was 15)
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
            # Min profit threshold - must cover trading fees (maker 0.02% + taker 0.06% = ~0.08-0.12% round-trip)
            # Plus provide meaningful profit after fees
            # Typical round-trip trading cost: ~0.1% (0.001)
            trading_fee_buffer = 0.0012  # 0.12% to cover round-trip fees with small buffer
            
            if available_balance < 100:
                # Micro accounts need higher threshold due to fixed minimums and slippage
                cls.MIN_PROFIT_THRESHOLD = trading_fee_buffer + 0.008  # 0.12% fees + 0.8% profit = 0.92%
            elif available_balance < 1000:
                # Small accounts 
                cls.MIN_PROFIT_THRESHOLD = trading_fee_buffer + 0.006  # 0.12% fees + 0.6% profit = 0.72%
            else:
                # Medium+ accounts
                cls.MIN_PROFIT_THRESHOLD = trading_fee_buffer + 0.005  # 0.12% fees + 0.5% profit = 0.62%
            
            logger.info(f"🤖 Auto-configured MIN_PROFIT_THRESHOLD: {cls.MIN_PROFIT_THRESHOLD:.2%} (balance: ${available_balance:.2f}, includes ~0.12% trading fees)")
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is set"""
        if not cls.API_KEY or not cls.API_SECRET or not cls.API_PASSPHRASE:
            raise ValueError("KuCoin API credentials are required. Please set them in .env file")
        return True
