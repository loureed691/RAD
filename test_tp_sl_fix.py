"""
Comprehensive test for take profit and stop loss fix

This test demonstrates that the bot now correctly respects take profit
and stop loss targets instead of closing positions prematurely.

Issue: "the take profit and stop loss doesn't work and the strategies also don't work"
Root Cause: Immediate profit taking logic was closing positions at 12% ROI (1.2% price move
            with 10x leverage) instead of waiting for the actual take profit target.
Fix: Modified should_close() to prioritize standard TP/SL checks and only use emergency
     profit protection for extreme cases (50%+ ROI with TP >10% away).
"""
import sys
from unittest.mock import MagicMock

# Mock the KuCoinClient before importing
sys.modules['kucoin_client'] = MagicMock()

from position_manager import Position

def test_positions_reach_take_profit():
    """Test that positions stay open until reaching take profit"""
    print("\n" + "=" * 70)
    print("TEST 1: POSITIONS REACH TAKE PROFIT TARGET")
    print("=" * 70)
    
    # LONG position with 10x leverage
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,    # 5% stop loss
        take_profit=55000.0   # 10% take profit
    )
    
    print("\nLONG Position Setup:")
    print(f"  Entry: ${position.entry_price:,.0f}")
    print(f"  Stop Loss: ${position.stop_loss:,.0f} (5% loss = 50% ROI loss)")
    print(f"  Take Profit: ${position.take_profit:,.0f} (10% gain = 100% ROI gain)")
    
    # Test price progression toward take profit
    test_cases = [
        (50100, 2.0, "Just entered"),
        (50500, 10.0, "Small profit"),
        (50600, 12.0, "12% ROI - used to close here!"),
        (51000, 20.0, "Good profit"),
        (52000, 40.0, "Strong profit"),
        (54000, 80.0, "Approaching TP"),
        (55000, 100.0, "At take profit"),
    ]
    
    print("\nPrice progression:")
    print(f"{'Price':>10} | {'PNL':>6} | {'Status':>8} | {'Reason':>25} | Notes")
    print("-" * 85)
    
    all_correct = True
    for price, expected_pnl, description in test_cases:
        should_close, reason = position.should_close(price)
        pnl = position.get_pnl(price)
        status = "CLOSES" if should_close else "OPEN"
        
        # Position should only close at TP or SL
        expected_close = (price >= position.take_profit or price <= position.stop_loss)
        is_correct = (should_close == expected_close)
        
        marker = "✓" if is_correct else "✗"
        print(f"{marker} ${price:>7,} | {pnl:>5.0%} | {status:>8} | {reason:>25} | {description}")
        
        if not is_correct:
            all_correct = False
            print(f"  ERROR: Expected should_close={expected_close}")
    
    # SHORT position test
    print("\n" + "-" * 70)
    print("\nSHORT Position Setup:")
    
    position = Position(
        symbol='BTCUSDT',
        side='short',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=52500.0,    # 5% stop loss
        take_profit=45000.0   # 10% take profit
    )
    
    print(f"  Entry: ${position.entry_price:,.0f}")
    print(f"  Stop Loss: ${position.stop_loss:,.0f} (5% loss = 50% ROI loss)")
    print(f"  Take Profit: ${position.take_profit:,.0f} (10% gain = 100% ROI gain)")
    
    test_cases = [
        (49900, 2.0, "Just entered"),
        (49500, 10.0, "Small profit"),
        (49400, 12.0, "12% ROI - used to close here!"),
        (49000, 20.0, "Good profit"),
        (48000, 40.0, "Strong profit"),
        (46000, 80.0, "Approaching TP"),
        (45000, 100.0, "At take profit"),
    ]
    
    print("\nPrice progression:")
    print(f"{'Price':>10} | {'PNL':>6} | {'Status':>8} | {'Reason':>25} | Notes")
    print("-" * 85)
    
    for price, expected_pnl, description in test_cases:
        should_close, reason = position.should_close(price)
        pnl = position.get_pnl(price)
        status = "CLOSES" if should_close else "OPEN"
        
        expected_close = (price <= position.take_profit or price >= position.stop_loss)
        is_correct = (should_close == expected_close)
        
        marker = "✓" if is_correct else "✗"
        print(f"{marker} ${price:>7,} | {pnl:>5.0%} | {status:>8} | {reason:>25} | {description}")
        
        if not is_correct:
            all_correct = False
            print(f"  ERROR: Expected should_close={expected_close}")
    
    return all_correct


def test_emergency_profit_protection():
    """Test that emergency profit protection works for extreme cases"""
    print("\n" + "=" * 70)
    print("TEST 2: EMERGENCY PROFIT PROTECTION")
    print("=" * 70)
    print("\nThis safety mechanism triggers when:")
    print("  - Position has 50%+ ROI AND")
    print("  - Take profit is >10% away from current price")
    
    # Create position with TP very far away
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,
        take_profit=65000.0  # 30% away - unrealistic TP
    )
    
    print(f"\nPosition with unrealistic TP:")
    print(f"  Entry: ${position.entry_price:,.0f}")
    print(f"  Take Profit: ${position.take_profit:,.0f} (30% away)")
    
    # Test cases
    test_cases = [
        (52000, 40.0, False, "Good profit but TP still reasonable"),
        (54000, 80.0, True, "Strong profit (80% ROI), TP far away (20%)"),
        (55000, 100.0, True, "Extreme profit (100% ROI), TP very far (18% away)"),
    ]
    
    print("\n" + f"{'Price':>10} | {'PNL':>6} | {'Dist to TP':>11} | {'Protection?':>12} | Notes")
    print("-" * 75)
    
    all_correct = True
    for price, expected_pnl, should_protect, description in test_cases:
        should_close, reason = position.should_close(price)
        pnl = position.get_pnl(price)
        distance_to_tp = (position.take_profit - price) / price
        
        protected = (reason == 'emergency_profit_protection')
        is_correct = (protected == should_protect)
        
        marker = "✓" if is_correct else "✗"
        print(f"{marker} ${price:>7,} | {pnl:>5.0%} | {distance_to_tp:>10.1%} | {'Yes' if protected else 'No':>12} | {description}")
        
        if not is_correct:
            all_correct = False
            print(f"  ERROR: Expected protection={should_protect}, got={protected}")
    
    return all_correct


def test_stop_loss_triggers():
    """Test that stop loss still triggers correctly"""
    print("\n" + "=" * 70)
    print("TEST 3: STOP LOSS TRIGGERS CORRECTLY")
    print("=" * 70)
    
    position = Position(
        symbol='BTCUSDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,
        take_profit=55000.0
    )
    
    print(f"\nLONG Position: Entry=${position.entry_price:,.0f}, SL=${position.stop_loss:,.0f}")
    
    test_cases = [
        (48000, -40.0, False, "Losing but above SL"),
        (47500, -50.0, True, "At stop loss"),
        (47000, -60.0, True, "Below stop loss"),
    ]
    
    print("\n" + f"{'Price':>10} | {'PNL':>6} | {'Triggers SL?':>13} | Notes")
    print("-" * 60)
    
    all_correct = True
    for price, expected_pnl, should_trigger, description in test_cases:
        should_close, reason = position.should_close(price)
        pnl = position.get_pnl(price)
        
        triggered = (reason == 'stop_loss')
        is_correct = (triggered == should_trigger)
        
        marker = "✓" if is_correct else "✗"
        print(f"{marker} ${price:>7,} | {pnl:>5.0%} | {'Yes' if triggered else 'No':>13} | {description}")
        
        if not is_correct:
            all_correct = False
            print(f"  ERROR: Expected SL trigger={should_trigger}, got={triggered}")
    
    return all_correct


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE TAKE PROFIT AND STOP LOSS FIX TEST")
    print("=" * 70)
    print("\nProblem: Positions were closing at 12% ROI (1.2% price move with 10x)")
    print("         instead of reaching the intended take profit targets.")
    print("\nFix: Modified should_close() to respect TP/SL targets and only use")
    print("     emergency profit protection for extreme cases.")
    print("=" * 70)
    
    results = {
        "Positions reach TP": test_positions_reach_take_profit(),
        "Emergency protection": test_emergency_profit_protection(),
        "Stop loss triggers": test_stop_loss_triggers(),
    }
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "=" * 70)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("=" * 70)
        print("\nThe bot now correctly:")
        print("  1. Respects take profit targets (waits for TP)")
        print("  2. Respects stop loss targets (triggers at SL)")
        print("  3. Has emergency protection for extreme cases")
        print("  4. Allows positions to reach their intended targets")
        print("=" * 70)
    else:
        print("\n✗ Some tests failed")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
