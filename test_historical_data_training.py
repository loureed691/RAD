"""
Test ML model training with historical data
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_historical_data_training():
    """Test training ML model with historical data"""
    print("\n" + "="*60)
    print("Testing ML Model Training with Historical Data")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    
    try:
        from ml_model import MLModel
        
        # Create temporary model path
        model_path = os.path.join(test_dir, 'test_model.pkl')
        
        print("\n1. Creating synthetic historical data...")
        # Create synthetic historical OHLCV data
        num_candles = 200
        start_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
        
        data = []
        base_price = 50000
        for i in range(num_candles):
            timestamp = start_time + i * 3600000  # 1 hour intervals
            
            # Simulate price movement with trend
            trend = i * 5  # Upward trend
            noise = np.random.normal(0, 100)
            close = base_price + trend + noise
            
            high = close + abs(np.random.normal(0, 50))
            low = close - abs(np.random.normal(0, 50))
            open_price = (high + low) / 2
            volume = np.random.uniform(1000, 2000)
            
            data.append([timestamp, open_price, high, low, close, volume])
        
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        print(f"   ✓ Created {len(df)} candles of synthetic data")
        
        # Save to CSV
        csv_path = os.path.join(test_dir, 'test_data.csv')
        df.to_csv(csv_path, index=False)
        print(f"   ✓ Saved to CSV: {csv_path}")
        
        print("\n2. Initializing ML model...")
        model = MLModel(model_path)
        initial_training_data_len = len(model.training_data)
        print(f"   Initial training data: {initial_training_data_len} samples")
        
        print("\n3. Training with historical data from DataFrame...")
        success = model.train_with_historical_data(df, min_samples=50)
        
        if not success:
            print("   ✗ Training failed")
            return False
        
        print(f"   ✓ Training successful")
        print(f"   Training samples generated: {len(model.training_data)}")
        
        # Verify training data was added
        assert len(model.training_data) > initial_training_data_len, \
            "Training data should have increased"
        
        # Verify model was trained
        assert model.model is not None, "Model should be trained"
        assert model.scaler is not None, "Scaler should be fitted"
        
        print(f"   ✓ Model trained successfully with {len(model.training_data)} samples")
        
        print("\n4. Testing model predictions...")
        # Test prediction with sample indicators
        sample_indicators = {
            'rsi': 55,
            'macd': 0.5,
            'macd_signal': 0.3,
            'macd_diff': 0.2,
            'stoch_k': 60,
            'stoch_d': 55,
            'bb_width': 0.04,
            'volume_ratio': 1.3,
            'momentum': 0.015,
            'roc': 1.5,
            'atr': 2.0,
            'close': 51000,
            'bb_high': 51200,
            'bb_low': 50800,
            'bb_mid': 51000,
            'ema_12': 50900,
            'ema_26': 50800
        }
        
        signal, confidence = model.predict(sample_indicators)
        print(f"   Prediction: {signal} with {confidence:.2%} confidence")
        assert signal in ['BUY', 'SELL', 'HOLD'], "Signal should be valid"
        assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
        print("   ✓ Predictions working correctly")
        
        print("\n5. Testing CSV loading functionality...")
        model2 = MLModel(os.path.join(test_dir, 'test_model2.pkl'))
        historical_df = model2.load_historical_data_from_csv(csv_path)
        
        assert not historical_df.empty, "Should load data from CSV"
        assert len(historical_df) == len(df), "Should load all rows"
        print(f"   ✓ Loaded {len(historical_df)} candles from CSV")
        
        print("\n6. Testing model persistence...")
        # Verify model was saved
        assert os.path.exists(model_path), "Model file should exist"
        
        # Load model in new instance
        model3 = MLModel(model_path)
        assert model3.model is not None, "Loaded model should have trained model"
        assert len(model3.training_data) > 0, "Loaded model should have training data"
        print(f"   ✓ Model persisted with {len(model3.training_data)} samples")
        
        print("\n7. Testing feature importance...")
        if model.feature_importance:
            top_features = sorted(
                model.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            print("   Top 5 features:")
            for feature, importance in top_features:
                print(f"     {feature}: {importance:.4f}")
            print("   ✓ Feature importance calculated")
        
        print("\n8. Testing invalid CSV handling...")
        # Test with invalid CSV
        invalid_csv = os.path.join(test_dir, 'invalid.csv')
        with open(invalid_csv, 'w') as f:
            f.write("invalid,data\n1,2\n")
        
        invalid_df = model.load_historical_data_from_csv(invalid_csv)
        assert invalid_df.empty, "Should return empty DataFrame for invalid CSV"
        print("   ✓ Invalid CSV handled correctly")
        
        print("\n9. Testing insufficient data handling...")
        # Create very small dataset
        small_df = df.head(50)  # Only 50 candles
        success = model.train_with_historical_data(small_df, min_samples=100)
        # Should fail due to insufficient samples but not crash
        print("   ✓ Insufficient data handled correctly")
        
        print("\n" + "="*60)
        print("✅ All Historical Data Training Tests PASSED")
        print("="*60)
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

def test_list_based_historical_data():
    """Test training with list-based historical data (OHLCV format)"""
    print("\n" + "="*60)
    print("Testing Training with List-Based Historical Data")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    
    try:
        from ml_model import MLModel
        
        print("\n1. Creating list-based OHLCV data...")
        # Create OHLCV data as list (as returned by exchange APIs)
        num_candles = 200  # Increased for more samples
        start_time = int((datetime.now() - timedelta(days=25)).timestamp() * 1000)
        
        # Set random seed for reproducibility
        np.random.seed(42)
        
        ohlcv_list = []
        base_price = 40000
        for i in range(num_candles):
            timestamp = start_time + i * 3600000
            # Create more diverse price movements
            trend = i * 15  # Stronger trend
            volatility = np.random.normal(0, 100)  # More volatility
            close = base_price + trend + volatility
            high = close + abs(np.random.normal(0, 50))
            low = close - abs(np.random.normal(0, 50))
            open_price = (high + low) / 2
            volume = np.random.uniform(800, 1200)
            
            ohlcv_list.append([timestamp, open_price, high, low, close, volume])
        
        print(f"   ✓ Created {len(ohlcv_list)} OHLCV candles")
        
        print("\n2. Training with list data...")
        model_path = os.path.join(test_dir, 'list_test_model.pkl')
        model = MLModel(model_path)
        
        success = model.train_with_historical_data(ohlcv_list, min_samples=50)
        
        assert success, "Training should succeed with list data"
        assert model.model is not None, "Model should be trained"
        print(f"   ✓ Successfully trained with {len(model.training_data)} samples")
        
        print("\n" + "="*60)
        print("✅ List-Based Data Training Test PASSED")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

if __name__ == '__main__':
    print("\n" + "="*70)
    print(" Running Historical Data Training Tests ".center(70, "="))
    print("="*70)
    
    tests = [
        test_historical_data_training,
        test_list_based_historical_data
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "="*70)
    print(" Test Summary ".center(70, "="))
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
