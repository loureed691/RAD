"""
Integration test to verify scale-out minimum adjustment works end-to-end
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime

class TestScaleOutAdjustmentIntegration(unittest.TestCase):
    """Integration test for scale-out order size adjustment"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('logger.Logger.get_logger'), \
             patch('logger.Logger.get_position_logger'), \
             patch('logger.Logger.get_orders_logger'):
            from position_manager import Position, PositionManager
            
            self.Position = Position
            self.PositionManager = PositionManager
    
    def test_end_to_end_small_position_partial_exit(self):
        """Test that small positions can still execute partial exits via adjustment"""
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
        
        # Scenario: Small position hits first profit target (25% scale-out)
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.714,  # Small position from real-world scenario
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Add position to manager
        position_manager.positions['BTC/USDT:USDT'] = position
        
        # Simulate profit target being hit: 25% scale-out requested
        scale_pct = 0.25
        amount_to_close = 1.714 * scale_pct  # = 0.4285 (below minimum)
        
        print(f"\n=== Scale-Out Adjustment Integration Test ===")
        print(f"Position size: {position.amount} contracts")
        print(f"Requested scale-out: {scale_pct*100:.0f}% = {amount_to_close:.4f} contracts")
        print(f"Exchange minimum: 1.0 contracts")
        print(f"Expected adjustment: {amount_to_close:.4f} → 1.0 contracts")
        
        # Execute scale-out
        result = position_manager.scale_out_position(
            'BTC/USDT:USDT', 
            amount_to_close,
            'profit_scaling - First target reached (2.04%)'
        )
        
        # Verify success
        self.assertIsNotNone(result, "Scale-out should succeed with adjusted amount")
        
        # Verify order was created with adjusted amount
        mock_client.create_market_order.assert_called_once()
        call_args = mock_client.create_market_order.call_args
        actual_amount = call_args[0][2]
        self.assertEqual(actual_amount, 1.0, "Order should be adjusted to minimum 1.0")
        
        # Verify position was reduced by adjusted amount
        expected_remaining = 1.714 - 1.0
        self.assertAlmostEqual(position.amount, expected_remaining, places=3,
                              msg=f"Position should be reduced to {expected_remaining:.3f}")
        
        print(f"✓ Order adjusted to: {actual_amount} contracts")
        print(f"✓ Position reduced to: {position.amount:.3f} contracts")
        print(f"✓ Partial exit successful despite being below minimum")
        print(f"=== Test Passed ===\n")
    
    def test_multiple_sequential_scale_outs(self):
        """Test that multiple scale-outs work correctly with adjustment"""
        # Create a mock client
        mock_client = Mock()
        
        # Mock get_market_limits to return min amount of 1.0
        mock_client.get_market_limits.return_value = {
            'amount': {'min': 1.0, 'max': 10000.0},
            'cost': {'min': 1.0, 'max': 100000.0}
        }
        
        # Mock get_ticker with increasing prices
        ticker_responses = [
            {'last': 51020.0},  # +2% - First target
            {'last': 52040.0},  # +4% - Second target
        ]
        mock_client.get_ticker.side_effect = ticker_responses
        
        # Mock create_market_order to return successful orders
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
        
        # Start with a position that can handle 2 scale-outs after adjustment
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=3.0,  # Larger position to allow multiple scale-outs
            leverage=10,
            stop_loss=49000.0,
            take_profit=54000.0
        )
        
        position_manager.positions['BTC/USDT:USDT'] = position
        
        print(f"\n=== Multiple Scale-Out Integration Test ===")
        print(f"Initial position: {position.amount} contracts")
        
        # First scale-out: 25% of 3.0 = 0.75 → adjusted to 1.0
        result1 = position_manager.scale_out_position(
            'BTC/USDT:USDT', 
            0.75,  # 25% of 3.0
            'First target (2%)'
        )
        self.assertIsNotNone(result1)
        self.assertAlmostEqual(position.amount, 2.0, places=3)
        print(f"✓ First scale-out: 0.75 → 1.0 contracts, remaining: {position.amount:.1f}")
        
        # Second scale-out: 25% of 2.0 = 0.5 → adjusted to 1.0
        result2 = position_manager.scale_out_position(
            'BTC/USDT:USDT', 
            0.5,  # 25% of remaining 2.0
            'Second target (4%)'
        )
        self.assertIsNotNone(result2)
        self.assertAlmostEqual(position.amount, 1.0, places=3)
        print(f"✓ Second scale-out: 0.5 → 1.0 contracts, remaining: {position.amount:.1f}")
        
        print(f"✓ Multiple scale-outs handled correctly with adjustments")
        print(f"=== Test Passed ===\n")

if __name__ == '__main__':
    unittest.main(verbosity=2)
