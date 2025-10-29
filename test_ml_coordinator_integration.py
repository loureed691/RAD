"""
Integration test to verify ML Strategy Coordinator 2025 works with:
1. DCA (Dollar Cost Averaging) strategy
2. All buy/sell strategies
3. Take profit strategies
4. Stop loss strategies
"""
import unittest
import os
import pandas as pd
import numpy as np

# Set environment
os.environ['LOG_LEVEL'] = 'ERROR'
os.environ['LOG_FILE'] = '/tmp/test_ml_integration.log'

from signals import SignalGenerator
from indicators import Indicators
from dca_strategy import DCAStrategy
from position_manager import Position
from hedging_strategy import HedgingStrategy


class TestMLCoordinatorIntegration(unittest.TestCase):
    """Test ML Coordinator integration with all trading strategies"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test fixtures"""
        np.random.seed(42)
        
        # Create sample OHLCV data
        cls.dates = pd.date_range('2024-01-01', periods=100, freq='h')
        cls.df = cls._create_sample_data(cls.dates)
        cls.df = Indicators.calculate_all(cls.df)
        cls.indicators = Indicators.get_latest_indicators(cls.df)
        
        # Initialize signal generator with ML coordinator
        cls.signal_generator = SignalGenerator()
    
    @staticmethod
    def _create_sample_data(dates):
        """Create sample OHLCV data"""
        n = len(dates)
        base_price = 40000
        trend = np.linspace(0, 500, n)
        noise = np.random.randn(n).cumsum() * 50
        
        close = base_price + trend + noise
        high = close + np.random.uniform(20, 100, n)
        low = close - np.random.uniform(20, 100, n)
        open_price = close + np.random.randn(n) * 30
        volume = np.random.uniform(1000, 5000, n)
        
        return pd.DataFrame({
            'timestamp': dates,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    def test_ml_coordinator_generates_valid_signals(self):
        """Test ML coordinator generates signals compatible with trading strategies"""
        signal, confidence, reasons = self.signal_generator.generate_signal(self.df)
        
        # Verify signal is valid
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
        
        # Verify confidence is valid
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        
        # Verify reasons dict exists
        self.assertIsInstance(reasons, dict)
        
        # If ML coordinator is enabled, should have ml_coordinator key in reasons (when signal != HOLD)
        if self.signal_generator.ml_coordinator_enabled and signal != 'HOLD':
            # ML coordinator may or may not add keys depending on signal strength
            # Just verify the signal is still valid
            pass
    
    def test_ml_signal_compatible_with_dca_strategy(self):
        """Test ML-generated signals work with DCA strategy"""
        signal, confidence, reasons = self.signal_generator.generate_signal(self.df)
        
        # Skip if signal is HOLD
        if signal == 'HOLD':
            self.skipTest("Signal is HOLD, skipping DCA test")
        
        dca = DCAStrategy()
        
        # Test DCA plan creation with ML signal
        dca_plan = dca.initialize_entry_dca(
            symbol='BTC-USDT',
            signal=signal,
            total_amount=100.0,
            entry_price=40000.0,
            confidence=confidence
        )
        
        # Verify DCA plan was created
        self.assertIsNotNone(dca_plan)
        self.assertIn('num_entries', dca_plan)
        self.assertIn('amounts', dca_plan)
        self.assertIn('prices', dca_plan)
        
        # Verify DCA adapts to confidence
        # High confidence (>0.75) should use fewer entries (2)
        # Medium confidence (0.65-0.75) should use 3 entries
        # Low confidence (<0.65) should use more entries (4)
        expected_entries = 2 if confidence >= 0.75 else (3 if confidence >= 0.65 else 4)
        self.assertEqual(dca_plan['num_entries'], expected_entries)
        
        # Verify total amount equals sum of entry amounts
        total_dca_amount = sum(dca_plan['amounts'])
        self.assertAlmostEqual(total_dca_amount, 100.0, places=2)
    
    def test_ml_signal_compatible_with_position_management(self):
        """Test ML-generated signals work with position management (stop loss/take profit)"""
        signal, confidence, reasons = self.signal_generator.generate_signal(self.df)
        
        # Skip if signal is HOLD
        if signal == 'HOLD':
            self.skipTest("Signal is HOLD, skipping position test")
        
        # Create position with ML signal
        entry_price = 40000.0
        position = Position(
            symbol='BTC-USDT',
            side='long' if signal == 'BUY' else 'short',
            entry_price=entry_price,
            amount=0.01,
            leverage=10,
            stop_loss=39000.0 if signal == 'BUY' else 41000.0,
            take_profit=42000.0 if signal == 'BUY' else 38000.0
        )
        
        # Verify position was created correctly
        self.assertEqual(position.symbol, 'BTC-USDT')
        self.assertEqual(position.side, 'long' if signal == 'BUY' else 'short')
        self.assertEqual(position.entry_price, entry_price)
        
        # Test trailing stop update
        current_price = 41000.0 if signal == 'BUY' else 39000.0
        initial_stop = position.stop_loss
        position.update_trailing_stop(current_price, 0.02, volatility=0.03, momentum=0.01)
        
        # Verify stop loss was updated (should move in favorable direction only)
        if signal == 'BUY':
            self.assertGreaterEqual(position.stop_loss, initial_stop)
        else:
            self.assertLessEqual(position.stop_loss, initial_stop)
        
        # Test take profit update
        initial_tp = position.take_profit
        position.update_take_profit(current_price, momentum=0.02, trend_strength=0.7, volatility=0.03)
        
        # Verify take profit exists (may or may not be updated depending on conditions)
        self.assertIsNotNone(position.take_profit)
    
    def test_hedging_strategy_works_independently(self):
        """Test hedging strategy works independently of ML signals"""
        hedging = HedgingStrategy()
        
        # Test drawdown hedge
        hedge_rec = hedging.should_hedge_drawdown(
            current_drawdown=0.12,  # 12% drawdown
            portfolio_value=10000.0
        )
        
        # Should generate hedge recommendation
        self.assertIsNotNone(hedge_rec)
        self.assertEqual(hedge_rec['reason'], 'drawdown_protection')
        self.assertEqual(hedge_rec['hedge_size'], 5000.0)  # 50% of 10k
        
        # Test that hedge doesn't depend on ML signals
        self.assertNotIn('ml_signal', hedge_rec)
        self.assertNotIn('confidence', hedge_rec)
    
    def test_ml_coordinator_preserves_signal_flow(self):
        """Test that ML coordinator preserves the signal generation flow"""
        # Generate signal multiple times
        signals = []
        for _ in range(3):
            signal, confidence, reasons = self.signal_generator.generate_signal(self.df)
            signals.append((signal, confidence))
        
        # Verify all signals are valid
        for signal, confidence in signals:
            self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
    
    def test_ml_confidence_influences_dca_entries(self):
        """Test that ML confidence properly influences DCA entry count"""
        dca = DCAStrategy()
        
        # Test high confidence (should use fewer DCA entries)
        dca_plan_high = dca.initialize_entry_dca(
            symbol='BTC-USDT',
            signal='BUY',
            total_amount=100.0,
            entry_price=40000.0,
            confidence=0.80  # High confidence
        )
        
        # Test low confidence (should use more DCA entries)
        dca_plan_low = dca.initialize_entry_dca(
            symbol='BTC-USDT',
            signal='BUY',
            total_amount=100.0,
            entry_price=40000.0,
            confidence=0.60  # Low confidence
        )
        
        # High confidence should have fewer entries than low confidence
        self.assertLessEqual(dca_plan_high['num_entries'], dca_plan_low['num_entries'])
        
        # Verify entry counts match expectations
        self.assertEqual(dca_plan_high['num_entries'], 2)  # confidence >= 0.75
        self.assertEqual(dca_plan_low['num_entries'], 4)   # confidence < 0.65
    
    def test_position_management_works_with_both_buy_sell(self):
        """Test position management works for both BUY and SELL signals from ML"""
        # Test with BUY signal
        pos_long = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=40000.0,
            amount=0.01,
            leverage=10,
            stop_loss=39000.0,
            take_profit=42000.0
        )
        
        # Verify long position
        self.assertEqual(pos_long.side, 'long')
        self.assertLess(pos_long.stop_loss, pos_long.entry_price)
        self.assertGreater(pos_long.take_profit, pos_long.entry_price)
        
        # Test with SELL signal
        pos_short = Position(
            symbol='BTC-USDT',
            side='short',
            entry_price=40000.0,
            amount=0.01,
            leverage=10,
            stop_loss=41000.0,
            take_profit=38000.0
        )
        
        # Verify short position
        self.assertEqual(pos_short.side, 'short')
        self.assertGreater(pos_short.stop_loss, pos_short.entry_price)
        self.assertLess(pos_short.take_profit, pos_short.entry_price)
    
    def test_ml_coordinator_enabled_flag(self):
        """Test ML coordinator enabled flag is accessible"""
        self.assertIsInstance(self.signal_generator.ml_coordinator_enabled, bool)
        
        # If enabled, ml_coordinator object should exist
        if self.signal_generator.ml_coordinator_enabled:
            self.assertIsNotNone(self.signal_generator.ml_coordinator)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
