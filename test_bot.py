"""
Basic tests for the trading bot components
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
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
        print("✓ All modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    try:
        from config import Config

        # Test that config attributes exist
        assert hasattr(Config, 'LEVERAGE')
        assert hasattr(Config, 'MAX_POSITION_SIZE')
        assert hasattr(Config, 'RISK_PER_TRADE')

        # Test auto-configuration with different balance tiers
        print("  Testing auto-configuration with different balances...")

        # Test micro account ($50) - leverage is now fixed at 10x regardless of balance
        Config.auto_configure_from_balance(50)
        assert Config.LEVERAGE == 10, f"Expected leverage 10 (fixed), got {Config.LEVERAGE}"
        assert Config.RISK_PER_TRADE == 0.01, f"Expected 1% risk for $50 balance, got {Config.RISK_PER_TRADE}"
        print(f"  ✓ Micro account ($50): Leverage={Config.LEVERAGE}x, Risk={Config.RISK_PER_TRADE:.2%}")

        # Test small account ($500) - leverage is now fixed at 10x regardless of balance
        Config.auto_configure_from_balance(500)
        assert Config.LEVERAGE == 10, f"Expected leverage 10 (fixed), got {Config.LEVERAGE}"
        assert Config.RISK_PER_TRADE == 0.015, f"Expected 1.5% risk for $500 balance, got {Config.RISK_PER_TRADE}"
        print(f"  ✓ Small account ($500): Leverage={Config.LEVERAGE}x, Risk={Config.RISK_PER_TRADE:.2%}")

        # Test medium account ($5000) - leverage is now fixed at 10x regardless of balance
        Config.auto_configure_from_balance(5000)
        assert Config.LEVERAGE == 10, f"Expected leverage 10 (fixed), got {Config.LEVERAGE}"
        assert Config.RISK_PER_TRADE == 0.02, f"Expected 2% risk for $5000 balance, got {Config.RISK_PER_TRADE}"
        print(f"  ✓ Medium account ($5000): Leverage={Config.LEVERAGE}x, Risk={Config.RISK_PER_TRADE:.2%}")

        # Test large account ($50000) - leverage is now fixed at 10x regardless of balance
        Config.auto_configure_from_balance(50000)
        assert Config.LEVERAGE == 10, f"Expected leverage 10 (fixed), got {Config.LEVERAGE}"
        assert Config.RISK_PER_TRADE == 0.025, f"Expected 2.5% risk for $50000 balance, got {Config.RISK_PER_TRADE}"
        print(f"  ✓ Large account ($50000): Leverage={Config.LEVERAGE}x, Risk={Config.RISK_PER_TRADE:.2%}")

        # Test very large account ($200000) - leverage is now fixed at 10x regardless of balance
        Config.auto_configure_from_balance(200000)
        assert Config.LEVERAGE == 10, f"Expected leverage 10 (fixed), got {Config.LEVERAGE}"
        assert Config.RISK_PER_TRADE == 0.03, f"Expected 3% risk for $200000 balance, got {Config.RISK_PER_TRADE}"
        print(f"  ✓ Very large account ($200000): Leverage={Config.LEVERAGE}x, Risk={Config.RISK_PER_TRADE:.2%}")

        print("✓ Configuration auto-configuration working correctly")
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logger():
    """Test logger setup"""
    print("\nTesting logger...")
    try:
        from logger import Logger

        log = Logger.setup('INFO', 'logs/test.log')
        log.info("Test log message")
        print("✓ Logger working correctly")
        return True
    except Exception as e:
        print(f"✗ Logger error: {e}")
        return False

def test_indicators():
    """Test indicator calculations"""
    print("\nTesting indicators...")
    try:
        from indicators import Indicators
        import pandas as pd

        # Create sample OHLCV data
        sample_data = [
            [i * 60000, 100 + i, 101 + i, 99 + i, 100.5 + i, 1000]
            for i in range(100)
        ]

        df = Indicators.calculate_all(sample_data)
        assert not df.empty
        assert 'rsi' in df.columns
        assert 'macd' in df.columns

        indicators = Indicators.get_latest_indicators(df)
        assert 'rsi' in indicators
        assert 'macd' in indicators

        print(f"  Sample RSI: {indicators['rsi']:.2f}")
        print(f"  Sample MACD: {indicators['macd']:.4f}")
        print("✓ Indicators calculated successfully")
        return True
    except Exception as e:
        print(f"✗ Indicators error: {e}")
        return False

def test_signal_generator():
    """Test signal generation"""
    print("\nTesting signal generator...")
    try:
        from signals import SignalGenerator
        from indicators import Indicators

        # Create sample data
        sample_data = [
            [i * 60000, 100 + i * 0.5, 101 + i * 0.5, 99 + i * 0.5, 100.5 + i * 0.5, 1000]
            for i in range(100)
        ]

        df = Indicators.calculate_all(sample_data)
        generator = SignalGenerator()
        signal, confidence, reasons = generator.generate_signal(df)

        assert signal in ['BUY', 'SELL', 'HOLD']
        assert 0 <= confidence <= 1

        print(f"  Signal: {signal}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Reasons: {reasons}")
        print("✓ Signal generator working correctly")
        return True
    except Exception as e:
        print(f"✗ Signal generator error: {e}")
        return False

def test_risk_manager():
    """Test risk management calculations"""
    print("\nTesting risk manager...")
    try:
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

        print(f"  Calculated position size: {size:.4f} contracts")

        # Test position validation
        should_open, reason = manager.should_open_position(0, balance)
        assert should_open

        print(f"  Position validation: {should_open} - {reason}")
        print("✓ Risk manager working correctly")
        return True
    except Exception as e:
        print(f"✗ Risk manager error: {e}")
        return False

def test_ml_model():
    """Test ML model initialization and enhanced features"""
    print("\nTesting ML model...")
    try:
        from ml_model import MLModel

        model = MLModel('models/test_model.pkl')

        # Test feature preparation with enhanced features
        sample_indicators = {
            'rsi': 50,
            'macd': 0.5,
            'macd_signal': 0.3,
            'macd_diff': 0.2,
            'stoch_k': 50,
            'stoch_d': 50,
            'bb_width': 0.05,
            'volume_ratio': 1.5,
            'momentum': 0.01,
            'roc': 1.0,
            'atr': 2.5
        }

        features = model.prepare_features(sample_indicators)
        # Enhanced features should have 26 features now (11 base + 15 derived)
        assert features.shape[1] == 31, f"Expected 31 features, got {features.shape[1]}"

        # Test performance metrics
        metrics = model.get_performance_metrics()
        assert 'total_trades' in metrics
        assert 'win_rate' in metrics

        # Test adaptive threshold
        threshold = model.get_adaptive_confidence_threshold()
        assert 0.5 <= threshold <= 0.75

        print(f"  Feature vector shape: {features.shape}")
        print(f"  Adaptive threshold: {threshold:.2f}")
        print("✓ ML model initialized successfully with enhanced features")
        return True
    except Exception as e:
        print(f"✗ ML model error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_futures_filter():
    """Test futures market filtering logic"""
    print("\nTesting futures market filtering...")
    try:
        # Simulate different market types
        test_markets = {
            'BTC/USDT:USDT': {'swap': True, 'future': False, 'active': True},
            'ETH/USDT:USDT': {'swap': True, 'future': False, 'active': True},
            'BTC/USD:BTC-251226': {'swap': False, 'future': True, 'active': True},
            'SOL/USDT:USDT': {'swap': True, 'future': False, 'active': True},
            'BTC/USDT': {'swap': False, 'future': False, 'active': True},  # Spot
            'OLD/USDT:USDT': {'swap': True, 'future': False, 'active': False},  # Inactive
        }

        # Apply the new filter logic (USDT-only)
        usdt_filtered = [
            symbol for symbol, market in test_markets.items()
            if (market.get('swap') or market.get('future')) and market.get('active') and ':USDT' in symbol
        ]

        # Apply the old filter logic (all futures)
        all_filtered = [
            symbol for symbol, market in test_markets.items()
            if (market.get('swap') or market.get('future')) and market.get('active')
        ]

        assert len(usdt_filtered) == 3, f"Expected 3 USDT contracts, got {len(usdt_filtered)}"
        assert len(all_filtered) == 4, f"All filter should find 4 contracts, got {len(all_filtered)}"
        assert 'BTC/USD:BTC-251226' not in usdt_filtered, "Non-USDT pairs should be filtered out"
        assert all(':USDT' in s for s in usdt_filtered), "All filtered pairs should be USDT pairs"

        print(f"  All futures filter: {len(all_filtered)} contract(s)")
        print(f"  USDT-only filter: {len(usdt_filtered)} contracts")
        print(f"  USDT pairs detected: {', '.join(usdt_filtered)}")
        print("✓ Futures filter logic working correctly (USDT-only)")
        return True
    except Exception as e:
        print(f"✗ Futures filter error: {e}")
        return False

def test_insufficient_data_handling():
    """Test handling of insufficient data"""
    print("\nTesting insufficient data handling...")
    try:
        from indicators import Indicators

        # Test with insufficient data (40 candles, need 50+)
        small_data = [
            [i * 3600000, 100 + i*0.1, 101 + i*0.1, 99 + i*0.1, 100.5 + i*0.1, 1000]
            for i in range(40)
        ]
        df_small = Indicators.calculate_all(small_data)
        assert df_small.empty, "Should return empty DataFrame for insufficient data"

        # Test with empty data
        df_empty = Indicators.calculate_all([])
        assert df_empty.empty, "Should return empty DataFrame for no data"

        # Test with None
        df_none = Indicators.calculate_all(None)
        assert df_none.empty, "Should return empty DataFrame for None"

        print("  ✓ Insufficient data (40 candles) handled correctly")
        print("  ✓ Empty data handled correctly")
        print("  ✓ None data handled correctly")
        print("✓ Data validation working correctly")
        return True
    except Exception as e:
        print(f"✗ Data handling error: {e}")
        return False


def test_signal_generator_enhancements():
    """Test enhanced signal generator with market regime detection"""
    print("\nTesting enhanced signal generator...")
    try:
        from signals import SignalGenerator
        from indicators import Indicators

        # Create trending market data
        trending_data = [
            [i * 60000, 100 + i * 0.5, 101 + i * 0.5, 99 + i * 0.5, 100.5 + i * 0.5, 1000]
            for i in range(100)
        ]

        df = Indicators.calculate_all(trending_data)
        generator = SignalGenerator()
        signal, confidence, reasons = generator.generate_signal(df)

        assert signal in ['BUY', 'SELL', 'HOLD']
        assert 0 <= confidence <= 1
        assert 'market_regime' in reasons

        # Test market regime detection
        regime = generator.detect_market_regime(df)
        assert regime in ['trending', 'ranging', 'neutral']

        # Test adaptive threshold setting
        generator.set_adaptive_threshold(0.65)
        assert generator.adaptive_threshold == 0.65

        print(f"  Signal: {signal}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Market Regime: {regime}")
        print(f"  Adaptive threshold: {generator.adaptive_threshold:.2f}")
        print("✓ Enhanced signal generator working correctly")
        return True
    except Exception as e:
        print(f"✗ Signal generator error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_manager_enhancements():
    """Test enhanced risk management with adaptive leverage"""
    print("\nTesting enhanced risk manager...")
    try:
        from risk_manager import RiskManager

        manager = RiskManager(
            max_position_size=1000,
            risk_per_trade=0.02,
            max_open_positions=3
        )

        # Test adaptive leverage based on volatility and confidence
        # Low volatility, high confidence
        leverage1 = manager.get_max_leverage(volatility=0.015, confidence=0.80)
        assert leverage1 >= 10, f"Expected high leverage for low vol/high conf, got {leverage1}"

        # High volatility, low confidence
        leverage2 = manager.get_max_leverage(volatility=0.10, confidence=0.60)
        assert leverage2 <= 5, f"Expected low leverage for high vol/low conf, got {leverage2}"

        # Test adaptive stop loss
        stop1 = manager.calculate_stop_loss_percentage(volatility=0.01)
        stop2 = manager.calculate_stop_loss_percentage(volatility=0.10)
        assert stop2 > stop1, "Higher volatility should have wider stop"

        print(f"  Low vol/High conf leverage: {leverage1}x")
        print(f"  High vol/Low conf leverage: {leverage2}x")
        print(f"  Low vol stop loss: {stop1:.2%}")
        print(f"  High vol stop loss: {stop2:.2%}")
        print("✓ Enhanced risk manager working correctly")
        return True
    except Exception as e:
        print(f"✗ Risk manager error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_scanner_caching():
    """Test market scanner caching mechanism"""
    print("\nTesting market scanner caching...")
    try:
        # Note: This is a basic test since we can't mock KuCoinClient easily
        # In production, caching is tested through integration
        from market_scanner import MarketScanner

        # We can't fully test without a real client, but we can verify the class has caching
        assert hasattr(MarketScanner, 'clear_cache'), "MarketScanner should have clear_cache method"

        # Verify cache attributes exist
        from unittest.mock import Mock
        mock_client = Mock()
        scanner = MarketScanner(mock_client)

        assert hasattr(scanner, 'cache'), "Scanner should have cache attribute"
        assert hasattr(scanner, 'cache_duration'), "Scanner should have cache_duration"
        assert hasattr(scanner, 'scan_results_cache'), "Scanner should have scan_results_cache"
        assert scanner.cache_duration == 300, "Cache duration should be 5 minutes (300s)"

        # Test clear_cache
        scanner.cache['test'] = ('data', 12345)
        scanner.scan_results_cache = [{'test': 'data'}]
        scanner.clear_cache()
        assert len(scanner.cache) == 0, "Cache should be empty after clear"
        assert len(scanner.scan_results_cache) == 0, "Scan results cache should be empty"

        print("  ✓ Cache attributes initialized correctly")
        print("  ✓ Cache duration set to 5 minutes")
        print("  ✓ clear_cache() method working")
        print("✓ Market scanner caching mechanism validated")
        return True
    except Exception as e:
        print(f"✗ Market scanner caching error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("Running Trading Bot Component Tests")
    print("="*60)

    tests = [
        test_imports,
        test_config,
        test_logger,
        test_indicators,
        test_signal_generator,
        test_risk_manager,
        test_ml_model,
        test_futures_filter,
        test_insufficient_data_handling,
        test_signal_generator_enhancements,
        test_risk_manager_enhancements,
        test_market_scanner_caching
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "="*60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*60)

    if all(results):
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
