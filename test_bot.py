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
        
        print(f"  Leverage: {Config.LEVERAGE}")
        print(f"  Max Position Size: {Config.MAX_POSITION_SIZE}")
        print(f"  Risk per Trade: {Config.RISK_PER_TRADE}")
        print("✓ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
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
    """Test ML model initialization"""
    print("\nTesting ML model...")
    try:
        from ml_model import MLModel
        
        model = MLModel('models/test_model.pkl')
        
        # Test feature preparation
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
        assert features.shape[1] == 11
        
        print(f"  Feature vector shape: {features.shape}")
        print("✓ ML model initialized successfully")
        return True
    except Exception as e:
        print(f"✗ ML model error: {e}")
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
        test_ml_model
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
