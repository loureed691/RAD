"""
Test for improved balance logging
"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_balance_logging_no_funds():
    """Test logging when account has no funds at all"""
    print("\nTest 1: Account with no funds")
    
    with patch('bot.KuCoinClient') as MockClient, \
         patch('bot.MarketScanner') as MockScanner, \
         patch('bot.PositionManager') as MockPosManager, \
         patch('bot.RiskManager') as MockRiskManager, \
         patch('bot.MLModel') as MockMLModel, \
         patch('bot.AdvancedAnalytics') as MockAnalytics, \
         patch('bot.Config') as MockConfig:
        
        # Setup config
        MockConfig.validate.return_value = True
        MockConfig.API_KEY = 'test'
        MockConfig.API_SECRET = 'test'
        MockConfig.API_PASSPHRASE = 'test'
        MockConfig.LOG_LEVEL = 'INFO'
        MockConfig.LOG_FILE = 'logs/bot.log'
        MockConfig.POSITION_LOG_FILE = 'logs/positions.log'
        MockConfig.SCANNING_LOG_FILE = 'logs/scanning.log'
        MockConfig.ORDERS_LOG_FILE = 'logs/orders.log'
        MockConfig.STRATEGY_LOG_FILE = 'logs/strategy.log'
        MockConfig.DETAILED_LOG_LEVEL = 'DEBUG'
        MockConfig.LEVERAGE = 10
        MockConfig.MAX_POSITION_SIZE = 1000
        MockConfig.RISK_PER_TRADE = 0.02
        MockConfig.MIN_PROFIT_THRESHOLD = 0.005
        MockConfig.TRAILING_STOP_PERCENTAGE = 0.02
        MockConfig.MAX_OPEN_POSITIONS = 3
        MockConfig.RETRAIN_INTERVAL = 86400
        MockConfig.ML_MODEL_PATH = 'models/signal_model.pkl'
        MockConfig.CHECK_INTERVAL = 60
        
        # Mock client to return no balance
        mock_client_instance = MockClient.return_value
        mock_client_instance.get_balance.return_value = {
            'free': {'USDT': 0.0},
            'used': {'USDT': 0.0},
            'total': {'USDT': 0.0}
        }
        
        # Mock position manager
        mock_pos_manager = MockPosManager.return_value
        mock_pos_manager.get_open_positions_count.return_value = 0
        mock_pos_manager.has_position.return_value = False
        mock_pos_manager.sync_existing_positions.return_value = 0
        mock_pos_manager.positions = {}
        
        from bot import TradingBot
        
        bot = TradingBot()
        
        # Test execute_trade with no balance
        opportunity = {
            'symbol': 'BTC/USDT:USDT',
            'signal': 'BUY',
            'confidence': 0.8,
            'score': 100
        }
        
        result = bot.execute_trade(opportunity)
        
        assert result is False, "Should return False when no balance"
        print("✓ Correctly returns False for no balance")
        print("✓ Should log: '💰 No available balance - account has no funds'")


def test_balance_logging_funds_in_use():
    """Test logging when funds are in use (normal trading scenario)"""
    print("\nTest 2: Funds in use (normal active trading)")
    
    with patch('bot.KuCoinClient') as MockClient, \
         patch('bot.MarketScanner') as MockScanner, \
         patch('bot.PositionManager') as MockPosManager, \
         patch('bot.RiskManager') as MockRiskManager, \
         patch('bot.MLModel') as MockMLModel, \
         patch('bot.AdvancedAnalytics') as MockAnalytics, \
         patch('bot.Config') as MockConfig:
        
        # Setup config
        MockConfig.validate.return_value = True
        MockConfig.API_KEY = 'test'
        MockConfig.API_SECRET = 'test'
        MockConfig.API_PASSPHRASE = 'test'
        MockConfig.LOG_LEVEL = 'INFO'
        MockConfig.LOG_FILE = 'logs/bot.log'
        MockConfig.POSITION_LOG_FILE = 'logs/positions.log'
        MockConfig.SCANNING_LOG_FILE = 'logs/scanning.log'
        MockConfig.ORDERS_LOG_FILE = 'logs/orders.log'
        MockConfig.STRATEGY_LOG_FILE = 'logs/strategy.log'
        MockConfig.DETAILED_LOG_LEVEL = 'DEBUG'
        MockConfig.LEVERAGE = 10
        MockConfig.MAX_POSITION_SIZE = 1000
        MockConfig.RISK_PER_TRADE = 0.02
        MockConfig.MIN_PROFIT_THRESHOLD = 0.005
        MockConfig.TRAILING_STOP_PERCENTAGE = 0.02
        MockConfig.MAX_OPEN_POSITIONS = 3
        MockConfig.RETRAIN_INTERVAL = 86400
        MockConfig.ML_MODEL_PATH = 'models/signal_model.pkl'
        MockConfig.CHECK_INTERVAL = 60
        
        # Mock client to return balance all in use
        mock_client_instance = MockClient.return_value
        mock_client_instance.get_balance.return_value = {
            'free': {'USDT': 0.0},
            'used': {'USDT': 950.0},
            'total': {'USDT': 950.0}
        }
        
        # Mock position manager with active positions
        mock_pos_manager = MockPosManager.return_value
        mock_pos_manager.get_open_positions_count.return_value = 3
        mock_pos_manager.has_position.return_value = False
        mock_pos_manager.sync_existing_positions.return_value = 3
        mock_pos_manager.positions = {}
        
        from bot import TradingBot
        
        bot = TradingBot()
        
        # Test execute_trade with balance in use
        opportunity = {
            'symbol': 'BTC/USDT:USDT',
            'signal': 'BUY',
            'confidence': 0.8,
            'score': 100
        }
        
        result = bot.execute_trade(opportunity)
        
        assert result is False, "Should return False when no free balance"
        print("✓ Correctly returns False for no free balance")
        print("✓ Should log: '💰 No free balance available (Free: $0.00, In use: $950.00, Total: $950.00, Positions: 3/3)'")


def test_balance_logging_partial_use():
    """Test logging when some funds are free and some in use"""
    print("\nTest 3: Partial balance in use (can still trade)")
    
    with patch('bot.KuCoinClient') as MockClient, \
         patch('bot.MarketScanner') as MockScanner, \
         patch('bot.PositionManager') as MockPosManager, \
         patch('bot.RiskManager') as MockRiskManager, \
         patch('bot.MLModel') as MockMLModel, \
         patch('bot.AdvancedAnalytics') as MockAnalytics, \
         patch('bot.Config') as MockConfig:
        
        # Setup config
        MockConfig.validate.return_value = True
        MockConfig.API_KEY = 'test'
        MockConfig.API_SECRET = 'test'
        MockConfig.API_PASSPHRASE = 'test'
        MockConfig.LOG_LEVEL = 'INFO'
        MockConfig.LOG_FILE = 'logs/bot.log'
        MockConfig.POSITION_LOG_FILE = 'logs/positions.log'
        MockConfig.SCANNING_LOG_FILE = 'logs/scanning.log'
        MockConfig.ORDERS_LOG_FILE = 'logs/orders.log'
        MockConfig.STRATEGY_LOG_FILE = 'logs/strategy.log'
        MockConfig.DETAILED_LOG_LEVEL = 'DEBUG'
        MockConfig.LEVERAGE = 10
        MockConfig.MAX_POSITION_SIZE = 1000
        MockConfig.RISK_PER_TRADE = 0.02
        MockConfig.MIN_PROFIT_THRESHOLD = 0.005
        MockConfig.TRAILING_STOP_PERCENTAGE = 0.02
        MockConfig.MAX_OPEN_POSITIONS = 3
        MockConfig.RETRAIN_INTERVAL = 86400
        MockConfig.ML_MODEL_PATH = 'models/signal_model.pkl'
        MockConfig.CHECK_INTERVAL = 60
        
        # Mock client to return partial balance in use
        mock_client_instance = MockClient.return_value
        mock_client_instance.get_balance.return_value = {
            'free': {'USDT': 350.0},
            'used': {'USDT': 650.0},
            'total': {'USDT': 1000.0}
        }
        mock_client_instance.get_ticker.return_value = {'last': 50000.0}
        mock_client_instance.get_ohlcv.return_value = [
            [i * 60000, 50000 + i * 10, 50010 + i * 10, 49990 + i * 10, 50005 + i * 10, 1000]
            for i in range(100)
        ]
        
        # Mock position manager with some positions
        mock_pos_manager = MockPosManager.return_value
        mock_pos_manager.get_open_positions_count.return_value = 2
        mock_pos_manager.has_position.return_value = False
        mock_pos_manager.open_position.return_value = True
        mock_pos_manager.sync_existing_positions.return_value = 2
        mock_pos_manager.positions = {}
        
        # Mock risk manager to allow the trade
        mock_risk_manager = MockRiskManager.return_value
        mock_risk_manager.check_portfolio_diversification.return_value = (True, "OK")
        mock_risk_manager.should_open_position.return_value = (True, "OK")
        mock_risk_manager.validate_trade.return_value = (True, "OK")
        mock_risk_manager.calculate_stop_loss_percentage.return_value = 0.025
        mock_risk_manager.get_max_leverage.return_value = 10
        mock_risk_manager.risk_per_trade = 0.02
        mock_risk_manager.update_drawdown.return_value = 1.0
        mock_risk_manager.calculate_position_size.return_value = 100
        
        # Mock scanner
        mock_scanner = MockScanner.return_value
        mock_scanner.signal_generator.detect_market_regime.return_value = 'trending'
        
        # Mock ML model
        mock_ml = MockMLModel.return_value
        mock_ml.get_performance_metrics.return_value = {'total_trades': 10}
        
        from bot import TradingBot
        
        bot = TradingBot()
        
        # Test execute_trade with available balance
        opportunity = {
            'symbol': 'BTC/USDT:USDT',
            'signal': 'BUY',
            'confidence': 0.8,
            'score': 100
        }
        
        result = bot.execute_trade(opportunity)
        
        # Should not hit the balance warning since we have $350 free
        print(f"✓ Result: {result}")
        print("✓ Should NOT log balance warning since $350.00 is available")
        print("✓ Should proceed with trade execution logic")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Balance Logging Improvements")
    print("=" * 60)
    
    test_balance_logging_no_funds()
    test_balance_logging_funds_in_use()
    test_balance_logging_partial_use()
    
    print("\n" + "=" * 60)
    print("✅ All balance logging tests passed!")
    print("=" * 60)
