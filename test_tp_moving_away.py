"""
Test to reproduce the issue where TP keeps moving away as price approaches it
"""
import sys
from unittest.mock import MagicMock
sys.modules['kucoin_client'] = MagicMock()

from position_manager import Position

def test_tp_stays_reachable():
    """Test that TP doesn't keep moving away as price approaches"""
    print("\n" + "=" * 80)
    print("TEST: TAKE PROFIT DOESN'T MOVE AWAY WHEN PRICE APPROACHES")
    print("=" * 80)
    
    # Create LONG position
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,
        take_profit=55000.0  # 10% target
    )
    
    print(f"\nInitial Setup:")
    print(f"  Entry: ${position.entry_price:,.0f}")
    print(f"  Initial TP: ${position.take_profit:,.0f} (10% away)")
    print(f"  Initial SL: ${position.stop_loss:,.0f}")
    
    # Simulate price moving toward TP with strong momentum
    # This should trigger TP extension logic
    prices = [51000, 52000, 53000, 54000, 54500]
    
    print(f"\nSimulating price progression with TP updates:")
    print(f"{'Price':<10} | {'Distance to TP':<15} | {'TP After Update':<17} | {'Issue?'}")
    print("-" * 80)
    
    issues_found = []
    
    for price in prices:
        # Distance to TP before update
        dist_before = position.take_profit - price
        pct_before = (dist_before / price) * 100
        
        # Update TP with strong momentum (which triggers extension logic)
        position.update_take_profit(
            current_price=price,
            momentum=0.05,  # Strong positive momentum
            trend_strength=0.8,  # Strong trend
            volatility=0.06,  # High volatility
            rsi=50.0  # Neutral RSI
        )
        
        # Distance to TP after update
        dist_after = position.take_profit - price
        pct_after = (dist_after / price) * 100
        
        # Check if TP moved further away
        moved_away = dist_after > dist_before
        issue_marker = "❌ ISSUE!" if moved_away else "✓ OK"
        
        print(f"${price:<9,.0f} | {dist_before:>7,.0f} ({pct_before:>5.2f}%) | ${position.take_profit:>10,.0f} ({pct_after:>5.2f}%) | {issue_marker}")
        
        if moved_away:
            issues_found.append(f"At ${price:,.0f}, TP moved from ${price + dist_before:,.0f} to ${position.take_profit:,.0f}")
    
    print("\n" + "=" * 80)
    if issues_found:
        print("❌ TEST FAILED - TP moved away from price:")
        for issue in issues_found:
            print(f"  - {issue}")
        return False
    else:
        print("✓ TEST PASSED - TP never moved further away")
        return True

if __name__ == "__main__":
    success = test_tp_stays_reachable()
    exit(0 if success else 1)
