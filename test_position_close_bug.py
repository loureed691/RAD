#!/usr/bin/env python3
"""
Regression test for position closing bug

Bug Description:
    kucoin_client.close_position() returns True even when the market order 
    to close the position fails (returns None). This causes position_manager 
    to incorrectly remove the position from tracking while it's still open 
    on the exchange.

Root Cause:
    In kucoin_client.py line 285-287:
    ```python
    self.create_market_order(symbol, side, abs(contracts))
    self.logger.info(f"Closed position for {symbol}")
    return True  # Always returns True, doesn't check order result
    ```

Impact:
    - Position appears closed in bot but remains open on exchange
    - No stop loss/take profit monitoring for "ghost" positions
    - Potential for unexpected losses
    - Desynchronization between bot state and exchange state
"""

import sys
from unittest.mock import Mock, MagicMock, patch


def test_close_position_failure_handling():
    """Test that close_position returns False when market order fails"""
    print("\n" + "="*70)
    print("Test: close_position should return False when order fails")
    print("="*70)
    
    try:
        from kucoin_client import KuCoinClient
        
        # Mock the ccxt exchange
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Initialize client
            client = KuCoinClient('test_key', 'test_secret', 'test_pass')
            
            # Test Case 1: Order creation returns None (failure)
            print("\n  Test 1: Market order returns None (API error)")
            mock_exchange.fetch_positions.return_value = [
                {
                    'symbol': 'BTC/USDT:USDT',
                    'contracts': 10.0,
                    'side': 'long',
                }
            ]
            mock_exchange.create_order.return_value = None
            
            result = client.close_position('BTC/USDT:USDT')
            
            if result == False:
                print("    ✓ PASS: close_position correctly returned False")
            else:
                print(f"    ✗ FAIL: close_position returned {result}, expected False")
                print("    BUG: Position will be removed from tracking but still open on exchange!")
                return False
            
            # Test Case 2: Order creation succeeds
            print("\n  Test 2: Market order succeeds")
            mock_exchange.create_order.return_value = {
                'id': '12345',
                'symbol': 'BTC/USDT:USDT',
                'status': 'closed'
            }
            
            result = client.close_position('BTC/USDT:USDT')
            
            if result == True:
                print("    ✓ PASS: close_position correctly returned True")
            else:
                print(f"    ✗ FAIL: close_position returned {result}, expected True")
                return False
            
            # Test Case 3: No position found for symbol
            print("\n  Test 3: No position found for symbol")
            mock_exchange.fetch_positions.return_value = []
            
            result = client.close_position('ETH/USDT:USDT')
            
            if result == False:
                print("    ✓ PASS: close_position correctly returned False")
            else:
                print(f"    ✗ FAIL: close_position returned {result}, expected False")
                return False
            
            print("\n✓ All test cases passed!")
            return True
            
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_manager_integration():
    """Test that position_manager doesn't remove position when close fails"""
    print("\n" + "="*70)
    print("Test: position_manager integration with failed close")
    print("="*70)
    
    try:
        from position_manager import PositionManager, Position
        from unittest.mock import Mock
        
        # Create mock client that fails to close
        client = Mock()
        client.close_position.return_value = False  # Simulate failure
        client.get_ticker.return_value = {'last': 55000.0}
        
        pm = PositionManager(client, 0.02)
        
        # Manually add a position
        pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=10.0,
            leverage=10,
            stop_loss=47500.0,
            take_profit=60000.0
        )
        pm.positions['BTC/USDT:USDT'] = pos
        
        print("\n  Before close attempt:")
        print(f"    Tracked positions: {list(pm.positions.keys())}")
        
        # Try to close the position
        pnl = pm.close_position('BTC/USDT:USDT')
        
        print("\n  After close attempt:")
        print(f"    Tracked positions: {list(pm.positions.keys())}")
        print(f"    Returned P/L: {pnl}")
        
        if pnl is None and 'BTC/USDT:USDT' in pm.positions:
            print("\n    ✓ PASS: Position remains tracked after failed close")
            return True
        elif pnl is None and 'BTC/USDT:USDT' not in pm.positions:
            print("\n    ✗ FAIL: Position removed despite close failure!")
            return False
        else:
            print(f"\n    ✗ UNEXPECTED: P/L={pnl}, position in dict={('BTC/USDT:USDT' in pm.positions)}")
            return False
            
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all regression tests"""
    print("="*70)
    print("Position Close Bug - Regression Test Suite")
    print("="*70)
    
    results = {
        'close_position_failure_handling': test_close_position_failure_handling(),
        'position_manager_integration': test_position_manager_integration(),
    }
    
    print("\n" + "="*70)
    print("Test Results Summary")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name:.<50} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("✓✓✓ All regression tests passed! ✓✓✓")
        print("="*70)
        return 0
    else:
        print("✗✗✗ Some regression tests failed - BUG PRESENT ✗✗✗")
        print("="*70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
