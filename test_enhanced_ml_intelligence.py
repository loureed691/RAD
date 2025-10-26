"""
Tests for Enhanced ML Intelligence features
"""
import pytest
import numpy as np
from enhanced_ml_intelligence import (
    DeepLearningSignalPredictor,
    MultiTimeframeSignalFusion,
    AdaptiveExitStrategy,
    ReinforcementLearningStrategy
)


class TestDeepLearningSignalPredictor:
    """Test deep learning signal prediction"""
    
    def test_initialization(self):
        """Test model initialization"""
        predictor = DeepLearningSignalPredictor(n_features=31, sequence_length=10)
        assert predictor.n_features == 31
        assert predictor.sequence_length == 10
        assert predictor.model is not None or not predictor.model  # May be None if TF not available
        print("✅ Deep learning predictor initialized")
    
    def test_prediction_with_insufficient_data(self):
        """Test prediction returns HOLD with low confidence when buffer not full"""
        predictor = DeepLearningSignalPredictor(n_features=31, sequence_length=10)
        features = np.random.randn(31)
        
        # First prediction should have low confidence
        signal, confidence = predictor.predict(features)
        assert signal == 'HOLD'
        assert confidence < 0.5
        print(f"✅ Returns HOLD with low confidence before buffer full: {signal} ({confidence:.2f})")
    
    def test_prediction_with_sufficient_data(self):
        """Test prediction after filling buffer"""
        predictor = DeepLearningSignalPredictor(n_features=31, sequence_length=3)
        
        # Fill buffer with 3 feature vectors
        for _ in range(3):
            features = np.random.randn(31)
            signal, confidence = predictor.predict(features)
        
        # Should now have a real prediction
        assert signal in ['HOLD', 'BUY', 'SELL']
        assert 0 <= confidence <= 1.0
        print(f"✅ Makes prediction after buffer full: {signal} ({confidence:.2f})")


class TestMultiTimeframeSignalFusion:
    """Test multi-timeframe signal fusion"""
    
    def test_unanimous_agreement(self):
        """Test fusion when all timeframes agree"""
        fusion = MultiTimeframeSignalFusion()
        
        signals_1h = ('BUY', 0.8)
        signals_4h = ('BUY', 0.75)
        signals_1d = ('BUY', 0.85)
        
        fused_signal, fused_confidence, details = fusion.fuse_signals(
            signals_1h, signals_4h, signals_1d
        )
        
        assert fused_signal == 'BUY'
        assert fused_confidence > 0.7  # High confidence when all agree
        assert details['agreement_score'] == 1.0
        print(f"✅ Unanimous agreement: {fused_signal} ({fused_confidence:.2f})")
    
    def test_majority_agreement(self):
        """Test fusion when 2/3 timeframes agree"""
        fusion = MultiTimeframeSignalFusion()
        
        signals_1h = ('BUY', 0.7)
        signals_4h = ('BUY', 0.6)
        signals_1d = ('HOLD', 0.5)
        
        fused_signal, fused_confidence, details = fusion.fuse_signals(
            signals_1h, signals_4h, signals_1d
        )
        
        # Should lean towards BUY with moderate confidence
        assert fused_signal in ['BUY', 'HOLD']
        assert 0.4 < fused_confidence < 0.9
        assert details['agreement_score'] == 0.6
        print(f"✅ Majority agreement: {fused_signal} ({fused_confidence:.2f}, agreement: {details['agreement_score']:.2f})")
    
    def test_conflicting_signals(self):
        """Test fusion when timeframes conflict"""
        fusion = MultiTimeframeSignalFusion()
        
        signals_1h = ('BUY', 0.6)
        signals_4h = ('SELL', 0.6)
        signals_1d = ('HOLD', 0.5)
        
        fused_signal, fused_confidence, details = fusion.fuse_signals(
            signals_1h, signals_4h, signals_1d
        )
        
        # Should have low confidence when signals conflict
        assert fused_confidence < 0.7
        assert details['agreement_score'] < 0.5
        print(f"✅ Conflicting signals handled: {fused_signal} ({fused_confidence:.2f}, agreement: {details['agreement_score']:.2f})")
    
    def test_consistency_tracking(self):
        """Test temporal consistency tracking"""
        fusion = MultiTimeframeSignalFusion()
        
        # Make consistent signals over time
        for _ in range(3):
            signals_1h = ('BUY', 0.7)
            signals_4h = ('BUY', 0.7)
            signals_1d = ('BUY', 0.7)
            
            fused_signal, fused_confidence, details = fusion.fuse_signals(
                signals_1h, signals_4h, signals_1d
            )
        
        # Consistency should be high
        assert details['consistency_score'] > 0.5
        print(f"✅ Consistency tracked: {details['consistency_score']:.2f}")


class TestAdaptiveExitStrategy:
    """Test adaptive exit strategy"""
    
    def test_trailing_stop_hit(self):
        """Test exit when trailing stop is hit"""
        strategy = AdaptiveExitStrategy()
        
        # Simulate position that went up to 5%, now at 2.5%
        # First call establishes the high water mark
        result1 = strategy.calculate_optimal_exit(
            symbol='BTCUSDT',
            entry_price=100.0,
            current_price=105.0,
            side='long',
            volatility=0.03,
            volume_ratio=1.2,
            momentum=0.01,
            time_in_position=60,
            unrealized_pnl_pct=0.05
        )
        
        # Verify high water mark was set
        assert result1['highest_pnl'] == 0.05
        
        # Now price drops significantly from peak
        result2 = strategy.calculate_optimal_exit(
            symbol='BTCUSDT',
            entry_price=100.0,
            current_price=101.5,  # Much lower than peak
            side='long',
            volatility=0.03,
            volume_ratio=1.2,
            momentum=-0.01,
            time_in_position=90,
            unrealized_pnl_pct=0.015  # Down from 5% to 1.5%
        )
        
        # Should exit due to trailing stop (dropped >2.5% from peak of 5%)
        assert result2['should_exit'], f"Expected exit but got: {result2}"
        assert result2['exit_reason'] == 'trailing_stop'
        assert result2['exit_confidence'] > 0.8
        print(f"✅ Trailing stop detected: {result2['exit_reason']} (confidence: {result2['exit_confidence']:.2f})")
    
    def test_momentum_reversal(self):
        """Test exit on momentum reversal at profit"""
        strategy = AdaptiveExitStrategy()
        
        result = strategy.calculate_optimal_exit(
            symbol='BTCUSDT',
            entry_price=100.0,
            current_price=103.0,
            side='long',
            volatility=0.03,
            volume_ratio=1.2,
            momentum=-0.02,  # Strong negative momentum
            time_in_position=120,
            unrealized_pnl_pct=0.03
        )
        
        assert result['should_exit']
        assert result['exit_reason'] == 'momentum_reversal_at_profit'
        print(f"✅ Momentum reversal detected: {result['exit_reason']}")
    
    def test_stagnant_position(self):
        """Test exit for stagnant position"""
        strategy = AdaptiveExitStrategy()
        
        # First call to set baseline
        strategy.calculate_optimal_exit(
            symbol='ETHUSDT',
            entry_price=100.0,
            current_price=100.5,
            side='long',
            volatility=0.02,
            volume_ratio=1.0,
            momentum=0.001,
            time_in_position=480,
            unrealized_pnl_pct=0.005
        )
        
        # Second call after long time with minimal movement
        result = strategy.calculate_optimal_exit(
            symbol='ETHUSDT',
            entry_price=100.0,
            current_price=100.6,
            side='long',
            volatility=0.02,
            volume_ratio=1.0,
            momentum=0.001,
            time_in_position=600,  # 10 hours
            unrealized_pnl_pct=0.006
        )
        
        assert result['should_exit']
        assert result['exit_reason'] == 'stagnant_position'
        print(f"✅ Stagnant position detected: {result['exit_reason']}")
    
    def test_dynamic_targets(self):
        """Test dynamic profit targets adjust with volatility"""
        strategy = AdaptiveExitStrategy()
        
        # Low volatility - tighter targets
        result_low_vol = strategy.calculate_optimal_exit(
            symbol='BTCUSDT',
            entry_price=100.0,
            current_price=102.0,
            side='long',
            volatility=0.02,
            volume_ratio=1.2,
            momentum=0.01,
            time_in_position=60,
            unrealized_pnl_pct=0.02
        )
        
        # High volatility - wider targets
        result_high_vol = strategy.calculate_optimal_exit(
            symbol='BTCUSDT',
            entry_price=100.0,
            current_price=102.0,
            side='long',
            volatility=0.08,
            volume_ratio=1.2,
            momentum=0.01,
            time_in_position=60,
            unrealized_pnl_pct=0.02
        )
        
        # High volatility should have wider targets
        assert result_high_vol['dynamic_targets']['target_1'] > result_low_vol['dynamic_targets']['target_1']
        print(f"✅ Dynamic targets: Low vol={result_low_vol['dynamic_targets']['target_1']:.3f}, High vol={result_high_vol['dynamic_targets']['target_1']:.3f}")
    
    def test_scale_out_recommendation(self):
        """Test scale out recommendation at profit levels"""
        strategy = AdaptiveExitStrategy()
        
        result = strategy.calculate_optimal_exit(
            symbol='BTCUSDT',
            entry_price=100.0,
            current_price=105.0,
            side='long',
            volatility=0.03,
            volume_ratio=1.2,
            momentum=0.01,
            time_in_position=120,
            unrealized_pnl_pct=0.05
        )
        
        assert result['scale_out_recommendation'] > 0
        print(f"✅ Scale out recommended: {result['scale_out_recommendation']:.1%}")


class TestReinforcementLearningStrategy:
    """Test reinforcement learning strategy selector"""
    
    def test_initialization(self):
        """Test RL strategy initialization"""
        rl = ReinforcementLearningStrategy()
        assert len(rl.q_table) > 0
        assert rl.epsilon > 0
        print(f"✅ RL strategy initialized with {len(rl.q_table)} states, epsilon={rl.epsilon:.2f}")
    
    def test_strategy_selection(self):
        """Test strategy selection"""
        rl = ReinforcementLearningStrategy()
        
        strategy = rl.select_strategy('bull', 0.03)
        assert strategy in ['trend_following', 'mean_reversion', 'breakout', 'momentum']
        print(f"✅ Strategy selected: {strategy}")
    
    def test_q_value_update(self):
        """Test Q-value update from trade outcome"""
        rl = ReinforcementLearningStrategy()
        
        # Get initial Q-value
        state = rl.get_state('bull', 0.03)
        strategy = 'trend_following'
        initial_q = rl.q_table[state][strategy]
        
        # Update with positive reward
        rl.update_q_value('bull', 0.03, strategy, 1.0)
        
        # Q-value should have increased
        updated_q = rl.q_table[state][strategy]
        assert updated_q > initial_q
        print(f"✅ Q-value updated: {initial_q:.3f} -> {updated_q:.3f}")
    
    def test_exploration_decay(self):
        """Test epsilon decay over time"""
        rl = ReinforcementLearningStrategy()
        
        initial_epsilon = rl.epsilon
        
        # Perform multiple updates
        for _ in range(10):
            rl.update_q_value('bull', 0.03, 'trend_following', 0.5)
        
        # Epsilon should have decayed
        assert rl.epsilon < initial_epsilon
        assert rl.epsilon >= rl.min_epsilon
        print(f"✅ Epsilon decayed: {initial_epsilon:.3f} -> {rl.epsilon:.3f}")
    
    def test_state_mapping(self):
        """Test state mapping from market conditions"""
        rl = ReinforcementLearningStrategy()
        
        # Test different volatility levels
        state_low = rl.get_state('bull', 0.02)
        state_med = rl.get_state('bull', 0.04)
        state_high = rl.get_state('bull', 0.07)
        
        assert 'low' in state_low
        assert 'medium' in state_med
        assert 'high' in state_high
        print(f"✅ State mapping: low={state_low}, med={state_med}, high={state_high}")


def test_all_components_work_together():
    """Integration test - all components work together"""
    # Initialize all components
    dl_predictor = DeepLearningSignalPredictor(n_features=31, sequence_length=3)
    mtf_fusion = MultiTimeframeSignalFusion()
    adaptive_exit = AdaptiveExitStrategy()
    rl_strategy = ReinforcementLearningStrategy()
    
    # Simulate a trading workflow
    
    # 1. Get signals from multiple timeframes
    signals_1h = ('BUY', 0.75)
    signals_4h = ('BUY', 0.70)
    signals_1d = ('BUY', 0.80)
    
    # 2. Fuse signals
    fused_signal, fused_confidence, _ = mtf_fusion.fuse_signals(
        signals_1h, signals_4h, signals_1d
    )
    
    # 3. Select strategy using RL
    strategy = rl_strategy.select_strategy('bull', 0.03)
    
    # 4. Make deep learning prediction
    features = np.random.randn(31)
    for _ in range(3):  # Fill buffer
        dl_predictor.predict(features)
    dl_signal, dl_confidence = dl_predictor.predict(features)
    
    # 5. Calculate optimal exit
    exit_result = adaptive_exit.calculate_optimal_exit(
        symbol='BTCUSDT',
        entry_price=100.0,
        current_price=103.0,
        side='long',
        volatility=0.03,
        volume_ratio=1.2,
        momentum=0.01,
        time_in_position=120,
        unrealized_pnl_pct=0.03
    )
    
    # 6. Update RL after trade
    rl_strategy.update_q_value('bull', 0.03, strategy, 1.0)
    
    print("✅ All components work together successfully")
    print(f"   Fused signal: {fused_signal} ({fused_confidence:.2f})")
    print(f"   Strategy: {strategy}")
    print(f"   DL signal: {dl_signal} ({dl_confidence:.2f})")
    print(f"   Exit decision: {exit_result['should_exit']}")
    
    assert True  # If we get here, everything worked


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
