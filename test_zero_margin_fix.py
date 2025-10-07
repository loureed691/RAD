#!/usr/bin/env python3
"""
Test script for zero margin division by zero fix
Tests that the system properly handles:
1. Zero available margin without division by zero
2. reduce_only parameter in create_market_order
3. Closing positions without margin checks
"""

from unittest.mock import Mock, patch, MagicMock

def test_zero_margin_adjustment():
    """Test that adjust_position_for_margin handles zero margin without division by zero"""
    print("\nTesting zero margin adjustment...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            # Mock load_markets to return contract info
            mock_instance.load_markets.return_value = {
                'BAN/USDT:USDT': {
                    'contractSize': 1,
                    'limits': {
                        'amount': {'min': 1.0, 'max': 10000},
                        'cost': {'min': 1.0, 'max': 100000}
                    }
                }
            }
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Test Case 1: Zero margin should not cause division by zero
            print("  Test 1: Zero available margin")
            adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
                'BAN/USDT:USDT', 100, 1.0, 7, 0.00
            )
            
            # Should return 0.0, 1 indicating failure
            print(f"    Result: amount={adjusted_amount:.4f}, leverage={adjusted_leverage}x")
            assert adjusted_amount == 0.0, f"Expected 0.0 amount, got {adjusted_amount}"
            assert adjusted_leverage == 1, f"Expected 1x leverage, got {adjusted_leverage}"
            print("    ✓ Zero margin handled without division by zero")
            
            # Test Case 2: Very small margin (below threshold)
            print("  Test 2: Very small available margin ($0.005)")
            adjusted_amount2, adjusted_leverage2 = client.adjust_position_for_margin(
                'BAN/USDT:USDT', 100, 1.0, 7, 0.005
            )
            
            # Should also return 0.0, 1 as it's below $0.01 threshold
            print(f"    Result: amount={adjusted_amount2:.4f}, leverage={adjusted_leverage2}x")
            assert adjusted_amount2 == 0.0, f"Expected 0.0 amount, got {adjusted_amount2}"
            assert adjusted_leverage2 == 1, f"Expected 1x leverage, got {adjusted_leverage2}"
            print("    ✓ Small margin handled without division by zero")
            
            # Test Case 3: Sufficient margin should work normally
            print("  Test 3: Sufficient available margin ($10.00)")
            adjusted_amount3, adjusted_leverage3 = client.adjust_position_for_margin(
                'BAN/USDT:USDT', 100, 1.0, 7, 10.00
            )
            
            # Should return adjusted values
            print(f"    Result: amount={adjusted_amount3:.4f}, leverage={adjusted_leverage3}x")
            assert adjusted_amount3 > 0, f"Expected positive amount, got {adjusted_amount3}"
            print("    ✓ Normal margin adjustment works correctly")
            
        print("✓ Zero margin adjustment tests passed")
        return True
    except Exception as e:
        print(f"✗ Zero margin adjustment test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reduce_only_parameter():
    """Test that create_market_order supports reduce_only parameter"""
    print("\nTesting reduce_only parameter in create_market_order...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            # Mock the methods
            mock_instance.load_markets.return_value = {
                'BAN/USDT:USDT': {
                    'contractSize': 1,
                    'limits': {
                        'amount': {'min': 1.0, 'max': 10000},
                        'cost': {'min': 1.0, 'max': 100000}
                    }
                }
            }
            
            mock_instance.fetch_ticker.return_value = {
                'last': 1.0,
                'bid': 0.99,
                'ask': 1.01
            }
            
            mock_instance.create_order.return_value = {
                'id': 'test_order_123',
                'status': 'closed',
                'filled': 100,
                'average': 1.0
            }
            
            mock_instance.fetch_order.return_value = {
                'id': 'test_order_123',
                'status': 'closed',
                'filled': 100,
                'average': 1.0
            }
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Test Case 1: reduce_only=True should skip margin check
            print("  Test 1: reduce_only=True (closing position)")
            
            # Mock get_balance to return zero margin (would normally fail)
            with patch.object(client, 'get_balance') as mock_balance:
                mock_balance.return_value = {
                    'free': {'USDT': 0.0},
                    'used': {'USDT': 100.0},
                    'total': {'USDT': 100.0}
                }
                
                # This should succeed even with zero margin because reduce_only=True
                order = client.create_market_order(
                    'BAN/USDT:USDT', 'sell', 44.0, leverage=3, reduce_only=True
                )
                
                print(f"    Result: order={'success' if order else 'failed'}")
                assert order is not None, "Order should succeed with reduce_only=True even with zero margin"
                print("    ✓ reduce_only=True bypasses margin check")
            
            # Test Case 2: reduce_only=False should check margin
            print("  Test 2: reduce_only=False (opening position)")
            
            with patch.object(client, 'get_balance') as mock_balance:
                mock_balance.return_value = {
                    'free': {'USDT': 0.0},
                    'used': {'USDT': 100.0},
                    'total': {'USDT': 100.0}
                }
                
                # This should fail because of zero margin
                order2 = client.create_market_order(
                    'BAN/USDT:USDT', 'buy', 44.0, leverage=3, reduce_only=False
                )
                
                print(f"    Result: order={'success' if order2 else 'failed'}")
                assert order2 is None, "Order should fail with reduce_only=False and zero margin"
                print("    ✓ reduce_only=False enforces margin check")
            
        print("✓ reduce_only parameter tests passed")
        return True
    except Exception as e:
        print(f"✗ reduce_only parameter test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zero_price_protection():
    """Test that adjust_position_for_margin handles zero price"""
    print("\nTesting zero price protection...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            mock_instance.load_markets.return_value = {
                'TEST/USDT:USDT': {
                    'contractSize': 1,
                    'limits': {
                        'amount': {'min': 1.0, 'max': 10000},
                        'cost': {'min': 1.0, 'max': 100000}
                    }
                }
            }
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Test with zero price
            print("  Test: Zero price")
            adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
                'TEST/USDT:USDT', 100, 0.0, 7, 10.00
            )
            
            # Should return 0.0, 1 indicating failure
            print(f"    Result: amount={adjusted_amount:.4f}, leverage={adjusted_leverage}x")
            assert adjusted_amount == 0.0, f"Expected 0.0 amount, got {adjusted_amount}"
            assert adjusted_leverage == 1, f"Expected 1x leverage, got {adjusted_leverage}"
            print("    ✓ Zero price handled without division by zero")
            
        print("✓ Zero price protection tests passed")
        return True
    except Exception as e:
        print(f"✗ Zero price protection test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING ZERO MARGIN FIX")
    print("=" * 60)
    
    results = []
    results.append(test_zero_margin_adjustment())
    results.append(test_reduce_only_parameter())
    results.append(test_zero_price_protection())
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    if all(results):
        print("✓ All tests passed!")
    else:
        print(f"✗ {len(results) - sum(results)} test(s) failed")
    print("=" * 60)
