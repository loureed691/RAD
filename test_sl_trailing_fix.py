"""
Test to verify stop loss trailing logic doesn't move SL further away (losing direction)
"""
import sys
from unittest.mock import MagicMock
sys.modules['kucoin_client'] = MagicMock()

from position_manager import Position

def test_sl_trailing_long():
    """Test that trailing SL for LONG positions doesn't move in losing direction"""
    print("\n" + "=" * 80)
    print("TEST: TRAILING STOP LOSS FOR LONG POSITION")
    print("=" * 80)
    
    # Create LONG position
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,  # 5% SL
        take_profit=55000.0
    )
    
    print(f"\nInitial Setup:")
    print(f"  Entry: ${position.entry_price:,.0f}")
    print(f"  Initial SL: ${position.stop_loss:,.0f} (5% below entry)")
    
    # Simulate price moving up (profit) - SL should trail up (tighten)
    prices_up = [51000, 52000, 53000]
    
    print(f"\nPrice moving UP (profitable):")
    print(f"{'Price':<10} | {'SL Before':<12} | {'SL After':<12} | {'Direction'}")
    print("-" * 60)
    
    issues = []
    for price in prices_up:
        sl_before = position.stop_loss
        position.update_trailing_stop(price, trailing_percentage=0.05, volatility=0.03, momentum=0.02)
        sl_after = position.stop_loss
        
        # For LONG, SL should only move UP (never down)
        moved_correctly = sl_after >= sl_before
        direction = "UP ✓" if sl_after > sl_before else ("SAME ✓" if sl_after == sl_before else "DOWN ❌")
        
        print(f"${price:<9,.0f} | ${sl_before:<11,.0f} | ${sl_after:<11,.0f} | {direction}")
        
        if not moved_correctly:
            issues.append(f"LONG SL moved DOWN from ${sl_before:,.0f} to ${sl_after:,.0f} at price ${price:,.0f}")
    
    # Simulate price moving down (loss) - SL should NOT move (stays at current level)
    print(f"\nPrice moving DOWN (losing):")
    print(f"{'Price':<10} | {'SL Before':<12} | {'SL After':<12} | {'Should Stay'}")
    print("-" * 60)
    
    prices_down = [52500, 52000, 51500]
    for price in prices_down:
        sl_before = position.stop_loss
        position.update_trailing_stop(price, trailing_percentage=0.05, volatility=0.03, momentum=-0.02)
        sl_after = position.stop_loss
        
        # For LONG going down, SL should NOT move down (only locks in gains)
        moved_correctly = sl_after >= sl_before
        status = "SAME ✓" if sl_after == sl_before else ("UP ✓" if sl_after > sl_before else "DOWN ❌")
        
        print(f"${price:<9,.0f} | ${sl_before:<11,.0f} | ${sl_after:<11,.0f} | {status}")
        
        if not moved_correctly:
            issues.append(f"LONG SL moved DOWN from ${sl_before:,.0f} to ${sl_after:,.0f} at price ${price:,.0f}")
    
    print("\n" + "=" * 80)
    if issues:
        print("❌ TEST FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ TEST PASSED - Stop loss behaved correctly")
        return True

def test_sl_trailing_short():
    """Test that trailing SL for SHORT positions doesn't move in losing direction"""
    print("\n" + "=" * 80)
    print("TEST: TRAILING STOP LOSS FOR SHORT POSITION")
    print("=" * 80)
    
    # Create SHORT position
    position = Position(
        symbol='BTCUSDT',
        side='short',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=52500.0,  # 5% SL above entry
        take_profit=45000.0
    )
    
    print(f"\nInitial Setup:")
    print(f"  Entry: ${position.entry_price:,.0f}")
    print(f"  Initial SL: ${position.stop_loss:,.0f} (5% above entry)")
    
    # Simulate price moving down (profit) - SL should trail down (tighten)
    prices_down = [49000, 48000, 47000]
    
    print(f"\nPrice moving DOWN (profitable for SHORT):")
    print(f"{'Price':<10} | {'SL Before':<12} | {'SL After':<12} | {'Direction'}")
    print("-" * 60)
    
    issues = []
    for price in prices_down:
        sl_before = position.stop_loss
        position.update_trailing_stop(price, trailing_percentage=0.05, volatility=0.03, momentum=-0.02)
        sl_after = position.stop_loss
        
        # For SHORT, SL should only move DOWN (never up)
        moved_correctly = sl_after <= sl_before
        direction = "DOWN ✓" if sl_after < sl_before else ("SAME ✓" if sl_after == sl_before else "UP ❌")
        
        print(f"${price:<9,.0f} | ${sl_before:<11,.0f} | ${sl_after:<11,.0f} | {direction}")
        
        if not moved_correctly:
            issues.append(f"SHORT SL moved UP from ${sl_before:,.0f} to ${sl_after:,.0f} at price ${price:,.0f}")
    
    # Simulate price moving up (loss) - SL should NOT move (stays at current level)
    print(f"\nPrice moving UP (losing for SHORT):")
    print(f"{'Price':<10} | {'SL Before':<12} | {'SL After':<12} | {'Should Stay'}")
    print("-" * 60)
    
    prices_up = [47500, 48000, 48500]
    for price in prices_up:
        sl_before = position.stop_loss
        position.update_trailing_stop(price, trailing_percentage=0.05, volatility=0.03, momentum=0.02)
        sl_after = position.stop_loss
        
        # For SHORT going up, SL should NOT move up (only locks in gains)
        moved_correctly = sl_after <= sl_before
        status = "SAME ✓" if sl_after == sl_before else ("DOWN ✓" if sl_after < sl_before else "UP ❌")
        
        print(f"${price:<9,.0f} | ${sl_before:<11,.0f} | ${sl_after:<11,.0f} | {status}")
        
        if not moved_correctly:
            issues.append(f"SHORT SL moved UP from ${sl_before:,.0f} to ${sl_after:,.0f} at price ${price:,.0f}")
    
    print("\n" + "=" * 80)
    if issues:
        print("❌ TEST FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ TEST PASSED - Stop loss behaved correctly")
        return True

if __name__ == "__main__":
    success1 = test_sl_trailing_long()
    success2 = test_sl_trailing_short()
    
    print("\n" + "=" * 80)
    if success1 and success2:
        print("✓✓✓ ALL TRAILING STOP TESTS PASSED ✓✓✓")
        exit(0)
    else:
        print("❌ SOME TRAILING STOP TESTS FAILED")
        exit(1)
