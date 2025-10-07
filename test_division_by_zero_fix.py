#!/usr/bin/env python3
"""
Test division by zero fix in adjust_position_for_margin
This test validates the fix for the error:
"Error adjusting position for margin: float division by zero"
"""

from unittest.mock import MagicMock, patch

def test_zero_available_margin():
    """Test handling when available_margin is 0"""
    print("\nTest 1: Zero available margin")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock load_markets
            mock_instance.load_markets.return_value = {
                'BAN/USDT:USDT': {'contractSize': 1}
            }
            
            # Mock validate_and_cap_amount
            with patch.object(client, 'validate_and_cap_amount', return_value=44.0):
                # Test with zero available margin - this should not crash
                adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
                    symbol='BAN/USDT:USDT',
                    amount=44.0,
                    price=59.67,
                    leverage=7,
                    available_margin=0.0  # This is the problematic case
                )
                
                # Should return 0.0 amount and minimum leverage instead of crashing
                assert adjusted_amount == 0.0, f"Expected 0.0, got {adjusted_amount}"
                assert adjusted_leverage == 1, f"Expected 1, got {adjusted_leverage}"
                print(f"  ✓ Handled zero margin: returned ({adjusted_amount}, {adjusted_leverage})")
                
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_negative_available_margin():
    """Test handling when available_margin is negative"""
    print("\nTest 2: Negative available margin")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock load_markets
            mock_instance.load_markets.return_value = {
                'BAN/USDT:USDT': {'contractSize': 1}
            }
            
            # Test with negative available margin
            adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
                symbol='BAN/USDT:USDT',
                amount=44.0,
                price=59.67,
                leverage=7,
                available_margin=-10.0  # Negative margin
            )
            
            # Should return 0.0 amount and minimum leverage
            assert adjusted_amount == 0.0, f"Expected 0.0, got {adjusted_amount}"
            assert adjusted_leverage == 1, f"Expected 1, got {adjusted_leverage}"
            print(f"  ✓ Handled negative margin: returned ({adjusted_amount}, {adjusted_leverage})")
            
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zero_price():
    """Test handling when price is 0"""
    print("\nTest 3: Zero price")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock load_markets
            mock_instance.load_markets.return_value = {
                'BAN/USDT:USDT': {'contractSize': 1}
            }
            
            # Test with zero price - this should not crash
            adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
                symbol='BAN/USDT:USDT',
                amount=44.0,
                price=0.0,  # Zero price
                leverage=7,
                available_margin=10.0
            )
            
            # Should return 0.0 amount and minimum leverage instead of crashing
            assert adjusted_amount == 0.0, f"Expected 0.0, got {adjusted_amount}"
            assert adjusted_leverage == 1, f"Expected 1, got {adjusted_leverage}"
            print(f"  ✓ Handled zero price: returned ({adjusted_amount}, {adjusted_leverage})")
            
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_very_small_margin():
    """Test handling when available_margin is very small"""
    print("\nTest 4: Very small available margin")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock load_markets
            mock_instance.load_markets.return_value = {
                'BAN/USDT:USDT': {'contractSize': 1}
            }
            
            # Mock validate_and_cap_amount to return a small value
            with patch.object(client, 'validate_and_cap_amount', return_value=0.1):
                with patch.object(client, 'calculate_required_margin', return_value=0.05):
                    # Test with very small available margin (but not zero)
                    adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
                        symbol='BAN/USDT:USDT',
                        amount=44.0,
                        price=1.0,
                        leverage=7,
                        available_margin=0.001  # Very small but not zero
                    )
                    
                    # Should return some adjusted values, not crash
                    print(f"  ✓ Handled small margin: returned ({adjusted_amount:.4f}, {adjusted_leverage})")
                    
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_normal_case():
    """Test that normal cases still work correctly"""
    print("\nTest 5: Normal case (sufficient margin)")
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock load_markets
            mock_instance.load_markets.return_value = {
                'BAN/USDT:USDT': {'contractSize': 1}
            }
            
            # Mock validate_and_cap_amount
            with patch.object(client, 'validate_and_cap_amount', side_effect=lambda s, a: a):
                with patch.object(client, 'calculate_required_margin', return_value=5.0):
                    # Test with normal values
                    adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
                        symbol='BAN/USDT:USDT',
                        amount=100.0,
                        price=1.0,
                        leverage=10,
                        available_margin=50.0
                    )
                    
                    # Should work normally
                    assert adjusted_amount > 0, f"Expected positive amount, got {adjusted_amount}"
                    assert adjusted_leverage >= 1, f"Expected leverage >= 1, got {adjusted_leverage}"
                    print(f"  ✓ Normal case works: returned ({adjusted_amount:.4f}, {adjusted_leverage})")
                    
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING DIVISION BY ZERO FIX")
    print("=" * 60)
    
    tests = [
        ("Zero available margin", test_zero_available_margin),
        ("Negative available margin", test_negative_available_margin),
        ("Zero price", test_zero_price),
        ("Very small margin", test_very_small_margin),
        ("Normal case", test_normal_case),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    print("=" * 60)
    
    import sys
    sys.exit(0 if passed == total else 1)
