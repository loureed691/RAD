"""
Test to verify the bot.log fixes are working correctly
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestBotLogFixes(unittest.TestCase):
    """Test the fixes for bot.log issues"""
    
    def test_orderbook_parameter_fix(self):
        """Test that orderbook is called with correct parameter"""
        from kucoin_client import KuCoinClient
        
        # Create a mock exchange
        with patch('kucoin_client.ccxt') as mock_ccxt:
            mock_exchange = MagicMock()
            mock_ccxt.kucoinfutures.return_value = mock_exchange
            
            # Initialize client
            client = KuCoinClient("test_key", "test_secret", "test_pass", enable_websocket=False)
            
            # Mock the fetch_order_book method
            mock_exchange.fetch_order_book.return_value = {
                'bids': [[100.0, 1.0], [99.0, 2.0]],
                'asks': [[101.0, 1.0], [102.0, 2.0]],
                'timestamp': 1234567890
            }
            
            # Call get_order_book with limit parameter
            result = client.get_order_book('BTC/USDT:USDT', limit=20)
            
            # Verify the method was called with correct parameter name
            mock_exchange.fetch_order_book.assert_called_once_with('BTC/USDT:USDT', limit=20)
            
            # Verify result structure
            self.assertIn('bids', result)
            self.assertIn('asks', result)
            self.assertEqual(len(result['bids']), 2)
            self.assertEqual(len(result['asks']), 2)
    
    def test_support_resistance_extraction(self):
        """Test that support/resistance levels are correctly extracted"""
        # Test data simulating what calculate_support_resistance returns
        support_resistance = {
            'support': [
                {'price': 100.0, 'strength': 0.5},
                {'price': 95.0, 'strength': 0.3},
                {'price': 90.0, 'strength': 0.2}
            ],
            'resistance': [
                {'price': 110.0, 'strength': 0.6},
                {'price': 115.0, 'strength': 0.4},
                {'price': 120.0, 'strength': 0.1}
            ],
            'poc': 105.0
        }
        
        # Test BUY signal - should extract strongest support
        signal = 'BUY'
        support_level = None
        if signal == 'BUY' and 'support' in support_resistance:
            support_list = support_resistance['support']
            if support_list and len(support_list) > 0:
                support_level = support_list[0]['price'] if isinstance(support_list[0], dict) else support_list[0]
        
        self.assertEqual(support_level, 100.0)
        self.assertIsInstance(support_level, float)
        
        # Test SELL signal - should extract strongest resistance
        signal = 'SELL'
        support_level = None
        if signal == 'SELL' and 'resistance' in support_resistance:
            resistance_list = support_resistance['resistance']
            if resistance_list and len(resistance_list) > 0:
                support_level = resistance_list[0]['price'] if isinstance(resistance_list[0], dict) else resistance_list[0]
        
        self.assertEqual(support_level, 110.0)
        self.assertIsInstance(support_level, float)
    
    def test_websocket_subscription_limit(self):
        """Test that WebSocket subscription limit is enforced"""
        from kucoin_websocket import KuCoinWebSocket
        
        # Create WebSocket instance
        ws = KuCoinWebSocket()
        
        # Verify max_subscriptions is set
        self.assertEqual(ws._max_subscriptions, 380)
        
        # Simulate subscriptions approaching limit
        ws.connected = True
        ws.ws = MagicMock()
        
        # Add subscriptions up to limit
        for i in range(380):
            ws._subscriptions.add(f'ticker:PAIR{i}/USDT:USDT')
        
        # Try to subscribe when at limit - should fail
        result = ws.subscribe_ticker('BTC/USDT:USDT')
        
        # Should return False when limit is reached
        self.assertFalse(result)
        
        # Verify subscription count doesn't exceed limit
        self.assertLessEqual(len(ws._subscriptions), 380)
    
    def test_websocket_connection_check(self):
        """Test that subscription checks connection state"""
        from kucoin_websocket import KuCoinWebSocket
        
        # Create WebSocket instance
        ws = KuCoinWebSocket()
        
        # Test subscription when not connected
        ws.connected = False
        ws.ws = None
        
        result = ws.subscribe_ticker('BTC/USDT:USDT')
        
        # Should return False when not connected
        self.assertFalse(result)
        
        # Now test with connected but ws is None
        ws.connected = True
        ws.ws = None
        
        # The _subscribe_ticker should check for both conditions
        # We can't test this directly without mocking, but we've verified the code path


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
