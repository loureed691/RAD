#!/usr/bin/env python3
"""
Test that reduce_only orders don't call set_leverage (Fix for error 330008 on close)

Problem: When closing positions with reduce_only=True, set_leverage() was being called
which could fail with error 330008 if all margin is in use in the position being closed.

Solution: Skip set_leverage() and set_margin_mode() calls for reduce_only orders.
"""

from unittest.mock import Mock, patch, MagicMock, call

def test_market_order_reduce_only_skips_leverage():
    """Test that create_market_order with reduce_only=True does NOT call set_leverage"""
    print("\nTesting market order reduce_only skips leverage setting...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            # Mock the methods
            mock_instance.load_markets.return_value = {
                'BNB/USDT:USDT': {
                    'contractSize': 1,
                    'limits': {
                        'amount': {'min': 1.0, 'max': 10000},
                        'cost': {'min': 1.0, 'max': 100000}
                    }
                }
            }
            
            mock_instance.fetch_ticker.return_value = {
                'last': 300.0,
                'bid': 299.0,
                'ask': 301.0
            }
            
            mock_instance.create_order.return_value = {
                'id': 'close_order_456',
                'status': 'closed',
                'filled': 10,
                'average': 300.0
            }
            
            mock_instance.fetch_order.return_value = {
                'id': 'close_order_456',
                'status': 'closed',
                'filled': 10,
                'average': 300.0
            }
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Reset mock to clear initialization calls
            mock_instance.reset_mock()
            
            # Test reduce_only=True - should NOT call set_leverage
            print("  Test 1: reduce_only=True - should skip set_leverage")
            order = client.create_market_order(
                'BNB/USDT:USDT', 'sell', 10.0, leverage=10, reduce_only=True
            )
            
            # Check that set_leverage was NOT called
            set_leverage_calls = [call for call in mock_instance.mock_calls if 'set_leverage' in str(call)]
            set_margin_mode_calls = [call for call in mock_instance.mock_calls if 'set_margin_mode' in str(call)]
            
            print(f"    set_leverage calls: {len(set_leverage_calls)}")
            print(f"    set_margin_mode calls: {len(set_margin_mode_calls)}")
            
            assert len(set_leverage_calls) == 0, \
                f"set_leverage should NOT be called for reduce_only orders, but was called {len(set_leverage_calls)} times"
            assert len(set_margin_mode_calls) == 0, \
                f"set_margin_mode should NOT be called for reduce_only orders, but was called {len(set_margin_mode_calls)} times"
            
            # Check that create_order WAS called with reduceOnly param
            create_order_calls = [call for call in mock_instance.mock_calls if 'create_order' in str(call)]
            assert len(create_order_calls) >= 1, "create_order should be called"
            
            # Verify the params include reduceOnly
            create_order_call = [c for c in mock_instance.method_calls if c[0] == 'create_order'][0]
            params = create_order_call[2].get('params', {})
            assert params.get('reduceOnly') == True, f"reduceOnly should be True in params, got {params}"
            
            print("    ✓ set_leverage NOT called for reduce_only=True")
            print("    ✓ set_margin_mode NOT called for reduce_only=True")
            print("    ✓ reduceOnly=True passed in params")
            
            # Reset mock
            mock_instance.reset_mock()
            
            # Test reduce_only=False - SHOULD call set_leverage
            print("  Test 2: reduce_only=False - should call set_leverage")
            
            # Mock balance for opening position
            with patch.object(client, 'get_balance') as mock_balance:
                mock_balance.return_value = {
                    'free': {'USDT': 100.0},
                    'used': {'USDT': 0.0},
                    'total': {'USDT': 100.0}
                }
                
                order2 = client.create_market_order(
                    'BNB/USDT:USDT', 'buy', 10.0, leverage=10, reduce_only=False
                )
            
            # Check that set_leverage WAS called
            set_leverage_calls2 = [call for call in mock_instance.mock_calls if 'set_leverage' in str(call)]
            set_margin_mode_calls2 = [call for call in mock_instance.mock_calls if 'set_margin_mode' in str(call)]
            
            print(f"    set_leverage calls: {len(set_leverage_calls2)}")
            print(f"    set_margin_mode calls: {len(set_margin_mode_calls2)}")
            
            assert len(set_leverage_calls2) == 1, \
                f"set_leverage should be called once for non-reduce_only orders, got {len(set_leverage_calls2)}"
            assert len(set_margin_mode_calls2) == 1, \
                f"set_margin_mode should be called once for non-reduce_only orders, got {len(set_margin_mode_calls2)}"
            
            print("    ✓ set_leverage called for reduce_only=False")
            print("    ✓ set_margin_mode called for reduce_only=False")
            
        print("✓ Market order reduce_only leverage tests passed")
        return True
    except Exception as e:
        print(f"✗ Market order test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_limit_order_reduce_only_skips_leverage():
    """Test that create_limit_order with reduce_only=True does NOT call set_leverage"""
    print("\nTesting limit order reduce_only skips leverage setting...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            # Mock the methods
            mock_instance.load_markets.return_value = {
                'BNB/USDT:USDT': {
                    'contractSize': 1,
                    'limits': {
                        'amount': {'min': 1.0, 'max': 10000},
                        'cost': {'min': 1.0, 'max': 100000}
                    }
                }
            }
            
            mock_instance.create_order.return_value = {
                'id': 'limit_close_789',
                'status': 'open',
                'filled': 0,
                'amount': 10
            }
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Reset mock to clear initialization calls
            mock_instance.reset_mock()
            
            # Test reduce_only=True - should NOT call set_leverage
            print("  Test 1: reduce_only=True - should skip set_leverage")
            order = client.create_limit_order(
                'BNB/USDT:USDT', 'sell', 10.0, price=305.0, leverage=10, reduce_only=True
            )
            
            # Check that set_leverage was NOT called
            set_leverage_calls = [call for call in mock_instance.mock_calls if 'set_leverage' in str(call)]
            set_margin_mode_calls = [call for call in mock_instance.mock_calls if 'set_margin_mode' in str(call)]
            
            print(f"    set_leverage calls: {len(set_leverage_calls)}")
            print(f"    set_margin_mode calls: {len(set_margin_mode_calls)}")
            
            assert len(set_leverage_calls) == 0, \
                f"set_leverage should NOT be called for reduce_only orders, but was called {len(set_leverage_calls)} times"
            assert len(set_margin_mode_calls) == 0, \
                f"set_margin_mode should NOT be called for reduce_only orders, but was called {len(set_margin_mode_calls)} times"
            
            # Check that create_order WAS called with reduceOnly param
            create_order_calls = [call for call in mock_instance.mock_calls if 'create_order' in str(call)]
            assert len(create_order_calls) >= 1, "create_order should be called"
            
            # Verify the params include reduceOnly
            create_order_call = [c for c in mock_instance.method_calls if c[0] == 'create_order'][0]
            params = create_order_call[2].get('params', {})
            assert params.get('reduceOnly') == True, f"reduceOnly should be True in params, got {params}"
            
            print("    ✓ set_leverage NOT called for reduce_only=True")
            print("    ✓ set_margin_mode NOT called for reduce_only=True")
            print("    ✓ reduceOnly=True passed in params")
            
            # Reset mock
            mock_instance.reset_mock()
            
            # Test reduce_only=False - SHOULD call set_leverage
            print("  Test 2: reduce_only=False - should call set_leverage")
            
            # Mock balance for opening position
            with patch.object(client, 'get_balance') as mock_balance:
                mock_balance.return_value = {
                    'free': {'USDT': 100.0},
                    'used': {'USDT': 0.0},
                    'total': {'USDT': 100.0}
                }
                
                order2 = client.create_limit_order(
                    'BNB/USDT:USDT', 'buy', 10.0, price=295.0, leverage=10, reduce_only=False
                )
            
            # Check that set_leverage WAS called
            set_leverage_calls2 = [call for call in mock_instance.mock_calls if 'set_leverage' in str(call)]
            set_margin_mode_calls2 = [call for call in mock_instance.mock_calls if 'set_margin_mode' in str(call)]
            
            print(f"    set_leverage calls: {len(set_leverage_calls2)}")
            print(f"    set_margin_mode calls: {len(set_margin_mode_calls2)}")
            
            assert len(set_leverage_calls2) == 1, \
                f"set_leverage should be called once for non-reduce_only orders, got {len(set_leverage_calls2)}"
            assert len(set_margin_mode_calls2) == 1, \
                f"set_margin_mode should be called once for non-reduce_only orders, got {len(set_margin_mode_calls2)}"
            
            print("    ✓ set_leverage called for reduce_only=False")
            print("    ✓ set_margin_mode called for reduce_only=False")
            
        print("✓ Limit order reduce_only leverage tests passed")
        return True
    except Exception as e:
        print(f"✗ Limit order test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_close_position_with_zero_margin():
    """
    Test the exact scenario from the problem statement:
    - Closing a position when all margin is tied up
    - Should NOT fail with error 330008
    """
    print("\nTesting close position with zero available margin...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            # Mock the methods
            mock_instance.load_markets.return_value = {
                'BNB/USDT:USDT': {
                    'contractSize': 1,
                    'limits': {
                        'amount': {'min': 1.0, 'max': 10000},
                        'cost': {'min': 1.0, 'max': 100000}
                    }
                }
            }
            
            mock_instance.fetch_ticker.return_value = {
                'last': 590.0,
                'bid': 589.5,
                'ask': 590.5
            }
            
            mock_instance.fetch_positions.return_value = [
                {
                    'symbol': 'BNB/USDT:USDT',
                    'contracts': 5.0,
                    'side': 'long',
                    'leverage': 10,
                    'info': {'realLeverage': '10'}
                }
            ]
            
            mock_instance.create_order.return_value = {
                'id': 'close_123',
                'status': 'closed',
                'filled': 5.0,
                'average': 590.0
            }
            
            mock_instance.fetch_order.return_value = {
                'id': 'close_123',
                'status': 'closed',
                'filled': 5.0,
                'average': 590.0
            }
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Reset mock to clear initialization calls
            mock_instance.reset_mock()
            
            # Mock zero available margin (all margin in position)
            with patch.object(client, 'get_balance') as mock_balance:
                mock_balance.return_value = {
                    'free': {'USDT': 0.0},  # Zero available
                    'used': {'USDT': 295.0},  # All in position
                    'total': {'USDT': 295.0}
                }
                
                print("  Scenario: All margin in position, trying to close")
                print("  Available margin: $0.00")
                print("  Position: 5 BNB contracts at 10x leverage")
                
                # This should succeed WITHOUT calling set_leverage
                result = client.close_position('BNB/USDT:USDT')
                
                print(f"  Result: {'Success' if result else 'Failed'}")
                assert result == True, "Close position should succeed"
                
                # Verify set_leverage was NOT called
                set_leverage_calls = [call for call in mock_instance.mock_calls if 'set_leverage' in str(call)]
                print(f"  set_leverage calls: {len(set_leverage_calls)}")
                assert len(set_leverage_calls) == 0, \
                    "set_leverage should NOT be called when closing position"
                
                # Verify create_order WAS called with reduceOnly
                create_order_call = [c for c in mock_instance.method_calls if c[0] == 'create_order'][0]
                params = create_order_call[2].get('params', {})
                assert params.get('reduceOnly') == True, f"reduceOnly should be True, got {params}"
                
                print("  ✓ Position closed successfully")
                print("  ✓ No set_leverage call (avoids error 330008)")
                print("  ✓ reduceOnly=True in order params")
        
        print("✓ Close position with zero margin test passed")
        return True
    except Exception as e:
        print(f"✗ Close position test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("TESTING REDUCE_ONLY LEVERAGE FIX (Error 330008 on Close)")
    print("=" * 70)
    
    results = []
    results.append(test_market_order_reduce_only_skips_leverage())
    results.append(test_limit_order_reduce_only_skips_leverage())
    results.append(test_close_position_with_zero_margin())
    
    print("\n" + "=" * 70)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    if all(results):
        print("✓ ALL TESTS PASSED!")
        print("\nFix verified:")
        print("  • reduce_only orders skip set_leverage()")
        print("  • reduce_only orders skip set_margin_mode()")
        print("  • Closing positions works even with zero available margin")
        print("  • Error 330008 is prevented on close orders")
    else:
        print(f"✗ {len(results) - sum(results)} test(s) failed")
    print("=" * 70)
