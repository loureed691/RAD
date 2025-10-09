#!/usr/bin/env python3
"""
Test rate limiting improvements for API calls
Validates that position monitoring and order execution respect KuCoin rate limits
"""
import sys
import os
import time
import threading
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rate_limit_override():
    """Test that ccxt rate limit is properly overridden to safe KuCoin limits"""
    print("\n" + "=" * 60)
    print("Testing Rate Limit Override")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient
    
    # Mock the exchange initialization
    with patch('ccxt.kucoinfutures') as mock_exchange:
        mock_instance = MagicMock()
        mock_instance.rateLimit = 75  # Default ccxt value
        mock_exchange.return_value = mock_instance
        
        # Initialize client
        client = KuCoinClient('test_key', 'test_secret', 'test_pass')
        
        # Verify rate limit was overridden
        assert mock_instance.rateLimit == 250, \
            f"Rate limit should be 250ms, got {mock_instance.rateLimit}ms"
        
        print(f"  ✓ Rate limit overridden from 75ms to 250ms")
        print(f"  ✓ Max calls per second: {1000/mock_instance.rateLimit:.1f}")
        print(f"  ✓ Max calls per minute: {60000/mock_instance.rateLimit:.0f}")
        print(f"  ✓ Safely within KuCoin's limit of 240 calls/minute")
    
    return True

def test_explicit_rate_limiting():
    """Test that explicit rate limiting is enforced between API calls"""
    print("\n" + "=" * 60)
    print("Testing Explicit Rate Limiting")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient
    
    with patch('ccxt.kucoinfutures') as mock_exchange:
        mock_instance = MagicMock()
        mock_exchange.return_value = mock_instance
        
        client = KuCoinClient('test_key', 'test_secret', 'test_pass')
        
        # Test multiple consecutive calls - measure AFTER enforcement
        call_times = []
        
        # First call to initialize
        client._enforce_rate_limit()
        
        # Now test 5 consecutive calls
        for i in range(5):
            client._enforce_rate_limit()
            call_times.append(time.time())  # Measure AFTER rate limit enforcement
        
        # Check intervals between calls
        intervals = []
        for i in range(1, len(call_times)):
            interval = call_times[i] - call_times[i-1]
            intervals.append(interval)
        
        min_interval = min(intervals)
        avg_interval = sum(intervals) / len(intervals)
        
        print(f"  Calls made: {len(call_times)}")
        print(f"  Min interval: {min_interval*1000:.1f}ms")
        print(f"  Avg interval: {avg_interval*1000:.1f}ms")
        print(f"  Target interval: 250ms")
        
        # Verify minimum interval is enforced (with 10ms tolerance for timing variance)
        assert min_interval >= 0.24, \
            f"Min interval {min_interval*1000:.1f}ms should be >= 240ms"
        
        print(f"  ✓ Rate limiting enforced correctly")
    
    return True

def test_order_creation_rate_limiting():
    """Test that order creation includes rate limiting between API calls"""
    print("\n" + "=" * 60)
    print("Testing Order Creation Rate Limiting")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient
    
    with patch('ccxt.kucoinfutures') as mock_exchange:
        mock_instance = MagicMock()
        mock_instance.set_margin_mode = MagicMock()
        mock_instance.set_leverage = MagicMock()
        mock_instance.create_order = MagicMock(return_value={'id': 'test123', 'status': 'open'})
        mock_instance.fetch_order = MagicMock(return_value={'id': 'test123', 'status': 'closed'})
        mock_exchange.return_value = mock_instance
        
        client = KuCoinClient('test_key', 'test_secret', 'test_pass')
        
        # Mock other methods
        client.get_ticker = MagicMock(return_value={'last': 50000})
        client.validate_and_cap_amount = MagicMock(return_value=1.0)
        client.check_available_margin = MagicMock(return_value=(True, 1000, 'OK'))
        
        # Track API call times
        api_call_times = []
        
        def track_call(*args, **kwargs):
            api_call_times.append(time.time())
            return MagicMock()
        
        mock_instance.set_margin_mode.side_effect = track_call
        mock_instance.set_leverage.side_effect = track_call
        mock_instance.create_order.side_effect = track_call
        
        # Create an order
        start = time.time()
        result = client.create_market_order('BTC/USDT:USDT', 'buy', 1.0, leverage=10)
        duration = time.time() - start
        
        print(f"  Order creation took: {duration*1000:.0f}ms")
        print(f"  API calls made: {len(api_call_times)}")
        
        # Check intervals between API calls within order creation
        if len(api_call_times) > 1:
            intervals = []
            for i in range(1, len(api_call_times)):
                interval = api_call_times[i] - api_call_times[i-1]
                intervals.append(interval)
            
            min_interval = min(intervals)
            print(f"  Min interval between API calls: {min_interval*1000:.1f}ms")
            
            # Should have rate limiting between internal API calls
            assert min_interval >= 0.24, \
                f"Min interval {min_interval*1000:.1f}ms should be >= 240ms"
            
            print(f"  ✓ Rate limiting enforced during order creation")
        else:
            print(f"  ⚠️  Only one API call detected, cannot verify intervals")
    
    return True

def test_position_monitoring_rate_limiting():
    """Test that position monitoring respects rate limits"""
    print("\n" + "=" * 60)
    print("Testing Position Monitoring Rate Limiting")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient, APICallPriority
    
    with patch('ccxt.kucoinfutures') as mock_exchange:
        mock_instance = MagicMock()
        mock_instance.fetch_positions = MagicMock(return_value=[
            {'symbol': 'BTC/USDT:USDT', 'contracts': 1, 'side': 'long'}
        ])
        mock_exchange.return_value = mock_instance
        
        client = KuCoinClient('test_key', 'test_secret', 'test_pass')
        
        # Simulate rapid position checks - time AFTER each call completes
        call_times = []
        for i in range(5):
            positions = client.get_open_positions()
            call_times.append(time.time())  # Record time AFTER call completes
        
        # Check actual intervals
        intervals = []
        for i in range(1, len(call_times)):
            interval = call_times[i] - call_times[i-1]
            intervals.append(interval)
        
        min_interval = min(intervals)
        avg_interval = sum(intervals) / len(intervals)
        
        print(f"  Position checks: {len(call_times)}")
        print(f"  Min interval: {min_interval*1000:.0f}ms")
        print(f"  Avg interval: {avg_interval*1000:.0f}ms")
        
        # Should respect rate limiting (250ms minimum)
        assert min_interval >= 0.24, \
            f"Min interval {min_interval*1000:.0f}ms should be >= 240ms"
        
        print(f"  ✓ Position monitoring respects rate limits")
    
    return True

def test_concurrent_operations_rate_limiting():
    """Test that concurrent operations (scanning + position monitoring) respect rate limits"""
    print("\n" + "=" * 60)
    print("Testing Concurrent Operations Rate Limiting")
    print("=" * 60)
    
    from kucoin_client import KuCoinClient, APICallPriority
    
    with patch('ccxt.kucoinfutures') as mock_exchange:
        mock_instance = MagicMock()
        mock_instance.fetch_positions = MagicMock(return_value=[])
        mock_instance.fetch_ticker = MagicMock(return_value={'last': 50000})
        mock_exchange.return_value = mock_instance
        
        client = KuCoinClient('test_key', 'test_secret', 'test_pass')
        
        # Track all API call completion times across threads
        api_call_times = []
        api_call_lock = threading.Lock()
        
        def monitor_positions():
            """Simulate position monitoring"""
            for _ in range(3):
                client.get_open_positions()
                with api_call_lock:
                    api_call_times.append(('position', time.time()))
        
        def scan_market():
            """Simulate market scanning"""
            for _ in range(3):
                client.get_ticker('BTC/USDT:USDT', priority=APICallPriority.NORMAL)
                with api_call_lock:
                    api_call_times.append(('scan', time.time()))
        
        # Run both threads concurrently
        t1 = threading.Thread(target=monitor_positions)
        t2 = threading.Thread(target=scan_market)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # Sort by time
        api_call_times.sort(key=lambda x: x[1])
        
        print(f"  Total API calls: {len(api_call_times)}")
        
        # Check intervals between ALL calls (regardless of thread)
        intervals = []
        for i in range(1, len(api_call_times)):
            interval = api_call_times[i][1] - api_call_times[i-1][1]
            intervals.append(interval)
        
        if intervals:
            min_interval = min(intervals)
            avg_interval = sum(intervals) / len(intervals)
            
            print(f"  Min interval between any calls: {min_interval*1000:.0f}ms")
            print(f"  Avg interval between calls: {avg_interval*1000:.0f}ms")
            
            # Even with concurrent threads, rate limiting should be enforced
            assert min_interval >= 0.24, \
                f"Min interval {min_interval*1000:.0f}ms should be >= 240ms"
            
            print(f"  ✓ Rate limiting enforced across concurrent operations")
        else:
            print(f"  ⚠️  Not enough calls to verify intervals")
    
    return True

def run_all_tests():
    """Run all rate limiting tests"""
    print("\n" + "=" * 80)
    print("RATE LIMITING IMPROVEMENTS - TEST SUITE")
    print("=" * 80)
    
    tests = [
        test_rate_limit_override,
        test_explicit_rate_limiting,
        test_order_creation_rate_limiting,
        test_position_monitoring_rate_limiting,
        test_concurrent_operations_rate_limiting,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n  ✗ {test_func.__name__} failed with exception:")
            print(f"    {str(e)}")
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
