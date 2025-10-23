"""
Shared fixtures for integration tests
"""
import pytest
from unittest.mock import Mock, MagicMock
import time


@pytest.fixture
def mock_api_response():
    """Mock API response data"""
    return {
        'ticker': {
            'symbol': 'BTC-USDT',
            'last': 50000.0,
            'bid': 49999.0,
            'ask': 50001.0,
            'volume': 1000.0,
            'timestamp': int(time.time() * 1000)
        },
        'order': {
            'id': 'test_order_123',
            'symbol': 'BTC-USDT',
            'type': 'market',
            'side': 'buy',
            'amount': 1.0,
            'price': 50000.0,
            'status': 'closed',
            'filled': 1.0,
            'cost': 50000.0,
            'timestamp': int(time.time() * 1000)
        },
        'balance': {
            'free': {'USDT': 10000.0},
            'used': {'USDT': 0.0},
            'total': {'USDT': 10000.0}
        },
        'position': {
            'symbol': 'BTC-USDT',
            'side': 'long',
            'contracts': 1.0,
            'contractSize': 0.001,
            'entryPrice': 50000.0,
            'markPrice': 50100.0,
            'liquidationPrice': 45000.0,
            'leverage': 10,
            'unrealizedPnl': 100.0
        }
    }


@pytest.fixture
def mock_kucoin_client():
    """Mock KuCoin client for integration tests"""
    mock_client = Mock()
    
    # Mock methods
    mock_client.get_ticker.return_value = {
        'symbol': 'BTC-USDT',
        'last': 50000.0,
        'bid': 49999.0,
        'ask': 50001.0
    }
    
    mock_client.get_balance.return_value = {
        'free': {'USDT': 10000.0},
        'used': {'USDT': 0.0},
        'total': {'USDT': 10000.0}
    }
    
    mock_client.create_market_order.return_value = {
        'id': 'test_order_123',
        'status': 'closed',
        'filled': 1.0
    }
    
    mock_client._round_to_precision.return_value = 1.23
    mock_client._round_to_step_size.return_value = 1.0
    
    return mock_client


@pytest.fixture
def mock_websocket_messages():
    """Pre-recorded WebSocket messages for replay"""
    return [
        {
            'type': 'message',
            'topic': '/contractMarket/ticker:BTC-USDT',
            'subject': 'ticker',
            'data': {
                'symbol': 'BTC-USDT',
                'price': '50000.00',
                'bestBidPrice': '49999.00',
                'bestAskPrice': '50001.00',
                'volume': '1000.0',
                'ts': int(time.time() * 1000000000)
            }
        },
        {
            'type': 'message',
            'topic': '/contractMarket/ticker:BTC-USDT',
            'subject': 'ticker',
            'data': {
                'symbol': 'BTC-USDT',
                'price': '50100.00',
                'bestBidPrice': '50099.00',
                'bestAskPrice': '50101.00',
                'volume': '1050.0',
                'ts': int(time.time() * 1000000000)
            }
        }
    ]
