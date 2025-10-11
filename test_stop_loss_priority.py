#!/usr/bin/env python3
"""
Test for stop loss priority fix

This test verifies that:
1. Stop loss price checks have priority over emergency ROI-based stops
2. When stop loss price is hit, returns 'stop_loss' (not 'emergency_stop_*')
3. Emergency stops only trigger when stop loss hasn't been hit
4. ROI calculations work correctly with leverage for stop loss thresholds
"""
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_stop_loss_priority():
    """Test that stop loss price checks have priority over emergency stops"""
    print("\nTesting stop loss priority...")
    
    try:
        from position_manager import Position
        
        # Test 1: Stop loss price hit (should return 'stop_loss' not 'emergency_stop_*')
        print("\n  Test 1: Stop loss price hit with 10x leverage")
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=95.0,
            take_profit=110.0
        )
        
        # At $95, price move is -5%, ROI is -50%
        # This would trigger emergency_stop_liquidation_risk if checked first
        # But stop loss price is hit, so should return 'stop_loss'
        price_at_sl = 95.0
        unleveraged_pnl = position.get_pnl(price_at_sl)
        leveraged_pnl = position.get_leveraged_pnl(price_at_sl)
        should_close, reason = position.should_close(price_at_sl)
        
        print(f"    Entry: ${position.entry_price}")
        print(f"    Stop Loss: ${position.stop_loss}")
        print(f"    Current Price: ${price_at_sl}")
        print(f"    Price movement: {unleveraged_pnl:.2%}")
        print(f"    Leveraged ROI: {leveraged_pnl:.2%}")
        print(f"    Should close: {should_close}")
        print(f"    Reason: {reason}")
        
        assert should_close, "Position should close at stop loss"
        assert reason == 'stop_loss', f"Expected 'stop_loss', got '{reason}'"
        assert leveraged_pnl == -0.50, f"Expected -50% ROI, got {leveraged_pnl:.2%}"
        
        print(f"    ✓ Stop loss price check has priority (returns 'stop_loss' not 'emergency')")
        
        # Test 2: Emergency stop only triggers when stop loss NOT hit
        print("\n  Test 2: Emergency stop when stop loss not hit but ROI very negative")
        position2 = Position(
            symbol='ETH/USDT:USDT',
            side='long',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=90.0,  # Stop loss at $90
            take_profit=110.0
        )
        
        # At $96, price hasn't hit stop loss ($90)
        # But ROI is -40% (4% price × 10x leverage)
        # Should trigger emergency_stop_severe_loss
        price_above_sl = 96.0
        roi = position2.get_leveraged_pnl(price_above_sl)
        should_close2, reason2 = position2.should_close(price_above_sl)
        
        print(f"    Entry: ${position2.entry_price}")
        print(f"    Stop Loss: ${position2.stop_loss}")
        print(f"    Current Price: ${price_above_sl}")
        print(f"    Leveraged ROI: {roi:.2%}")
        print(f"    Should close: {should_close2}")
        print(f"    Reason: {reason2}")
        
        assert should_close2, "Position should close via emergency stop"
        assert 'emergency' in reason2, f"Expected emergency stop, got '{reason2}'"
        assert price_above_sl > position2.stop_loss, "Price should be above stop loss"
        
        print(f"    ✓ Emergency stop acts as failsafe when stop loss not hit")
        
        # Test 3: All leverage levels return 'stop_loss' when price hits stop
        print("\n  Test 3: All leverage levels use stop loss price correctly")
        leverage_levels = [1, 5, 10, 20]
        
        for lev in leverage_levels:
            pos = Position(
                symbol='TEST/USDT:USDT',
                side='long',
                entry_price=100.0,
                amount=1.0,
                leverage=lev,
                stop_loss=95.0,
                take_profit=110.0
            )
            
            should_close, reason = pos.should_close(95.0)
            roi = pos.get_leveraged_pnl(95.0)
            
            print(f"    {lev:2d}x leverage: ROI={roi:7.2%}, Reason={reason}")
            
            assert should_close, f"Expected close with {lev}x leverage"
            assert reason == 'stop_loss', f"Expected 'stop_loss' with {lev}x leverage, got '{reason}'"
        
        print(f"    ✓ All leverage levels return 'stop_loss' when price hits stop")
        
        # Test 4: SHORT positions work correctly too
        print("\n  Test 4: SHORT positions with stop loss priority")
        short_pos = Position(
            symbol='BTC/USDT:USDT',
            side='short',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=105.0,  # Stop loss at $105 for short
            take_profit=90.0
        )
        
        # At $105, price move is +5%, ROI is -50% for short
        should_close, reason = short_pos.should_close(105.0)
        roi = short_pos.get_leveraged_pnl(105.0)
        
        print(f"    SHORT Entry: ${short_pos.entry_price}")
        print(f"    Stop Loss: ${short_pos.stop_loss}")
        print(f"    Current Price: $105.0")
        print(f"    Leveraged ROI: {roi:.2%}")
        print(f"    Should close: {should_close}")
        print(f"    Reason: {reason}")
        
        assert should_close, "SHORT position should close at stop loss"
        assert reason == 'stop_loss', f"Expected 'stop_loss' for SHORT, got '{reason}'"
        
        print(f"    ✓ SHORT positions use stop loss priority correctly")
        
        print("\n✓ All stop loss priority tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Stop loss priority test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("=" * 70)
    print("STOP LOSS PRIORITY TEST")
    print("=" * 70)
    print("\nThis test verifies that stop loss price checks have priority")
    print("over ROI-based emergency stops.")
    
    result = test_stop_loss_priority()
    
    print("\n" + "=" * 70)
    if result:
        print("✅ TEST PASSED")
        print("\nSummary:")
        print("  ✓ Stop loss price check has priority over emergency stops")
        print("  ✓ When stop loss is hit, returns 'stop_loss' reason")
        print("  ✓ Emergency stops act as failsafe when stop loss not hit")
        print("  ✓ Works correctly for all leverage levels")
        print("  ✓ Works correctly for both LONG and SHORT positions")
    else:
        print("❌ TEST FAILED")
    print("=" * 70)
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())
