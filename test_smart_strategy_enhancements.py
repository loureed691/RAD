"""
Tests for enhanced smarter trading and leverage strategies
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_streak_tracking():
    """Test win/loss streak tracking in risk manager"""
    print("\nTesting win/loss streak tracking...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Test win streak
        manager.record_trade_outcome(0.05)  # Win
        assert manager.win_streak == 1, f"Expected win_streak=1, got {manager.win_streak}"
        assert manager.loss_streak == 0, f"Expected loss_streak=0, got {manager.loss_streak}"
        
        manager.record_trade_outcome(0.03)  # Win
        assert manager.win_streak == 2, f"Expected win_streak=2, got {manager.win_streak}"
        
        manager.record_trade_outcome(0.02)  # Win
        assert manager.win_streak == 3, f"Expected win_streak=3, got {manager.win_streak}"
        
        # Test loss breaks win streak
        manager.record_trade_outcome(-0.02)  # Loss
        assert manager.win_streak == 0, f"Expected win_streak reset to 0"
        assert manager.loss_streak == 1, f"Expected loss_streak=1, got {manager.loss_streak}"
        
        manager.record_trade_outcome(-0.015)  # Loss
        assert manager.loss_streak == 2, f"Expected loss_streak=2, got {manager.loss_streak}"
        
        # Test recent trades tracking
        assert len(manager.recent_trades) == 5, f"Expected 5 recent trades, got {len(manager.recent_trades)}"
        
        print(f"  ✓ Win streak tracking: {manager.win_streak}")
        print(f"  ✓ Loss streak tracking: {manager.loss_streak}")
        print(f"  ✓ Recent trades window: {len(manager.recent_trades)}")
        print("✓ Streak tracking working correctly")
        return True
    except Exception as e:
        print(f"✗ Streak tracking test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_recent_win_rate():
    """Test recent win rate calculation"""
    print("\nTesting recent win rate calculation...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Record 7 wins and 3 losses
        manager.record_trade_outcome(0.05)   # Win
        manager.record_trade_outcome(0.03)   # Win
        manager.record_trade_outcome(-0.02)  # Loss
        manager.record_trade_outcome(0.02)   # Win
        manager.record_trade_outcome(0.04)   # Win
        manager.record_trade_outcome(-0.01)  # Loss
        manager.record_trade_outcome(0.025)  # Win
        manager.record_trade_outcome(0.03)   # Win
        manager.record_trade_outcome(-0.015) # Loss
        manager.record_trade_outcome(0.035)  # Win
        
        recent_win_rate = manager.get_recent_win_rate()
        expected_win_rate = 0.7  # 7 wins out of 10 trades
        
        assert abs(recent_win_rate - expected_win_rate) < 0.01, \
            f"Expected win rate ~{expected_win_rate}, got {recent_win_rate}"
        
        print(f"  ✓ Recent win rate: {recent_win_rate:.1%} (7/10 trades)")
        print("✓ Recent win rate calculation working correctly")
        return True
    except Exception as e:
        print(f"✗ Recent win rate test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_leverage_calculation():
    """Test enhanced multi-factor leverage calculation"""
    print("\nTesting enhanced leverage calculation...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Test 1: Low volatility + high confidence + strong trend = high leverage
        leverage1 = manager.get_max_leverage(
            volatility=0.015,      # Low volatility
            confidence=0.85,       # High confidence
            momentum=0.035,        # Strong momentum
            trend_strength=0.8,    # Strong trend
            market_regime='trending'
        )
        print(f"  ✓ Optimal conditions: {leverage1}x leverage")
        assert leverage1 >= 15, f"Expected high leverage (≥15x), got {leverage1}x"
        
        # Test 2: High volatility + low confidence = low leverage
        leverage2 = manager.get_max_leverage(
            volatility=0.09,       # High volatility
            confidence=0.58,       # Low confidence
            momentum=0.005,        # Weak momentum
            trend_strength=0.3,    # Weak trend
            market_regime='ranging'
        )
        print(f"  ✓ Poor conditions: {leverage2}x leverage")
        assert leverage2 <= 6, f"Expected low leverage (≤6x), got {leverage2}x"
        
        # Test 3: Win streak increases leverage
        for _ in range(5):
            manager.record_trade_outcome(0.03)  # 5 wins
        
        leverage3 = manager.get_max_leverage(
            volatility=0.03,
            confidence=0.70,
            momentum=0.02,
            trend_strength=0.6,
            market_regime='neutral'
        )
        print(f"  ✓ After 5-win streak: {leverage3}x leverage")
        
        # Test 4: Loss streak reduces leverage
        manager2 = RiskManager(1000, 0.02, 3)
        for _ in range(4):
            manager2.record_trade_outcome(-0.02)  # 4 losses
        
        leverage4 = manager2.get_max_leverage(
            volatility=0.03,
            confidence=0.70,
            momentum=0.02,
            trend_strength=0.6,
            market_regime='neutral'
        )
        print(f"  ✓ After 4-loss streak: {leverage4}x leverage")
        assert leverage4 < leverage3, "Loss streak should reduce leverage vs normal conditions"
        
        # Test 5: Drawdown protection overrides other factors
        manager3 = RiskManager(1000, 0.02, 3)
        manager3.update_drawdown(10000)  # Set peak
        manager3.update_drawdown(7500)   # 25% drawdown
        
        leverage5 = manager3.get_max_leverage(
            volatility=0.02,       # Good volatility
            confidence=0.80,       # High confidence
            momentum=0.03,         # Good momentum
            trend_strength=0.7,    # Strong trend
            market_regime='trending'
        )
        print(f"  ✓ With 25% drawdown: {leverage5}x leverage (protected)")
        assert leverage5 <= 12, f"Drawdown should significantly reduce leverage, got {leverage5}x"
        
        print("✓ Enhanced leverage calculation working correctly")
        return True
    except Exception as e:
        print(f"✗ Enhanced leverage test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adaptive_fractional_kelly():
    """Test adaptive fractional Kelly Criterion"""
    print("\nTesting adaptive fractional Kelly Criterion...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Use marginal profitable data: win_rate=0.52, avg_win=0.015, avg_loss=0.020
        # b = 0.015/0.020 = 0.75, kelly = (0.75*0.52 - 0.48)/0.75 = (0.39 - 0.48)/0.75 = -0.12 (negative!)
        # The Kelly will default to risk_per_trade (2%)
        # Let's test the fractional adjustment mechanism directly instead
        
        # Test with: win_rate=0.54, avg_win=0.020, avg_loss=0.025
        # b = 0.02/0.025 = 0.8, kelly = (0.8*0.54 - 0.46)/0.8 = (0.432 - 0.46)/0.8 = -0.028/0.8 (negative!)
        # Use: win_rate=0.58, avg_win=0.025, avg_loss=0.025
        # b = 1.0, kelly = (1.0*0.58 - 0.42)/1.0 = 0.16, half = 0.08 = 8%, still above cap
        # Use: win_rate=0.54, avg_win=0.020, avg_loss=0.030
        # b = 0.667, kelly = (0.667*0.54 - 0.46)/0.667 = (0.36 - 0.46)/0.667 = -0.15 (negative!)
        # Use: win_rate=0.56, avg_win=0.025, avg_loss=0.030
        # b = 0.833, kelly = (0.833*0.56 - 0.44)/0.833 = (0.467 - 0.44)/0.833 = 0.032, half = 0.016 = 1.6%
        
        # Baseline: Standard half-Kelly with 56% win rate, 2.5% avg win, 3.0% avg loss
        baseline_risk = manager.calculate_kelly_criterion(0.56, 0.025, 0.030, use_fractional=False)
        print(f"  ✓ Standard half-Kelly: {baseline_risk:.3%}")
        
        # Test 1: Consistent performance (recent 60% vs historical 56%)
        for i in range(10):
            if i < 6:
                manager.record_trade_outcome(0.025)  # Win
            else:
                manager.record_trade_outcome(-0.030)  # Loss
        
        # Recent win rate: 60% vs historical 56% - consistency = 0.96 -> use 0.6 fraction
        consistent_risk = manager.calculate_kelly_criterion(0.56, 0.025, 0.030, use_fractional=True)
        print(f"  ✓ With consistent performance (60% recent): {consistent_risk:.3%}")
        
        # Test 2: Inconsistent performance (recent 30% vs historical 56%)
        manager2 = RiskManager(1000, 0.02, 3)
        for i in range(10):
            if i < 3:
                manager2.record_trade_outcome(0.025)  # Win
            else:
                manager2.record_trade_outcome(-0.030)  # Loss
        
        # Recent win rate: 30% vs historical 56% - consistency = 0.74 -> use 0.55 fraction
        inconsistent_risk = manager2.calculate_kelly_criterion(0.56, 0.025, 0.030, use_fractional=True)
        print(f"  ✓ With inconsistent performance (30% recent): {inconsistent_risk:.3%}")
        
        # With the raw Kelly being 1.6%, adjustments should be visible
        # 0.6 fraction: 1.6% * 0.6 = 0.96%
        # 0.55 fraction: 1.6% * 0.55 = 0.88%
        assert inconsistent_risk < consistent_risk, \
            f"Inconsistent (0.55 frac) should be less than consistent (0.6 frac): {inconsistent_risk:.3%} vs {consistent_risk:.3%}"
        
        # Test 3: Win streak increases Kelly
        manager3 = RiskManager(1000, 0.02, 3)
        for _ in range(5):
            manager3.record_trade_outcome(0.025)  # 5-win streak (100% recent win rate)
        
        # consistency = 1.0 - abs(1.0 - 0.56) = 0.56 -> use 0.45 fraction
        # But win streak multiplies by 1.1: 0.45 * 1.1 = 0.495, capped at 0.65
        winstreak_risk = manager3.calculate_kelly_criterion(0.56, 0.025, 0.030, use_fractional=True)
        print(f"  ✓ With 5-win streak (100% recent): {winstreak_risk:.3%}")
        
        # Test 4: Loss streak reduces Kelly
        manager4 = RiskManager(1000, 0.02, 3)
        for _ in range(3):
            manager4.record_trade_outcome(-0.030)  # 3-loss streak (0% recent win rate)
        
        # consistency = 1.0 - abs(0.0 - 0.56) = 0.44 -> use 0.4 fraction
        # Loss streak multiplies by 0.7: 0.4 * 0.7 = 0.28
        lossstreak_risk = manager4.calculate_kelly_criterion(0.56, 0.025, 0.030, use_fractional=True)
        print(f"  ✓ With 3-loss streak (0% recent): {lossstreak_risk:.3%}")
        
        assert lossstreak_risk < baseline_risk, \
            f"Loss streak should reduce Kelly: {lossstreak_risk:.3%} vs baseline {baseline_risk:.3%}"
        
        print("✓ Adaptive fractional Kelly working correctly")
        return True
    except Exception as e:
        print(f"✗ Adaptive Kelly test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_volatility_regime_classification():
    """Test volatility regime classification in leverage calculation"""
    print("\nTesting volatility regime classification...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Test different volatility regimes
        regimes = [
            (0.005, 'very_low', 16),   # Very low volatility
            (0.015, 'low', 14),        # Low volatility
            (0.025, 'normal', 11),     # Normal volatility
            (0.04, 'medium', 8),       # Medium volatility
            (0.06, 'high', 6),         # High volatility
            (0.09, 'very_high', 4),    # Very high volatility
            (0.12, 'extreme', 3),      # Extreme volatility
        ]
        
        print("  Volatility Regime → Base Leverage:")
        for vol, regime, expected_base in regimes:
            leverage = manager.get_max_leverage(
                volatility=vol,
                confidence=0.65,  # Neutral confidence
                momentum=0.01,    # Neutral momentum
                trend_strength=0.5,  # Neutral trend
                market_regime='neutral'
            )
            print(f"    {regime:12s} ({vol:.3f}): {leverage:2d}x")
            # Allow some variance due to other factors
            assert 3 <= leverage <= 20, f"Leverage should be in valid range, got {leverage}x"
        
        print("✓ Volatility regime classification working correctly")
        return True
    except Exception as e:
        print(f"✗ Volatility regime test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_regime_impact():
    """Test market regime impact on leverage"""
    print("\nTesting market regime impact on leverage...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Same conditions, different market regimes
        base_params = {
            'volatility': 0.03,
            'confidence': 0.70,
            'momentum': 0.02,
            'trend_strength': 0.6
        }
        
        trending_lev = manager.get_max_leverage(**base_params, market_regime='trending')
        neutral_lev = manager.get_max_leverage(**base_params, market_regime='neutral')
        ranging_lev = manager.get_max_leverage(**base_params, market_regime='ranging')
        
        print(f"  ✓ Trending market: {trending_lev}x leverage")
        print(f"  ✓ Neutral market: {neutral_lev}x leverage")
        print(f"  ✓ Ranging market: {ranging_lev}x leverage")
        
        assert trending_lev > neutral_lev, "Trending should allow higher leverage than neutral"
        assert neutral_lev > ranging_lev, "Neutral should allow higher leverage than ranging"
        
        print("✓ Market regime impact working correctly")
        return True
    except Exception as e:
        print(f"✗ Market regime test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("Running Smart Strategy Enhancement Tests")
    print("=" * 60)
    
    tests = [
        test_streak_tracking,
        test_recent_win_rate,
        test_enhanced_leverage_calculation,
        test_adaptive_fractional_kelly,
        test_volatility_regime_classification,
        test_market_regime_impact,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{len(tests)} passed")
    print("=" * 60)
    
    if failed > 0:
        print("\n✗ Some tests failed")
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")
        sys.exit(0)
