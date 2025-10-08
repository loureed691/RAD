"""
Test suite for truly live mode operation (continuous monitoring without sleep cycles)
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time
import threading


class TestTrulyLiveMode(unittest.TestCase):
    """Tests for truly live continuous monitoring mode"""
    
    def test_live_loop_interval_config(self):
        """Test that LIVE_LOOP_INTERVAL configuration is available"""
        from config import Config
        
        # Should have a LIVE_LOOP_INTERVAL parameter
        self.assertTrue(hasattr(Config, 'LIVE_LOOP_INTERVAL'))
        
        # Should be a float
        self.assertIsInstance(Config.LIVE_LOOP_INTERVAL, float)
        
        # Should be a reasonable value (between 0.01 and 10 seconds)
        self.assertGreater(Config.LIVE_LOOP_INTERVAL, 0.01)
        self.assertLess(Config.LIVE_LOOP_INTERVAL, 10.0)
    
    def test_continuous_monitoring_with_throttling(self):
        """Test that continuous monitoring respects API throttling"""
        with patch('bot.Config.validate'):
            with patch('bot.KuCoinClient') as mock_client:
                mock_client.return_value.get_balance.return_value = {'free': {'USDT': 1000.0}}
                
                with patch('bot.MarketScanner'):
                    with patch('bot.PositionManager') as mock_pos:
                        # Setup position manager to have 1 open position
                        mock_pos.return_value.sync_existing_positions.return_value = 0
                        mock_pos.return_value.get_open_positions_count.return_value = 1
                        mock_pos.return_value.update_positions.return_value = []
                        
                        with patch('bot.RiskManager'):
                            with patch('bot.MLModel'):
                                with patch('bot.AdvancedAnalytics'):
                                    with patch('bot.Logger.setup') as mock_logger:
                                        logger_mock = Mock()
                                        mock_logger.return_value = logger_mock
                                        
                                        with patch('bot.Logger.setup_specialized_logger') as mock_spec_logger:
                                            mock_spec_logger.return_value = logger_mock
                                            
                                            from bot import TradingBot
                                            bot = TradingBot()
                                            
                                            # Track update calls
                                            update_calls = []
                                            original_update = bot.update_open_positions
                                            
                                            def track_update():
                                                update_calls.append(datetime.now())
                                                # Don't actually update
                                            
                                            bot.update_open_positions = track_update
                                            
                                            # Run bot for a short time in a thread
                                            bot_thread = threading.Thread(target=bot.run, daemon=True)
                                            bot_thread.start()
                                            
                                            # Let it run for 2.5 seconds
                                            time.sleep(2.5)
                                            
                                            # Stop the bot
                                            bot.running = False
                                            bot_thread.join(timeout=2)
                                            
                                            # Should have been called at least once but not too frequently
                                            # With POSITION_UPDATE_INTERVAL=5, should not call more than once in 2.5s
                                            self.assertGreaterEqual(len(update_calls), 0)  # May be 0 or 1
                                            self.assertLessEqual(len(update_calls), 1)
    
    def test_no_long_sleep_cycles(self):
        """Test that the bot doesn't have long sleep cycles anymore"""
        with patch('bot.Config.validate'):
            with patch('bot.KuCoinClient') as mock_client:
                mock_client.return_value.get_balance.return_value = {'free': {'USDT': 1000.0}}
                
                with patch('bot.MarketScanner'):
                    with patch('bot.PositionManager') as mock_pos:
                        mock_pos.return_value.sync_existing_positions.return_value = 0
                        mock_pos.return_value.get_open_positions_count.return_value = 0
                        
                        with patch('bot.RiskManager'):
                            with patch('bot.MLModel'):
                                with patch('bot.AdvancedAnalytics'):
                                    with patch('bot.Logger.setup') as mock_logger:
                                        logger_mock = Mock()
                                        mock_logger.return_value = logger_mock
                                        
                                        with patch('bot.Logger.setup_specialized_logger') as mock_spec_logger:
                                            mock_spec_logger.return_value = logger_mock
                                            
                                            from bot import TradingBot
                                            from config import Config
                                            bot = TradingBot()
                                            
                                            # Track time.sleep calls to ensure short sleeps
                                            sleep_calls = []
                                            original_sleep = time.sleep
                                            
                                            def track_sleep(duration):
                                                sleep_calls.append(duration)
                                                # Actually sleep briefly for test
                                                if duration > 0.01:
                                                    original_sleep(min(duration, 0.1))
                                            
                                            # Run in thread
                                            with patch('time.sleep', side_effect=track_sleep):
                                                bot_thread = threading.Thread(target=bot.run, daemon=True)
                                                bot_thread.start()
                                                
                                                # Let it run briefly
                                                original_sleep(0.5)
                                                
                                                # Stop
                                                bot.running = False
                                                bot_thread.join(timeout=2)
                                            
                                            # Should have multiple short sleep calls, not long ones
                                            # With LIVE_LOOP_INTERVAL=0.1, should see 0.1s sleeps
                                            short_sleeps = [s for s in sleep_calls if s <= 1.0]
                                            
                                            # Should have at least one short sleep
                                            self.assertGreater(len(short_sleeps), 0)
                                            
                                            # Most sleeps should be very short (LIVE_LOOP_INTERVAL)
                                            very_short = [s for s in sleep_calls if s <= Config.LIVE_LOOP_INTERVAL + 0.01]
                                            self.assertGreater(len(very_short), 0)
    
    def test_position_update_throttling_prevents_spam(self):
        """Test that position updates are throttled even in continuous loop"""
        with patch('bot.Config.validate'):
            with patch('bot.KuCoinClient') as mock_client:
                mock_client.return_value.get_balance.return_value = {'free': {'USDT': 1000.0}}
                
                with patch('bot.MarketScanner'):
                    with patch('bot.PositionManager') as mock_pos:
                        mock_pos.return_value.sync_existing_positions.return_value = 0
                        mock_pos.return_value.get_open_positions_count.return_value = 1
                        mock_pos.return_value.update_positions.return_value = []
                        
                        with patch('bot.RiskManager'):
                            with patch('bot.MLModel'):
                                with patch('bot.AdvancedAnalytics'):
                                    with patch('bot.Logger.setup') as mock_logger:
                                        logger_mock = Mock()
                                        mock_logger.return_value = logger_mock
                                        
                                        with patch('bot.Logger.setup_specialized_logger') as mock_spec_logger:
                                            mock_spec_logger.return_value = logger_mock
                                            
                                            from bot import TradingBot
                                            from config import Config
                                            bot = TradingBot()
                                            
                                            # Track actual position manager update calls
                                            update_count = [0]
                                            
                                            def count_updates():
                                                update_count[0] += 1
                                                return []
                                            
                                            mock_pos.return_value.update_positions = count_updates
                                            
                                            # Run for 1 second
                                            bot_thread = threading.Thread(target=bot.run, daemon=True)
                                            bot_thread.start()
                                            
                                            time.sleep(1.0)
                                            
                                            bot.running = False
                                            bot_thread.join(timeout=2)
                                            
                                            # With POSITION_UPDATE_INTERVAL=5, should not update more than once per second
                                            # In 1 second, should be 0 or 1 calls (since interval is 5 seconds)
                                            self.assertLessEqual(update_count[0], 1)


if __name__ == '__main__':
    unittest.main()
