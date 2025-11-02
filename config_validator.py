"""
Configuration validation and schema enforcement for RAD Trading Bot

This module ensures all configuration values are valid and within safe ranges
to prevent misconfiguration that could lead to trading losses.
"""
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


class ConfigError(Exception):
    """Raised when configuration validation fails"""
    pass


class LogLevel(Enum):
    """Valid logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ConfigParameter:
    """Configuration parameter metadata"""
    name: str
    required: bool
    param_type: type
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default: Any = None
    description: str = ""
    sensitive: bool = False  # Mask in logs


class ConfigValidator:
    """Validates trading bot configuration against safety constraints"""
    
    # Define all configuration parameters with validation rules
    PARAMETERS = {
        # API Configuration (Required, Sensitive)
        'KUCOIN_API_KEY': ConfigParameter(
            name='KUCOIN_API_KEY',
            required=True,
            param_type=str,
            description='KuCoin API Key',
            sensitive=True
        ),
        'KUCOIN_API_SECRET': ConfigParameter(
            name='KUCOIN_API_SECRET',
            required=True,
            param_type=str,
            description='KuCoin API Secret',
            sensitive=True
        ),
        'KUCOIN_API_PASSPHRASE': ConfigParameter(
            name='KUCOIN_API_PASSPHRASE',
            required=True,
            param_type=str,
            description='KuCoin API Passphrase',
            sensitive=True
        ),
        
        # WebSocket Configuration
        'ENABLE_WEBSOCKET': ConfigParameter(
            name='ENABLE_WEBSOCKET',
            required=False,
            param_type=bool,
            default=True,
            description='Enable WebSocket for real-time data'
        ),
        
        # Trading Parameters (Auto-configured but can be overridden)
        'LEVERAGE': ConfigParameter(
            name='LEVERAGE',
            required=False,
            param_type=int,
            min_value=2,
            max_value=25,  # Updated range: 2-25x
            default=None,
            description='Trading leverage (2-25x, fixed at 10x by default)'
        ),
        'MAX_POSITION_SIZE': ConfigParameter(
            name='MAX_POSITION_SIZE',
            required=False,
            param_type=float,
            min_value=10.0,
            max_value=1000000.0,
            default=None,
            description='Maximum position size in USDT'
        ),
        'RISK_PER_TRADE': ConfigParameter(
            name='RISK_PER_TRADE',
            required=False,
            param_type=float,
            min_value=0.001,  # 0.1% minimum
            max_value=0.10,   # 10% maximum (very aggressive)
            default=None,
            description='Risk per trade as decimal (e.g., 0.02 = 2%)'
        ),
        'MIN_PROFIT_THRESHOLD': ConfigParameter(
            name='MIN_PROFIT_THRESHOLD',
            required=False,
            param_type=float,
            min_value=0.0001,  # 0.01% minimum
            max_value=0.50,    # 50% maximum
            default=None,
            description='Minimum profit threshold to enter trade'
        ),
        
        # Bot Timing Parameters
        'CHECK_INTERVAL': ConfigParameter(
            name='CHECK_INTERVAL',
            required=False,
            param_type=int,
            min_value=10,
            max_value=3600,
            default=60,
            description='Market scanning interval in seconds'
        ),
        'POSITION_UPDATE_INTERVAL': ConfigParameter(
            name='POSITION_UPDATE_INTERVAL',
            required=False,
            param_type=float,
            min_value=0.5,
            max_value=60.0,
            default=1.0,
            description='Position update interval in seconds'
        ),
        'LIVE_LOOP_INTERVAL': ConfigParameter(
            name='LIVE_LOOP_INTERVAL',
            required=False,
            param_type=float,
            min_value=0.01,
            max_value=10.0,
            default=0.05,
            description='Main loop sleep interval in seconds'
        ),
        'TRAILING_STOP_PERCENTAGE': ConfigParameter(
            name='TRAILING_STOP_PERCENTAGE',
            required=False,
            param_type=float,
            min_value=0.005,  # 0.5% minimum
            max_value=0.20,   # 20% maximum
            default=0.02,
            description='Trailing stop percentage'
        ),
        'MAX_OPEN_POSITIONS': ConfigParameter(
            name='MAX_OPEN_POSITIONS',
            required=False,
            param_type=int,
            min_value=1,
            max_value=20,
            default=3,
            description='Maximum concurrent positions'
        ),
        'MAX_WORKERS': ConfigParameter(
            name='MAX_WORKERS',
            required=False,
            param_type=int,
            min_value=1,
            max_value=50,
            default=8,
            description='Number of parallel workers for scanning'
        ),
        'CACHE_DURATION': ConfigParameter(
            name='CACHE_DURATION',
            required=False,
            param_type=int,
            min_value=60,
            max_value=3600,
            default=300,
            description='Cache duration in seconds'
        ),
        'STALE_DATA_MULTIPLIER': ConfigParameter(
            name='STALE_DATA_MULTIPLIER',
            required=False,
            param_type=int,
            min_value=1,
            max_value=10,
            default=2,
            description='Multiplier for max age of opportunity data'
        ),
        
        # Logging Configuration
        'LOG_LEVEL': ConfigParameter(
            name='LOG_LEVEL',
            required=False,
            param_type=str,
            default='INFO',
            description='Main log level'
        ),
        'LOG_FILE': ConfigParameter(
            name='LOG_FILE',
            required=False,
            param_type=str,
            default='logs/bot.log',
            description='Main log file path'
        ),
        'DETAILED_LOG_LEVEL': ConfigParameter(
            name='DETAILED_LOG_LEVEL',
            required=False,
            param_type=str,
            default='DEBUG',
            description='Detailed log level for specialized loggers'
        ),
        
        # ML Configuration
        'RETRAIN_INTERVAL': ConfigParameter(
            name='RETRAIN_INTERVAL',
            required=False,
            param_type=int,
            min_value=3600,   # 1 hour minimum
            max_value=604800,  # 1 week maximum
            default=86400,
            description='ML model retrain interval in seconds'
        ),
        'ML_MODEL_PATH': ConfigParameter(
            name='ML_MODEL_PATH',
            required=False,
            param_type=str,
            default='models/signal_model.pkl',
            description='ML model file path'
        ),
        
        # Reproducibility
        'RANDOM_SEED': ConfigParameter(
            name='RANDOM_SEED',
            required=False,
            param_type=int,
            min_value=0,
            max_value=999999,
            default=42,
            description='Random seed for reproducibility'
        ),
    }
    
    @classmethod
    def validate_config(cls, env_dict: Optional[Dict[str, str]] = None) -> Tuple[bool, List[str]]:
        """
        Validate configuration from environment variables or provided dict
        
        Args:
            env_dict: Optional dict of config values (uses os.environ if None)
            
        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        if env_dict is None:
            env_dict = dict(os.environ)
        
        errors = []
        warnings = []
        
        # Check required parameters
        for param_name, param in cls.PARAMETERS.items():
            if param.required:
                value = env_dict.get(param_name, '').strip()
                if not value or value in ('your_api_key_here', 'your_api_secret_here', 
                                         'your_api_passphrase_here'):
                    errors.append(
                        f"Required parameter '{param_name}' is missing or has placeholder value. "
                        f"Description: {param.description}"
                    )
        
        # Validate parameter types and ranges
        for param_name, param in cls.PARAMETERS.items():
            value_str = env_dict.get(param_name, '').strip()
            
            # Skip if not provided and not required
            if not value_str and not param.required:
                continue
            
            # Skip if empty (will use default)
            if not value_str:
                continue
            
            try:
                # Type conversion
                if param.param_type == bool:
                    value = value_str.lower() in ('true', '1', 'yes', 'on')
                elif param.param_type == int:
                    value = int(float(value_str))  # Handle "10.0" -> 10
                elif param.param_type == float:
                    value = float(value_str)
                else:
                    value = value_str
                
                # Range validation
                if param.param_type in (int, float):
                    if param.min_value is not None and value < param.min_value:
                        errors.append(
                            f"Parameter '{param_name}' value {value} is below minimum {param.min_value}"
                        )
                    if param.max_value is not None and value > param.max_value:
                        errors.append(
                            f"Parameter '{param_name}' value {value} exceeds maximum {param.max_value}"
                        )
                
                # Log level validation
                if param_name in ('LOG_LEVEL', 'DETAILED_LOG_LEVEL'):
                    if value not in [level.value for level in LogLevel]:
                        errors.append(
                            f"Parameter '{param_name}' has invalid value '{value}'. "
                            f"Must be one of: {[l.value for l in LogLevel]}"
                        )
                
            except (ValueError, TypeError) as e:
                errors.append(
                    f"Parameter '{param_name}' has invalid type. "
                    f"Expected {param.param_type.__name__}, got '{value_str}': {e}"
                )
        
        # Safety checks
        leverage = env_dict.get('LEVERAGE', '').strip()
        risk_per_trade = env_dict.get('RISK_PER_TRADE', '').strip()
        
        if leverage and risk_per_trade:
            try:
                lev = int(float(leverage))
                risk = float(risk_per_trade)
                
                # Warn if combined leverage and risk is very aggressive
                if lev * risk > 0.5:  # More than 50% of equity at risk
                    warnings.append(
                        f"WARNING: High risk configuration detected! "
                        f"Leverage ({lev}x) × Risk per trade ({risk:.1%}) = "
                        f"{lev * risk:.1%} of equity at risk. "
                        f"Consider reducing leverage or risk per trade."
                    )
            except (ValueError, TypeError):
                pass  # Already caught in type validation
        
        # Return validation results
        all_messages = errors + warnings
        is_valid = len(errors) == 0
        
        return is_valid, all_messages
    
    @classmethod
    def get_parameter_info(cls, param_name: str) -> Optional[ConfigParameter]:
        """Get metadata for a specific parameter"""
        return cls.PARAMETERS.get(param_name)
    
    @classmethod
    def list_parameters(cls) -> Dict[str, ConfigParameter]:
        """List all configuration parameters"""
        return cls.PARAMETERS.copy()
    
    @classmethod
    def generate_env_example(cls) -> str:
        """Generate .env.example content from parameter definitions"""
        lines = [
            "# RAD Trading Bot Configuration",
            "# Generated configuration template with validation rules",
            "# Copy this file to .env and fill in your values",
            "",
        ]
        
        # Group parameters by category
        categories = {
            'API Configuration': ['KUCOIN_API_KEY', 'KUCOIN_API_SECRET', 'KUCOIN_API_PASSPHRASE'],
            'WebSocket': ['ENABLE_WEBSOCKET'],
            'Trading Parameters': ['LEVERAGE', 'MAX_POSITION_SIZE', 'RISK_PER_TRADE', 'MIN_PROFIT_THRESHOLD'],
            'Bot Timing': ['CHECK_INTERVAL', 'POSITION_UPDATE_INTERVAL', 'LIVE_LOOP_INTERVAL', 
                          'TRAILING_STOP_PERCENTAGE', 'MAX_OPEN_POSITIONS', 'MAX_WORKERS',
                          'CACHE_DURATION', 'STALE_DATA_MULTIPLIER'],
            'Logging': ['LOG_LEVEL', 'LOG_FILE', 'DETAILED_LOG_LEVEL'],
            'Machine Learning': ['RETRAIN_INTERVAL', 'ML_MODEL_PATH'],
            'Reproducibility': ['RANDOM_SEED'],
        }
        
        for category, param_names in categories.items():
            lines.append(f"# {category}")
            lines.append("#" + "=" * (len(category) + 2))
            
            for param_name in param_names:
                param = cls.PARAMETERS.get(param_name)
                if not param:
                    continue
                
                # Add description
                lines.append(f"# {param.description}")
                
                # Add constraints
                constraints = []
                if param.required:
                    constraints.append("REQUIRED")
                if param.min_value is not None:
                    constraints.append(f"min: {param.min_value}")
                if param.max_value is not None:
                    constraints.append(f"max: {param.max_value}")
                if param.default is not None:
                    constraints.append(f"default: {param.default}")
                
                if constraints:
                    lines.append(f"# [{', '.join(constraints)}]")
                
                # Add parameter line
                if param.required:
                    if param.sensitive:
                        lines.append(f"{param_name}=your_{param_name.lower()}_here")
                    else:
                        lines.append(f"{param_name}=")
                else:
                    if param.default is not None:
                        lines.append(f"# {param_name}={param.default}")
                    else:
                        lines.append(f"# {param_name}=")
                
                lines.append("")
        
        return "\n".join(lines)


def validate_and_report() -> bool:
    """
    Validate current configuration and print report
    
    Returns:
        True if configuration is valid, False otherwise
    """
    is_valid, messages = ConfigValidator.validate_config()
    
    if messages:
        print("=" * 70)
        print("CONFIGURATION VALIDATION REPORT")
        print("=" * 70)
        
        for msg in messages:
            if msg.startswith("WARNING:"):
                print(f"⚠️  {msg}")
            else:
                print(f"❌ {msg}")
        
        print("=" * 70)
    
    if is_valid:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors - please fix before running")
    
    return is_valid


if __name__ == "__main__":
    # When run directly, validate current config
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--generate-example':
        # Generate .env.example
        content = ConfigValidator.generate_env_example()
        print(content)
    else:
        # Validate current configuration
        is_valid = validate_and_report()
        sys.exit(0 if is_valid else 1)
