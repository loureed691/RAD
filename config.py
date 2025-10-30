"""
Configuration management for the KuCoin Futures Trading Bot
"""
import os
import random
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# REPRODUCIBILITY: Set random seeds for consistent behavior across runs
# This is critical for debugging and testing
RANDOM_SEED = int(os.getenv('RANDOM_SEED', '42'))
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Helper functions for safely parsing environment variables
def _safe_parse_int(value: str, param_name: str):
    """Safely parse string to int, handling floats and invalid values"""
    if not value or not value.strip():
        return None
    try:
        # Try converting via float first to handle values like "10.5"
        return int(float(value.strip()))
    except (ValueError, TypeError):
        # Log warning but don't crash - will use auto-configuration instead
        import sys
        print(f"Warning: Invalid {param_name} value '{value}' in .env, will use auto-configuration", file=sys.stderr)
        return None

def _safe_parse_float(value: str, param_name: str):
    """Safely parse string to float, handling invalid values"""
    if not value or not value.strip():
        return None
    try:
        return float(value.strip())
    except (ValueError, TypeError):
        # Log warning but don't crash - will use auto-configuration instead
        import sys
        print(f"Warning: Invalid {param_name} value '{value}' in .env, will use auto-configuration", file=sys.stderr)
        return None

# Set TensorFlow seed for reproducibility (if TensorFlow is used)
try:
    import tensorflow as tf
    tf.random.set_seed(RANDOM_SEED)
    # For reproducible hash-based operations, PYTHONHASHSEED must be set in the environment before launching Python.
    # Example: `PYTHONHASHSEED=42 python your_script.py`
    import logging
    pythonhashseed_env = os.environ.get('PYTHONHASHSEED')
    if pythonhashseed_env is None:
        logging.warning(f"PYTHONHASHSEED is not set. For reproducible hash-based operations, set PYTHONHASHSEED in your environment before launching Python (e.g., PYTHONHASHSEED={RANDOM_SEED}).")
    elif pythonhashseed_env != str(RANDOM_SEED):
        logging.warning(f"PYTHONHASHSEED ({pythonhashseed_env}) does not match RANDOM_SEED ({RANDOM_SEED}). For full reproducibility, set PYTHONHASHSEED={RANDOM_SEED} in your environment before launching Python.")
except ImportError:
    pass  # TensorFlow not installed or not needed

class Config:
    """
    Configuration class for trading bot with intelligent auto-configuration
    
    MINIMAL SETUP: Only KuCoin API credentials are required in .env file.
    All other parameters are automatically configured with optimal defaults.
    
    AUTO-CONFIGURED PARAMETERS (based on account balance):
    - LEVERAGE: 4-12x (smaller accounts get lower leverage for safety)
    - MAX_POSITION_SIZE: 30-60% of balance (scaled for account size)
    - RISK_PER_TRADE: 1-3% (conservative for small, aggressive for large)
    - MIN_PROFIT_THRESHOLD: 0.62-0.92% (includes trading fees + profit)
    
    OPTIMAL DEFAULTS (fine-tuned for best performance):
    - WebSocket: Enabled (real-time data)
    - Dashboard: Enabled on port 5000 (monitor your trades)
    - CHECK_INTERVAL: 60s (fast enough, avoids rate limits)
    - MAX_WORKERS: 20 (parallel scanning, fast but safe)
    - DCA Strategy: Enabled with smart defaults
    - Hedging: Enabled for portfolio protection
    
    OVERRIDE: Set any parameter in .env to override defaults.
    """
    
    # API Configuration
    API_KEY = os.getenv('KUCOIN_API_KEY', '')
    API_SECRET = os.getenv('KUCOIN_API_SECRET', '')
    API_PASSPHRASE = os.getenv('KUCOIN_API_PASSPHRASE', '')
    
    # WebSocket Configuration
    ENABLE_WEBSOCKET = os.getenv('ENABLE_WEBSOCKET', 'true').lower() in ('true', '1', 'yes')
    
    # Dashboard Configuration
    ENABLE_DASHBOARD = os.getenv('ENABLE_DASHBOARD', 'true').lower() in ('true', '1', 'yes')
    DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', '5000'))
    DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '127.0.0.1')  # Localhost by default for security
    
    # Store user overrides from environment if provided
    _LEVERAGE_OVERRIDE = os.getenv('LEVERAGE')
    _MAX_POSITION_SIZE_OVERRIDE = os.getenv('MAX_POSITION_SIZE')
    _RISK_PER_TRADE_OVERRIDE = os.getenv('RISK_PER_TRADE')
    _MIN_PROFIT_THRESHOLD_OVERRIDE = os.getenv('MIN_PROFIT_THRESHOLD')
    
    # Trading Configuration - apply user overrides immediately if provided, otherwise will be auto-configured
    LEVERAGE = _safe_parse_int(_LEVERAGE_OVERRIDE, 'LEVERAGE') if _LEVERAGE_OVERRIDE else None
    MAX_POSITION_SIZE = _safe_parse_float(_MAX_POSITION_SIZE_OVERRIDE, 'MAX_POSITION_SIZE') if _MAX_POSITION_SIZE_OVERRIDE else None
    RISK_PER_TRADE = _safe_parse_float(_RISK_PER_TRADE_OVERRIDE, 'RISK_PER_TRADE') if _RISK_PER_TRADE_OVERRIDE else None
    MIN_PROFIT_THRESHOLD = _safe_parse_float(_MIN_PROFIT_THRESHOLD_OVERRIDE, 'MIN_PROFIT_THRESHOLD') if _MIN_PROFIT_THRESHOLD_OVERRIDE else None
    
    # Bot Parameters - Optimal defaults for best performance and safety
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))  # 60s = optimal balance (not too fast to avoid rate limits, not too slow to miss opportunities)
    POSITION_UPDATE_INTERVAL = int(float(os.getenv('POSITION_UPDATE_INTERVAL', '3.0')))  # 3s (reduced from 5s, 40% faster trailing stops, responsive without rate limiting)
    LIVE_LOOP_INTERVAL = float(os.getenv('LIVE_LOOP_INTERVAL', '0.1'))  # 100ms = truly live monitoring, fast response to market changes
    TRAILING_STOP_PERCENTAGE = float(os.getenv('TRAILING_STOP_PERCENTAGE', '0.02'))  # 2% trailing stop = industry standard, balances protection vs noise
    MAX_OPEN_POSITIONS = int(os.getenv('MAX_OPEN_POSITIONS', '3'))  # 3 positions = balanced diversification without overextension
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '20'))  # 20 workers = fast parallel scanning while staying under API rate limits
    CACHE_DURATION = int(os.getenv('CACHE_DURATION', '300'))  # 5 min cache for scanning (live data always used for trading)
    STALE_DATA_MULTIPLIER = int(os.getenv('STALE_DATA_MULTIPLIER', '2'))  # 2x CHECK_INTERVAL = reasonable tolerance for opportunity data
    
    # DCA Strategy Configuration
    ENABLE_DCA = os.getenv('ENABLE_DCA', 'true').lower() in ('true', '1', 'yes')
    DCA_ENTRY_ENABLED = os.getenv('DCA_ENTRY_ENABLED', 'true').lower() in ('true', '1', 'yes')
    DCA_ACCUMULATION_ENABLED = os.getenv('DCA_ACCUMULATION_ENABLED', 'true').lower() in ('true', '1', 'yes')
    DCA_NUM_ENTRIES = int(os.getenv('DCA_NUM_ENTRIES', '3'))  # Number of DCA entries
    DCA_CONFIDENCE_THRESHOLD = float(os.getenv('DCA_CONFIDENCE_THRESHOLD', '0.70'))  # Use DCA for signals below this confidence (smarter: 70%)
    
    # Hedging Strategy Configuration
    ENABLE_HEDGING = os.getenv('ENABLE_HEDGING', 'true').lower() in ('true', '1', 'yes')
    HEDGE_DRAWDOWN_THRESHOLD = float(os.getenv('HEDGE_DRAWDOWN_THRESHOLD', '0.10'))  # Hedge at 10% drawdown
    HEDGE_VOLATILITY_THRESHOLD = float(os.getenv('HEDGE_VOLATILITY_THRESHOLD', '0.08'))  # Hedge at 8% volatility
    HEDGE_CORRELATION_THRESHOLD = float(os.getenv('HEDGE_CORRELATION_THRESHOLD', '0.70'))  # Hedge at 70% concentration
    
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
    def _apply_override_or_auto_configure(cls, override_var, config_attr_name, auto_config_func, logger, param_name, format_func=None):
        """
        Helper method to apply user override or auto-configure a parameter
        
        Args:
            override_var: The cached override string from environment (e.g., cls._LEVERAGE_OVERRIDE)
            config_attr_name: Name of the config attribute (e.g., 'LEVERAGE')
            auto_config_func: Function that returns the auto-configured value
            logger: Logger instance
            param_name: Display name of the parameter (e.g., 'LEVERAGE')
            format_func: Optional function to format the value for logging (e.g., lambda x: f"{x}x")
        """
        current_value = getattr(cls, config_attr_name)
        
        # If user provided an override and it was successfully parsed, use it
        if override_var and current_value is not None:
            formatted = format_func(current_value) if format_func else current_value
            logger.info(f"📌 Using user-defined {param_name}: {formatted}")
        # Otherwise, auto-configure
        elif not override_var or current_value is None:
            auto_value = auto_config_func()
            setattr(cls, config_attr_name, auto_value)
            formatted = format_func(auto_value) if format_func else auto_value
            logger.info(f"🤖 Auto-configured {param_name}: {formatted}")
        # If override exists but parsing failed, warn and auto-configure
        elif override_var and current_value is None:
            logger.warning(f"⚠️  Invalid {param_name} value in .env, using auto-configuration")
            auto_value = auto_config_func()
            setattr(cls, config_attr_name, auto_value)
            formatted = format_func(auto_value) if format_func else auto_value
            logger.info(f"🤖 Auto-configured {param_name}: {formatted}")
    
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
        
        # LEVERAGE: Apply user override or auto-configure based on balance
        def auto_leverage():
            # Smart leverage based on balance - MORE CONSERVATIVE (smaller accounts = lower leverage for safety)
            if available_balance < 100:
                return 4  # Micro account - very conservative (was 5)
            elif available_balance < 1000:
                return 6  # Small account - conservative (was 7)
            elif available_balance < 10000:
                return 8  # Medium account - balanced (was 10)
            elif available_balance < 100000:
                return 10  # Large account - moderate (was 12)
            else:
                return 12  # Very large account - moderate-aggressive (was 15)
        
        cls._apply_override_or_auto_configure(
            cls._LEVERAGE_OVERRIDE, 'LEVERAGE', auto_leverage, logger, 'LEVERAGE',
            format_func=lambda x: f"{x}x (balance: ${available_balance:.2f})" if not cls._LEVERAGE_OVERRIDE else f"{x}x"
        )
        
        # MAX_POSITION_SIZE: Apply user override or auto-configure based on balance
        def auto_max_position():
            # Max position size as percentage of balance
            if available_balance < 100:
                size = available_balance * 0.3  # 30% max for micro accounts
            elif available_balance < 1000:
                size = available_balance * 0.4  # 40% max for small accounts
            elif available_balance < 10000:
                size = available_balance * 0.5  # 50% max for medium accounts
            else:
                size = available_balance * 0.6  # 60% max for large accounts
            # Ensure reasonable min/max bounds
            return max(10, min(size, 50000))
        
        cls._apply_override_or_auto_configure(
            cls._MAX_POSITION_SIZE_OVERRIDE, 'MAX_POSITION_SIZE', auto_max_position, logger, 'MAX_POSITION_SIZE',
            format_func=lambda x: f"${x:.2f} (balance: ${available_balance:.2f})" if not cls._MAX_POSITION_SIZE_OVERRIDE else f"${x:.2f}"
        )
        
        # RISK_PER_TRADE: Apply user override or auto-configure based on balance
        def auto_risk():
            # Risk per trade - smaller for larger accounts (relative risk management)
            if available_balance < 100:
                return 0.01  # 1% risk for micro accounts (be very careful)
            elif available_balance < 1000:
                return 0.015  # 1.5% risk for small accounts
            elif available_balance < 10000:
                return 0.02  # 2% risk for medium accounts
            elif available_balance < 100000:
                return 0.025  # 2.5% risk for large accounts
            else:
                return 0.03  # 3% risk for very large accounts
        
        cls._apply_override_or_auto_configure(
            cls._RISK_PER_TRADE_OVERRIDE, 'RISK_PER_TRADE', auto_risk, logger, 'RISK_PER_TRADE',
            format_func=lambda x: f"{x:.2%} (balance: ${available_balance:.2f})" if not cls._RISK_PER_TRADE_OVERRIDE else f"{x:.2%}"
        )
        
        # MIN_PROFIT_THRESHOLD: Apply user override or auto-configure based on balance
        def auto_min_profit():
            # Min profit threshold - must cover trading fees (maker 0.02% + taker 0.06% = ~0.08-0.12% round-trip)
            # Plus provide meaningful profit after fees
            # Typical round-trip trading cost: ~0.1% (0.001)
            trading_fee_buffer = 0.0012  # 0.12% to cover round-trip fees with small buffer
            
            if available_balance < 100:
                # Micro accounts need higher threshold due to fixed minimums and slippage
                return trading_fee_buffer + 0.008  # 0.12% fees + 0.8% profit = 0.92%
            elif available_balance < 1000:
                # Small accounts 
                return trading_fee_buffer + 0.006  # 0.12% fees + 0.6% profit = 0.72%
            else:
                # Medium+ accounts
                return trading_fee_buffer + 0.005  # 0.12% fees + 0.5% profit = 0.62%
        
        cls._apply_override_or_auto_configure(
            cls._MIN_PROFIT_THRESHOLD_OVERRIDE, 'MIN_PROFIT_THRESHOLD', auto_min_profit, logger, 'MIN_PROFIT_THRESHOLD',
            format_func=lambda x: f"{x:.2%} (balance: ${available_balance:.2f}, includes ~0.12% trading fees)" if not cls._MIN_PROFIT_THRESHOLD_OVERRIDE else f"{x:.2%}"
        )
    
    @classmethod
    def validate(cls):
        """
        Validate that required configuration is set and parameters are within safe limits
        
        SAFETY: Enhanced validation to prevent catastrophic configuration errors
        """
        from logger import Logger
        logger = Logger.get_logger()
        
        # Use enhanced config validator for comprehensive checks
        try:
            from config_validator import ConfigValidator
            is_valid, messages = ConfigValidator.validate_config()
            
            # Log validation messages
            for msg in messages:
                if msg.startswith("WARNING:"):
                    logger.warning(msg)
                else:
                    logger.error(msg)
            
            if not is_valid:
                raise ValueError("Configuration validation failed. Check logs for details.")
        except ImportError:
            logger.debug("config_validator module not found, using legacy validation")
            # Fallback to legacy validation
            pass
        
        # Legacy validation (kept for backward compatibility)
        # Check API credentials
        if not cls.API_KEY or not cls.API_SECRET or not cls.API_PASSPHRASE:
            raise ValueError("KuCoin API credentials are required. Please set them in .env file")
        
        # SAFETY: Validate numerical parameters are within safe bounds
        if cls.LEVERAGE is not None:
            if not (1 <= cls.LEVERAGE <= 20):
                raise ValueError(f"LEVERAGE must be between 1 and 20, got {cls.LEVERAGE}")
        
        if cls.MAX_POSITION_SIZE is not None:
            if cls.MAX_POSITION_SIZE <= 0:
                raise ValueError(f"MAX_POSITION_SIZE must be positive, got {cls.MAX_POSITION_SIZE}")
            if cls.MAX_POSITION_SIZE > 1000000:  # $1M sanity check
                raise ValueError(f"MAX_POSITION_SIZE seems unreasonably large: ${cls.MAX_POSITION_SIZE}")
        
        if cls.RISK_PER_TRADE is not None:
            if not (0.001 <= cls.RISK_PER_TRADE <= 0.10):  # 0.1% to 10%
                raise ValueError(f"RISK_PER_TRADE must be between 0.001 and 0.10, got {cls.RISK_PER_TRADE}")
        
        if cls.MAX_OPEN_POSITIONS < 1 or cls.MAX_OPEN_POSITIONS > 20:
            raise ValueError(f"MAX_OPEN_POSITIONS must be between 1 and 20, got {cls.MAX_OPEN_POSITIONS}")
        
        if cls.TRAILING_STOP_PERCENTAGE <= 0 or cls.TRAILING_STOP_PERCENTAGE > 0.50:  # Max 50%
            raise ValueError(f"TRAILING_STOP_PERCENTAGE must be between 0 and 0.50, got {cls.TRAILING_STOP_PERCENTAGE}")
        
        if cls.CHECK_INTERVAL < 10 or cls.CHECK_INTERVAL > 3600:  # 10s to 1h
            raise ValueError(f"CHECK_INTERVAL must be between 10 and 3600 seconds, got {cls.CHECK_INTERVAL}")
        
        # SAFETY: Warn about aggressive settings
        if cls.LEVERAGE is not None and cls.LEVERAGE > 15:
            logger.warning(f"⚠️  HIGH LEVERAGE WARNING: {cls.LEVERAGE}x leverage is very risky!")
        
        if cls.RISK_PER_TRADE is not None and cls.RISK_PER_TRADE > 0.05:
            logger.warning(f"⚠️  HIGH RISK WARNING: {cls.RISK_PER_TRADE:.1%} risk per trade is aggressive!")
        
        return True
