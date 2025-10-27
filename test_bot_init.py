"""
Test bot initialization with smart strategy mode
"""
import os
import sys

# Set up environment for testing
os.environ['USE_SMART_STRATEGIES_ONLY'] = 'true'
os.environ['KUCOIN_API_KEY'] = 'test_key'
os.environ['KUCOIN_API_SECRET'] = 'test_secret'
os.environ['KUCOIN_API_PASSPHRASE'] = 'test_passphrase'

# Mock the KuCoinClient to avoid real API calls
from unittest.mock import Mock, MagicMock, patch
import config

# Reload config to pick up environment variables
import importlib
importlib.reload(config)
from config import Config

# Constants
WEIGHT_TOLERANCE = 0.01  # Tolerance for weight sum validation

def run_tests():
    """Run all initialization tests"""
    print("=" * 60)
    print("Testing Bot Initialization with Smart Strategy Mode")
    print("=" * 60)
    
    errors = []
    
    # Test 1: Configuration Check
    print("\n1. Configuration Check:")
    print(f"   USE_SMART_STRATEGIES_ONLY: {Config.USE_SMART_STRATEGIES_ONLY}")
    print(f"   RL_STRATEGY_WEIGHT: {Config.RL_STRATEGY_WEIGHT}")
    print(f"   DEEP_LEARNING_WEIGHT: {Config.DEEP_LEARNING_WEIGHT}")
    print(f"   TRADITIONAL_STRATEGY_WEIGHT: {Config.TRADITIONAL_STRATEGY_WEIGHT}")
    
    if Config.USE_SMART_STRATEGIES_ONLY:
        print("✅ Smart Strategy Mode is ENABLED")
    else:
        print("✗ Smart Strategy Mode is DISABLED")
        errors.append("Smart Strategy Mode not enabled")
    
    # Test 2: Strategy Weight Validation
    print("\n2. Strategy Weight Validation:")
    total = Config.RL_STRATEGY_WEIGHT + Config.DEEP_LEARNING_WEIGHT + Config.TRADITIONAL_STRATEGY_WEIGHT
    print(f"   Total weight: {total:.2f}")
    if abs(total - 1.0) < WEIGHT_TOLERANCE:
        print("✅ Weights sum to 1.0")
    else:
        print(f"✗ Weights don't sum to 1.0 (got {total})")
        errors.append(f"Weights sum to {total}, expected 1.0")
    
    # Test 3: ML Components
    print("\n3. Testing ML Components:")
    try:
        from enhanced_ml_intelligence import (
            DeepLearningSignalPredictor,
            ReinforcementLearningStrategy,
            MultiTimeframeSignalFusion,
            AdaptiveExitStrategy
        )
        print("✅ All ML components imported successfully")
        
        # Test RL strategy
        rl = ReinforcementLearningStrategy()
        strategy = rl.select_strategy('bull', 0.03)
        print(f"   RL Strategy Selection: {strategy}")
        
        # Test confidence
        confidence = rl.get_strategy_confidence(strategy, 'bull', 0.03)
        print(f"   RL Strategy Confidence: {confidence:.2f}")
        
        print("✅ ML components working correctly")
        
    except Exception as e:
        print(f"✗ ML component error: {e}")
        errors.append(f"ML component error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Adaptive Strategy Selector
    print("\n4. Testing Adaptive Strategy Selector:")
    try:
        from adaptive_strategy_2026 import AdaptiveStrategySelector2026
        
        selector = AdaptiveStrategySelector2026()
        confidence_scores = {
            'trend_following': 0.8,
            'mean_reversion': 0.6,
            'breakout': 0.7,
            'momentum': 0.75
        }
        
        selected = selector.select_strategy('bull', 0.03, 0.5, confidence_scores)
        print(f"   Adaptive selector choice: {selected}")
        print("✅ Adaptive strategy selector working")
        
    except Exception as e:
        print(f"✗ Adaptive selector error: {e}")
        errors.append(f"Adaptive selector error: {e}")
        import traceback
        traceback.print_exc()
    
    # Report results
    print("\n" + "=" * 60)
    if errors:
        print(f"✗ {len(errors)} test(s) failed:")
        for error in errors:
            print(f"  - {error}")
        print("=" * 60)
        return False
    else:
        print("✓ All bot initialization tests passed!")
        print("=" * 60)
        print("\nSmart Strategy Mode is properly configured and ready to use.")
        print("The bot will prioritize self-learning AI strategies:")
        print(f"  - Reinforcement Learning: {Config.RL_STRATEGY_WEIGHT*100:.0f}%")
        print(f"  - Deep Learning: {Config.DEEP_LEARNING_WEIGHT*100:.0f}%")
        print(f"  - Traditional: {Config.TRADITIONAL_STRATEGY_WEIGHT*100:.0f}%")
        return True

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
