"""
Test new smarter bot features: Kelly Criterion and Early Exit Intelligence
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_kelly_criterion():
    """Test Kelly Criterion calculation in risk manager"""
    print("\n" + "="*60)
    print("Testing Kelly Criterion Position Sizing")
    print("="*60)
    
    from risk_manager import RiskManager
    
    # Initialize risk manager
    risk_mgr = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
    
    # Test 1: With insufficient trades (should return default risk)
    print("\n1. Testing with insufficient trades (< 20)...")
    kelly = risk_mgr.calculate_kelly_criterion(win_rate=0.6, avg_win=0.04, avg_loss=0.02)
    # With no trade history (recent_trades empty), should still calculate but use half-Kelly baseline
    print(f"   ✓ Kelly fraction: {kelly:.4f}")
    assert kelly > 0, "Kelly should be positive with winning parameters"
    assert kelly <= 0.035, "Kelly should be capped at 3.5%"
    
    # Test 2: Simulate 25 trades with 60% win rate
    print("\n2. Simulating 25 trades (60% win rate, 2:1 reward/risk)...")
    # Record trades to populate recent_trades for adaptive logic
    for i in range(25):
        if i < 15:  # 15 wins
            risk_mgr.record_trade_outcome(0.04)  # 4% profit
        else:  # 10 losses
            risk_mgr.record_trade_outcome(-0.02)  # 2% loss
    
    # Now calculate Kelly with trade history
    win_rate = risk_mgr.get_win_rate()
    avg_profit = risk_mgr.get_avg_win()
    avg_loss = risk_mgr.get_avg_loss()
    
    kelly = risk_mgr.calculate_kelly_criterion(win_rate, avg_profit, avg_loss, use_fractional=True)
    
    print(f"   ✓ Kelly fraction: {kelly:.4f}")
    print(f"   ✓ Win rate: {win_rate:.2%}")
    print(f"   ✓ Avg profit: {avg_profit:.2%}")
    print(f"   ✓ Avg loss: {avg_loss:.2%}")
    
    # Verify Kelly is reasonable (should be positive and capped properly)
    assert kelly > 0, "Kelly should be positive with winning strategy"
    assert kelly <= 0.035, "Kelly should be capped at 3.5%"
    print(f"   ✓ Kelly in valid range (0 < {kelly:.4f} <= 0.035)")
    
    # Calculate full Kelly for comparison
    b = avg_profit / avg_loss
    p = win_rate
    q = 1 - p
    full_kelly = (b * p - q) / b
    print(f"   ✓ Full Kelly: {full_kelly:.4f}")
    print(f"   ✓ Adaptive fractional Kelly: {kelly:.4f}")
    
    # Test 3: With negative expectancy (should return default risk)
    print("\n3. Testing with negative expectancy (losing strategy)...")
    kelly_negative = risk_mgr.calculate_kelly_criterion(
        win_rate=0.30,   # 30% win rate
        avg_win=0.02,    # 2% avg win
        avg_loss=0.04,   # 4% avg loss
        use_fractional=True
    )
    # With negative expectancy, Kelly will be negative, function should return default risk_per_trade
    print(f"   ✓ Kelly fraction: {kelly_negative:.4f}")
    assert kelly_negative >= 0.005, "Should return at least minimum risk"
    print(f"   ✓ Correctly handles negative expectancy")
    
    print("\n✓ Kelly Criterion tests passed!")
    return True

def test_smarter_stop_loss():
    """Test smarter stop loss logic with time-based adjustments"""
    print("\n" + "="*60)
    print("Testing Smarter Stop Loss Logic")
    print("="*60)
    
    from position_manager import Position
    from datetime import datetime, timedelta
    
    # Test 1: Normal stop loss triggers correctly
    print("\n1. Testing normal stop loss trigger...")
    pos = Position('BTC/USDT:USDT', 'long', 50000, 1.0, 10, 48000, 52000)
    
    current_price = 47900  # Below stop loss
    should_close, reason = pos.should_close(current_price)
    print(f"   Entry: ${pos.entry_price:,.0f}")
    print(f"   Stop Loss: ${pos.stop_loss:,.0f}")
    print(f"   Current Price: ${current_price:,.0f}")
    print(f"   Should close: {should_close} (reason: {reason})")
    assert should_close == True, "Should close at stop loss"
    assert reason == 'stop_loss', f"Expected stop_loss, got {reason}"
    print("   ✓ Normal stop loss working correctly")
    
    # Test 2: Stalled position triggers tighter stop
    print("\n2. Testing stalled position stop loss...")
    pos2 = Position('ETH/USDT:USDT', 'long', 3000, 1.0, 10, 2900, 3200)
    
    # Simulate 5 hours have passed with minimal movement
    pos2.entry_time = datetime.now() - timedelta(hours=5)
    
    # Price slightly below entry (within 1%)
    current_price = 2970  # -1% from entry
    should_close, reason = pos2.should_close(current_price)
    print(f"   Time in trade: 5 hours")
    print(f"   Entry: ${pos2.entry_price:,.0f}")
    print(f"   Current Price: ${current_price:,.0f}")
    print(f"   P/L: {pos2.get_pnl(current_price):.2%}")
    print(f"   Should close: {should_close} (reason: {reason})")
    assert should_close == True, "Should close stalled position"
    assert reason == 'stop_loss_stalled_position', f"Expected stop_loss_stalled_position, got {reason}"
    print("   ✓ Stalled position stop loss working correctly")
    
    # Test 3: Profitable position doesn't trigger stalled stop
    print("\n3. Testing profitable position not affected by stalled stop...")
    pos3 = Position('SOL/USDT:USDT', 'long', 100, 1.0, 10, 95, 102)  # TP closer
    
    # Simulate 5 hours with small profit
    pos3.entry_time = datetime.now() - timedelta(hours=5)
    
    # Price with small profit (0.5% price move = 5% ROI with 10x, at threshold but TP is close)
    current_price = 100.5  # +0.5% from entry, +5% ROI with 10x
    should_close, reason = pos3.should_close(current_price)
    pnl = pos3.get_pnl(current_price)
    distance_to_tp = (pos3.take_profit - current_price) / current_price
    print(f"   Time in trade: 5 hours")
    print(f"   Entry: ${pos3.entry_price:.2f}")
    print(f"   Take Profit: ${pos3.take_profit:.2f}")
    print(f"   Current Price: ${current_price:.2f}")
    print(f"   P/L: {pnl:.2%}")
    print(f"   Distance to TP: {distance_to_tp:.2%}")
    print(f"   Should close: {should_close} (reason: {reason})")
    # Should not close - profit is 5% but TP is only 1.5% away (< 5% threshold)
    assert should_close == False, f"Should not close when TP is close, got reason: {reason}"
    print("   ✓ Profitable positions not affected by stalled stop when TP is close")
    
    print("\n✓ Smarter stop loss tests passed!")
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
        success = test_smarter_stop_loss() and success
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
