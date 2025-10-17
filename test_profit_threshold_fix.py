"""
Test to verify take profit calculation includes MIN_PROFIT_THRESHOLD
This ensures the bot accounts for trading fees (0.12%) in take profit targets
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from position_manager import PositionManager
from config import Config


class TestProfitThresholdFix(unittest.TestCase):
    """Test that take profit calculations include MIN_PROFIT_THRESHOLD"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the client
        self.mock_client = Mock()
        
        # Create position manager
        self.position_manager = PositionManager(
            client=self.mock_client,
            trailing_stop_percentage=0.02
        )
    
    def test_take_profit_includes_min_threshold_low_stop_loss(self):
        """Test take profit uses MIN_PROFIT_THRESHOLD when stop loss is small"""
        # Set MIN_PROFIT_THRESHOLD to simulate fees + desired profit
        Config.MIN_PROFIT_THRESHOLD = 0.0062  # 0.62% (0.12% fees + 0.5% profit)
        
        # Mock ticker response
        self.mock_client.get_ticker.return_value = {'last': 50000}
        
        # Mock order creation
        self.mock_client.create_market_order.return_value = {
            'id': 'test_order_123',
            'average': 50000,
            'filled': 0.1
        }
        
        # Open position with small stop loss (1%)
        stop_loss_pct = 0.01  # 1%
        
        # Open the position
        result = self.position_manager.open_position(
            symbol='BTC/USDT:USDT',
            signal='BUY',
            amount=0.1,
            leverage=5,
            stop_loss_percentage=stop_loss_pct
        )
        
        self.assertTrue(result, "Position should open successfully")
        
        # Verify position was created
        self.assertIn('BTC/USDT:USDT', self.position_manager.positions)
        position = self.position_manager.positions['BTC/USDT:USDT']
        
        # Calculate expected take profit
        # With 1% stop loss, 3x would be 3% - but MIN_PROFIT_THRESHOLD is 0.62%
        # So take_profit should use max(1% * 3, 0.62%) = 3%
        expected_tp = 50000 * (1 + 0.03)  # 3%
        
        # Verify take profit is correct
        self.assertAlmostEqual(position.take_profit, expected_tp, places=2,
                              msg=f"Take profit should be {expected_tp}, got {position.take_profit}")
    
    def test_take_profit_uses_min_threshold_with_tiny_stop_loss(self):
        """Test take profit uses MIN_PROFIT_THRESHOLD when stop loss * 3 < threshold"""
        # Set MIN_PROFIT_THRESHOLD
        Config.MIN_PROFIT_THRESHOLD = 0.01  # 1%
        
        # Mock ticker response
        self.mock_client.get_ticker.return_value = {'last': 50000}
        
        # Mock order creation
        self.mock_client.create_market_order.return_value = {
            'id': 'test_order_456',
            'average': 50000,
            'filled': 0.1
        }
        
        # Open position with tiny stop loss (0.2%)
        stop_loss_pct = 0.002  # 0.2%
        
        # Open the position
        result = self.position_manager.open_position(
            symbol='ETH/USDT:USDT',
            signal='BUY',
            amount=1.0,
            leverage=3,
            stop_loss_percentage=stop_loss_pct
        )
        
        self.assertTrue(result, "Position should open successfully")
        
        # Verify position was created
        self.assertIn('ETH/USDT:USDT', self.position_manager.positions)
        position = self.position_manager.positions['ETH/USDT:USDT']
        
        # Calculate expected take profit
        # With 0.2% stop loss, 3x would be 0.6% - but MIN_PROFIT_THRESHOLD is 1%
        # So take_profit should use max(0.2% * 3, 1%) = 1%
        expected_tp = 50000 * (1 + 0.01)  # 1%
        
        # Verify take profit uses minimum threshold
        self.assertAlmostEqual(position.take_profit, expected_tp, places=2,
                              msg=f"Take profit should use MIN_PROFIT_THRESHOLD of {expected_tp}, got {position.take_profit}")
    
    def test_take_profit_uses_3x_when_larger_than_threshold(self):
        """Test take profit uses 3x stop loss when it's larger than MIN_PROFIT_THRESHOLD"""
        # Set MIN_PROFIT_THRESHOLD
        Config.MIN_PROFIT_THRESHOLD = 0.005  # 0.5%
        
        # Mock ticker response
        self.mock_client.get_ticker.return_value = {'last': 40000}
        
        # Mock order creation
        self.mock_client.create_market_order.return_value = {
            'id': 'test_order_789',
            'average': 40000,
            'filled': 0.5
        }
        
        # Open position with larger stop loss (2%)
        stop_loss_pct = 0.02  # 2%
        
        # Open the position
        result = self.position_manager.open_position(
            symbol='SOL/USDT:USDT',
            signal='SELL',
            amount=10.0,
            leverage=5,
            stop_loss_percentage=stop_loss_pct
        )
        
        self.assertTrue(result, "Position should open successfully")
        
        # Verify position was created
        self.assertIn('SOL/USDT:USDT', self.position_manager.positions)
        position = self.position_manager.positions['SOL/USDT:USDT']
        
        # Calculate expected take profit
        # With 2% stop loss, 3x would be 6% - which is larger than MIN_PROFIT_THRESHOLD (0.5%)
        # So take_profit should use max(2% * 3, 0.5%) = 6%
        expected_tp = 40000 * (1 - 0.06)  # 6% for SELL position
        
        # Verify take profit uses 3x rule (not minimum)
        self.assertAlmostEqual(position.take_profit, expected_tp, places=2,
                              msg=f"Take profit should use 3x stop loss = {expected_tp}, got {position.take_profit}")


if __name__ == '__main__':
    unittest.main()
