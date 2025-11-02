"""
Test to verify the new leverage range (2-25x) and that leverage is not balance-based
"""
import os
import sys

def test_leverage_range():
    """Test that leverage range is 2-25x and not balance-based"""
    print("\n" + "="*60)
    print("Testing Leverage Range (2-25x, Not Balance-Based)")
    print("="*60)
    
    # Set required API credentials
    os.environ['KUCOIN_API_KEY'] = 'test'
    os.environ['KUCOIN_API_SECRET'] = 'test'
    os.environ['KUCOIN_API_PASSPHRASE'] = 'test'
    
    # Test 1: Default leverage is 10x for all balances
    print("\nTest 1: Default leverage is fixed at 10x (not balance-based)")
    
    # Clear any existing LEVERAGE override
    if 'LEVERAGE' in os.environ:
        del os.environ['LEVERAGE']
    
    # Import config fresh
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import Config
    
    test_balances = [50, 500, 5000, 50000, 200000]
    for balance in test_balances:
        Config.auto_configure_from_balance(balance)
        assert Config.LEVERAGE == 10, f"Expected 10x for ${balance}, got {Config.LEVERAGE}x"
        print(f"  ✓ ${balance:>7} balance: Leverage={Config.LEVERAGE}x (fixed)")
    
    # Test 2: Minimum leverage (2x)
    print("\nTest 2: Minimum leverage (2x)")
    os.environ['LEVERAGE'] = '2'
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import Config
    try:
        Config.validate()
        print(f"  ✓ Leverage 2x passed validation")
    except Exception as e:
        print(f"  ✗ Leverage 2x failed: {e}")
        return False
    
    # Test 3: Maximum leverage (25x)
    print("\nTest 3: Maximum leverage (25x)")
    os.environ['LEVERAGE'] = '25'
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import Config
    try:
        Config.validate()
        print(f"  ✓ Leverage 25x passed validation")
    except Exception as e:
        print(f"  ✗ Leverage 25x failed: {e}")
        return False
    
    # Test 4: Mid-range leverage (15x)
    print("\nTest 4: Mid-range leverage (15x)")
    os.environ['LEVERAGE'] = '15'
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import Config
    try:
        Config.validate()
        print(f"  ✓ Leverage 15x passed validation")
    except Exception as e:
        print(f"  ✗ Leverage 15x failed: {e}")
        return False
    
    # Test 5: Below minimum (1x - should fail)
    print("\nTest 5: Below minimum leverage (1x - should fail)")
    os.environ['LEVERAGE'] = '1'
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import Config
    try:
        Config.validate()
        print(f"  ✗ Leverage 1x should have been rejected but passed")
        return False
    except (ValueError, Exception):
        print(f"  ✓ Leverage 1x correctly rejected (below minimum)")
    
    # Test 6: Above maximum (26x - should fail)
    print("\nTest 6: Above maximum leverage (26x - should fail)")
    os.environ['LEVERAGE'] = '26'
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import Config
    try:
        Config.validate()
        print(f"  ✗ Leverage 26x should have been rejected but passed")
        return False
    except (ValueError, Exception):
        print(f"  ✓ Leverage 26x correctly rejected (above maximum)")
    
    # Test 7: Verify high leverage warning threshold
    print("\nTest 7: High leverage warning (>20x)")
    os.environ['LEVERAGE'] = '22'
    if 'config' in sys.modules:
        del sys.modules['config']
    from config import Config
    try:
        Config.validate()
        print(f"  ✓ Leverage 22x passed validation (warning expected in logs)")
    except Exception as e:
        print(f"  ✗ Leverage 22x failed: {e}")
        return False
    
    print("\n" + "="*60)
    print("✓ All leverage range tests passed!")
    print("="*60)
    return True

if __name__ == "__main__":
    try:
        success = test_leverage_range()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
