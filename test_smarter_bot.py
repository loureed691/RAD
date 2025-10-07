"""
Test new smarter bot features: Kelly Criterion and Early Exit Intelligence
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_kelly_criterion():
    """Test Kelly Criterion calculation in ML model"""
    print("\n" + "="*60)
    print("Testing Kelly Criterion Position Sizing")
    print("="*60)
    
    from ml_model import MLModel
    
    model = MLModel()
    
    # Test with insufficient trades (should return 0)
    print("\n1. Testing with insufficient trades (< 20)...")
    kelly = model.get_kelly_fraction()
    assert kelly == 0.0, "Kelly should be 0 with insufficient trades"
    print(f"   ✓ Kelly fraction: {kelly:.4f} (correctly returns 0)")
    
    # Simulate 25 trades with 60% win rate
    print("\n2. Simulating 25 trades (60% win rate, 2:1 reward/risk)...")
    model.performance_metrics['total_trades'] = 25
    model.performance_metrics['wins'] = 15
    model.performance_metrics['losses'] = 10
    model.performance_metrics['win_rate'] = 0.60
    model.performance_metrics['avg_profit'] = 0.04  # 4% avg win
    model.performance_metrics['avg_loss'] = 0.02    # 2% avg loss
    
    kelly = model.get_kelly_fraction()
    print(f"   ✓ Kelly fraction: {kelly:.4f}")
    print(f"   ✓ Win rate: {model.performance_metrics['win_rate']:.2%}")
    print(f"   ✓ Avg profit: {model.performance_metrics['avg_profit']:.2%}")
    print(f"   ✓ Avg loss: {model.performance_metrics['avg_loss']:.2%}")
    
    # Verify Kelly is reasonable (should be positive and < 0.25)
    assert kelly > 0, "Kelly should be positive with winning strategy"
    assert kelly <= 0.25, "Kelly should be capped at 25%"
    print(f"   ✓ Kelly in valid range (0 < {kelly:.4f} <= 0.25)")
    
    # Calculate full Kelly for comparison
    b = model.performance_metrics['avg_profit'] / model.performance_metrics['avg_loss']
    p = model.performance_metrics['win_rate']
    q = 1 - p
    full_kelly = (b * p - q) / b
    expected_half_kelly = full_kelly * 0.5
    print(f"   ✓ Full Kelly: {full_kelly:.4f}")
    print(f"   ✓ Half-Kelly (expected): {expected_half_kelly:.4f}")
    print(f"   ✓ Actual: {kelly:.4f}")
    
    # Test with negative expectancy (should return 0)
    print("\n3. Testing with negative expectancy (losing strategy)...")
    model.performance_metrics['win_rate'] = 0.30  # 30% win rate
    model.performance_metrics['avg_profit'] = 0.02  # 2% avg win
    model.performance_metrics['avg_loss'] = 0.04    # 4% avg loss (worse than wins)
    
    kelly = model.get_kelly_fraction()
    assert kelly == 0.0, "Kelly should be 0 with negative expectancy"
    print(f"   ✓ Kelly fraction: {kelly:.4f} (correctly returns 0 for losing strategy)")
    
    print("\n✓ Kelly Criterion tests passed!")
    return True

def test_early_exit_intelligence():
    """Test early exit logic in Position class"""
    print("\n" + "="*60)
    print("Testing Early Exit Intelligence")
    print("="*60)
    
    from position_manager import Position
    from datetime import datetime, timedelta
    
    # Test 1: Rapid loss acceleration
    print("\n1. Testing rapid loss acceleration exit...")
    pos = Position('BTC/USDT:USDT', 'long', 50000, 1.0, 10, 48000, 52000)
    
    # Simulate 30 minutes have passed (updated from 15 minutes)
    pos.entry_time = datetime.now() - timedelta(minutes=35)
    
    # Simulate rapid loss (-2.8% to exceed -2.5% threshold)
    current_price = 48600  # -2.8% loss with 10x leverage
    current_pnl = pos.get_pnl(current_price)
    
    # Simulate consecutive negative updates (4 required now)
    pos.consecutive_negative_updates = 4
    pos.max_adverse_excursion = -0.028
    
    should_exit, reason = pos.should_early_exit(current_price, current_pnl)
    print(f"   Current P/L: {current_pnl:.2%}")
    print(f"   Consecutive negative updates: {pos.consecutive_negative_updates}")
    print(f"   Should exit: {should_exit} (reason: {reason})")
    assert should_exit == True, "Should exit on rapid loss"
    assert reason == 'early_exit_rapid_loss', f"Expected rapid_loss, got {reason}"
    print("   ✓ Rapid loss exit working correctly")
    
    # Test 2: Extended time underwater
    print("\n2. Testing extended time underwater exit...")
    pos2 = Position('ETH/USDT:USDT', 'long', 3000, 1.0, 10, 2950, 3100)
    
    # Simulate 4.5 hours have passed (updated from 2.5 hours)
    pos2.entry_time = datetime.now() - timedelta(hours=4, minutes=30)
    
    # Still losing after 4.5 hours (-1.8% to exceed -1.5% threshold)
    current_price = 2945.5  # -1.8% loss
    current_pnl = pos2.get_pnl(current_price)
    
    should_exit, reason = pos2.should_early_exit(current_price, current_pnl)
    print(f"   Time in trade: 4.5 hours")
    print(f"   Current P/L: {current_pnl:.2%}")
    print(f"   Should exit: {should_exit} (reason: {reason})")
    assert should_exit == True, "Should exit after extended time underwater"
    assert reason == 'early_exit_extended_loss', f"Expected extended_loss, got {reason}"
    print("   ✓ Extended underwater exit working correctly")
    
    # Test 3: Maximum adverse excursion
    print("\n3. Testing max adverse excursion exit...")
    pos3 = Position('SOL/USDT:USDT', 'long', 100, 1.0, 10, 97, 105)
    
    # Simulate high drawdown (-3.6% to exceed -3.5% threshold)
    pos3.max_adverse_excursion = -0.036  # -3.6% peak loss
    current_price = 97.25  # -2.75% current loss (exceeds -2.5% threshold)
    current_pnl = pos3.get_pnl(current_price)
    
    should_exit, reason = pos3.should_early_exit(current_price, current_pnl)
    print(f"   Max adverse excursion: {pos3.max_adverse_excursion:.2%}")
    print(f"   Current P/L: {current_pnl:.2%}")
    print(f"   Should exit: {should_exit} (reason: {reason})")
    assert should_exit == True, "Should exit on high adverse excursion"
    assert reason == 'early_exit_mae_threshold', f"Expected mae_threshold, got {reason}"
    print("   ✓ Max adverse excursion exit working correctly")
    
    # Test 4: Failed reversal
    print("\n4. Testing failed reversal exit...")
    pos4 = Position('BNB/USDT:USDT', 'long', 300, 1.0, 10, 295, 310)
    
    # Was up at some point (1.2% to exceed 1% threshold)
    pos4.max_favorable_excursion = 0.012  # Was up 1.2%
    
    # Now falling significantly (-2.1% to exceed -2% threshold)
    current_price = 293.7  # -2.1% loss
    current_pnl = pos4.get_pnl(current_price)
    
    should_exit, reason = pos4.should_early_exit(current_price, current_pnl)
    print(f"   Max favorable excursion: {pos4.max_favorable_excursion:.2%}")
    print(f"   Current P/L: {current_pnl:.2%}")
    print(f"   Should exit: {should_exit} (reason: {reason})")
    assert should_exit == True, "Should exit on failed reversal"
    assert reason == 'early_exit_failed_reversal', f"Expected failed_reversal, got {reason}"
    print("   ✓ Failed reversal exit working correctly")
    
    # Test 5: No exit on profitable position
    print("\n5. Testing no exit on profitable position...")
    pos5 = Position('AVAX/USDT:USDT', 'long', 20, 1.0, 10, 19, 22)
    
    current_price = 20.5  # +2.5% profit
    current_pnl = pos5.get_pnl(current_price)
    
    should_exit, reason = pos5.should_early_exit(current_price, current_pnl)
    print(f"   Current P/L: {current_pnl:.2%} (profitable)")
    print(f"   Should exit: {should_exit}")
    assert should_exit == False, "Should not exit profitable position early"
    print("   ✓ No false exits on profitable positions")
    
    # Test 6: No premature exit - position should be allowed to recover
    print("\n6. Testing no premature exits (conservative thresholds)...")
    pos6 = Position('LINK/USDT:USDT', 'long', 15, 1.0, 10, 14.5, 16)
    
    # Position at 20 minutes with -1.8% loss - should NOT exit (needs 30 min + -2.5%)
    pos6.entry_time = datetime.now() - timedelta(minutes=20)
    current_price = 14.73  # -1.8% loss
    current_pnl = pos6.get_pnl(current_price)
    pos6.consecutive_negative_updates = 3
    
    should_exit, reason = pos6.should_early_exit(current_price, current_pnl)
    print(f"   Time in trade: 20 minutes (less than 30 min threshold)")
    print(f"   Current P/L: {current_pnl:.2%} (above -2.5% threshold)")
    print(f"   Should exit: {should_exit}")
    assert should_exit == False, "Should not exit before 30 minutes with only -1.8% loss"
    print("   ✓ Position allowed to recover (not exited prematurely)")
    
    # Test 7: No premature exit - extended time but loss not severe enough
    print("\n7. Testing no premature exit on extended time with minor loss...")
    pos7 = Position('ADA/USDT:USDT', 'long', 0.5, 1.0, 10, 0.48, 0.52)
    
    # Position at 3 hours with -1.2% loss - should NOT exit (needs 4 hours + -1.5%)
    pos7.entry_time = datetime.now() - timedelta(hours=3)
    current_price = 0.494  # -1.2% loss
    current_pnl = pos7.get_pnl(current_price)
    
    should_exit, reason = pos7.should_early_exit(current_price, current_pnl)
    print(f"   Time in trade: 3 hours (less than 4 hour threshold)")
    print(f"   Current P/L: {current_pnl:.2%} (above -1.5% threshold)")
    print(f"   Should exit: {should_exit}")
    assert should_exit == False, "Should not exit at 3 hours with only -1.2% loss"
    print("   ✓ Position allowed more time to recover")
    
    print("\n✓ Early exit intelligence tests passed!")
    return True

def test_adaptive_threshold_momentum():
    """Test momentum-based adaptive threshold"""
    print("\n" + "="*60)
    print("Testing Momentum-Based Adaptive Threshold")
    print("="*60)
    
    from ml_model import MLModel
    
    model = MLModel()
    
    # Test with insufficient trades
    print("\n1. Testing with insufficient trades (< 10)...")
    model.performance_metrics['total_trades'] = 5
    threshold = model.get_adaptive_confidence_threshold()
    assert threshold == 0.6, "Should return base threshold with insufficient trades"
    print(f"   ✓ Threshold: {threshold:.2f} (base threshold)")
    
    # Test with hot streak (recent wins)
    print("\n2. Testing hot streak (recent 75% win rate)...")
    model.performance_metrics['total_trades'] = 25
    model.performance_metrics['win_rate'] = 0.60  # Overall 60%
    model.performance_metrics['recent_trades'] = [
        0.02, 0.03, -0.01, 0.04, 0.02,  # 4 wins, 1 loss
        0.03, 0.02, 0.01, 0.03, 0.02,   # 5 wins
        0.04, 0.02, 0.03, -0.01, 0.02,  # 4 wins, 1 loss
        0.03, 0.02, 0.04, 0.02, 0.03    # 5 wins
    ]  # 18 wins / 20 = 90% recent win rate
    
    threshold = model.get_adaptive_confidence_threshold()
    print(f"   Recent win rate: 90%")
    print(f"   Overall win rate: 60%")
    print(f"   Threshold: {threshold:.4f}")
    assert threshold < 0.6, "Threshold should be lower during hot streak"
    print(f"   ✓ Threshold lowered for hot streak (more aggressive)")
    
    # Test with cold streak (recent losses)
    print("\n3. Testing cold streak (recent 25% win rate)...")
    model.performance_metrics['recent_trades'] = [
        -0.02, -0.03, 0.01, -0.04, -0.02,  # 1 win, 4 losses
        -0.03, -0.02, -0.01, -0.03, 0.02,  # 1 win, 4 losses
        -0.04, -0.02, 0.03, -0.01, -0.02,  # 1 win, 4 losses
        -0.03, 0.02, -0.04, -0.02, -0.03   # 1 win, 4 losses
    ]  # 4 wins / 20 = 20% recent win rate
    
    threshold = model.get_adaptive_confidence_threshold()
    print(f"   Recent win rate: 20%")
    print(f"   Overall win rate: 60%")
    print(f"   Threshold: {threshold:.4f}")
    assert threshold > 0.6, "Threshold should be higher during cold streak"
    print(f"   ✓ Threshold raised for cold streak (more conservative)")
    
    # Verify bounds
    print("\n4. Verifying threshold bounds (0.52 to 0.75)...")
    assert threshold >= 0.52 and threshold <= 0.75, "Threshold should be within bounds"
    print(f"   ✓ Threshold {threshold:.4f} is within bounds [0.52, 0.75]")
    
    print("\n✓ Adaptive threshold tests passed!")
    return True

if __name__ == '__main__':
    try:
        # Run all tests
        success = True
        success = test_kelly_criterion() and success
        success = test_early_exit_intelligence() and success
        success = test_adaptive_threshold_momentum() and success
        
        print("\n" + "="*60)
        if success:
            print("✅ ALL SMARTER BOT TESTS PASSED!")
        else:
            print("❌ SOME TESTS FAILED")
        print("="*60)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
