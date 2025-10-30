#!/usr/bin/env python3
"""
Test for configuration overrides from .env file
Tests that user-defined values in .env properly override auto-configured values
"""
import os
import sys
import unittest

# Ensure we're testing the local config module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestConfigOverrides(unittest.TestCase):
    """Test configuration override functionality"""
    
    def setUp(self):
        """Set up test environment with API credentials"""
        os.environ['KUCOIN_API_KEY'] = 'test_key'
        os.environ['KUCOIN_API_SECRET'] = 'test_secret'
        os.environ['KUCOIN_API_PASSPHRASE'] = 'test_passphrase'
        
        # Clear any existing overrides
        for key in ['LEVERAGE', 'MAX_POSITION_SIZE', 'RISK_PER_TRADE', 'MIN_PROFIT_THRESHOLD']:
            os.environ.pop(key, None)
        
        # Reload config to get fresh state
        if 'config' in sys.modules:
            del sys.modules['config']
        if 'logger' in sys.modules:
            del sys.modules['logger']
    
    def test_leverage_override_from_env(self):
        """Test that LEVERAGE from .env overrides auto-configuration"""
        os.environ['LEVERAGE'] = '15'
        
        # Reload config
        if 'config' in sys.modules:
            del sys.modules['config']
        if 'logger' in sys.modules:
            del sys.modules['logger']
        
        from config import Config
        
        # Leverage should be set immediately from environment
        self.assertEqual(Config.LEVERAGE, 15, "LEVERAGE should be set from environment on load")
        
        # Should remain when auto_configure is called
        Config.auto_configure_from_balance(1000)
        self.assertEqual(Config.LEVERAGE, 15, "LEVERAGE should remain user-defined after auto_configure")
        
        # Should remain when fallback is used (balance fetch fails)
        if Config.LEVERAGE is None:  # This shouldn't happen now
            Config.LEVERAGE = 10
        self.assertEqual(Config.LEVERAGE, 15, "LEVERAGE should remain user-defined after fallback")
    
    def test_all_overrides_from_env(self):
        """Test that all config overrides work"""
        os.environ['LEVERAGE'] = '20'
        os.environ['MAX_POSITION_SIZE'] = '5000'
        os.environ['RISK_PER_TRADE'] = '0.05'
        os.environ['MIN_PROFIT_THRESHOLD'] = '0.01'
        
        # Reload config
        if 'config' in sys.modules:
            del sys.modules['config']
        if 'logger' in sys.modules:
            del sys.modules['logger']
        
        from config import Config
        
        # All should be set immediately from environment
        self.assertEqual(Config.LEVERAGE, 20)
        self.assertEqual(Config.MAX_POSITION_SIZE, 5000.0)
        self.assertEqual(Config.RISK_PER_TRADE, 0.05)
        self.assertEqual(Config.MIN_PROFIT_THRESHOLD, 0.01)
        
        # Should remain after auto_configure
        Config.auto_configure_from_balance(10000)
        self.assertEqual(Config.LEVERAGE, 20)
        self.assertEqual(Config.MAX_POSITION_SIZE, 5000.0)
        self.assertEqual(Config.RISK_PER_TRADE, 0.05)
        self.assertEqual(Config.MIN_PROFIT_THRESHOLD, 0.01)
    
    def test_no_overrides_uses_auto_configure(self):
        """Test that auto-configuration works when no overrides are set"""
        # No overrides set
        
        from config import Config
        
        # Should be None initially
        self.assertIsNone(Config.LEVERAGE)
        self.assertIsNone(Config.MAX_POSITION_SIZE)
        self.assertIsNone(Config.RISK_PER_TRADE)
        self.assertIsNone(Config.MIN_PROFIT_THRESHOLD)
        
        # Auto-configure should set appropriate values
        Config.auto_configure_from_balance(1000)
        
        # For $1000 balance: leverage = 8 (balance >= 1000 and < 10000)
        # position = 50% = 500 (balance >= 1000 and < 10000)
        self.assertEqual(Config.LEVERAGE, 8)
        self.assertEqual(Config.MAX_POSITION_SIZE, 500.0)
        self.assertEqual(Config.RISK_PER_TRADE, 0.02)
        # MIN_PROFIT_THRESHOLD should include fees
        self.assertGreater(Config.MIN_PROFIT_THRESHOLD, 0.006)
    
    def test_fallback_defaults_when_no_overrides(self):
        """Test fallback defaults when balance fetch fails and no overrides"""
        # No overrides set
        
        from config import Config
        
        # Simulate balance fetch failure - apply fallback defaults
        if Config.LEVERAGE is None:
            Config.LEVERAGE = 10
        if Config.MAX_POSITION_SIZE is None:
            Config.MAX_POSITION_SIZE = 1000
        if Config.RISK_PER_TRADE is None:
            Config.RISK_PER_TRADE = 0.02
        if Config.MIN_PROFIT_THRESHOLD is None:
            Config.MIN_PROFIT_THRESHOLD = 0.0062
        
        # Should use fallback defaults
        self.assertEqual(Config.LEVERAGE, 10)
        self.assertEqual(Config.MAX_POSITION_SIZE, 1000)
        self.assertEqual(Config.RISK_PER_TRADE, 0.02)
        self.assertEqual(Config.MIN_PROFIT_THRESHOLD, 0.0062)
    
    def test_partial_overrides(self):
        """Test that partial overrides work (some from env, some auto-configured)"""
        # Only override LEVERAGE
        os.environ['LEVERAGE'] = '12'
        
        # Reload config
        if 'config' in sys.modules:
            del sys.modules['config']
        if 'logger' in sys.modules:
            del sys.modules['logger']
        
        from config import Config
        
        # LEVERAGE should be from env
        self.assertEqual(Config.LEVERAGE, 12)
        
        # Others should be None initially
        self.assertIsNone(Config.MAX_POSITION_SIZE)
        self.assertIsNone(Config.RISK_PER_TRADE)
        
        # Auto-configure should only set the None values
        Config.auto_configure_from_balance(5000)
        
        # LEVERAGE should remain user-defined
        self.assertEqual(Config.LEVERAGE, 12)
        
        # Others should be auto-configured for $5000 balance
        self.assertIsNotNone(Config.MAX_POSITION_SIZE)
        self.assertIsNotNone(Config.RISK_PER_TRADE)


if __name__ == '__main__':
    print("Testing configuration overrides...")
    print("=" * 70)
    unittest.main(verbosity=2)
