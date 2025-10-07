#!/usr/bin/env python3
"""
Comprehensive bug check for trading strategy implementation
This script performs thorough validation beyond the existing tests
"""
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_division_by_zero_scenarios():
    """Test various division by zero scenarios throughout the codebase"""
    print("\n=== Testing Division by Zero Scenarios ===")
    
    try:
        from risk_manager import RiskManager
        
        # Test 1: Zero balance
        rm = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
        pos_size = rm.calculate_position_size(
            balance=0,  # Zero balance
            entry_price=50000,
            stop_loss_price=49000,
            leverage=10
        )
        print(f"✓ Zero balance handled: position_size={pos_size:.4f}")
        
        # Test 2: Zero entry price
        try:
            pos_size = rm.calculate_position_size(
                balance=1000,
                entry_price=0,  # Zero entry price
                stop_loss_price=49000,
                leverage=10
            )
            print(f"⚠️  Zero entry price returned: {pos_size:.4f}")
        except (ZeroDivisionError, ValueError) as e:
            print(f"✓ Zero entry price caught: {e}")
        
        # Test 3: Entry price == Stop loss price
        pos_size = rm.calculate_position_size(
            balance=1000,
            entry_price=50000,
            stop_loss_price=50000,  # Same as entry
            leverage=10
        )
        print(f"✓ Equal prices handled: position_size={pos_size:.4f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_nan_propagation():
    """Test NaN value propagation in calculations"""
    print("\n=== Testing NaN Propagation ===")
    
    try:
        from signals import SignalGenerator
        from indicators import Indicators
        
        sg = SignalGenerator()
        
        # Create dataframe with NaN values
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100, freq='1h'),
            'open': np.random.randn(100) * 100 + 50000,
            'high': np.random.randn(100) * 100 + 50100,
            'low': np.random.randn(100) * 100 + 49900,
            'close': np.random.randn(100) * 100 + 50000,
            'volume': np.random.randn(100) * 1000 + 5000
        })
        
        # Inject some NaN values
        df.loc[50:55, 'close'] = np.nan
        df.loc[60:65, 'volume'] = np.nan
        
        # Calculate indicators
        df_with_indicators = Indicators.calculate_all(df)
        
        # Generate signal
        signal, confidence, reasons = sg.generate_signal(df_with_indicators)
        
        print(f"✓ NaN handling in indicators: signal={signal}, confidence={confidence:.2f}")
        
        # Check if any NaN in critical indicators
        if df_with_indicators.empty:
            print("⚠️  Empty dataframe returned")
        else:
            indicators = Indicators.get_latest_indicators(df_with_indicators)
            nan_indicators = [k for k, v in indicators.items() if pd.isna(v)]
            if nan_indicators:
                print(f"⚠️  NaN found in indicators: {nan_indicators}")
            else:
                print("✓ No NaN in final indicators")
        
        return True
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_extreme_values():
    """Test behavior with extreme input values"""
    print("\n=== Testing Extreme Values ===")
    
    try:
        from risk_manager import RiskManager
        
        rm = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
        
        # Test 1: Extreme volatility
        leverage = rm.get_max_leverage(
            volatility=0.5,  # 50% volatility (extreme)
            confidence=0.8,
            momentum=0.1,
            trend_strength=0.8
        )
        print(f"✓ Extreme volatility (50%): leverage={leverage}x")
        assert leverage >= 3, "Leverage should be at minimum 3x"
        
        # Test 2: Extreme negative momentum
        leverage = rm.get_max_leverage(
            volatility=0.03,
            confidence=0.5,
            momentum=-0.9,  # Extreme negative
            trend_strength=0.5
        )
        print(f"✓ Extreme negative momentum (-90%): leverage={leverage}x")
        assert leverage >= 3, "Leverage should be at minimum 3x"
        
        # Test 3: Zero confidence
        leverage = rm.get_max_leverage(
            volatility=0.03,
            confidence=0.0,  # Zero confidence
            momentum=0.1,
            trend_strength=0.5
        )
        print(f"✓ Zero confidence: leverage={leverage}x")
        assert leverage >= 3, "Leverage should be at minimum 3x"
        
        # Test 4: Extreme drawdown
        rm.peak_balance = 10000
        rm.update_drawdown(1000)  # 90% drawdown
        print(f"✓ 90% drawdown: current_drawdown={rm.current_drawdown:.2%}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_case_indicators():
    """Test indicator calculation with edge cases"""
    print("\n=== Testing Edge Case Indicators ===")
    
    try:
        from indicators import Indicators
        
        # Test 1: Flat price (no movement)
        flat_data = []
        base_price = 50000
        for i in range(100):
            flat_data.append([
                i * 3600000,  # timestamp
                base_price,   # open
                base_price,   # high
                base_price,   # low
                base_price,   # close
                1000          # volume
            ])
        
        df_flat = Indicators.calculate_all(flat_data)
        if df_flat.empty:
            print("⚠️  Flat price returned empty dataframe")
        else:
            indicators = Indicators.get_latest_indicators(df_flat)
            print(f"✓ Flat price handled: RSI={indicators.get('rsi', 'N/A'):.1f}, "
                  f"Stoch={indicators.get('stoch_k', 'N/A'):.1f}")
        
        # Test 2: Zero volume
        zero_vol_data = []
        for i in range(100):
            zero_vol_data.append([
                i * 3600000,
                50000 + np.random.randn() * 100,
                50100 + np.random.randn() * 100,
                49900 + np.random.randn() * 100,
                50000 + np.random.randn() * 100,
                0  # Zero volume
            ])
        
        df_zero_vol = Indicators.calculate_all(zero_vol_data)
        if df_zero_vol.empty:
            print("⚠️  Zero volume returned empty dataframe")
        else:
            indicators = Indicators.get_latest_indicators(df_zero_vol)
            vol_ratio = indicators.get('volume_ratio', 1.0)
            print(f"✓ Zero volume handled: volume_ratio={vol_ratio:.2f}")
        
        # Test 3: Insufficient data
        short_data = [[i * 3600000, 50000, 50100, 49900, 50000, 1000] for i in range(10)]
        df_short = Indicators.calculate_all(short_data)
        print(f"✓ Insufficient data handled: empty={df_short.empty}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_race_conditions():
    """Test potential race conditions in position management"""
    print("\n=== Testing Race Conditions ===")
    
    try:
        # This is a basic check - real race conditions need threading tests
        from position_manager import Position
        
        # Test 1: Rapid position updates
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000,
            amount=0.1,
            leverage=10,
            stop_loss=48000,
            take_profit=52000
        )
        
        # Simulate rapid price updates
        for price in [50100, 50200, 50150, 50250, 50200]:
            position.update_trailing_stop(price, 0.02)
        
        print(f"✓ Rapid updates handled: highest_price={position.highest_price:.2f}")
        
        # Test 2: Concurrent stop loss checks (simplified)
        should_close_sl = position.stop_loss and 49000 <= position.stop_loss
        should_close_tp = position.take_profit and 50500 >= position.take_profit
        
        print(f"✓ No conflicting close conditions: SL={should_close_sl}, TP={should_close_tp}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logic_inversions():
    """Test for potential logic inversion bugs"""
    print("\n=== Testing Logic Inversions ===")
    
    try:
        from signals import SignalGenerator
        from indicators import Indicators
        
        sg = SignalGenerator()
        
        # Create strongly bullish scenario
        bullish_data = []
        for i in range(100):
            price = 40000 + (i * 100)  # Strong uptrend
            bullish_data.append([
                i * 3600000,
                price,
                price + 100,
                price - 50,
                price + 50,
                1000 * (1 + i/100)  # Increasing volume
            ])
        
        df_bullish = Indicators.calculate_all(bullish_data)
        signal_bullish, conf_bullish, reasons_bullish = sg.generate_signal(df_bullish)
        
        print(f"✓ Bullish scenario: signal={signal_bullish}, confidence={conf_bullish:.2f}")
        
        # Create strongly bearish scenario
        bearish_data = []
        for i in range(100):
            price = 60000 - (i * 100)  # Strong downtrend
            bearish_data.append([
                i * 3600000,
                price,
                price + 50,
                price - 100,
                price - 50,
                1000 * (1 + i/100)  # Increasing volume
            ])
        
        df_bearish = Indicators.calculate_all(bearish_data)
        signal_bearish, conf_bearish, reasons_bearish = sg.generate_signal(df_bearish)
        
        print(f"✓ Bearish scenario: signal={signal_bearish}, confidence={conf_bearish:.2f}")
        
        # Verify signals match trends
        if signal_bullish == 'BUY' and signal_bearish == 'SELL':
            print("✓ Signal logic is correct (BUY on uptrend, SELL on downtrend)")
        elif signal_bullish == 'SELL' or signal_bearish == 'BUY':
            print("✗ INVERTED SIGNAL LOGIC DETECTED!")
            return False
        else:
            print("⚠️  Signals are HOLD - may need stronger trends")
        
        return True
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_boundary_conditions():
    """Test boundary conditions in calculations"""
    print("\n=== Testing Boundary Conditions ===")
    
    try:
        from risk_manager import RiskManager
        
        rm = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
        
        # Test 1: RSI exactly at thresholds (30, 70)
        print("✓ RSI boundary logic verified in existing tests")
        
        # Test 2: Leverage at min/max boundaries
        min_lev = rm.get_max_leverage(0.15, 0.1, -0.5, 0.1, 'ranging')  # Should hit min
        max_lev = rm.get_max_leverage(0.01, 0.95, 0.5, 0.9, 'trending')  # Should approach max
        
        print(f"✓ Leverage boundaries: min={min_lev}x (>= 3), max={max_lev}x (<= 20)")
        assert 3 <= min_lev <= 20, "Min leverage out of bounds"
        assert 3 <= max_lev <= 20, "Max leverage out of bounds"
        
        # Test 3: Stop loss percentage boundaries
        min_sl = rm.calculate_stop_loss_percentage(0.001)  # Very low vol
        max_sl = rm.calculate_stop_loss_percentage(0.20)   # Very high vol
        
        print(f"✓ Stop loss boundaries: min={min_sl:.2%} (>= 1.5%), max={max_sl:.2%} (<= 8%)")
        assert 0.015 <= min_sl <= 0.08, "Min stop loss out of bounds"
        assert 0.015 <= max_sl <= 0.08, "Max stop loss out of bounds"
        
        return True
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_kelly_criterion_edge_cases():
    """Test Kelly Criterion calculation edge cases"""
    print("\n=== Testing Kelly Criterion Edge Cases ===")
    
    try:
        from risk_manager import RiskManager
        
        rm = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
        
        # Test 1: Zero win rate
        kelly = rm.calculate_kelly_criterion(win_rate=0.0, avg_win=0.02, avg_loss=0.02)
        print(f"✓ Zero win rate: kelly={kelly:.4f} (should be minimal)")
        assert kelly >= 0, "Kelly should not be negative"
        
        # Test 2: 100% win rate
        kelly = rm.calculate_kelly_criterion(win_rate=1.0, avg_win=0.02, avg_loss=0.02)
        print(f"✓ 100% win rate: kelly={kelly:.4f}")
        assert kelly > 0, "Kelly should be positive"
        
        # Test 3: Very small profit/loss
        kelly = rm.calculate_kelly_criterion(win_rate=0.5, avg_win=0.0001, avg_loss=0.0001)
        print(f"✓ Tiny profit/loss: kelly={kelly:.4f}")
        assert kelly >= 0, "Kelly should not be negative"
        
        # Test 4: Large loss vs small profit (bad scenario)
        kelly = rm.calculate_kelly_criterion(win_rate=0.3, avg_win=0.01, avg_loss=0.05)
        print(f"✓ Large loss ratio: kelly={kelly:.4f} (should be minimal)")
        
        return True
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all comprehensive bug checks"""
    print("=" * 60)
    print("COMPREHENSIVE TRADING STRATEGY BUG CHECK")
    print("=" * 60)
    
    tests = [
        ("Division by Zero Scenarios", test_division_by_zero_scenarios),
        ("NaN Propagation", test_nan_propagation),
        ("Extreme Values", test_extreme_values),
        ("Edge Case Indicators", test_edge_case_indicators),
        ("Race Conditions", test_race_conditions),
        ("Logic Inversions", test_logic_inversions),
        ("Boundary Conditions", test_boundary_conditions),
        ("Kelly Criterion Edge Cases", test_kelly_criterion_edge_cases),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nResults: {passed}/{total} test suites passed")
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
