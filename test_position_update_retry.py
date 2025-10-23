"""
Test for improved position update retry logic
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from position_manager import PositionManager, Position


class TestPositionUpdateRetry(unittest.TestCase):
    """Test position update retry logic improvements"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock client
        self.mock_client = Mock()
        
        # Mock get_market_limits to prevent scale_out errors
        self.mock_client.get_market_limits.return_value = {
            'amount': {'min': 0.001, 'max': 10000}
        }
        
        self.position_manager = PositionManager(self.mock_client, trailing_stop_percentage=0.02)
        
        # Add a test position
        self.test_symbol = "BTC/USDT:USDT"
        test_position = Position(
            symbol=self.test_symbol,
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=3,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        self.position_manager.positions[self.test_symbol] = test_position
    
    def test_successful_price_fetch_first_attempt(self):
        """Test that successful price fetch on first attempt doesn't retry"""
        # Mock successful ticker fetch
        self.mock_client.get_ticker.return_value = {
            'last': 50500.0,
            'symbol': self.test_symbol
        }
        
        # Mock OHLCV to prevent further API calls
        self.mock_client.get_ohlcv.return_value = None
        
        # Update positions
        list(self.position_manager.update_positions())
        
        # Should call get_ticker at least once for the position update (no retries needed)
        # May be called more if advanced exit strategy needs it
        self.assertGreaterEqual(self.mock_client.get_ticker.call_count, 1)
        # But should not retry excessively (less than 4 calls for a simple case)
        self.assertLessEqual(self.mock_client.get_ticker.call_count, 4)
    
    def test_retry_on_none_response(self):
        """Test that API returns None triggers retries"""
        # Track how many times get_ticker is called during initial fetch attempts
        call_count_before = 0
        
        def ticker_side_effect(*args, **kwargs):
            nonlocal call_count_before
            call_count_before += 1
            if call_count_before <= 2:
                return None  # First 2 attempts
            else:
                return {'last': 50500.0, 'symbol': self.test_symbol}  # Succeeds on 3rd
        
        self.mock_client.get_ticker.side_effect = ticker_side_effect
        
        # Mock OHLCV to prevent further API calls
        self.mock_client.get_ohlcv.return_value = None
        
        # Update positions
        list(self.position_manager.update_positions())
        
        # Should have retried at least 3 times during the position update
        self.assertGreaterEqual(self.mock_client.get_ticker.call_count, 3)
    
    def test_retry_on_invalid_price(self):
        """Test that invalid price (0 or negative) triggers retries"""
        # Track how many times get_ticker is called during initial fetch attempts
        call_count_before = 0
        
        def ticker_side_effect(*args, **kwargs):
            nonlocal call_count_before
            call_count_before += 1
            if call_count_before == 1:
                return {'last': 0, 'symbol': self.test_symbol}  # Invalid
            elif call_count_before == 2:
                return {'last': -100, 'symbol': self.test_symbol}  # Invalid
            else:
                return {'last': 50500.0, 'symbol': self.test_symbol}  # Valid
        
        self.mock_client.get_ticker.side_effect = ticker_side_effect
        
        # Mock OHLCV to prevent further API calls
        self.mock_client.get_ohlcv.return_value = None
        
        # Update positions
        list(self.position_manager.update_positions())
        
        # Should have retried at least 3 times
        self.assertGreaterEqual(self.mock_client.get_ticker.call_count, 3)
    
    def test_retry_on_api_exception(self):
        """Test that API exceptions trigger retries"""
        # Track how many times get_ticker is called during initial fetch attempts
        call_count_before = 0
        
        def ticker_side_effect(*args, **kwargs):
            nonlocal call_count_before
            call_count_before += 1
            if call_count_before <= 2:
                raise Exception(f"Network error {call_count_before}")
            else:
                return {'last': 50500.0, 'symbol': self.test_symbol}
        
        self.mock_client.get_ticker.side_effect = ticker_side_effect
        
        # Mock OHLCV to prevent further API calls
        self.mock_client.get_ohlcv.return_value = None
        
        # Update positions
        list(self.position_manager.update_positions())
        
        # Should have retried at least 3 times
        self.assertGreaterEqual(self.mock_client.get_ticker.call_count, 3)
    
    def test_skip_position_after_all_retries_fail(self):
        """Test that position is skipped after all retries fail"""
        # Mock ticker to always return None (all retries fail)
        self.mock_client.get_ticker.return_value = None
        
        # Update positions
        list(self.position_manager.update_positions())
        
        # Should call get_ticker 10 times (max retries)
        self.assertEqual(self.mock_client.get_ticker.call_count, 10)
        
        # Position should still be open (not closed due to failed price fetch)
        self.assertIn(self.test_symbol, self.position_manager.positions)
    
    def test_stop_loss_triggers_with_price(self):
        """Test that stop loss triggers when price is fetched successfully"""
        # Mock ticker to return price below stop loss
        self.mock_client.get_ticker.return_value = {
            'last': 48000.0,  # Below stop loss of 49000
            'symbol': self.test_symbol
        }
        
        # Mock close position
        self.mock_client.close_position.return_value = True
        
        # Mock OHLCV to prevent further API calls
        self.mock_client.get_ohlcv.return_value = None
        
        # Update positions
        closed_positions = list(self.position_manager.update_positions())
        
        # Should have closed the position
        self.assertEqual(len(closed_positions), 1)
        self.assertEqual(closed_positions[0][0], self.test_symbol)
        
        # Position should be removed
        self.assertNotIn(self.test_symbol, self.position_manager.positions)
    
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_retry_delay_increases(self, mock_sleep):
        """Test that retry delays increase with each attempt"""
        # Mock ticker to fail several times
        self.mock_client.get_ticker.side_effect = [
            None,  # Attempt 1
            None,  # Attempt 2
            None,  # Attempt 3
            None,  # Attempt 4
            {'last': 50500.0, 'symbol': self.test_symbol}  # Attempt 5 succeeds
        ]
        
        # Mock OHLCV to prevent further API calls
        self.mock_client.get_ohlcv.return_value = None
        
        # Update positions
        list(self.position_manager.update_positions())
        
        # Check that sleep was called with increasing delays
        # Sleep should be called 4 times (not after the successful 5th attempt)
        self.assertEqual(mock_sleep.call_count, 4)
        
        # Get all sleep call arguments
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        
        # Verify delays are within expected ranges (with jitter)
        # Expected delays: 1s, 2s, 3s, 5s (with ±20% jitter)
        self.assertGreater(sleep_calls[0], 0.8)  # 1s * 0.8
        self.assertLess(sleep_calls[0], 1.2)  # 1s * 1.2
        
        self.assertGreater(sleep_calls[1], 1.6)  # 2s * 0.8
        self.assertLess(sleep_calls[1], 2.4)  # 2s * 1.2
        
        self.assertGreater(sleep_calls[2], 2.4)  # 3s * 0.8
        self.assertLess(sleep_calls[2], 3.6)  # 3s * 1.2
        
        self.assertGreater(sleep_calls[3], 4.0)  # 5s * 0.8
        self.assertLess(sleep_calls[3], 6.0)  # 5s * 1.2


if __name__ == '__main__':
    unittest.main()
