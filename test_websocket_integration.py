"""
Test WebSocket integration with KuCoin API
Verifies that WebSocket is used for market data and REST API for trading
"""
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys


def test_websocket_imports():
    """Test that WebSocket components can be imported"""
    print("\n" + "=" * 80)
    print("TEST 1: WebSocket Module Imports")
    print("=" * 80)
    
    try:
        from kucoin_websocket import KuCoinWebSocket
        print("  ✓ KuCoinWebSocket imported successfully")
        
        from kucoin_client import KuCoinClient
        print("  ✓ KuCoinClient imported successfully")
        
        from config import Config
        print("  ✓ Config imported successfully")
        print(f"    - WebSocket enabled: {Config.ENABLE_WEBSOCKET}")
        
        return True
    except Exception as e:
        print(f"  ✗ Failed to import: {e}")


def test_websocket_initialization():
    """Test that WebSocket client initializes correctly"""
    print("\n" + "=" * 80)
    print("TEST 2: WebSocket Client Initialization")
    print("=" * 80)
    
    try:
        from kucoin_websocket import KuCoinWebSocket
        
        # Create WebSocket client (without connecting)
        ws_client = KuCoinWebSocket()
        
        print("  ✓ WebSocket client created")
        print(f"    - Public URL: {ws_client.WS_PUBLIC_URL}")
        print(f"    - Connected: {ws_client.is_connected()}")
        print(f"    - Should reconnect: {ws_client.should_reconnect}")
        
        # Check internal data structures
        assert hasattr(ws_client, '_tickers'), "Missing _tickers dict"
        assert hasattr(ws_client, '_candles'), "Missing _candles dict"
        assert hasattr(ws_client, '_orderbooks'), "Missing _orderbooks dict"
        print("  ✓ Internal data structures initialized")
        
        return True
    except Exception as e:
        print(f"  ✗ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()


def test_kucoin_client_with_websocket():
    """Test that KuCoinClient integrates WebSocket correctly"""
    print("\n" + "=" * 80)
    print("TEST 3: KuCoinClient with WebSocket Integration")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        from unittest.mock import MagicMock, patch
        
        # Mock the WebSocket and ccxt exchange
        with patch('kucoin_client.KuCoinWebSocket') as mock_ws_class, \
             patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            
            # Setup mocks
            mock_ws = MagicMock()
            mock_ws.is_connected.return_value = True
            mock_ws_class.return_value = mock_ws
            
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Create client with WebSocket enabled
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=True)
            
            print("  ✓ KuCoinClient created with WebSocket enabled")
            print(f"    - WebSocket attribute exists: {hasattr(client, 'websocket')}")
            print(f"    - WebSocket enabled flag: {client.enable_websocket}")
            
            # Verify WebSocket was initialized
            mock_ws_class.assert_called_once_with('test_key', 'test_secret', 'test_pass')
            print("  ✓ WebSocket initialization called with correct credentials")
            
            # Verify WebSocket connect was called
            mock_ws.connect.assert_called_once()
            print("  ✓ WebSocket connect method called")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_kucoin_client_without_websocket():
    """Test that KuCoinClient works without WebSocket (REST API only)"""
    print("\n" + "=" * 80)
    print("TEST 4: KuCoinClient without WebSocket (REST API only)")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        from unittest.mock import MagicMock, patch
        
        # Mock ccxt exchange only
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Create client with WebSocket disabled
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=False)
            
            print("  ✓ KuCoinClient created with WebSocket disabled")
            print(f"    - WebSocket attribute: {client.websocket}")
            print(f"    - WebSocket enabled flag: {client.enable_websocket}")
            
            assert client.websocket is None, "WebSocket should be None when disabled"
            print("  ✓ WebSocket is None as expected")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_get_ticker_with_websocket():
    """Test that get_ticker uses WebSocket data when available"""
    print("\n" + "=" * 80)
    print("TEST 5: get_ticker() Uses WebSocket Data")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient, APICallPriority
        from unittest.mock import MagicMock, patch
        
        with patch('kucoin_client.KuCoinWebSocket') as mock_ws_class, \
             patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            
            # Setup WebSocket mock
            mock_ws = MagicMock()
            mock_ws.is_connected.return_value = True
            mock_ws.get_ticker.return_value = {
                'symbol': 'BTC/USDT:USDT',
                'last': 50000.0,
                'bid': 49990.0,
                'ask': 50010.0,
                'volume': 1000.0,
                'source': 'websocket'
            }
            mock_ws_class.return_value = mock_ws
            
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Create client
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=True)
            
            # Call get_ticker
            ticker = client.get_ticker('BTC/USDT:USDT')
            
            print("  ✓ get_ticker() called successfully")
            print(f"    - Ticker data: {ticker}")
            
            # Verify WebSocket was used
            mock_ws.get_ticker.assert_called_once_with('BTC/USDT:USDT')
            print("  ✓ WebSocket get_ticker was called")
            
            # Verify REST API was NOT used
            assert not mock_exchange.fetch_ticker.called, "REST API should not be called when WebSocket has data"
            print("  ✓ REST API was not used (WebSocket data available)")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_get_ticker_fallback_to_rest():
    """Test that get_ticker falls back to REST API when WebSocket data unavailable"""
    print("\n" + "=" * 80)
    print("TEST 6: get_ticker() Falls Back to REST API")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient, APICallPriority
        from unittest.mock import MagicMock, patch
        
        with patch('kucoin_client.KuCoinWebSocket') as mock_ws_class, \
             patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            
            # Setup WebSocket mock - connected but no data
            mock_ws = MagicMock()
            mock_ws.is_connected.return_value = True
            mock_ws.get_ticker.return_value = None  # No WebSocket data
            mock_ws.has_ticker.return_value = False
            mock_ws_class.return_value = mock_ws
            
            # Setup REST API mock
            mock_exchange = MagicMock()
            mock_exchange.fetch_ticker.return_value = {
                'symbol': 'BTC/USDT:USDT',
                'last': 50000.0,
                'bid': 49990.0,
                'ask': 50010.0,
                'source': 'rest_api'
            }
            mock_exchange_class.return_value = mock_exchange
            
            # Create client
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=True)
            
            # Call get_ticker
            ticker = client.get_ticker('BTC/USDT:USDT')
            
            print("  ✓ get_ticker() called successfully")
            print(f"    - Ticker data: {ticker}")
            
            # Verify WebSocket was tried first
            mock_ws.get_ticker.assert_called()
            print("  ✓ WebSocket get_ticker was tried first")
            
            # Verify REST API was used as fallback
            mock_exchange.fetch_ticker.assert_called_once_with('BTC/USDT:USDT')
            print("  ✓ REST API was used as fallback")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_get_ohlcv_with_websocket():
    """Test that get_ohlcv uses WebSocket data when available"""
    print("\n" + "=" * 80)
    print("TEST 7: get_ohlcv() Uses WebSocket Data")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        from unittest.mock import MagicMock, patch
        
        with patch('kucoin_client.KuCoinWebSocket') as mock_ws_class, \
             patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            
            # Setup WebSocket mock with candle data
            mock_ws = MagicMock()
            mock_ws.is_connected.return_value = True
            mock_candles = [[1000 + i*60, 50000 + i*10, 50100 + i*10, 49900 + i*10, 50050 + i*10, 100] for i in range(100)]
            mock_ws.get_ohlcv.return_value = mock_candles
            mock_ws_class.return_value = mock_ws
            
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Create client
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=True)
            
            # Call get_ohlcv
            ohlcv = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            
            print("  ✓ get_ohlcv() called successfully")
            print(f"    - Candles retrieved: {len(ohlcv)}")
            
            # Verify WebSocket was used
            mock_ws.get_ohlcv.assert_called()
            print("  ✓ WebSocket get_ohlcv was called")
            
            # Verify REST API was NOT used
            assert not mock_exchange.fetch_ohlcv.called, "REST API should not be called when WebSocket has data"
            print("  ✓ REST API was not used (WebSocket data available)")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_trading_uses_rest_api():
    """Test that trading operations always use REST API, not WebSocket"""
    print("\n" + "=" * 80)
    print("TEST 8: Trading Operations Use REST API Only")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        from unittest.mock import MagicMock, patch
        
        with patch('kucoin_client.KuCoinWebSocket') as mock_ws_class, \
             patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            
            # Setup mocks
            mock_ws = MagicMock()
            mock_ws.is_connected.return_value = True
            mock_ws_class.return_value = mock_ws
            
            mock_exchange = MagicMock()
            mock_exchange.fetch_balance.return_value = {
                'free': {'USDT': 1000},
                'used': {'USDT': 0},
                'total': {'USDT': 1000}
            }
            mock_exchange_class.return_value = mock_exchange
            
            # Create client
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=True)
            
            # Test balance fetching (should use REST API)
            balance = client.get_balance()
            
            print("  ✓ get_balance() called successfully")
            
            # Verify REST API was used
            mock_exchange.fetch_balance.assert_called_once()
            print("  ✓ REST API fetch_balance was called")
            
            # Verify WebSocket was NOT used for balance (it doesn't have balance methods)
            assert not hasattr(mock_ws, 'get_balance') or not mock_ws.get_balance.called
            print("  ✓ WebSocket was not used for balance (correct)")
            
            print("\n  Summary: Trading operations use REST API ✓")
            print("  - get_balance: REST API")
            print("  - create_order: REST API (not tested here, but same pattern)")
            print("  - get_positions: REST API (not tested here, but same pattern)")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_websocket_cleanup():
    """Test that WebSocket connection is properly closed on client cleanup"""
    print("\n" + "=" * 80)
    print("TEST 9: WebSocket Cleanup on Client Close")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient
        from unittest.mock import MagicMock, patch
        
        with patch('kucoin_client.KuCoinWebSocket') as mock_ws_class, \
             patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            
            # Setup mocks
            mock_ws = MagicMock()
            mock_ws.is_connected.return_value = True
            mock_ws_class.return_value = mock_ws
            
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Create client
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=True)
            
            print("  ✓ Client created with WebSocket")
            
            # Close client
            client.close()
            
            print("  ✓ Client close() called")
            
            # Verify WebSocket disconnect was called
            mock_ws.disconnect.assert_called_once()
            print("  ✓ WebSocket disconnect was called")
            
            # Verify WebSocket is set to None
            assert client.websocket is None, "WebSocket should be None after close"
            print("  ✓ WebSocket set to None after close")
            
            return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


def test_config_websocket_setting():
    """Test that Config loads WebSocket setting correctly"""
    print("\n" + "=" * 80)
    print("TEST 10: Config WebSocket Setting")
    print("=" * 80)
    
    try:
        from config import Config
        
        print("  ✓ Config imported")
        print(f"    - ENABLE_WEBSOCKET: {Config.ENABLE_WEBSOCKET}")
        print(f"    - Type: {type(Config.ENABLE_WEBSOCKET)}")
        
        # Verify it's a boolean
        assert isinstance(Config.ENABLE_WEBSOCKET, bool), "ENABLE_WEBSOCKET should be boolean"
        print("  ✓ ENABLE_WEBSOCKET is boolean type")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


def run_all_tests():
    """Run all WebSocket integration tests"""
    print("\n" + "=" * 80)
    print("KUCOIN WEBSOCKET INTEGRATION TEST SUITE")
    print("=" * 80)
    print("Testing WebSocket for market data & REST API for trading")
    print("=" * 80)
    
    tests = [
        ("WebSocket Imports", test_websocket_imports),
        ("WebSocket Initialization", test_websocket_initialization),
        ("KuCoinClient with WebSocket", test_kucoin_client_with_websocket),
        ("KuCoinClient without WebSocket", test_kucoin_client_without_websocket),
        ("get_ticker with WebSocket", test_get_ticker_with_websocket),
        ("get_ticker Fallback to REST", test_get_ticker_fallback_to_rest),
        ("get_ohlcv with WebSocket", test_get_ohlcv_with_websocket),
        ("Trading Uses REST API", test_trading_uses_rest_api),
        ("WebSocket Cleanup", test_websocket_cleanup),
        ("Config WebSocket Setting", test_config_websocket_setting),
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
        print("\n🎉 ALL TESTS PASSED! WebSocket integration working correctly!")
        print("   📊 Market Data: WebSocket")
        print("   💼 Trading: REST API")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
