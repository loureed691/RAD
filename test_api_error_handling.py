#!/usr/bin/env python3
"""
Test API error handling and rate limiting
Tests the new error handling mechanisms in KuCoinClient
"""
import sys
import os
import time
from unittest.mock import Mock, MagicMock, patch
import ccxt

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rate_limit_handling():
    """Test that RateLimitExceeded errors are handled with exponential backoff"""
    print("\n" + "=" * 60)
    print("Testing Rate Limit Error Handling")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient
    
    # Create mock exchange that raises RateLimitExceeded
    call_count = [0]
    
    def mock_fetch_ticker(symbol):
        call_count[0] += 1
        if call_count[0] < 3:
            # Fail first 2 attempts
            raise ccxt.RateLimitExceeded("429 Too Many Requests")
        # Succeed on 3rd attempt
        return {'last': 50000, 'symbol': symbol}
    
    with patch('ccxt.kucoinfutures') as mock_ccxt:
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker = mock_fetch_ticker
        mock_exchange.set_position_mode = MagicMock()
        mock_ccxt.return_value = mock_exchange
        
        client = KuCoinClient("key", "secret", "pass", enable_websocket=False)
        client.exchange = mock_exchange
        
        # Test that it retries and succeeds
        start_time = time.time()
        result = client.get_ticker("BTC/USDT:USDT")
        elapsed = time.time() - start_time
        
        assert result is not None, "Should succeed after retries"
        assert result['last'] == 50000, "Should return correct data"
        assert call_count[0] == 3, f"Should have retried 3 times, got {call_count[0]}"
        assert elapsed >= 3, f"Should have used backoff delays (1s + 2s), got {elapsed:.1f}s"
        
        print(f"  ✓ Rate limit error handled successfully")
        print(f"  ✓ Retried {call_count[0]} times")
        print(f"  ✓ Total time with backoff: {elapsed:.1f}s")
    
    return True

def test_insufficient_funds_handling():
    """Test that InsufficientFunds errors are not retried"""
    print("\n" + "=" * 60)
    print("Testing Insufficient Funds Error Handling")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient
    
    call_count = [0]
    
    def mock_create_order(**kwargs):
        call_count[0] += 1
        raise ccxt.InsufficientFunds("Insufficient balance")
    
    with patch('ccxt.kucoinfutures') as mock_ccxt:
        mock_exchange = MagicMock()
        mock_exchange.create_order = mock_create_order
        mock_exchange.set_position_mode = MagicMock()
        mock_exchange.load_markets = MagicMock(return_value={})
        mock_exchange.fetch_ticker = MagicMock(return_value={'last': 50000})
        mock_exchange.fetch_balance = MagicMock(return_value={'USDT': {'free': 1000000}})
        mock_ccxt.return_value = mock_exchange
        
        client = KuCoinClient("key", "secret", "pass", enable_websocket=False)
        client.exchange = mock_exchange
        
        # Test that it doesn't retry insufficient funds
        result = client.create_market_order("BTC/USDT:USDT", "buy", 0.01, leverage=10)
        
        assert result is None, "Should return None for insufficient funds"
        assert call_count[0] == 1, f"Should NOT retry insufficient funds, got {call_count[0]} attempts"
        
        print(f"  ✓ Insufficient funds error handled correctly")
        print(f"  ✓ Did not retry (attempts: {call_count[0]})")
    
    return True

def test_authentication_error_handling():
    """Test that AuthenticationError is raised (critical error)"""
    print("\n" + "=" * 60)
    print("Testing Authentication Error Handling")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient
    
    call_count = [0]
    
    def mock_fetch_balance():
        call_count[0] += 1
        raise ccxt.AuthenticationError("Invalid API key")
    
    with patch('ccxt.kucoinfutures') as mock_ccxt:
        mock_exchange = MagicMock()
        mock_exchange.fetch_balance = mock_fetch_balance
        mock_exchange.set_position_mode = MagicMock()
        mock_ccxt.return_value = mock_exchange
        
        client = KuCoinClient("key", "secret", "pass", enable_websocket=False)
        client.exchange = mock_exchange
        
        # Test that AuthenticationError is raised
        error_raised = False
        try:
            client.get_balance()
        except ccxt.AuthenticationError:
            error_raised = True
        
        assert error_raised, "AuthenticationError should be raised"
        assert call_count[0] == 1, f"Should not retry auth errors, got {call_count[0]} attempts"
        
        print(f"  ✓ Authentication error raised correctly")
        print(f"  ✓ Did not retry (attempts: {call_count[0]})")
    
    return True

def test_network_error_retry():
    """Test that NetworkError is retried with backoff"""
    print("\n" + "=" * 60)
    print("Testing Network Error Handling")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient
    
    call_count = [0]
    
    def mock_fetch_ohlcv(symbol, timeframe, limit):
        call_count[0] += 1
        if call_count[0] < 2:
            raise ccxt.NetworkError("Connection timeout")
        return [[1, 2, 3, 4, 5, 6]]
    
    with patch('ccxt.kucoinfutures') as mock_ccxt:
        mock_exchange = MagicMock()
        mock_exchange.fetch_ohlcv = mock_fetch_ohlcv
        mock_exchange.set_position_mode = MagicMock()
        mock_ccxt.return_value = mock_exchange
        
        client = KuCoinClient("key", "secret", "pass", enable_websocket=False)
        client.exchange = mock_exchange
        
        # Test network error retry
        start_time = time.time()
        result = client.get_ohlcv("BTC/USDT:USDT", "1h", 100)
        elapsed = time.time() - start_time
        
        assert result is not None, "Should succeed after retry"
        assert len(result) == 1, "Should return data"
        assert call_count[0] == 2, f"Should have retried once, got {call_count[0]} attempts"
        assert elapsed >= 1, f"Should have used backoff delay (1s), got {elapsed:.1f}s"
        
        print(f"  ✓ Network error handled with retry")
        print(f"  ✓ Retried {call_count[0]} times")
        print(f"  ✓ Total time with backoff: {elapsed:.1f}s")
    
    return True

def test_exchange_error_codes():
    """Test that specific exchange error codes are handled correctly"""
    print("\n" + "=" * 60)
    print("Testing Exchange Error Code Handling")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient
    
    # Test 400 error (no retry)
    call_count = [0]
    
    def mock_create_order_400(**kwargs):
        call_count[0] += 1
        raise ccxt.ExchangeError("400 Bad Request - Invalid parameter")
    
    with patch('ccxt.kucoinfutures') as mock_ccxt:
        mock_exchange = MagicMock()
        mock_exchange.create_order = mock_create_order_400
        mock_exchange.set_position_mode = MagicMock()
        mock_exchange.load_markets = MagicMock(return_value={})
        mock_exchange.fetch_ticker = MagicMock(return_value={'last': 50000})
        mock_exchange.fetch_balance = MagicMock(return_value={'USDT': {'free': 1000000}})
        mock_ccxt.return_value = mock_exchange
        
        client = KuCoinClient("key", "secret", "pass", enable_websocket=False)
        client.exchange = mock_exchange
        
        result = client.create_limit_order("BTC/USDT:USDT", "buy", 0.01, 50000)
        
        assert result is None, "Should return None for 400 error"
        assert call_count[0] == 1, f"Should NOT retry 400 errors, got {call_count[0]} attempts"
        
        print(f"  ✓ 400 error handled correctly (no retry)")
    
    # Test 500 error (should retry)
    call_count[0] = 0
    
    def mock_create_order_500(**kwargs):
        call_count[0] += 1
        if call_count[0] < 2:
            raise ccxt.ExchangeError("500 Internal Server Error")
        return {'id': '123', 'status': 'open'}
    
    mock_exchange.create_order = mock_create_order_500
    
    start_time = time.time()
    result = client.create_limit_order("BTC/USDT:USDT", "buy", 0.01, 50000)
    elapsed = time.time() - start_time
    
    assert result is not None, "Should succeed after retry"
    assert call_count[0] == 2, f"Should have retried once, got {call_count[0]} attempts"
    assert elapsed >= 1, f"Should have used backoff delay, got {elapsed:.1f}s"
    
    print(f"  ✓ 500 error handled with retry")
    print(f"  ✓ Retried {call_count[0]} times")
    
    return True

def test_max_retries_exhausted():
    """Test behavior when max retries are exhausted"""
    print("\n" + "=" * 60)
    print("Testing Max Retries Exhausted")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient
    
    call_count = [0]
    
    def mock_fetch_ticker(symbol):
        call_count[0] += 1
        # Always fail
        raise ccxt.RateLimitExceeded("429 Too Many Requests")
    
    with patch('ccxt.kucoinfutures') as mock_ccxt:
        mock_exchange = MagicMock()
        mock_exchange.fetch_ticker = mock_fetch_ticker
        mock_exchange.set_position_mode = MagicMock()
        mock_ccxt.return_value = mock_exchange
        
        client = KuCoinClient("key", "secret", "pass", enable_websocket=False)
        client.exchange = mock_exchange
        
        # Test that it gives up after max retries
        start_time = time.time()
        result = client.get_ticker("BTC/USDT:USDT")
        elapsed = time.time() - start_time
        
        assert result is None, "Should return None after exhausting retries"
        assert call_count[0] == 3, f"Should have tried 3 times, got {call_count[0]}"
        # Expected delays: 1s + 2s + 4s (but capped) = at least 3s
        assert elapsed >= 3, f"Should have used all backoff delays, got {elapsed:.1f}s"
        
        print(f"  ✓ Gave up after max retries")
        print(f"  ✓ Total attempts: {call_count[0]}")
        print(f"  ✓ Total time: {elapsed:.1f}s")
    
    return True

def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("API ERROR HANDLING TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Rate Limit Handling", test_rate_limit_handling),
        ("Insufficient Funds Handling", test_insufficient_funds_handling),
        ("Authentication Error Handling", test_authentication_error_handling),
        ("Network Error Retry", test_network_error_retry),
        ("Exchange Error Code Handling", test_exchange_error_codes),
        ("Max Retries Exhausted", test_max_retries_exhausted),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  ✗ {test_name} failed")
        except Exception as e:
            failed += 1
            print(f"\n  ✗ {test_name} failed with exception:")
            print(f"    {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
