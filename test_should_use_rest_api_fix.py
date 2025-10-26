"""
Test for the _should_use_rest_api() method fix in KuCoinClient
"""
import sys
from unittest.mock import MagicMock, patch


def test_should_use_rest_api_method_exists():
    """Test that _should_use_rest_api method exists"""
    print("\n" + "=" * 80)
    print("TEST 1: _should_use_rest_api() Method Exists")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        
        # Check that the method exists
        assert hasattr(KuCoinClient, '_should_use_rest_api'), \
            "_should_use_rest_api method not found in KuCoinClient"
        print("  ✓ _should_use_rest_api method exists in KuCoinClient")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_should_use_rest_api_no_websocket():
    """Test _should_use_rest_api returns True when websocket is None"""
    print("\n" + "=" * 80)
    print("TEST 2: _should_use_rest_api() with No WebSocket")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Create client without WebSocket
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=False)
            
            # Test the method
            result = client._should_use_rest_api()
            
            print(f"  ✓ _should_use_rest_api() returned: {result}")
            assert result is True, "Should return True when websocket is None"
            print("  ✓ Correctly returns True when WebSocket is disabled")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_should_use_rest_api_disconnected_websocket():
    """Test _should_use_rest_api returns True when websocket is disconnected"""
    print("\n" + "=" * 80)
    print("TEST 3: _should_use_rest_api() with Disconnected WebSocket")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.KuCoinWebSocket') as mock_ws_class, \
             patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            
            # Setup WebSocket mock - not connected
            mock_ws = MagicMock()
            mock_ws.is_connected.return_value = False
            mock_ws_class.return_value = mock_ws
            
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Create client with WebSocket
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=True)
            
            # Test the method
            result = client._should_use_rest_api()
            
            print(f"  ✓ _should_use_rest_api() returned: {result}")
            assert result is True, "Should return True when websocket is disconnected"
            print("  ✓ Correctly returns True when WebSocket is disconnected")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_should_use_rest_api_low_subscription_count():
    """Test _should_use_rest_api returns False when subscription count is low"""
    print("\n" + "=" * 80)
    print("TEST 4: _should_use_rest_api() with Low Subscription Count")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.KuCoinWebSocket') as mock_ws_class, \
             patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            
            # Setup WebSocket mock - connected with low subscription count
            mock_ws = MagicMock()
            mock_ws.is_connected.return_value = True
            mock_ws.get_subscription_count.return_value = 100  # Well below 350
            mock_ws_class.return_value = mock_ws
            
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Create client with WebSocket
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=True)
            
            # Test the method
            result = client._should_use_rest_api()
            
            print(f"  ✓ _should_use_rest_api() returned: {result}")
            print(f"    - Subscription count: {mock_ws.get_subscription_count.return_value}")
            assert result is False, "Should return False when subscription count is low"
            print("  ✓ Correctly returns False when subscription count is low (can use WebSocket)")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_should_use_rest_api_high_subscription_count():
    """Test _should_use_rest_api returns True when subscription count is high"""
    print("\n" + "=" * 80)
    print("TEST 5: _should_use_rest_api() with High Subscription Count")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.KuCoinWebSocket') as mock_ws_class, \
             patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            
            # Setup WebSocket mock - connected with high subscription count
            mock_ws = MagicMock()
            mock_ws.is_connected.return_value = True
            mock_ws.get_subscription_count.return_value = 360  # Above 350 threshold
            mock_ws_class.return_value = mock_ws
            
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Create client with WebSocket
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=True)
            
            # Test the method
            result = client._should_use_rest_api()
            
            print(f"  ✓ _should_use_rest_api() returned: {result}")
            print(f"    - Subscription count: {mock_ws.get_subscription_count.return_value}")
            assert result is True, "Should return True when subscription count is high"
            print("  ✓ Correctly returns True when subscription count is high (use REST API)")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_ohlcv_calls_should_use_rest_api():
    """Test that get_ohlcv correctly calls _should_use_rest_api"""
    print("\n" + "=" * 80)
    print("TEST 6: get_ohlcv() Calls _should_use_rest_api()")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.KuCoinWebSocket') as mock_ws_class, \
             patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            
            # Setup WebSocket mock - connected with high subscription count (forces REST API)
            mock_ws = MagicMock()
            mock_ws.is_connected.return_value = True
            mock_ws.get_subscription_count.return_value = 360  # Above threshold
            mock_ws_class.return_value = mock_ws
            
            # Setup REST API mock
            mock_exchange = MagicMock()
            mock_candles = [[1000 + i*60, 50000, 50100, 49900, 50050, 100] for i in range(100)]
            mock_exchange.fetch_ohlcv.return_value = mock_candles
            mock_exchange_class.return_value = mock_exchange
            
            # Create client with WebSocket
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=True)
            
            # Call get_ohlcv - should use REST API due to high subscription count
            ohlcv = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            
            print(f"  ✓ get_ohlcv() called successfully")
            print(f"    - Retrieved {len(ohlcv)} candles")
            
            # Verify REST API was used
            mock_exchange.fetch_ohlcv.assert_called()
            print("  ✓ REST API fetch_ohlcv was called (high subscription count)")
            
            # Verify WebSocket get_ohlcv was NOT called (due to _should_use_rest_api check)
            assert not mock_ws.get_ohlcv.called, "WebSocket should not be used with high subscription count"
            print("  ✓ WebSocket was not used (correctly handled by _should_use_rest_api)")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests for _should_use_rest_api fix"""
    print("\n" + "=" * 80)
    print("_should_use_rest_api() FIX TEST SUITE")
    print("=" * 80)
    print("Testing the fix for AttributeError in KuCoinClient")
    print("=" * 80)
    
    tests = [
        ("Method Exists", test_should_use_rest_api_method_exists),
        ("No WebSocket", test_should_use_rest_api_no_websocket),
        ("Disconnected WebSocket", test_should_use_rest_api_disconnected_websocket),
        ("Low Subscription Count", test_should_use_rest_api_low_subscription_count),
        ("High Subscription Count", test_should_use_rest_api_high_subscription_count),
        ("get_ohlcv Integration", test_get_ohlcv_calls_should_use_rest_api),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print("-" * 80)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 80)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The _should_use_rest_api() fix is working correctly!")
        print("   ✅ Method exists and is callable")
        print("   ✅ Handles WebSocket states correctly")
        print("   ✅ Checks subscription count properly")
        print("   ✅ Integrates with get_ohlcv correctly")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
