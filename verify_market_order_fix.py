"""
Quick verification that the market order validation fix works correctly.
This verifies the specific bug fix made to kucoin_client.py.
"""
import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("\n" + "="*80)
    print("🔍 VERIFYING MARKET ORDER VALIDATION FIX")
    print("="*80)
    print("\nThis test verifies the specific bug fix:")
    print("  - Before: Market orders were rejected with 'Order cost $0.00 below minimum'")
    print("  - After: Market orders skip cost validation (price=0) and work correctly")
    print("="*80)
    
    try:
        from kucoin_client import KuCoinClient
        
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            
            # Setup mock environment
            mock_exchange.set_position_mode = Mock()
            mock_exchange.set_margin_mode = Mock()
            mock_exchange.set_leverage = Mock()
            
            markets = {
                'BTC-USDT': {
                    'active': True,
                    'limits': {
                        'amount': {'min': 0.001, 'max': 10000},
                        'cost': {'min': 10, 'max': 1000000}  # Min cost is $10
                    },
                    'contractSize': 0.001,
                    'precision': {'amount': 3, 'price': 1}
                }
            }
            mock_exchange.load_markets = Mock(return_value=markets)
            mock_exchange.markets = markets
            
            mock_exchange.fetch_ticker = Mock(return_value={
                'last': 50000.0,
                'bid': 49990.0,
                'ask': 50010.0
            })
            
            mock_exchange.fetch_balance = Mock(return_value={
                'free': {'USDT': 10000.0},
                'used': {'USDT': 0.0},
                'total': {'USDT': 10000.0}
            })
            
            mock_exchange.create_order = Mock(return_value={
                'id': 'test_order_123',
                'status': 'closed',
                'average': 50000.0,
                'amount': 0.1
            })
            
            mock_exchange.fetch_order = Mock(return_value={
                'id': 'test_order_123',
                'status': 'closed',
                'average': 50000.0,
                'filled': 0.1,
                'cost': 5000.0
            })
            
            # Create client
            client = KuCoinClient('test_key', 'test_secret', 'test_pass')
            
            print("\n📝 TEST 1: Validate order with price=0 (market order)")
            print("  - Simulates the validation that happens before fetching market price")
            
            is_valid, reason = client.validate_order_locally('BTC-USDT', 0.1, 0)
            
            if is_valid:
                print(f"  ✅ PASSED: Market order validation accepts price=0")
                print(f"     Reason: {reason}")
            else:
                print(f"  ❌ FAILED: Market order validation rejected with: {reason}")
                print(f"     This means the fix is NOT working!")
                return False
            
            print("\n📝 TEST 2: Create actual market order")
            print("  - This is what the bot does when executing a trade")
            
            order = client.create_market_order('BTC-USDT', 'buy', 0.1, leverage=10)
            
            if order is not None:
                print(f"  ✅ PASSED: Market order created successfully")
                print(f"     Order ID: {order.get('id')}")
                print(f"     Status: {order.get('status')}")
                print(f"     Price: ${order.get('average', 0):.2f}")
            else:
                print(f"  ❌ FAILED: Market order was rejected")
                print(f"     This means the fix is NOT working!")
                return False
            
            print("\n📝 TEST 3: Validate limit order still checks cost properly")
            print("  - Ensure we didn't break limit order validation")
            
            # Valid limit order (0.001 * 50000 = $50 > $10 minimum)
            is_valid, reason = client.validate_order_locally('BTC-USDT', 0.001, 50000)
            if is_valid:
                print(f"  ✅ PASSED: Valid limit order accepted")
            else:
                print(f"  ❌ FAILED: Valid limit order rejected: {reason}")
                return False
            
            # Invalid limit order (0.001 * 1 = $1 < $10 minimum)
            is_valid, reason = client.validate_order_locally('BTC-USDT', 0.001, 1.0)
            if not is_valid and "below minimum" in reason:
                print(f"  ✅ PASSED: Invalid limit order correctly rejected")
                print(f"     Reason: {reason}")
            else:
                print(f"  ❌ FAILED: Invalid limit order should have been rejected")
                return False
            
            print("\n" + "="*80)
            print("✅ ALL TESTS PASSED - MARKET ORDER FIX IS WORKING!")
            print("="*80)
            print("\n✨ Summary:")
            print("  - Market orders with price=0 are correctly accepted")
            print("  - Market orders can be created successfully")
            print("  - Limit orders still validate cost properly")
            print("\n🎯 The bot is ready to execute market orders in real trading!")
            print("="*80)
            
            return True
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
