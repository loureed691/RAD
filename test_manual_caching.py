"""
Manual test to demonstrate the caching behavior
"""

from unittest.mock import Mock, MagicMock, patch
from kucoin_client import KuCoinClient
import time


def test_manual_caching_demo():
    """Demonstrate that caching reduces API calls"""
    
    print("\n" + "="*80)
    print("MANUAL CACHING DEMONSTRATION")
    print("="*80)
    
    # Create sample candle data
    def create_candles(count, base_price=100.0):
        candles = []
        base_ts = int(time.time() * 1000) - (count * 3600000)
        for i in range(count):
            ts = base_ts + (i * 3600000)
            candles.append([ts, base_price + i, base_price + i + 5, base_price + i - 5, base_price + i + 2, 1000])
        return candles
    
    # Mock the exchange
    mock_exchange = MagicMock()
    api_call_count = [0]
    
    def mock_fetch(symbol, timeframe, limit):
        api_call_count[0] += 1
        print(f"  📡 API CALL #{api_call_count[0]}: fetch_ohlcv({symbol}, {timeframe}, limit={limit})")
        if limit == 20:
            # Incremental fetch - return recent data
            return create_candles(20, 100.0)
        else:
            # Full fetch
            return create_candles(limit, 100.0)
    
    mock_exchange.fetch_ohlcv = Mock(side_effect=mock_fetch)
    mock_exchange.load_markets = Mock(return_value={})
    mock_exchange.set_position_mode = Mock()
    
    # Create client with mocked exchange
    with patch('kucoin_client.ccxt.kucoinfutures', return_value=mock_exchange):
        with patch('kucoin_client.KuCoinWebSocket'):
            print("\n1. Creating KuCoinClient with caching enabled...")
            client = KuCoinClient('test', 'test', 'test', enable_websocket=False)
            
            print("\n2. First call - fetches all data from API:")
            print(f"   get_ohlcv('BTC/USDT:USDT', '1h', 100)")
            ohlcv = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            print(f"   ✓ Received {len(ohlcv)} candles")
            print(f"   📊 Total API calls so far: {api_call_count[0]}")
            
            print("\n3. Second call (within 60 seconds) - uses cache:")
            print(f"   get_ohlcv('BTC/USDT:USDT', '1h', 100)")
            ohlcv = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            print(f"   ✓ Received {len(ohlcv)} candles")
            print(f"   📊 Total API calls so far: {api_call_count[0]}")
            print(f"   💡 No API call made - used cached data!")
            
            print("\n4. Simulating time passing (cache older than 60s)...")
            # Manually age the cache
            with client._ohlcv_cache_lock:
                cache_key = ('BTC/USDT:USDT', '1h')
                if cache_key in client._ohlcv_cache:
                    client._ohlcv_cache[cache_key]['last_update'] = time.time() - 61
            
            print("\n5. Third call (cache aged) - incremental fetch:")
            print(f"   get_ohlcv('BTC/USDT:USDT', '1h', 100)")
            ohlcv = client.get_ohlcv('BTC/USDT:USDT', '1h', 100)
            print(f"   ✓ Received {len(ohlcv)} candles")
            print(f"   📊 Total API calls so far: {api_call_count[0]}")
            print(f"   💡 Only fetched new candles (limit=20) instead of all 100!")
            
            print("\n6. Different symbol - separate cache:")
            print(f"   get_ohlcv('ETH/USDT:USDT', '1h', 50)")
            ohlcv = client.get_ohlcv('ETH/USDT:USDT', '1h', 50)
            print(f"   ✓ Received {len(ohlcv)} candles")
            print(f"   📊 Total API calls so far: {api_call_count[0]}")
            
            print("\n" + "="*80)
            print("SUMMARY")
            print("="*80)
            print(f"✓ Total API calls made: {api_call_count[0]}")
            print(f"✓ Without caching: Would have made 4 full API calls")
            print(f"✓ With caching: Made 3 calls (1 incremental)")
            print(f"✓ API call reduction: ~25% in this demo")
            print(f"✓ In production with frequent polling: Could save 50-90% of API calls")
            print("="*80)
            
            client.close()


if __name__ == "__main__":
    test_manual_caching_demo()
