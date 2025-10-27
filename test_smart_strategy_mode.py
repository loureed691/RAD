"""
Test Smart Strategy Mode - Ensure bot uses self-learning strategies
"""
import os
import sys

# Mock environment before importing config
os.environ['USE_SMART_STRATEGIES_ONLY'] = 'true'
os.environ['RL_STRATEGY_WEIGHT'] = '0.6'
os.environ['DEEP_LEARNING_WEIGHT'] = '0.3'
os.environ['TRADITIONAL_STRATEGY_WEIGHT'] = '0.1'
os.environ['REQUIRE_ML_TRAINING'] = 'true'
os.environ['MIN_ML_TRAINING_SAMPLES'] = '50'

from config import Config
from enhanced_ml_intelligence import ReinforcementLearningStrategy


def test_smart_strategy_config():
    """Test that smart strategy mode configuration is loaded correctly"""
    print("Testing Smart Strategy Mode Configuration...")
    
    # Check config values
    assert Config.USE_SMART_STRATEGIES_ONLY == True, "Smart strategies mode should be enabled"
    assert Config.REQUIRE_ML_TRAINING == True, "ML training should be required"
    assert Config.MIN_ML_TRAINING_SAMPLES == 50, "Min training samples should be 50"
    assert Config.RL_STRATEGY_WEIGHT == 0.6, "RL weight should be 0.6"
    assert Config.DEEP_LEARNING_WEIGHT == 0.3, "DL weight should be 0.3"
    assert Config.TRADITIONAL_STRATEGY_WEIGHT == 0.1, "Traditional weight should be 0.1"
    
    print("✅ Smart Strategy Mode configuration loaded correctly")
    print(f"   USE_SMART_STRATEGIES_ONLY: {Config.USE_SMART_STRATEGIES_ONLY}")
    print(f"   REQUIRE_ML_TRAINING: {Config.REQUIRE_ML_TRAINING}")
    print(f"   MIN_ML_TRAINING_SAMPLES: {Config.MIN_ML_TRAINING_SAMPLES}")
    print(f"   RL_STRATEGY_WEIGHT: {Config.RL_STRATEGY_WEIGHT}")
    print(f"   DEEP_LEARNING_WEIGHT: {Config.DEEP_LEARNING_WEIGHT}")
    print(f"   TRADITIONAL_STRATEGY_WEIGHT: {Config.TRADITIONAL_STRATEGY_WEIGHT}")
    return True


def test_rl_strategy_confidence():
    """Test RL strategy confidence calculation"""
    print("\nTesting RL Strategy Confidence...")
    
    rl = ReinforcementLearningStrategy()
    
    # Test confidence calculation
    confidence = rl.get_strategy_confidence('trend_following', 'bull', 0.03)
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    print(f"✅ Strategy confidence: {confidence:.2f}")
    
    # Test different market conditions
    conf_bull_low_vol = rl.get_strategy_confidence('trend_following', 'bull', 0.02)
    conf_bull_high_vol = rl.get_strategy_confidence('trend_following', 'bull', 0.08)
    
    print(f"   Bull + Low Vol: {conf_bull_low_vol:.2f}")
    print(f"   Bull + High Vol: {conf_bull_high_vol:.2f}")
    
    return True


def test_strategy_selection():
    """Test that RL strategy selection works"""
    print("\nTesting RL Strategy Selection...")
    
    rl = ReinforcementLearningStrategy()
    
    # Test strategy selection in different market conditions
    strategy_bull = rl.select_strategy('bull', 0.03)
    strategy_bear = rl.select_strategy('bear', 0.03)
    strategy_neutral = rl.select_strategy('neutral', 0.02)
    
    strategies = ['trend_following', 'mean_reversion', 'breakout', 'momentum']
    
    assert strategy_bull in strategies, f"Invalid strategy: {strategy_bull}"
    assert strategy_bear in strategies, f"Invalid strategy: {strategy_bear}"
    assert strategy_neutral in strategies, f"Invalid strategy: {strategy_neutral}"
    
    print(f"✅ Strategy selection working correctly")
    print(f"   Bull market: {strategy_bull}")
    print(f"   Bear market: {strategy_bear}")
    print(f"   Neutral market: {strategy_neutral}")
    
    return True


def test_q_learning_update():
    """Test that Q-learning updates work"""
    print("\nTesting Q-Learning Update...")
    
    rl = ReinforcementLearningStrategy()
    
    # Get initial Q-value
    state = rl.get_state('bull', 0.03)
    initial_q = rl.q_table[state]['trend_following']
    
    # Update with positive reward
    rl.update_q_value('bull', 0.03, 'trend_following', 1.0)
    
    # Check that Q-value increased
    new_q = rl.q_table[state]['trend_following']
    assert new_q > initial_q, "Q-value should increase after positive reward"
    
    print(f"✅ Q-Learning update working correctly")
    print(f"   Initial Q-value: {initial_q:.3f}")
    print(f"   Updated Q-value: {new_q:.3f}")
    print(f"   Improvement: +{(new_q - initial_q):.3f}")
    
    return True


def test_strategy_weights():
    """Test that strategy weights sum correctly"""
    print("\nTesting Strategy Weights...")
    
    total_weight = (Config.RL_STRATEGY_WEIGHT + 
                   Config.DEEP_LEARNING_WEIGHT + 
                   Config.TRADITIONAL_STRATEGY_WEIGHT)
    
    assert abs(total_weight - 1.0) < 0.01, "Strategy weights should sum to 1.0"
    
    print(f"✅ Strategy weights sum correctly: {total_weight:.2f}")
    print(f"   RL: {Config.RL_STRATEGY_WEIGHT*100:.0f}%")
    print(f"   Deep Learning: {Config.DEEP_LEARNING_WEIGHT*100:.0f}%")
    print(f"   Traditional: {Config.TRADITIONAL_STRATEGY_WEIGHT*100:.0f}%")
    
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running Smart Strategy Mode Tests")
    print("=" * 60)
    
    tests = [
        test_smart_strategy_config,
        test_rl_strategy_confidence,
        test_strategy_selection,
        test_q_learning_update,
        test_strategy_weights,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{len(tests)} passed")
    print("=" * 60)
    
    if failed > 0:
        print("✗ Some tests failed")
        sys.exit(1)
    else:
        print("✓ All tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    main()
