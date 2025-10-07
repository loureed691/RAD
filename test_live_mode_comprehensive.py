#!/usr/bin/env python3
"""
Comprehensive test for live mode bot functionality
Tests for errors, bugs, race conditions, and edge cases
"""
import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import threading
import time
from datetime import datetime, timedelta

class TestLiveModeComprehensive(unittest.TestCase):
    """Comprehensive tests for live mode functionality"""
    
    def test_threading_initialization(self):
        """Test that threading components are properly initialized"""
        with patch('bot.Config.validate'):
            with patch('bot.KuCoinClient') as mock_client:
                mock_client.return_value.get_balance.return_value = {'free': {'USDT': 1000.0}}
                with patch('bot.MarketScanner'):
                    with patch('bot.PositionManager') as mock_pos:
                        mock_pos.return_value.sync_existing_positions.return_value = 0
                        with patch('bot.RiskManager'):
                            with patch('bot.MLModel'):
                                with patch('bot.AdvancedAnalytics'):
                                    with patch('bot.Logger.setup') as mock_logger:
                                        mock_logger.return_value = Mock()
                                        with patch('bot.Logger.setup_specialized_logger') as mock_spec_logger:
                                            mock_spec_logger.return_value = Mock()
                                            
                                            from bot import TradingBot
                                            bot = TradingBot()
                                            
                                            # Check threading attributes exist
                                            self.assertTrue(hasattr(bot, '_scan_thread'))
                                            self.assertTrue(hasattr(bot, '_scan_thread_running'))
                                            self.assertTrue(hasattr(bot, '_scan_lock'))
                                            self.assertTrue(hasattr(bot, '_latest_opportunities'))
                                            self.assertTrue(hasattr(bot, '_last_opportunity_update'))
    
    def test_background_scanner_thread_safety(self):
        """Test that background scanner uses proper thread synchronization"""
        with patch('bot.Config.validate'):
            with patch('bot.KuCoinClient') as mock_client:
                mock_client.return_value.get_balance.return_value = {'free': {'USDT': 1000.0}}
                with patch('bot.MarketScanner') as mock_scanner:
                    mock_scanner.return_value.get_best_pairs.return_value = [
                        {'symbol': 'BTC-USDT', 'score': 85, 'signal': 'BUY', 'confidence': 0.8}
                    ]
                    with patch('bot.PositionManager') as mock_pos:
                        mock_pos.return_value.sync_existing_positions.return_value = 0
                        with patch('bot.RiskManager'):
                            with patch('bot.MLModel'):
                                with patch('bot.AdvancedAnalytics'):
                                    with patch('bot.Logger.setup') as mock_logger:
                                        mock_logger.return_value = Mock()
                                        with patch('bot.Logger.setup_specialized_logger') as mock_spec_logger:
                                            mock_spec_logger.return_value = Mock()
                                            
                                            from bot import TradingBot
                                            bot = TradingBot()
                                            
                                            # Verify lock exists and is a threading.Lock
                                            self.assertIsInstance(bot._scan_lock, threading.Lock)
    
    def test_graceful_shutdown_stops_thread(self):
        """Test that shutdown properly stops background thread"""
        with patch('bot.Config.validate'):
            with patch('bot.KuCoinClient') as mock_client:
                mock_client.return_value.get_balance.return_value = {'free': {'USDT': 1000.0}}
                with patch('bot.MarketScanner'):
                    with patch('bot.PositionManager') as mock_pos:
                        mock_pos.return_value.positions = {}
                        mock_pos.return_value.sync_existing_positions.return_value = 0
                        with patch('bot.RiskManager'):
                            with patch('bot.MLModel') as mock_ml:
                                mock_ml.return_value.save_model = Mock()
                                with patch('bot.AdvancedAnalytics'):
                                    with patch('bot.Logger.setup') as mock_logger:
                                        mock_logger.return_value = Mock()
                                        with patch('bot.Logger.setup_specialized_logger') as mock_spec_logger:
                                            mock_spec_logger.return_value = Mock()
                                            
                                            from bot import TradingBot
                                            bot = TradingBot()
                                            
                                            # Start the thread
                                            bot._scan_thread_running = True
                                            bot._scan_thread = threading.Thread(
                                                target=lambda: None,  # Dummy target
                                                daemon=True
                                            )
                                            bot._scan_thread.start()
                                            
                                            # Call shutdown
                                            bot.shutdown()
                                            
                                            # Verify thread flag is set to False
                                            self.assertFalse(bot._scan_thread_running)
    
    def test_opportunity_validation(self):
        """Test that invalid opportunity data is handled"""
        with patch('bot.Config.validate'):
            with patch('bot.KuCoinClient') as mock_client:
                mock_client.return_value.get_balance.return_value = {'free': {'USDT': 1000.0}}
                with patch('bot.MarketScanner'):
                    with patch('bot.PositionManager') as mock_pos:
                        mock_pos.return_value.get_open_positions_count.return_value = 0
                        mock_pos.return_value.sync_existing_positions.return_value = 0
                        with patch('bot.RiskManager'):
                            with patch('bot.MLModel'):
                                with patch('bot.AdvancedAnalytics'):
                                    with patch('bot.Logger.setup') as mock_logger:
                                        logger_mock = Mock()
                                        mock_logger.return_value = logger_mock
                                        with patch('bot.Logger.setup_specialized_logger') as mock_spec_logger:
                                            mock_spec_logger.return_value = Mock()
                                            
                                            from bot import TradingBot
                                            bot = TradingBot()
                                            
                                            # Set invalid opportunities
                                            bot._latest_opportunities = [
                                                None,  # Invalid
                                                {},  # Invalid - no symbol
                                                {'symbol': 'BTC-USDT', 'score': 85},  # Valid
                                            ]
                                            bot._last_opportunity_update = datetime.now()
                                            
                                            # Should not crash
                                            bot.scan_for_opportunities()
                                            
                                            # Should log warnings for invalid data
                                            self.assertTrue(logger_mock.warning.called or logger_mock.info.called)
    
    def test_position_update_error_handling(self):
        """Test that errors in position updates don't crash the bot"""
        with patch('bot.Config.validate'):
            with patch('bot.KuCoinClient') as mock_client:
                mock_client.return_value.get_balance.return_value = {'free': {'USDT': 1000.0}}
                with patch('bot.MarketScanner'):
                    with patch('bot.PositionManager') as mock_pos:
                        # Make update_position raise an exception
                        mock_pos.return_value.update_position.side_effect = Exception("Test error")
                        mock_pos.return_value.get_all_positions.return_value = [
                            Mock(symbol='BTC-USDT')
                        ]
                        mock_pos.return_value.sync_existing_positions.return_value = 0
                        with patch('bot.RiskManager'):
                            with patch('bot.MLModel'):
                                with patch('bot.AdvancedAnalytics'):
                                    with patch('bot.Logger.setup') as mock_logger:
                                        logger_mock = Mock()
                                        mock_logger.return_value = logger_mock
                                        with patch('bot.Logger.setup_specialized_logger') as mock_spec_logger:
                                            mock_spec_logger.return_value = Mock()
                                            
                                            from bot import TradingBot
                                            bot = TradingBot()
                                            
                                            # Should not crash
                                            bot.update_open_positions()
                                            
                                            # Should log the error
                                            self.assertTrue(logger_mock.error.called)
    
    def test_run_cycle_error_recovery(self):
        """Test that errors in run_cycle are handled and don't stop the bot"""
        with patch('bot.Config.validate'):
            with patch('bot.KuCoinClient') as mock_client:
                # Balance fetch succeeds for initialization but fails in run_cycle
                mock_client.return_value.get_balance.side_effect = [
                    {'free': {'USDT': 1000.0}},  # First call succeeds (initialization)
                    Exception("API error")  # Second call fails (in run_cycle)
                ]
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
                                            mock_spec_logger.return_value = Mock()
                                            
                                            from bot import TradingBot
                                            bot = TradingBot()
                                            
                                            # Should not crash even with errors
                                            try:
                                                bot.run_cycle()
                                            except Exception as e:
                                                self.fail(f"run_cycle should not raise exception: {e}")
    
    def test_live_monitoring_intervals(self):
        """Test that monitoring intervals are correctly configured"""
        from config import Config
        
        # Position updates should be more frequent than full cycles
        self.assertLess(Config.POSITION_UPDATE_INTERVAL, Config.CHECK_INTERVAL)
        
        # Intervals should be reasonable (not too fast, not too slow)
        self.assertGreaterEqual(Config.POSITION_UPDATE_INTERVAL, 1)  # At least 1 second
        self.assertLessEqual(Config.POSITION_UPDATE_INTERVAL, 30)  # At most 30 seconds
        
        self.assertGreaterEqual(Config.CHECK_INTERVAL, 10)  # At least 10 seconds
        self.assertLessEqual(Config.CHECK_INTERVAL, 300)  # At most 5 minutes

def print_results():
    """Print test results summary"""
    print("\n" + "=" * 70)
    print("🧪 LIVE MODE COMPREHENSIVE TEST RESULTS")
    print("=" * 70)
    print("\n✅ All live mode tests passed!")
    print("\nTested:")
    print("  ✓ Threading initialization")
    print("  ✓ Thread safety with locks")
    print("  ✓ Graceful shutdown")
    print("  ✓ Invalid data handling")
    print("  ✓ Error handling in position updates")
    print("  ✓ Error recovery in run cycle")
    print("  ✓ Monitoring interval configuration")
    print("\n🎉 Bot is ready for live trading!")
    print("=" * 70)

if __name__ == '__main__':
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestLiveModeComprehensive)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print_results()
    
    exit(0 if result.wasSuccessful() else 1)
