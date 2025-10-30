#!/usr/bin/env python3
"""
Test for robust leverage parsing from .env file
Tests that malformed values are handled gracefully without crashing
"""
import os
import sys
import unittest

# Ensure we're testing the local config module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestLeverageParsing(unittest.TestCase):
    """Test leverage parsing handles various input formats"""
    
    def _reload_config(self):
        """Helper method to reload config modules for clean test state"""
        if 'config' in sys.modules:
            del sys.modules['config']
        if 'logger' in sys.modules:
            del sys.modules['logger']
    
    def setUp(self):
        """Set up test environment with API credentials"""
        os.environ['KUCOIN_API_KEY'] = 'test_key'
        os.environ['KUCOIN_API_SECRET'] = 'test_secret'
        os.environ['KUCOIN_API_PASSPHRASE'] = 'test_passphrase'
        
        # Clear leverage override
        os.environ.pop('LEVERAGE', None)
        
        # Reload config to get fresh state
        self._reload_config()
    
    def test_clean_integer_value(self):
        """Test parsing of clean integer value"""
        os.environ['LEVERAGE'] = '10'
        self._reload_config()
        
        from config import Config
        self.assertEqual(Config.LEVERAGE, 10)
        
        # Should remain after auto_configure
        Config.auto_configure_from_balance(5000)
        self.assertEqual(Config.LEVERAGE, 10)
    
    def test_float_value_truncates(self):
        """Test that float values are converted to int (truncated)"""
        os.environ['LEVERAGE'] = '10.5'
        self._reload_config()
        
        from config import Config
        self.assertEqual(Config.LEVERAGE, 10, "10.5 should be truncated to 10")
        
        # Should remain after auto_configure
        Config.auto_configure_from_balance(5000)
        self.assertEqual(Config.LEVERAGE, 10)
    
    def test_float_value_rounds_down(self):
        """Test that float values like 10.9 are truncated to 10, not rounded"""
        os.environ['LEVERAGE'] = '10.9'
        self._reload_config()
        
        from config import Config
        self.assertEqual(Config.LEVERAGE, 10, "10.9 should be truncated to 10")
    
    def test_value_with_whitespace(self):
        """Test that values with leading/trailing whitespace work"""
        os.environ['LEVERAGE'] = ' 15 '
        self._reload_config()
        
        from config import Config
        self.assertEqual(Config.LEVERAGE, 15)
    
    def test_invalid_value_with_suffix(self):
        """Test that invalid values like '10x' are rejected and auto-configured"""
        os.environ['LEVERAGE'] = '10x'
        self._reload_config()
        
        from config import Config
        # Should be None initially (parsing failed)
        self.assertIsNone(Config.LEVERAGE)
        
        # Should auto-configure
        Config.auto_configure_from_balance(5000)
        self.assertEqual(Config.LEVERAGE, 8, "Should auto-configure to 8 for $5000 balance")
    
    def test_completely_invalid_value(self):
        """Test that completely invalid values are rejected"""
        os.environ['LEVERAGE'] = 'invalid'
        self._reload_config()
        
        from config import Config
        self.assertIsNone(Config.LEVERAGE)
        
        # Should auto-configure
        Config.auto_configure_from_balance(5000)
        self.assertEqual(Config.LEVERAGE, 8)
    
    def test_empty_string_value(self):
        """Test that empty string is treated as no override"""
        os.environ['LEVERAGE'] = ''
        self._reload_config()
        
        from config import Config
        self.assertIsNone(Config.LEVERAGE)
        
        # Should auto-configure
        Config.auto_configure_from_balance(5000)
        self.assertEqual(Config.LEVERAGE, 8)
    
    def test_no_leverage_env_var(self):
        """Test that missing LEVERAGE env var auto-configures"""
        # LEVERAGE not set in env
        self._reload_config()
        
        from config import Config
        self.assertIsNone(Config.LEVERAGE)
        
        # Should auto-configure
        Config.auto_configure_from_balance(5000)
        self.assertEqual(Config.LEVERAGE, 8)
    
    def test_max_position_size_float_parsing(self):
        """Test that MAX_POSITION_SIZE handles float values correctly"""
        os.environ['MAX_POSITION_SIZE'] = '1500.50'
        self._reload_config()
        
        from config import Config
        self.assertEqual(Config.MAX_POSITION_SIZE, 1500.50)
    
    def test_risk_per_trade_float_parsing(self):
        """Test that RISK_PER_TRADE handles float values correctly"""
        os.environ['RISK_PER_TRADE'] = '0.025'
        self._reload_config()
        
        from config import Config
        self.assertEqual(Config.RISK_PER_TRADE, 0.025)
    
    def test_invalid_max_position_size(self):
        """Test that invalid MAX_POSITION_SIZE is rejected"""
        os.environ['MAX_POSITION_SIZE'] = 'invalid'
        self._reload_config()
        
        from config import Config
        self.assertIsNone(Config.MAX_POSITION_SIZE)
        
        # Should auto-configure
        Config.auto_configure_from_balance(5000)
        self.assertEqual(Config.MAX_POSITION_SIZE, 2500.0, "Should be 50% of $5000")


if __name__ == '__main__':
    print("Testing leverage parsing robustness...")
    print("=" * 70)
    unittest.main(verbosity=2)
