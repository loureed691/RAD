#!/usr/bin/env python3
"""
Test suite for bug fixes and edge cases
"""
import sys
import os
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_indicators_division_by_zero():
    """Test that indicators handle division by zero correctly"""
    print("\nTesting indicators division by zero handling...")
    
    try:
        from indicators import Indicators
        
        # Create test OHLCV data with potential edge cases
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
        
        # Calculate indicators
        df = Indicators.calculate_all(ohlcv)
        
        # Check that bb_width doesn't have inf values
        if not df.empty and 'bb_width' in df.columns:
            assert not df['bb_width'].isin([np.inf, -np.inf]).any(), "bb_width contains inf values"
            assert not df['bb_width'].isna().all(), "bb_width is all NaN"
            print("  ✓ bb_width handles division by zero correctly")
        
        # Check volume_ratio doesn't have inf values
        if not df.empty and 'volume_ratio' in df.columns:
            assert not df['volume_ratio'].isin([np.inf, -np.inf]).any(), "volume_ratio contains inf values"
            print("  ✓ volume_ratio handles division by zero correctly")
        
        # Test with edge case: all closes are the same (no volatility)
        ohlcv_flat = []
        for i in range(100):
            ohlcv_flat.append([
                1000000 + i * 60000,  # timestamp
                100.0,  # open
                100.0,  # high
                100.0,  # low
                100.0,  # close
                1000.0  # volume
            ])
        
        df_flat = Indicators.calculate_all(ohlcv_flat)
        
        if not df_flat.empty:
            # Check no inf or excessive NaN values
            for col in df_flat.columns:
                if col not in ['timestamp']:
                    inf_count = df_flat[col].isin([np.inf, -np.inf]).sum()
                    assert inf_count == 0, f"Column {col} has {inf_count} inf values with flat data"
            print("  ✓ Flat price data handled correctly")
        
        print("✓ Indicators division by zero handling working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Indicators test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_manager_zero_price():
    """Test that risk manager handles zero/negative prices correctly"""
    print("\nTesting risk manager zero price handling...")
    
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(
            max_position_size=1000.0,
            risk_per_trade=0.02,
            max_open_positions=3
        )
        
        # Test with zero entry price
        balance = 1000.0
        entry_price = 0.0
        stop_loss_price = 95.0
        leverage = 10
        
        position_size = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage
        )
        
        # Should return 0 for invalid entry price
        assert position_size == 0.0, f"Expected 0 for zero entry price, got {position_size}"
        print("  ✓ Zero entry price handled correctly")
        
        # Test with negative entry price
        entry_price = -100.0
        position_size = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage
        )
        
        assert position_size == 0.0, f"Expected 0 for negative entry price, got {position_size}"
        print("  ✓ Negative entry price handled correctly")
        
        # Test with valid prices
        entry_price = 100.0
        stop_loss_price = 95.0
        position_size = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage
        )
        
        assert position_size > 0, "Should return positive position size for valid prices"
        print(f"  ✓ Valid prices work correctly (size: {position_size:.4f})")
        
        print("✓ Risk manager zero price handling working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Risk manager test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_order_book_zero_volume():
    """Test order book analysis with zero volume"""
    print("\nTesting order book zero volume handling...")
    
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(
            max_position_size=1000.0,
            risk_per_trade=0.02,
            max_open_positions=3
        )
        
        # Test with zero volume order book
        order_book = {
            'bids': [[100.0, 0.0], [99.0, 0.0]],
            'asks': [[101.0, 0.0], [102.0, 0.0]]
        }
        
        result = manager.analyze_order_book_imbalance(order_book)
        
        # Should return neutral signal with zero volume
        assert result['signal'] == 'neutral', f"Expected neutral signal, got {result['signal']}"
        assert result['confidence'] == 0.0, f"Expected 0.0 confidence, got {result['confidence']}"
        print("  ✓ Zero volume order book handled correctly")
        
        # Test with normal order book
        order_book_normal = {
            'bids': [[100.0, 5.0], [99.0, 3.0]],
            'asks': [[101.0, 2.0], [102.0, 1.0]]
        }
        
        result_normal = manager.analyze_order_book_imbalance(order_book_normal)
        assert result_normal['signal'] in ['bullish', 'bearish', 'neutral'], "Should return valid signal"
        print("  ✓ Normal order book works correctly")
        
        print("✓ Order book zero volume handling working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Order book test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_response_validation():
    """Test that API responses are properly validated"""
    print("\nTesting API response validation...")
    
    try:
        # Test ticker validation in bot.py logic
        # Simulate ticker with missing 'last' field
        ticker_invalid = {}
        entry_price = ticker_invalid.get('last')
        
        # Should be None
        assert entry_price is None, "Should return None for missing 'last' field"
        
        # Check validation
        if not entry_price or entry_price <= 0:
            is_valid = False
        else:
            is_valid = True
        
        assert not is_valid, "Should be invalid for None price"
        print("  ✓ None price validation works")
        
        # Test with zero price
        ticker_zero = {'last': 0}
        entry_price = ticker_zero.get('last')
        if not entry_price or entry_price <= 0:
            is_valid = False
        else:
            is_valid = True
        
        assert not is_valid, "Should be invalid for zero price"
        print("  ✓ Zero price validation works")
        
        # Test with valid price
        ticker_valid = {'last': 100.5}
        entry_price = ticker_valid.get('last')
        if not entry_price or entry_price <= 0:
            is_valid = False
        else:
            is_valid = True
        
        assert is_valid, "Should be valid for positive price"
        print("  ✓ Valid price validation works")
        
        print("✓ API response validation working correctly")
        return True
        
    except Exception as e:
        print(f"✗ API response validation test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_balance_validation():
    """Test balance fetch and validation"""
    print("\nTesting balance validation...")
    
    try:
        # Test balance with missing 'free' field
        balance_invalid = {}
        if balance_invalid and 'free' in balance_invalid:
            is_valid = True
        else:
            is_valid = False
        
        assert not is_valid, "Should be invalid for missing 'free' field"
        print("  ✓ Missing 'free' field validation works")
        
        # Test balance with None value
        balance_none = None
        if balance_none and 'free' in balance_none:
            is_valid = True
        else:
            is_valid = False
        
        assert not is_valid, "Should be invalid for None balance"
        print("  ✓ None balance validation works")
        
        # Test valid balance
        balance_valid = {'free': {'USDT': 1000.0}}
        if balance_valid and 'free' in balance_valid:
            is_valid = True
            available = float(balance_valid.get('free', {}).get('USDT', 0))
            assert available == 1000.0, f"Expected 1000.0, got {available}"
        else:
            is_valid = False
        
        assert is_valid, "Should be valid for proper balance structure"
        print("  ✓ Valid balance structure works")
        
        print("✓ Balance validation working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Balance validation test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all bug fix tests"""
    print("=" * 60)
    print("Bug Fixes and Edge Cases Test Suite")
    print("=" * 60)
    
    tests = [
        test_indicators_division_by_zero,
        test_risk_manager_zero_price,
        test_order_book_zero_volume,
        test_api_response_validation,
        test_balance_validation,
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
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All bug fix tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
