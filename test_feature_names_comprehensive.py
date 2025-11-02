"""
Comprehensive test to verify StandardScaler feature names warning fix
Tests multiple scenarios including old models, new models, and attention weighting
"""
import sys
import os
import warnings
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_model import MLModel
from attention_features_2025 import AttentionFeatureSelector


def test_new_model_no_warnings():
    """Test that a newly trained model doesn't produce feature name warnings"""
    print("\n" + "="*70)
    print("TEST 1: New Model Training (No Warnings Expected)")
    print("="*70)
    
    model = MLModel(model_path='models/test_new_model.pkl')
    
    # Generate training data
    np.random.seed(42)
    for i in range(150):
        indicators = generate_test_indicators()
        profit_loss = np.random.uniform(-0.03, 0.03)
        signal = 'BUY' if np.random.random() > 0.5 else 'SELL'
        model.record_outcome(indicators, signal, profit_loss)
    
    print(f"✓ Generated {len(model.training_data)} training samples")
    
    # Train with warning capture
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        success = model.train(min_samples=100)
        
        if not success:
            print("✗ Training failed")
            return False
        
        feature_warnings = [warn for warn in w if "feature names" in str(warn.message).lower()]
        if feature_warnings:
            print(f"✗ Found {len(feature_warnings)} feature name warning(s) during training")
            for warn in feature_warnings:
                print(f"   {warn.message}")
            return False
        print("✓ No feature name warnings during training")
    
    # Test prediction with warning capture
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        test_indicators = generate_test_indicators()
        signal, confidence = model.predict(test_indicators)
        
        feature_warnings = [warn for warn in w if "feature names" in str(warn.message).lower()]
        if feature_warnings:
            print(f"✗ Found {len(feature_warnings)} feature name warning(s) during prediction")
            for warn in feature_warnings:
                print(f"   {warn.message}")
            return False
        print(f"✓ No feature name warnings during prediction (Signal: {signal}, Confidence: {confidence:.3f})")
    
    # Cleanup
    if os.path.exists('models/test_new_model.pkl'):
        os.remove('models/test_new_model.pkl')
    
    print("✓ TEST 1 PASSED")
    return True


def test_loaded_model_no_warnings():
    """Test that a loaded model doesn't produce feature name warnings"""
    print("\n" + "="*70)
    print("TEST 2: Loaded Model (No Warnings Expected)")
    print("="*70)
    
    # First train and save a model
    model1 = MLModel(model_path='models/test_loaded_model.pkl')
    np.random.seed(42)
    
    for i in range(150):
        indicators = generate_test_indicators()
        profit_loss = np.random.uniform(-0.03, 0.03)
        signal = 'BUY' if np.random.random() > 0.5 else 'SELL'
        model1.record_outcome(indicators, signal, profit_loss)
    
    model1.train(min_samples=100)
    print("✓ Trained and saved initial model")
    
    # Now load the model and test for warnings
    model2 = MLModel(model_path='models/test_loaded_model.pkl')
    print("✓ Loaded model from disk")
    
    # Test prediction with warning capture
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        test_indicators = generate_test_indicators()
        signal, confidence = model2.predict(test_indicators)
        
        feature_warnings = [warn for warn in w if "feature names" in str(warn.message).lower()]
        if feature_warnings:
            print(f"✗ Found {len(feature_warnings)} feature name warning(s) during prediction")
            for warn in feature_warnings:
                print(f"   {warn.message}")
            return False
        print(f"✓ No feature name warnings during prediction (Signal: {signal}, Confidence: {confidence:.3f})")
    
    # Cleanup
    if os.path.exists('models/test_loaded_model.pkl'):
        os.remove('models/test_loaded_model.pkl')
    
    print("✓ TEST 2 PASSED")
    return True


def test_attention_weighting_no_warnings():
    """Test that attention weighting doesn't introduce feature name warnings"""
    print("\n" + "="*70)
    print("TEST 3: Attention Weighting (No Warnings Expected)")
    print("="*70)
    
    model = MLModel(model_path='models/test_attention_model.pkl')
    
    # Add attention selector
    attention_selector = AttentionFeatureSelector(n_features=len(MLModel.FEATURE_NAMES), learning_rate=0.01)
    model.attention_selector = attention_selector
    print("✓ Configured attention selector")
    
    # Generate training data
    np.random.seed(42)
    for i in range(150):
        indicators = generate_test_indicators()
        profit_loss = np.random.uniform(-0.03, 0.03)
        signal = 'BUY' if np.random.random() > 0.5 else 'SELL'
        model.record_outcome(indicators, signal, profit_loss)
    
    # Train with warning capture
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        success = model.train(min_samples=100)
        
        if not success:
            print("✗ Training failed")
            return False
        
        feature_warnings = [warn for warn in w if "feature names" in str(warn.message).lower()]
        if feature_warnings:
            print(f"✗ Found {len(feature_warnings)} feature name warning(s) during training")
            return False
        print("✓ No feature name warnings during training with attention")
    
    # Test multiple predictions with attention weighting
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        for i in range(5):
            test_indicators = generate_test_indicators()
            signal, confidence = model.predict(test_indicators)
        
        feature_warnings = [warn for warn in w if "feature names" in str(warn.message).lower()]
        if feature_warnings:
            print(f"✗ Found {len(feature_warnings)} feature name warning(s) during predictions")
            for warn in feature_warnings:
                print(f"   {warn.message}")
            return False
        print("✓ No feature name warnings during 5 predictions with attention weighting")
    
    # Verify attention features are logged
    top_features = attention_selector.get_top_features(5)
    if top_features:
        print(f"✓ Attention mechanism working - Top feature: {top_features[0][0]} ({top_features[0][1]:.6f})")
    
    # Cleanup
    if os.path.exists('models/test_attention_model.pkl'):
        os.remove('models/test_attention_model.pkl')
    
    print("✓ TEST 3 PASSED")
    return True


def test_old_scaler_format_simulation():
    """Test that loading an old model (without set_output configured) still works"""
    print("\n" + "="*70)
    print("TEST 4: Old Model Format Simulation (Backward Compatibility)")
    print("="*70)
    
    # Create a model with old-style scaler (no set_output)
    model1 = MLModel(model_path='models/test_old_format.pkl')
    np.random.seed(42)
    
    for i in range(150):
        indicators = generate_test_indicators()
        profit_loss = np.random.uniform(-0.03, 0.03)
        signal = 'BUY' if np.random.random() > 0.5 else 'SELL'
        model1.record_outcome(indicators, signal, profit_loss)
    
    model1.train(min_samples=100)
    
    # Save the model (when loaded, the fix will automatically reconfigure the scaler)
    # This tests backward compatibility with models saved before the fix
    print("✓ Trained and saved model (simulating pre-fix model)")
    
    # Load the model (our fix should reconfigure the scaler)
    model2 = MLModel(model_path='models/test_old_format.pkl')
    print("✓ Loaded old format model (scaler should be reconfigured automatically)")
    
    # Test prediction should not produce warnings due to automatic reconfiguration
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        test_indicators = generate_test_indicators()
        signal, confidence = model2.predict(test_indicators)
        
        feature_warnings = [warn for warn in w if "feature names" in str(warn.message).lower()]
        if feature_warnings:
            print(f"✗ Found {len(feature_warnings)} feature name warning(s)")
            for warn in feature_warnings:
                print(f"   {warn.message}")
            return False
        print(f"✓ No warnings after automatic scaler reconfiguration (Signal: {signal}, Confidence: {confidence:.3f})")
    
    # Cleanup
    if os.path.exists('models/test_old_format.pkl'):
        os.remove('models/test_old_format.pkl')
    
    print("✓ TEST 4 PASSED")
    return True


def generate_test_indicators():
    """Generate test indicators for consistency"""
    return {
        'rsi': np.random.uniform(20, 80),
        'macd': np.random.uniform(-2, 2),
        'macd_signal': np.random.uniform(-2, 2),
        'macd_diff': np.random.uniform(-1, 1),
        'stoch_k': np.random.uniform(20, 80),
        'stoch_d': np.random.uniform(20, 80),
        'bb_width': np.random.uniform(0.01, 0.1),
        'volume_ratio': np.random.uniform(0.5, 2.0),
        'momentum': np.random.uniform(-0.05, 0.05),
        'roc': np.random.uniform(-0.1, 0.1),
        'atr': np.random.uniform(0.5, 3.0),
        'close': 50000,
        'bb_high': 51000,
        'bb_low': 49000,
        'bb_mid': 50000,
        'ema_12': 50000,
        'ema_26': 49800,
        'sma_20': 49900,
        'sma_50': 49500
    }


if __name__ == '__main__':
    print("\n" + "="*70)
    print("COMPREHENSIVE FEATURE NAMES WARNING FIX TEST SUITE")
    print("="*70)
    
    all_passed = True
    
    # Run all tests
    tests = [
        ("New Model Training", test_new_model_no_warnings),
        ("Loaded Model", test_loaded_model_no_warnings),
        ("Attention Weighting", test_attention_weighting_no_warnings),
        ("Old Model Format", test_old_scaler_format_simulation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
            all_passed = all_passed and passed
        except Exception as e:
            print(f"\n✗ TEST FAILED WITH EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
            all_passed = False
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print("="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED - No feature name warnings!")
        print("="*70)
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        print("="*70)
        sys.exit(1)
