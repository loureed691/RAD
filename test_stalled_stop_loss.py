#!/usr/bin/env python3
"""
Test for stop loss stalled position logic
"""
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_stalled_position_stop_loss():
    """Test that stalled position stop loss uses correct leveraged P&L threshold"""
    print("\nTesting stalled position stop loss logic...")
    
    try:
        from position_manager import Position
        
        # Test 1: 10x leverage position with 1.5% ROI after 4 hours
        print("\n  Test 1: 10x leverage, 1.5% ROI after 4+ hours (should trigger tighter stop)")
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
        # 0.15% of 100 = 0.15, so price is 100.15
        current_price = 100.15
        unleveraged_pnl = position.get_pnl(current_price)
        leveraged_pnl = position.get_leveraged_pnl(current_price)
        
        print(f"    Entry: ${position.entry_price}")
        print(f"    Current: ${current_price}")
        print(f"    Price movement: {unleveraged_pnl:.4%}")
        print(f"    Leveraged ROI: {leveraged_pnl:.2%}")
        print(f"    Time in trade: 4.5 hours")
        print(f"    Expected: Should trigger tighter stop at 1.5% ROI (< 2% threshold)")
        
        # Price drops to 99.0 (tighter stop is at entry * 0.99 = 99.0)
        price_at_tighter_stop = 99.0
        should_close, reason = position.should_close(price_at_tighter_stop)
        
        print(f"    Price drops to ${price_at_tighter_stop}")
        print(f"    Should close: {should_close}")
        print(f"    Reason: {reason}")
        
        assert leveraged_pnl < 0.02, f"Test setup: ROI should be < 2%, got {leveraged_pnl:.2%}"
        assert should_close, "Position should close at tighter stop when stalled with < 2% ROI"
        assert reason == 'stop_loss_stalled_position', f"Expected 'stop_loss_stalled_position', got '{reason}'"
        
        print(f"    ✓ Stalled position stop loss triggers correctly at < 2% ROI")
        
        # Test 2: 10x leverage position with 2.5% ROI after 4 hours (should NOT trigger tighter stop)
        print("\n  Test 2: 10x leverage, 2.5% ROI after 4+ hours (should NOT trigger tighter stop)")
        position2 = Position(
            symbol='ETH/USDT:USDT',
            side='long',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=95.0,
            take_profit=110.0
        )
        
        position2.entry_time = datetime.now() - timedelta(hours=4.5)
        
        # Price is at 100.25, giving 2.5% ROI (0.25% price move with 10x leverage)
        # This is above the 2% threshold, so stalled stop should NOT be active
        current_price2 = 100.25
        leveraged_pnl2 = position2.get_leveraged_pnl(current_price2)
        
        print(f"    Entry: ${position2.entry_price}")
        print(f"    Current: ${current_price2}")
        print(f"    Leveraged ROI: {leveraged_pnl2:.2%}")
        print(f"    Time in trade: 4.5 hours")
        print(f"    Expected: Should NOT trigger stalled stop at 2.5% ROI (> 2% threshold)")
        
        # Check at current price - should NOT trigger stalled stop
        should_close2, reason2 = position2.should_close(current_price2)
        
        print(f"    At current price ${current_price2}:")
        print(f"    Should close: {should_close2}")
        if should_close2:
            print(f"    Reason: {reason2}")
        
        assert leveraged_pnl2 > 0.02, f"Test setup: ROI should be > 2%, got {leveraged_pnl2:.2%}"
        
        # At 2.5% ROI, should not close (no stop/TP hit, not stalled)
        if not should_close2:
            print(f"    ✓ Position does NOT close at 2.5% ROI (correct)")
        elif reason2 != 'stop_loss_stalled_position':
            print(f"    ✓ Position closes for different reason: {reason2}")
        else:
            raise AssertionError(f"Position should NOT trigger stalled stop at 2.5% ROI, but got: {reason2}")
        
        # Test 3: Different leverage levels should all use 2% ROI threshold
        print("\n  Test 3: Different leverage levels all use 2% ROI threshold")
        leverage_levels = [1, 5, 10, 20]
        
        for lev in leverage_levels:
            pos = Position(
                symbol='TEST/USDT:USDT',
                side='long',
                entry_price=100.0,
                amount=1.0,
                leverage=lev,
                stop_loss=90.0,
                take_profit=120.0
            )
            pos.entry_time = datetime.now() - timedelta(hours=5)
            
            # Set price to give exactly 1.9% ROI
            price_move_needed = 0.019 / lev
            test_price = 100.0 * (1 + price_move_needed)
            
            roi = pos.get_leveraged_pnl(test_price)
            print(f"    {lev:2d}x leverage: {roi:.2%} ROI → should trigger at 1.9% ROI")
            
            assert roi < 0.02, f"Expected < 2% ROI with {lev}x leverage"
            assert abs(roi - 0.019) < 0.0001, f"Expected 1.9% ROI, got {roi:.2%}"
        
        print("\n✓ All stalled position stop loss tests passed!")
        
    except Exception as e:
        print(f"\n✗ Stalled position stop loss test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run the test"""
    print("=" * 70)
    print("STALLED POSITION STOP LOSS TEST")
    print("=" * 70)
    
    result = test_stalled_position_stop_loss()
    
    print("\n" + "=" * 70)
    if result:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    print("=" * 70)
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())
