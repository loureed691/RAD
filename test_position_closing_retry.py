"""
Test position closing retry logic to ensure trades are executed
"""
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import ccxt
import time

# Mock the logger before importing kucoin_client
with patch('logger.Logger.get_logger'), patch('logger.Logger.get_orders_logger'):
    from kucoin_client import KuCoinClient

class TestPositionClosingRetry(unittest.TestCase):
    """Test that position closing retries aggressively"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('kucoin_client.KuCoinWebSocket'):
            self.client = KuCoinClient(
                api_key='test_key',
                api_secret='test_secret',
                api_passphrase='test_pass',
                enable_websocket=False
            )
    
    def test_handle_api_error_with_critical_flag(self):
        """Test that critical operations get more retries"""
        mock_func = Mock(side_effect=ccxt.NetworkError("Network error"))
        
        # Non-critical operation should try 3 times (default)
        result = self.client._handle_api_error(
            mock_func,
            max_retries=3,
            exponential_backoff=False,
            operation_name="test_non_critical",
            is_critical=False
        )
        
        self.assertIsNone(result)
        self.assertEqual(mock_func.call_count, 3)
        
        # Reset mock
        mock_func.reset_mock()
        mock_func.side_effect = ccxt.NetworkError("Network error")
        
        # Critical operation should try 9 times (3 * 3)
        result = self.client._handle_api_error(
            mock_func,
            max_retries=3,
            exponential_backoff=False,
            operation_name="test_critical",
            is_critical=True
        )
        
        self.assertIsNone(result)
        self.assertEqual(mock_func.call_count, 9)
    
    def test_handle_api_error_recovers_on_retry(self):
        """Test that retries eventually succeed"""
        # Fail 2 times, then succeed
        mock_func = Mock(side_effect=[
            ccxt.NetworkError("Error 1"),
            ccxt.NetworkError("Error 2"),
            {"success": True}
        ])
        
        result = self.client._handle_api_error(
            mock_func,
            max_retries=3,
            exponential_backoff=False,
            operation_name="test_recovery",
            is_critical=False
        )
        
        self.assertEqual(result, {"success": True})
        self.assertEqual(mock_func.call_count, 3)
    
    def test_close_position_retries_entire_operation(self):
        """Test that close_position retries the entire operation"""
        # Mock get_open_positions to return a position
        self.client.get_open_positions = Mock(return_value=[{
            'symbol': 'BTC/USDT:USDT',
            'side': 'long',
            'contracts': 0.01,
            'leverage': 10
        }])
        
        # Mock create_market_order to fail twice, then succeed
        call_count = [0]
        def create_order_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                return None  # Fail
            return {"id": "123", "status": "closed"}  # Success
        
        self.client.create_market_order = Mock(side_effect=create_order_side_effect)
        
        # Call close_position
        result = self.client.close_position('BTC/USDT:USDT', max_close_retries=5)
        
        # Should succeed after retries
        self.assertTrue(result)
        self.assertEqual(call_count[0], 3)
    
    def test_close_position_handles_position_not_found(self):
        """Test that close_position handles position not found gracefully"""
        # Mock get_open_positions to return empty list (position already closed)
        self.client.get_open_positions = Mock(return_value=[])
        
        # Call close_position
        result = self.client.close_position('BTC/USDT:USDT')
        
        # Should return True (position already closed)
        self.assertTrue(result)
    
    def test_close_position_exhausts_retries(self):
        """Test that close_position eventually gives up after max retries"""
        # Mock get_open_positions to return a position
        self.client.get_open_positions = Mock(return_value=[{
            'symbol': 'BTC/USDT:USDT',
            'side': 'long',
            'contracts': 0.01,
            'leverage': 10
        }])
        
        # Mock create_market_order to always fail
        self.client.create_market_order = Mock(return_value=None)
        
        # Call close_position with limited retries
        result = self.client.close_position('BTC/USDT:USDT', max_close_retries=3)
        
        # Should fail after exhausting retries
        self.assertFalse(result)
        # Should have tried 3 times
        self.assertEqual(self.client.create_market_order.call_count, 3)

if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPositionClosingRetry)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✓ All position closing retry tests passed!")
    else:
        print(f"✗ {len(result.failures)} test(s) failed")
        print(f"✗ {len(result.errors)} test(s) had errors")
    print("=" * 70)
