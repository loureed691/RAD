"""
Real-world simulation test to verify the StandardScaler warning fix
This simulates the exact scenario from the problem statement where:
1. Model is trained with attention features
2. Predictions are made with attention-based feature weighting
3. No sklearn warnings about feature names should appear
"""
import sys
import os
import warnings
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_model import MLModel
from attention_features_2025 import AttentionFeatureSelector


def simulate_real_world_scenario():
    """
    Simulate the exact scenario from the problem statement:
    - Train a model with attention features
    - Make predictions that trigger attention-based feature weighting
    - Verify no sklearn warnings appear
    """
    print("\n" + "="*70)
    print("REAL-WORLD SCENARIO SIMULATION")
    print("Simulating the exact issue from the problem statement")
    print("="*70)

    # Create ML model
    model = MLModel(model_path='models/test_real_world.pkl')

    # Initialize attention selector (2025 AI Enhancement)
    attention_selector = AttentionFeatureSelector(
        n_features=len(MLModel.FEATURE_NAMES),
        learning_rate=0.01
    )
    model.attention_selector = attention_selector

    print("\n1. Training model with attention selector...")
    np.random.seed(42)

    # Generate realistic training data
    for i in range(200):
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
            'close': 50000 + np.random.uniform(-1000, 1000),
            'bb_high': 51000,
            'bb_low': 49000,
            'bb_mid': 50000,
            'ema_12': 50000 + np.random.uniform(-500, 500),
            'ema_26': 49800 + np.random.uniform(-500, 500),
            'sma_20': 49900 + np.random.uniform(-500, 500),
            'sma_50': 49500 + np.random.uniform(-500, 500)
        }

        profit_loss = np.random.uniform(-0.03, 0.03)
        signal = 'BUY' if np.random.random() > 0.5 else 'SELL'
        model.record_outcome(indicators, signal, profit_loss)

    print(f"   ✓ Generated {len(model.training_data)} training samples")

    # Train model (this is where the problem could occur)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        success = model.train(min_samples=100)
        if not success:
            print("   ✗ Training failed")
            return False

        # Check for the specific sklearn warning from the problem statement
        sklearn_warnings = [
            warn for warn in w
            if "StandardScaler was fitted without feature names" in str(warn.message)
        ]

        if sklearn_warnings:
            print("   ✗ FOUND THE SKLEARN WARNING FROM PROBLEM STATEMENT:")
            for warn in sklearn_warnings:
                print(f"      {warn.message}")
            return False

        print("   ✓ Model trained successfully - No sklearn warnings")

    print("\n2. Making predictions with attention-based feature weighting...")
    print("   (This is where the warning appeared in the problem statement)")

    # Make multiple predictions to simulate real trading
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        for i in range(10):
            test_indicators = {
                'rsi': 65 + np.random.uniform(-10, 10),
                'macd': 1.2 + np.random.uniform(-0.5, 0.5),
                'macd_signal': 0.8 + np.random.uniform(-0.3, 0.3),
                'macd_diff': 0.4 + np.random.uniform(-0.2, 0.2),
                'stoch_k': 70 + np.random.uniform(-10, 10),
                'stoch_d': 65 + np.random.uniform(-10, 10),
                'bb_width': 0.05,
                'volume_ratio': 1.5,
                'momentum': 0.02,
                'roc': 0.03,
                'atr': 1.5,
                'close': 50000,
                'bb_high': 51000,
                'bb_low': 49000,
                'bb_mid': 50000,
                'ema_12': 50200,
                'ema_26': 49800,
                'sma_20': 49900,
                'sma_50': 49500
            }

            signal, confidence = model.predict(test_indicators)

            if i == 0:
                print(f"   Sample prediction: Signal={signal}, Confidence={confidence:.3f}")

        # Check for the specific sklearn warning
        sklearn_warnings = [
            warn for warn in w
            if "StandardScaler was fitted without feature names" in str(warn.message)
        ]

        if sklearn_warnings:
            print("\n   ✗ PROBLEM STATEMENT ISSUE REPRODUCED!")
            print("   ✗ Found sklearn warnings during prediction with attention weighting:")
            for warn in sklearn_warnings:
                print(f"      {warn.message}")
            return False

        print("   ✓ 10 predictions completed - No sklearn warnings!")

    print("\n3. Verifying attention mechanism is working...")
    top_features = attention_selector.get_top_features(5)
    if top_features:
        print("   ✓ Top attention features (as shown in problem statement):")
        for i, (feature, weight) in enumerate(top_features, 1):
            print(f"      {i}. {feature}: {weight:.6f}")

    print("\n4. Testing model save/load cycle...")
    # Save model
    model.save_model()
    print("   ✓ Model saved")

    # Load model
    model2 = MLModel(model_path='models/test_real_world.pkl')
    model2.attention_selector = attention_selector
    print("   ✓ Model loaded")

    # Predict with loaded model
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        test_indicators = {
            'rsi': 65, 'macd': 1.2, 'macd_signal': 0.8, 'macd_diff': 0.4,
            'stoch_k': 70, 'stoch_d': 65, 'bb_width': 0.05,
            'volume_ratio': 1.5, 'momentum': 0.02, 'roc': 0.03, 'atr': 1.5,
            'close': 50000, 'bb_high': 51000, 'bb_low': 49000, 'bb_mid': 50000,
            'ema_12': 50200, 'ema_26': 49800, 'sma_20': 49900, 'sma_50': 49500
        }

        signal, confidence = model2.predict(test_indicators)

        sklearn_warnings = [
            warn for warn in w
            if "StandardScaler was fitted without feature names" in str(warn.message)
        ]

        if sklearn_warnings:
            print("   ✗ Warning appeared after load cycle")
            return False

        print(f"   ✓ Loaded model prediction: Signal={signal}, Confidence={confidence:.3f}")
        print("   ✓ No warnings after save/load cycle")

    # Cleanup
    if os.path.exists('models/test_real_world.pkl'):
        os.remove('models/test_real_world.pkl')

    return True


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Real-World Scenario Test - Problem Statement Verification")
    print("Testing: sklearn StandardScaler feature names warning fix")
    print("="*70)

    try:
        success = simulate_real_world_scenario()

        if success:
            print("\n" + "="*70)
            print("✅ SUCCESS - PROBLEM STATEMENT ISSUE FIXED!")
            print("="*70)
            print("\nThe sklearn warning:")
            print("  'X has feature names, but StandardScaler was fitted without feature names'")
            print("\nis no longer appearing when using attention-based feature weighting!")
            print("="*70)
            sys.exit(0)
        else:
            print("\n" + "="*70)
            print("❌ FAILED - Problem statement issue still present")
            print("="*70)
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
