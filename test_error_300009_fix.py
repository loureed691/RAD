#!/usr/bin/env python3
"""
Test to verify error 300009 'No open positions to close' is handled gracefully.

This test simulates the exact scenario from the problem statement:
- Trying to close a position that doesn't exist on the exchange
- Error 300009: "No open positions to close"
- Verifies it's now treated as a success case instead of an error
"""
import sys
from unittest.mock import Mock, patch
import ccxt

# Add parent directory to path
sys.path.insert(0, '.')

from kucoin_client import KuCoinClient

def test_error_300009_market_order():
    """Test error 300009 handling with market order"""
    print("\n" + "=" * 70)
    print("TEST: Error 300009 handling with reduce_only market order")
    print("=" * 70)
    
    with patch('ccxt.kucoinfutures') as mock_exchange_class:
        mock_exchange = Mock()
        mock_exchange_class.return_value = mock_exchange
        mock_exchange.set_position_mode = Mock()
        mock_exchange.set_margin_mode = Mock()
        mock_exchange.set_leverage = Mock()
        mock_exchange.load_markets = Mock(return_value={
            'ENS/USDT:USDT': {
                'limits': {
                    'amount': {'min': 1, 'max': 10000},
                    'cost': {'min': 10, 'max': 1000000}
                }
            }
        })
        mock_exchange.fetch_ticker = Mock(return_value={
            'last': 21.092,
            'bid': 21.09,
            'ask': 21.095
        })
        
        # Simulate the exact error from the problem statement
        mock_exchange.create_order = Mock(
            side_effect=ccxt.InvalidOrder(
                'kucoinfutures {"msg":"No open positions to close.","code":"300009"}'
            )
        )
        
        client = KuCoinClient('test_key', 'test_secret', 'test_pass')
        
        print("\nScenario: Trying to close ENS/USDT:USDT position that doesn't exist")
        print("  Expected: Error 300009 should be handled gracefully")
        print("  Before fix: Would log error and return None")
        print("  After fix: Should return success response")
        print()
        
        # This should NOT log an error now
        order = client.create_market_order(
            'ENS/USDT:USDT', 'sell', 0.1875, leverage=10, reduce_only=True
        )
        
        print(f"Result: {order}")
        print()
        
        # Verify the fix
        if order is None:
            print("❌ FAIL: Returned None (old behavior)")
            return False
        
        if order.get('status') != 'closed':
            print(f"❌ FAIL: Status is '{order.get('status')}', expected 'closed'")
            return False
        
        if 'already closed' not in order.get('info', '').lower():
            print(f"❌ FAIL: Info doesn't mention 'already closed': {order.get('info')}")
            return False
        
        print("✅ SUCCESS: Error 300009 handled gracefully!")
        print("   - Returned success response instead of None")
        print("   - Status: 'closed'")
        print("   - Info: Position already closed")
        print()
        return True

def test_error_300009_exchange_error():
    """Test error 300009 handling when raised as ExchangeError"""
    print("\n" + "=" * 70)
    print("TEST: Error 300009 handling as ExchangeError")
    print("=" * 70)
    
    with patch('ccxt.kucoinfutures') as mock_exchange_class:
        mock_exchange = Mock()
        mock_exchange_class.return_value = mock_exchange
        mock_exchange.set_position_mode = Mock()
        mock_exchange.set_margin_mode = Mock()
        mock_exchange.set_leverage = Mock()
        mock_exchange.load_markets = Mock(return_value={
            'ENS/USDT:USDT': {
                'limits': {
                    'amount': {'min': 1, 'max': 10000},
                    'cost': {'min': 10, 'max': 1000000}
                }
            }
        })
        mock_exchange.fetch_ticker = Mock(return_value={
            'last': 21.092,
            'bid': 21.09,
            'ask': 21.095
        })
        
        # Some exchanges may raise ExchangeError instead of InvalidOrder
        mock_exchange.create_order = Mock(
            side_effect=ccxt.ExchangeError(
                'kucoinfutures {"msg":"No open positions to close.","code":"300009"}'
            )
        )
        
        client = KuCoinClient('test_key', 'test_secret', 'test_pass')
        
        print("\nScenario: Error 300009 raised as ExchangeError")
        print()
        
        order = client.create_market_order(
            'ENS/USDT:USDT', 'sell', 1.0, leverage=10, reduce_only=True
        )
        
        print(f"Result: {order}")
        print()
        
        if order and order.get('status') == 'closed':
            print("✅ SUCCESS: ExchangeError with 300009 also handled!")
            print()
            return True
        else:
            print("❌ FAIL: Not handled correctly")
            print()
            return False

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Error 300009 Fix Verification")
    print("=" * 70)
    print()
    print("Problem: Error message 'No open positions to close' (code 300009)")
    print("         was being treated as a hard error.")
    print()
    print("Solution: Detect code 300009 and treat as success (position already")
    print("          closed, which is the desired end state).")
    print()
    
    results = []
    
    try:
        results.append(test_error_300009_market_order())
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    try:
        results.append(test_error_300009_exchange_error())
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    print("=" * 70)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)
    
    if all(results):
        print("\n✅ ALL TESTS PASSED - Fix verified!")
        print("\nThe error 'No open positions to close' (code 300009) is now")
        print("handled gracefully and treated as a success case.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
