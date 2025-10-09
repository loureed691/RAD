"""
Test suite for incremental/online learning functionality
"""
import os
import sys
import shutil
from datetime import datetime

def test_incremental_model_import():
    """Test importing incremental ML model"""
    print("\nTesting incremental model import...")
    try:
        from incremental_ml_model import IncrementalMLModel
        print("✓ Incremental model imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_incremental_model_basic():
    """Test basic incremental model functionality"""
    print("\nTesting incremental model basic functionality...")
    try:
        from incremental_ml_model import IncrementalMLModel
        
        # Create test model
        test_model_path = 'models/test_incremental_model.pkl'
        model = IncrementalMLModel(test_model_path)
        
        # Test feature preparation
        sample_indicators = {
            'rsi': 50,
            'macd': 0.5,
            'macd_signal': 0.3,
            'macd_diff': 0.2,
            'stoch_k': 50,
            'stoch_d': 50,
            'bb_width': 0.05,
            'volume_ratio': 1.5,
            'momentum': 0.01,
            'roc': 1.0,
            'atr': 2.5,
            'close': 100,
            'bb_high': 105,
            'bb_low': 95,
            'bb_mid': 100,
            'ema_12': 99,
            'ema_26': 98,
            'sma_20': 99.5,
            'sma_50': 98.5
        }
        
        features = model.prepare_features(sample_indicators)
        assert isinstance(features, dict), "Features should be a dictionary"
        assert len(features) == 31, f"Expected 31 features, got {len(features)}"
        
        # Test prediction (before any training)
        signal, confidence = model.predict(sample_indicators)
        assert signal in ['BUY', 'SELL', 'HOLD'], f"Invalid signal: {signal}"
        assert 0 <= confidence <= 1, f"Invalid confidence: {confidence}"
        
        print(f"  Feature dict has {len(features)} features")
        print(f"  Initial prediction: {signal} (confidence: {confidence:.2f})")
        print("✓ Basic functionality working")
        
        # Cleanup
        if os.path.exists(test_model_path):
            os.remove(test_model_path)
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_incremental_learning():
    """Test incremental learning (learn_one method)"""
    print("\nTesting incremental learning...")
    try:
        from incremental_ml_model import IncrementalMLModel
        
        # Create test model
        test_model_path = 'models/test_incremental_learning.pkl'
        model = IncrementalMLModel(test_model_path)
        
        sample_indicators = {
            'rsi': 70,
            'macd': 0.8,
            'macd_signal': 0.5,
            'macd_diff': 0.3,
            'stoch_k': 80,
            'stoch_d': 75,
            'bb_width': 0.06,
            'volume_ratio': 1.8,
            'momentum': 0.02,
            'roc': 1.5,
            'atr': 3.0,
            'close': 110,
            'bb_high': 115,
            'bb_low': 105,
            'bb_mid': 110,
            'ema_12': 109,
            'ema_26': 107,
            'sma_20': 108,
            'sma_50': 106
        }
        
        # Learn from several profitable BUY trades
        initial_trades = model.performance_metrics.get('total_trades', 0)
        for i in range(10):
            profit = 0.01 + (i * 0.001)  # Increasing profits
            model.learn_one(sample_indicators, 'BUY', profit)
        
        # Check that metrics were updated
        final_trades = model.performance_metrics.get('total_trades', 0)
        assert final_trades == initial_trades + 10, f"Expected {initial_trades + 10} trades, got {final_trades}"
        
        metrics = model.get_performance_metrics()
        assert metrics['total_trades'] >= 10, "Should have at least 10 trades recorded"
        assert metrics['win_rate'] > 0, "Should have some wins"
        
        print(f"  Learned from {final_trades} trades")
        print(f"  Win rate: {metrics['win_rate']:.2%}")
        print(f"  Accuracy: {metrics['accuracy']:.2%}")
        print("✓ Incremental learning working")
        
        # Cleanup
        if os.path.exists(test_model_path):
            os.remove(test_model_path)
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_incremental_model_persistence():
    """Test saving and loading incremental model"""
    print("\nTesting incremental model persistence...")
    try:
        from incremental_ml_model import IncrementalMLModel
        
        test_model_path = 'models/test_incremental_persistence.pkl'
        
        # Create and train model
        model1 = IncrementalMLModel(test_model_path)
        
        sample_indicators = {
            'rsi': 60,
            'macd': 0.6,
            'macd_signal': 0.4,
            'macd_diff': 0.2,
            'stoch_k': 65,
            'stoch_d': 60,
            'bb_width': 0.05,
            'volume_ratio': 1.4,
            'momentum': 0.015,
            'roc': 1.2,
            'atr': 2.8,
            'close': 105,
            'bb_high': 110,
            'bb_low': 100,
            'bb_mid': 105,
            'ema_12': 104,
            'ema_26': 103,
            'sma_20': 103.5,
            'sma_50': 102.5
        }
        
        # Learn from some trades
        for i in range(5):
            model1.learn_one(sample_indicators, 'BUY', 0.01)
        
        metrics1 = model1.get_performance_metrics()
        
        # Save model
        model1.save_model()
        
        # Load model in a new instance
        model2 = IncrementalMLModel(test_model_path)
        metrics2 = model2.get_performance_metrics()
        
        # Check that metrics match
        assert metrics1['total_trades'] == metrics2['total_trades'], "Trade count should match"
        assert metrics1['win_rate'] == metrics2['win_rate'], "Win rate should match"
        
        print(f"  Saved model with {metrics1['total_trades']} trades")
        print(f"  Loaded model with {metrics2['total_trades']} trades")
        print("✓ Model persistence working")
        
        # Cleanup
        if os.path.exists(test_model_path):
            os.remove(test_model_path)
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ml_model_with_incremental():
    """Test MLModel class with incremental learning enabled"""
    print("\nTesting MLModel with incremental learning...")
    try:
        from ml_model import MLModel
        
        # Create model with incremental learning
        test_model_path = 'models/test_ml_incremental.pkl'
        model = MLModel(test_model_path, use_incremental=True)
        
        assert model.use_incremental == True, "Incremental mode should be enabled"
        assert model.incremental_model is not None, "Incremental model should be initialized"
        
        sample_indicators = {
            'rsi': 55,
            'macd': 0.4,
            'macd_signal': 0.3,
            'macd_diff': 0.1,
            'stoch_k': 55,
            'stoch_d': 52,
            'bb_width': 0.04,
            'volume_ratio': 1.3,
            'momentum': 0.012,
            'roc': 1.1,
            'atr': 2.6,
            'close': 102,
            'bb_high': 107,
            'bb_low': 97,
            'bb_mid': 102,
            'ema_12': 101,
            'ema_26': 100,
            'sma_20': 100.5,
            'sma_50': 99.5
        }
        
        # Test prediction
        signal, confidence = model.predict(sample_indicators)
        assert signal in ['BUY', 'SELL', 'HOLD'], f"Invalid signal: {signal}"
        
        # Test recording outcome
        model.record_outcome(sample_indicators, 'BUY', 0.015)
        
        metrics = model.get_performance_metrics()
        assert metrics['total_trades'] >= 1, "Should have recorded at least one trade"
        
        # Test adaptive threshold
        threshold = model.get_adaptive_confidence_threshold()
        assert 0.5 <= threshold <= 0.75, f"Invalid threshold: {threshold}"
        
        print(f"  Prediction: {signal} (confidence: {confidence:.2f})")
        print(f"  Trades recorded: {metrics['total_trades']}")
        print(f"  Adaptive threshold: {threshold:.2f}")
        print("✓ MLModel with incremental learning working")
        
        # Cleanup
        if os.path.exists(test_model_path):
            os.remove(test_model_path)
        incremental_path = test_model_path.replace('.pkl', '_incremental.pkl')
        if os.path.exists(incremental_path):
            os.remove(incremental_path)
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_vs_incremental():
    """Compare batch and incremental learning modes"""
    print("\nTesting batch vs incremental modes...")
    try:
        from ml_model import MLModel
        
        # Create both models
        batch_path = 'models/test_batch.pkl'
        incr_path = 'models/test_incremental.pkl'
        
        batch_model = MLModel(batch_path, use_incremental=False)
        incr_model = MLModel(incr_path, use_incremental=True)
        
        sample_indicators = {
            'rsi': 65,
            'macd': 0.7,
            'macd_signal': 0.5,
            'macd_diff': 0.2,
            'stoch_k': 70,
            'stoch_d': 68,
            'bb_width': 0.055,
            'volume_ratio': 1.6,
            'momentum': 0.018,
            'roc': 1.4,
            'atr': 2.9,
            'close': 108,
            'bb_high': 113,
            'bb_low': 103,
            'bb_mid': 108,
            'ema_12': 107,
            'ema_26': 105,
            'sma_20': 106,
            'sma_50': 104
        }
        
        # Record outcomes in both models
        for i in range(5):
            profit = 0.008 + (i * 0.002)
            batch_model.record_outcome(sample_indicators, 'BUY', profit)
            incr_model.record_outcome(sample_indicators, 'BUY', profit)
        
        batch_metrics = batch_model.get_performance_metrics()
        incr_metrics = incr_model.get_performance_metrics()
        
        # Both should have recorded the same number of trades
        assert batch_metrics['total_trades'] == 5, "Batch model should have 5 trades"
        assert incr_metrics['total_trades'] == 5, "Incremental model should have 5 trades"
        
        # Check that incremental model has additional metrics
        assert 'accuracy' in incr_metrics, "Incremental model should have accuracy metric"
        assert 'f1_score' in incr_metrics, "Incremental model should have F1 score"
        
        print(f"  Batch model trades: {batch_metrics['total_trades']}")
        print(f"  Incremental model trades: {incr_metrics['total_trades']}")
        print(f"  Incremental accuracy: {incr_metrics.get('accuracy', 0):.2%}")
        print(f"  Incremental F1 score: {incr_metrics.get('f1_score', 0):.2%}")
        print("✓ Both modes working correctly")
        
        # Cleanup
        for path in [batch_path, incr_path, incr_path.replace('.pkl', '_incremental.pkl')]:
            if os.path.exists(path):
                os.remove(path)
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auto_model_selection():
    """Test automatic model selection feature"""
    print("\nTesting automatic model selection...")
    try:
        from ml_model import MLModel
        
        # Create model with auto-selection enabled
        test_model_path = 'models/test_auto_select.pkl'
        model = MLModel(test_model_path, auto_select_best=True)
        
        assert model.auto_select_best == True, "Auto-selection should be enabled"
        assert model.incremental_model is not None, "Incremental model should be initialized"
        
        sample_indicators = {
            'rsi': 60,
            'macd': 0.5,
            'macd_signal': 0.4,
            'macd_diff': 0.1,
            'stoch_k': 62,
            'stoch_d': 60,
            'bb_width': 0.045,
            'volume_ratio': 1.4,
            'momentum': 0.013,
            'roc': 1.2,
            'atr': 2.7,
            'close': 103,
            'bb_high': 108,
            'bb_low': 98,
            'bb_mid': 103,
            'ema_12': 102,
            'ema_26': 101,
            'sma_20': 101.5,
            'sma_50': 100
        }
        
        # Test prediction with auto-selection
        signal, confidence = model.predict(sample_indicators)
        assert signal in ['BUY', 'SELL', 'HOLD'], f"Invalid signal: {signal}"
        
        # Record outcomes to populate metrics
        for i in range(5):
            profit = 0.01 + (i * 0.002)
            model.record_outcome(sample_indicators, 'BUY', profit)
        
        # Check that both models received the outcomes
        assert model.batch_metrics['total_trades'] == 5, "Batch metrics should have 5 trades"
        assert model.incremental_metrics['total_trades'] == 5, "Incremental metrics should have 5 trades"
        
        print(f"  Auto-selection enabled: {model.auto_select_best}")
        print(f"  Batch model trades: {model.batch_metrics['total_trades']}")
        print(f"  Incremental model trades: {model.incremental_metrics['total_trades']}")
        print(f"  Currently using: {'Incremental' if model.use_incremental else 'Batch'}")
        print("✓ Auto model selection working")
        
        # Cleanup
        if os.path.exists(test_model_path):
            os.remove(test_model_path)
        incr_path = test_model_path.replace('.pkl', '_incremental.pkl')
        if os.path.exists(incr_path):
            os.remove(incr_path)
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all incremental learning tests"""
    print("=" * 60)
    print("Running Incremental Learning Tests")
    print("=" * 60)
    
    tests = [
        test_incremental_model_import,
        test_incremental_model_basic,
        test_incremental_learning,
        test_incremental_model_persistence,
        test_ml_model_with_incremental,
        test_batch_vs_incremental,
        test_auto_model_selection
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✓ All tests passed")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
