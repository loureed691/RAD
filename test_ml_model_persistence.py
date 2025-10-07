"""
Test ML model persistence across bot restarts
"""
import os
import sys
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ml_model_saves_on_shutdown():
    """Test that ML model is saved during bot shutdown"""
    print("\n" + "=" * 60)
    print("Testing ML Model Persistence on Shutdown")
    print("=" * 60)
    
    # Create a temporary directory for the test
    test_dir = tempfile.mkdtemp()
    model_path = os.path.join(test_dir, 'test_model.pkl')
    
    try:
        from ml_model import MLModel
        from bot import TradingBot
        from config import Config
        
        # Create and configure ML model
        print("\n1. Creating initial ML model...")
        model = MLModel(model_path)
        
        # Add some training data to simulate trading activity
        sample_indicators = {
            'rsi': 45,
            'macd': 0.3,
            'macd_signal': 0.2,
            'macd_diff': 0.1,
            'stoch_k': 55,
            'stoch_d': 50,
            'bb_width': 0.04,
            'volume_ratio': 1.3,
            'momentum': 0.008,
            'roc': 0.8,
            'atr': 2.0,
            'close': 100,
            'bb_high': 102,
            'bb_low': 98,
            'bb_mid': 100,
            'ema_12': 99,
            'ema_26': 98
        }
        
        # Record some outcomes
        print("2. Recording trading outcomes...")
        model.record_outcome(sample_indicators, 'BUY', 0.01)  # Profitable trade
        model.record_outcome(sample_indicators, 'SELL', -0.008)  # Losing trade
        model.record_outcome(sample_indicators, 'BUY', 0.015)  # Profitable trade
        
        initial_trades = model.performance_metrics['total_trades']
        initial_training_data_len = len(model.training_data)
        print(f"   Total trades recorded: {initial_trades}")
        print(f"   Training data samples: {initial_training_data_len}")
        
        # Manually save the model (simulating what shutdown should do)
        print("\n3. Saving model (simulating shutdown)...")
        model.save_model()
        
        # Verify file was created
        assert os.path.exists(model_path), "Model file should exist after save"
        print(f"   ✓ Model file created at {model_path}")
        
        # Create a new model instance (simulating bot restart)
        print("\n4. Loading model in new instance (simulating restart)...")
        model2 = MLModel(model_path)
        
        # Verify data was persisted
        assert model2.performance_metrics['total_trades'] == initial_trades, \
            f"Expected {initial_trades} trades, got {model2.performance_metrics['total_trades']}"
        assert len(model2.training_data) == initial_training_data_len, \
            f"Expected {initial_training_data_len} training samples, got {len(model2.training_data)}"
        
        print(f"   ✓ Total trades preserved: {model2.performance_metrics['total_trades']}")
        print(f"   ✓ Training data preserved: {len(model2.training_data)} samples")
        print(f"   ✓ Win rate preserved: {model2.performance_metrics.get('win_rate', 0):.2%}")
        
        # Test bot shutdown integration
        print("\n5. Testing bot shutdown integration...")
        
        # Mock the bot components to avoid API calls
        with patch('bot.KuCoinClient') as mock_client, \
             patch('bot.MarketScanner') as mock_scanner, \
             patch('bot.PositionManager') as mock_position_mgr, \
             patch('bot.RiskManager') as mock_risk_mgr, \
             patch('bot.AdvancedAnalytics') as mock_analytics, \
             patch('config.Config.validate') as mock_validate:
            
            # Setup mocks
            mock_validate.return_value = True
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_balance.return_value = {
                'free': {'USDT': 1000},
                'used': {'USDT': 0},
                'total': {'USDT': 1000}
            }
            
            mock_position_mgr_instance = MagicMock()
            mock_position_mgr.return_value = mock_position_mgr_instance
            mock_position_mgr_instance.sync_existing_positions.return_value = 0
            mock_position_mgr_instance.positions = {}
            
            # Override the ML model path in config
            original_path = Config.ML_MODEL_PATH
            Config.ML_MODEL_PATH = model_path
            
            try:
                # Create bot instance
                bot = TradingBot()
                
                # Record some outcomes through the bot's ML model
                bot.ml_model.record_outcome(sample_indicators, 'BUY', 0.02)
                trades_before_shutdown = bot.ml_model.performance_metrics['total_trades']
                
                print(f"   Trades before shutdown: {trades_before_shutdown}")
                
                # Call shutdown
                bot.shutdown()
                
                # Verify model was saved
                print(f"   ✓ Shutdown completed")
                
                # Create new bot instance to verify persistence
                bot2 = TradingBot()
                trades_after_restart = bot2.ml_model.performance_metrics['total_trades']
                
                assert trades_after_restart == trades_before_shutdown, \
                    f"Expected {trades_before_shutdown} trades after restart, got {trades_after_restart}"
                
                print(f"   ✓ Trades persisted after restart: {trades_after_restart}")
                
            finally:
                # Restore original config
                Config.ML_MODEL_PATH = original_path
        
        print("\n" + "=" * 60)
        print("✅ ML Model Persistence Test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        print(f"\nCleaned up temporary directory: {test_dir}")

if __name__ == '__main__':
    success = test_ml_model_saves_on_shutdown()
    sys.exit(0 if success else 1)
