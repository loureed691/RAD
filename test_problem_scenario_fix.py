#!/usr/bin/env python3
"""
Test for the specific problem scenario where adjusted position is rejected
even though it's viable.

Problem from logs:
- Desired position: 11634.2087 contracts at $0.000100901 with 12x leverage
- Available margin: $46.96
- Adjusted position: 20.9416 contracts
- Result: REJECTED because 20.9416 < 11634.2087 * 0.1 (only 0.18% of desired)

But the adjusted position is actually viable:
- Position value: 20.9416 * $0.000100901 = $2.11
- Required margin: $2.11 / 12 = $0.176
- This should be accepted!
"""

import sys
from unittest.mock import Mock, MagicMock, patch

def test_problem_scenario():
    """Test the exact scenario from the problem statement"""
    print("\n" + "="*70)
    print("TESTING PROBLEM SCENARIO FIX")
    print("="*70)
    
    try:
        from kucoin_client import KuCoinClient
        
        # Create a mock client
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            # Create client
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock the exchange methods
            mock_instance.load_markets.return_value = {
                'FLOKI/USDT:USDT': {
                    'contractSize': 1,
                    'limits': {
                        'amount': {'min': 1, 'max': 1000000},
                        'cost': {'min': 1, 'max': None}
                    }
                }
            }
            
            mock_instance.fetch_ticker.return_value = {
                'last': 0.000100901,
                'bid': 0.000100900,
                'ask': 0.000100902
            }
            
            # Available margin: $46.96 (from problem statement)
            mock_instance.fetch_balance.return_value = {
                'free': {'USDT': 46.96},
                'used': {'USDT': 0},
                'total': {'USDT': 46.96}
            }
            
            # Mock order book (for depth validation)
            mock_instance.fetch_order_book.return_value = {
                'bids': [[0.000100900, 100000], [0.000100890, 100000]],
                'asks': [[0.000100902, 100000], [0.000100912, 100000]],
                'timestamp': 1234567890
            }
            
            # Mock successful order creation
            mock_instance.create_order.return_value = {
                'id': 'test123',
                'symbol': 'FLOKI/USDT:USDT',
                'side': 'sell',
                'amount': 20.9416,
                'average': 0.000100901,
                'status': 'closed'
            }
            
            # Test parameters from problem statement
            symbol = 'FLOKI/USDT:USDT'
            desired_amount = 11634.2087  # Original desired position
            price = 0.000100901
            leverage = 12
            
            print(f"\nScenario from problem statement:")
            print(f"  Symbol: {symbol}")
            print(f"  Desired position: {desired_amount:.4f} contracts")
            print(f"  Price: ${price}")
            print(f"  Leverage: {leverage}x")
            print(f"  Available margin: $46.96")
            
            # Calculate what the adjusted position would be
            available_margin = 46.96
            usable_margin = available_margin * 0.90  # $42.26
            max_position_value = usable_margin * leverage  # $507.12
            adjusted_amount = max_position_value / price  # ~5026 contracts
            
            # But validate_and_cap_amount will cap it to exchange limits
            # Let's check what the actual adjustment would be
            print(f"\nExpected adjustment calculation:")
            print(f"  Usable margin (90%): ${usable_margin:.2f}")
            print(f"  Max position value: ${max_position_value:.2f}")
            print(f"  Calculated adjusted amount: {adjusted_amount:.4f} contracts")
            
            # Now try to create the order
            print(f"\nAttempting to create order...")
            result = client.create_market_order(
                symbol=symbol,
                side='sell',
                amount=desired_amount,
                leverage=leverage
            )
            
            if result:
                print(f"  ✓ Order created successfully!")
                print(f"    Filled: {result['amount']} contracts")
                return True
            else:
                print(f"  ✗ Order was rejected (should have been adjusted and accepted)")
                return False
                
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("\nTesting fix for problem scenario...")
    success = test_problem_scenario()
    
    print("\n" + "="*70)
    if success:
        print("✓ Test passed! Order is accepted after adjustment.")
    else:
        print("✗ Test failed! Order is still being rejected.")
    print("="*70)
    
    return 0 if success else 1

if __name__ == '__main__':
    exit(main())
