"""
Test priority pairs caching functionality
"""
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from market_scanner import MarketScanner
from config import Config


class TestPriorityPairsCaching(unittest.TestCase):
    """Test the priority pairs caching mechanism"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock client
        self.mock_client = Mock()
        self.scanner = MarketScanner(self.mock_client)

    def test_priority_pairs_cache_initialization(self):
        """Test that priority pairs cache is initialized correctly"""
        self.assertIsNone(self.scanner._cached_priority_pairs)
        self.assertIsNone(self.scanner._last_priority_pairs_update)
        self.assertEqual(
            self.scanner._priority_pairs_refresh_interval,
            Config.PRIORITY_PAIRS_REFRESH_INTERVAL
        )

    def test_priority_pairs_fetched_on_first_scan(self):
        """Test that priority pairs are fetched on first scan"""
        # Mock get_active_futures to return test data
        mock_futures = [
            {'symbol': 'BTCUSDT', 'quoteVolume': 10000000, 'swap': True},
            {'symbol': 'ETHUSDT', 'quoteVolume': 5000000, 'swap': True},
            {'symbol': 'SOLUSDT', 'quoteVolume': 2000000, 'swap': True},
        ]
        self.mock_client.get_active_futures.return_value = mock_futures

        # Mock scan_pair to return dummy results
        def mock_scan_pair(symbol):
            return (symbol, 50.0, 'BUY', 0.75, {}, None)
        
        with patch.object(self.scanner, 'scan_pair', side_effect=mock_scan_pair):
            # Run scan
            results = self.scanner.scan_all_pairs(max_workers=1)

        # Verify priority pairs were cached
        self.assertIsNotNone(self.scanner._cached_priority_pairs)
        self.assertIsNotNone(self.scanner._last_priority_pairs_update)
        self.assertGreater(len(self.scanner._cached_priority_pairs), 0)

    def test_priority_pairs_cache_reused_within_refresh_interval(self):
        """Test that cached priority pairs are reused within refresh interval"""
        # Set up initial cache
        self.scanner._cached_priority_pairs = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        self.scanner._last_priority_pairs_update = time.time()
        
        # Mock scan_pair
        def mock_scan_pair(symbol):
            return (symbol, 50.0, 'BUY', 0.75, {}, None)
        
        with patch.object(self.scanner, 'scan_pair', side_effect=mock_scan_pair):
            # Run scan - should use cached priority pairs
            results = self.scanner.scan_all_pairs(max_workers=1)

        # get_active_futures should NOT have been called
        self.mock_client.get_active_futures.assert_not_called()

    def test_priority_pairs_refreshed_after_interval(self):
        """Test that priority pairs are refreshed after interval expires"""
        # Set up expired cache
        self.scanner._cached_priority_pairs = ['BTCUSDT']
        # Set update time to be older than refresh interval
        self.scanner._last_priority_pairs_update = time.time() - (
            self.scanner._priority_pairs_refresh_interval + 10
        )
        
        # Mock get_active_futures
        mock_futures = [
            {'symbol': 'BTCUSDT', 'quoteVolume': 10000000, 'swap': True},
            {'symbol': 'ETHUSDT', 'quoteVolume': 5000000, 'swap': True},
        ]
        self.mock_client.get_active_futures.return_value = mock_futures
        
        # Mock scan_pair
        def mock_scan_pair(symbol):
            return (symbol, 50.0, 'BUY', 0.75, {}, None)
        
        with patch.object(self.scanner, 'scan_pair', side_effect=mock_scan_pair):
            # Run scan - should refresh priority pairs
            results = self.scanner.scan_all_pairs(max_workers=1)

        # get_active_futures SHOULD have been called to refresh
        self.mock_client.get_active_futures.assert_called_once()

    def test_clear_cache_clears_priority_pairs(self):
        """Test that clear_cache also clears priority pairs cache"""
        # Set up cache
        self.scanner._cached_priority_pairs = ['BTCUSDT', 'ETHUSDT']
        self.scanner._last_priority_pairs_update = time.time()
        
        # Clear cache
        self.scanner.clear_cache()
        
        # Verify priority pairs cache is cleared
        self.assertIsNone(self.scanner._cached_priority_pairs)
        self.assertIsNone(self.scanner._last_priority_pairs_update)


if __name__ == '__main__':
    unittest.main()
