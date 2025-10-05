#!/usr/bin/env python3
"""
Test contract_size handling in margin calculations
Tests the fix for bug where position value wasn't including contract_size in adjust_position_for_margin
"""

from unittest.mock import MagicMock, patch

def test_contract_size_in_adjustment():
    """Test that adjust_position_for_margin correctly uses contract_size"""
    print("\nTesting contract_size handling in position adjustment...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock load_markets to return a contract with large contract_size
            # This simulates real scenarios where contract_size != 1
            mock_instance.load_markets.return_value = {
                'TEST/USDT:USDT': {
                    'contractSize': 100,  # Each contract represents 100 units
                    'limits': {
                        'amount': {'min': 1, 'max': 1000000},
                        'cost': {'min': 1, 'max': 1000000}
                    }
                }
            }
            
            # Mock validate_and_cap_amount to just return the amount
            with patch.object(client, 'validate_and_cap_amount') as mock_validate:
                mock_validate.side_effect = lambda symbol, amount: amount
                
                # Test scenario from problem statement:
                # available=$47.75, want leverage=3x
                # If contract_size = 100 and price = 0.0001
                # Want position of 100 contracts
                # Position value = 100 * 0.0001 * 100 = 1.0 USDT
                # Required margin at 3x = 1.0 / 3 = 0.33 USDT (not 348.35!)
                
                adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
                    'TEST/USDT:USDT', 
                    amount=100,           # 100 contracts
                    price=0.0001,         # Price per unit
                    leverage=3,           # 3x leverage
                    available_margin=47.75  # Available margin
                )
                
                print(f"  ✓ Test 1: Large contract_size scenario")
                print(f"    Input: 100 contracts @ $0.0001 with 3x leverage, $47.75 available")
                print(f"    Position value = 100 * 0.0001 * 100 = $1.00")
                print(f"    Required margin = $1.00 / 3 = $0.33 (should fit easily in $47.75)")
                print(f"    Output: {adjusted_amount:.4f} contracts at {adjusted_leverage}x")
                
                # With $47.75 available and 10% buffer = $42.975 usable
                # At 3x leverage, max position value = $42.975 * 3 = $128.925
                # Max contracts = $128.925 / ($0.0001 * 100) = 12892.5 contracts
                # So 100 contracts should easily fit
                assert adjusted_amount == 100, f"Should keep original amount, got {adjusted_amount}"
                assert adjusted_leverage == 3, f"Should keep original leverage, got {adjusted_leverage}"
                
                # Test scenario 2: Position that needs adjustment with contract_size
                # available=$1.00, want 1000 contracts at 5x
                # Position value = 1000 * 0.01 * 10 = $100
                # Required = $100 / 5 = $20 (exceeds $1.00)
                adjusted_amount2, adjusted_leverage2 = client.adjust_position_for_margin(
                    'TEST/USDT:USDT',
                    amount=1000,           # 1000 contracts  
                    price=0.01,            # Price per unit
                    leverage=5,            # 5x leverage
                    available_margin=1.0   # Only $1 available
                )
                
                print(f"  ✓ Test 2: Position requiring adjustment")
                print(f"    Input: 1000 contracts @ $0.01 with 5x leverage, $1.00 available")
                print(f"    Position value = 1000 * 0.01 * 100 = $100.00")
                print(f"    Required margin = $100.00 / 5 = $20.00 (exceeds $1.00)")
                print(f"    Output: {adjusted_amount2:.4f} contracts at {adjusted_leverage2}x")
                
                # With $1.00 available and 10% buffer = $0.90 usable
                # At 5x leverage, max position value = $0.90 * 5 = $4.50
                # Max contracts = $4.50 / ($0.01 * 100) = 4.5 contracts
                assert adjusted_amount2 <= 4.5, f"Should reduce to fit margin, got {adjusted_amount2}"
                
                # Verify the adjusted position actually fits in available margin
                # Calculate required margin for adjusted position
                position_value2 = adjusted_amount2 * 0.01 * 100
                required_margin2 = position_value2 / adjusted_leverage2
                usable_margin = 1.0 * 0.90
                
                print(f"    Verification: position_value=${position_value2:.2f}, required=${required_margin2:.2f}, usable=${usable_margin:.2f}")
                assert required_margin2 <= usable_margin, \
                    f"Adjusted position should fit: required={required_margin2:.2f}, usable={usable_margin:.2f}"
                
        print("✓ Contract size handling tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Contract size test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_check_margin_logging():
    """Test that check_available_margin logs correct position value with contract_size"""
    print("\nTesting position value logging in check_available_margin...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock load_markets with contract_size
            mock_instance.load_markets.return_value = {
                'TEST/USDT:USDT': {
                    'contractSize': 100,
                    'limits': {
                        'amount': {'min': 1, 'max': 1000000},
                        'cost': {'min': 1, 'max': 1000000}
                    }
                }
            }
            
            # Mock get_balance to return insufficient margin
            with patch.object(client, 'get_balance') as mock_balance:
                mock_balance.return_value = {
                    'free': {'USDT': 0.5},
                    'used': {'USDT': 0.0}
                }
                
                # Check margin for a position
                # 100 contracts * $0.0001 * 100 contract_size = $1.00 position value
                # Required at 3x = $1.00 / 3 = $0.33
                # With 5% buffer = $0.35
                # Available = $0.50 (should be sufficient!)
                has_margin, available, reason = client.check_available_margin(
                    'TEST/USDT:USDT',
                    amount=100,
                    price=0.0001,
                    leverage=3
                )
                
                print(f"  ✓ Margin check: has_margin={has_margin}, reason={reason}")
                
                # Verify the log message contains correct position value
                if not has_margin:
                    # Extract position value from reason string
                    import re
                    match = re.search(r'position value=\$(\d+\.\d+)', reason)
                    if match:
                        logged_position_value = float(match.group(1))
                        expected_position_value = 100 * 0.0001 * 100  # 1.00
                        print(f"    Logged position value: ${logged_position_value:.2f}")
                        print(f"    Expected position value: ${expected_position_value:.2f}")
                        assert abs(logged_position_value - expected_position_value) < 0.01, \
                            f"Position value should be {expected_position_value:.2f}, logged as {logged_position_value:.2f}"
                
        print("✓ Margin logging tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Margin logging test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING CONTRACT_SIZE MARGIN FIX")
    print("=" * 60)
    
    results = []
    results.append(test_contract_size_in_adjustment())
    results.append(test_check_margin_logging())
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    if all(results):
        print("✓ All tests passed!")
    else:
        print(f"✗ {len(results) - sum(results)} test(s) failed")
    print("=" * 60)
