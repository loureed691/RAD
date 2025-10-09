#!/usr/bin/env python3
"""
Test to verify the P&L calculation fix
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from position_manager import Position
from datetime import datetime

def test_pnl_calculations():
    """Test that P&L is calculated correctly without leverage multiplication"""
    
    print("=" * 80)
    print("TESTING P&L CALCULATION FIX")
    print("=" * 80)
    
    # Test case 1: Long position with 10x leverage
    print("\n" + "=" * 80)
    print("TEST 1: Long Position with 10x Leverage")
    print("=" * 80)
    
    position = Position(
        symbol="BTCUSDT",
        side="long",
        entry_price=100.0,
        amount=40.0,  # 40 contracts
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0
    )
    
    test_prices = [
        (101, 0.01, 40.0),    # 1% move = $40 profit
        (102, 0.02, 80.0),    # 2% move = $80 profit
        (105, 0.05, 200.0),   # 5% move = $200 profit
        (110, 0.10, 400.0),   # 10% move = $400 profit
        (120, 0.20, 800.0),   # 20% move = $800 profit
    ]
    
    print(f"\nPosition Setup:")
    print(f"  Symbol: {position.symbol}")
    print(f"  Side: {position.side}")
    print(f"  Amount: {position.amount} contracts")
    print(f"  Entry Price: ${position.entry_price:.2f}")
    print(f"  Leverage: {position.leverage}x")
    print(f"  Position Value: ${position.amount * position.entry_price:.2f}")
    
    print(f"\n{'Price':<10} {'Expected PNL %':<18} {'Expected $ PNL':<18} {'Actual PNL %':<18} {'Status':<10}")
    print("-" * 74)
    
    all_passed = True
    for current_price, expected_pnl_pct, expected_pnl_usd in test_prices:
        actual_pnl = position.get_pnl(current_price)
        position_value = position.amount * position.entry_price
        actual_pnl_usd = actual_pnl * position_value
        
        pnl_match = abs(actual_pnl - expected_pnl_pct) < 0.0001
        usd_match = abs(actual_pnl_usd - expected_pnl_usd) < 0.01
        
        status = "✓ PASS" if (pnl_match and usd_match) else "✗ FAIL"
        if not (pnl_match and usd_match):
            all_passed = False
        
        print(f"${current_price:<9.2f} {expected_pnl_pct:<17.2%} ${expected_pnl_usd:<16.2f} {actual_pnl:<17.2%} {status}")
    
    print()
    if all_passed:
        print("✓ All long position tests PASSED")
    else:
        print("✗ Some long position tests FAILED")
    
    # Test case 2: Short position with 10x leverage
    print("\n" + "=" * 80)
    print("TEST 2: Short Position with 10x Leverage")
    print("=" * 80)
    
    position_short = Position(
        symbol="ETHUSDT",
        side="short",
        entry_price=100.0,
        amount=40.0,  # 40 contracts
        leverage=10,
        stop_loss=105.0,
        take_profit=90.0
    )
    
    test_prices_short = [
        (99, 0.01, 40.0),     # 1% move down = $40 profit
        (98, 0.02, 80.0),     # 2% move down = $80 profit
        (95, 0.05, 200.0),    # 5% move down = $200 profit
        (90, 0.10, 400.0),    # 10% move down = $400 profit
        (80, 0.20, 800.0),    # 20% move down = $800 profit
    ]
    
    print(f"\nPosition Setup:")
    print(f"  Symbol: {position_short.symbol}")
    print(f"  Side: {position_short.side}")
    print(f"  Amount: {position_short.amount} contracts")
    print(f"  Entry Price: ${position_short.entry_price:.2f}")
    print(f"  Leverage: {position_short.leverage}x")
    print(f"  Position Value: ${position_short.amount * position_short.entry_price:.2f}")
    
    print(f"\n{'Price':<10} {'Expected PNL %':<18} {'Expected $ PNL':<18} {'Actual PNL %':<18} {'Status':<10}")
    print("-" * 74)
    
    all_passed_short = True
    for current_price, expected_pnl_pct, expected_pnl_usd in test_prices_short:
        actual_pnl = position_short.get_pnl(current_price)
        position_value = position_short.amount * position_short.entry_price
        actual_pnl_usd = actual_pnl * position_value
        
        pnl_match = abs(actual_pnl - expected_pnl_pct) < 0.0001
        usd_match = abs(actual_pnl_usd - expected_pnl_usd) < 0.01
        
        status = "✓ PASS" if (pnl_match and usd_match) else "✗ FAIL"
        if not (pnl_match and usd_match):
            all_passed_short = False
        
        print(f"${current_price:<9.2f} {expected_pnl_pct:<17.2%} ${expected_pnl_usd:<16.2f} {actual_pnl:<17.2%} {status}")
    
    print()
    if all_passed_short:
        print("✓ All short position tests PASSED")
    else:
        print("✗ Some short position tests FAILED")
    
    # Test case 3: Verify leverage independence
    print("\n" + "=" * 80)
    print("TEST 3: P&L Should Be Independent of Leverage")
    print("=" * 80)
    
    current_price = 105.0
    print(f"\nTesting at price ${current_price} (5% move from $100 entry)")
    print(f"\n{'Leverage':<12} {'PNL %':<12} {'Expected':<12} {'Status':<10}")
    print("-" * 46)
    
    all_leverage_passed = True
    for lev in [1, 5, 10, 20, 50]:
        pos = Position(
            symbol="BTCUSDT",
            side="long",
            entry_price=100.0,
            amount=40.0,
            leverage=lev,
            stop_loss=95.0,
            take_profit=110.0
        )
        
        pnl = pos.get_pnl(current_price)
        expected = 0.05  # 5% price movement
        match = abs(pnl - expected) < 0.0001
        status = "✓ PASS" if match else "✗ FAIL"
        
        if not match:
            all_leverage_passed = False
        
        print(f"{lev}x{'':<10} {pnl:<11.2%} {expected:<11.2%} {status}")
    
    print()
    if all_leverage_passed:
        print("✓ P&L is correctly leverage-independent")
    else:
        print("✗ P&L incorrectly varies with leverage")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    
    if all_passed and all_passed_short and all_leverage_passed:
        print("\n✅ ALL TESTS PASSED!")
        print("\nThe P&L calculation fix is working correctly:")
        print("  • P&L represents price movement percentage")
        print("  • P&L is independent of leverage")
        print("  • Dollar P&L is calculated correctly")
        print("  • Works for both long and short positions")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("\nTests that failed:")
        if not all_passed:
            print("  • Long position P&L calculations")
        if not all_passed_short:
            print("  • Short position P&L calculations")
        if not all_leverage_passed:
            print("  • Leverage independence")
        return 1

if __name__ == "__main__":
    exit_code = test_pnl_calculations()
    sys.exit(exit_code)
