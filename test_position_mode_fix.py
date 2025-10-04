#!/usr/bin/env python3
"""
Unit tests for position mode and quantity limit fixes
"""
import sys
from unittest.mock import Mock, MagicMock, patch

def test_validate_and_cap_amount():
    """Test the validate_and_cap_amount method"""
    print("\nTesting validate_and_cap_amount...")
    
    try:
        from kucoin_client import KuCoinClient
        
        # Create a mock client
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            # Create client
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Test Case 1: Normal amount within limits
            print("  Test 1: Normal amount (5000)...")
            client.get_market_limits = Mock(return_value={
                'amount': {'min': 1, 'max': 10000},
                'cost': {'min': 1, 'max': None}
            })
            result = client.validate_and_cap_amount("BTC/USDT:USDT", 5000)
            assert result == 5000, f"Expected 5000, got {result}"
            print(f"    ✓ Returned {result} (unchanged)")
            
            # Test Case 2: Amount exceeds maximum
            print("  Test 2: Amount exceeds max (15000 > 10000)...")
            result = client.validate_and_cap_amount("BTC/USDT:USDT", 15000)
            assert result == 10000, f"Expected 10000, got {result}"
            print(f"    ✓ Capped to {result}")
            
            # Test Case 3: Amount below minimum
            print("  Test 3: Amount below min (0.5 < 1)...")
            result = client.validate_and_cap_amount("BTC/USDT:USDT", 0.5)
            assert result == 1, f"Expected 1, got {result}"
            print(f"    ✓ Adjusted to {result}")
            
            # Test Case 4: No limits available (default to 10,000 cap)
            print("  Test 4: No limits, amount exceeds default (20000)...")
            client.get_market_limits = Mock(return_value=None)
            result = client.validate_and_cap_amount("BTC/USDT:USDT", 20000)
            assert result == 10000, f"Expected 10000, got {result}"
            print(f"    ✓ Capped to default {result}")
            
            # Test Case 5: No limits available, normal amount
            print("  Test 5: No limits, normal amount (5000)...")
            result = client.validate_and_cap_amount("BTC/USDT:USDT", 5000)
            assert result == 5000, f"Expected 5000, got {result}"
            print(f"    ✓ Returned {result} (unchanged)")
            
            print("✓ All validate_and_cap_amount tests passed")
            return True
            
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_market_limits():
    """Test the get_market_limits method"""
    print("\nTesting get_market_limits...")
    
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            # Create client
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Mock the exchange load_markets
            mock_instance.load_markets.return_value = {
                'BTC/USDT:USDT': {
                    'limits': {
                        'amount': {'min': 1, 'max': 10000},
                        'cost': {'min': 10, 'max': 100000}
                    }
                }
            }
            
            print("  Test 1: Get limits for valid symbol...")
            limits = client.get_market_limits('BTC/USDT:USDT')
            assert limits is not None, "Expected limits dict"
            assert limits['amount']['min'] == 1, "Min amount should be 1"
            assert limits['amount']['max'] == 10000, "Max amount should be 10000"
            print(f"    ✓ Got limits: min={limits['amount']['min']}, max={limits['amount']['max']}")
            
            print("  Test 2: Get limits for invalid symbol...")
            limits = client.get_market_limits('INVALID/SYMBOL:USDT')
            assert limits is None, "Expected None for invalid symbol"
            print(f"    ✓ Returned None for invalid symbol")
            
            print("✓ All get_market_limits tests passed")
            return True
            
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_mode_initialization():
    """Test that position mode is set on initialization"""
    print("\nTesting position mode initialization...")
    
    try:
        from kucoin_client import KuCoinClient
        
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange:
            mock_instance = MagicMock()
            mock_exchange.return_value = mock_instance
            
            # Create client - this should call set_position_mode
            print("  Test 1: Position mode set on init...")
            client = KuCoinClient("test_key", "test_secret", "test_pass")
            
            # Verify set_position_mode was called
            assert mock_instance.set_position_mode.called, "set_position_mode should be called"
            call_args = mock_instance.set_position_mode.call_args
            # call_args is a tuple of (args, kwargs) or just kwargs
            if call_args.args:
                assert call_args.args[0] == False, "hedged should be False (ONE_WAY mode)"
            else:
                assert call_args.kwargs.get('hedged') == False or call_args[0] == (False,), "hedged should be False"
            print(f"    ✓ set_position_mode(hedged=False) was called")
            
            print("  Test 2: Graceful handling of set_position_mode failure...")
            # Mock set_position_mode to raise an exception
            mock_instance2 = MagicMock()
            mock_instance2.set_position_mode.side_effect = Exception("Position mode not supported")
            mock_exchange.return_value = mock_instance2
            
            # Should not raise exception, but should log warning
            client2 = KuCoinClient("test_key", "test_secret", "test_pass")
            print(f"    ✓ Client initialized despite set_position_mode failure")
            
            print("✓ All position mode initialization tests passed")
            return True
            
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all unit tests"""
    print("="*70)
    print("Unit Tests for Position Mode & Quantity Limit Fixes")
    print("="*70)
    
    results = {
        'validate_and_cap_amount': test_validate_and_cap_amount(),
        'get_market_limits': test_get_market_limits(),
        'position_mode_initialization': test_position_mode_initialization(),
    }
    
    print("\n" + "="*70)
    print("Unit Test Results")
    print("="*70)
    
    for test, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test:.<50} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("✓✓✓ All unit tests passed! ✓✓✓")
    else:
        print("✗✗✗ Some unit tests failed. ✗✗✗")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
