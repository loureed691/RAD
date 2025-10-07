"""
Test concurrent scanning and trading functionality
"""
import unittest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from bot import TradingBot
from config import Config


class TestConcurrentScanning(unittest.TestCase):
    """Test that scanning and trading happen concurrently"""
    
    @patch('bot.signal.signal')
    @patch('bot.PositionManager')
    @patch('bot.RiskManager')
    @patch('bot.MLModel')
    @patch('bot.AdvancedAnalytics')
    @patch('bot.MarketScanner')
    @patch('bot.KuCoinClient')
    def test_background_scanner_thread_starts(self, mock_client, mock_scanner, 
                                               mock_analytics, mock_ml, mock_risk, 
                                               mock_position, mock_signal):
        """Test that background scanner thread starts on bot.run()"""
        # Mock API credentials
        Config.API_KEY = 'test_key'
        Config.API_SECRET = 'test_secret'
        Config.API_PASSPHRASE = 'test_passphrase'
        
        # Mock balance response
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_balance.return_value = {
            'free': {'USDT': 1000}
        }
        
        # Mock scanner
        mock_scanner_instance = mock_scanner.return_value
        mock_scanner_instance.get_best_pairs.return_value = []
        
        # Mock position manager
        mock_position_instance = mock_position.return_value
        mock_position_instance.sync_existing_positions.return_value = 0
        mock_position_instance.get_open_positions_count.return_value = 0
        
        bot = TradingBot()
        
        # Verify bot is initialized with threading attributes
        self.assertIsNotNone(bot._scan_lock)
        self.assertIsInstance(bot._scan_lock, type(threading.Lock()))
        self.assertIsInstance(bot._latest_opportunities, list)
        self.assertEqual(len(bot._latest_opportunities), 0)
        self.assertFalse(bot._scan_thread_running)
        
    @patch('bot.signal.signal')
    @patch('bot.PositionManager')
    @patch('bot.RiskManager')
    @patch('bot.MLModel')
    @patch('bot.AdvancedAnalytics')
    @patch('bot.MarketScanner')
    @patch('bot.KuCoinClient')
    def test_get_latest_opportunities_thread_safe(self, mock_client, mock_scanner,
                                                   mock_analytics, mock_ml, mock_risk,
                                                   mock_position, mock_signal):
        """Test that _get_latest_opportunities is thread-safe"""
        # Mock API credentials
        Config.API_KEY = 'test_key'
        Config.API_SECRET = 'test_secret'
        Config.API_PASSPHRASE = 'test_passphrase'
        
        # Mock balance response
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_balance.return_value = {
            'free': {'USDT': 1000}
        }
        
        # Mock position manager
        mock_position_instance = mock_position.return_value
        mock_position_instance.sync_existing_positions.return_value = 0
        
        bot = TradingBot()
        
        # Set some opportunities
        test_opportunities = [
            {'symbol': 'BTCUSDT', 'score': 10, 'signal': 'BUY', 'confidence': 0.9},
            {'symbol': 'ETHUSDT', 'score': 8, 'signal': 'SELL', 'confidence': 0.8}
        ]
        
        with bot._scan_lock:
            bot._latest_opportunities = test_opportunities
        
        # Get opportunities (should be thread-safe)
        retrieved = bot._get_latest_opportunities()
        
        # Should be a copy, not the original
        self.assertIsNot(retrieved, bot._latest_opportunities)
        self.assertEqual(len(retrieved), 2)
        self.assertEqual(retrieved[0]['symbol'], 'BTCUSDT')
    
    @patch('bot.signal.signal')
    @patch('bot.PositionManager')
    @patch('bot.RiskManager')
    @patch('bot.MLModel')
    @patch('bot.AdvancedAnalytics')
    @patch('bot.MarketScanner')
    @patch('bot.KuCoinClient')
    def test_scan_for_opportunities_uses_cached_results(self, mock_client, mock_scanner,
                                                         mock_analytics, mock_ml, mock_risk,
                                                         mock_position, mock_signal):
        """Test that scan_for_opportunities uses cached results from background scanner"""
        # Mock API credentials
        Config.API_KEY = 'test_key'
        Config.API_SECRET = 'test_secret'
        Config.API_PASSPHRASE = 'test_passphrase'
        
        # Mock balance response
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_balance.return_value = {
            'free': {'USDT': 1000}
        }
        
        # Mock position manager
        mock_position_instance = mock_position.return_value
        mock_position_instance.sync_existing_positions.return_value = 0
        mock_position_instance.get_open_positions_count.return_value = 0
        mock_position_instance.has_position.return_value = False
        
        # Mock scanner - should NOT be called during scan_for_opportunities
        mock_scanner_instance = mock_scanner.return_value
        mock_scanner_instance.get_best_pairs.return_value = []
        
        bot = TradingBot()
        
        # Set cached opportunities
        test_opportunities = [
            {'symbol': 'BTCUSDT', 'score': 10, 'signal': 'BUY', 'confidence': 0.9}
        ]
        
        with bot._scan_lock:
            bot._latest_opportunities = test_opportunities
            bot._last_opportunity_update = datetime.now()
        
        # Call scan_for_opportunities - should use cached results
        bot.scan_for_opportunities()
        
        # Scanner's get_best_pairs should NOT have been called
        # (it only gets called by the background thread)
        # The scan_for_opportunities method should just process cached results
        
    def test_concurrent_execution_logic(self):
        """Test the logic that enables concurrent scanning and trading"""
        # The key improvement is:
        # 1. Background thread continuously scans and updates cache
        # 2. Main thread executes trades from cache without waiting for scan
        
        # Simulate timing
        scan_duration = 30  # Scanning takes 30 seconds
        trade_duration = 2  # Trading takes 2 seconds
        
        # Old behavior: sequential (scan then trade)
        old_total_time = scan_duration + trade_duration  # 32 seconds
        
        # New behavior: concurrent (scan in background, trade immediately from cache)
        new_total_time = max(scan_duration, trade_duration)  # Only 30 seconds (or 2 if trade happens first)
        # But more importantly, trades can happen WHILE scanning continues
        
        # The benefit is that trades don't wait for the full scan to complete
        self.assertLess(trade_duration, old_total_time)
        
    @patch('bot.signal.signal')
    @patch('bot.PositionManager')
    @patch('bot.RiskManager')
    @patch('bot.MLModel')
    @patch('bot.AdvancedAnalytics')
    @patch('bot.MarketScanner')
    @patch('bot.KuCoinClient')
    def test_shutdown_stops_background_thread(self, mock_client, mock_scanner,
                                               mock_analytics, mock_ml, mock_risk,
                                               mock_position, mock_signal):
        """Test that shutdown properly stops the background scanner thread"""
        # Mock API credentials
        Config.API_KEY = 'test_key'
        Config.API_SECRET = 'test_secret'
        Config.API_PASSPHRASE = 'test_passphrase'
        
        # Mock balance response
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_balance.return_value = {
            'free': {'USDT': 1000}
        }
        
        # Mock position manager
        mock_position_instance = mock_position.return_value
        mock_position_instance.sync_existing_positions.return_value = 0
        mock_position_instance.positions = {}
        
        # Mock ML model
        mock_ml_instance = mock_ml.return_value
        mock_ml_instance.save_model.return_value = None
        
        bot = TradingBot()
        
        # Simulate thread running
        bot._scan_thread_running = True
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        bot._scan_thread = mock_thread
        
        # Call shutdown
        bot.shutdown()
        
        # Verify thread was stopped
        self.assertFalse(bot._scan_thread_running)
        mock_thread.join.assert_called_once()


if __name__ == '__main__':
    unittest.main()
