"""
Test keyboard shutdown functionality
"""
import sys
import os
import signal
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_signal_handler_registration():
    """Test that signal handlers are properly registered"""
    print("\nTesting signal handler registration...")
    try:
        from bot import TradingBot
        from unittest.mock import Mock, patch
        
        # Mock dependencies to avoid actual API calls
        with patch('bot.KuCoinClient'), \
             patch('bot.MarketScanner'), \
             patch('bot.PositionManager') as mock_pm, \
             patch('bot.RiskManager'), \
             patch('bot.MLModel'), \
             patch('bot.AdvancedAnalytics'), \
             patch('bot.Config') as mock_config:
            
            # Setup config mock
            mock_config.API_KEY = "test_key"
            mock_config.API_SECRET = "test_secret"
            mock_config.API_PASSPHRASE = "test_passphrase"
            mock_config.LOG_LEVEL = "INFO"
            mock_config.LOG_FILE = "logs/test.log"
            mock_config.POSITION_LOG_FILE = "logs/test_position.log"
            mock_config.SCANNING_LOG_FILE = "logs/test_scanning.log"
            mock_config.ORDERS_LOG_FILE = "logs/test_orders.log"
            mock_config.STRATEGY_LOG_FILE = "logs/test_strategy.log"
            mock_config.DETAILED_LOG_LEVEL = "DEBUG"
            mock_config.TRAILING_STOP_PERCENTAGE = 0.02
            mock_config.MAX_POSITION_SIZE = 1000
            mock_config.RISK_PER_TRADE = 0.02
            mock_config.MAX_OPEN_POSITIONS = 3
            mock_config.ML_MODEL_PATH = "models/test.pkl"
            mock_config.validate = Mock()
            
            # Mock balance response
            mock_client = Mock()
            mock_client.get_balance.return_value = {
                'free': {'USDT': 1000.0}
            }
            
            # Mock position manager to return 0 synced positions
            mock_pm_instance = Mock()
            mock_pm_instance.sync_existing_positions.return_value = 0
            mock_pm.return_value = mock_pm_instance
            
            with patch('bot.KuCoinClient', return_value=mock_client):
                bot = TradingBot()
                
                # Check that signal handlers are registered
                assert hasattr(bot, 'signal_handler')
                assert callable(bot.signal_handler)
                assert bot.running == False
                
                print("✓ Signal handlers registered successfully")
                return True
    
    except Exception as e:
        print(f"✗ Signal handler registration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_handler_behavior():
    """Test that signal handler sets running to False"""
    print("\nTesting signal handler behavior...")
    try:
        from bot import TradingBot
        from unittest.mock import Mock, patch
        
        # Mock dependencies
        with patch('bot.KuCoinClient'), \
             patch('bot.MarketScanner'), \
             patch('bot.PositionManager') as mock_pm, \
             patch('bot.RiskManager'), \
             patch('bot.MLModel'), \
             patch('bot.AdvancedAnalytics'), \
             patch('bot.Config') as mock_config:
            
            # Setup config mock
            mock_config.API_KEY = "test_key"
            mock_config.API_SECRET = "test_secret"
            mock_config.API_PASSPHRASE = "test_passphrase"
            mock_config.LOG_LEVEL = "INFO"
            mock_config.LOG_FILE = "logs/test.log"
            mock_config.POSITION_LOG_FILE = "logs/test_position.log"
            mock_config.SCANNING_LOG_FILE = "logs/test_scanning.log"
            mock_config.ORDERS_LOG_FILE = "logs/test_orders.log"
            mock_config.STRATEGY_LOG_FILE = "logs/test_strategy.log"
            mock_config.DETAILED_LOG_LEVEL = "DEBUG"
            mock_config.TRAILING_STOP_PERCENTAGE = 0.02
            mock_config.MAX_POSITION_SIZE = 1000
            mock_config.RISK_PER_TRADE = 0.02
            mock_config.MAX_OPEN_POSITIONS = 3
            mock_config.ML_MODEL_PATH = "models/test.pkl"
            mock_config.validate = Mock()
            
            # Mock balance response
            mock_client = Mock()
            mock_client.get_balance.return_value = {
                'free': {'USDT': 1000.0}
            }
            
            # Mock position manager to return 0 synced positions
            mock_pm_instance = Mock()
            mock_pm_instance.sync_existing_positions.return_value = 0
            mock_pm.return_value = mock_pm_instance
            
            with patch('bot.KuCoinClient', return_value=mock_client):
                bot = TradingBot()
                
                # Bot should not be running initially
                assert bot.running == False
                print("✓ Bot not running initially")
                
                # Set bot to running
                bot.running = True
                assert bot.running == True
                print("✓ Bot running state set")
                
                # Simulate signal handler call
                bot.signal_handler(signal.SIGINT, None)
                
                # Bot should stop running after signal
                assert bot.running == False
                print("✓ Signal handler stopped bot")
                
                return True
    
    except Exception as e:
        print(f"✗ Signal handler behavior error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_keyboard_interrupt_handling():
    """Test that KeyboardInterrupt is properly caught"""
    print("\nTesting KeyboardInterrupt handling...")
    try:
        from bot import TradingBot
        from unittest.mock import Mock, patch
        
        # Mock dependencies
        with patch('bot.KuCoinClient'), \
             patch('bot.MarketScanner'), \
             patch('bot.PositionManager') as mock_pm, \
             patch('bot.RiskManager'), \
             patch('bot.MLModel'), \
             patch('bot.AdvancedAnalytics'), \
             patch('bot.Config') as mock_config:
            
            # Setup config mock
            mock_config.API_KEY = "test_key"
            mock_config.API_SECRET = "test_secret"
            mock_config.API_PASSPHRASE = "test_passphrase"
            mock_config.LOG_LEVEL = "INFO"
            mock_config.LOG_FILE = "logs/test.log"
            mock_config.POSITION_LOG_FILE = "logs/test_position.log"
            mock_config.SCANNING_LOG_FILE = "logs/test_scanning.log"
            mock_config.ORDERS_LOG_FILE = "logs/test_orders.log"
            mock_config.STRATEGY_LOG_FILE = "logs/test_strategy.log"
            mock_config.DETAILED_LOG_LEVEL = "DEBUG"
            mock_config.TRAILING_STOP_PERCENTAGE = 0.02
            mock_config.MAX_POSITION_SIZE = 1000
            mock_config.RISK_PER_TRADE = 0.02
            mock_config.MAX_OPEN_POSITIONS = 3
            mock_config.ML_MODEL_PATH = "models/test.pkl"
            mock_config.CHECK_INTERVAL = 1
            mock_config.validate = Mock()
            
            # Mock balance response
            mock_client = Mock()
            mock_client.get_balance.return_value = {
                'free': {'USDT': 1000.0}
            }
            
            # Mock position manager to return 0 synced positions
            mock_pm_instance = Mock()
            mock_pm_instance.sync_existing_positions.return_value = 0
            mock_pm.return_value = mock_pm_instance
            
            with patch('bot.KuCoinClient', return_value=mock_client):
                bot = TradingBot()
                
                # Mock run_cycle to raise KeyboardInterrupt after first call
                call_count = [0]
                
                def mock_run_cycle():
                    call_count[0] += 1
                    if call_count[0] == 1:
                        raise KeyboardInterrupt("Test interrupt")
                
                bot.run_cycle = mock_run_cycle
                
                # Mock shutdown to track if it's called
                shutdown_called = [False]
                original_shutdown = bot.shutdown
                
                def mock_shutdown():
                    shutdown_called[0] = True
                    # Don't call original to avoid issues with mocked components
                
                bot.shutdown = mock_shutdown
                
                # Run bot - should catch KeyboardInterrupt and call shutdown
                bot.run()
                
                # Verify shutdown was called
                assert shutdown_called[0] == True
                print("✓ Shutdown called after KeyboardInterrupt")
                
                return True
    
    except Exception as e:
        print(f"✗ KeyboardInterrupt handling error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_shutdown_method():
    """Test that shutdown method works correctly"""
    print("\nTesting shutdown method...")
    try:
        from bot import TradingBot
        from unittest.mock import Mock, patch
        
        # Mock dependencies
        with patch('bot.KuCoinClient'), \
             patch('bot.MarketScanner'), \
             patch('bot.PositionManager') as mock_pm, \
             patch('bot.RiskManager'), \
             patch('bot.MLModel') as mock_ml, \
             patch('bot.AdvancedAnalytics'), \
             patch('bot.Config') as mock_config:
            
            # Setup config mock
            mock_config.API_KEY = "test_key"
            mock_config.API_SECRET = "test_secret"
            mock_config.API_PASSPHRASE = "test_passphrase"
            mock_config.LOG_LEVEL = "INFO"
            mock_config.LOG_FILE = "logs/test.log"
            mock_config.POSITION_LOG_FILE = "logs/test_position.log"
            mock_config.SCANNING_LOG_FILE = "logs/test_scanning.log"
            mock_config.ORDERS_LOG_FILE = "logs/test_orders.log"
            mock_config.STRATEGY_LOG_FILE = "logs/test_strategy.log"
            mock_config.DETAILED_LOG_LEVEL = "DEBUG"
            mock_config.TRAILING_STOP_PERCENTAGE = 0.02
            mock_config.MAX_POSITION_SIZE = 1000
            mock_config.RISK_PER_TRADE = 0.02
            mock_config.MAX_OPEN_POSITIONS = 3
            mock_config.ML_MODEL_PATH = "models/test.pkl"
            mock_config.CLOSE_POSITIONS_ON_SHUTDOWN = False
            mock_config.validate = Mock()
            
            # Mock balance response
            mock_client = Mock()
            mock_client.get_balance.return_value = {
                'free': {'USDT': 1000.0}
            }
            
            # Mock position manager
            mock_pm_instance = Mock()
            mock_pm_instance.positions = {}
            mock_pm_instance.sync_existing_positions.return_value = 0
            mock_pm.return_value = mock_pm_instance
            
            # Mock ML model
            mock_ml_instance = Mock()
            mock_ml_instance.save_model.return_value = True
            mock_ml.return_value = mock_ml_instance
            
            with patch('bot.KuCoinClient', return_value=mock_client):
                bot = TradingBot()
                
                # Call shutdown
                bot.shutdown()
                
                # Verify ML model save was called
                mock_ml_instance.save_model.assert_called_once()
                print("✓ ML model save called during shutdown")
                
                return True
    
    except Exception as e:
        print(f"✗ Shutdown method error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all keyboard shutdown tests"""
    print("=" * 60)
    print("Keyboard Shutdown Tests")
    print("=" * 60)
    
    tests = [
        ("Signal Handler Registration", test_signal_handler_registration),
        ("Signal Handler Behavior", test_signal_handler_behavior),
        ("KeyboardInterrupt Handling", test_keyboard_interrupt_handling),
        ("Shutdown Method", test_shutdown_method),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
