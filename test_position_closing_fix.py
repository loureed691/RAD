"""
Test to verify that positions close correctly when TP is reached.
This addresses the issue: "somethin is wrong the bot nearly never closes positions"

The bug was that when price reached the take profit, the TP would be moved further away
during update_take_profit() calls, preventing the position from ever closing.
"""
import sys
from unittest.mock import MagicMock

# Mock the KuCoinClient before importing
sys.modules['kucoin_client'] = MagicMock()

from position_manager import Position


def test_position_closes_at_take_profit():
    """
    Test that positions actually close when price reaches take profit,
    even with continuous update_take_profit() calls with strong momentum.
    """
    print("\n" + "="*70)
    print("TEST: Position Closes When TP is Reached")
    print("="*70)
    print("\nThis test simulates the bug where positions never close because")
    print("TP keeps moving away as price approaches it.")
    
    # Test LONG position
    print("\n" + "-"*70)
    print("1. LONG Position Test")
    print("-"*70)
    
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=100.0,
        amount=10.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0
    )
    
    print(f"Initial: Entry={position.entry_price}, TP={position.take_profit}")
    
    # Strong momentum (would normally extend TP)
    momentum = 0.05
    trend_strength = 0.9
    volatility = 0.06
    
    # Simulate price moving towards TP with multiple updates
    test_prices = [102.0, 105.0, 108.0, 109.5, 110.0]
    
    for price in test_prices:
        # Update TP with strong momentum (this used to move TP away)
        position.update_take_profit(
            price,
            momentum=momentum,
            trend_strength=trend_strength,
            volatility=volatility
        )
        
        should_close, reason = position.should_close(price)
        pnl = position.get_pnl(price)
        
        print(f"  Price {price:6.1f}: TP={position.take_profit:6.2f}, P/L={pnl:5.1%}, Close={should_close}, Reason={reason}")
        
        # When price reaches TP, position MUST close
        if price >= 110.0:
            if should_close and ('take_profit' in reason or reason == 'take_profit'):
                print(f"  ✓ PASS: Position closes at TP (P/L: {pnl:.1%}, Reason: {reason})")
            else:
                print(f"  ✗ FAIL: Position should close at TP but doesn't!")
                print(f"         should_close={should_close}, reason='{reason}'")
                return False
    
    # Test SHORT position
    print("\n" + "-"*70)
    print("2. SHORT Position Test")
    print("-"*70)
    
    position = Position(
        symbol='BTCUSDT',
        side='short',
        entry_price=100.0,
        amount=10.0,
        leverage=10,
        stop_loss=105.0,
        take_profit=90.0
    )
    
    print(f"Initial: Entry={position.entry_price}, TP={position.take_profit}")
    
    # Strong momentum (would normally extend TP)
    momentum = 0.05  # Positive momentum means favorable for short
    
    # Simulate price moving towards TP with multiple updates
    test_prices = [98.0, 95.0, 92.0, 90.5, 90.0]
    
    for price in test_prices:
        # Update TP with strong momentum (this used to move TP away)
        position.update_take_profit(
            price,
            momentum=momentum,
            trend_strength=trend_strength,
            volatility=volatility
        )
        
        should_close, reason = position.should_close(price)
        pnl = position.get_pnl(price)
        
        print(f"  Price {price:6.1f}: TP={position.take_profit:6.2f}, P/L={pnl:5.1%}, Close={should_close}, Reason={reason}")
        
        # When price reaches TP, position MUST close
        if price <= 90.0:
            if should_close and ('take_profit' in reason or reason == 'take_profit'):
                print(f"  ✓ PASS: Position closes at TP (P/L: {pnl:.1%}, Reason: {reason})")
            else:
                print(f"  ✗ FAIL: Position should close at TP but doesn't!")
                print(f"         should_close={should_close}, reason='{reason}'")
                return False
    
    print("\n" + "="*70)
    print("✓✓✓ ALL TESTS PASSED ✓✓✓")
    print("="*70)
    print("\nPositions now close correctly when take profit is reached!")
    print("The bug where TP kept moving away has been FIXED.")
    return True


def test_position_closes_with_rapid_updates():
    """
    Test that positions close even with very rapid TP updates simulating
    a fast-moving market with frequent update_positions() calls.
    """
    print("\n" + "="*70)
    print("TEST: Position Closes with Rapid TP Updates")
    print("="*70)
    print("\nSimulating rapid market with frequent update_take_profit() calls")
    
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=100.0,
        amount=10.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0
    )
    
    print(f"Initial: Entry={position.entry_price}, TP={position.take_profit}")
    
    # Simulate very rapid updates at TP
    current_price = 110.0
    print(f"\nPrice reaches TP at {current_price}")
    
    # Do 10 rapid updates (simulating frequent bot cycles)
    for i in range(10):
        position.update_take_profit(
            current_price,
            momentum=0.08,  # Very strong momentum
            trend_strength=0.95,
            volatility=0.08
        )
        
        should_close, reason = position.should_close(current_price)
        
        if i == 0:
            print(f"  Update {i+1:2d}: TP={position.take_profit:.2f}, Close={should_close}")
        elif i == 9:
            print(f"  Update {i+1:2d}: TP={position.take_profit:.2f}, Close={should_close}")
    
    # After all updates, position must still close
    should_close, reason = position.should_close(current_price)
    pnl = position.get_pnl(current_price)
    
    if should_close and ('take_profit' in reason or reason == 'take_profit'):
        print(f"\n  ✓ PASS: Position closes after {10} rapid updates")
        print(f"         Final TP={position.take_profit:.2f}, P/L={pnl:.1%}, Reason: {reason}")
        return True
    else:
        print(f"\n  ✗ FAIL: Position doesn't close after rapid updates!")
        print(f"         should_close={should_close}, reason='{reason}'")
        print(f"         Final TP={position.take_profit:.2f}")
        return False


if __name__ == '__main__':
    results = []
    
    try:
        results.append(("Position closes at TP", test_position_closes_at_take_profit()))
    except Exception as e:
        print(f"\n✗ Test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Position closes at TP", False))
    
    try:
        results.append(("Rapid updates", test_position_closes_with_rapid_updates()))
    except Exception as e:
        print(f"\n✗ Test FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Rapid updates", False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "="*70)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("="*70)
        print("\n🎉 FIX CONFIRMED: Positions now close correctly!")
        print("   The bot will no longer keep positions open indefinitely.")
        sys.exit(0)
    else:
        print(f"\n✗✗✗ {total - passed} TEST(S) FAILED ✗✗✗")
        sys.exit(1)
