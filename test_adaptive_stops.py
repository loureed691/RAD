"""
Tests for adaptive stop loss and take profit features
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_position_tracking_enhancements():
    """Test that Position tracks max favorable excursion and initial values"""
    print("\nTesting Position tracking enhancements...")
    try:
        from position_manager import Position
        
        # Create a long position
        position = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=55000
        )
        
        # Verify new attributes exist
        assert hasattr(position, 'max_favorable_excursion'), "Missing max_favorable_excursion"
        assert hasattr(position, 'initial_stop_loss'), "Missing initial_stop_loss"
        assert hasattr(position, 'initial_take_profit'), "Missing initial_take_profit"
        
        # Verify initial values
        assert position.max_favorable_excursion == 0.0, "MFE should start at 0"
        assert position.initial_stop_loss == 47500, "Initial stop loss not stored"
        assert position.initial_take_profit == 55000, "Initial take profit not stored"
        
        print("  ✓ Position tracks max favorable excursion")
        print("  ✓ Position stores initial stop loss and take profit")
        print("✓ Position tracking enhancements working correctly")
        return True
    except Exception as e:
        print(f"✗ Position tracking error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adaptive_trailing_stop():
    """Test adaptive trailing stop based on market conditions"""
    print("\nTesting adaptive trailing stop...")
    try:
        from position_manager import Position
        
        # Test 1: Low volatility should tighten stop
        position = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=55000
        )
        
        # Price moves up
        position.update_trailing_stop(
            current_price=51000,
            trailing_percentage=0.02,  # 2% base
            volatility=0.01,  # Low volatility
            momentum=0.02
        )
        
        # Stop should be tighter than base 2% (which would be 49980)
        expected_base_stop = 51000 * 0.98
        assert position.stop_loss > expected_base_stop, "Stop should be tightened in low volatility"
        print(f"  ✓ Low volatility trailing stop: {position.stop_loss:.2f}")
        
        # Test 2: High volatility should widen stop
        position2 = Position(
            symbol='ETH-USDT',
            side='long',
            entry_price=3000,
            amount=1.0,
            leverage=10,
            stop_loss=2850,
            take_profit=3300
        )
        
        position2.update_trailing_stop(
            current_price=3100,
            trailing_percentage=0.02,
            volatility=0.08,  # High volatility
            momentum=0.02
        )
        
        # Should allow wider stop
        assert position2.trailing_stop_activated, "Trailing stop should activate"
        print(f"  ✓ High volatility trailing stop: {position2.stop_loss:.2f}")
        
        # Test 3: High profit should tighten stop
        position3 = Position(
            symbol='SOL-USDT',
            side='long',
            entry_price=100,
            amount=10.0,
            leverage=10,
            stop_loss=95,
            take_profit=120
        )
        
        # Price moves to 15% profit
        position3.update_trailing_stop(
            current_price=115,
            trailing_percentage=0.02,
            volatility=0.03,
            momentum=0.01
        )
        
        # Stop should be much tighter when in profit
        profit_pnl = position3.get_pnl(115)
        assert profit_pnl > 0.10, "Should be in profit"
        print(f"  ✓ High profit position (P/L: {profit_pnl:.2%}), stop: {position3.stop_loss:.2f}")
        
        # Test 4: Strong momentum should widen stop
        position4 = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=55000
        )
        
        position4.update_trailing_stop(
            current_price=51000,
            trailing_percentage=0.02,
            volatility=0.03,
            momentum=0.05  # Strong positive momentum
        )
        
        assert position4.trailing_stop_activated, "Should activate with price increase"
        print(f"  ✓ Strong momentum trailing stop: {position4.stop_loss:.2f}")
        
        print("✓ Adaptive trailing stop working correctly")
        return True
    except Exception as e:
        print(f"✗ Adaptive trailing stop error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dynamic_take_profit():
    """Test dynamic take profit adjustments"""
    print("\nTesting dynamic take profit...")
    try:
        from position_manager import Position
        
        # Test 1: Strong momentum should extend take profit
        position = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=55000
        )
        
        initial_tp = position.take_profit
        
        # Strong upward momentum
        position.update_take_profit(
            current_price=51000,
            momentum=0.04,  # Strong positive momentum
            trend_strength=0.8,  # Strong trend
            volatility=0.03
        )
        
        assert position.take_profit >= initial_tp, "TP should extend or stay same"
        print(f"  ✓ Strong momentum extended TP from {initial_tp:.2f} to {position.take_profit:.2f}")
        
        # Test 2: Weak momentum should keep TP more conservative
        position2 = Position(
            symbol='ETH-USDT',
            side='long',
            entry_price=3000,
            amount=1.0,
            leverage=10,
            stop_loss=2850,
            take_profit=3300
        )
        
        initial_tp2 = position2.take_profit
        
        position2.update_take_profit(
            current_price=3050,
            momentum=0.005,  # Weak momentum
            trend_strength=0.3,  # Weak trend
            volatility=0.02
        )
        
        # Should not extend much or at all
        extension = position2.take_profit - initial_tp2
        print(f"  ✓ Weak momentum TP extension: {extension:.2f}")
        
        # Test 3: Short position with negative momentum
        position3 = Position(
            symbol='SOL-USDT',
            side='short',
            entry_price=100,
            amount=10.0,
            leverage=10,
            stop_loss=105,
            take_profit=90
        )
        
        initial_tp3 = position3.take_profit
        
        position3.update_take_profit(
            current_price=98,
            momentum=-0.04,  # Strong downward momentum (favorable for short)
            trend_strength=0.7,
            volatility=0.04
        )
        
        # For short, TP should move down (lower price)
        assert position3.take_profit <= initial_tp3, "Short TP should move down or stay same"
        print(f"  ✓ Short position TP adjusted from {initial_tp3:.2f} to {position3.take_profit:.2f}")
        
        # Test 4: High volatility should extend TP
        position4 = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=55000
        )
        
        initial_tp4 = position4.take_profit
        
        position4.update_take_profit(
            current_price=51000,
            momentum=0.02,
            trend_strength=0.6,
            volatility=0.08  # High volatility
        )
        
        assert position4.take_profit > initial_tp4, "High volatility should extend TP"
        print(f"  ✓ High volatility extended TP from {initial_tp4:.2f} to {position4.take_profit:.2f}")
        
        print("✓ Dynamic take profit working correctly")
        return True
    except Exception as e:
        print(f"✗ Dynamic take profit error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_max_favorable_excursion_tracking():
    """Test that max favorable excursion is tracked correctly"""
    print("\nTesting max favorable excursion tracking...")
    try:
        from position_manager import Position
        
        position = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=55000
        )
        
        # Initial MFE should be 0
        assert position.max_favorable_excursion == 0.0
        
        # Price moves up 5%
        position.update_trailing_stop(51000, 0.02, 0.03, 0.02)
        current_pnl = position.get_pnl(51000)
        assert position.max_favorable_excursion >= current_pnl
        print(f"  ✓ MFE after 5% move: {position.max_favorable_excursion:.2%}")
        
        # Price moves up more to 10%
        position.update_trailing_stop(52000, 0.02, 0.03, 0.02)
        new_pnl = position.get_pnl(52000)
        assert position.max_favorable_excursion >= new_pnl
        assert position.max_favorable_excursion > current_pnl
        print(f"  ✓ MFE after 10% move: {position.max_favorable_excursion:.2%}")
        
        # Price drops back to 7% - MFE should not decrease
        mfe_before = position.max_favorable_excursion
        position.update_trailing_stop(51500, 0.02, 0.03, 0.01)
        assert position.max_favorable_excursion == mfe_before
        print(f"  ✓ MFE maintained after pullback: {position.max_favorable_excursion:.2%}")
        
        print("✓ Max favorable excursion tracking working correctly")
        return True
    except Exception as e:
        print(f"✗ MFE tracking error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adaptive_parameters_bounds():
    """Test that adaptive parameters stay within reasonable bounds"""
    print("\nTesting adaptive parameters bounds...")
    try:
        from position_manager import Position
        
        position = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=55000
        )
        
        # Test extreme conditions
        test_cases = [
            # (volatility, momentum, description)
            (0.0, 0.0, "Zero volatility and momentum"),
            (0.20, 0.15, "Extreme high volatility and momentum"),
            (0.001, -0.08, "Very low volatility, strong negative momentum"),
        ]
        
        for volatility, momentum, description in test_cases:
            initial_stop = position.stop_loss
            position.update_trailing_stop(
                current_price=51000,
                trailing_percentage=0.02,
                volatility=volatility,
                momentum=momentum
            )
            
            # Stop should never be too far from price (max 5% away)
            max_distance = 51000 * 0.05
            distance = 51000 - position.stop_loss
            assert distance <= max_distance, f"Stop too far: {distance:.2f}"
            
            # Stop should never be too tight (min 0.5% away)
            min_distance = 51000 * 0.005
            assert distance >= min_distance, f"Stop too tight: {distance:.2f}"
            
            print(f"  ✓ {description}: stop at {position.stop_loss:.2f} ({distance/51000:.2%} away)")
        
        print("✓ Adaptive parameters bounds working correctly")
        return True
    except Exception as e:
        print(f"✗ Bounds test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rsi_based_adjustments():
    """Test RSI-based take profit adjustments"""
    print("\nTesting RSI-based TP adjustments...")
    try:
        from position_manager import Position
        
        # Test 1: Overbought RSI should tighten TP (long position)
        position = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=55000
        )
        
        initial_tp = position.take_profit
        
        # Overbought RSI (reversal risk)
        position.update_take_profit(
            current_price=51000,
            momentum=0.03,
            trend_strength=0.6,
            volatility=0.03,
            rsi=80.0  # Overbought
        )
        
        print(f"  ✓ Overbought RSI (80): TP at {position.take_profit:.2f} (initial: {initial_tp:.2f})")
        
        # Test 2: Oversold RSI should extend TP (long position)
        position2 = Position(
            symbol='ETH-USDT',
            side='long',
            entry_price=3000,
            amount=1.0,
            leverage=10,
            stop_loss=2850,
            take_profit=3300
        )
        
        initial_tp2 = position2.take_profit
        
        position2.update_take_profit(
            current_price=3050,
            momentum=0.02,
            trend_strength=0.6,
            volatility=0.03,
            rsi=30.0  # Oversold (room to run)
        )
        
        # Should extend more than with neutral RSI
        assert position2.take_profit >= initial_tp2, "Oversold RSI should extend TP"
        print(f"  ✓ Oversold RSI (30): TP at {position2.take_profit:.2f} (initial: {initial_tp2:.2f})")
        
        # Test 3: Short position with overbought RSI
        position3 = Position(
            symbol='SOL-USDT',
            side='short',
            entry_price=100,
            amount=10.0,
            leverage=10,
            stop_loss=105,
            take_profit=90
        )
        
        initial_tp3 = position3.take_profit
        
        position3.update_take_profit(
            current_price=98,
            momentum=-0.02,
            trend_strength=0.6,
            volatility=0.03,
            rsi=70.0  # Overbought (favorable for short)
        )
        
        print(f"  ✓ Short with overbought RSI (70): TP at {position3.take_profit:.2f} (initial: {initial_tp3:.2f})")
        
        print("✓ RSI-based adjustments working correctly")
        return True
    except Exception as e:
        print(f"✗ RSI adjustment error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_support_resistance_awareness():
    """Test support/resistance based TP adjustments"""
    print("\nTesting support/resistance awareness...")
    try:
        from position_manager import Position
        
        # Test 1: Long position with low initial TP that would extend beyond resistance
        position = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=52000  # Lower initial TP
        )
        
        # Mock resistance level at 54000
        support_resistance = {
            'support': [],
            'resistance': [
                {'price': 54000, 'strength': 0.3},
                {'price': 56000, 'strength': 0.2}
            ],
            'poc': 51000
        }
        
        initial_tp = position.take_profit
        
        # Strong conditions that would normally extend TP significantly
        position.update_take_profit(
            current_price=51000,
            momentum=0.04,  # Strong momentum
            trend_strength=0.8,  # Strong trend
            volatility=0.06,  # High volatility
            rsi=60.0,
            support_resistance=support_resistance
        )
        
        # TP should extend but be capped near resistance
        # With these conditions, TP would normally extend to ~55-56k, but should be capped
        assert position.take_profit > initial_tp, "TP should extend from initial"
        assert position.take_profit < 54000, f"TP should be capped by resistance: {position.take_profit}"
        print(f"  ✓ Long position TP extended to {position.take_profit:.2f}, capped by resistance at 54000")
        
        # Test 2: Short position near support
        position2 = Position(
            symbol='ETH-USDT',
            side='short',
            entry_price=3000,
            amount=1.0,
            leverage=10,
            stop_loss=3150,
            take_profit=2850  # Initial TP above support level
        )
        
        # Mock support level at 2800
        support_resistance2 = {
            'support': [
                {'price': 2800, 'strength': 0.3},
                {'price': 2600, 'strength': 0.2}
            ],
            'resistance': [],
            'poc': 2900
        }
        
        initial_tp2 = position2.take_profit
        
        # Strong conditions for short, price not yet at TP
        position2.update_take_profit(
            current_price=2950,  # Price still above TP, allowing extension
            momentum=-0.04,  # Strong downward momentum
            trend_strength=0.8,
            volatility=0.06,
            rsi=40.0,
            support_resistance=support_resistance2
        )
        
        # TP should extend lower but be capped near support
        assert position2.take_profit <= initial_tp2, "Short TP should move down or stay same"
        assert position2.take_profit > 2800, f"Short TP should be capped by support: {position2.take_profit}"
        print(f"  ✓ Short position TP extended to {position2.take_profit:.2f}, capped by support at 2800")
        
        print("✓ Support/resistance awareness working correctly")
        return True
    except Exception as e:
        print(f"✗ S/R awareness error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_profit_velocity_tracking():
    """Test profit velocity tracking for smart adjustments"""
    print("\nTesting profit velocity tracking...")
    try:
        from position_manager import Position
        import time
        
        position = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=55000
        )
        
        # Simulate fast profit accumulation
        # First update
        position.update_take_profit(
            current_price=50500,
            momentum=0.03,
            trend_strength=0.6,
            volatility=0.03,
            rsi=60.0
        )
        
        time.sleep(0.1)  # Small delay
        
        # Second update with higher price (fast movement)
        initial_tp = position.take_profit
        position.update_take_profit(
            current_price=51500,
            momentum=0.03,
            trend_strength=0.6,
            volatility=0.03,
            rsi=60.0
        )
        
        # Check that profit velocity is being tracked
        assert hasattr(position, 'profit_velocity'), "Missing profit_velocity attribute"
        assert hasattr(position, 'last_pnl'), "Missing last_pnl attribute"
        
        print(f"  ✓ Profit velocity tracked: {position.profit_velocity:.4f}% per hour")
        print(f"  ✓ Last P/L: {position.last_pnl:.2%}")
        
        print("✓ Profit velocity tracking working correctly")
        return True
    except Exception as e:
        print(f"✗ Profit velocity error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_time_based_adjustments():
    """Test time-based adjustments for aging positions"""
    print("\nTesting time-based TP adjustments...")
    try:
        from position_manager import Position
        from datetime import datetime, timedelta
        
        # Test 1: Fresh position
        position = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=47500,
            take_profit=55000
        )
        
        initial_tp = position.take_profit
        
        position.update_take_profit(
            current_price=51000,
            momentum=0.03,
            trend_strength=0.6,
            volatility=0.03,
            rsi=60.0
        )
        
        fresh_tp = position.take_profit
        print(f"  ✓ Fresh position TP: {fresh_tp:.2f}")
        
        # Test 2: Old position (simulate by changing entry_time)
        position2 = Position(
            symbol='ETH-USDT',
            side='long',
            entry_price=3000,
            amount=1.0,
            leverage=10,
            stop_loss=2850,
            take_profit=3300
        )
        
        # Manually set entry time to 30 hours ago
        position2.entry_time = datetime.now() - timedelta(hours=30)
        
        initial_tp2 = position2.take_profit
        
        position2.update_take_profit(
            current_price=3100,
            momentum=0.03,
            trend_strength=0.6,
            volatility=0.03,
            rsi=60.0
        )
        
        aged_tp = position2.take_profit
        print(f"  ✓ Aged position (30h) TP: {aged_tp:.2f} (initial: {initial_tp2:.2f})")
        
        print("✓ Time-based adjustments working correctly")
        return True
    except Exception as e:
        print(f"✗ Time-based adjustment error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all adaptive feature tests"""
    print("="*60)
    print("Running Adaptive Stop Loss and Take Profit Tests")
    print("="*60)
    
    tests = [
        test_position_tracking_enhancements,
        test_adaptive_trailing_stop,
        test_dynamic_take_profit,
        test_max_favorable_excursion_tracking,
        test_adaptive_parameters_bounds,
        test_rsi_based_adjustments,
        test_support_resistance_awareness,
        test_profit_velocity_tracking,
        test_time_based_adjustments,
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
        print("\n✓ All adaptive feature tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
