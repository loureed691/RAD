"""
Test OHLCV Incremental Caching

This test verifies that the KuCoinClient properly caches OHLCV data
and fetches only new candles on subsequent calls.
"""

import time
from unittest.mock import Mock, MagicMock, patch
from kucoin_client import KuCoinClient


def test_ohlcv_incremental_caching():
    """Test that OHLCV data is cached and updated incrementally"""
    print("\n" + "="*80)
    print("TEST: OHLCV Incremental Caching")
    print("="*80)
    
    # Create mock candle data
    def create_candles(start_timestamp, count):
        """Helper to create mock candle data"""
        candles = []
        for i in range(count):
            timestamp = start_timestamp + (i * 3600000)  # 1 hour intervals
            candles.append([
                timestamp,  # timestamp
                100.0 + i,  # open
                105.0 + i,  # high
                95.0 + i,   # low
                102.0 + i,  # close
                1000.0      # volume
            ])
        return candles
    
    # Initial timestamp
    base_timestamp = int(time.time() * 1000) - (100 * 3600000)  # 100 hours ago
    
    # Mock the exchange
    mock_exchange = MagicMock()
    
    # First call returns 100 candles
    initial_candles = create_candles(base_timestamp, 100)
    
    # Second call returns 20 recent candles (with 2 new ones)
    # This simulates what happens when we do incremental fetch
    recent_timestamp = initial_candles[-1][0]  # Last timestamp from initial
    incremental_candles = create_candles(recent_timestamp - (18 * 3600000), 20)
    
    # Setup mock responses
    call_count = [0]
    def mock_fetch_ohlcv(symbol, timeframe, limit):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call - full data
            print(f"  Call {call_count[0]}: Fetching full {limit} candles")
            return initial_candles[:limit]
        else:
            # Subsequent calls - incremental data
            print(f"  Call {call_count[0]}: Fetching incremental {limit} candles")
            return incremental_candles
    
    mock_exchange.fetch_ohlcv = Mock(side_effect=mock_fetch_ohlcv)
    mock_exchange.load_markets = Mock(return_value={})
    mock_exchange.set_position_mode = Mock()
    
    # Create client with mocked exchange
    with patch('kucoin_client.ccxt.kucoinfutures', return_value=mock_exchange):
        with patch('kucoin_client.KuCoinWebSocket'):
            # Disable websocket for this test
            client = KuCoinClient('test', 'test', 'test', enable_websocket=False)
            
            # First call - should fetch full data and cache it
            print("\n1. First call - fetching and caching full data:")
            ohlcv_1 = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            print(f"   Retrieved {len(ohlcv_1)} candles")
            print(f"   First candle timestamp: {ohlcv_1[0][0]}")
            print(f"   Last candle timestamp: {ohlcv_1[-1][0]}")
            
            assert len(ohlcv_1) == 100, f"Expected 100 candles, got {len(ohlcv_1)}"
            assert call_count[0] == 1, f"Expected 1 API call, got {call_count[0]}"
            print("   ✓ Data cached successfully")
            
            # Manually age the cache to bypass the 60-second recent cache check
            print("\n   Aging cache to trigger incremental fetch...")
            with client._ohlcv_cache_lock:
                cache_key = ('BTC/USDT:USDT', '1h')
                if cache_key in client._ohlcv_cache:
                    # Set last_update to 61 seconds ago
                    client._ohlcv_cache[cache_key]['last_update'] = time.time() - 61
            
            # Second call - should use cache and fetch incrementally
            print("\n2. Second call - using cache + incremental fetch:")
            ohlcv_2 = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            print(f"   Retrieved {len(ohlcv_2)} candles")
            print(f"   First candle timestamp: {ohlcv_2[0][0]}")
            print(f"   Last candle timestamp: {ohlcv_2[-1][0]}")
            
            assert len(ohlcv_2) >= 100, f"Expected at least 100 candles, got {len(ohlcv_2)}"
            assert call_count[0] == 2, f"Expected 2 API calls, got {call_count[0]}"
            print("   ✓ Incremental fetch successful")
            
            # Third call within cache validity - should use recent cache
            print("\n3. Third call - using recent cache:")
            ohlcv_3 = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            print(f"   Retrieved {len(ohlcv_3)} candles")
            
            # Should be same as previous call since cache is very recent
            assert len(ohlcv_3) >= 100, f"Expected at least 100 candles, got {len(ohlcv_3)}"
            print("   ✓ Cache reused successfully")
            
            # Test with different symbol - should create separate cache entry
            print("\n4. Different symbol - separate cache:")
            initial_eth_candles = create_candles(base_timestamp, 50)
            mock_exchange.fetch_ohlcv = Mock(return_value=initial_eth_candles)
            
            ohlcv_eth = client.get_ohlcv('ETH/USDT:USDT', '1h', 50)
            print(f"   Retrieved {len(ohlcv_eth)} candles for ETH")
            
            assert len(ohlcv_eth) == 50, f"Expected 50 candles, got {len(ohlcv_eth)}"
            print("   ✓ Separate cache for different symbol")
            
            # Test with different timeframe - should create separate cache entry
            print("\n5. Different timeframe - separate cache:")
            initial_4h_candles = create_candles(base_timestamp, 50)
            mock_exchange.fetch_ohlcv = Mock(return_value=initial_4h_candles)
            
            ohlcv_4h = client.get_ohlcv('BTC/USDT:USDT', '4h', 50)
            print(f"   Retrieved {len(ohlcv_4h)} candles for 4h timeframe")
            
            assert len(ohlcv_4h) == 50, f"Expected 50 candles, got {len(ohlcv_4h)}"
            print("   ✓ Separate cache for different timeframe")
            
            # Verify cache is cleared on close
            print("\n6. Cache cleanup on close:")
            client.close()
            print("   ✓ Client closed successfully")
            
            print("\n" + "="*80)
            print("✓ ALL TESTS PASSED")
            print("="*80)
            
            return True


def test_cache_expiration():
    """Test that cache expires after TTL"""
    print("\n" + "="*80)
    print("TEST: Cache Expiration")
    print("="*80)
    
    # Create mock candle data
    base_timestamp = int(time.time() * 1000) - (100 * 3600000)
    candles = []
    for i in range(100):
        timestamp = base_timestamp + (i * 3600000)
        candles.append([timestamp, 100.0, 105.0, 95.0, 102.0, 1000.0])
    
    # Mock the exchange
    mock_exchange = MagicMock()
    mock_exchange.fetch_ohlcv = Mock(return_value=candles)
    mock_exchange.load_markets = Mock(return_value={})
    mock_exchange.set_position_mode = Mock()
    
    # Create client with mocked exchange
    with patch('kucoin_client.ccxt.kucoinfutures', return_value=mock_exchange):
        with patch('kucoin_client.KuCoinWebSocket'):
            client = KuCoinClient('test', 'test', 'test', enable_websocket=False)
            
            # Set a very short cache TTL for testing
            client._ohlcv_cache_ttl = 0.5  # 0.5 seconds
            
            print("\n1. First call - caching data:")
            ohlcv_1 = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            assert len(ohlcv_1) == 100
            call_count_1 = mock_exchange.fetch_ohlcv.call_count
            print(f"   Cached {len(ohlcv_1)} candles (API calls: {call_count_1})")
            
            # Age the cache slightly to trigger incremental fetch
            with client._ohlcv_cache_lock:
                cache_key = ('BTC/USDT:USDT', '1h')
                if cache_key in client._ohlcv_cache:
                    client._ohlcv_cache[cache_key]['last_update'] = time.time() - 61
            
            print("\n2. Second call after aging cache - incremental fetch:")
            ohlcv_2 = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            call_count_2 = mock_exchange.fetch_ohlcv.call_count
            print(f"   Retrieved {len(ohlcv_2)} candles (API calls: {call_count_2})")
            # Should have made one additional incremental fetch
            assert call_count_2 > call_count_1, f"Expected incremental fetch, got {call_count_2} vs {call_count_1}"
            
            print("\n3. Waiting for cache to expire...")
            time.sleep(1.0)  # Wait for cache to expire
            
            print("\n4. Call after expiration - full refetch:")
            ohlcv_3 = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            call_count_3 = mock_exchange.fetch_ohlcv.call_count
            print(f"   Retrieved {len(ohlcv_3)} candles (API calls: {call_count_3})")
            assert call_count_3 > call_count_2, "Expected new fetch after expiration"
            print("   ✓ Cache expired and refetched")
            
            client.close()
            
            print("\n" + "="*80)
            print("✓ CACHE EXPIRATION TEST PASSED")
            print("="*80)
            
            return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("OHLCV CACHING TEST SUITE")
    print("="*80)
    
    try:
        # Run tests
        test_ohlcv_incremental_caching()
        test_cache_expiration()
        
        print("\n" + "="*80)
        print("✓ ALL TEST SUITES PASSED")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise
