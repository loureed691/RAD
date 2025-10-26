#!/usr/bin/env python3
"""
Test for diversification check bug fix

This test verifies that the diversification check now correctly uses the actual
number of open positions rather than the theoretical maximum when calculating
concentration limits.

Bug: Previously used max_open_positions instead of actual positions count,
allowing scenarios where all positions could be concentrated in one group.
"""

import sys
from typing import Tuple

def test_diversification_uses_actual_positions():
    """
    Test that diversification limits are based on actual positions, not max_open_positions
    
    This prevents the bug where with max_open_positions=10 and only 3 actual positions,
    the system would allow up to 4 positions in one group (40% of 10), meaning all 3
    positions plus 1 more could be in the same group = 100% concentration.
    """
    print("\n" + "="*60)
    print("TESTING DIVERSIFICATION FIX")
    print("="*60)
    
    try:
        from risk_manager import RiskManager
        
        # Use a high max_open_positions to expose the bug
        manager = RiskManager(
            max_position_size=1000,
            risk_per_trade=0.02,
            max_open_positions=10  # High limit
        )
        
        # Test 1: With 3 positions all in one group, should reject 4th in same group
        print("\n  Test 1: Prevent over-concentration in layer1 group")
        existing = ['SOL/USDT:USDT', 'AVAX/USDT:USDT', 'DOT/USDT:USDT']
        print(f"    Existing: {len(existing)} positions, all layer1")
        
        # With 3 positions total: max_group = max(2, int(3 * 0.4)) = 2
        # Current count = 3, should reject
        is_ok, reason = manager.check_portfolio_diversification('NEAR/USDT:USDT', existing)
        assert not is_ok, f"Should reject 4th position in same group when only 3 total: {reason}"
        print(f"    ✓ Correctly rejected: {reason}")
        
        # Test 2: With 5 positions, 3 in one group, should reject 4th
        print("\n  Test 2: With 5 positions, prevent 4th in one group")
        existing2 = ['SOL/USDT:USDT', 'AVAX/USDT:USDT', 'DOT/USDT:USDT', 
                     'BTC/USDT:USDT', 'UNI/USDT:USDT']
        print(f"    Existing: {len(existing2)} positions")
        print(f"      layer1: SOL, AVAX, DOT")
        print(f"      major_coins: BTC")
        print(f"      defi: UNI")
        
        # With 5 positions: max_group = max(2, int(5 * 0.4)) = 2
        # layer1 has 3 positions, should reject another
        is_ok2, reason2 = manager.check_portfolio_diversification('NEAR/USDT:USDT', existing2)
        assert not is_ok2, f"Should reject when group already at limit: {reason2}"
        print(f"    ✓ Correctly rejected: {reason2}")
        
        # Test 3: Should allow adding to a different group
        print("\n  Test 3: Allow adding to underrepresented group")
        is_ok3, reason3 = manager.check_portfolio_diversification('PEPE/USDT:USDT', existing2)
        assert is_ok3, f"Should allow position in different group: {reason3}"
        print(f"    ✓ Correctly allowed: {reason3}")
        
        # Test 4: Edge case with only 2 positions
        print("\n  Test 4: Edge case with 2 positions")
        existing4 = ['BTC/USDT:USDT']
        # With 1 position: max = max(2, int(1*0.4)) = 2
        # Should allow 2nd position even in same group (minimum diversity)
        is_ok4, reason4 = manager.check_portfolio_diversification('ETH/USDT:USDT', existing4)
        assert is_ok4, f"Should allow 2nd position for minimum portfolio: {reason4}"
        print(f"    ✓ Correctly allowed: {reason4}")
        
        print("\n✓ All diversification fix tests passed!")
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_old_bug_scenario():
    """
    Demonstrate the specific bug that was fixed
    
    Before fix: With max_open_positions=10 and 3 actual positions,
    concentration limit was 4 (40% of 10), allowing poor diversification.
    
    After fix: With 3 actual positions, concentration limit is 2 (max of 2 or 40% of 3),
    ensuring better diversification.
    """
    print("\n" + "="*60)
    print("DEMONSTRATING OLD BUG SCENARIO (NOW FIXED)")
    print("="*60)
    
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(
            max_position_size=1000,
            risk_per_trade=0.02,
            max_open_positions=10
        )
        
        print("\n  Scenario: 3 positions, trying to add 4th in same group")
        print("  Before fix: Would incorrectly ALLOW (limit based on max_open_positions=10)")
        print("  After fix: Should correctly REJECT (limit based on actual positions=3)")
        
        existing = ['SOL/USDT:USDT', 'AVAX/USDT:USDT', 'DOT/USDT:USDT']
        is_ok, reason = manager.check_portfolio_diversification('NEAR/USDT:USDT', existing)
        
        print(f"\n  Result: {'ALLOWED' if is_ok else 'REJECTED'}")
        print(f"  Reason: {reason}")
        
        if not is_ok:
            print("\n  ✓ Bug is FIXED! Correctly rejected over-concentration.")
            return True
        else:
            print("\n  ✗ Bug still exists! Should have rejected this.")
            return False
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DIVERSIFICATION FIX TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Diversification uses actual positions", test_diversification_uses_actual_positions()))
    results.append(("Old bug scenario (fixed)", test_old_bug_scenario()))
    
    # Summary
    print("\n" + "="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    print("="*60)
    
    for test_name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {test_name}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)
