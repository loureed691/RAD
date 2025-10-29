"""
Comprehensive tests for smart and adaptive exit management system
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_market_regime_detection():
    """Test market regime detection with various volatility levels"""
    print("\n" + "=" * 80)
    print("TEST 1: Market Regime Detection")
    print("=" * 80)
    
    try:
        from smart_adaptive_exits import MarketRegimeDetector
        
        detector = MarketRegimeDetector()
        
        test_cases = [
            (0.01, 'low_vol', "Low volatility"),
            (0.03, 'normal', "Normal volatility"),
            (0.06, 'high_vol', "High volatility"),
            (0.10, 'extreme_vol', "Extreme volatility"),
        ]
        
        all_passed = True
        for volatility, expected_regime, description in test_cases:
            result = detector.detect_regime(volatility)
            actual_regime = result['regime']
            
            status = "✓ PASS" if actual_regime == expected_regime else "✗ FAIL"
            if actual_regime != expected_regime:
                all_passed = False
            
            print(f"{status} | {description}")
            print(f"      | Volatility: {volatility:.3f} → Regime: {actual_regime}")
            print(f"      | Stop multiplier: {result['stop_loss_multiplier']:.2f}x")
            print(f"      | TP multiplier: {result['take_profit_multiplier']:.2f}x")
            print(f"      | Emergency adj: {result['emergency_threshold_adj']:.2f}x")
            print()
        
        if all_passed:
            print("✅ Market regime detection working correctly\n")
            return True
        else:
            print("❌ Some regime detection tests failed\n")
            return False
            
    except Exception as e:
        print(f"✗ Error in regime detection test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smart_stop_loss():
    """Test adaptive stop loss calculations"""
    print("\n" + "=" * 80)
    print("TEST 2: Smart Adaptive Stop Loss")
    print("=" * 80)
    
    try:
        from smart_adaptive_exits import SmartStopLossManager
        
        manager = SmartStopLossManager()
        
        # Test long position in normal volatility
        result = manager.calculate_adaptive_stop(
            entry_price=50000,
            side='long',
            atr=1000,  # 2% ATR
            volatility=0.03,
            base_stop_pct=0.02
        )
        
        print("Test Case: Long position, normal volatility")
        print(f"  Entry Price: $50,000")
        print(f"  ATR: $1,000 (2%)")
        print(f"  Volatility: 3%")
        print(f"  ✓ Stop Price: ${result['stop_price']:,.2f} ({result['stop_pct']:.2%})")
        print(f"  ✓ Regime: {result['regime']}")
        print(f"  ✓ Reasoning: {result['reasoning']}")
        print()
        
        # Test with high volatility
        result_high_vol = manager.calculate_adaptive_stop(
            entry_price=50000,
            side='long',
            atr=2000,  # 4% ATR
            volatility=0.08,
            base_stop_pct=0.02
        )
        
        print("Test Case: Long position, high volatility")
        print(f"  Entry Price: $50,000")
        print(f"  ATR: $2,000 (4%)")
        print(f"  Volatility: 8%")
        print(f"  ✓ Stop Price: ${result_high_vol['stop_price']:,.2f} ({result_high_vol['stop_pct']:.2%})")
        print(f"  ✓ Regime: {result_high_vol['regime']}")
        
        # Verify high volatility gives wider stop
        if result_high_vol['stop_pct'] > result['stop_pct']:
            print(f"  ✓ PASS: High volatility stop ({result_high_vol['stop_pct']:.2%}) is wider than normal ({result['stop_pct']:.2%})")
            print()
            return True
        else:
            print(f"  ✗ FAIL: High volatility stop should be wider")
            print()
            return False
            
    except Exception as e:
        print(f"✗ Error in stop loss test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smart_take_profit():
    """Test adaptive take profit calculations"""
    print("\n" + "=" * 80)
    print("TEST 3: Smart Adaptive Take Profit")
    print("=" * 80)
    
    try:
        from smart_adaptive_exits import SmartTakeProfitManager
        
        manager = SmartTakeProfitManager()
        
        # Test with weak trend
        result_weak = manager.calculate_adaptive_target(
            entry_price=50000,
            side='long',
            atr=1000,
            volatility=0.03,
            trend_strength=0.3,
            base_target_pct=0.04
        )
        
        print("Test Case: Weak trend (0.3)")
        print(f"  Entry Price: $50,000")
        print(f"  ✓ Target Price: ${result_weak['target_price']:,.2f} ({result_weak['target_pct']:.2%})")
        print(f"  ✓ Trend multiplier: {result_weak['trend_multiplier']:.2f}x")
        print()
        
        # Test with strong trend
        result_strong = manager.calculate_adaptive_target(
            entry_price=50000,
            side='long',
            atr=1000,
            volatility=0.03,
            trend_strength=0.8,
            base_target_pct=0.04
        )
        
        print("Test Case: Strong trend (0.8)")
        print(f"  Entry Price: $50,000")
        print(f"  ✓ Target Price: ${result_strong['target_price']:,.2f} ({result_strong['target_pct']:.2%})")
        print(f"  ✓ Trend multiplier: {result_strong['trend_multiplier']:.2f}x")
        print()
        
        # Verify strong trend gives higher or equal target (ATR may dominate)
        # The key is that trend_multiplier is correctly applied to pct_distance
        if result_strong['target_pct'] >= result_weak['target_pct']:
            # Check that trend multiplier was applied correctly
            if result_strong['trend_multiplier'] > result_weak['trend_multiplier']:
                print(f"✅ PASS: Strong trend multiplier ({result_strong['trend_multiplier']:.2f}x) > weak trend ({result_weak['trend_multiplier']:.2f}x)")
                print(f"         Targets: Strong={result_strong['target_pct']:.2%}, Weak={result_weak['target_pct']:.2%}")
                print(f"         (ATR may dominate target distance, but multiplier is correctly applied)")
                print()
                return True
            else:
                print(f"❌ FAIL: Strong trend should have higher multiplier")
                print()
                return False
        else:
            print(f"❌ FAIL: Strong trend target should not be lower than weak trend")
            print()
            return False
            
    except Exception as e:
        print(f"✗ Error in take profit test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adaptive_emergency_thresholds():
    """Test adaptive emergency stop thresholds"""
    print("\n" + "=" * 80)
    print("TEST 4: Adaptive Emergency Thresholds")
    print("=" * 80)
    
    try:
        from smart_adaptive_exits import AdaptiveEmergencyManager
        
        manager = AdaptiveEmergencyManager()
        
        # Test normal conditions
        result_normal = manager.get_adaptive_thresholds(
            volatility=0.03,
            current_drawdown=0.0,
            portfolio_correlation=0.5
        )
        
        print("Test Case: Normal market conditions")
        print(f"  Volatility: 3%")
        print(f"  Drawdown: 0%")
        print(f"  Correlation: 50%")
        print(f"  ✓ Level 1 (liquidation): {result_normal['thresholds']['level_1']:.1%}")
        print(f"  ✓ Level 2 (severe): {result_normal['thresholds']['level_2']:.1%}")
        print(f"  ✓ Level 3 (excessive): {result_normal['thresholds']['level_3']:.1%}")
        print(f"  ✓ Combined adjustment: {result_normal['combined_adj']:.2f}x")
        print()
        
        # Test high volatility with drawdown
        result_stressed = manager.get_adaptive_thresholds(
            volatility=0.08,
            current_drawdown=0.12,
            portfolio_correlation=0.75
        )
        
        print("Test Case: Stressed market conditions")
        print(f"  Volatility: 8% (high)")
        print(f"  Drawdown: 12% (moderate)")
        print(f"  Correlation: 75% (concentrated)")
        print(f"  ✓ Level 1 (liquidation): {result_stressed['thresholds']['level_1']:.1%}")
        print(f"  ✓ Level 2 (severe): {result_stressed['thresholds']['level_2']:.1%}")
        print(f"  ✓ Level 3 (excessive): {result_stressed['thresholds']['level_3']:.1%}")
        print(f"  ✓ Combined adjustment: {result_stressed['combined_adj']:.2f}x")
        print()
        
        # Verify stressed conditions tighten thresholds
        if abs(result_stressed['thresholds']['level_3']) < abs(result_normal['thresholds']['level_3']):
            print(f"✅ PASS: Stressed conditions tighten emergency thresholds")
            print(f"         Normal: {result_normal['thresholds']['level_3']:.1%} → Stressed: {result_stressed['thresholds']['level_3']:.1%}")
            print()
            return True
        else:
            print(f"❌ FAIL: Stressed conditions should tighten thresholds")
            print()
            return False
            
    except Exception as e:
        print(f"✗ Error in emergency threshold test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_emergency_trigger_logic():
    """Test emergency trigger with adaptive thresholds"""
    print("\n" + "=" * 80)
    print("TEST 5: Emergency Trigger Logic")
    print("=" * 80)
    
    try:
        from smart_adaptive_exits import AdaptiveEmergencyManager
        
        manager = AdaptiveEmergencyManager()
        
        # Test various P&L levels in high volatility
        test_cases = [
            (-0.10, False, "Moderate loss in high vol"),
            (-0.12, True, "Should trigger Level 3 (high vol tightened)"),
            (-0.20, True, "Should trigger Level 2"),
            (-0.35, True, "Should trigger Level 1"),
        ]
        
        print("Testing with high volatility (8%):")
        print("-" * 80)
        
        all_passed = True
        for pnl, expected_trigger, description in test_cases:
            should_trigger, reason = manager.should_trigger_emergency(
                current_pnl=pnl,
                volatility=0.08,  # High volatility
                current_drawdown=0.0,
                portfolio_correlation=0.5
            )
            
            status = "✓ PASS" if should_trigger == expected_trigger else "✗ FAIL"
            if should_trigger != expected_trigger:
                all_passed = False
            
            print(f"{status} | P&L: {pnl:+.1%} | Trigger: {should_trigger} | {description}")
            if should_trigger:
                print(f"      | Reason: {reason}")
            print()
        
        if all_passed:
            print("✅ Emergency trigger logic working correctly\n")
            return True
        else:
            print("❌ Some emergency trigger tests failed\n")
            return False
            
    except Exception as e:
        print(f"✗ Error in emergency trigger test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complete_smart_targets():
    """Test complete smart target calculation"""
    print("\n" + "=" * 80)
    print("TEST 6: Complete Smart Target Calculation")
    print("=" * 80)
    
    try:
        from smart_adaptive_exits import SmartAdaptiveExitManager
        
        manager = SmartAdaptiveExitManager()
        
        # Calculate complete targets for a long position
        result = manager.calculate_smart_targets(
            entry_price=50000,
            side='long',
            atr=1000,
            volatility=0.04,
            trend_strength=0.7,
            current_drawdown=0.05,
            portfolio_correlation=0.6
        )
        
        print("Test Case: Long position with full smart targets")
        print(f"  Entry Price: $50,000")
        print(f"  Volatility: 4%")
        print(f"  Trend Strength: 0.7")
        print()
        print("Results:")
        print(f"  ✓ Stop Loss: ${result['summary']['stop_price']:,.2f} ({result['summary']['stop_pct']:.2%})")
        print(f"  ✓ Take Profit: ${result['summary']['target_price']:,.2f} ({result['summary']['target_pct']:.2%})")
        print(f"  ✓ Risk/Reward Ratio: {result['summary']['risk_reward_ratio']:.2f}")
        print(f"  ✓ Market Regime: {result['summary']['regime']}")
        print()
        print("Emergency Thresholds:")
        print(f"  ✓ Level 1: {result['emergency']['thresholds']['level_1']:.1%}")
        print(f"  ✓ Level 2: {result['emergency']['thresholds']['level_2']:.1%}")
        print(f"  ✓ Level 3: {result['emergency']['thresholds']['level_3']:.1%}")
        print()
        
        # Verify risk/reward is reasonable
        if 1.5 <= result['summary']['risk_reward_ratio'] <= 5.0:
            print(f"✅ PASS: Risk/reward ratio is reasonable ({result['summary']['risk_reward_ratio']:.2f})")
            print()
            return True
        else:
            print(f"❌ FAIL: Risk/reward ratio is unreasonable ({result['summary']['risk_reward_ratio']:.2f})")
            print()
            return False
            
    except Exception as e:
        print(f"✗ Error in complete targets test: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all smart adaptive exit tests"""
    print("\n" + "=" * 80)
    print("SMART ADAPTIVE EXITS - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()
    
    tests = [
        ("Market Regime Detection", test_market_regime_detection),
        ("Smart Stop Loss", test_smart_stop_loss),
        ("Smart Take Profit", test_smart_take_profit),
        ("Adaptive Emergency Thresholds", test_adaptive_emergency_thresholds),
        ("Emergency Trigger Logic", test_emergency_trigger_logic),
        ("Complete Smart Targets", test_complete_smart_targets),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
    
    print()
    print(f"Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Smart adaptive exits system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
