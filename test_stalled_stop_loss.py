#!/usr/bin/env python3
"""
Test that time-based exit conditions have been removed from positions
"""
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_no_time_based_exit():
    """Test that positions do NOT close based on time alone"""
    print("\nTesting that time-based exits are disabled...")
    
    try:
        from position_manager import Position
        
        # Test 1: Position held for 4+ hours with low ROI should NOT close based on time
        print("\n  Test 1: Long position with 1.5% ROI after 4+ hours (should NOT close based on time)")
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=95.0,
            take_profit=110.0
        )
        
        # Manually set entry time to 4+ hours ago
        position.entry_time = datetime.now() - timedelta(hours=4.5)
        
        # Price moves to give 1.5% ROI (0.15% price move with 10x leverage)
        current_price = 100.15
        leveraged_pnl = position.get_leveraged_pnl(current_price)
        
        print(f"    Entry: ${position.entry_price}")
        print(f"    Current: ${current_price}")
        print(f"    Leveraged ROI: {leveraged_pnl:.2%}")
        print(f"    Time in trade: 4.5 hours")
        
        # Check at current price - should NOT close based on time
        should_close, reason = position.should_close(current_price)
        
        print(f"    Should close: {should_close}")
        if should_close:
            print(f"    Reason: {reason}")
        
        assert not should_close, f"Position should NOT close based on time alone, but got: {reason}"
        print(f"    ✓ Position stays open despite time elapsed")
        
        # Test 2: Short position held for 10+ hours with low ROI should NOT close based on time
        print("\n  Test 2: Short position with 1.0% ROI after 10+ hours (should NOT close based on time)")
        position2 = Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=105.0,
            take_profit=90.0
        )
        
        position2.entry_time = datetime.now() - timedelta(hours=10)
        
        # Price moves to give 1.0% ROI
        current_price2 = 99.9
        leveraged_pnl2 = position2.get_leveraged_pnl(current_price2)
        
        print(f"    Entry: ${position2.entry_price}")
        print(f"    Current: ${current_price2}")
        print(f"    Leveraged ROI: {leveraged_pnl2:.2%}")
        print(f"    Time in trade: 10 hours")
        
        # Check at current price - should NOT close based on time
        should_close2, reason2 = position2.should_close(current_price2)
        
        print(f"    Should close: {should_close2}")
        if should_close2:
            print(f"    Reason: {reason2}")
        
        assert not should_close2, f"Position should NOT close based on time alone, but got: {reason2}"
        print(f"    ✓ Position stays open despite long time elapsed")
        
        # Test 3: Verify stop loss still works (time should not affect stop loss logic)
        print("\n  Test 3: Position should still close when stop loss is hit")
        position3 = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=98.0,
            take_profit=110.0
        )
        
        position3.entry_time = datetime.now() - timedelta(hours=5)
        
        # Price drops to stop loss level
        stop_price = 98.0
        should_close3, reason3 = position3.should_close(stop_price)
        
        print(f"    Entry: ${position3.entry_price}")
        print(f"    Current: ${stop_price}")
        print(f"    Stop Loss: ${position3.stop_loss}")
        print(f"    Should close: {should_close3}")
        print(f"    Reason: {reason3}")
        
        assert should_close3, "Position should close when stop loss is hit"
        # Position closes due to either regular stop_loss or emergency stop - both are valid
        assert reason3 in ['stop_loss', 'emergency_stop_excessive_loss', 'emergency_stop_severe_loss'], \
            f"Expected valid stop reason, got '{reason3}'"
        print(f"    ✓ Stop loss mechanism still works correctly")
        
        print("\n✓ All time-based exit removal tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Time-based exit removal test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("=" * 70)
    print("NO TIME-BASED EXIT TEST")
    print("=" * 70)
    
    result = test_no_time_based_exit()
    
    print("\n" + "=" * 70)
    if result:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    print("=" * 70)
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())
