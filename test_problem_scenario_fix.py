#!/usr/bin/env python3
"""
Test for the specific problem scenario where adjusted position is rejected
even though it's viable.

Problem from logs:
- Desired position: 11634.2087 contracts at $0.000100901 with 12x leverage
- Available margin: $46.96
- Adjusted position: 20.9416 contracts
- OLD BEHAVIOR: REJECTED because 20.9416 < 11634.2087 * 0.1 (only 0.18% of desired)
- NEW BEHAVIOR: Should ACCEPT because position value ~$2.11 and margin ~$0.18 are viable

The adjusted position should be accepted because:
- Position value: 20.9416 * $0.000100901 = $2.11 (> $1 minimum)
- Required margin: $2.11 / 12 = $0.176 (> $0.10 minimum)
- Meets exchange minimums
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
                    'contractSize': 100000,  # FLOKI has a large contract multiplier
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
            def create_order_side_effect(*args, **kwargs):
                return {
                    'id': 'test123',
                    'symbol': kwargs.get('symbol', 'FLOKI/USDT:USDT'),
                    'side': kwargs.get('side', 'sell'),
                    'amount': kwargs.get('amount', 20.9416),
                    'average': 0.000100901,
                    'status': 'closed'
                }
            mock_instance.create_order.side_effect = create_order_side_effect
            
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
            calculated_adjusted = max_position_value / price  # Many contracts
            
            # But we need to see what actually happens with validation
            print(f"\nExpected adjustment calculation:")
            print(f"  Usable margin (90%): ${usable_margin:.2f}")
            print(f"  Max position value: ${max_position_value:.2f}")
            print(f"  Initial calculated: {calculated_adjusted:.4f} contracts")
            
            # Now try to create the order
            print(f"\nAttempting to create order...")
            result = client.create_market_order(
                symbol=symbol,
                side='sell',
                amount=desired_amount,
                leverage=leverage
            )
            
            if result:
                actual_amount = result['amount']
                contract_size = 100000
                actual_value = actual_amount * price * contract_size
                actual_margin = actual_value / leverage
                
                print(f"  ✓ Order created successfully!")
                print(f"    Filled: {actual_amount} contracts")
                print(f"    Position value: ${actual_value:.2f}")
                print(f"    Required margin: ${actual_margin:.2f}")
                
                # Verify the position is viable
                if actual_value >= 1.0 and actual_margin >= 0.10:
                    print(f"  ✓ Position meets viability criteria")
                    return True
                else:
                    print(f"  ✗ Position doesn't meet viability criteria")
                    return False
            else:
                print(f"  ✗ Order was rejected")
                print(f"  This could be correct if adjusted position doesn't meet minimums,")
                print(f"  but should NOT be rejected just for being small relative to desired size")
                return False
                
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_viability_checks():
    """Test the is_position_viable method directly"""
    print("\n" + "="*70)
    print("TESTING POSITION VIABILITY CHECKS")
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
                'TEST/USDT:USDT': {
                    'contractSize': 100000,  # Use large contract size like FLOKI
                    'limits': {
                        'amount': {'min': 1, 'max': 1000000},
                        'cost': {'min': 1, 'max': None}
                    }
                }
            }
            
            symbol = 'TEST/USDT:USDT'
            
            # Test 1: Viable position (from problem statement)
            print(f"\nTest 1: Position from problem statement (should be VIABLE)")
            amount = 20.9416
            price = 0.000100901
            leverage = 12
            contract_size = 100000
            is_viable, reason = client.is_position_viable(symbol, amount, price, leverage)
            position_value = amount * price * contract_size
            required_margin = position_value / leverage
            print(f"  Amount: {amount:.4f}, Price: ${price}, Leverage: {leverage}x")
            print(f"  Position value: ${position_value:.2f}, Required margin: ${required_margin:.2f}")
            print(f"  Result: {'✓ VIABLE' if is_viable else '✗ NOT VIABLE'} - {reason}")
            if not is_viable:
                print(f"  ✗ FAIL: This position should be viable!")
                return False
            
            # Test 2: Below minimum value (after accounting for contract size)
            print(f"\nTest 2: Position below $1 value (should be NOT VIABLE)")
            amount = 0.005  # Very small amount
            price = 0.0001
            leverage = 12
            is_viable, reason = client.is_position_viable(symbol, amount, price, leverage)
            position_value = amount * price * contract_size
            print(f"  Amount: {amount:.4f}, Price: ${price}, Leverage: {leverage}x")
            print(f"  Position value: ${position_value:.4f}")
            print(f"  Result: {'✓ VIABLE' if is_viable else '✗ NOT VIABLE'} - {reason}")
            if is_viable:
                print(f"  ✗ FAIL: Position below $1 should not be viable!")
                return False
            
            # Test 3: Below minimum margin
            print(f"\nTest 3: Position with tiny margin (should be NOT VIABLE)")
            amount = 0.001  # Extremely small
            price = 0.001
            leverage = 100  # Extreme leverage to make margin tiny
            is_viable, reason = client.is_position_viable(symbol, amount, price, leverage)
            position_value = amount * price * contract_size
            required_margin = position_value / leverage
            print(f"  Amount: {amount:.4f}, Price: ${price}, Leverage: {leverage}x")
            print(f"  Position value: ${position_value:.2f}, Required margin: ${required_margin:.4f}")
            print(f"  Result: {'✓ VIABLE' if is_viable else '✗ NOT VIABLE'} - {reason}")
            if is_viable:
                print(f"  ✗ FAIL: Position with margin < $0.10 should not be viable!")
                return False
            
            # Test 4: Normal viable position
            print(f"\nTest 4: Normal position (should be VIABLE)")
            amount = 100
            price = 0.001
            leverage = 10
            is_viable, reason = client.is_position_viable(symbol, amount, price, leverage)
            position_value = amount * price * contract_size
            required_margin = position_value / leverage
            print(f"  Amount: {amount:.4f}, Price: ${price}, Leverage: {leverage}x")
            print(f"  Position value: ${position_value:.2f}, Required margin: ${required_margin:.2f}")
            print(f"  Result: {'✓ VIABLE' if is_viable else '✗ NOT VIABLE'} - {reason}")
            if not is_viable:
                print(f"  ✗ FAIL: This normal position should be viable!")
                return False
            
            print(f"\n✓ All viability checks passed!")
            return True
            
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\nTesting fix for margin-adjusted position rejection...")
    
    test1_passed = test_problem_scenario()
    test2_passed = test_viability_checks()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Problem scenario test: {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Viability checks test: {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n✓ All tests passed! Fix is working correctly.")
        return 0
    else:
        print("\n✗ Some tests failed.")
        return 1

if __name__ == '__main__':
    exit(main())
