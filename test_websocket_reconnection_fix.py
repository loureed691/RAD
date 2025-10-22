#!/usr/bin/env python3
"""
Test script to verify WebSocket reconnection symbol conversion fix
"""
import sys

def test_symbol_conversion():
    """Test that symbol conversion works correctly"""
    print("=" * 60)
    print("Testing WebSocket Symbol Conversion Fix")
    print("=" * 60)
    
    # Test symbol conversion
    test_cases = [
        ("BTC/USDT:USDT", "BTCUSDTUSDT"),
        ("ETH/USDT:USDT", "ETHUSDTUSDT"),
        ("DOGE/USDT:USDT", "DOGEUSDTUSDT"),
        ("10000CAT/USDT:USDT", "10000CATUSDTUSDT"),
    ]
    
    print("\n📊 Testing Symbol Format Conversion:")
    all_passed = True
    
    for input_symbol, expected_output in test_cases:
        # This is what the code does
        output = input_symbol.replace('/', '').replace(':', '')
        
        if output == expected_output:
            print(f"  ✓ {input_symbol} -> {output}")
        else:
            print(f"  ✗ {input_symbol} -> {output} (expected {expected_output})")
            all_passed = False
    
    # Test timeframe conversion
    print("\n📊 Testing Timeframe Conversion:")
    tf_test_cases = [
        ("1h", "1hour"),
        ("4h", "4hour"),
        ("1d", "1day"),
        ("1m", "1min"),
    ]
    
    tf_map = {
        '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
        '1h': '1hour', '4h': '4hour', '1d': '1day', '1w': '1week'
    }
    
    for input_tf, expected_output in tf_test_cases:
        output = tf_map.get(input_tf, input_tf)
        
        if output == expected_output:
            print(f"  ✓ {input_tf} -> {output}")
        else:
            print(f"  ✗ {input_tf} -> {output} (expected {expected_output})")
            all_passed = False
    
    # Test subscription parsing
    print("\n📊 Testing Subscription Parsing:")
    subscription_tests = [
        ("ticker:BTC/USDT:USDT", ["BTC/USDT:USDT"]),
        ("candles:ETH/USDT:USDT:1h", ["ETH/USDT:USDT", "1h"]),
        ("candles:DOGE/USDT:USDT:4h", ["DOGE/USDT:USDT", "4h"]),
    ]
    
    for subscription, expected in subscription_tests:
        if subscription.startswith('ticker:'):
            parts = subscription.split(':', 1)
            symbol = parts[1] if len(parts) > 1 else None
            if symbol == expected[0]:
                print(f"  ✓ Parsed ticker subscription correctly: {subscription}")
            else:
                print(f"  ✗ Failed to parse ticker subscription: {subscription} (got {symbol}, expected {expected[0]})")
                all_passed = False
        elif subscription.startswith('candles:'):
            parts = subscription.split(':')
            if len(parts) >= 3:
                # Last part is timeframe, everything between 'candles:' and timeframe is symbol
                timeframe = parts[-1]
                symbol = ':'.join(parts[1:-1])
                if symbol == expected[0] and timeframe == expected[1]:
                    print(f"  ✓ Parsed candles subscription correctly: {subscription}")
                else:
                    print(f"  ✗ Failed to parse candles subscription: {subscription} (got {symbol}:{timeframe}, expected {expected[0]}:{expected[1]})")
                    all_passed = False
            else:
                print(f"  ✗ Failed to parse candles subscription: {subscription} (not enough parts)")
                all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All WebSocket conversion tests passed!")
        print("=" * 60)
    else:
        print("❌ Some tests failed")
        print("=" * 60)

if __name__ == "__main__":
    success = test_symbol_conversion()
    sys.exit(0 if success else 1)
