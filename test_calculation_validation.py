#!/usr/bin/env python3
"""
Detailed Calculation Validation Tests
Validates all numerical calculations with specific test cases
"""
import sys

def test_pnl_calculations():
    """Test P&L calculations with specific scenarios"""
    print("\n" + "="*80)
    print("P&L CALCULATION VALIDATION")
    print("="*80)
    
    from position_manager import Position
    
    issues = []
    
    # Scenario 1: Long position with 5% profit
    pos = Position('BTC/USDT:USDT', 'long', 50000, 1, 10, 47500, 52500)
    current_price = 52500  # 5% gain
    pnl = pos.get_pnl(current_price)
    expected = 0.05  # 5%
    
    if abs(pnl - expected) < 0.0001:
        print(f"✓ Long 5% profit: {pnl:.4f} == {expected:.4f}")
    else:
        issues.append(f"❌ Long 5% profit: got {pnl:.4f}, expected {expected:.4f}")
    
    # Scenario 2: Long position with 10% loss
    current_price = 45000  # 10% loss
    pnl = pos.get_pnl(current_price)
    expected = -0.10  # -10%
    
    if abs(pnl - expected) < 0.0001:
        print(f"✓ Long 10% loss: {pnl:.4f} == {expected:.4f}")
    else:
        issues.append(f"❌ Long 10% loss: got {pnl:.4f}, expected {expected:.4f}")
    
    # Scenario 3: Short position with 5% profit
    pos_short = Position('BTC/USDT:USDT', 'short', 50000, 1, 10, 52500, 47500)
    current_price = 47500  # 5% gain for short
    pnl = pos_short.get_pnl(current_price)
    expected = 0.05  # 5%
    
    if abs(pnl - expected) < 0.0001:
        print(f"✓ Short 5% profit: {pnl:.4f} == {expected:.4f}")
    else:
        issues.append(f"❌ Short 5% profit: got {pnl:.4f}, expected {expected:.4f}")
    
    # Scenario 4: Short position with 10% loss
    current_price = 55000  # 10% loss for short
    pnl = pos_short.get_pnl(current_price)
    expected = -0.10  # -10%
    
    if abs(pnl - expected) < 0.0001:
        print(f"✓ Short 10% loss: {pnl:.4f} == {expected:.4f}")
    else:
        issues.append(f"❌ Short 10% loss: got {pnl:.4f}, expected {expected:.4f}")
    
    # Scenario 5: Verify P&L is NOT multiplied by leverage
    # With 10x leverage, 5% price move should still report as 5%, not 50%
    pos_high_lev = Position('BTC/USDT:USDT', 'long', 50000, 1, 20, 47500, 52500)
    current_price = 52500  # 5% move
    pnl = pos_high_lev.get_pnl(current_price)
    
    if abs(pnl - 0.05) < 0.0001:
        print(f"✓ High leverage (20x) doesn't affect P&L: {pnl:.4f} == 0.05")
    else:
        issues.append(f"❌ High leverage affected P&L: got {pnl:.4f}, expected 0.05")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n✅ All P&L calculations correct")
        return True


def test_margin_calculations():
    """Test margin calculations with specific scenarios"""
    print("\n" + "="*80)
    print("MARGIN CALCULATION VALIDATION")
    print("="*80)
    
    from kucoin_client import KuCoinClient
    from unittest.mock import Mock, MagicMock
    
    issues = []
    
    # Create a mock client
    client = Mock(spec=KuCoinClient)
    client.logger = Mock()
    
    # Mock the exchange and markets
    client.exchange = Mock()
    client.exchange.load_markets = Mock(return_value={
        'BTC/USDT:USDT': {
            'contractSize': 0.001  # BTC contract size
        },
        'ETH/USDT:USDT': {
            'contractSize': 0.01  # ETH contract size
        }
    })
    
    # Test the actual calculation method
    from kucoin_client import KuCoinClient
    real_client = KuCoinClient.__new__(KuCoinClient)
    real_client.logger = Mock()
    real_client.exchange = client.exchange
    
    # Scenario 1: BTC position - 1 contract at $50,000 with 10x leverage
    # Position value = 1 * 50000 * 0.001 = $50
    # Required margin = $50 / 10 = $5
    symbol = 'BTC/USDT:USDT'
    amount = 1
    price = 50000
    leverage = 10
    
    margin = real_client.calculate_required_margin(symbol, amount, price, leverage)
    expected = 5.0
    
    if abs(margin - expected) < 0.01:
        print(f"✓ BTC margin (1 contract, $50k, 10x): ${margin:.2f} == ${expected:.2f}")
    else:
        issues.append(f"❌ BTC margin: got ${margin:.2f}, expected ${expected:.2f}")
    
    # Scenario 2: BTC position - 10 contracts at $50,000 with 5x leverage
    # Position value = 10 * 50000 * 0.001 = $500
    # Required margin = $500 / 5 = $100
    amount = 10
    leverage = 5
    
    margin = real_client.calculate_required_margin(symbol, amount, price, leverage)
    expected = 100.0
    
    if abs(margin - expected) < 0.01:
        print(f"✓ BTC margin (10 contracts, $50k, 5x): ${margin:.2f} == ${expected:.2f}")
    else:
        issues.append(f"❌ BTC margin: got ${margin:.2f}, expected ${expected:.2f}")
    
    # Scenario 3: ETH position - 10 contracts at $3,000 with 10x leverage
    # Position value = 10 * 3000 * 0.01 = $300
    # Required margin = $300 / 10 = $30
    symbol = 'ETH/USDT:USDT'
    amount = 10
    price = 3000
    leverage = 10
    
    margin = real_client.calculate_required_margin(symbol, amount, price, leverage)
    expected = 30.0
    
    if abs(margin - expected) < 0.01:
        print(f"✓ ETH margin (10 contracts, $3k, 10x): ${margin:.2f} == ${expected:.2f}")
    else:
        issues.append(f"❌ ETH margin: got ${margin:.2f}, expected ${expected:.2f}")
    
    # Scenario 4: Verify margin scales linearly with leverage
    # Same position with 20x leverage should need half the margin
    leverage = 20
    margin_20x = real_client.calculate_required_margin(symbol, amount, price, leverage)
    expected = 15.0
    
    if abs(margin_20x - expected) < 0.01:
        print(f"✓ ETH margin (10 contracts, $3k, 20x): ${margin_20x:.2f} == ${expected:.2f}")
    else:
        issues.append(f"❌ ETH margin at 20x: got ${margin_20x:.2f}, expected ${expected:.2f}")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n✅ All margin calculations correct")
        return True


def test_position_sizing():
    """Test position sizing calculations"""
    print("\n" + "="*80)
    print("POSITION SIZING VALIDATION")
    print("="*80)
    
    from risk_manager import RiskManager
    
    issues = []
    
    manager = RiskManager(max_position_size=10000, risk_per_trade=0.02, max_open_positions=3)
    
    # Scenario 1: $10,000 balance, 2% risk, entry at $100, stop at $95
    # Risk amount = $10,000 * 0.02 = $200
    # Price distance = ($100 - $95) / $100 = 0.05 = 5%
    # Position value = $200 / 0.05 = $4,000
    # Position size = $4,000 / $100 = 40 contracts
    balance = 10000
    entry = 100
    stop = 95
    leverage = 10
    
    size = manager.calculate_position_size(balance, entry, stop, leverage)
    expected = 40.0
    
    if abs(size - expected) < 0.1:
        print(f"✓ Position size (2% risk, 5% stop): {size:.2f} == {expected:.2f} contracts")
    else:
        issues.append(f"❌ Position size: got {size:.2f}, expected {expected:.2f}")
    
    # Scenario 2: Same setup but with 3% stop loss
    # Price distance = 3%
    # Position value = $200 / 0.03 = $6,666.67
    # Position size = $6,666.67 / $100 = 66.67 contracts
    stop = 97
    size = manager.calculate_position_size(balance, entry, stop, leverage)
    expected = 66.67
    
    if abs(size - expected) < 0.1:
        print(f"✓ Position size (2% risk, 3% stop): {size:.2f} == {expected:.2f} contracts")
    else:
        issues.append(f"❌ Position size: got {size:.2f}, expected {expected:.2f}")
    
    # Scenario 3: Verify position size is capped at max
    # With very tight stop (0.1%), calculated position would be huge, but should cap
    stop = 99.9
    size = manager.calculate_position_size(balance, entry, stop, leverage)
    
    if size <= 100:  # $10,000 max / $100 entry = 100 contracts max
        print(f"✓ Position size capped at maximum: {size:.2f} <= 100 contracts")
    else:
        issues.append(f"❌ Position size not capped: {size:.2f} > 100")
    
    # Scenario 4: Verify leverage doesn't affect position size
    # Position size should be the same regardless of leverage
    stop = 95
    size_10x = manager.calculate_position_size(balance, entry, stop, 10)
    size_20x = manager.calculate_position_size(balance, entry, stop, 20)
    
    if abs(size_10x - size_20x) < 0.1:
        print(f"✓ Position size independent of leverage: {size_10x:.2f} == {size_20x:.2f}")
    else:
        issues.append(f"❌ Leverage affected position size: 10x={size_10x:.2f}, 20x={size_20x:.2f}")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n✅ All position sizing calculations correct")
        return True


def test_stop_loss_calculations():
    """Test stop loss percentage calculations"""
    print("\n" + "="*80)
    print("STOP LOSS CALCULATION VALIDATION")
    print("="*80)
    
    from risk_manager import RiskManager
    
    issues = []
    
    manager = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
    
    # Scenario 1: Low volatility (1%) - should get tight stop
    volatility = 0.01
    stop_pct = manager.calculate_stop_loss_percentage(volatility)
    
    if 0.015 <= stop_pct <= 0.04:  # Should be tight but not too tight
        print(f"✓ Low volatility stop loss: {stop_pct:.4f} (1.5-4% range)")
    else:
        issues.append(f"❌ Low volatility stop: {stop_pct:.4f} outside expected range")
    
    # Scenario 2: Medium volatility (3%) - should get moderate stop
    volatility = 0.03
    stop_pct = manager.calculate_stop_loss_percentage(volatility)
    
    if 0.04 <= stop_pct <= 0.08:  # Should be moderate
        print(f"✓ Medium volatility stop loss: {stop_pct:.4f} (4-8% range)")
    else:
        issues.append(f"❌ Medium volatility stop: {stop_pct:.4f} outside expected range")
    
    # Scenario 3: High volatility (10%) - should get wide stop but capped
    volatility = 0.10
    stop_pct = manager.calculate_stop_loss_percentage(volatility)
    
    if stop_pct <= 0.08:  # Should be capped at 8%
        print(f"✓ High volatility stop loss capped: {stop_pct:.4f} <= 8%")
    else:
        issues.append(f"❌ High volatility stop not capped: {stop_pct:.4f}")
    
    # Scenario 4: Verify stops scale with volatility
    vol_low = 0.02
    vol_high = 0.04
    stop_low = manager.calculate_stop_loss_percentage(vol_low)
    stop_high = manager.calculate_stop_loss_percentage(vol_high)
    
    if stop_high > stop_low:
        print(f"✓ Stop loss scales with volatility: {stop_low:.4f} < {stop_high:.4f}")
    else:
        issues.append(f"❌ Stop loss doesn't scale: low={stop_low:.4f}, high={stop_high:.4f}")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n✅ All stop loss calculations correct")
        return True


def test_leverage_calculations():
    """Test leverage calculations"""
    print("\n" + "="*80)
    print("LEVERAGE CALCULATION VALIDATION")
    print("="*80)
    
    from risk_manager import RiskManager
    
    issues = []
    
    manager = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
    
    # Scenario 1: Low volatility + high confidence = high leverage
    volatility = 0.01
    confidence = 0.85
    leverage = manager.get_max_leverage(volatility, confidence)
    
    if leverage >= 15:
        print(f"✓ Low vol + high confidence = high leverage: {leverage}x >= 15x")
    else:
        issues.append(f"❌ Low vol + high confidence leverage too low: {leverage}x")
    
    # Scenario 2: High volatility + low confidence = low leverage
    volatility = 0.10
    confidence = 0.55
    leverage = manager.get_max_leverage(volatility, confidence)
    
    if leverage <= 5:
        print(f"✓ High vol + low confidence = low leverage: {leverage}x <= 5x")
    else:
        issues.append(f"❌ High vol + low confidence leverage too high: {leverage}x")
    
    # Scenario 3: Verify leverage is always capped at reasonable max (25x)
    # Even with perfect conditions
    volatility = 0.005
    confidence = 0.95
    momentum = 0.05
    trend_strength = 0.9
    market_regime = 'trending'
    leverage = manager.get_max_leverage(volatility, confidence, momentum, trend_strength, market_regime)
    
    if leverage <= 25:
        print(f"✓ Leverage capped at maximum: {leverage}x <= 25x")
    else:
        issues.append(f"❌ Leverage exceeds maximum: {leverage}x")
    
    # Scenario 4: Verify leverage never goes below 3x (minimum safe leverage)
    # Even with worst conditions
    volatility = 0.20
    confidence = 0.50
    momentum = -0.05
    trend_strength = 0.1
    market_regime = 'ranging'
    
    # Simulate worst performance
    manager.loss_streak = 5
    manager.recent_trades = [-0.05] * 10  # All losses
    
    leverage = manager.get_max_leverage(volatility, confidence, momentum, trend_strength, market_regime)
    
    if leverage >= 3:
        print(f"✓ Leverage has minimum floor: {leverage}x >= 3x")
    else:
        issues.append(f"❌ Leverage below minimum: {leverage}x")
    
    # Reset for other tests
    manager.loss_streak = 0
    manager.recent_trades = []
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n✅ All leverage calculations correct")
        return True


def test_kelly_criterion():
    """Test Kelly Criterion calculations"""
    print("\n" + "="*80)
    print("KELLY CRITERION VALIDATION")
    print("="*80)
    
    from risk_manager import RiskManager
    
    issues = []
    
    manager = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
    
    # Scenario 1: Perfect system (100% win rate, impossible but test boundary)
    # Kelly = (p*b - q) / b where p=win rate, q=1-p, b=avg_win/avg_loss
    # For 100% win rate, Kelly should be capped
    win_rate = 1.0
    avg_win = 0.05
    avg_loss = 0.03
    
    kelly = manager.calculate_kelly_criterion(win_rate, avg_win, avg_loss, use_fractional=True)
    
    # Should be capped at conservative level (3.5%)
    if kelly <= 0.035:
        print(f"✓ Kelly for perfect system capped: {kelly:.4f} <= 0.035")
    else:
        issues.append(f"❌ Kelly not capped for perfect system: {kelly:.4f}")
    
    # Scenario 2: Good system (60% win rate, 2:1 R:R)
    win_rate = 0.60
    avg_win = 0.04
    avg_loss = 0.02
    
    kelly = manager.calculate_kelly_criterion(win_rate, avg_win, avg_loss, use_fractional=True)
    
    # Should be positive and reasonable (capped at 3.5% for safety)
    # With fractional Kelly (50% default), good system will hit the cap
    if 0.01 <= kelly <= 0.035:
        print(f"✓ Kelly for good system (60%, 2:1): {kelly:.4f} in 1-3.5% range")
    else:
        issues.append(f"❌ Kelly for good system out of range: {kelly:.4f}")
    
    # Scenario 3: Breakeven system (50% win rate, 1:1 R:R)
    win_rate = 0.50
    avg_win = 0.03
    avg_loss = 0.03
    
    kelly = manager.calculate_kelly_criterion(win_rate, avg_win, avg_loss, use_fractional=True)
    
    # Should be near zero or very small
    if kelly <= 0.005:
        print(f"✓ Kelly for breakeven system near zero: {kelly:.4f}")
    else:
        issues.append(f"❌ Kelly for breakeven system too high: {kelly:.4f}")
    
    # Scenario 4: Losing system (40% win rate, 1:1 R:R)
    win_rate = 0.40
    avg_win = 0.03
    avg_loss = 0.03
    
    kelly = manager.calculate_kelly_criterion(win_rate, avg_win, avg_loss, use_fractional=True)
    
    # Should be very small (Kelly is negative, but returns minimum of 0.5% as fallback)
    # This is correct - even with negative Kelly, we use conservative default
    if kelly <= 0.01:
        print(f"✓ Kelly for losing system uses conservative minimum: {kelly:.4f}")
    else:
        issues.append(f"❌ Kelly for losing system too high: {kelly:.4f}")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n✅ All Kelly Criterion calculations correct")
        return True


def main():
    """Run all calculation validation tests"""
    print("\n" + "="*80)
    print("DETAILED CALCULATION VALIDATION")
    print("="*80)
    
    results = {}
    
    results['pnl'] = test_pnl_calculations()
    results['margin'] = test_margin_calculations()
    results['position_sizing'] = test_position_sizing()
    results['stop_loss'] = test_stop_loss_calculations()
    results['leverage'] = test_leverage_calculations()
    results['kelly'] = test_kelly_criterion()
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n{passed}/{total} validation tests passed")
    
    if passed == total:
        print("\n✅ ALL CALCULATIONS VALIDATED - Numbers are correct!")
        return 0
    else:
        print("\n❌ SOME CALCULATIONS FAILED - Review above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
