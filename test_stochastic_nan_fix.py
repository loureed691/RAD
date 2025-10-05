"""
Test case for Stochastic Oscillator NaN handling bug fix

This test verifies that the bot correctly handles edge cases where
the Stochastic Oscillator returns NaN values (when high == low).
"""
import sys
import pandas as pd
import numpy as np
from indicators import Indicators
from signals import SignalGenerator


def test_stochastic_nan_with_flat_data():
    """Test that stochastic NaN is handled when price data is flat"""
    print("\nTesting stochastic NaN handling with flat price data...")
    
    # Create flat price data (high == low for all candles)
    flat_data = []
    for i in range(100):
        flat_data.append([
            1000000000000 + i * 60000,  # timestamp
            100.0,  # open
            100.0,  # high (same as low - causes NaN)
            100.0,  # low
            100.0,  # close
            1000.0  # volume
        ])
    
    # Calculate indicators
    df = Indicators.calculate_all(flat_data)
    assert not df.empty, "DataFrame should not be empty"
    
    # Get latest indicators
    indicators = Indicators.get_latest_indicators(df)
    
    # Check that stochastic values are not NaN (should be filled with 50.0)
    stoch_k = indicators['stoch_k']
    stoch_d = indicators['stoch_d']
    
    print(f"  Stochastic K: {stoch_k}")
    print(f"  Stochastic D: {stoch_d}")
    
    assert not pd.isna(stoch_k), "Stochastic K should not be NaN"
    assert not pd.isna(stoch_d), "Stochastic D should not be NaN"
    assert stoch_k == 50.0, "Stochastic K should default to 50.0 (neutral)"
    assert stoch_d == 50.0, "Stochastic D should default to 50.0 (neutral)"
    
    print("  ✓ Stochastic values are not NaN (filled with neutral 50.0)")
    
    return True


def test_stochastic_nan_in_signal_generation():
    """Test that signal generator works correctly when stochastic was originally NaN"""
    print("\nTesting signal generation with originally-NaN stochastic data...")
    
    # Create flat price data
    flat_data = []
    for i in range(100):
        flat_data.append([
            1000000000000 + i * 60000,
            100.0, 100.0, 100.0, 100.0, 1000.0
        ])
    
    # Calculate indicators (stochastic will be filled to 50.0)
    df = Indicators.calculate_all(flat_data)
    indicators = Indicators.get_latest_indicators(df)
    
    # Create signal generator
    signal_gen = SignalGenerator()
    
    # Generate signal - should not crash
    try:
        signal, confidence, reasons = signal_gen.generate_signal(df)
        
        print(f"  Signal: {signal}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Stochastic in reasons: {'stochastic' in reasons}")
        
        # Signal should be generated without error
        assert signal in ['BUY', 'SELL', 'HOLD'], f"Invalid signal: {signal}"
        assert 0.0 <= confidence <= 1.0, f"Invalid confidence: {confidence}"
        
        # With neutral stochastic (50.0), it shouldn't trigger stochastic signals
        # (needs <20 or >80 to trigger)
        assert 'stochastic' not in reasons, "Stochastic signals shouldn't trigger with neutral value"
        
        print("  ✓ Signal generation works correctly with neutral stochastic values")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Signal generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stochastic_with_normal_data():
    """Test that stochastic still works correctly with normal price data"""
    print("\nTesting stochastic with normal price data...")
    
    # Create normal price data with variation
    normal_data = []
    base_price = 100.0
    for i in range(100):
        # Add some price variation
        variation = 5.0 * (i % 10) / 10.0
        price = base_price + variation
        
        normal_data.append([
            1000000000000 + i * 60000,
            price,           # open
            price + 1.0,     # high
            price - 1.0,     # low
            price,           # close
            1000.0           # volume
        ])
    
    # Calculate indicators
    df = Indicators.calculate_all(normal_data)
    indicators = Indicators.get_latest_indicators(df)
    
    # Check that stochastic values are calculated normally
    stoch_k = indicators['stoch_k']
    stoch_d = indicators['stoch_d']
    
    print(f"  Stochastic K: {stoch_k:.2f}")
    print(f"  Stochastic D: {stoch_d:.2f}")
    
    assert not pd.isna(stoch_k), "Stochastic K should be calculated"
    assert not pd.isna(stoch_d), "Stochastic D should be calculated"
    
    # Stochastic should be a valid value between 0 and 100
    assert 0.0 <= stoch_k <= 100.0, f"Stochastic K out of range: {stoch_k}"
    assert 0.0 <= stoch_d <= 100.0, f"Stochastic D out of range: {stoch_d}"
    
    print("  ✓ Stochastic calculated correctly with normal data")
    
    return True


def test_position_manager_division_guard():
    """Test that position_manager has defensive checks for division by zero"""
    print("\nTesting position_manager division by zero guard...")
    
    # Read the position_manager.py file and check for the guard
    with open('position_manager.py', 'r') as f:
        content = f.read()
    
    # Look for the fix on line 229
    # Should have: if initial_distance > 0:
    if 'if calculated_tp > max_tp:' in content:
        # Find the line after this condition
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'if calculated_tp > max_tp:' in line:
                # Check next few lines for the guard
                next_lines = '\n'.join(lines[i:i+3])
                if 'if initial_distance > 0:' in next_lines:
                    print("  ✓ Division by zero guard found at line ~229")
                    return True
                else:
                    print(f"  ✗ Division by zero guard NOT found")
                    print(f"  Next lines:\n{next_lines}")
                    return False
    
    print("  ✗ Could not find target code block")
    return False


def main():
    """Run all stochastic NaN fix tests"""
    print("=" * 60)
    print("Testing Stochastic Oscillator NaN Handling Fix")
    print("=" * 60)
    
    tests = [
        ("Stochastic NaN with flat data", test_stochastic_nan_with_flat_data),
        ("Signal generation with NaN stochastic", test_stochastic_nan_in_signal_generation),
        ("Stochastic with normal data", test_stochastic_with_normal_data),
        ("Position manager division guard", test_position_manager_division_guard),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  ✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"  ✗ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{len(tests)} passed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All stochastic NaN fix tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
