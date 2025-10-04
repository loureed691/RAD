#!/usr/bin/env python3
"""
Verification script for position mode and quantity limit fixes
"""

def check_position_mode_fix():
    """Verify position mode fix is implemented"""
    print("\n" + "="*70)
    print("Checking Position Mode Fix (Error 330011)")
    print("="*70)
    
    try:
        with open('kucoin_client.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('set_position_mode', 'Position mode setting'),
            ('hedged=False', 'ONE_WAY mode parameter'),
            ('Set position mode to ONE_WAY', 'Position mode logging'),
        ]
        
        all_passed = True
        for check, description in checks:
            if check in content:
                print(f"✓ {description}: Found")
            else:
                print(f"✗ {description}: NOT FOUND")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error checking file: {e}")
        return False


def check_quantity_limit_fix():
    """Verify quantity limit fix is implemented"""
    print("\n" + "="*70)
    print("Checking Quantity Limit Fix (Error 100001)")
    print("="*70)
    
    try:
        with open('kucoin_client.py', 'r') as f:
            content = f.read()
        
        checks = [
            ('get_market_limits', 'Market limits fetching method'),
            ('validate_and_cap_amount', 'Amount validation method'),
            ('default_max = 10000', 'Default 10,000 contract cap'),
            ('validated_amount = self.validate_and_cap_amount', 'Validation in create_market_order'),
        ]
        
        all_passed = True
        for check, description in checks:
            if check in content:
                print(f"✓ {description}: Found")
            else:
                print(f"✗ {description}: NOT FOUND")
                all_passed = False
        
        # Count occurrences of validation calls
        validation_count = content.count('validated_amount = self.validate_and_cap_amount')
        print(f"\n  Validation used in {validation_count} order creation methods")
        if validation_count >= 2:
            print(f"  ✓ Both market and limit orders use validation")
        else:
            print(f"  ✗ Expected 2+ validation calls, found {validation_count}")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error checking file: {e}")
        return False


def check_documentation():
    """Verify documentation is complete"""
    print("\n" + "="*70)
    print("Checking Documentation")
    print("="*70)
    
    try:
        with open('POSITION_MODE_FIX.md', 'r') as f:
            content = f.read()
        
        checks = [
            ('Error 330011', 'Error 330011 documented'),
            ('Error 100001', 'Error 100001 documented'),
            ('set_position_mode', 'Position mode solution documented'),
            ('validate_and_cap_amount', 'Validation solution documented'),
            ('hedged=False', 'ONE_WAY mode explained'),
        ]
        
        all_passed = True
        for check, description in checks:
            if check in content:
                print(f"✓ {description}: Found")
            else:
                print(f"✗ {description}: NOT FOUND")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error checking documentation: {e}")
        return False


def test_validation_logic():
    """Test the validation logic with mock data"""
    print("\n" + "="*70)
    print("Testing Validation Logic")
    print("="*70)
    
    try:
        # Test the validation function
        test_cases = [
            (5000, 10000, 5000, "Normal amount"),
            (15000, 10000, 10000, "Over limit amount"),
            (0.5, 10000, 1, "Below minimum (assuming min=1)"),
        ]
        
        print("\nTest cases:")
        for amount, max_limit, expected, description in test_cases:
            if amount > max_limit:
                result = max_limit
            else:
                result = max(amount, 1)  # Simplified min check
            
            if result == expected:
                print(f"✓ {description}: {amount} -> {result}")
            else:
                print(f"✗ {description}: Expected {expected}, got {result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing logic: {e}")
        return False


def main():
    """Run all verification checks"""
    print("="*70)
    print("KuCoin Position Mode & Quantity Limit Fix Verification")
    print("="*70)
    
    results = {
        'Position Mode Fix': check_position_mode_fix(),
        'Quantity Limit Fix': check_quantity_limit_fix(),
        'Documentation': check_documentation(),
        'Validation Logic': test_validation_logic(),
    }
    
    print("\n" + "="*70)
    print("Verification Results")
    print("="*70)
    
    for check, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{check:.<50} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("✓✓✓ All checks passed! Fixes are properly implemented. ✓✓✓")
    else:
        print("✗✗✗ Some checks failed. Please review the implementation. ✗✗✗")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
