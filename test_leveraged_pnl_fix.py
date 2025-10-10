#!/usr/bin/env python3
"""
Test for position closing with leveraged P&L fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_leveraged_pnl_position_closing():
    """Test that positions close at correct leveraged ROI thresholds"""
    print("\nTesting leveraged P&L position closing...")
    
    try:
        from position_manager import Position
        
        # Test 1: 10x leverage position with 2% price movement = 20% ROI
        print("\n  Test 1: 10x leverage, 2% price up (20% ROI)")
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=95.0,  # 5% below
            take_profit=110.0  # 10% above
        )
        
        # Price moves up 2% = 102.0
        current_price = 102.0
        unleveraged_pnl = position.get_pnl(current_price)
        leveraged_pnl = position.get_leveraged_pnl(current_price)
        
        print(f"    Entry: {position.entry_price}")
        print(f"    Current: {current_price}")
        print(f"    Price move: {unleveraged_pnl:.2%}")
        print(f"    Leveraged ROI: {leveraged_pnl:.2%}")
        
        # Should close at 20% ROI (2% price move * 10x)
        should_close, reason = position.should_close(current_price)
        assert leveraged_pnl == 0.20, f"Expected 20% ROI, got {leveraged_pnl:.2%}"
        assert should_close, f"Position should close at 20% ROI but didn't (reason: {reason})"
        print(f"    ✓ Position closes at 20% ROI: {reason}")
        
        # Test 2: 10x leverage position with -3% price movement = -30% ROI loss
        print("\n  Test 2: 10x leverage, -3% price down (-30% ROI)")
        position2 = Position(
            symbol='ETH/USDT:USDT',
            side='long',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=97.0,  # 3% below
            take_profit=110.0
        )
        
        # Price moves down 3% = 97.0 (hits stop loss)
        current_price = 97.0
        unleveraged_pnl = position2.get_pnl(current_price)
        leveraged_pnl = position2.get_leveraged_pnl(current_price)
        
        print(f"    Entry: {position2.entry_price}")
        print(f"    Current: {current_price}")
        print(f"    Stop loss: {position2.stop_loss}")
        print(f"    Price move: {unleveraged_pnl:.2%}")
        print(f"    Leveraged ROI: {leveraged_pnl:.2%}")
        
        # Should close at stop loss (-30% ROI)
        should_close, reason = position2.should_close(current_price)
        assert leveraged_pnl == -0.30, f"Expected -30% ROI, got {leveraged_pnl:.2%}"
        assert should_close, f"Position should close at stop loss but didn't"
        assert reason == 'stop_loss', f"Expected 'stop_loss', got '{reason}'"
        print(f"    ✓ Position closes at stop loss: {reason}")
        
        # Test 3: 5x leverage position with 4% price movement = 20% ROI
        print("\n  Test 3: 5x leverage, 4% price up (20% ROI)")
        position3 = Position(
            symbol='SOL/USDT:USDT',
            side='long',
            entry_price=100.0,
            amount=1.0,
            leverage=5,
            stop_loss=94.0,  # 6% below
            take_profit=115.0
        )
        
        # Price moves up 4% = 104.0
        current_price = 104.0
        unleveraged_pnl = position3.get_pnl(current_price)
        leveraged_pnl = position3.get_leveraged_pnl(current_price)
        
        print(f"    Entry: {position3.entry_price}")
        print(f"    Current: {current_price}")
        print(f"    Price move: {unleveraged_pnl:.2%}")
        print(f"    Leveraged ROI: {leveraged_pnl:.2%}")
        
        # Should close at 20% ROI (4% price move * 5x)
        should_close, reason = position3.should_close(current_price)
        assert leveraged_pnl == 0.20, f"Expected 20% ROI, got {leveraged_pnl:.2%}"
        assert should_close, f"Position should close at 20% ROI but didn't (reason: {reason})"
        print(f"    ✓ Position closes at 20% ROI: {reason}")
        
        # Test 4: 1x leverage (no leverage) with 20% price movement = 20% ROI
        print("\n  Test 4: 1x leverage (no leverage), 20% price up (20% ROI)")
        position4 = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=100.0,
            amount=1.0,
            leverage=1,
            stop_loss=92.0,  # 8% below
            take_profit=130.0
        )
        
        # Price moves up 20% = 120.0
        current_price = 120.0
        unleveraged_pnl = position4.get_pnl(current_price)
        leveraged_pnl = position4.get_leveraged_pnl(current_price)
        
        print(f"    Entry: {position4.entry_price}")
        print(f"    Current: {current_price}")
        print(f"    Price move: {unleveraged_pnl:.2%}")
        print(f"    Leveraged ROI: {leveraged_pnl:.2%}")
        
        # Should close at 20% ROI (20% price move * 1x)
        should_close, reason = position4.should_close(current_price)
        assert leveraged_pnl == 0.20, f"Expected 20% ROI, got {leveraged_pnl:.2%}"
        assert should_close, f"Position should close at 20% ROI but didn't (reason: {reason})"
        print(f"    ✓ Position closes at 20% ROI: {reason}")
        
        # Test 5: Short position with 10x leverage and 2% price down = 20% ROI
        print("\n  Test 5: SHORT 10x leverage, 2% price down (20% ROI)")
        position5 = Position(
            symbol='BTC/USDT:USDT',
            side='short',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=105.0,  # 5% above
            take_profit=90.0
        )
        
        # Price moves down 2% = 98.0
        current_price = 98.0
        unleveraged_pnl = position5.get_pnl(current_price)
        leveraged_pnl = position5.get_leveraged_pnl(current_price)
        
        print(f"    Entry: {position5.entry_price}")
        print(f"    Current: {current_price}")
        print(f"    Price move: {unleveraged_pnl:.2%}")
        print(f"    Leveraged ROI: {leveraged_pnl:.2%}")
        
        # Should close at 20% ROI (2% price move * 10x)
        should_close, reason = position5.should_close(current_price)
        assert leveraged_pnl == 0.20, f"Expected 20% ROI, got {leveraged_pnl:.2%}"
        assert should_close, f"Position should close at 20% ROI but didn't (reason: {reason})"
        print(f"    ✓ Position closes at 20% ROI: {reason}")
        
        print("\n✓ All leveraged P&L position closing tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Leveraged P&L test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("=" * 70)
    print("LEVERAGED P&L POSITION CLOSING TEST")
    print("=" * 70)
    
    result = test_leveraged_pnl_position_closing()
    
    print("\n" + "=" * 70)
    if result:
        print("✅ TEST PASSED")
        print("\nPositions now close at correct leveraged ROI thresholds:")
        print("  • 20% ROI profit → closes regardless of leverage")
        print("  • 30% ROI loss → hits stop loss as expected")
        print("  • Works correctly with any leverage level")
    else:
        print("❌ TEST FAILED")
    print("=" * 70)
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())
