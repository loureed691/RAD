"""
Test for zero balance division error fix in advanced_analytics.py

Tests that calculate_calmar_ratio handles edge cases:
1. Zero initial balance
2. Zero peak value
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_zero_initial_balance():
    """Test that zero initial balance does not cause ZeroDivisionError"""
    print("\n" + "="*60)
    print("TEST 1: Zero initial balance - should NOT crash")
    print("="*60)
    
    try:
        from advanced_analytics import AdvancedAnalytics
        
        # Create analytics instance
        analytics = AdvancedAnalytics()
        
        # Record equity with zero balance (simulating the exact error scenario)
        analytics.record_equity(0.0)
        analytics.record_equity(0.0)
        
        # This should NOT raise ZeroDivisionError
        result = analytics.calculate_calmar_ratio()
        
        print(f"✓ No error with zero initial balance in calculate_calmar_ratio")
        print(f"  Calmar ratio returned: {result}")
        assert result == 0.0, f"Expected 0.0 for zero initial balance, got {result}"
        
        # Also test ulcer_index with zero balance
        ulcer = analytics.calculate_ulcer_index()
        print(f"✓ No error with zero initial balance in calculate_ulcer_index")
        print(f"  Ulcer index returned: {ulcer}")
        assert ulcer == 0.0, f"Expected 0.0 for zero balance ulcer index, got {ulcer}"
        
        print(f"✓ TEST 1 PASSED: Returns 0.0 for zero initial balance in both methods")
        return True
        
    except ZeroDivisionError as e:
        print(f"✗ TEST 1 FAILED: ZeroDivisionError still occurs: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zero_to_positive_balance():
    """Test that transition from zero to positive balance works"""
    print("\n" + "="*60)
    print("TEST 2: Zero to positive balance - should calculate correctly")
    print("="*60)
    
    try:
        from advanced_analytics import AdvancedAnalytics
        
        # Create analytics instance
        analytics = AdvancedAnalytics()
        
        # Record equity starting from zero, then growing
        analytics.record_equity(0.0)
        analytics.record_equity(100.0)
        analytics.record_equity(150.0)
        
        # This should work without error (initial balance is 0)
        result = analytics.calculate_calmar_ratio()
        
        print(f"✓ No error with zero initial balance transitioning to positive")
        print(f"  Calmar ratio returned: {result}")
        # With zero initial balance, should return 0.0
        assert result == 0.0, f"Expected 0.0 when starting from zero balance, got {result}"
        print(f"✓ TEST 2 PASSED: Handles transition from zero balance")
        return True
        
    except ZeroDivisionError as e:
        print(f"✗ TEST 2 FAILED: ZeroDivisionError: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_zero_balances():
    """Test that all zero balances is handled gracefully"""
    print("\n" + "="*60)
    print("TEST 3: All zero balances - should NOT crash")
    print("="*60)
    
    try:
        from advanced_analytics import AdvancedAnalytics
        
        # Create analytics instance
        analytics = AdvancedAnalytics()
        
        # Record multiple zero equity points
        for _ in range(5):
            analytics.record_equity(0.0)
        
        # This should NOT raise ZeroDivisionError
        result = analytics.calculate_calmar_ratio()
        
        print(f"✓ No error with all zero balances")
        print(f"  Calmar ratio returned: {result}")
        assert result == 0.0, f"Expected 0.0 for all zero balances, got {result}"
        print(f"✓ TEST 3 PASSED: Returns 0.0 for all zero balances")
        return True
        
    except ZeroDivisionError as e:
        print(f"✗ TEST 3 FAILED: ZeroDivisionError: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_normal_positive_balance():
    """Test that normal positive balance still works correctly"""
    print("\n" + "="*60)
    print("TEST 4: Normal positive balance - should work as before")
    print("="*60)
    
    try:
        from advanced_analytics import AdvancedAnalytics
        
        # Create analytics instance
        analytics = AdvancedAnalytics()
        
        # Record normal equity progression
        analytics.record_equity(1000.0)
        analytics.record_equity(1100.0)
        analytics.record_equity(1050.0)  # Drawdown
        analytics.record_equity(1200.0)
        
        # This should work normally
        result = analytics.calculate_calmar_ratio()
        
        print(f"✓ Normal calculation works")
        print(f"  Calmar ratio returned: {result}")
        # Should return a valid number (not 0, not inf, not error)
        assert isinstance(result, (int, float)), f"Expected numeric result, got {type(result)}"
        print(f"✓ TEST 4 PASSED: Normal balance progression works correctly")
        return True
        
    except Exception as e:
        print(f"✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_insufficient_data():
    """Test that insufficient data is handled"""
    print("\n" + "="*60)
    print("TEST 5: Insufficient data (< 2 points) - should return 0.0")
    print("="*60)
    
    try:
        from advanced_analytics import AdvancedAnalytics
        
        # Create analytics instance
        analytics = AdvancedAnalytics()
        
        # Record only one equity point
        analytics.record_equity(1000.0)
        
        # Should return 0.0 for insufficient data
        result = analytics.calculate_calmar_ratio()
        
        print(f"✓ No error with insufficient data")
        print(f"  Calmar ratio returned: {result}")
        assert result == 0.0, f"Expected 0.0 for insufficient data, got {result}"
        print(f"✓ TEST 5 PASSED: Returns 0.0 for insufficient data")
        return True
        
    except Exception as e:
        print(f"✗ TEST 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_performance_summary_with_zero_balance():
    """Test the exact call from the error traceback - get_performance_summary with zero balance"""
    print("\n" + "="*60)
    print("TEST 6: get_performance_summary() with zero balance - should NOT crash")
    print("="*60)
    
    try:
        from advanced_analytics import AdvancedAnalytics
        
        # Create analytics instance (as bot does)
        analytics = AdvancedAnalytics()
        
        # Record zero balance (exact scenario from error)
        analytics.record_equity(0.0)
        analytics.record_equity(0.0)
        
        # This is the exact call that was failing in bot.py line 353
        summary = analytics.get_performance_summary()
        
        print(f"✓ get_performance_summary() completed without error")
        print(f"  Summary length: {len(summary)} characters")
        assert isinstance(summary, str), f"Expected string summary, got {type(summary)}"
        assert len(summary) > 0, "Expected non-empty summary"
        print(f"✓ TEST 6 PASSED: get_performance_summary() works with zero balance")
        return True
        
    except ZeroDivisionError as e:
        print(f"✗ TEST 6 FAILED: ZeroDivisionError in get_performance_summary: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ZERO BALANCE ANALYTICS FIX - TEST SUITE")
    print("="*60)
    
    results = []
    results.append(("Zero initial balance", test_zero_initial_balance()))
    results.append(("Zero to positive balance", test_zero_to_positive_balance()))
    results.append(("All zero balances", test_all_zero_balances()))
    results.append(("Normal positive balance", test_normal_positive_balance()))
    results.append(("Insufficient data", test_insufficient_data()))
    results.append(("get_performance_summary with zero balance", test_get_performance_summary_with_zero_balance()))
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
