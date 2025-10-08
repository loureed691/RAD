#!/usr/bin/env python3
"""
Focused test to demonstrate the position sizing fix works correctly
and prevents the 10x undersizing bug.
"""
import sys
sys.path.insert(0, '/home/runner/work/RAD/RAD')

from risk_manager import RiskManager

def test_leverage_bug_is_fixed():
    """
    Test that verifies the leverage bug is fixed.
    
    The OLD BUG was:
    position_value = risk_amount / (price_distance * leverage)
    
    This made positions leverage-times too SMALL.
    Example: With 10x leverage and 2% risk, traders only risked 0.2%
    
    The FIX is:
    position_value = risk_amount / price_distance
    
    Leverage doesn't affect risk calculation - it only affects margin.
    """
    print("="*80)
    print("TESTING: LEVERAGE BUG FIX")
    print("="*80)
    
    rm = RiskManager(max_position_size=100000, risk_per_trade=0.02, max_open_positions=3)
    
    balance = 10000
    entry = 100.0
    stop_loss = 95.0  # 5% stop loss
    target_risk_pct = 0.02  # 2% risk per trade
    
    print(f"\nTest Setup:")
    print(f"  Balance: ${balance:,.2f}")
    print(f"  Entry Price: ${entry:.2f}")
    print(f"  Stop Loss: ${stop_loss:.2f} (5% away)")
    print(f"  Target Risk: {target_risk_pct*100:.1f}%")
    
    # Test with different leverages - risk should be the same for all
    leverages = [1, 5, 10, 20, 50]
    
    print(f"\n{'Leverage':<12} {'Position Size':<18} {'Position Value':<18} {'Actual Risk':<15} {'Risk %':<10} {'Status':<10}")
    print("-" * 90)
    
    all_passed = True
    expected_risk_usd = balance * target_risk_pct  # $200
    
    for leverage in leverages:
        position_size = rm.calculate_position_size(
            balance=balance,
            entry_price=entry,
            stop_loss_price=stop_loss,
            leverage=leverage,
            risk_per_trade=target_risk_pct
        )
        
        position_value = position_size * entry
        price_distance = abs(entry - stop_loss) / entry
        actual_risk_usd = position_value * price_distance
        actual_risk_pct = (actual_risk_usd / balance) * 100
        
        # Check if risk is correct (should be 2.0% regardless of leverage)
        risk_is_correct = abs(actual_risk_pct - (target_risk_pct * 100)) < 0.01
        status = "✓ PASS" if risk_is_correct else "✗ FAIL"
        
        print(f"{leverage:2d}x          {position_size:8.4f} contracts  ${position_value:8.2f}         ${actual_risk_usd:8.2f}      {actual_risk_pct:4.2f}%     {status}")
        
        if not risk_is_correct:
            all_passed = False
    
    print("-" * 90)
    
    # Verify the bug is fixed
    if all_passed:
        print("\n✅ SUCCESS! All leverages produce the correct 2.00% risk")
        print("   The leverage bug has been FIXED!")
        print(f"   Expected risk: ${expected_risk_usd:.2f}")
        return True
    else:
        print("\n❌ FAILURE! Risk varies with leverage (BUG STILL EXISTS)")
        return False

def test_before_and_after_comparison():
    """
    Show the difference between old buggy code and new fixed code
    """
    print("\n" + "="*80)
    print("BEFORE vs AFTER COMPARISON")
    print("="*80)
    
    balance = 10000
    entry = 100.0
    stop_loss = 95.0
    leverage = 10
    risk_pct = 0.02
    
    price_distance = abs(entry - stop_loss) / entry
    risk_amount = balance * risk_pct
    
    # OLD (BUGGY) calculation
    old_position_value = risk_amount / (price_distance * leverage)
    old_position_size = old_position_value / entry
    old_actual_risk = old_position_value * price_distance
    
    # NEW (FIXED) calculation
    new_position_value = risk_amount / price_distance
    new_position_size = new_position_value / entry
    new_actual_risk = new_position_value * price_distance
    
    print(f"\nTest: ${balance} balance, ${entry} entry, ${stop_loss} SL, {leverage}x leverage, {risk_pct*100}% risk")
    print(f"\n{'Calculation':<15} {'Position Size':<18} {'Position Value':<18} {'Actual Risk':<15}")
    print("-" * 70)
    print(f"OLD (BUGGY):    {old_position_size:8.4f} contracts  ${old_position_value:8.2f}         ${old_actual_risk:8.2f} ({old_actual_risk/balance*100:.2f}%)")
    print(f"NEW (FIXED):    {new_position_size:8.4f} contracts  ${new_position_value:8.2f}         ${new_actual_risk:8.2f} ({new_actual_risk/balance*100:.2f}%)")
    print("-" * 70)
    
    difference_pct = ((new_position_size / old_position_size) - 1) * 100
    
    print(f"\nOLD BUG IMPACT:")
    print(f"  • Positions were {abs(difference_pct):.0f}% too SMALL")
    print(f"  • With 10x leverage, 2% risk became 0.2% risk")
    print(f"  • Traders were under-allocated by a factor of {leverage}x")
    print(f"\nFIX IMPACT:")
    print(f"  • Now correctly risking ${new_actual_risk:.2f} ({risk_pct*100}%) as intended")
    print(f"  • Position size increased from {old_position_size:.4f} to {new_position_size:.4f} contracts")

if __name__ == '__main__':
    print("\n" + "="*80)
    print("POSITION SIZING BUG FIX - COMPREHENSIVE TEST")
    print("="*80)
    
    test1_passed = test_leverage_bug_is_fixed()
    test_before_and_after_comparison()
    
    print("\n" + "="*80)
    if test1_passed:
        print("✅ ALL TESTS PASSED - Position sizing bug is FIXED!")
    else:
        print("❌ TESTS FAILED - Bug still exists!")
    print("="*80 + "\n")
    
    sys.exit(0 if test1_passed else 1)
