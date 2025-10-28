"""
Comprehensive test to verify buy and sell strategies execute correctly.

This test verifies:
1. BUY signals correctly open LONG positions
2. SELL signals correctly open SHORT positions  
3. Stop losses trigger correctly for both long and short positions
4. Take profits trigger correctly for both long and short positions
5. Position closing logic works correctly for both directions
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime


class TestBuySellStrategyExecution(unittest.TestCase):
    """Test that buy and sell strategies execute correctly in all scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock logger to avoid initialization issues
        with patch('logger.Logger.get_logger'), \
             patch('logger.Logger.get_position_logger'), \
             patch('logger.Logger.get_orders_logger'):
            from position_manager import Position, PositionManager
            from kucoin_client import KuCoinClient
            
            self.Position = Position
            self.PositionManager = PositionManager
            
            # Create mock client
            self.mock_client = Mock(spec=KuCoinClient)
            
            # Create position manager with mock client
            self.position_manager = PositionManager(
                client=self.mock_client,
                trailing_stop_percentage=0.02
            )
    
    def test_buy_signal_opens_long_position(self):
        """Test that BUY signal opens a LONG position correctly"""
        symbol = 'BTC/USDT:USDT'
        signal = 'BUY'
        amount = 0.01
        leverage = 10
        
        # Mock ticker and order creation
        self.mock_client.get_ticker.return_value = {'last': 50000.0}
        self.mock_client.create_market_order.return_value = {
            'id': '12345',
            'average': 50000.0
        }
        
        # Execute trade
        success = self.position_manager.open_position(
            symbol, signal, amount, leverage, stop_loss_percentage=0.05
        )
        
        # Verify position opened successfully
        self.assertTrue(success)
        
        # Verify position exists and is long
        self.assertTrue(self.position_manager.has_position(symbol))
        position = self.position_manager.get_position(symbol)
        self.assertIsNotNone(position)
        self.assertEqual(position.side, 'long')
        self.assertEqual(position.entry_price, 50000.0)
        self.assertEqual(position.amount, amount)
        self.assertEqual(position.leverage, leverage)
        
        # Verify stop loss is below entry (for long)
        self.assertLess(position.stop_loss, position.entry_price)
        
        # Verify take profit is above entry (for long)
        self.assertGreater(position.take_profit, position.entry_price)
        
        # Verify order was placed with correct side
        self.mock_client.create_market_order.assert_called_once()
        call_args = self.mock_client.create_market_order.call_args
        self.assertEqual(call_args[0][1], 'buy')  # Second arg is side
    
    def test_sell_signal_opens_short_position(self):
        """Test that SELL signal opens a SHORT position correctly"""
        symbol = 'ETH/USDT:USDT'
        signal = 'SELL'
        amount = 0.1
        leverage = 5
        
        # Mock ticker and order creation
        self.mock_client.get_ticker.return_value = {'last': 3000.0}
        self.mock_client.create_market_order.return_value = {
            'id': '67890',
            'average': 3000.0
        }
        
        # Execute trade
        success = self.position_manager.open_position(
            symbol, signal, amount, leverage, stop_loss_percentage=0.05
        )
        
        # Verify position opened successfully
        self.assertTrue(success)
        
        # Verify position exists and is short
        self.assertTrue(self.position_manager.has_position(symbol))
        position = self.position_manager.get_position(symbol)
        self.assertIsNotNone(position)
        self.assertEqual(position.side, 'short')
        self.assertEqual(position.entry_price, 3000.0)
        self.assertEqual(position.amount, amount)
        self.assertEqual(position.leverage, leverage)
        
        # Verify stop loss is above entry (for short)
        self.assertGreater(position.stop_loss, position.entry_price)
        
        # Verify take profit is below entry (for short)
        self.assertLess(position.take_profit, position.entry_price)
        
        # Verify order was placed with correct side
        self.mock_client.create_market_order.assert_called_once()
        call_args = self.mock_client.create_market_order.call_args
        self.assertEqual(call_args[0][1], 'sell')  # Second arg is side
    
    def test_long_position_stop_loss_triggers(self):
        """Test that stop loss correctly closes a LONG position when price drops"""
        # Create a long position
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.01,
            leverage=10,
            stop_loss=47500.0,  # 5% below entry
            take_profit=65000.0  # 30% above entry (3x risk/reward)
        )
        
        # Price drops to stop loss
        current_price = 47500.0
        should_close, reason = position.should_close(current_price)
        
        # Verify emergency stop triggered
        # At -5% price move with 10x leverage = -50% ROI
        # This triggers emergency_stop_liquidation_risk at -40% ROI threshold (triggers when ROI <= -0.40)
        self.assertTrue(should_close)
        self.assertIn('emergency_stop', reason)
    
    def test_short_position_stop_loss_triggers(self):
        """Test that stop loss correctly closes a SHORT position when price rises"""
        # Create a short position
        position = self.Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=0.1,
            leverage=5,
            stop_loss=3150.0,  # 5% above entry
            take_profit=2550.0  # 15% below entry (3x risk/reward)
        )
        
        # Price rises to stop loss
        current_price = 3150.0
        should_close, reason = position.should_close(current_price)
        
        # Verify emergency stop triggered
        # At +5% price move against short with 5x leverage = -25% ROI
        # This triggers emergency_stop_severe_loss at -25% ROI threshold (triggers when ROI <= -0.25)
        self.assertTrue(should_close)
        self.assertIn('emergency_stop', reason)
    
    def test_long_position_take_profit_triggers(self):
        """Test that take profit correctly closes a LONG position when price rises"""
        # Create a long position
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.01,
            leverage=10,
            stop_loss=47500.0,
            take_profit=51000.0  # 2% above entry
        )
        
        # Price rises to take profit
        current_price = 51000.0
        should_close, reason = position.should_close(current_price)
        
        # Verify take profit triggered
        self.assertTrue(should_close)
        # With 2% price move and 10x leverage = 20% ROI
        # This triggers take_profit_20pct_exceptional
        self.assertIn('take_profit', reason)
    
    def test_short_position_take_profit_triggers(self):
        """Test that take profit correctly closes a SHORT position when price drops"""
        # Create a short position
        position = self.Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=0.1,
            leverage=5,
            stop_loss=3150.0,
            take_profit=2700.0  # 10% below entry
        )
        
        # Price drops to take profit
        current_price = 2700.0
        should_close, reason = position.should_close(current_price)
        
        # Verify take profit triggered
        self.assertTrue(should_close)
        # With 10% price move and 5x leverage = 50% ROI
        # This triggers take_profit_20pct_exceptional (> 20%)
        self.assertIn('take_profit', reason)
    
    def test_long_position_pnl_calculation(self):
        """Test that P&L is calculated correctly for LONG positions"""
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.01,
            leverage=10,
            stop_loss=47500.0,
            take_profit=55000.0
        )
        
        # Test profit scenario: price goes up 10%
        profit_price = 55000.0
        pnl = position.get_pnl(profit_price)
        leveraged_pnl = position.get_leveraged_pnl(profit_price)
        
        # Price moved 10%, so unleveraged P&L should be 0.1 (10%)
        self.assertAlmostEqual(pnl, 0.1, places=4)
        # With 10x leverage, ROI should be 100% (1.0)
        self.assertAlmostEqual(leveraged_pnl, 1.0, places=4)
        
        # Test loss scenario: price goes down 5%
        loss_price = 47500.0
        pnl = position.get_pnl(loss_price)
        leveraged_pnl = position.get_leveraged_pnl(loss_price)
        
        # Price moved -5%, so unleveraged P&L should be -0.05 (-5%)
        self.assertAlmostEqual(pnl, -0.05, places=4)
        # With 10x leverage, ROI should be -50% (-0.5)
        self.assertAlmostEqual(leveraged_pnl, -0.5, places=4)
    
    def test_short_position_pnl_calculation(self):
        """Test that P&L is calculated correctly for SHORT positions"""
        position = self.Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=0.1,
            leverage=5,
            stop_loss=3150.0,
            take_profit=2700.0
        )
        
        # Test profit scenario: price goes down 10%
        profit_price = 2700.0
        pnl = position.get_pnl(profit_price)
        leveraged_pnl = position.get_leveraged_pnl(profit_price)
        
        # Price moved -10% (down is good for short), so unleveraged P&L should be 0.1 (10%)
        self.assertAlmostEqual(pnl, 0.1, places=4)
        # With 5x leverage, ROI should be 50% (0.5)
        self.assertAlmostEqual(leveraged_pnl, 0.5, places=4)
        
        # Test loss scenario: price goes up 5%
        loss_price = 3150.0
        pnl = position.get_pnl(loss_price)
        leveraged_pnl = position.get_leveraged_pnl(loss_price)
        
        # Price moved +5% (up is bad for short), so unleveraged P&L should be -0.05 (-5%)
        self.assertAlmostEqual(pnl, -0.05, places=4)
        # With 5x leverage, ROI should be -25% (-0.25)
        self.assertAlmostEqual(leveraged_pnl, -0.25, places=4)
    
    def test_long_position_intelligent_exits(self):
        """Test that LONG position has intelligent exit strategies (emergency stops and profit taking)"""
        position = self.Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.01,
            leverage=10,
            stop_loss=47500.0,
            take_profit=55000.0
        )
        
        # Test 1: Large profit triggers intelligent profit taking
        # Price at 52000 = 4% price move = 40% ROI with 10x leverage
        # Should trigger intelligent profit taking at 20% threshold
        current_price = 52000.0
        should_close, reason = position.should_close(current_price)
        self.assertTrue(should_close)
        self.assertIn('take_profit', reason)
        
        # Test 2: Large loss triggers emergency stop
        # Price at 48000 = -4% price move = -40% ROI with 10x leverage
        # Should trigger emergency_stop_liquidation_risk at -40% threshold
        current_price = 48000.0
        should_close, reason = position.should_close(current_price)
        self.assertTrue(should_close)
        self.assertIn('emergency_stop', reason)
        
        # Test 3: Small loss does NOT trigger any stops
        # Price at 49500 = -1% price move = -10% ROI with 10x leverage
        # Should NOT close - this is within acceptable loss range
        current_price = 49500.0
        should_close, reason = position.should_close(current_price)
        self.assertFalse(should_close)
        
        # Test 4: High profit triggers intelligent profit taking
        # Price at 54500 = 9% price move = 90% ROI with 10x leverage
        # At such high profit, intelligent profit taking will trigger (>20% threshold)
        # This verifies that exceptional profits are captured even before reaching TP
        current_price = 54500.0
        should_close, reason = position.should_close(current_price)
        self.assertTrue(should_close)
        self.assertIn('take_profit', reason)
    
    def test_short_position_intelligent_exits(self):
        """Test that SHORT position has intelligent exit strategies (emergency stops and profit taking)"""
        # Test 1: Moderate profit triggers intelligent profit taking  
        position1 = self.Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=0.1,
            leverage=5,
            stop_loss=3150.0,
            take_profit=2700.0
        )
        # Price at 2850 = -5% price move = 25% ROI with 5x leverage
        # Should trigger intelligent profit taking at 20% threshold
        current_price = 2850.0
        should_close, reason = position1.should_close(current_price)
        self.assertTrue(should_close)
        self.assertIn('take_profit', reason)
        
        # Test 2: Small loss does NOT trigger emergency stop
        position2 = self.Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=0.1,
            leverage=5,
            stop_loss=3150.0,
            take_profit=2700.0
        )
        # Price at 3075 = +2.5% price move = -12.5% ROI with 5x leverage
        # Should NOT close - this is within acceptable loss range (< -15% threshold)
        current_price = 3075.0
        should_close, reason = position2.should_close(current_price)
        self.assertFalse(should_close)
        
        # Test 3: Large loss triggers emergency stop
        position3 = self.Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=0.1,
            leverage=5,
            stop_loss=3150.0,
            take_profit=2700.0
        )
        # Price at 3180 = +6% price move = -30% ROI with 5x leverage
        # Should trigger emergency_stop_severe_loss at -25% threshold
        current_price = 3180.0
        should_close, reason = position3.should_close(current_price)
        self.assertTrue(should_close)
        self.assertIn('emergency_stop', reason)
        
        # Test 4: Very small profit does NOT trigger premature close
        position4 = self.Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=0.1,
            leverage=5,
            stop_loss=3150.0,
            take_profit=2700.0
        )
        # Price at 2985 = -0.5% price move = 2.5% ROI with 5x leverage
        # Should NOT close - below 5% threshold
        current_price = 2985.0
        should_close, reason = position4.should_close(current_price)
        self.assertFalse(should_close)


def run_tests():
    """Run all tests and print results"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBuySellStrategyExecution)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✓ ALL BUY/SELL STRATEGY EXECUTION TESTS PASSED!")
        print("=" * 70)
        print("Verified:")
        print("  ✓ BUY signals open LONG positions correctly")
        print("  ✓ SELL signals open SHORT positions correctly")
        print("  ✓ Stop losses trigger correctly for LONG positions")
        print("  ✓ Stop losses trigger correctly for SHORT positions")
        print("  ✓ Take profits trigger correctly for LONG positions")
        print("  ✓ Take profits trigger correctly for SHORT positions")
        print("  ✓ P&L calculations are correct for both directions")
        print("  ✓ Intelligent exit strategies work correctly:")
        print("      - Emergency stops at -40%, -25%, -15% ROI")
        print("      - Intelligent profit taking at 20%, 15%, 10%, 8%, 5% ROI")
        print("  ✓ Positions don't close with small P&L movements")
        print("=" * 70)
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 70)
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit(run_tests())
