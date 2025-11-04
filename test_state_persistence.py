"""
Test state persistence for key components
Ensures that all components can save and load their state correctly
"""
import unittest
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch
from datetime import datetime

# Components to test
from advanced_analytics import AdvancedAnalytics
from risk_manager import RiskManager
from attention_features_2025 import AttentionFeatureSelector


class TestStatePersistence(unittest.TestCase):
    """Test state persistence for all key components"""

    def setUp(self):
        """Set up test environment with temp directory"""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_models_dir = 'models'

        # Temporarily override models directory
        self.models_backup = None
        if os.path.exists('models'):
            self.models_backup = tempfile.mkdtemp(prefix='models_backup_')
            shutil.move('models', self.models_backup)

        # Create new models directory for testing
        os.makedirs('models', exist_ok=True)

    def tearDown(self):
        """Clean up test environment"""
        # Remove test models directory
        if os.path.exists('models'):
            shutil.rmtree('models')

        # Restore original models directory if it existed
        if self.models_backup and os.path.exists(self.models_backup):
            shutil.move(self.models_backup, 'models')

        # Clean up temp directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_analytics_save_and_load(self):
        """Test that AdvancedAnalytics can save and load state"""
        # Create analytics instance and record some data
        analytics1 = AdvancedAnalytics()

        # Record some trades
        analytics1.record_trade({
            'symbol': 'BTC-USDT',
            'side': 'long',
            'entry_price': 50000,
            'exit_price': 51000,
            'pnl': 0.02,
            'pnl_pct': 0.02,
            'duration': 60,
            'leverage': 10
        })

        analytics1.record_trade({
            'symbol': 'ETH-USDT',
            'side': 'short',
            'entry_price': 3000,
            'exit_price': 2950,
            'pnl': 0.015,
            'pnl_pct': 0.015,
            'duration': 45,
            'leverage': 10
        })

        # Record equity
        analytics1.record_equity(10000)
        analytics1.record_equity(10200)
        analytics1.record_equity(10350)

        # Save state
        analytics1.save_state()

        # Verify file exists
        self.assertTrue(os.path.exists(analytics1.state_path))

        # Create new instance and verify data was loaded
        analytics2 = AdvancedAnalytics()

        # Check trade history
        self.assertEqual(len(analytics2.trade_history), 2)
        self.assertEqual(analytics2.trade_history[0]['symbol'], 'BTC-USDT')
        self.assertEqual(analytics2.trade_history[1]['symbol'], 'ETH-USDT')

        # Check equity curve
        self.assertEqual(len(analytics2.equity_curve), 3)
        self.assertEqual(analytics2.equity_curve[0]['balance'], 10000)
        self.assertEqual(analytics2.equity_curve[2]['balance'], 10350)

    def test_risk_manager_save_and_load(self):
        """Test that RiskManager can save and load state"""
        # Create risk manager instance
        risk1 = RiskManager(
            max_position_size=1000,
            risk_per_trade=0.02,
            max_open_positions=5
        )

        # Update some state
        risk1.peak_balance = 10000
        risk1.current_drawdown = -0.05
        risk1.total_trades = 25
        risk1.wins = 15
        risk1.losses = 10
        risk1.total_profit = 0.75
        risk1.total_loss = 0.45
        risk1.win_streak = 3
        risk1.loss_streak = 0
        risk1.recent_trades = [0.01, 0.02, -0.01, 0.015, 0.03]

        # Save state
        risk1.save_state()

        # Verify file exists
        self.assertTrue(os.path.exists(risk1.state_path))

        # Create new instance and verify data was loaded
        risk2 = RiskManager(
            max_position_size=1000,
            risk_per_trade=0.02,
            max_open_positions=5
        )

        # Check state
        self.assertEqual(risk2.peak_balance, 10000)
        self.assertEqual(risk2.current_drawdown, -0.05)
        self.assertEqual(risk2.total_trades, 25)
        self.assertEqual(risk2.wins, 15)
        self.assertEqual(risk2.losses, 10)
        self.assertAlmostEqual(risk2.total_profit, 0.75, places=6)
        self.assertAlmostEqual(risk2.total_loss, 0.45, places=6)
        self.assertEqual(risk2.win_streak, 3)
        self.assertEqual(risk2.loss_streak, 0)
        self.assertEqual(len(risk2.recent_trades), 5)
        self.assertAlmostEqual(risk2.recent_trades[-1], 0.03, places=6)

        # Check calculated metrics
        self.assertAlmostEqual(risk2.get_win_rate(), 15/25, places=4)

    def test_attention_weights_save_and_load(self):
        """Test that AttentionFeatureSelector can save and load weights"""
        import numpy as np

        # Create attention selector
        attention1 = AttentionFeatureSelector(n_features=31)

        # Modify weights
        attention1.attention_weights = np.random.rand(31)
        attention1.attention_weights /= attention1.attention_weights.sum()  # Normalize

        # Save weights
        attention1.save_weights()

        # Verify file exists
        self.assertTrue(os.path.exists('models/attention_weights.npy'))

        # Create new instance and verify weights were loaded
        attention2 = AttentionFeatureSelector(n_features=31)

        # Check weights match
        np.testing.assert_array_almost_equal(
            attention1.attention_weights,
            attention2.attention_weights,
            decimal=6
        )

    def test_periodic_save_doesnt_crash(self):
        """Test that periodic saves handle errors gracefully"""
        # Test with invalid path (to trigger error handling)
        analytics = AdvancedAnalytics()
        original_path = analytics.state_path
        analytics.state_path = '/invalid/path/that/doesnt/exist/state.pkl'

        # Should not raise exception, just log error
        analytics.save_state()

        # Restore path
        analytics.state_path = original_path

    def test_load_handles_missing_files(self):
        """Test that load methods handle missing files gracefully"""
        # Remove any existing state files
        for file in ['models/analytics_state.pkl', 'models/risk_manager_state.pkl', 'models/attention_weights.npy']:
            if os.path.exists(file):
                os.remove(file)

        # Create instances - should not crash
        analytics = AdvancedAnalytics()
        risk = RiskManager(1000, 0.02, 5)
        attention = AttentionFeatureSelector(31)

        # Verify default state
        self.assertEqual(len(analytics.trade_history), 0)
        self.assertEqual(len(analytics.equity_curve), 0)
        self.assertEqual(risk.total_trades, 0)
        self.assertEqual(len(attention.attention_weights), 31)


if __name__ == '__main__':
    unittest.main()
