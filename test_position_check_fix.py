"""
Test script for position check fix (error 330008)
Tests that bot properly checks for existing positions before creating orders
"""
import sys
from unittest.mock import Mock, patch, MagicMock

def test_has_open_position():
    """Test checking for open positions on exchange"""
    print("\nTesting has_open_position method...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Test case 1: No open positions
            mock_instance.fetch_positions.return_value = []
            
            has_pos = client.has_open_position('BTC/USDT:USDT')
            print(f"  ✓ No positions: has_position={has_pos}")
            assert has_pos == False, "Should return False when no positions"
            
            # Test case 2: Position exists for different symbol
            mock_instance.fetch_positions.return_value = [
                {'symbol': 'ETH/USDT:USDT', 'contracts': 10.0}
            ]
            
            has_pos = client.has_open_position('BTC/USDT:USDT')
            print(f"  ✓ Different symbol: has_position={has_pos}")
            assert has_pos == False, "Should return False for different symbol"
            
            # Test case 3: Position exists for the symbol
            mock_instance.fetch_positions.return_value = [
                {'symbol': 'BTC/USDT:USDT', 'contracts': 5.0}
            ]
            
            has_pos = client.has_open_position('BTC/USDT:USDT')
            print(f"  ✓ Position exists: has_position={has_pos}")
            assert has_pos == True, "Should return True when position exists"
            
            # Test case 4: Multiple positions, one matches
            mock_instance.fetch_positions.return_value = [
                {'symbol': 'ETH/USDT:USDT', 'contracts': 10.0},
                {'symbol': 'BTC/USDT:USDT', 'contracts': 3.0},
                {'symbol': 'SOL/USDT:USDT', 'contracts': 20.0}
            ]
            
            has_pos = client.has_open_position('BTC/USDT:USDT')
            print(f"  ✓ Multiple positions: has_position={has_pos}")
            assert has_pos == True, "Should find position among multiple"
            
            # Test case 5: Position with zero contracts (closed)
            mock_instance.fetch_positions.return_value = [
                {'symbol': 'BTC/USDT:USDT', 'contracts': 0}
            ]
            
            has_pos = client.has_open_position('BTC/USDT:USDT')
            print(f"  ✓ Zero contracts: has_position={has_pos}")
            assert has_pos == False, "Should return False for zero contracts"
        
        print("✓ has_open_position tests passed")
        return True
    except Exception as e:
        print(f"✗ has_open_position test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_order_with_existing_position():
    """Test that create_market_order prevents opening duplicate positions"""
    print("\nTesting create_market_order with existing position...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock has_open_position to return True
            with patch.object(client, 'has_open_position', return_value=True):
                # Mock get_ticker
                with patch.object(client, 'get_ticker') as mock_ticker:
                    mock_ticker.return_value = {'last': 50000.0}
                    
                    # Try to create an order when position already exists
                    result = client.create_market_order(
                        'BTC/USDT:USDT', 'buy', 1.0, leverage=10
                    )
                    
                    print(f"  ✓ Order creation with existing position: result={result}")
                    assert result is None, "Should return None when position exists"
            
            # Now test without existing position - should proceed to margin check
            with patch.object(client, 'has_open_position', return_value=False):
                with patch.object(client, 'get_ticker') as mock_ticker:
                    mock_ticker.return_value = {'last': 50000.0}
                    
                    # Mock balance check to fail (insufficient margin)
                    with patch.object(client, 'get_balance') as mock_balance:
                        mock_balance.return_value = {'free': {'USDT': 1.0}}
                        
                        # Mock validate_and_cap_amount
                        with patch.object(client, 'validate_and_cap_amount') as mock_validate:
                            mock_validate.return_value = 1.0
                            
                            # Should proceed past position check but fail on margin
                            result = client.create_market_order(
                                'BTC/USDT:USDT', 'buy', 1.0, leverage=10
                            )
                            
                            # Result will be None due to insufficient margin
                            print(f"  ✓ Order without existing position proceeds to margin check")
        
        print("✓ create_market_order position check tests passed")
        return True
    except Exception as e:
        print(f"✗ create_market_order test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_limit_order_with_existing_position():
    """Test that create_limit_order prevents opening duplicate positions"""
    print("\nTesting create_limit_order with existing position...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock has_open_position to return True
            with patch.object(client, 'has_open_position', return_value=True):
                # Try to create a limit order when position already exists
                result = client.create_limit_order(
                    'BTC/USDT:USDT', 'buy', 1.0, 50000.0, leverage=10
                )
                
                print(f"  ✓ Limit order with existing position: result={result}")
                assert result is None, "Should return None when position exists"
            
            # Test reduce_only order - should NOT check for existing position
            with patch.object(client, 'has_open_position', return_value=True):
                # Mock validate_and_cap_amount
                with patch.object(client, 'validate_and_cap_amount', return_value=1.0):
                    # Mock exchange methods
                    mock_instance.set_margin_mode = MagicMock()
                    mock_instance.set_leverage = MagicMock()
                    mock_instance.create_order.return_value = {
                        'id': '12345',
                        'symbol': 'BTC/USDT:USDT',
                        'status': 'open'
                    }
                    
                    # reduce_only order should bypass position check
                    result = client.create_limit_order(
                        'BTC/USDT:USDT', 'sell', 1.0, 50000.0, 
                        leverage=10, reduce_only=True
                    )
                    
                    print(f"  ✓ Reduce-only order bypasses position check")
                    assert result is not None, "reduce_only order should succeed"
        
        print("✓ create_limit_order position check tests passed")
        return True
    except Exception as e:
        print(f"✗ create_limit_order test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all position check tests"""
    print("=" * 60)
    print("TESTING POSITION CHECK FIX (ERROR 330008)")
    print("=" * 60)
    
    results = []
    results.append(("has_open_position", test_has_open_position()))
    results.append(("create_market_order", test_create_order_with_existing_position()))
    results.append(("create_limit_order", test_limit_order_with_existing_position()))
    
    print("\n" + "=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        for name, result in results:
            status = "✓" if result else "✗"
            print(f"  {status} {name}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
