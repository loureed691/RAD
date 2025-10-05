"""
Test for take profit extension bug fix
"""
import sys
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Mock the KuCoinClient before importing
sys.modules['kucoin_client'] = MagicMock()

from position_manager import Position

def test_short_position_tp_not_moving_away():
    """Test that SHORT position TP doesn't move away from current price"""
    print("\n" + "="*60)
    print("TEST 1: SHORT Position - TP should not move away from price")
    print("="*60)
    
    # Setup SHORT position
    entry_price = 100.0
    stop_loss_percentage = 0.05
    stop_loss = entry_price * (1 + stop_loss_percentage)  # 105
    take_profit = entry_price * (1 - stop_loss_percentage * 2)  # 90
    
    position = Position(
        symbol='BTCUSDT',
        side='short',
        entry_price=entry_price,
        amount=10.0,
        leverage=10,
        stop_loss=stop_loss,
        take_profit=take_profit
    )
    
    print(f"Initial state:")
    print(f"  Entry: {entry_price}, TP: {take_profit}")
    
    # Scenario 1: Price at 92, approaching TP
    # With strong momentum, tp_multiplier would be 1.5
    # Without fix: TP would move to 85 (further away)
    # With fix: TP should stay at 90 (not move away)
    current_price = 92.0
    print(f"\n1. Price drops to {current_price} (approaching TP at {take_profit})")
    
    # Strong momentum would normally extend TP
    momentum = 0.05  # Strong negative momentum for short
    trend_strength = 0.8
    volatility = 0.04
    
    old_tp = position.take_profit
    position.update_take_profit(
        current_price,
        momentum=momentum,
        trend_strength=trend_strength,
        volatility=volatility
    )
    
    old_distance = abs(current_price - old_tp)
    new_distance = abs(current_price - position.take_profit)
    
    print(f"  Old TP: {old_tp}, distance from price: {old_distance}")
    print(f"  New TP: {position.take_profit}, distance from price: {new_distance}")
    
    # TP should not move further away
    if new_distance <= old_distance:
        print(f"  ✓ PASS: TP did not move away (distance: {old_distance:.1f} -> {new_distance:.1f})")
    else:
        print(f"  ✗ FAIL: TP moved away (distance: {old_distance:.1f} -> {new_distance:.1f})")
        return False
    
    # Scenario 2: Price reaches TP exactly
    current_price = 90.0
    print(f"\n2. Price reaches TP at {current_price}")
    
    old_tp = position.take_profit
    position.update_take_profit(
        current_price,
        momentum=momentum,
        trend_strength=trend_strength,
        volatility=volatility
    )
    
    old_distance = abs(current_price - old_tp)
    new_distance = abs(current_price - position.take_profit)
    
    print(f"  Old TP: {old_tp}, distance from price: {old_distance}")
    print(f"  New TP: {position.take_profit}, distance from price: {new_distance}")
    
    if new_distance <= old_distance:
        print(f"  ✓ PASS: TP did not move away (distance: {old_distance:.1f} -> {new_distance:.1f})")
    else:
        print(f"  ✗ FAIL: TP moved away (distance: {old_distance:.1f} -> {new_distance:.1f})")
        return False
    
    # Scenario 3: Price passes TP
    current_price = 89.0
    print(f"\n3. Price passes TP to {current_price}")
    
    old_tp = position.take_profit
    position.update_take_profit(
        current_price,
        momentum=momentum,
        trend_strength=trend_strength,
        volatility=volatility
    )
    
    old_distance = abs(current_price - old_tp)
    new_distance = abs(current_price - position.take_profit)
    
    print(f"  Old TP: {old_tp}, distance from price: {old_distance}")
    print(f"  New TP: {position.take_profit}, distance from price: {new_distance}")
    
    if new_distance <= old_distance:
        print(f"  ✓ PASS: TP did not move away (distance: {old_distance:.1f} -> {new_distance:.1f})")
    else:
        print(f"  ✗ FAIL: TP moved away (distance: {old_distance:.1f} -> {new_distance:.1f})")
        return False
    
    print("\n✓ All SHORT position tests PASSED")
    return True


def test_long_position_tp_not_moving_away():
    """Test that LONG position TP doesn't move away from current price"""
    print("\n" + "="*60)
    print("TEST 2: LONG Position - TP should not move away from price")
    print("="*60)
    
    # Setup LONG position
    entry_price = 100.0
    stop_loss_percentage = 0.05
    stop_loss = entry_price * (1 - stop_loss_percentage)  # 95
    take_profit = entry_price * (1 + stop_loss_percentage * 2)  # 110
    
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=entry_price,
        amount=10.0,
        leverage=10,
        stop_loss=stop_loss,
        take_profit=take_profit
    )
    
    print(f"Initial state:")
    print(f"  Entry: {entry_price}, TP: {take_profit}")
    
    # Scenario 1: Price at 108, approaching TP
    current_price = 108.0
    print(f"\n1. Price rises to {current_price} (approaching TP at {take_profit})")
    print(f"  Progress: 80% (close to TP)")
    
    # Strong momentum would normally extend TP
    momentum = 0.05  # Strong positive momentum for long
    trend_strength = 0.8
    volatility = 0.04
    
    old_tp = position.take_profit
    position.update_take_profit(
        current_price,
        momentum=momentum,
        trend_strength=trend_strength,
        volatility=volatility
    )
    
    old_distance = abs(current_price - old_tp)
    new_distance = abs(current_price - position.take_profit)
    
    print(f"  Old TP: {old_tp}, distance from price: {old_distance}")
    print(f"  New TP: {position.take_profit}, distance from price: {new_distance}")
    
    # With >75% progress, TP should not extend
    if new_distance == old_distance:
        print(f"  ✓ PASS: TP did not move (distance stayed at {old_distance:.1f})")
    else:
        print(f"  ✗ FAIL: TP moved (distance: {old_distance:.1f} -> {new_distance:.1f})")
        return False
    
    # Scenario 2: Price reaches TP exactly
    current_price = 110.0
    print(f"\n2. Price reaches TP at {current_price}")
    
    old_tp = position.take_profit
    position.update_take_profit(
        current_price,
        momentum=momentum,
        trend_strength=trend_strength,
        volatility=volatility
    )
    
    old_distance = abs(current_price - old_tp)
    new_distance = abs(current_price - position.take_profit)
    
    print(f"  Old TP: {old_tp}, distance from price: {old_distance}")
    print(f"  New TP: {position.take_profit}, distance from price: {new_distance}")
    
    if new_distance <= old_distance:
        print(f"  ✓ PASS: TP did not move away (distance: {old_distance:.1f} -> {new_distance:.1f})")
    else:
        print(f"  ✗ FAIL: TP moved away (distance: {old_distance:.1f} -> {new_distance:.1f})")
        return False
    
    print("\n✓ All LONG position tests PASSED")
    return True


def test_tp_still_extends_when_appropriate():
    """Test that TP still extends in strong trends when price is far from TP"""
    print("\n" + "="*60)
    print("TEST 3: TP should still extend when price moves favorably")
    print("="*60)
    
    # Setup LONG position
    entry_price = 100.0
    take_profit = 110.0
    
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=entry_price,
        amount=10.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=take_profit
    )
    
    print(f"Initial state:")
    print(f"  Entry: {entry_price}, TP: {take_profit}")
    
    # Price moves favorably but still far from TP
    current_price = 103.0  # Up 3%, but TP is at 110 (7% away)
    print(f"\n1. Price rises to {current_price} (still far from TP at {take_profit})")
    
    # Strong momentum suggests extending TP
    momentum = 0.05
    trend_strength = 0.8
    volatility = 0.04
    
    old_tp = position.take_profit
    position.update_take_profit(
        current_price,
        momentum=momentum,
        trend_strength=trend_strength,
        volatility=volatility
    )
    
    print(f"  Old TP: {old_tp}")
    print(f"  New TP: {position.take_profit}")
    
    # TP should extend upward (increase) for long positions in strong trends
    if position.take_profit > old_tp:
        print(f"  ✓ PASS: TP extended from {old_tp} to {position.take_profit}")
    else:
        print(f"  ✗ FAIL: TP did not extend (stayed at {position.take_profit})")
        return False
    
    print("\n✓ TP extension test PASSED")
    return True


def test_should_close_triggers_correctly():
    """Test that should_close triggers when price reaches TP"""
    print("\n" + "="*60)
    print("TEST 4: should_close should trigger at take profit")
    print("="*60)
    
    # SHORT position with lower leverage and smaller TP to avoid immediate profit taking
    position = Position(
        symbol='BTCUSDT',
        side='short',
        entry_price=100.0,
        amount=10.0,
        leverage=3,  # Lower leverage
        stop_loss=105.0,
        take_profit=98.0  # Smaller profit target: only 2% = 6% ROI with 3x leverage
    )
    
    print(f"SHORT Position: Entry {position.entry_price}, TP {position.take_profit}, Leverage {position.leverage}x")
    
    # Test 1: Price above TP (should not close)
    current_price = 99.0  # Only 1% profit with 3x leverage = 3% ROI (well below thresholds)
    should_close, reason = position.should_close(current_price)
    print(f"\n1. Price at {current_price} (above TP): should_close={should_close}, reason='{reason}'")
    pnl = position.get_pnl(current_price)
    print(f"  P/L: {pnl:.2%}")
    if not should_close:
        print(f"  ✓ PASS: Position stays open")
    else:
        print(f"  ✗ FAIL: Position closed prematurely (reason: {reason})")
        return False
    
    # Test 2: Price at TP (should close)
    current_price = 98.0  # At TP
    should_close, reason = position.should_close(current_price)
    print(f"\n2. Price at {current_price} (at TP): should_close={should_close}, reason='{reason}'")
    if should_close and reason == 'take_profit':
        print(f"  ✓ PASS: Position closed with reason 'take_profit'")
    else:
        print(f"  ✗ FAIL: Position did not close at TP (got: {should_close}, {reason})")
        return False
    
    # Test 3: Price below TP (should close)
    position.take_profit = 98.0  # Reset
    current_price = 97.0  # Below TP
    should_close, reason = position.should_close(current_price)
    print(f"\n3. Price at {current_price} (below TP): should_close={should_close}, reason='{reason}'")
    if should_close and reason == 'take_profit':
        print(f"  ✓ PASS: Position closed with reason 'take_profit'")
    else:
        print(f"  ✗ FAIL: Position did not close below TP (got: {should_close}, {reason})")
        return False
    
    print("\n✓ should_close test PASSED")
    return True


if __name__ == '__main__':
    print("\n" + "="*60)
    print("TAKE PROFIT FIX - COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    results = []
    
    try:
        results.append(("SHORT TP not moving away", test_short_position_tp_not_moving_away()))
    except Exception as e:
        print(f"\n✗ SHORT test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("SHORT TP not moving away", False))
    
    try:
        results.append(("LONG TP not moving away", test_long_position_tp_not_moving_away()))
    except Exception as e:
        print(f"\n✗ LONG test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("LONG TP not moving away", False))
    
    try:
        results.append(("TP extension in trends", test_tp_still_extends_when_appropriate()))
    except Exception as e:
        print(f"\n✗ Extension test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("TP extension in trends", False))
    
    try:
        results.append(("should_close triggers", test_should_close_triggers_correctly()))
    except Exception as e:
        print(f"\n✗ should_close test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("should_close triggers", False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        sys.exit(0)
    else:
        print(f"\n✗✗✗ {total - passed} TEST(S) FAILED ✗✗✗")
        sys.exit(1)
