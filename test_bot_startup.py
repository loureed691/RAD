#!/usr/bin/env python3
"""
Test bot startup and configuration to ensure live bot is functional
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

def test_bot_imports():
    """Test that bot module can be imported"""
    import bot
    assert hasattr(bot, 'TradingBot')
    assert hasattr(bot, 'main')

def test_bot_initialization_with_mock():
    """Test bot can initialize with mocked KuCoin client"""
    from bot import TradingBot
    from config import Config
    
    # Set test credentials
    Config.API_KEY = 'test_key'
    Config.API_SECRET = 'test_secret'
    Config.API_PASSPHRASE = 'test_pass'
    
    # Mock the KuCoin client to avoid network calls
    with patch('bot.KuCoinClient') as MockClient:
        mock_instance = Mock()
        mock_instance.get_balance.return_value = {'free': {'USDT': 1000.0}}
        mock_instance.verify_clock_sync_if_needed.return_value = True
        MockClient.return_value = mock_instance
        
        # Mock position manager's sync_existing_positions to return 0 (no existing positions)
        with patch('bot.MarketScanner'), \
             patch('bot.PositionManager') as MockPosManager, \
             patch('bot.RiskManager'), \
             patch('bot.MLModel'), \
             patch('bot.AdvancedAnalytics'), \
             patch('bot.get_monitor'), \
             patch('bot.AdvancedRiskManager2026'), \
             patch('bot.MarketMicrostructure2026'), \
             patch('bot.AdaptiveStrategySelector2026'), \
             patch('bot.AdvancedPerformanceMetrics2026'):
            
            # Configure PositionManager mock
            mock_pos_instance = Mock()
            mock_pos_instance.sync_existing_positions.return_value = 0
            MockPosManager.return_value = mock_pos_instance
            
            # This should not raise any exceptions
            bot_instance = TradingBot()
            
            assert bot_instance is not None
            assert hasattr(bot_instance, 'client')
            assert hasattr(bot_instance, 'scanner')
            assert hasattr(bot_instance, 'position_manager')
            assert hasattr(bot_instance, 'risk_manager')
            assert hasattr(bot_instance, 'ml_model')

def test_start_script_check_dependencies():
    """Test that start.py can check dependencies"""
    from start import check_dependencies
    
    # Should return True since all dependencies are installed
    assert check_dependencies() == True

def test_config_auto_configuration():
    """Test auto-configuration with different balances"""
    from config import Config
    
    # Test with different balance tiers
    test_cases = [
        (50, 4, 0.01),      # Micro: $50 -> 4x leverage, 1% risk
        (500, 6, 0.015),    # Small: $500 -> 6x leverage, 1.5% risk
        (5000, 8, 0.02),    # Medium: $5000 -> 8x leverage, 2% risk
        (50000, 10, 0.025), # Large: $50000 -> 10x leverage, 2.5% risk
        (200000, 12, 0.03), # Very large: $200000 -> 12x leverage, 3% risk
    ]
    
    for balance, expected_leverage, expected_risk in test_cases:
        Config.auto_configure_from_balance(balance)
        assert Config.LEVERAGE == expected_leverage, \
            f"Expected leverage {expected_leverage} for ${balance}, got {Config.LEVERAGE}"
        assert Config.RISK_PER_TRADE == expected_risk, \
            f"Expected risk {expected_risk} for ${balance}, got {Config.RISK_PER_TRADE}"

def test_config_validation():
    """Test configuration validation"""
    from config import Config
    
    # Test that config has all required attributes
    assert hasattr(Config, 'API_KEY')
    assert hasattr(Config, 'API_SECRET')
    assert hasattr(Config, 'API_PASSPHRASE')
    assert hasattr(Config, 'ENABLE_WEBSOCKET')
    assert hasattr(Config, 'CHECK_INTERVAL')
    assert hasattr(Config, 'POSITION_UPDATE_INTERVAL')
    assert hasattr(Config, 'TRAILING_STOP_PERCENTAGE')
    assert hasattr(Config, 'MAX_OPEN_POSITIONS')
    
    # Test validate method exists
    assert hasattr(Config, 'validate')
    
    # Config validation should work (even with test credentials)
    try:
        Config.validate()
        # If it doesn't raise, validation passed (or has reasonable defaults)
        assert True
    except Exception as e:
        # Some validation errors are expected with test credentials
        assert 'API' in str(e) or 'key' in str(e).lower()

def test_kucoin_client_import():
    """Test KuCoin client can be imported and has required methods"""
    from kucoin_client import KuCoinClient
    
    # Check class has required methods
    assert hasattr(KuCoinClient, 'get_balance')
    assert hasattr(KuCoinClient, 'get_ticker')
    assert hasattr(KuCoinClient, 'get_ohlcv')
    assert hasattr(KuCoinClient, 'get_open_positions')
    # Check for order creation methods
    assert hasattr(KuCoinClient, 'create_market_order')
    assert hasattr(KuCoinClient, 'create_limit_order')
    assert hasattr(KuCoinClient, 'close_position')
    assert hasattr(KuCoinClient, 'cancel_order')

def test_ccxt_version():
    """Test that CCXT is installed and KuCoin Futures is available"""
    import ccxt
    
    # Check CCXT version is recent
    version = ccxt.__version__
    major, minor, patch = map(int, version.split('.'))
    assert major >= 4, f"CCXT version {version} is too old, need 4.x or higher"
    
    # Check KuCoin Futures is available
    assert 'kucoinfutures' in ccxt.exchanges
    
    # Test we can instantiate (without API keys)
    exchange = ccxt.kucoinfutures()
    assert exchange.id == 'kucoinfutures'
    assert exchange.has['future'] == True or exchange.has['swap'] == True

def test_all_components_importable():
    """Test that all bot components can be imported"""
    import config
    import logger
    import kucoin_client
    import indicators
    import signals
    import market_scanner
    import ml_model
    import position_manager
    import risk_manager
    import monitor
    import bot
    
    # 2026 features
    import advanced_risk_2026
    import market_microstructure_2026
    import adaptive_strategy_2026
    import performance_metrics_2026
    
    # Optional components
    import kucoin_websocket
    import advanced_analytics
    import performance_monitor
    
    # All imports successful
    assert True

def test_logger_setup():
    """Test logger can be set up"""
    from logger import Logger
    
    log = Logger.setup('INFO', 'logs/test_startup.log')
    assert log is not None
    
    # Test logging works
    log.info("Test log message")
    log.debug("Test debug message")
    log.warning("Test warning message")
    
    # Test specialized loggers
    position_logger = Logger.setup_specialized_logger('TestPositionLogger', 'logs/test_positions.log', 'DEBUG')
    assert position_logger is not None

def test_indicators_calculation():
    """Test indicators can calculate on sample data"""
    from indicators import Indicators
    
    # Create sample OHLCV data
    sample_data = [
        [i * 60000, 100 + i, 101 + i, 99 + i, 100.5 + i, 1000]
        for i in range(100)
    ]
    
    df = Indicators.calculate_all(sample_data)
    assert not df.empty
    assert 'rsi' in df.columns
    assert 'macd' in df.columns
    # Bollinger bands use bb_high, bb_mid, bb_low naming
    assert 'bb_high' in df.columns or 'bb_upper' in df.columns
    assert 'bb_low' in df.columns or 'bb_lower' in df.columns

def test_signal_generation():
    """Test signal generator works"""
    from signals import SignalGenerator
    from indicators import Indicators
    
    sample_data = [
        [i * 60000, 100 + i * 0.5, 101 + i * 0.5, 99 + i * 0.5, 100.5 + i * 0.5, 1000]
        for i in range(100)
    ]
    
    df = Indicators.calculate_all(sample_data)
    generator = SignalGenerator()
    signal, confidence, reasons = generator.generate_signal(df)
    
    assert signal in ['BUY', 'SELL', 'HOLD']
    assert 0 <= confidence <= 1
    assert isinstance(reasons, dict)

def test_risk_manager_calculations():
    """Test risk manager performs calculations"""
    from risk_manager import RiskManager
    
    manager = RiskManager(
        max_position_size=1000,
        risk_per_trade=0.02,
        max_open_positions=3
    )
    
    # Test position size calculation
    balance = 10000
    entry_price = 100
    stop_loss_price = 95
    leverage = 10
    
    size = manager.calculate_position_size(balance, entry_price, stop_loss_price, leverage)
    assert size > 0
    assert isinstance(size, (int, float))

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
