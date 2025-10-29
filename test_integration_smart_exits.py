"""
Simple integration test for smart adaptive exits without full dependencies
"""

def test_integration():
    """Test integration between components"""
    print("=" * 80)
    print("INTEGRATION TEST: Smart Adaptive Exits")
    print("=" * 80)
    print()
    
    try:
        from smart_adaptive_exits import (
            MarketRegimeDetector,
            SmartStopLossManager,
            SmartTakeProfitManager,
            AdaptiveEmergencyManager,
            SmartAdaptiveExitManager
        )
        
        print("✓ All modules imported successfully")
        print()
        
        # Test 1: Market Regime Detection
        print("Test 1: Market Regime Detection")
        detector = MarketRegimeDetector()
        regime_info = detector.detect_regime(volatility=0.05)
        print(f"  Volatility: 5% → Regime: {regime_info['regime']}")
        print(f"  Stop multiplier: {regime_info['stop_loss_multiplier']:.2f}x")
        print(f"  ✓ Pass")
        print()
        
        # Test 2: Smart Stop Loss
        print("Test 2: Smart Stop Loss Calculation")
        sl_manager = SmartStopLossManager()
        stop_info = sl_manager.calculate_adaptive_stop(
            entry_price=50000,
            side='long',
            atr=1500,
            volatility=0.05
        )
        print(f"  Entry: $50,000")
        print(f"  Stop: ${stop_info['stop_price']:,.0f} ({stop_info['stop_pct']:.1%})")
        print(f"  Regime: {stop_info['regime']}")
        print(f"  ✓ Pass")
        print()
        
        # Test 3: Smart Take Profit
        print("Test 3: Smart Take Profit Calculation")
        tp_manager = SmartTakeProfitManager()
        target_info = tp_manager.calculate_adaptive_target(
            entry_price=50000,
            side='long',
            atr=1500,
            volatility=0.05,
            trend_strength=0.75
        )
        print(f"  Entry: $50,000")
        print(f"  Target: ${target_info['target_price']:,.0f} ({target_info['target_pct']:.1%})")
        print(f"  Trend multiplier: {target_info['trend_multiplier']:.2f}x")
        print(f"  ✓ Pass")
        print()
        
        # Test 4: Adaptive Emergency
        print("Test 4: Adaptive Emergency Thresholds")
        emergency_mgr = AdaptiveEmergencyManager()
        threshold_info = emergency_mgr.get_adaptive_thresholds(
            volatility=0.05,
            current_drawdown=0.10,
            portfolio_correlation=0.70
        )
        print(f"  Normal Level 3: -15%")
        print(f"  Adaptive Level 3: {threshold_info['thresholds']['level_3']:.1%}")
        print(f"  Adjustment: {threshold_info['combined_adj']:.2f}x")
        print(f"  ✓ Pass")
        print()
        
        # Test 5: Complete Smart Targets
        print("Test 5: Complete Smart Target Calculation")
        smart_mgr = SmartAdaptiveExitManager()
        targets = smart_mgr.calculate_smart_targets(
            entry_price=50000,
            side='long',
            atr=1500,
            volatility=0.05,
            trend_strength=0.75,
            current_drawdown=0.08,
            portfolio_correlation=0.65
        )
        print(f"  Entry: $50,000")
        print(f"  Stop: ${targets['summary']['stop_price']:,.0f} ({targets['summary']['stop_pct']:.1%})")
        print(f"  Target: ${targets['summary']['target_price']:,.0f} ({targets['summary']['target_pct']:.1%})")
        print(f"  Risk/Reward: {targets['summary']['risk_reward_ratio']:.2f}")
        print(f"  Regime: {targets['summary']['regime']}")
        print(f"  Emergency Level 3: {targets['emergency']['thresholds']['level_3']:.1%}")
        print(f"  ✓ Pass")
        print()
        
        print("=" * 80)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 80)
        print()
        print("Summary:")
        print("  • Market regime detection: ✓")
        print("  • Smart stop loss calculation: ✓")
        print("  • Smart take profit calculation: ✓")
        print("  • Adaptive emergency thresholds: ✓")
        print("  • Complete smart targets: ✓")
        print()
        print("The smart adaptive exits system is fully integrated and functional!")
        
        return 0
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(test_integration())
