#!/usr/bin/env python3
"""
Test for dynamic position sizing based on available balance
Ensures position sizing always uses current balance, never a fixed amount
"""
import os
import sys
import unittest
from unittest.mock import MagicMock

# Ensure we're testing the local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up minimal environment for testing
os.environ['KUCOIN_API_KEY'] = 'test_key'
os.environ['KUCOIN_API_SECRET'] = 'test_secret'
os.environ['KUCOIN_API_PASSPHRASE'] = 'test_passphrase'


class TestDynamicPositionSizing(unittest.TestCase):
    """Test dynamic position sizing based on current balance"""
    
    def setUp(self):
        """Set up test environment"""
        from risk_manager import RiskManager
        
        # Create risk manager with initial values
        self.risk_manager = RiskManager(
            max_position_size=1000,  # This should be overridden dynamically
            risk_per_trade=0.02,
            max_open_positions=3
        )
    
    def test_position_size_scales_with_balance_no_override(self):
        """Test that position size scales with balance when no override is set"""
        # Clear any override
        from config import Config
        Config._MAX_POSITION_SIZE_OVERRIDE = None
        
        # Test with small balance ($500)
        # Expected max position: 500 * 0.4 = 200 (small account tier)
        position_size_small = self.risk_manager.calculate_position_size(
            balance=500,
            entry_price=100,
            stop_loss_price=95,  # 5% stop loss
            leverage=10
        )
        
        # Expected calculation:
        # risk_amount = 500 * 0.02 = 10
        # price_distance = 5/100 = 0.05
        # position_value = 10 / 0.05 = 200
        # max_position for 500 balance = 500 * 0.4 = 200
        # capped position_value = min(200, 200) = 200
        # position_size = 200 / 100 = 2
        self.assertAlmostEqual(position_size_small, 2.0, places=2)
        
        # Test with larger balance ($5000)
        # Expected max position: 5000 * 0.5 = 2500 (medium account tier)
        position_size_large = self.risk_manager.calculate_position_size(
            balance=5000,
            entry_price=100,
            stop_loss_price=95,  # 5% stop loss
            leverage=10
        )
        
        # Expected calculation:
        # risk_amount = 5000 * 0.02 = 100
        # price_distance = 5/100 = 0.05
        # position_value = 100 / 0.05 = 2000
        # max_position for 5000 balance = 5000 * 0.5 = 2500
        # capped position_value = min(2000, 2500) = 2000
        # position_size = 2000 / 100 = 20
        self.assertAlmostEqual(position_size_large, 20.0, places=2)
        
        # Verify that position size scales with balance (10x balance = 10x position)
        self.assertAlmostEqual(position_size_large / position_size_small, 10.0, places=1)
    
    def test_position_size_respects_fixed_override(self):
        """Test that position size respects fixed MAX_POSITION_SIZE override"""
        from config import Config
        
        # Set a fixed override
        Config._MAX_POSITION_SIZE_OVERRIDE = "500"
        
        # Even with large balance, should be capped at override value
        position_size = self.risk_manager.calculate_position_size(
            balance=10000,  # Large balance
            entry_price=100,
            stop_loss_price=95,  # 5% stop loss
            leverage=10
        )
        
        # Expected calculation:
        # risk_amount = 10000 * 0.02 = 200
        # price_distance = 5/100 = 0.05
        # position_value = 200 / 0.05 = 4000
        # But max_position with override = 500 (fixed)
        # capped position_value = min(4000, 500) = 500
        # position_size = 500 / 100 = 5
        self.assertAlmostEqual(position_size, 5.0, places=2)
        
        # Clean up
        Config._MAX_POSITION_SIZE_OVERRIDE = None
    
    def test_balance_depletion_reduces_position_size(self):
        """Test that position size automatically reduces as balance is depleted"""
        from config import Config
        Config._MAX_POSITION_SIZE_OVERRIDE = None
        
        # Start with good balance
        initial_balance = 2000
        position_size_initial = self.risk_manager.calculate_position_size(
            balance=initial_balance,
            entry_price=100,
            stop_loss_price=95,
            leverage=10
        )
        
        # After losses, balance is depleted
        depleted_balance = 500  # Lost 75% of capital
        position_size_depleted = self.risk_manager.calculate_position_size(
            balance=depleted_balance,
            entry_price=100,
            stop_loss_price=95,
            leverage=10
        )
        
        # Position size should reduce proportionally with balance
        # This ensures we're always using available balance, not a fixed amount
        expected_ratio = depleted_balance / initial_balance  # 0.25
        actual_ratio = position_size_depleted / position_size_initial
        
        self.assertAlmostEqual(actual_ratio, expected_ratio, places=1,
                              msg="Position size should scale with balance changes")
    
    def test_balance_growth_increases_position_size(self):
        """Test that position size automatically increases as balance grows"""
        from config import Config
        Config._MAX_POSITION_SIZE_OVERRIDE = None
        
        # Start with small balance
        initial_balance = 500
        position_size_initial = self.risk_manager.calculate_position_size(
            balance=initial_balance,
            entry_price=100,
            stop_loss_price=95,
            leverage=10
        )
        
        # After profits, balance grows
        grown_balance = 2000  # 4x growth
        position_size_grown = self.risk_manager.calculate_position_size(
            balance=grown_balance,
            entry_price=100,
            stop_loss_price=95,
            leverage=10
        )
        
        # Position size should increase with balance
        # (not exact 4x due to tier changes, but should be significantly larger)
        self.assertGreater(position_size_grown, position_size_initial * 2,
                          msg="Position size should increase significantly with balance growth")
    
    def test_dynamic_max_position_size_calculation(self):
        """Test the internal dynamic max position size calculation"""
        from config import Config
        Config._MAX_POSITION_SIZE_OVERRIDE = None
        
        # Test different balance tiers
        test_cases = [
            (50, 15),      # Micro: 50 * 0.3 = 15
            (500, 200),    # Small: 500 * 0.4 = 200
            (5000, 2500),  # Medium: 5000 * 0.5 = 2500
            (20000, 12000) # Large: 20000 * 0.6 = 12000
        ]
        
        for balance, expected_max in test_cases:
            max_pos = self.risk_manager._calculate_max_position_size_for_balance(balance)
            self.assertAlmostEqual(max_pos, expected_max, places=0,
                                  msg=f"Max position size for ${balance} should be ${expected_max}")


class TestLeverageOverride(unittest.TestCase):
    """Test that leverage override works correctly"""
    
    def _reload_config(self):
        """Helper to reload config"""
        if 'config' in sys.modules:
            del sys.modules['config']
        if 'logger' in sys.modules:
            del sys.modules['logger']
    
    def setUp(self):
        """Set up test environment"""
        os.environ['KUCOIN_API_KEY'] = 'test_key'
        os.environ['KUCOIN_API_SECRET'] = 'test_secret'
        os.environ['KUCOIN_API_PASSPHRASE'] = 'test_passphrase'
        
        # Clear leverage override
        os.environ.pop('LEVERAGE', None)
        self._reload_config()
    
    def test_leverage_override_persists(self):
        """Test that LEVERAGE override persists through auto_configure"""
        os.environ['LEVERAGE'] = '15'
        self._reload_config()
        
        from config import Config
        
        # Should be set immediately
        self.assertEqual(Config.LEVERAGE, 15)
        
        # Should persist after auto_configure with different balances
        Config.auto_configure_from_balance(100)
        self.assertEqual(Config.LEVERAGE, 15, "Leverage should stay at override value")
        
        Config.auto_configure_from_balance(10000)
        self.assertEqual(Config.LEVERAGE, 15, "Leverage should stay at override value")
    
    def test_leverage_auto_configures_without_override(self):
        """Test that leverage auto-configures when no override is set"""
        # No override set
        self._reload_config()
        
        from config import Config
        
        # Should be None initially
        self.assertIsNone(Config.LEVERAGE)
        
        # Should auto-configure based on balance
        Config.auto_configure_from_balance(5000)
        self.assertEqual(Config.LEVERAGE, 8, "Should auto-configure to 8x for $5000")


if __name__ == '__main__':
    print("Testing dynamic position sizing and leverage override...")
    print("=" * 70)
    unittest.main(verbosity=2)
