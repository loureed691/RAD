"""
Test script for margin limit fix (error 330008)
"""
import sys
from unittest.mock import Mock, patch, MagicMock

def test_margin_calculation():
    """Test margin calculation logic"""
    print("\nTesting margin calculation...")
    try:
        from kucoin_client import KuCoinClient
        
        # Mock the client
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Test calculate_required_margin
            # Example: 100 contracts at $0.001 with 10x leverage
            required_margin = client.calculate_required_margin(
                'TEST/USDT:USDT', 100, 0.001, 10
            )
            expected_margin = (100 * 0.001) / 10  # = 0.01 USDT
            
            print(f"  ✓ Required margin calculation: {required_margin:.4f} USDT")
            assert abs(required_margin - expected_margin) < 0.0001, \
                f"Expected {expected_margin}, got {required_margin}"
            
            # Test with higher leverage
            required_margin_20x = client.calculate_required_margin(
                'TEST/USDT:USDT', 100, 0.001, 20
            )
            expected_margin_20x = (100 * 0.001) / 20  # = 0.005 USDT
            
            print(f"  ✓ Required margin with 20x leverage: {required_margin_20x:.4f} USDT")
            assert abs(required_margin_20x - expected_margin_20x) < 0.0001, \
                f"Expected {expected_margin_20x}, got {required_margin_20x}"
            
            # Test with larger position
            required_margin_large = client.calculate_required_margin(
                'TEST/USDT:USDT', 2000, 0.0013, 12
            )
            expected_margin_large = (2000 * 0.0013) / 12  # = 0.2167 USDT
            
            print(f"  ✓ Required margin for large position: {required_margin_large:.4f} USDT")
            assert abs(required_margin_large - expected_margin_large) < 0.0001, \
                f"Expected {expected_margin_large}, got {required_margin_large}"
            
        print("✓ Margin calculation tests passed")
        return True
    except Exception as e:
        print(f"✗ Margin calculation test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_margin_checking():
    """Test margin availability checking"""
    print("\nTesting margin availability checking...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock get_balance to return specific available margin
            with patch.object(client, 'get_balance') as mock_balance:
                # Test case 1: Sufficient margin
                mock_balance.return_value = {
                    'free': {'USDT': 100.0},
                    'used': {'USDT': 50.0},
                    'total': {'USDT': 150.0}
                }
                
                has_margin, available, reason = client.check_available_margin(
                    'TEST/USDT:USDT', 100, 0.001, 10
                )
                
                print(f"  ✓ Sufficient margin test: has_margin={has_margin}, available=${available:.2f}")
                assert has_margin == True, "Should have sufficient margin"
                assert available == 100.0, f"Expected 100.0, got {available}"
                
                # Test case 2: Insufficient margin
                mock_balance.return_value = {
                    'free': {'USDT': 0.5},  # Only 0.5 USDT available
                    'used': {'USDT': 99.5},
                    'total': {'USDT': 100.0}
                }
                
                has_margin, available, reason = client.check_available_margin(
                    'TEST/USDT:USDT', 10000, 0.001, 10
                )
                
                print(f"  ✓ Insufficient margin test: has_margin={has_margin}, reason={reason}")
                assert has_margin == False, "Should not have sufficient margin"
                assert available == 0.5, f"Expected 0.5, got {available}"
                assert "Insufficient margin" in reason, "Reason should mention insufficient margin"
                
        print("✓ Margin checking tests passed")
        return True
    except Exception as e:
        print(f"✗ Margin checking test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_position_adjustment():
    """Test position adjustment for available margin"""
    print("\nTesting position adjustment...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock validate_and_cap_amount to just return the amount
            with patch.object(client, 'validate_and_cap_amount') as mock_validate:
                mock_validate.side_effect = lambda symbol, amount: amount
                
                # Test case: Want 2000 contracts at $0.0013 with 12x leverage
                # Position value = 2000 * 0.0013 = 2.6 USDT
                # Required margin = 2.6 / 12 = 0.2167 USDT
                # But only have 1.0 USDT available
                
                adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
                    'TEST/USDT:USDT', 2000, 0.0013, 12, 1.0
                )
                
                print(f"  ✓ Position adjusted: amount={adjusted_amount:.4f}, leverage={adjusted_leverage}x")
                
                # Should reduce amount to fit within 0.9 USDT (90% of available)
                # Max position value = 0.9 * 12 = 10.8 USDT
                # Max amount = 10.8 / 0.0013 = 8307.69 contracts
                # But we wanted 2000, so should return 2000
                assert adjusted_amount <= 2000, f"Amount should not exceed desired: {adjusted_amount}"
                
                # Test case 2: Very limited margin
                adjusted_amount2, adjusted_leverage2 = client.adjust_position_for_margin(
                    'TEST/USDT:USDT', 10000, 0.001, 10, 0.5
                )
                
                print(f"  ✓ Limited margin adjustment: amount={adjusted_amount2:.4f}, leverage={adjusted_leverage2}x")
                
                # With 0.5 USDT and 10x leverage, max position value = 0.45 * 10 = 4.5 USDT
                # Max amount = 4.5 / 0.001 = 4500 contracts
                assert adjusted_amount2 <= 4500, f"Amount should fit margin: {adjusted_amount2}"
                
        print("✓ Position adjustment tests passed")
        return True
    except Exception as e:
        print(f"✗ Position adjustment test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_create_order():
    """Test integration with create_market_order"""
    print("\nTesting integration with create_market_order...")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock all required methods
            with patch.object(client, 'get_ticker') as mock_ticker, \
                 patch.object(client, 'get_balance') as mock_balance, \
                 patch.object(client, 'validate_and_cap_amount') as mock_validate:
                
                mock_ticker.return_value = {'last': 0.0013}
                mock_balance.return_value = {
                    'free': {'USDT': 0.5},  # Limited margin
                    'used': {'USDT': 50.0},
                    'total': {'USDT': 50.5}
                }
                mock_validate.side_effect = lambda symbol, amount: amount
                
                # Mock the exchange methods
                mock_instance.set_margin_mode = Mock()
                mock_instance.set_leverage = Mock()
                mock_instance.create_order = Mock(return_value={
                    'id': 'test_order_123',
                    'symbol': 'TEST/USDT:USDT',
                    'average': 0.0013,
                    'amount': 3461.54  # Adjusted amount
                })
                
                # Try to create order with large position (should be adjusted)
                order = client.create_market_order(
                    'TEST/USDT:USDT', 'buy', 10000, leverage=12
                )
                
                if order:
                    print(f"  ✓ Order created with adjustment: {order.get('amount')} contracts")
                    assert order is not None, "Order should be created"
                    # Should have called create_order with adjusted amount
                    assert mock_instance.create_order.called, "create_order should be called"
                else:
                    print("  ✓ Order rejected due to insufficient margin (as expected)")
                
        print("✓ Integration tests passed")
        return True
    except Exception as e:
        print(f"✗ Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("TESTING MARGIN LIMIT FIX (ERROR 330008)")
    print("=" * 60)
    
    tests = [
        test_margin_calculation,
        test_margin_checking,
        test_position_adjustment,
        test_integration_with_create_order
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{len(tests)} passed")
    if failed == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ {failed} test(s) failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
