"""
Test for concentration limit fix for 'unknown' category assets
"""
import unittest
from position_correlation import PositionCorrelationManager


class TestConcentrationLimitFix(unittest.TestCase):
    """Test concentration limit behavior for unknown category assets"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.correlation_manager = PositionCorrelationManager()
    
    def test_unknown_category_no_concentration_limit(self):
        """Test that 'unknown' category assets don't trigger concentration limits"""
        # Create existing positions with multiple unknown category assets
        # These should not trigger concentration limit since they're unrelated
        existing_positions = [
            {'symbol': 'XYZUSDT', 'value': 3000},  # Unknown asset 1
            {'symbol': 'ABCUSDT', 'value': 2000},  # Unknown asset 2
            {'symbol': 'DEFUSDT', 'value': 1000},  # Unknown asset 3
        ]
        
        # Total portfolio value
        portfolio_value = 10000  # 60% in 'unknown' category
        
        # Try to add another unknown asset
        new_symbol = 'GHIUSDT'  # Another unknown asset
        
        # Verify the category is 'unknown'
        self.assertEqual(
            self.correlation_manager.get_asset_category(new_symbol),
            'unknown'
        )
        
        # This should be allowed despite 'unknown' category being at 60%
        is_allowed, reason = self.correlation_manager.check_category_concentration(
            new_symbol, existing_positions, portfolio_value
        )
        
        self.assertTrue(
            is_allowed,
            f"Unknown category should not have concentration limits, but got: {reason}"
        )
    
    def test_known_category_concentration_limit(self):
        """Test that known category assets still have concentration limits"""
        # Create existing positions with assets in the same known category
        existing_positions = [
            {'symbol': 'BTCUSDT', 'value': 4500},  # BTC group
        ]
        
        # Total portfolio value
        portfolio_value = 10000  # 45% in btc_group
        
        # Try to add another BTC group asset (should fail)
        new_symbol = 'XBTUSD'
        
        # Verify the category is known
        category = self.correlation_manager.get_asset_category(new_symbol)
        self.assertEqual(category, 'btc_group')
        
        # This should NOT be allowed as btc_group is at 45% (over 40% limit)
        is_allowed, reason = self.correlation_manager.check_category_concentration(
            new_symbol, existing_positions, portfolio_value
        )
        
        self.assertFalse(
            is_allowed,
            "Known category over 40% should be blocked"
        )
        self.assertIn('btc_group', reason)
        self.assertIn('45.0%', reason)
    
    def test_unknown_asset_categorization(self):
        """Test that assets not in predefined lists are categorized as unknown"""
        unknown_symbols = ['XYZUSDT', 'ABC123USDT', 'NEWCOINUSDT']
        
        for symbol in unknown_symbols:
            category = self.correlation_manager.get_asset_category(symbol)
            self.assertEqual(
                category,
                'unknown',
                f"Symbol {symbol} should be categorized as 'unknown'"
            )
    
    def test_known_asset_categorization(self):
        """Test that predefined assets are categorized correctly"""
        test_cases = [
            ('BTCUSDT', 'btc_group'),
            ('ETHUSDT', 'eth_group'),
            ('SOLUSDT', 'layer1_high_cap'),
            ('UNIUSDT', 'defi_protocols'),
        ]
        
        for symbol, expected_category in test_cases:
            category = self.correlation_manager.get_asset_category(symbol)
            self.assertEqual(
                category,
                expected_category,
                f"Symbol {symbol} should be in category {expected_category}"
            )
    
    def test_mixed_categories_concentration(self):
        """Test concentration limits with mixed known and unknown categories"""
        # Mix of known and unknown assets
        existing_positions = [
            {'symbol': 'BTCUSDT', 'value': 2000},   # btc_group
            {'symbol': 'ETHUSDT', 'value': 2000},   # eth_group
            {'symbol': 'XYZUSDT', 'value': 2000},   # unknown
            {'symbol': 'ABCUSDT', 'value': 2000},   # unknown
        ]
        
        portfolio_value = 10000  # 40% unknown, 20% btc, 20% eth
        
        # Adding another unknown should work (40% unknown is OK since it's ignored)
        new_unknown = 'NEWUSDT'
        is_allowed, reason = self.correlation_manager.check_category_concentration(
            new_unknown, existing_positions, portfolio_value
        )
        self.assertTrue(is_allowed, f"Should allow unknown asset: {reason}")
        
        # Adding another BTC should work (only 20% currently)
        new_btc = 'XBTUSD'
        is_allowed, reason = self.correlation_manager.check_category_concentration(
            new_btc, existing_positions, portfolio_value
        )
        self.assertTrue(is_allowed, f"Should allow BTC asset at 20%: {reason}")

if __name__ == '__main__':
    unittest.main()
