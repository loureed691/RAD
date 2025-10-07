#!/usr/bin/env python3
"""
Test that simulates the exact problem scenario from the issue
"""

from unittest.mock import Mock, patch, MagicMock

def test_exact_problem_scenario():
    """
    Simulates the exact scenario from the problem statement:
    - Closing a position (partial exit signal)
    - Available margin: $0.00
    - Should NOT get division by zero error
    - Should create close order successfully with reduce_only=True
    """
    print("\n" + "="*70)
    print("SIMULATING EXACT PROBLEM SCENARIO")
    print("="*70)
    
    print("\nScenario:")
    print("  - Partial exit signal: profit_scaling - First target reached")
    print("  - Available margin: $0.00 (all margin used in open position)")
    print("  - Trying to close position: 44 contracts at 3x leverage")
    print("  - Symbol: BAN/USDT:USDT")
    
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            # Mock the exchange methods
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
                'last': 1.356,  # Current price
                'bid': 1.35,
                'ask': 1.36
            }
            
            # Mock successful order creation
            mock_instance.create_order.return_value = {
                'id': 'close_order_123',
                'status': 'closed',
                'filled': 44,
                'average': 1.356,
                'side': 'sell',
                'amount': 44
            }
            
            mock_instance.fetch_order.return_value = {
                'id': 'close_order_123',
                'status': 'closed',
                'filled': 44,
                'average': 1.356
            }
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            print("\n" + "-"*70)
            print("BEFORE FIX (Expected behavior):")
            print("  13:51:12 ⚠️ WARNING Margin check failed: available=$0.00")
            print("  13:51:12 ⚠️ WARNING Amount 0.0000 below minimum 1.0")
            print("  13:51:12 ✗ ERROR Error adjusting position: float division by zero")
            print("  13:51:13 ✗ ERROR Failed to create close order for BAN/USDT:USDT")
            
            print("\n" + "-"*70)
            print("AFTER FIX (Testing now):")
            print("-"*70)
            
            # Mock get_balance to return zero margin (all margin in position)
            with patch.object(client, 'get_balance') as mock_balance:
                mock_balance.return_value = {
                    'free': {'USDT': 0.0},  # Zero available margin
                    'used': {'USDT': 20.0},  # All margin used in position
                    'total': {'USDT': 20.0}
                }
                
                print("\nAttempting to close 44 contracts (reduce_only=True)...")
                
                # This should succeed WITHOUT division by zero error
                order = client.create_market_order(
                    symbol='BAN/USDT:USDT',
                    side='sell',
                    amount=44.0,
                    leverage=3,
                    reduce_only=True  # This is the key fix
                )
                
                print("\n" + "-"*70)
                if order and order.get('id'):
                    print("✓ SUCCESS: Close order created without errors!")
                    print(f"  Order ID: {order['id']}")
                    print(f"  Status: {order.get('status')}")
                    print(f"  Filled: {order.get('filled')} contracts")
                    print(f"  Average Price: ${order.get('average'):.3f}")
                    print("\n✓ No division by zero error!")
                    print("✓ No margin check error!")
                    print("✓ Position closed successfully!")
                    return True
                else:
                    print("✗ FAILED: Order was not created")
                    return False
                    
    except ZeroDivisionError as e:
        print("\n" + "="*70)
        print("✗ DIVISION BY ZERO ERROR STILL OCCURS!")
        print(f"  Error: {e}")
        print("="*70)
        import traceback
        traceback.print_exc()
        return False
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_exact_problem_scenario()
    
    print("\n" + "="*70)
    if success:
        print("✓ PROBLEM FIXED!")
        print("  Close orders now work with zero margin using reduce_only=True")
    else:
        print("✗ PROBLEM STILL EXISTS")
    print("="*70)
