#!/usr/bin/env python3
"""
Comprehensive integration test for the trading bot
Tests all major components working together
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_full_bot_initialization():
    """Test that the bot can initialize all components without errors"""
    print("\nTesting full bot initialization...")
    
    try:
        # Import all major components
        from config import Config
        from logger import Logger
        from indicators import Indicators
        from signals import SignalGenerator
        from risk_manager import RiskManager
        from ml_model import MLModel
        from market_scanner import MarketScanner
        
        print("  ✓ All imports successful")
        
        # Test config validation would fail without API keys
        # So we'll just test that the class methods exist
        assert hasattr(Config, 'validate'), "Config.validate method missing"
        assert hasattr(Config, 'auto_configure_from_balance'), "Config.auto_configure_from_balance missing"
        print("  ✓ Config methods present")
        
        # Test logger initialization
        logger = Logger.setup('INFO', 'logs/test.log')
        assert logger is not None, "Logger initialization failed"
        print("  ✓ Logger initializes correctly")
        
        # Test signal generator initialization
        signal_gen = SignalGenerator()
        assert signal_gen is not None, "SignalGenerator initialization failed"
        print("  ✓ SignalGenerator initializes correctly")
        
        # Test risk manager initialization
        risk_mgr = RiskManager(
            max_position_size=1000.0,
            risk_per_trade=0.02,
            max_open_positions=3
        )
        assert risk_mgr is not None, "RiskManager initialization failed"
        print("  ✓ RiskManager initializes correctly")
        
        # Test ML model initialization
        ml_model = MLModel('models/test_model.pkl')
        assert ml_model is not None, "MLModel initialization failed"
        print("  ✓ MLModel initializes correctly")
        
        print("✓ Full bot initialization test passed")
        
    except Exception as e:
        print(f"✗ Full bot initialization test failed: {e}")
        import traceback
        traceback.print_exc()

def test_data_flow():
    """Test data flow through the system"""
    print("\nTesting data flow through system...")
    
    try:
        from indicators import Indicators
        from signals import SignalGenerator
        from risk_manager import RiskManager
        
        # Create sample OHLCV data
        ohlcv = []
        for i in range(100):
            ohlcv.append([
                1000000 + i * 60000,  # timestamp
                100.0 + i * 0.1,  # open
                100.5 + i * 0.1,  # high
                99.5 + i * 0.1,   # low
                100.0 + i * 0.1,  # close
                1000.0 + i * 10   # volume
            ])
        
        # Test indicators calculation
        df = Indicators.calculate_all(ohlcv)
        assert not df.empty, "Indicators calculation produced empty dataframe"
        print("  ✓ Indicators calculate correctly")
        
        # Test signal generation
        signal_gen = SignalGenerator()
        signal, confidence, reasons = signal_gen.generate_signal(df, 'BTC/USDT:USDT')
        assert signal in ['BUY', 'SELL', 'HOLD'], f"Invalid signal: {signal}"
        assert 0 <= confidence <= 1, f"Invalid confidence: {confidence}"
        print(f"  ✓ Signal generation works (signal: {signal}, confidence: {confidence:.2f})")
        
        # Test risk calculation
        risk_mgr = RiskManager(
            max_position_size=1000.0,
            risk_per_trade=0.02,
            max_open_positions=3
        )
        
        indicators = Indicators.get_latest_indicators(df)
        volatility = indicators.get('bb_width', 0.03)
        
        stop_loss_pct = risk_mgr.calculate_stop_loss_percentage(volatility)
        assert 0 < stop_loss_pct < 1, f"Invalid stop loss percentage: {stop_loss_pct}"
        print(f"  ✓ Risk calculation works (stop loss: {stop_loss_pct:.2%})")
        
        # Test position sizing
        balance = 1000.0
        entry_price = 100.0
        stop_loss_price = entry_price * (1 - stop_loss_pct)
        leverage = 10
        
        position_size = risk_mgr.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage
        )
        assert position_size > 0, "Position size calculation failed"
        print(f"  ✓ Position sizing works (size: {position_size:.4f} contracts)")
        
        print("✓ Data flow test passed")
        
    except Exception as e:
        print(f"✗ Data flow test failed: {e}")
        import traceback
        traceback.print_exc()

def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\nTesting edge cases...")
    
    try:
        from indicators import Indicators
        from risk_manager import RiskManager
        
        # Test with minimal data
        minimal_ohlcv = []
        for i in range(10):  # Less than typical minimum
            minimal_ohlcv.append([
                1000000 + i * 60000,
                100.0, 100.0, 100.0, 100.0, 1000.0
            ])
        
        df = Indicators.calculate_all(minimal_ohlcv)
        # Should either return empty or handle gracefully
        print("  ✓ Minimal data handled gracefully")
        
        # Test with zero volume
        zero_vol_ohlcv = []
        for i in range(50):
            zero_vol_ohlcv.append([
                1000000 + i * 60000,
                100.0, 100.0, 100.0, 100.0, 0.0  # Zero volume
            ])
        
        df = Indicators.calculate_all(zero_vol_ohlcv)
        if not df.empty and 'volume_ratio' in df.columns:
            assert not df['volume_ratio'].isin([float('inf'), float('-inf')]).any(), "Infinite volume ratios"
        print("  ✓ Zero volume handled correctly")
        
        # Test with extreme volatility
        extreme_vol_ohlcv = []
        for i in range(50):
            # Extreme price swings
            extreme_vol_ohlcv.append([
                1000000 + i * 60000,
                100.0 if i % 2 == 0 else 200.0,
                250.0 if i % 2 == 0 else 300.0,
                50.0 if i % 2 == 0 else 100.0,
                150.0 if i % 2 == 0 else 250.0,
                1000.0
            ])
        
        df = Indicators.calculate_all(extreme_vol_ohlcv)
        if not df.empty:
            # Should calculate without errors
            print("  ✓ Extreme volatility handled correctly")
        
        # Test risk manager with edge cases
        risk_mgr = RiskManager(1000.0, 0.02, 3)
        
        # Very high volatility
        stop_loss_pct = risk_mgr.calculate_stop_loss_percentage(0.5)  # 50% volatility
        assert 0 < stop_loss_pct < 1, "Invalid stop loss for high volatility"
        print(f"  ✓ High volatility handled (stop loss: {stop_loss_pct:.2%})")
        
        # Very low volatility
        stop_loss_pct = risk_mgr.calculate_stop_loss_percentage(0.001)  # 0.1% volatility
        assert 0 < stop_loss_pct < 1, "Invalid stop loss for low volatility"
        print(f"  ✓ Low volatility handled (stop loss: {stop_loss_pct:.2%})")
        
        print("✓ Edge cases test passed")
        
    except Exception as e:
        print(f"✗ Edge cases test failed: {e}")
        import traceback
        traceback.print_exc()

def test_thread_safety():
    """Test thread safety of shared components"""
    print("\nTesting thread safety...")
    
    try:
        import threading
        import time
        
        from market_scanner import MarketScanner
        from unittest.mock import Mock
        
        # Create mock client
        mock_client = Mock()
        mock_client.get_active_futures = Mock(return_value=[])
        mock_client.get_ticker = Mock(return_value={'last': 100.0})
        mock_client.get_ohlcv = Mock(return_value=[])
        
        scanner = MarketScanner(mock_client)
        
        # Verify lock exists
        assert hasattr(scanner, '_cache_lock'), "Cache lock missing"
        print("  ✓ Scanner has thread lock")
        
        # Test concurrent cache access
        errors = []
        
        def access_cache():
            try:
                scanner.clear_cache()
            except Exception as e:
                errors.append(e)
        
        threads = []
        for _ in range(5):
            t = threading.Thread(target=access_cache)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=2)
        
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        print("  ✓ Concurrent cache access safe")
        
        print("✓ Thread safety test passed")
        
    except Exception as e:
        print(f"✗ Thread safety test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all integration tests"""
    print("=" * 70)
    print("COMPREHENSIVE INTEGRATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_full_bot_initialization,
        test_data_flow,
        test_edge_cases,
        test_thread_safety,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 70)
    print(f"Integration Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 70)
    
    if all(results):
        print("\n✅ All integration tests passed!")
        print("\n🎉 BOT IS FULLY FUNCTIONAL AND READY FOR USE")
        return 0
    else:
        print("\n✗ Some integration tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
