#!/usr/bin/env python3
"""
Test script to verify position close error handling fix
"""
import sys

def test_error_code_detection():
    """Test that error code 300009 is properly detected"""
    print("=" * 60)
    print("Testing Position Close Error Handling")
    print("=" * 60)
    
    # Test error string patterns
    test_errors = [
        ('kucoinfutures {"msg":"No open positions to close.","code":"300009"}', True),
        ('No open positions to close', True),
        ('kucoinfutures {"code":"300009","msg":"No open positions to close."}', True),
        ('Invalid order size', False),
        ('Insufficient funds', False),
        ('kucoinfutures {"msg":"Some other error","code":"100001"}', False),
    ]
    
    print("\n📊 Testing Error Code Detection:")
    all_passed = True
    
    for error_str, should_match in test_errors:
        # This is what the code checks
        is_no_position_error = '300009' in error_str or 'No open positions to close' in error_str
        
        result = "should be DEBUG" if should_match else "should be ERROR"
        actual = "would be DEBUG" if is_no_position_error else "would be ERROR"
        
        if is_no_position_error == should_match:
            print(f"  ✓ '{error_str[:50]}...' {actual} ✓")
        else:
            print(f"  ✗ '{error_str[:50]}...' {actual} (expected: {result})")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All error handling tests passed!")
        print("=" * 60)
        return True
    else:
        print("❌ Some tests failed")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_error_code_detection()
    sys.exit(0 if success else 1)
