"""
Comprehensive test simulating a complete trading scenario
to verify that TP/SL strategies work correctly
"""
import sys
from unittest.mock import MagicMock
sys.modules['kucoin_client'] = MagicMock()

from position_manager import Position

def test_long_position_reaches_tp():
    """Simulate a LONG position that should reach TP"""
    print("\n" + "=" * 80)
    print("SCENARIO 1: LONG Position Should Reach Take Profit")
    print("=" * 80)
    
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,  # 5% SL (-50% ROI)
        take_profit=55000.0  # 10% TP (+100% ROI)
    )
    
    print(f"\nPosition Setup:")
    print(f"  Entry: ${position.entry_price:,.0f}")
    print(f"  Stop Loss: ${position.stop_loss:,.0f} (5% below)")
    print(f"  Take Profit: ${position.take_profit:,.0f} (10% above)")
    print(f"  Leverage: {position.leverage}x")
    
    # Simulate price moving toward TP with periodic updates
    price_progression = [
        (50500, "Small move up"),
        (51000, "2% gain"),
        (51500, "3% gain"),
        (52000, "4% gain - strong momentum"),
        (53000, "6% gain - approaching TP"),
        (54000, "8% gain - very close to TP"),
        (55000, "10% gain - AT TAKE PROFIT"),
    ]
    
    print(f"\nPrice Progression:")
    print(f"{'Price':<10} | {'TP':<10} | {'Should Close?':<15} | {'Reason':<25} | Notes")
    print("-" * 95)
    
    tp_reached = False
    issues = []
    
    for price, note in price_progression:
        # Update TP with strong momentum (simulating real trading conditions)
        position.update_take_profit(
            current_price=price,
            momentum=0.04,  # Strong momentum
            trend_strength=0.75,  # Strong trend
            volatility=0.05,  # Moderate volatility
            rsi=60.0  # Bullish but not overbought
        )
        
        # Check if position should close
        should_close, reason = position.should_close(price)
        pnl = position.get_pnl(price)
        
        close_status = "YES" if should_close else "NO"
        
        print(f"${price:<9,.0f} | ${position.take_profit:<9,.0f} | {close_status:<15} | {reason:<25} | {note}")
        
        # Verify expectations
        if price < 55000 and should_close:
            issues.append(f"Position closed prematurely at ${price:,.0f} before reaching TP")
        elif price >= 55000 and not should_close:
            issues.append(f"Position didn't close at TP (price ${price:,.0f}, TP ${position.take_profit:,.0f})")
        elif price >= 55000 and should_close and reason == 'take_profit':
            tp_reached = True
    
    print("\n" + "=" * 80)
    if issues:
        print("❌ TEST FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    elif not tp_reached:
        print("❌ TEST FAILED: Position never reached take profit")
        return False
    else:
        print("✓ TEST PASSED: Position reached take profit correctly")
        return True

def test_short_position_hits_sl():
    """Simulate a SHORT position that should hit SL"""
    print("\n" + "=" * 80)
    print("SCENARIO 2: SHORT Position Should Hit Stop Loss")
    print("=" * 80)
    
    position = Position(
        symbol='ETHUSDT',
        side='short',
        entry_price=3000.0,
        amount=1.0,
        leverage=10,
        stop_loss=3150.0,  # 5% SL above (+50% loss ROI)
        take_profit=2700.0  # 10% TP below (+100% profit ROI)
    )
    
    print(f"\nPosition Setup:")
    print(f"  Entry: ${position.entry_price:,.0f}")
    print(f"  Stop Loss: ${position.stop_loss:,.0f} (5% above)")
    print(f"  Take Profit: ${position.take_profit:,.0f} (10% below)")
    print(f"  Leverage: {position.leverage}x")
    
    # Simulate price moving AGAINST position (toward SL)
    price_progression = [
        (3030, "Small move up (losing)"),
        (3060, "2% loss"),
        (3090, "3% loss"),
        (3120, "4% loss - approaching SL"),
        (3150, "5% loss - AT STOP LOSS"),
    ]
    
    print(f"\nPrice Progression (moving AGAINST short):")
    print(f"{'Price':<10} | {'SL':<10} | {'Should Close?':<15} | {'Reason':<25} | Notes")
    print("-" * 95)
    
    sl_hit = False
    issues = []
    
    for price, note in price_progression:
        # Update trailing stop (should not move UP for short in losing direction)
        old_sl = position.stop_loss
        position.update_trailing_stop(price, trailing_percentage=0.05, volatility=0.03, momentum=0.02)
        
        # Verify SL didn't move in losing direction
        if position.stop_loss > old_sl:
            issues.append(f"SHORT SL moved UP (losing direction) from ${old_sl:,.0f} to ${position.stop_loss:,.0f}")
        
        # Check if position should close
        should_close, reason = position.should_close(price)
        
        close_status = "YES" if should_close else "NO"
        
        print(f"${price:<9,.0f} | ${position.stop_loss:<9,.0f} | {close_status:<15} | {reason:<25} | {note}")
        
        # Verify expectations
        if price < 3150 and should_close:
            issues.append(f"Position closed prematurely at ${price:,.0f} before hitting SL")
        elif price >= 3150 and not should_close:
            issues.append(f"Position didn't close at SL (price ${price:,.0f}, SL ${position.stop_loss:,.0f})")
        elif price >= 3150 and should_close and reason == 'stop_loss':
            sl_hit = True
    
    print("\n" + "=" * 80)
    if issues:
        print("❌ TEST FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    elif not sl_hit:
        print("❌ TEST FAILED: Position didn't hit stop loss")
        return False
    else:
        print("✓ TEST PASSED: Position hit stop loss correctly")
        return True

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TRADING SCENARIO TESTS")
    print("=" * 80)
    print("\nTesting complete trading workflows to verify TP/SL strategies")
    
    test1 = test_long_position_reaches_tp()
    test2 = test_short_position_hits_sl()
    
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if test1 and test2:
        print("✓✓✓ ALL SCENARIOS PASSED ✓✓✓")
        print("\nThe trading strategies are working correctly:")
        print("  1. LONG positions reach their take profit targets")
        print("  2. SHORT positions hit stop loss when moving against them")
        print("  3. Take profit doesn't move away as price approaches")
        print("  4. Stop loss behaves correctly in both directions")
        exit(0)
    else:
        print("❌ SOME SCENARIOS FAILED")
        exit(1)
