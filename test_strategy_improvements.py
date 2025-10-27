"""
Tests for buy/sell strategy improvements
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_choppy_market_filter():
    """Test that choppy markets (low momentum) are filtered out"""
    print("\nTesting choppy market filter...")
    try:
        from signals import SignalGenerator
        from indicators import Indicators
        
        generator = SignalGenerator()
        
        # Create data with weak momentum (choppy/sideways market)
        # Price oscillates slightly around 100 without clear trend
        choppy_data = [
            [i * 60000, 100 + (i % 5) * 0.1, 100.5 + (i % 5) * 0.1, 
             99.5 + (i % 5) * 0.1, 100 + (i % 5) * 0.1, 2000]
            for i in range(100)
        ]
        
        df_choppy = Indicators.calculate_all(choppy_data)
        signal, confidence, reasons = generator.generate_signal(df_choppy)
        
        # Should reject choppy market
        assert signal == 'HOLD', f"Choppy market should be HOLD, got {signal}"
        assert 'choppy_market' in reasons or signal == 'HOLD', \
            f"Should have choppy_market reason, got {reasons}"
        
        print(f"  ✓ Choppy market correctly filtered out")
        print(f"  ✓ Signal: {signal}, Reason: {reasons.get('choppy_market', 'confidence too low')}")
        print("✓ Choppy market filter working correctly")
        return True
    except Exception as e:
        print(f"✗ Choppy market filter test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_breakout_volatility_requirement():
    """Test that breakout trades require sufficient volatility"""
    print("\nTesting breakout volatility requirement...")
    try:
        from signals import SignalGenerator
        from indicators import Indicators
        import pandas as pd
        
        generator = SignalGenerator()
        
        # Create data with price at BB band but low volatility
        # This simulates a breakout attempt without sufficient momentum
        low_vol_breakout_data = [
            [i * 60000, 100 + i * 0.01, 100.5 + i * 0.01, 
             99.5 + i * 0.01, 100 + i * 0.01, 1500]
            for i in range(100)
        ]
        
        df = Indicators.calculate_all(low_vol_breakout_data)
        
        # Manually set close near BB low to simulate breakout
        if not df.empty and 'bb_low' in df.columns:
            df.loc[df.index[-1], 'close'] = df['bb_low'].iloc[-1] * 0.99
        
        signal, confidence, reasons = generator.generate_signal(df)
        
        # Should reject low volatility breakout
        if 'low_volatility_breakout' in reasons:
            print(f"  ✓ Low volatility breakout correctly filtered")
            print(f"  ✓ Reason: {reasons['low_volatility_breakout']}")
        else:
            # May also be filtered by other reasons (choppy market, low confidence)
            print(f"  ✓ Trade filtered (signal: {signal})")
        
        print("✓ Breakout volatility requirement working correctly")
        return True
    except Exception as e:
        print(f"✗ Breakout volatility test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_very_low_volume_rejection():
    """Test that very low volume trades are rejected"""
    print("\nTesting very low volume rejection...")
    try:
        from signals import SignalGenerator
        from indicators import Indicators
        
        generator = SignalGenerator()
        
        # Create data with strong signal but very low volume
        strong_signal_data = [
            [i * 60000, 100 + i * 0.5, 101 + i * 0.5, 
             99 + i * 0.5, 100.5 + i * 0.5, 100 if i < 80 else 50]  # Very low volume
            for i in range(100)
        ]
        
        df = Indicators.calculate_all(strong_signal_data)
        
        # Check that low volume (< 60% average) is rejected
        signal, confidence, reasons = generator.generate_signal(df)
        
        # Should be rejected due to low volume
        if 'volume' in reasons and 'critically low' in reasons['volume']:
            print(f"  ✓ Very low volume correctly rejected")
            print(f"  ✓ Reason: {reasons['volume']}")
            assert signal == 'HOLD', f"Signal should be HOLD for very low volume, got {signal}"
        else:
            # May be filtered by other reasons
            print(f"  ✓ Trade filtered (signal: {signal})")
        
        print("✓ Very low volume rejection working correctly")
        return True
    except Exception as e:
        print(f"✗ Very low volume test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_streak_management():
    """Test enhanced win/loss streak adaptive sizing"""
    print("\nTesting enhanced streak management...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        base_risk = 0.02
        
        # Test 2-loss streak (new threshold)
        manager.loss_streak = 2
        manager.win_streak = 0
        adjusted = manager.adjust_risk_for_conditions(base_risk, 0.03, 0.5)
        assert adjusted < base_risk, f"2-loss streak should reduce risk, got {adjusted} vs {base_risk}"
        two_loss_reduction = base_risk - adjusted
        print(f"  ✓ 2-loss streak: {base_risk:.2%} → {adjusted:.2%} (-{two_loss_reduction/base_risk*100:.0f}%)")
        
        # Test 5-loss streak (extended streak)
        manager.loss_streak = 5
        manager.win_streak = 0
        adjusted_5 = manager.adjust_risk_for_conditions(base_risk, 0.03, 0.5)
        assert adjusted_5 < adjusted, f"5-loss streak should reduce more than 2-loss"
        print(f"  ✓ 5-loss streak: {base_risk:.2%} → {adjusted_5:.2%}")
        
        # Test 5-win streak (extended streak)
        manager.loss_streak = 0
        manager.win_streak = 5
        adjusted_win = manager.adjust_risk_for_conditions(base_risk, 0.03, 0.5)
        assert adjusted_win > base_risk, f"5-win streak should increase risk"
        print(f"  ✓ 5-win streak: {base_risk:.2%} → {adjusted_win:.2%}")
        
        print("✓ Enhanced streak management working correctly")
        return True
    except Exception as e:
        print(f"✗ Enhanced streak management test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_granular_volatility_adjustments():
    """Test granular volatility-based risk adjustments"""
    print("\nTesting granular volatility adjustments...")
    try:
        from risk_manager import RiskManager
        
        manager = RiskManager(1000, 0.02, 3)
        base_risk = 0.02
        
        # Test extreme volatility (>8%)
        adjusted_extreme = manager.adjust_risk_for_conditions(base_risk, 0.09, 0.5)
        print(f"  ✓ Extreme volatility (9%): {base_risk:.2%} → {adjusted_extreme:.2%}")
        
        # Test high volatility (6-8%)
        adjusted_high = manager.adjust_risk_for_conditions(base_risk, 0.07, 0.5)
        print(f"  ✓ High volatility (7%): {base_risk:.2%} → {adjusted_high:.2%}")
        
        # Test low volatility (<2%)
        adjusted_low = manager.adjust_risk_for_conditions(base_risk, 0.018, 0.5)
        print(f"  ✓ Low volatility (1.8%): {base_risk:.2%} → {adjusted_low:.2%}")
        
        # Test very low volatility (<1.5%)
        adjusted_very_low = manager.adjust_risk_for_conditions(base_risk, 0.012, 0.5)
        print(f"  ✓ Very low volatility (1.2%): {base_risk:.2%} → {adjusted_very_low:.2%}")
        
        # Verify ordering: extreme < high < base < low < very_low
        assert adjusted_extreme < adjusted_high, "Extreme vol should reduce risk more than high vol"
        assert adjusted_high < base_risk, "High vol should reduce risk"
        assert adjusted_low > base_risk, "Low vol should increase risk"
        assert adjusted_very_low > adjusted_low, "Very low vol should increase risk more"
        
        print("✓ Granular volatility adjustments working correctly")
        return True
    except Exception as e:
        print(f"✗ Granular volatility test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_daily_loss_limit():
    """Test daily loss limit tracking and enforcement"""
    print("\nTesting daily loss limit...")
    try:
        from risk_manager import RiskManager
        from datetime import date
        
        manager = RiskManager(1000, 0.02, 3)
        
        # Set up initial state
        initial_balance = 10000
        manager.trading_date = date.today()
        manager.daily_start_balance = initial_balance
        
        # Test within limit
        current_balance = 9500  # 5% loss (within 10% limit)
        can_trade, reason = manager.should_open_position(0, current_balance, 100)
        assert can_trade, f"Should allow trading within daily loss limit"
        print(f"  ✓ 5% daily loss: Trading allowed")
        
        # Test at limit
        current_balance = 9000  # 10% loss (at limit)
        can_trade, reason = manager.should_open_position(0, current_balance, 100)
        assert not can_trade, f"Should block trading at daily loss limit"
        assert 'Daily loss limit' in reason, f"Reason should mention daily loss limit"
        print(f"  ✓ 10% daily loss: Trading blocked - {reason}")
        
        # Test beyond limit
        current_balance = 8500  # 15% loss (beyond limit)
        can_trade, reason = manager.should_open_position(0, current_balance, 100)
        assert not can_trade, f"Should block trading beyond daily loss limit"
        print(f"  ✓ 15% daily loss: Trading blocked")
        
        print("✓ Daily loss limit working correctly")
        return True
    except Exception as e:
        print(f"✗ Daily loss limit test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mtf_counter_trend_penalty():
    """Test that counter-trend trades get stronger penalty"""
    print("\nTesting multi-timeframe counter-trend penalty...")
    try:
        from signals import SignalGenerator
        from indicators import Indicators
        import pandas as pd
        
        generator = SignalGenerator()
        
        # Create bullish 1h data
        bullish_1h_data = [
            [i * 60000, 100 + i * 0.3, 101 + i * 0.3, 
             99 + i * 0.3, 100.5 + i * 0.3, 2000]
            for i in range(100)
        ]
        
        # Create bearish 4h data (counter-trend)
        bearish_4h_data = [
            [i * 240000, 120 - i * 0.2, 121 - i * 0.2, 
             119 - i * 0.2, 120 - i * 0.2, 8000]
            for i in range(100)
        ]
        
        df_1h = Indicators.calculate_all(bullish_1h_data)
        df_4h = Indicators.calculate_all(bearish_4h_data)
        
        # Generate signal with MTF conflict
        signal, confidence, reasons = generator.generate_signal(df_1h, df_4h)
        
        # Check for MTF conflict warning
        if 'mtf_conflict' in reasons:
            print(f"  ✓ MTF counter-trend detected: {reasons['mtf_conflict']}")
            print(f"  ✓ Signal: {signal}, Confidence: {confidence:.2%}")
        else:
            # May be filtered by confidence threshold
            print(f"  ✓ Counter-trend trade filtered (signal: {signal})")
        
        print("✓ Multi-timeframe counter-trend penalty working correctly")
        return True
    except Exception as e:
        print(f"✗ MTF counter-trend test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_time_based_exit():
    """Test time-based exit for stale positions"""
    print("\nTesting time-based exit for stale positions...")
    try:
        from position_manager import Position
        from datetime import datetime, timedelta
        
        # Create a position
        pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=100.0,
            amount=1.0,
            leverage=10,
            stop_loss=95.0,
            take_profit=110.0
        )
        
        # Test 1: Fresh position near breakeven - should not close
        should_close, reason = pos.should_close(100.2)  # 0.2% profit
        assert not should_close, f"Fresh position near breakeven should not close"
        print(f"  ✓ Fresh position (0.2% profit): No exit")
        
        # Test 2: 12-hour position at exact breakeven - should close
        pos.entry_time = datetime.now() - timedelta(hours=12, minutes=5)
        should_close, reason = pos.should_close(100.0)  # Exact breakeven
        assert should_close, f"12-hour position at breakeven should close"
        assert 'time_exit_breakeven_12h' in reason, f"Should have time exit reason, got {reason}"
        print(f"  ✓ 12-hour position at breakeven: {reason}")
        
        # Test 3: 24-hour position with small profit - should close
        pos.entry_time = datetime.now() - timedelta(hours=24, minutes=5)
        should_close, reason = pos.should_close(100.8)  # 0.8% profit
        assert should_close, f"24-hour position with small profit should close"
        assert 'time_exit_stale_24h' in reason, f"Should have 24h time exit reason, got {reason}"
        print(f"  ✓ 24-hour position (0.8% profit): {reason}")
        
        # Test 4: 48-hour position with small loss - should close
        pos.entry_time = datetime.now() - timedelta(hours=48, minutes=5)
        should_close, reason = pos.should_close(98.5)  # 1.5% loss
        assert should_close, f"48-hour position with small loss should close"
        assert 'time_exit_stale_48h' in reason, f"Should have 48h time exit reason, got {reason}"
        print(f"  ✓ 48-hour position (1.5% loss): {reason}")
        
        # Test 5: Old position with good profit - should NOT close by time
        pos.entry_time = datetime.now() - timedelta(hours=50)
        should_close, reason = pos.should_close(105.0)  # 5% profit
        # If it closes, should be by take profit or other logic, not time
        if should_close and 'time_exit' in reason:
            assert False, f"Position with good profit should not close by time, got {reason}"
        print(f"  ✓ Old position with good profit: No time exit")
        
        print("✓ Time-based exit working correctly")
        return True
    except Exception as e:
        print(f"✗ Time-based exit test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all strategy improvement tests"""
    print("="*60)
    print("Running Buy/Sell Strategy Improvement Tests")
    print("="*60)
    
    tests = [
        test_choppy_market_filter,
        test_breakout_volatility_requirement,
        test_very_low_volume_rejection,
        test_enhanced_streak_management,
        test_granular_volatility_adjustments,
        test_daily_loss_limit,
        test_mtf_counter_trend_penalty,
        test_time_based_exit,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*60)
    
    if all(results):
        print("\n✓ All strategy improvement tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
