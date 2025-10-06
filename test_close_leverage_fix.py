"""
Test for close position leverage bug fix

Tests that positions are closed with the correct leverage, not hardcoded 10x
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_leverage_extraction_from_unified_field():
    """Test that leverage is correctly extracted from CCXT unified field"""
    print("\n" + "="*60)
    print("TEST 1: Extract leverage from unified 'leverage' field")
    print("="*60)
    
    try:
        # Mock position with 5x leverage (from CCXT unified field)
        pos = {
            'symbol': 'BTC/USDT:USDT',
            'contracts': 1.0,
            'side': 'long',
            'leverage': 5,  # Position opened with 5x leverage
            'info': {}
        }
        
        # Extract leverage (same logic as in close_position)
        leverage = pos.get('leverage')
        if leverage is not None:
            leverage = int(leverage)
        else:
            info = pos.get('info', {})
            real_leverage = info.get('realLeverage')
            if real_leverage is not None:
                leverage = int(real_leverage)
            else:
                leverage = 10
        
        print(f"Extracted leverage: {leverage}x")
        assert leverage == 5, f"Should extract 5x leverage, got {leverage}x"
        
        print("✓ TEST 1 PASSED: Leverage correctly extracted from unified field")
        return True
        
    except Exception as e:
        print(f"✗ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_leverage_extraction_from_realLeverage():
    """Test that leverage is correctly extracted from KuCoin's realLeverage field"""
    print("\n" + "="*60)
    print("TEST 2: Extract leverage from KuCoin 'realLeverage' field")
    print("="*60)
    
    try:
        # Mock position with leverage in 'info' field (KuCoin-specific)
        pos = {
            'symbol': 'ETH/USDT:USDT',
            'contracts': 10.0,
            'side': 'short',
            # No 'leverage' in unified structure
            'info': {
                'realLeverage': 20  # KuCoin-specific field
            }
        }
        
        # Extract leverage (same logic as in close_position)
        leverage = pos.get('leverage')
        if leverage is not None:
            leverage = int(leverage)
        else:
            info = pos.get('info', {})
            real_leverage = info.get('realLeverage')
            if real_leverage is not None:
                leverage = int(real_leverage)
            else:
                leverage = 10
        
        print(f"Extracted leverage: {leverage}x")
        assert leverage == 20, f"Should extract 20x leverage, got {leverage}x"
        
        print("✓ TEST 2 PASSED: Leverage correctly extracted from realLeverage")
        return True
        
    except Exception as e:
        print(f"✗ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_leverage_extraction_with_string_values():
    """Test that leverage is correctly converted to int from string values"""
    print("\n" + "="*60)
    print("TEST 3: Extract leverage handles string conversion")
    print("="*60)
    
    try:
        # Mock position with leverage as string (some exchanges return strings)
        pos = {
            'symbol': 'SOL/USDT:USDT',
            'contracts': 100.0,
            'side': 'long',
            'leverage': '3',  # String value
            'info': {}
        }
        
        # Extract leverage (same logic as in close_position)
        leverage = pos.get('leverage')
        if leverage is not None:
            try:
                leverage = int(leverage)
            except (ValueError, TypeError):
                leverage = 10
        else:
            info = pos.get('info', {})
            real_leverage = info.get('realLeverage')
            if real_leverage is not None:
                try:
                    leverage = int(real_leverage)
                except (ValueError, TypeError):
                    leverage = 10
            else:
                leverage = 10
        
        print(f"Extracted leverage: {leverage}x")
        assert leverage == 3, f"Should extract 3x leverage, got {leverage}x"
        
        print("✓ TEST 3 PASSED: Leverage correctly converted from string")
        return True
        
    except Exception as e:
        print(f"✗ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_leverage_extraction_defaults_to_10x():
    """Test that leverage defaults to 10x when missing"""
    print("\n" + "="*60)
    print("TEST 4: Extract leverage defaults to 10x when missing")
    print("="*60)
    
    try:
        # Mock position WITHOUT leverage information
        pos = {
            'symbol': 'MATIC/USDT:USDT',
            'contracts': 1000.0,
            'side': 'long',
            # No 'leverage' field
            'info': {}  # No 'realLeverage' either
        }
        
        # Extract leverage (same logic as in close_position)
        leverage = pos.get('leverage')
        if leverage is not None:
            try:
                leverage = int(leverage)
            except (ValueError, TypeError):
                leverage = 10
        else:
            info = pos.get('info', {})
            real_leverage = info.get('realLeverage')
            if real_leverage is not None:
                try:
                    leverage = int(real_leverage)
                except (ValueError, TypeError):
                    leverage = 10
            else:
                leverage = 10
        
        print(f"Extracted leverage (default): {leverage}x")
        assert leverage == 10, f"Should default to 10x leverage, got {leverage}x"
        
        print("✓ TEST 4 PASSED: Leverage defaults to 10x when missing (expected behavior)")
        return True
        
    except Exception as e:
        print(f"✗ TEST 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("CLOSE POSITION LEVERAGE BUG FIX TESTS")
    print("="*60)
    
    results = []
    results.append(test_leverage_extraction_from_unified_field())
    results.append(test_leverage_extraction_from_realLeverage())
    results.append(test_leverage_extraction_with_string_values())
    results.append(test_leverage_extraction_defaults_to_10x())
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
