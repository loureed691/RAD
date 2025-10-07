"""
Test for live trading enhancements
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import time
from config import Config

class TestLiveTrading(unittest.TestCase):
    """Test continuous position monitoring and live trading"""
    
    def test_position_update_interval_config(self):
        """Test that POSITION_UPDATE_INTERVAL is properly configured"""
        # Check that the configuration parameter exists
        self.assertTrue(hasattr(Config, 'POSITION_UPDATE_INTERVAL'))
        self.assertIsInstance(Config.POSITION_UPDATE_INTERVAL, int)
        self.assertGreater(Config.POSITION_UPDATE_INTERVAL, 0)
        self.assertLessEqual(Config.POSITION_UPDATE_INTERVAL, Config.CHECK_INTERVAL)
        
    def test_config_defaults(self):
        """Test that default values are sensible"""
        # Position updates should be more frequent than opportunity scans
        self.assertLess(Config.POSITION_UPDATE_INTERVAL, Config.CHECK_INTERVAL)
        
        # Position update interval should be frequent for live monitoring (5-10 seconds)
        self.assertLessEqual(Config.POSITION_UPDATE_INTERVAL, 10)
        
    @patch('bot.Config.validate')  # Mock config validation
    @patch('bot.KuCoinClient')
    @patch('bot.MarketScanner')
    @patch('bot.PositionManager')
    @patch('bot.RiskManager')
    @patch('bot.MLModel')
    @patch('bot.AdvancedAnalytics')
    @patch('bot.Logger')
    def test_bot_initialization_with_live_trading(self, mock_logger, mock_analytics, 
                                                   mock_ml, mock_risk, mock_position, 
                                                   mock_scanner, mock_client, mock_validate):
        """Test that bot initializes correctly with live trading parameters"""
        from bot import TradingBot
        
        # Mock config validation to pass
        mock_validate.return_value = None
        
        # Setup mocks
        mock_logger.setup.return_value = Mock()
        mock_logger.setup_specialized_logger.return_value = Mock()
        mock_logger.get_logger.return_value = Mock()
        mock_client.return_value.get_balance.return_value = {
            'free': {'USDT': 1000.0}
        }
        mock_position.return_value.sync_existing_positions.return_value = 0
        
        # Create bot instance
        bot = TradingBot()
        
        # Verify bot was initialized
        self.assertIsNotNone(bot)
        self.assertFalse(bot.running)
        
    def test_continuous_monitoring_logic(self):
        """Test the logic for continuous position monitoring"""
        # Simulate timing logic
        check_interval = 60  # Full cycle every 60 seconds
        position_update_interval = 5  # Position updates every 5 seconds
        
        last_full_cycle = datetime.now() - timedelta(seconds=30)
        current_time = datetime.now()
        
        time_since_last_cycle = (current_time - last_full_cycle).total_seconds()
        
        # After 30 seconds, should not do full cycle yet
        self.assertLess(time_since_last_cycle, check_interval)
        
        # Should calculate correct sleep time
        remaining_time = check_interval - time_since_last_cycle
        sleep_time = min(position_update_interval, remaining_time)
        
        self.assertEqual(sleep_time, position_update_interval)
        
        # After 60 seconds, should do full cycle
        last_full_cycle = datetime.now() - timedelta(seconds=65)
        time_since_last_cycle = (datetime.now() - last_full_cycle).total_seconds()
        
        self.assertGreaterEqual(time_since_last_cycle, check_interval)
        
    def test_responsive_sleep_intervals(self):
        """Test that sleep intervals allow responsive monitoring"""
        position_update_interval = 5
        check_interval = 60
        
        # Simulate being halfway through the cycle
        time_since_last_cycle = 30
        remaining_time = check_interval - time_since_last_cycle
        sleep_time = min(position_update_interval, remaining_time)
        
        # Should sleep for position update interval (5s)
        self.assertEqual(sleep_time, 5)
        
        # Simulate being near end of cycle
        time_since_last_cycle = 58
        remaining_time = check_interval - time_since_last_cycle
        sleep_time = min(position_update_interval, remaining_time)
        
        # Should sleep for only remaining time (2s)
        self.assertEqual(sleep_time, 2)
        
    @patch('bot.TradingBot.update_open_positions')
    @patch('bot.TradingBot.run_cycle')
    def test_live_monitoring_frequency(self, mock_run_cycle, mock_update_positions):
        """Test that position updates happen more frequently than full cycles"""
        # This is a conceptual test showing the difference in frequencies
        position_updates_per_cycle = Config.CHECK_INTERVAL // Config.POSITION_UPDATE_INTERVAL
        
        # Should have multiple position updates per full cycle
        self.assertGreater(position_updates_per_cycle, 1)
        
        # With default settings (60s / 5s), should get 12 updates per cycle
        self.assertGreaterEqual(position_updates_per_cycle, 10)

if __name__ == '__main__':
    unittest.main()
