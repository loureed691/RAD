#!/usr/bin/env python3
"""
Test that LEVERAGE override from .env works correctly
This test verifies the leverage selection logic without needing full bot initialization
"""
import os
import sys
import unittest

# Ensure we're testing the local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestLeverageOverrideBehavior(unittest.TestCase):
    """Test that leverage override is properly applied"""
    
    def setUp(self):
        """Set up test environment"""
        # Set API credentials
        os.environ['KUCOIN_API_KEY'] = 'test_key'
        os.environ['KUCOIN_API_SECRET'] = 'test_secret'
        os.environ['KUCOIN_API_PASSPHRASE'] = 'test_passphrase'
        
        # Clear any existing leverage override
        os.environ.pop('LEVERAGE', None)
        
        # Reload modules to get fresh state
        for mod in ['config', 'logger']:
            if mod in sys.modules:
                del sys.modules[mod]
    
    def tearDown(self):
        """Clean up after tests"""
        os.environ.pop('LEVERAGE', None)
        for mod in ['config', 'logger']:
            if mod in sys.modules:
                del sys.modules[mod]
    
    def test_leverage_override_sets_flag(self):
        """Test that setting LEVERAGE in .env sets the _LEVERAGE_OVERRIDE flag"""
        # Set user-defined leverage
        os.environ['LEVERAGE'] = '12'
        
        from config import Config
        
        # Verify Config has the override set
        self.assertEqual(Config.LEVERAGE, 12)
        self.assertEqual(Config._LEVERAGE_OVERRIDE, '12')
        
        # Verify it persists after auto_configure
        Config.auto_configure_from_balance(1000)
        self.assertEqual(Config.LEVERAGE, 12)
        self.assertEqual(Config._LEVERAGE_OVERRIDE, '12')
    
    def test_no_override_flag_when_not_set(self):
        """Test that _LEVERAGE_OVERRIDE is None when LEVERAGE is not in .env"""
        from config import Config
        
        # Verify no override is set
        self.assertIsNone(Config._LEVERAGE_OVERRIDE)
        self.assertIsNone(Config.LEVERAGE)
        
        # After auto_configure, LEVERAGE is set but _LEVERAGE_OVERRIDE remains None
        Config.auto_configure_from_balance(1000)
        self.assertIsNone(Config._LEVERAGE_OVERRIDE)
        self.assertEqual(Config.LEVERAGE, 10)  # Fixed at 10x (not balance-based)
    
    def test_leverage_selection_logic_with_override(self):
        """Test the leverage selection logic when override is present"""
        os.environ['LEVERAGE'] = '12'
        
        from config import Config
        
        # Simulate the logic in bot.py
        risk_manager_calculated_leverage = 8  # Risk manager calculates 8x
        
        # This is the fix: when override is set, use it directly
        if Config._LEVERAGE_OVERRIDE:
            final_leverage = Config.LEVERAGE
        else:
            final_leverage = min(risk_manager_calculated_leverage, Config.LEVERAGE)
        
        # Should use user's 12x, NOT risk manager's 8x
        self.assertEqual(final_leverage, 12,
            "When LEVERAGE override is set, should use user's value directly")
    
    def test_leverage_selection_logic_without_override(self):
        """Test the leverage selection logic when no override is present"""
        from config import Config
        
        # Auto-configure for balance
        Config.auto_configure_from_balance(1000)
        
        # Simulate the logic in bot.py
        risk_manager_calculated_leverage = 6  # Risk manager calculates 6x
        
        # Without override, use dynamic calculation
        if Config._LEVERAGE_OVERRIDE:
            final_leverage = Config.LEVERAGE
        else:
            final_leverage = min(risk_manager_calculated_leverage, Config.LEVERAGE)
        
        # Should use risk manager's 6x (less than auto-configured max of 8x)
        self.assertEqual(final_leverage, 6,
            "Without override, should use min of risk manager and auto-configured")
    
    def test_leverage_override_with_different_values(self):
        """Test multiple different leverage override values"""
        test_values = ['5', '10', '15', '20']
        
        for value in test_values:
            # Clean up
            os.environ.pop('LEVERAGE', None)
            for mod in ['config', 'logger']:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            # Set override
            os.environ['LEVERAGE'] = value
            
            from config import Config
            
            # Verify override is used
            self.assertEqual(Config.LEVERAGE, int(value))
            self.assertEqual(Config._LEVERAGE_OVERRIDE, value)
            
            # Simulate bot logic
            risk_manager_leverage = 8
            if Config._LEVERAGE_OVERRIDE:
                final_leverage = Config.LEVERAGE
            else:
                final_leverage = min(risk_manager_leverage, Config.LEVERAGE)
            
            # Should always use user's value when override is set
            self.assertEqual(final_leverage, int(value),
                f"Override value {value}x should be used directly")


if __name__ == '__main__':
    print("Testing leverage override behavior...")
    print("=" * 70)
    unittest.main(verbosity=2)

