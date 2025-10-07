"""
Comprehensive test suite for enhanced trading methods in the KuCoin client and position manager.

This module verifies advanced trading functionalities including:
- Limit order creation with post-only and reduce-only flags
- Stop-limit order creation
- Order status checking and validation
- Order book depth fetching
- Price slippage validation
- Market order execution with depth checks
- Position scaling in and out
- Position target modification
- Closing positions with limit orders

The purpose of these tests is to ensure robust and correct behavior of advanced trading features,
helping to prevent regressions and maintain reliability in automated trading systems.
"""
import sys
import os
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kucoin_client import KuCoinClient
from position_manager import Position, PositionManager

def test_limit_order_with_post_only():
    """Test limit order creation with post_only flag"""
    print("\nTesting limit order with post_only...")
    try:
        # Mock the KuCoin client
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            mock_exchange.set_margin_mode = Mock()
            mock_exchange.set_leverage = Mock()
            mock_exchange.load_markets = Mock(return_value={
                'BTC-USDT': {
                    'limits': {
                        'amount': {'min': 1, 'max': 10000},
                        'cost': {'min': 10, 'max': 1000000}
                    }
                }
            })
            mock_exchange.create_order = Mock(return_value={
                'id': '12345',
                'status': 'open',
                'price': 50000,
                'amount': 1.0
            })
            
            client = KuCoinClient('key', 'secret', 'pass')
            
            # Test post_only order
            order = client.create_limit_order(
                'BTC-USDT', 'buy', 1.0, 50000, leverage=10, post_only=True
            )
            
            assert order is not None, "Order should be created"
            assert mock_exchange.create_order.called, "create_order should be called"
            
            # Check that post_only was passed in params
            call_args = mock_exchange.create_order.call_args
            params = call_args[1]['params']
            assert params.get('postOnly') == True, "postOnly should be in params"
            
            print("  ✓ Limit order with post_only created successfully")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def test_limit_order_with_reduce_only():
    """Test limit order creation with reduce_only flag"""
    print("\nTesting limit order with reduce_only...")
    try:
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            mock_exchange.set_margin_mode = Mock()
            mock_exchange.set_leverage = Mock()
            mock_exchange.load_markets = Mock(return_value={
                'BTC-USDT': {
                    'limits': {
                        'amount': {'min': 1, 'max': 10000},
                        'cost': {'min': 10, 'max': 1000000}
                    }
                }
            })
            mock_exchange.create_order = Mock(return_value={
                'id': '12345',
                'status': 'open',
                'price': 50000,
                'amount': 1.0
            })
            
            client = KuCoinClient('key', 'secret', 'pass')
            
            # Test reduce_only order
            order = client.create_limit_order(
                'BTC-USDT', 'sell', 1.0, 51000, leverage=10, reduce_only=True
            )
            
            assert order is not None, "Order should be created"
            
            # Check that reduce_only was passed in params
            call_args = mock_exchange.create_order.call_args
            params = call_args[1]['params']
            assert params.get('reduceOnly') == True, "reduceOnly should be in params"
            
            print("  ✓ Limit order with reduce_only created successfully")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def test_stop_limit_order_creation():
    """Test stop-limit order creation"""
    print("\nTesting stop-limit order creation...")
    try:
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            mock_exchange.set_margin_mode = Mock()
            mock_exchange.set_leverage = Mock()
            mock_exchange.load_markets = Mock(return_value={
                'BTC-USDT': {
                    'limits': {
                        'amount': {'min': 1, 'max': 10000},
                        'cost': {'min': 10, 'max': 1000000}
                    }
                }
            })
            mock_exchange.create_order = Mock(return_value={
                'id': '12345',
                'status': 'open',
                'price': 48000,
                'amount': 1.0
            })
            
            client = KuCoinClient('key', 'secret', 'pass')
            
            # Test stop-limit order
            order = client.create_stop_limit_order(
                'BTC-USDT', 'sell', 1.0, stop_price=49000, 
                limit_price=48500, leverage=10, reduce_only=True
            )
            
            assert order is not None, "Stop-limit order should be created"
            
            # Check that stopPrice and reduceOnly were passed
            call_args = mock_exchange.create_order.call_args
            params = call_args[1]['params']
            assert params.get('stopPrice') == 49000, "stopPrice should be in params"
            assert params.get('reduceOnly') == True, "reduceOnly should be in params"
            
            print("  ✓ Stop-limit order created successfully")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def test_order_status_checking():
    """Test order status checking"""
    print("\nTesting order status checking...")
    try:
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            mock_exchange.fetch_order = Mock(return_value={
                'id': '12345',
                'status': 'closed',
                'filled': 1.0,
                'remaining': 0,
                'amount': 1.0,
                'price': 50000,
                'average': 50050,
                'cost': 50050,
                'timestamp': 1234567890
            })
            
            client = KuCoinClient('key', 'secret', 'pass')
            
            status = client.get_order_status('12345', 'BTC-USDT')
            
            assert status is not None, "Status should be returned"
            assert status['status'] == 'closed', "Status should be closed"
            assert status['filled'] == 1.0, "Filled amount should match"
            assert status['remaining'] == 0, "Remaining should be 0"
            
            print("  ✓ Order status checked successfully")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def test_order_book_fetching():
    """Test order book depth fetching"""
    print("\nTesting order book fetching...")
    try:
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            mock_exchange.fetch_order_book = Mock(return_value={
                'bids': [[50000, 10], [49990, 20], [49980, 30]],
                'asks': [[50010, 10], [50020, 20], [50030, 30]],
                'timestamp': 1234567890
            })
            
            client = KuCoinClient('key', 'secret', 'pass')
            
            order_book = client.get_order_book('BTC-USDT', limit=20)
            
            assert order_book is not None, "Order book should be returned"
            assert len(order_book['bids']) == 3, "Should have 3 bid levels"
            assert len(order_book['asks']) == 3, "Should have 3 ask levels"
            assert order_book['bids'][0][0] == 50000, "Best bid should be 50000"
            
            print("  ✓ Order book fetched successfully")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def test_slippage_validation():
    """Test price slippage validation"""
    print("\nTesting slippage validation...")
    try:
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            mock_exchange.fetch_ticker = Mock(return_value={
                'last': 50500,
                'bid': 50490,
                'ask': 50510
            })
            
            client = KuCoinClient('key', 'secret', 'pass')
            
            # Test buy with acceptable slippage
            is_valid, price = client.validate_price_with_slippage(
                'BTC-USDT', 'buy', 50000, max_slippage=0.01
            )
            
            assert is_valid == True, "Slippage should be acceptable"
            assert price == 50500, "Current price should be returned"
            
            # Test buy with excessive slippage
            is_valid, price = client.validate_price_with_slippage(
                'BTC-USDT', 'buy', 50000, max_slippage=0.005
            )
            
            assert is_valid == False, "Slippage should exceed limit"
            
            print("  ✓ Slippage validation working correctly")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def test_market_order_with_depth_check():
    """Test market order with order book depth validation"""
    print("\nTesting market order with depth check...")
    try:
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            mock_exchange.set_margin_mode = Mock()
            mock_exchange.set_leverage = Mock()
            mock_exchange.load_markets = Mock(return_value={
                'BTC-USDT': {
                    'limits': {
                        'amount': {'min': 1, 'max': 10000},
                        'cost': {'min': 10, 'max': 1000000}
                    },
                    'contractSize': 1
                }
            })
            mock_exchange.fetch_ticker = Mock(return_value={
                'last': 50000
            })
            mock_exchange.fetch_order_book = Mock(return_value={
                'bids': [[50000, 200], [49990, 150]],
                'asks': [[50010, 200], [50020, 150]],
                'timestamp': 1234567890
            })
            mock_exchange.fetch_balance = Mock(return_value={
                'free': {'USDT': 1000000},  # Sufficient margin for large order
                'used': {'USDT': 0},
                'total': {'USDT': 1000000}
            })
            mock_exchange.fetch_order = Mock(return_value=None)  # Prevent Mock from corrupting order data
            mock_exchange.create_order = Mock(return_value={
                'id': '12345',
                'status': 'closed',
                'average': 50000,
                'amount': 150.0
            })
            
            client = KuCoinClient('key', 'secret', 'pass')
            
            # Test large order - should check depth
            order = client.create_market_order(
                'BTC-USDT', 'buy', 150.0, leverage=10, validate_depth=True
            )
            
            assert order is not None, "Order should be created"
            assert mock_exchange.fetch_order_book.called, "Order book should be checked"
            
            print("  ✓ Market order with depth check created successfully")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def test_position_scaling_in():
    """Test scaling into an existing position"""
    print("\nTesting position scaling in...")
    try:
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            mock_exchange.set_margin_mode = Mock()
            mock_exchange.set_leverage = Mock()
            mock_exchange.load_markets = Mock(return_value={
                'BTC-USDT': {
                    'limits': {
                        'amount': {'min': 1, 'max': 10000},
                        'cost': {'min': 10, 'max': 1000000}
                    },
                    'contractSize': 1
                }
            })
            mock_exchange.fetch_balance = Mock(return_value={
                'free': {'USDT': 100000},  # Sufficient margin
                'used': {'USDT': 0},
                'total': {'USDT': 100000}
            })
            mock_exchange.fetch_order = Mock(return_value=None)  # Prevent Mock from corrupting order data
            mock_exchange.create_order = Mock(return_value={
                'id': '12345',
                'status': 'closed',
                'average': 51000,
                'amount': 1.0
            })
            mock_exchange.fetch_ticker = Mock(return_value={'last': 51000})
            
            client = KuCoinClient('key', 'secret', 'pass')
            manager = PositionManager(client)
            
            # Create initial position
            position = Position(
                symbol='BTC-USDT',
                side='long',
                entry_price=50000,
                amount=1.0,
                leverage=10,
                stop_loss=47500,
                take_profit=55000
            )
            manager.positions['BTC-USDT'] = position
            
            # Scale in
            success = manager.scale_in_position('BTC-USDT', 1.0, 51000)
            
            assert success == True, "Scale in should succeed"
            assert manager.positions['BTC-USDT'].amount == 2.0, "Amount should double"
            # Average entry should be (50000 + 51000) / 2 = 50500
            assert manager.positions['BTC-USDT'].entry_price == 50500, "Entry price should be averaged"
            
            print("  ✓ Position scaled in successfully")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def test_position_scaling_out():
    """Test scaling out of an existing position"""
    print("\nTesting position scaling out...")
    try:
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            mock_exchange.set_margin_mode = Mock()
            mock_exchange.set_leverage = Mock()
            mock_exchange.load_markets = Mock(return_value={
                'BTC-USDT': {
                    'limits': {
                        'amount': {'min': 1, 'max': 10000},
                        'cost': {'min': 10, 'max': 1000000}
                    },
                    'contractSize': 1
                }
            })
            mock_exchange.fetch_balance = Mock(return_value={
                'free': {'USDT': 100000},  # Sufficient margin
                'used': {'USDT': 0},
                'total': {'USDT': 100000}
            })
            mock_exchange.fetch_order = Mock(return_value=None)  # Prevent Mock from corrupting order data
            mock_exchange.create_order = Mock(return_value={
                'id': '12345',
                'status': 'closed',
                'average': 52000,
                'amount': 1.0
            })
            mock_exchange.fetch_ticker = Mock(return_value={'last': 52000})
            
            client = KuCoinClient('key', 'secret', 'pass')
            manager = PositionManager(client)
            
            # Create position
            position = Position(
                symbol='BTC-USDT',
                side='long',
                entry_price=50000,
                amount=2.0,
                leverage=10,
                stop_loss=47500,
                take_profit=55000
            )
            manager.positions['BTC-USDT'] = position
            
            # Scale out half
            pnl = manager.scale_out_position('BTC-USDT', 1.0, 'partial_take_profit')
            
            assert pnl is not None, "Scale out should succeed"
            assert pnl > 0, "Should be profitable"
            assert manager.positions['BTC-USDT'].amount == 1.0, "Amount should be halved"
            
            print("  ✓ Position scaled out successfully")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def test_position_target_modification():
    """Test modifying position stop loss and take profit"""
    print("\nTesting position target modification...")
    try:
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            
            client = KuCoinClient('key', 'secret', 'pass')
            manager = PositionManager(client)
            
            # Create position
            position = Position(
                symbol='BTC-USDT',
                side='long',
                entry_price=50000,
                amount=1.0,
                leverage=10,
                stop_loss=47500,
                take_profit=55000
            )
            manager.positions['BTC-USDT'] = position
            
            # Modify targets
            success = manager.modify_position_targets(
                'BTC-USDT',
                new_stop_loss=48000,
                new_take_profit=56000
            )
            
            assert success == True, "Modification should succeed"
            assert manager.positions['BTC-USDT'].stop_loss == 48000, "Stop loss should be updated"
            assert manager.positions['BTC-USDT'].take_profit == 56000, "Take profit should be updated"
            
            print("  ✓ Position targets modified successfully")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def test_close_position_with_limit_order():
    """Test closing position with limit order"""
    print("\nTesting close position with limit order...")
    try:
        with patch('ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = Mock()
            mock_exchange_class.return_value = mock_exchange
            mock_exchange.set_position_mode = Mock()
            mock_exchange.set_margin_mode = Mock()
            mock_exchange.set_leverage = Mock()
            mock_exchange.load_markets = Mock(return_value={})
            mock_exchange.create_order = Mock(return_value={
                'id': '12345',
                'status': 'open',
                'price': 51900,
                'amount': 1.0
            })
            mock_exchange.fetch_ticker = Mock(return_value={'last': 52000})
            mock_exchange.fetch_positions = Mock(return_value=[
                {
                    'symbol': 'BTC-USDT',
                    'contracts': 1.0,
                    'side': 'long'
                }
            ])
            
            client = KuCoinClient('key', 'secret', 'pass')
            
            # Close with limit order
            success = client.close_position('BTC-USDT', use_limit=True, slippage_tolerance=0.002)
            
            assert success == True, "Close should succeed"
            
            # Verify limit order was created
            call_args = mock_exchange.create_order.call_args
            assert call_args[1]['type'] == 'limit', "Should be limit order"
            params = call_args[1]['params']
            assert params.get('reduceOnly') == True, "Should have reduceOnly flag"
            
            print("  ✓ Position closed with limit order successfully")
            return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        return False

def main():
    """Run all enhanced trading methods tests"""
    print("=" * 60)
    print("Running Enhanced Trading Methods Tests")
    print("=" * 60)
    
    tests = [
        test_limit_order_with_post_only,
        test_limit_order_with_reduce_only,
        test_stop_limit_order_creation,
        test_order_status_checking,
        test_order_book_fetching,
        test_slippage_validation,
        test_market_order_with_depth_check,
        test_position_scaling_in,
        test_position_scaling_out,
        test_position_target_modification,
        test_close_position_with_limit_order,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All enhanced trading methods tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
