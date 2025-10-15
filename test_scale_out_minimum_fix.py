"""
Test that scale-out operations respect minimum order sizes
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

class TestScaleOutMinimumFix(unittest.TestCase):
    """Test that scale-out validates minimum order size"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock logger
        with patch('logger.Logger.get_logger'), \
             patch('logger.Logger.get_position_logger'), \
             patch('logger.Logger.get_orders_logger'):
            from position_manager import Position, PositionManager
            
            self.Position = Position
            self.PositionManager = PositionManager
    
    def test_scale_out_below_minimum_is_adjusted(self):
        """Test that scale-out is adjusted to minimum when amount is below minimum"""
        # Create a mock client
        mock_client = Mock()
        
        # Mock get_market_limits to return min amount of 1.0
        mock_client.get_market_limits.return_value = {
            'amount': {'min': 1.0, 'max': 10000.0},
            'cost': {'min': 1.0, 'max': 100000.0}
        }
        
        # Mock get_ticker
        mock_client.get_ticker.return_value = {'last': 51020.0}
        
        # Mock create_market_order to return a successful order
        mock_client.create_market_order.return_value = {
            'id': '123456',
            'status': 'closed',
            'filled': 1.0
        }
        
        # Create position manager with mock client
        with patch('logger.Logger.get_logger'), \
             patch('logger.Logger.get_position_logger'), \
             patch('logger.Logger.get_orders_logger'):
            position_manager = self.PositionManager(mock_client)
        
        # Create a position with 1.714 contracts
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.714,  # Small position
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Add position to manager
        position_manager.positions['BTC/USDT:USDT'] = position
        
        # Try to scale out 25% (0.4285 contracts) - below minimum of 1.0
        amount_to_close = 1.714 * 0.25  # = 0.4285
        result = position_manager.scale_out_position(
            'BTC/USDT:USDT', 
            amount_to_close,
            'First target reached (2.04%)'
        )
        
        # Should succeed with adjusted amount
        self.assertIsNotNone(result)
        
        # Verify order was created with adjusted amount (1.0 instead of 0.4285)
        mock_client.create_market_order.assert_called_once()
        call_args = mock_client.create_market_order.call_args
        self.assertEqual(call_args[0][2], 1.0)  # amount_to_close should be adjusted to 1.0
        
        # Verify position amount reduced by adjusted amount
        self.assertAlmostEqual(position.amount, 0.714, places=3)  # 1.714 - 1.0
    
    def test_scale_out_above_minimum_is_accepted(self):
        """Test that scale-out is accepted when amount is above minimum"""
        # Create a mock client
        mock_client = Mock()
        
        # Mock get_market_limits to return min amount of 1.0
        mock_client.get_market_limits.return_value = {
            'amount': {'min': 1.0, 'max': 10000.0},
            'cost': {'min': 1.0, 'max': 100000.0}
        }
        
        # Mock get_ticker
        mock_client.get_ticker.return_value = {'last': 51020.0}
        
        # Mock create_market_order to return a successful order
        mock_client.create_market_order.return_value = {
            'id': '123456',
            'status': 'closed',
            'filled': 1.25
        }
        
        # Create position manager with mock client
        with patch('logger.Logger.get_logger'), \
             patch('logger.Logger.get_position_logger'), \
             patch('logger.Logger.get_orders_logger'):
            position_manager = self.PositionManager(mock_client)
        
        # Create a position with 5.0 contracts (larger)
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=5.0,  # Larger position
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Add position to manager
        position_manager.positions['BTC/USDT:USDT'] = position
        
        # Try to scale out 25% (1.25 contracts) - above minimum of 1.0
        amount_to_close = 5.0 * 0.25  # = 1.25
        result = position_manager.scale_out_position(
            'BTC/USDT:USDT', 
            amount_to_close,
            'First target reached (2.04%)'
        )
        
        # Should return a P/L value (success)
        self.assertIsNotNone(result)
        
        # Verify order was created
        mock_client.create_market_order.assert_called_once()
        
        # Verify position amount reduced
        self.assertEqual(position.amount, 3.75)  # 5.0 - 1.25
    
    def test_scale_out_no_limits_available_allows_order(self):
        """Test that scale-out proceeds when limits cannot be retrieved"""
        # Create a mock client
        mock_client = Mock()
        
        # Mock get_market_limits to return None (can't get limits)
        mock_client.get_market_limits.return_value = None
        
        # Mock get_ticker
        mock_client.get_ticker.return_value = {'last': 51020.0}
        
        # Mock create_market_order to return a successful order
        mock_client.create_market_order.return_value = {
            'id': '123456',
            'status': 'closed',
            'filled': 0.4285
        }
        
        # Create position manager with mock client
        with patch('logger.Logger.get_logger'), \
             patch('logger.Logger.get_position_logger'), \
             patch('logger.Logger.get_orders_logger'):
            position_manager = self.PositionManager(mock_client)
        
        # Create a position
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.714,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Add position to manager
        position_manager.positions['BTC/USDT:USDT'] = position
        
        # Try to scale out - should proceed even though amount is small
        amount_to_close = 1.714 * 0.25
        result = position_manager.scale_out_position(
            'BTC/USDT:USDT', 
            amount_to_close,
            'First target reached (2.04%)'
        )
        
        # Should proceed (no limits to check)
        # Note: In reality, the exchange will reject it, but we allow it here
        # since we can't validate without limits
        self.assertIsNotNone(result)
        mock_client.create_market_order.assert_called_once()

    def test_scale_out_exactly_at_minimum(self):
        """Test that scale-out is accepted when amount equals minimum exactly"""
        # Create a mock client
        mock_client = Mock()
        
        # Mock get_market_limits to return min amount of 1.0
        mock_client.get_market_limits.return_value = {
            'amount': {'min': 1.0, 'max': 10000.0},
            'cost': {'min': 1.0, 'max': 100000.0}
        }
        
        # Mock get_ticker
        mock_client.get_ticker.return_value = {'last': 51020.0}
        
        # Mock create_market_order to return a successful order
        mock_client.create_market_order.return_value = {
            'id': '123456',
            'status': 'closed',
            'filled': 1.0
        }
        
        # Create position manager with mock client
        with patch('logger.Logger.get_logger'), \
             patch('logger.Logger.get_position_logger'), \
             patch('logger.Logger.get_orders_logger'):
            position_manager = self.PositionManager(mock_client)
        
        # Create a position with exactly 4.0 contracts
        # 25% of 4.0 = 1.0 (exactly at minimum)
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=4.0,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Add position to manager
        position_manager.positions['BTC/USDT:USDT'] = position
        
        # Try to scale out exactly at minimum (1.0 contracts)
        amount_to_close = 1.0
        result = position_manager.scale_out_position(
            'BTC/USDT:USDT', 
            amount_to_close,
            'First target reached (2.04%)'
        )
        
        # Should succeed (1.0 == 1.0 is valid)
        self.assertIsNotNone(result)
        
        # Verify order was created
        mock_client.create_market_order.assert_called_once()
        
        # Verify position amount reduced
        self.assertEqual(position.amount, 3.0)  # 4.0 - 1.0

    def test_scale_out_adjusted_closes_entire_position(self):
        """Test that scale-out closes entire position when adjusted amount exceeds position size"""
        # Create a mock client
        mock_client = Mock()
        
        # Mock get_market_limits to return min amount of 1.0
        mock_client.get_market_limits.return_value = {
            'amount': {'min': 1.0, 'max': 10000.0},
            'cost': {'min': 1.0, 'max': 100000.0}
        }
        
        # Mock get_ticker
        mock_client.get_ticker.return_value = {'last': 51020.0}
        
        # Mock close_position to return success
        mock_client.close_position.return_value = 0.0204
        
        # Create position manager with mock client
        with patch('logger.Logger.get_logger'), \
             patch('logger.Logger.get_position_logger'), \
             patch('logger.Logger.get_orders_logger'):
            position_manager = self.PositionManager(mock_client)
        
        # Create a position with 0.8 contracts (less than minimum)
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.8,  # Position smaller than minimum
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Add position to manager
        position_manager.positions['BTC/USDT:USDT'] = position
        
        # Try to scale out 25% (0.2 contracts) - would be adjusted to 1.0 but that exceeds position
        amount_to_close = 0.8 * 0.25  # = 0.2
        result = position_manager.scale_out_position(
            'BTC/USDT:USDT', 
            amount_to_close,
            'First target reached (2.04%)'
        )
        
        # Should close entire position instead of partial
        self.assertIsNotNone(result)
        
        # Verify close_position was called (not create_market_order)
        mock_client.close_position.assert_called_once_with('BTC/USDT:USDT')
        
        # Verify position is removed (closed)
        self.assertNotIn('BTC/USDT:USDT', position_manager.positions)

if __name__ == '__main__':
    unittest.main()
