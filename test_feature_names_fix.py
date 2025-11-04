"""
Test to verify that LGBMClassifier feature names warning is fixed
"""
import sys
import os
import warnings
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_model import MLModel

def test_no_feature_name_warnings():
    """Test that no feature name warnings are raised during training and prediction"""
    print("\n" + "="*70)
    print("Testing Feature Names Warning Fix")
    print("="*70)

    # Create ML model instance
    model = MLModel(model_path='models/test_feature_names_model.pkl')

    print("\n1. Generating training data...")
    np.random.seed(42)

    # Generate 150 samples for training
    for i in range(150):
        indicators = {
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

        profit_loss = np.random.uniform(-0.03, 0.03)
        signal = 'BUY' if np.random.random() > 0.5 else 'SELL'

        model.record_outcome(indicators, signal, profit_loss)

    print(f"   ✓ Generated {len(model.training_data)} training samples")

    print("\n2. Training model and checking for warnings...")

    # Capture warnings during training
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        success = model.train(min_samples=100)

        if not success:
            print("   ✗ Training failed")
            return False

        # Check for feature name warnings
        feature_name_warnings = [
            warning for warning in w
            if "feature names" in str(warning.message).lower()
        ]

        if feature_name_warnings:
            print(f"   ✗ Found {len(feature_name_warnings)} feature name warning(s):")
            for warning in feature_name_warnings:
                print(f"      - {warning.message}")
            return False
        else:
            print("   ✓ No feature name warnings during training")

    print("\n3. Making predictions and checking for warnings...")

    # Test prediction with multiple samples
    test_indicators_list = [
        {
            'rsi': 65, 'macd': 1.2, 'macd_signal': 0.8, 'macd_diff': 0.4,
            'stoch_k': 70, 'stoch_d': 65, 'bb_width': 0.05,
            'volume_ratio': 1.5, 'momentum': 0.02, 'roc': 0.03, 'atr': 1.5,
            'close': 50000, 'bb_high': 51000, 'bb_low': 49000, 'bb_mid': 50000,
            'ema_12': 50200, 'ema_26': 49800, 'sma_20': 49900, 'sma_50': 49500
        },
        {
            'rsi': 35, 'macd': -0.8, 'macd_signal': -0.3, 'macd_diff': -0.5,
            'stoch_k': 30, 'stoch_d': 35, 'bb_width': 0.03,
            'volume_ratio': 0.8, 'momentum': -0.01, 'roc': -0.02, 'atr': 1.2,
            'close': 49000, 'bb_high': 50000, 'bb_low': 48000, 'bb_mid': 49000,
            'ema_12': 48800, 'ema_26': 49200, 'sma_20': 49100, 'sma_50': 49500
        },
        {
            'rsi': 50, 'macd': 0.1, 'macd_signal': 0.0, 'macd_diff': 0.1,
            'stoch_k': 50, 'stoch_d': 50, 'bb_width': 0.04,
            'volume_ratio': 1.0, 'momentum': 0.0, 'roc': 0.0, 'atr': 1.3,
            'close': 50000, 'bb_high': 51000, 'bb_low': 49000, 'bb_mid': 50000,
            'ema_12': 50000, 'ema_26': 50000, 'sma_20': 50000, 'sma_50': 50000
        }
    ]

    # Capture warnings during prediction
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        predictions = []
        for test_indicators in test_indicators_list:
            signal, confidence = model.predict(test_indicators)
            predictions.append((signal, confidence))

        # Check for feature name warnings
        feature_name_warnings = [
            warning for warning in w
            if "feature names" in str(warning.message).lower()
        ]

        if feature_name_warnings:
            print(f"   ✗ Found {len(feature_name_warnings)} feature name warning(s):")
            for warning in feature_name_warnings:
                print(f"      - {warning.message}")
            return False
        else:
            print("   ✓ No feature name warnings during prediction")

    print("\n4. Verifying predictions...")
    for i, (signal, confidence) in enumerate(predictions, 1):
        print(f"   Sample {i}: Signal={signal}, Confidence={confidence:.3f}")
        if signal not in ['BUY', 'SELL', 'HOLD']:
            print(f"   ✗ Invalid signal: {signal}")
            return False
        if confidence < 0 or confidence > 1:
            print(f"   ✗ Invalid confidence: {confidence}")
            return False
    print("   ✓ All predictions valid")

    # Cleanup
    if os.path.exists('models/test_feature_names_model.pkl'):
        os.remove('models/test_feature_names_model.pkl')
        print("\n   ✓ Cleaned up test model file")

    print("\n" + "="*70)
    print("✓ Feature Names Warning Fix Verified!")
    print("="*70)
    return True

if __name__ == '__main__':
    print("\n" + "="*70)
    print("Feature Names Warning Fix Test Suite")
    print("="*70)

    success = test_no_feature_name_warnings()

    if success:
        print("\n✓ TEST PASSED: No feature name warnings detected")
        sys.exit(0)
    else:
        print("\n✗ TEST FAILED: Feature name warnings still present")
        sys.exit(1)
