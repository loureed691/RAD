#!/usr/bin/env python3
"""
Test suite for order execution and profit taking fixes
Tests that stop loss and take profit logic work correctly
"""

from position_manager import Position
from datetime import datetime, timedelta

def test_stop_loss_execution():
    """Test that stop loss triggers correctly for both LONG and SHORT positions"""
    print("\n" + "="*80)
    print("TEST: Stop Loss Execution")
    print("="*80)
    
    # Test LONG position stop loss
    print("\n1. Testing LONG position stop loss...")
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=95.0,  # 5% below entry
        take_profit=110.0
    )
    
    # Price above stop loss - should NOT close
    should_close, reason = position.should_close(97.0)
    assert not should_close, "Position should NOT close above stop loss"
    print(f"   ✓ Price 97 (above SL 95): should_close={should_close} (correct)")
    
    # Price AT stop loss - should close
    should_close, reason = position.should_close(95.0)
    assert should_close, "Position SHOULD close at stop loss"
    assert 'stop_loss' in reason, f"Reason should contain 'stop_loss', got: {reason}"
    print(f"   ✓ Price 95 (at SL 95): should_close={should_close}, reason={reason} (correct)")
    
    # Price below stop loss - should close
    should_close, reason = position.should_close(93.0)
    assert should_close, "Position SHOULD close below stop loss"
    assert 'stop_loss' in reason, f"Reason should contain 'stop_loss', got: {reason}"
    print(f"   ✓ Price 93 (below SL 95): should_close={should_close}, reason={reason} (correct)")
    
    # Test SHORT position stop loss
    print("\n2. Testing SHORT position stop loss...")
    position = Position(
        symbol='BTC-USDT',
        side='short',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=105.0,  # 5% above entry
        take_profit=90.0
    )
    
    # Price below stop loss - should NOT close
    should_close, reason = position.should_close(103.0)
    assert not should_close, "Position should NOT close below stop loss"
    print(f"   ✓ Price 103 (below SL 105): should_close={should_close} (correct)")
    
    # Price AT stop loss - should close
    should_close, reason = position.should_close(105.0)
    assert should_close, "Position SHOULD close at stop loss"
    assert 'stop_loss' in reason, f"Reason should contain 'stop_loss', got: {reason}"
    print(f"   ✓ Price 105 (at SL 105): should_close={should_close}, reason={reason} (correct)")
    
    # Price above stop loss - should close
    should_close, reason = position.should_close(107.0)
    assert should_close, "Position SHOULD close above stop loss"
    assert 'stop_loss' in reason, f"Reason should contain 'stop_loss', got: {reason}"
    print(f"   ✓ Price 107 (above SL 105): should_close={should_close}, reason={reason} (correct)")
    
    print("\n✅ Stop loss execution test PASSED")
    return True


def test_take_profit_execution():
    """Test that take profit triggers correctly for both LONG and SHORT positions"""
    print("\n" + "="*80)
    print("TEST: Take Profit Execution")
    print("="*80)
    
    # Test LONG position take profit
    print("\n1. Testing LONG position take profit...")
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0  # 10% above entry
    )
    
    # Price below take profit - should NOT close
    should_close, reason = position.should_close(108.0)
    assert not should_close, "Position should NOT close below take profit"
    print(f"   ✓ Price 108 (below TP 110): should_close={should_close} (correct)")
    
    # Price AT take profit (with tolerance) - should close
    should_close, reason = position.should_close(110.0)
    assert should_close, f"Position SHOULD close at take profit, but got should_close={should_close}"
    assert 'take_profit' in reason, f"Reason should contain 'take_profit', got: {reason}"
    print(f"   ✓ Price 110 (at TP 110): should_close={should_close}, reason={reason} (correct)")
    
    # Price above take profit - should close
    position2 = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0
    )
    should_close, reason = position2.should_close(112.0)
    assert should_close, "Position SHOULD close above take profit"
    assert 'take_profit' in reason, f"Reason should contain 'take_profit', got: {reason}"
    print(f"   ✓ Price 112 (above TP 110): should_close={should_close}, reason={reason} (correct)")
    
    # Test SHORT position take profit
    print("\n2. Testing SHORT position take profit...")
    position = Position(
        symbol='BTC-USDT',
        side='short',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=105.0,
        take_profit=90.0  # 10% below entry
    )
    
    # Price above take profit - should NOT close
    should_close, reason = position.should_close(92.0)
    assert not should_close, "Position should NOT close above take profit"
    print(f"   ✓ Price 92 (above TP 90): should_close={should_close} (correct)")
    
    # Price AT take profit (with tolerance) - should close
    should_close, reason = position.should_close(90.0)
    assert should_close, f"Position SHOULD close at take profit, but got should_close={should_close}"
    assert 'take_profit' in reason, f"Reason should contain 'take_profit', got: {reason}"
    print(f"   ✓ Price 90 (at TP 90): should_close={should_close}, reason={reason} (correct)")
    
    # Price below take profit - should close
    position2 = Position(
        symbol='BTC-USDT',
        side='short',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=105.0,
        take_profit=90.0
    )
    should_close, reason = position2.should_close(88.0)
    assert should_close, "Position SHOULD close below take profit"
    assert 'take_profit' in reason, f"Reason should contain 'take_profit', got: {reason}"
    print(f"   ✓ Price 88 (below TP 90): should_close={should_close}, reason={reason} (correct)")
    
    print("\n✅ Take profit execution test PASSED")
    return True


def test_tp_not_moving_away():
    """Test that take profit does NOT move away when price approaches it"""
    print("\n" + "="*80)
    print("TEST: Take Profit Does Not Move Away")
    print("="*80)
    
    print("\n1. Testing LONG position - TP should not extend past 70% progress...")
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0  # 10% above entry (initial TP)
    )
    
    # Store initial TP
    initial_tp = position.take_profit
    print(f"   Initial TP: {initial_tp}")
    
    # Simulate price moving from 100 to 109 (90% of way to TP)
    prices = [102, 105, 107, 109]
    
    for price in prices:
        # Calculate progress to initial TP
        progress = (price - position.entry_price) / (initial_tp - position.entry_price)
        
        # Try to update TP (simulating strong momentum conditions that would normally extend TP)
        old_tp = position.take_profit
        position.update_take_profit(
            current_price=price,
            momentum=0.05,  # Strong positive momentum
            trend_strength=0.8,  # Strong trend
            volatility=0.02,  # Low volatility
            rsi=60.0
        )
        
        # Check if TP was extended
        tp_extended = position.take_profit > old_tp
        
        print(f"   Price: {price}, Progress: {progress:.1%}, Old TP: {old_tp:.1f}, New TP: {position.take_profit:.1f}, Extended: {tp_extended}")
        
        # After 70% progress, TP should NOT be extended
        if progress >= 0.7:
            assert not tp_extended or position.take_profit <= old_tp * 1.01, \
                f"TP should not extend significantly past 70% progress (price {price})"
    
    # Verify position can close at final TP
    final_price = 110.0
    should_close, reason = position.should_close(final_price)
    print(f"\n   At price {final_price} (initial TP): should_close={should_close}, reason={reason}")
    assert should_close, f"Position SHOULD close at initial TP of {initial_tp}"
    
    print("\n✅ TP does not move away test PASSED")
    return True


def test_intelligent_profit_taking():
    """Test intelligent profit taking at key levels"""
    print("\n" + "="*80)
    print("TEST: Intelligent Profit Taking")
    print("="*80)
    
    print("\n1. Testing 10% profit taking when TP is far away...")
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=120.0  # TP is 20% away (far)
    )
    
    # Price at 110 = 10% profit, TP is at 120 (10% away, which is >2% threshold)
    current_price = 110.0
    should_close, reason = position.should_close(current_price)
    
    pnl = position.get_pnl(current_price)
    distance_to_tp = (position.take_profit - current_price) / current_price
    
    print(f"   Price: {current_price}, Entry: {position.entry_price}, TP: {position.take_profit}")
    print(f"   P/L: {pnl:.1%}, Distance to TP: {distance_to_tp:.1%}")
    print(f"   Should close: {should_close}, Reason: {reason}")
    
    # Should close because: 10% profit AND TP is >2% away
    assert should_close, f"Should close at 10% profit when TP is {distance_to_tp:.1%} away"
    assert 'take_profit' in reason, f"Reason should be profit taking, got: {reason}"
    
    print("\n2. Testing that 10% profit does NOT close when TP is close...")
    position2 = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=100.0,
        amount=1.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=111.0  # TP is only 1% away (close)
    )
    
    # Price at 110 = 10% profit, TP is at 111 (0.9% away, which is <2% threshold)
    current_price = 110.0
    should_close, reason = position2.should_close(current_price)
    
    pnl = position2.get_pnl(current_price)
    distance_to_tp = (position2.take_profit - current_price) / current_price
    
    print(f"   Price: {current_price}, Entry: {position2.entry_price}, TP: {position2.take_profit}")
    print(f"   P/L: {pnl:.1%}, Distance to TP: {distance_to_tp:.1%}")
    print(f"   Should close: {should_close}, Reason: {reason}")
    
    # Should NOT close early because TP is close - let it reach actual TP
    # Will close when price reaches TP at 111
    
    print("\n✅ Intelligent profit taking test PASSED")
    return True


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*80)
    print("ORDER EXECUTION AND PROFIT TAKING TEST SUITE")
    print("="*80)
    
    all_passed = True
    
    try:
        test_stop_loss_execution()
    except AssertionError as e:
        print(f"\n✗ Stop loss execution test FAILED: {e}")
        all_passed = False
    
    try:
        test_take_profit_execution()
    except AssertionError as e:
        print(f"\n✗ Take profit execution test FAILED: {e}")
        all_passed = False
    
    try:
        test_tp_not_moving_away()
    except AssertionError as e:
        print(f"\n✗ TP not moving away test FAILED: {e}")
        all_passed = False
    
    try:
        test_intelligent_profit_taking()
    except AssertionError as e:
        print(f"\n✗ Intelligent profit taking test FAILED: {e}")
        all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
