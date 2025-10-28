"""
Test that position manager properly cleans up already-closed positions during update
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Mock the logger before importing modules
with patch('logger.Logger.get_logger'), \
     patch('logger.Logger.get_position_logger'), \
     patch('logger.Logger.get_orders_logger'):
    from position_manager import PositionManager, Position


class TestPositionCleanup(unittest.TestCase):
    """Test that position manager cleans up externally-closed positions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock KuCoin client
        self.mock_client = Mock()
        
        # Create position manager
        self.position_manager = PositionManager(
            client=self.mock_client,
            trailing_stop_percentage=0.02
        )
    
    def test_update_positions_removes_closed_positions(self):
        """Test that update_positions removes positions not on exchange"""
        # Setup: Add 3 positions to local tracking
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
        for symbol in symbols:
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
        
        # Verify all 3 are tracked
        self.assertEqual(len(self.position_manager.positions), 3)
        
        # Mock: Only 1 position exists on exchange (2 were closed externally)
        self.mock_client.get_open_positions = Mock(return_value=[{
            'symbol': 'BTC/USDT:USDT',
            'side': 'long',
            'contracts': 0.01,
            'leverage': 10
        }])
        
        # Mock: Ticker for the remaining position
        self.mock_client.get_ticker = Mock(return_value={'last': 51000.0})
        
        # Mock: OHLCV data (empty to trigger simple update)
        self.mock_client.get_ohlcv = Mock(return_value=[])
        
        # Execute: Update positions (should clean up closed ones)
        list(self.position_manager.update_positions())
        
        # Verify: Only 1 position remains (the one on exchange)
        self.assertEqual(len(self.position_manager.positions), 1)
        self.assertIn('BTC/USDT:USDT', self.position_manager.positions)
        self.assertNotIn('ETH/USDT:USDT', self.position_manager.positions)
        self.assertNotIn('SOL/USDT:USDT', self.position_manager.positions)
    
    def test_update_positions_keeps_all_when_all_exist(self):
        """Test that update_positions keeps positions that exist on exchange"""
        # Setup: Add 2 positions to local tracking
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT']
        for symbol in symbols:
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
        
        # Mock: Both positions exist on exchange
        self.mock_client.get_open_positions = Mock(return_value=[
            {
                'symbol': 'BTC/USDT:USDT',
                'side': 'long',
                'contracts': 0.01,
                'leverage': 10
            },
            {
                'symbol': 'ETH/USDT:USDT',
                'side': 'long',
                'contracts': 0.01,
                'leverage': 10
            }
        ])
        
        # Mock: Ticker
        self.mock_client.get_ticker = Mock(return_value={'last': 51000.0})
        
        # Mock: OHLCV data
        self.mock_client.get_ohlcv = Mock(return_value=[])
        
        # Execute: Update positions
        list(self.position_manager.update_positions())
        
        # Verify: Both positions remain
        self.assertEqual(len(self.position_manager.positions), 2)
        self.assertIn('BTC/USDT:USDT', self.position_manager.positions)
        self.assertIn('ETH/USDT:USDT', self.position_manager.positions)
    
    def test_update_positions_handles_api_error_gracefully(self):
        """Test that update_positions handles API errors without crashing"""
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
        
        # Mock: API error when checking positions
        self.mock_client.get_open_positions = Mock(side_effect=Exception("API error"))
        
        # Mock: Ticker (for subsequent update)
        self.mock_client.get_ticker = Mock(return_value={'last': 51000.0})
        
        # Mock: OHLCV data
        self.mock_client.get_ohlcv = Mock(return_value=[])
        
        # Execute: Update positions (should not crash)
        try:
            list(self.position_manager.update_positions())
            success = True
        except Exception:
            success = False
        
        # Verify: Didn't crash and position still exists (wasn't removed)
        self.assertTrue(success)
        self.assertEqual(len(self.position_manager.positions), 1)
        self.assertIn(symbol, self.position_manager.positions)
    
    def test_update_positions_removes_all_when_none_exist(self):
        """Test that update_positions removes all positions when none exist on exchange"""
        # Setup: Add positions to local tracking
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT']
        for symbol in symbols:
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
        
        # Mock: No positions exist on exchange (all closed externally)
        self.mock_client.get_open_positions = Mock(return_value=[])
        
        # Execute: Update positions
        list(self.position_manager.update_positions())
        
        # Verify: All positions removed
        self.assertEqual(len(self.position_manager.positions), 0)


if __name__ == '__main__':
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPositionCleanup)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✓ All position cleanup tests passed!")
        print("  Position manager will now clean up externally-closed positions")
    else:
        print(f"✗ {len(result.failures)} test(s) failed")
        print(f"✗ {len(result.errors)} test(s) had errors")
    print("=" * 70)
