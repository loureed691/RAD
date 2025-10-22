#!/usr/bin/env python3
"""
Test suite for enhanced smart profit-taking functionality
Tests the intelligent ROI-based profit taking, momentum loss detection, and conservative TP extensions
"""

from position_manager import Position
from datetime import datetime, timedelta

def test_roi_based_profit_taking():
    """Test that positions close at intelligent ROI thresholds"""
    print("\n" + "="*80)
    print("Testing ROI-Based Profit Taking")
    print("="*80)
    
    # Test 5% ROI profit taking with far TP
    print("\n1. Testing 5% ROI with far TP (>5% away)...")
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,
        take_profit=58000.0  # 16% away (far TP)
    )
    
    # Price at 50250 gives 5% ROI with 10x leverage
    current_price = 50250.0
    should_close, reason = position.should_close(current_price)
    pnl = position.get_leveraged_pnl(current_price)
    
    print(f"   Entry: ${position.entry_price:,.0f}")
    print(f"   Current: ${current_price:,.0f}")
    print(f"   Take Profit: ${position.take_profit:,.0f}")
    print(f"   Current PNL: {pnl:.2%}")
    print(f"   Should Close: {should_close}")
    print(f"   Reason: {reason}")
    assert should_close, "Should close at 5% ROI when TP is far"
    assert reason == 'take_profit_5pct', f"Expected 'take_profit_5pct', got '{reason}'"
    print("   ✓ Position closes at 5% ROI with far TP")
    
    # Test 8% ROI profit taking
    print("\n2. Testing 8% ROI with far TP (>3% away)...")
    position2 = Position(
        symbol='ETH-USDT',
        side='long',
        entry_price=3000.0,
        amount=5.0,
        leverage=10,
        stop_loss=2850.0,
        take_profit=3300.0  # 10% away
    )
    
    # Price at 3024 gives 8% ROI with 10x leverage
    current_price2 = 3024.0
    should_close2, reason2 = position2.should_close(current_price2)
    pnl2 = position2.get_leveraged_pnl(current_price2)
    
    print(f"   Entry: ${position2.entry_price:,.0f}")
    print(f"   Current: ${current_price2:,.0f}")
    print(f"   Take Profit: ${position2.take_profit:,.0f}")
    print(f"   Current PNL: {pnl2:.2%}")
    print(f"   Should Close: {should_close2}")
    print(f"   Reason: {reason2}")
    assert should_close2, "Should close at 8% ROI when TP is far"
    assert reason2 == 'take_profit_8pct', f"Expected 'take_profit_8pct', got '{reason2}'"
    print("   ✓ Position closes at 8% ROI with far TP")
    
    # Test 15% ROI profit taking
    print("\n3. Testing 15% ROI with far TP...")
    position3 = Position(
        symbol='ADA-USDT',
        side='short',
        entry_price=0.50,
        amount=1000.0,
        leverage=10,
        stop_loss=0.525,
        take_profit=0.46  # Far TP
    )
    
    # Price at 0.4925 gives 15% ROI with 10x leverage (short)
    current_price3 = 0.4925
    should_close3, reason3 = position3.should_close(current_price3)
    pnl3 = position3.get_leveraged_pnl(current_price3)
    
    print(f"   Entry: ${position3.entry_price:.4f}")
    print(f"   Current: ${current_price3:.4f}")
    print(f"   Take Profit: ${position3.take_profit:.2f}")
    print(f"   Current PNL: {pnl3:.2%}")
    print(f"   Should Close: {should_close3}")
    print(f"   Reason: {reason3}")
    assert should_close3, "Should close at 15% ROI when TP is far"
    assert reason3 == 'take_profit_15pct_far_tp', f"Expected 'take_profit_15pct_far_tp', got '{reason3}'"
    print("   ✓ Short position closes at 15% ROI with far TP")
    
    # Test 20% ROI (exceptional profit - unconditional)
    print("\n4. Testing 20% ROI (exceptional - always closes)...")
    position4 = Position(
        symbol='BNB-USDT',
        side='long',
        entry_price=400.0,
        amount=2.0,
        leverage=10,
        stop_loss=380.0,
        take_profit=401.0  # Very close TP
    )
    
    # Price at 408 gives 20% ROI with 10x leverage
    current_price4 = 408.0
    should_close4, reason4 = position4.should_close(current_price4)
    pnl4 = position4.get_leveraged_pnl(current_price4)
    
    print(f"   Entry: ${position4.entry_price:,.0f}")
    print(f"   Current: ${current_price4:,.0f}")
    print(f"   Take Profit: ${position4.take_profit:,.2f}")
    print(f"   Current PNL: {pnl4:.2%}")
    print(f"   Should Close: {should_close4}")
    print(f"   Reason: {reason4}")
    assert should_close4, "Should ALWAYS close at 20% ROI (exceptional)"
    assert reason4 == 'take_profit_20pct_exceptional', f"Expected 'take_profit_20pct_exceptional', got '{reason4}'"
    print("   ✓ Position closes at 20% ROI (exceptional, unconditional)")
    
    print("\n✓ All ROI-based profit taking tests passed!")

def test_momentum_loss_detection():
    """Test that positions close when giving back significant profits"""
    print("\n" + "="*80)
    print("Testing Momentum Loss Detection")
    print("="*80)
    
    # Test 30% profit drawdown from peak
    print("\n1. Testing 30% profit drawdown from peak...")
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,
        take_profit=51000.0  # Closer TP so distance check doesn't trigger
    )
    
    # Simulate position reaching 15% ROI
    peak_price = 50750.0
    position.max_favorable_excursion = position.get_leveraged_pnl(peak_price)
    print(f"   Peak PNL at ${peak_price:,.0f}: {position.max_favorable_excursion:.2%}")
    
    # Now price retraces to 50525 (10.5% ROI, 30% below peak)
    # TP is only 0.94% away, so 10% check won't trigger
    current_price = 50525.0
    current_pnl = position.get_leveraged_pnl(current_price)
    should_close, reason = position.should_close(current_price)
    
    profit_drawdown = position.max_favorable_excursion - current_pnl
    drawdown_pct = profit_drawdown / position.max_favorable_excursion
    
    print(f"   Current price: ${current_price:,.0f}")
    print(f"   Current PNL: {current_pnl:.2%}")
    print(f"   Profit drawdown: {drawdown_pct:.1%}")
    print(f"   Should Close: {should_close}")
    print(f"   Reason: {reason}")
    assert should_close, "Should close after 30% profit drawdown"
    assert reason == 'take_profit_momentum_loss', f"Expected 'take_profit_momentum_loss', got '{reason}'"
    print("   ✓ Position closes after 30% profit drawdown")
    
    # Test 50% profit drawdown (major retracement)
    print("\n2. Testing 50% profit drawdown (major retracement)...")
    position2 = Position(
        symbol='ETH-USDT',
        side='short',
        entry_price=3000.0,
        amount=5.0,
        leverage=10,
        stop_loss=3150.0,
        take_profit=2850.0  # Far enough to not trigger 5% check
    )
    
    # Simulate position reaching 10% ROI
    peak_price2 = 2970.0
    position2.max_favorable_excursion = position2.get_leveraged_pnl(peak_price2)
    print(f"   Peak PNL at ${peak_price2:,.0f}: {position2.max_favorable_excursion:.2%}")
    
    # Now price retraces to 2985 (5% ROI, 50% below peak)
    # Distance to TP: (2985 - 2850) / 2985 = 4.52%, < 5% so won't trigger
    current_price2 = 2985.0
    current_pnl2 = position2.get_leveraged_pnl(current_price2)
    should_close2, reason2 = position2.should_close(current_price2)
    
    profit_drawdown2 = position2.max_favorable_excursion - current_pnl2
    drawdown_pct2 = profit_drawdown2 / position2.max_favorable_excursion
    
    print(f"   Current price: ${current_price2:,.0f}")
    print(f"   Current PNL: {current_pnl2:.2%}")
    print(f"   Profit drawdown: {drawdown_pct2:.1%}")
    print(f"   Should Close: {should_close2}")
    print(f"   Reason: {reason2}")
    assert should_close2, "Should close after 50% profit drawdown"
    assert reason2 == 'take_profit_major_retracement', f"Expected 'take_profit_major_retracement', got '{reason2}'"
    print("   ✓ Position closes after 50% profit drawdown (major retracement)")
    
    print("\n✓ All momentum loss detection tests passed!")

def test_conservative_tp_extensions():
    """Test that TP extensions are very conservative when already profitable"""
    print("\n" + "="*80)
    print("Testing Conservative TP Extensions")
    print("="*80)
    
    # Test minimal extension at 15% profit
    print("\n1. Testing TP extension at 15% profit (very conservative)...")
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,
        take_profit=52500.0  # 5% TP
    )
    
    # Position has 15% ROI (750 price gain / 10x leverage = 15%)
    current_price = 50750.0
    current_pnl = position.get_leveraged_pnl(current_price)
    print(f"   Entry: ${position.entry_price:,.0f}")
    print(f"   Current: ${current_price:,.0f}")
    print(f"   Current PNL: {current_pnl:.2%}")
    print(f"   Initial TP: ${position.take_profit:,.0f}")
    
    old_tp = position.take_profit
    # Strong conditions but should be capped due to high profit
    position.update_take_profit(
        current_price=current_price,
        momentum=0.05,  # Very strong
        trend_strength=0.8,  # Strong
        volatility=0.06,  # High
        rsi=60.0
    )
    
    tp_increase = (position.take_profit - old_tp) / old_tp
    print(f"   New TP: ${position.take_profit:,.0f}")
    print(f"   TP increase: {tp_increase:.2%}")
    assert tp_increase <= 0.051, "TP extension should be ≤5% at 15% profit"
    print(f"   ✓ TP extension capped at {tp_increase:.2%} (very conservative)")
    
    # Test limited extension at 10% profit
    print("\n2. Testing TP extension at 10% profit (limited)...")
    position2 = Position(
        symbol='ETH-USDT',
        side='long',
        entry_price=3000.0,
        amount=5.0,
        leverage=10,
        stop_loss=2850.0,
        take_profit=3200.0
    )
    
    # Position has 10% ROI
    current_price2 = 3030.0
    current_pnl2 = position2.get_leveraged_pnl(current_price2)
    print(f"   Entry: ${position2.entry_price:,.0f}")
    print(f"   Current: ${current_price2:,.0f}")
    print(f"   Current PNL: {current_pnl2:.2%}")
    print(f"   Initial TP: ${position2.take_profit:,.0f}")
    
    old_tp2 = position2.take_profit
    position2.update_take_profit(
        current_price=current_price2,
        momentum=0.04,
        trend_strength=0.7,
        volatility=0.05,
        rsi=65.0
    )
    
    tp_increase2 = (position2.take_profit - old_tp2) / old_tp2
    print(f"   New TP: ${position2.take_profit:,.0f}")
    print(f"   TP increase: {tp_increase2:.2%}")
    assert tp_increase2 <= 0.101, "TP extension should be ≤10% at 10% profit"
    print(f"   ✓ TP extension capped at {tp_increase2:.2%} (limited)")
    
    # Test moderate extension at 5% profit
    print("\n3. Testing TP extension at 5% profit (moderate cap)...")
    position3 = Position(
        symbol='SOL-USDT',
        side='long',
        entry_price=100.0,
        amount=10.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=108.0
    )
    
    # Position has 5% ROI
    current_price3 = 100.5
    current_pnl3 = position3.get_leveraged_pnl(current_price3)
    print(f"   Entry: ${position3.entry_price:,.0f}")
    print(f"   Current: ${current_price3:,.2f}")
    print(f"   Current PNL: {current_pnl3:.2%}")
    print(f"   Initial TP: ${position3.take_profit:,.0f}")
    
    old_tp3 = position3.take_profit
    position3.update_take_profit(
        current_price=current_price3,
        momentum=0.035,
        trend_strength=0.65,
        volatility=0.04,
        rsi=58.0
    )
    
    tp_increase3 = (position3.take_profit - old_tp3) / old_tp3
    print(f"   New TP: ${position3.take_profit:,.2f}")
    print(f"   TP increase: {tp_increase3:.2%}")
    assert tp_increase3 <= 0.201, "TP extension should be ≤20% at 5% profit"
    print(f"   ✓ TP extension capped at {tp_increase3:.2%} (moderate)")
    
    print("\n✓ All conservative TP extension tests passed!")

def test_progress_based_restrictions():
    """Test that TP extensions are restricted based on progress to target"""
    print("\n" + "="*80)
    print("Testing Progress-Based TP Restrictions")
    print("="*80)
    
    # Test minimal extension at 95% progress
    print("\n1. Testing TP restriction at 95% progress to target...")
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=47500.0,
        take_profit=52500.0  # 5% target
    )
    
    # 95% progress: 50000 + 0.95 * 2500 = 52375
    current_price = 52375.0
    progress = (current_price - position.entry_price) / (position.initial_take_profit - position.entry_price)
    print(f"   Entry: ${position.entry_price:,.0f}")
    print(f"   Current: ${current_price:,.0f}")
    print(f"   Initial TP: ${position.take_profit:,.0f}")
    print(f"   Progress: {progress:.1%}")
    
    old_tp = position.take_profit
    # Strong conditions
    position.update_take_profit(
        current_price=current_price,
        momentum=0.05,
        trend_strength=0.8,
        volatility=0.05,
        rsi=60.0
    )
    
    tp_increase = (position.take_profit - old_tp) / old_tp
    print(f"   New TP: ${position.take_profit:,.0f}")
    print(f"   TP increase: {tp_increase:.2%}")
    assert tp_increase <= 0.051, "TP extension should be ≤5% at 95% progress"
    print(f"   ✓ TP extension heavily restricted at 95% progress")
    
    # Test limited extension at 80% progress
    print("\n2. Testing TP restriction at 80% progress...")
    position2 = Position(
        symbol='ETH-USDT',
        side='long',
        entry_price=3000.0,
        amount=5.0,
        leverage=10,
        stop_loss=2850.0,
        take_profit=3300.0  # 10% target
    )
    
    # 80% progress: 3000 + 0.8 * 300 = 3240
    current_price2 = 3240.0
    progress2 = (current_price2 - position2.entry_price) / (position2.initial_take_profit - position2.entry_price)
    print(f"   Entry: ${position2.entry_price:,.0f}")
    print(f"   Current: ${current_price2:,.0f}")
    print(f"   Initial TP: ${position2.take_profit:,.0f}")
    print(f"   Progress: {progress2:.1%}")
    
    old_tp2 = position2.take_profit
    position2.update_take_profit(
        current_price=current_price2,
        momentum=0.045,
        trend_strength=0.75,
        volatility=0.05,
        rsi=62.0
    )
    
    tp_increase2 = (position2.take_profit - old_tp2) / old_tp2
    print(f"   New TP: ${position2.take_profit:,.0f}")
    print(f"   TP increase: {tp_increase2:.2%}")
    assert tp_increase2 <= 0.081, "TP extension should be ≤8% at 80% progress"
    print(f"   ✓ TP extension limited at 80% progress")
    
    # Test no extension at 70% progress when close to TP
    print("\n3. Testing TP freeze at 70% progress (approaching TP)...")
    position3 = Position(
        symbol='SOL-USDT',
        side='long',
        entry_price=100.0,
        amount=10.0,
        leverage=10,
        stop_loss=95.0,
        take_profit=110.0
    )
    
    # 72% progress but very close to current TP
    current_price3 = 107.2
    progress3 = (current_price3 - position3.entry_price) / (position3.initial_take_profit - position3.entry_price)
    print(f"   Entry: ${position3.entry_price:,.0f}")
    print(f"   Current: ${current_price3:,.2f}")
    print(f"   Initial TP: ${position3.take_profit:,.0f}")
    print(f"   Progress: {progress3:.1%}")
    
    old_tp3 = position3.take_profit
    position3.update_take_profit(
        current_price=current_price3,
        momentum=0.04,
        trend_strength=0.7,
        volatility=0.04,
        rsi=65.0
    )
    
    print(f"   Old TP: ${old_tp3:,.2f}")
    print(f"   New TP: ${position3.take_profit:,.2f}")
    assert position3.take_profit == old_tp3, "TP should not change at 70%+ progress"
    print(f"   ✓ TP frozen at 70%+ progress (prevents moving target)")
    
    print("\n✓ All progress-based restriction tests passed!")

def test_short_position_profit_taking():
    """Test that all enhancements work correctly for short positions"""
    print("\n" + "="*80)
    print("Testing Short Position Profit Taking")
    print("="*80)
    
    # Test short at 10% ROI with far TP
    print("\n1. Testing short position at 10% ROI with far TP...")
    position = Position(
        symbol='BTC-USDT',
        side='short',
        entry_price=50000.0,
        amount=1.0,
        leverage=10,
        stop_loss=52500.0,
        take_profit=44000.0  # Far TP
    )
    
    # Price at 49500 gives 10% ROI for short
    current_price = 49500.0
    should_close, reason = position.should_close(current_price)
    pnl = position.get_leveraged_pnl(current_price)
    
    print(f"   Entry: ${position.entry_price:,.0f}")
    print(f"   Current: ${current_price:,.0f}")
    print(f"   Take Profit: ${position.take_profit:,.0f}")
    print(f"   Current PNL: {pnl:.2%}")
    print(f"   Should Close: {should_close}")
    print(f"   Reason: {reason}")
    assert should_close, "Short should close at 10% ROI with far TP"
    assert reason == 'take_profit_10pct', f"Expected 'take_profit_10pct', got '{reason}'"
    print("   ✓ Short position closes at 10% ROI with far TP")
    
    # Test short momentum loss
    print("\n2. Testing short position momentum loss...")
    position2 = Position(
        symbol='ETH-USDT',
        side='short',
        entry_price=3000.0,
        amount=5.0,
        leverage=10,
        stop_loss=3150.0,
        take_profit=2700.0
    )
    
    # Reached peak at 2940 (20% ROI)
    peak_price = 2940.0
    position2.max_favorable_excursion = position2.get_leveraged_pnl(peak_price)
    
    # Now at 2982 (6% ROI, 70% drawdown from peak)
    current_price2 = 2982.0
    should_close2, reason2 = position2.should_close(current_price2)
    pnl2 = position2.get_leveraged_pnl(current_price2)
    
    print(f"   Peak PNL: {position2.max_favorable_excursion:.2%}")
    print(f"   Current PNL: {pnl2:.2%}")
    print(f"   Should Close: {should_close2}")
    print(f"   Reason: {reason2}")
    assert should_close2, "Short should close after major momentum loss"
    print("   ✓ Short position detects momentum loss correctly")
    
    print("\n✓ All short position tests passed!")

def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*80)
    print("SMART PROFIT TAKING TEST SUITE")
    print("="*80)
    
    all_passed = True
    
    try:
        test_roi_based_profit_taking()
    except AssertionError as e:
        print(f"\n✗ ROI-based profit taking test failed: {e}")
        all_passed = False
    
    try:
        test_momentum_loss_detection()
    except AssertionError as e:
        print(f"\n✗ Momentum loss detection test failed: {e}")
        all_passed = False
    
    try:
        test_conservative_tp_extensions()
    except AssertionError as e:
        print(f"\n✗ Conservative TP extension test failed: {e}")
        all_passed = False
    
    try:
        test_progress_based_restrictions()
    except AssertionError as e:
        print(f"\n✗ Progress-based restriction test failed: {e}")
        all_passed = False
    
    try:
        test_short_position_profit_taking()
    except AssertionError as e:
        print(f"\n✗ Short position test failed: {e}")
        all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("="*80)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("="*80)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
