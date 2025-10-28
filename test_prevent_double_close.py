"""
Test that bot doesn't try to close already-closed positions
"""
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

# Mock the logger before importing modules
with patch('logger.Logger.get_logger'), \
     patch('logger.Logger.get_position_logger'), \
     patch('logger.Logger.get_orders_logger'):
    from position_manager import PositionManager, Position


class TestPreventDoubleClose(unittest.TestCase):
    """Test that position manager doesn't try to close already-closed positions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock KuCoin client
        self.mock_client = Mock()
        
        # Create position manager
        self.position_manager = PositionManager(
            client=self.mock_client,
            trailing_stop_percentage=0.02
        )
    
    def test_close_position_checks_exchange_first(self):
        """Test that close_position checks if position exists on exchange before attempting close"""
        # Setup: Add a position to local tracking
        symbol = 'BTC/USDT:USDT'
        position = Position(
            symbol=symbol,
            side='long',
            entry_price=50000.0,
            amount=0.01,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        self.position_manager.positions[symbol] = position
        
        # Mock: Position does NOT exist on exchange (already closed externally)
        self.mock_client.get_open_positions = Mock(return_value=[])
        
        # Execute: Try to close the position
        result = self.position_manager.close_position(symbol, 'test')
        
        # Verify: Should return None (couldn't close because already closed)
        self.assertIsNone(result)
        
        # Verify: Position should be removed from local tracking
        self.assertNotIn(symbol, self.position_manager.positions)
        
        # Verify: Should NOT call client.close_position (position doesn't exist)
        self.mock_client.close_position.assert_not_called()
    
    def test_close_position_proceeds_when_position_exists(self):
        """Test that close_position proceeds normally when position exists on exchange"""
        # Setup: Add a position to local tracking
        symbol = 'BTC/USDT:USDT'
        position = Position(
            symbol=symbol,
            side='long',
            entry_price=50000.0,
            amount=0.01,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        self.position_manager.positions[symbol] = position
        
        # Mock: Position DOES exist on exchange
        self.mock_client.get_open_positions = Mock(return_value=[{
            'symbol': symbol,
            'side': 'long',
            'contracts': 0.01,
            'leverage': 10
        }])
        
        # Mock: Ticker and close operations
        self.mock_client.get_ticker = Mock(return_value={'last': 51000.0})
        self.mock_client.close_position = Mock(return_value=True)
        
        # Execute: Try to close the position
        result = self.position_manager.close_position(symbol, 'test')
        
        # Verify: Should return a P/L value (not None)
        self.assertIsNotNone(result)
        
        # Verify: Position should be removed from local tracking
        self.assertNotIn(symbol, self.position_manager.positions)
        
        # Verify: Should call client.close_position
        self.mock_client.close_position.assert_called_once_with(symbol)
    
    def test_update_positions_skips_closed_positions(self):
        """Test that update_positions skips positions that were closed externally"""
        # Setup: Add a position to local tracking
        symbol = 'BTC/USDT:USDT'
        position = Position(
            symbol=symbol,
            side='long',
            entry_price=50000.0,
            amount=0.01,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        self.position_manager.positions[symbol] = position
        
        # Mock: Position does NOT exist on exchange
        self.mock_client.get_open_positions = Mock(return_value=[])
        
        # Mock: Ticker returns a price that would trigger close
        self.mock_client.get_ticker = Mock(return_value={'last': 48000.0})  # Below stop loss
        
        # Mock: OHLCV data
        self.mock_client.get_ohlcv = Mock(return_value=[])
        
        # Execute: Update positions
        closed_positions = list(self.position_manager.update_positions())
        
        # Verify: No positions should be yielded (position doesn't exist to close)
        # The position should be cleaned up silently
        self.assertEqual(len(closed_positions), 0)
        
        # Note: The position will be cleaned up during the close attempt within update_positions(),
        # as update_positions now re-checks for position existence after updates.
    
    def test_close_position_not_in_tracking(self):
        """Test that close_position returns None when position not in local tracking"""
        symbol = 'BTC/USDT:USDT'
        
        # Execute: Try to close a position that's not tracked
        result = self.position_manager.close_position(symbol, 'test')
        
        # Verify: Should return None
        self.assertIsNone(result)
        
        # Verify: Should NOT call any client methods
        self.mock_client.get_open_positions.assert_not_called()
        self.mock_client.close_position.assert_not_called()
    
    def test_multiple_close_attempts_prevented(self):
        """Test that attempting to close the same position twice is handled gracefully"""
        # Setup: Add a position to local tracking
        symbol = 'BTC/USDT:USDT'
        position = Position(
            symbol=symbol,
            side='long',
            entry_price=50000.0,
            amount=0.01,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        self.position_manager.positions[symbol] = position
        
        # Mock: Position exists on exchange for first call
        self.mock_client.get_open_positions = Mock(return_value=[{
            'symbol': symbol,
            'side': 'long',
            'contracts': 0.01,
            'leverage': 10
        }])
        self.mock_client.get_ticker = Mock(return_value={'last': 51000.0})
        self.mock_client.close_position = Mock(return_value=True)
        
        # Execute: Close the position first time
        result1 = self.position_manager.close_position(symbol, 'test')
        
        # Verify: First close should succeed
        self.assertIsNotNone(result1)
        self.assertNotIn(symbol, self.position_manager.positions)
        
        # Mock: Position no longer exists on exchange for second call
        self.mock_client.get_open_positions = Mock(return_value=[])
        
        # Execute: Try to close the same position again
        result2 = self.position_manager.close_position(symbol, 'test')
        
        # Verify: Second close should return None (not in tracking)
        self.assertIsNone(result2)
        
        # Verify: client.close_position should only be called once (first time)
        self.assertEqual(self.mock_client.close_position.call_count, 1)


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPreventDoubleClose)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✓ All double-close prevention tests passed!")
        print("  The bot will now properly handle already-closed positions")
    else:
        print(f"✗ {len(result.failures)} test(s) failed")
        print(f"✗ {len(result.errors)} test(s) had errors")
    print("=" * 70)
