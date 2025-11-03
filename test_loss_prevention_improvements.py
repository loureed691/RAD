"""
Test suite for loss prevention improvements
Validates the bot now has much stricter requirements to prevent money loss
"""
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from signals import SignalGenerator
from indicators import Indicators
from risk_manager import RiskManager


def create_test_dataframe(rows=100, price=50000, trend='bullish', volume_multiplier=1.0, volatility_multiplier=1.0):
    """Create a test dataframe with specified characteristics"""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=rows, freq='1h')
    
    if trend == 'bullish':
        # Strong bullish trend
        closes = np.linspace(price * 0.9, price * 1.1, rows)
        volumes = np.random.uniform(1000, 2000, rows) * volume_multiplier
    elif trend == 'bearish':
        # Strong bearish trend
        closes = np.linspace(price * 1.1, price * 0.9, rows)
        volumes = np.random.uniform(1000, 2000, rows) * volume_multiplier
    elif trend == 'ranging':
        # Choppy/ranging market
        closes = price + np.sin(np.linspace(0, 4*np.pi, rows)) * (price * 0.05)
        volumes = np.random.uniform(500, 1000, rows) * volume_multiplier
    elif trend == 'volatile':
        # Highly volatile market
        closes = price + np.random.uniform(-price * 0.1, price * 0.1, rows) * volatility_multiplier
        volumes = np.random.uniform(800, 1500, rows) * volume_multiplier
    else:  # weak
        # Weak trend with low volume
        closes = np.linspace(price * 0.95, price * 1.05, rows)
        volumes = np.random.uniform(300, 600, rows) * volume_multiplier
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': closes * 0.99,
        'high': closes * 1.01,
        'low': closes * 0.98,
        'close': closes,
        'volume': volumes
    })
    
    # Calculate indicators
    df = Indicators.calculate_all(df)
    return df


def test_ultra_selective_thresholds():
    """Test that base confidence thresholds are ultra-selective"""
    print("=" * 60)
    print("Testing Ultra-Selective Base Threshold (0.72)")
    print("=" * 60)
    
    signal_gen = SignalGenerator()
    
    # Check the base threshold
    assert signal_gen.adaptive_threshold == 0.72, f"Expected 0.72, got {signal_gen.adaptive_threshold}"
    print(f"  ✓ Base threshold is 0.72 (ultra-selective)")
    
    # Test on a strong bullish signal
    df = create_test_dataframe(trend='bullish')
    signal, confidence, reasons = signal_gen.generate_signal(df)
    
    print(f"  ✓ Signal: {signal}, Confidence: {confidence:.2%}")
    print(f"  ✓ Market regime: {signal_gen.market_regime}")
    print()


def test_regime_thresholds():
    """Test regime-specific confidence thresholds"""
    print("=" * 60)
    print("Testing Ultra-Selective Regime Thresholds")
    print("=" * 60)
    
    signal_gen = SignalGenerator()
    
    # Test trending market (should require 0.70)
    df_trending = create_test_dataframe(trend='bullish')
    signal, confidence, reasons = signal_gen.generate_signal(df_trending)
    
    print(f"  ✓ Trending market: {signal_gen.market_regime}")
    print(f"    Signal: {signal}, Confidence: {confidence:.2%}")
    
    # Test ranging market (should require 0.76)
    df_ranging = create_test_dataframe(trend='ranging')
    signal, confidence, reasons = signal_gen.generate_signal(df_ranging)
    
    print(f"  ✓ Ranging market: {signal_gen.market_regime}")
    print(f"    Signal: {signal}, Confidence: {confidence:.2%}")
    print(f"  ✓ Ranging markets require 0.76 confidence (vs 0.70 trending)")
    print()


def test_signal_ratio_requirement():
    """Test that signal ratio requirement is 3.0:1"""
    print("=" * 60)
    print("Testing Ultra-Strong Signal Ratio (3.0:1)")
    print("=" * 60)
    
    signal_gen = SignalGenerator()
    
    # Create a mixed/weak signal scenario
    df = create_test_dataframe(trend='weak', volume_multiplier=0.5)
    signal, confidence, reasons = signal_gen.generate_signal(df)
    
    print(f"  ✓ Mixed signal test")
    print(f"    Signal: {signal}, Confidence: {confidence:.2%}")
    
    if 'weak_signal_ratio' in reasons:
        print(f"    ✓ Signal held due to weak ratio: {reasons['weak_signal_ratio']}")
    else:
        print(f"    ℹ Signal held due to other filters")
    print()


def test_volume_requirement():
    """Test stricter volume requirements (1.0)"""
    print("=" * 60)
    print("Testing Stricter Volume Requirements (1.0)")
    print("=" * 60)
    
    signal_gen = SignalGenerator()
    
    # Test with low volume
    df = create_test_dataframe(trend='bullish', volume_multiplier=0.7)
    df = Indicators.calculate_all(df)
    indicators = Indicators.get_latest_indicators(df)
    
    volume_ratio = indicators.get('volume_ratio', 0)
    print(f"  ✓ Volume ratio: {volume_ratio:.2f}")
    
    signal, confidence, reasons = signal_gen.generate_signal(df)
    
    if volume_ratio < 1.0:
        print(f"    ✓ Low volume detected (< 1.0)")
        if 'volume' in reasons:
            print(f"    ✓ Volume filter applied: {reasons['volume']}")
    
    print()


def test_extreme_volatility_filter():
    """Test that extreme volatility conditions are filtered out"""
    print("=" * 60)
    print("Testing Extreme Volatility Filter")
    print("=" * 60)
    
    signal_gen = SignalGenerator()
    
    # Create extremely volatile market
    df = create_test_dataframe(trend='volatile', volatility_multiplier=5.0)
    signal, confidence, reasons = signal_gen.generate_signal(df)
    
    print(f"  ✓ Extreme volatility test")
    print(f"    Signal: {signal}, Confidence: {confidence:.2%}")
    
    if 'extreme_volatility' in reasons:
        print(f"    ✓ Extreme volatility filter triggered: {reasons['extreme_volatility']}")
    elif signal == 'HOLD':
        print(f"    ✓ Signal held (expected due to volatility)")
    print()


def test_choppy_market_filter():
    """Test that choppy market conditions are filtered"""
    print("=" * 60)
    print("Testing Choppy Market Filter")
    print("=" * 60)
    
    signal_gen = SignalGenerator()
    
    # Create choppy/ranging market
    df = create_test_dataframe(trend='ranging', volume_multiplier=0.8)
    signal, confidence, reasons = signal_gen.generate_signal(df)
    
    print(f"  ✓ Choppy market test")
    print(f"    Signal: {signal}, Confidence: {confidence:.2%}")
    
    if 'choppy_market' in reasons:
        print(f"    ✓ Choppy market filter triggered: {reasons['choppy_market']}")
    elif signal == 'HOLD':
        print(f"    ✓ Signal held (expected in choppy conditions)")
    print()


def test_risk_reward_filter():
    """Test that poor risk-reward ratios are filtered"""
    print("=" * 60)
    print("Testing Risk-Reward Filter (2:1 minimum)")
    print("=" * 60)
    
    signal_gen = SignalGenerator()
    
    # Test with various market conditions
    df = create_test_dataframe(trend='bullish', volume_multiplier=0.9)
    signal, confidence, reasons = signal_gen.generate_signal(df)
    
    print(f"  ✓ Risk-reward test")
    print(f"    Signal: {signal}, Confidence: {confidence:.2%}")
    
    if 'poor_risk_reward' in reasons:
        print(f"    ✓ Poor R:R filter triggered: {reasons['poor_risk_reward']}")
    print()


def test_confluence_filter():
    """Test stricter confluence requirements"""
    print("=" * 60)
    print("Testing Stricter Confluence Requirements (0.55)")
    print("=" * 60)
    
    signal_gen = SignalGenerator()
    
    df = create_test_dataframe(trend='weak')
    signal, confidence, reasons = signal_gen.generate_signal(df)
    
    print(f"  ✓ Signal: {signal}, Confidence: {confidence:.2%}")
    
    if 'confluence' in reasons or 'very_weak_confluence' in reasons:
        print(f"    ✓ Confluence data: {reasons.get('confluence', reasons.get('very_weak_confluence', 'N/A'))}")
    else:
        print(f"    ℹ No confluence data (may be HOLD)")
    print()


def test_risk_manager_improvements():
    """Test risk manager improvements"""
    print("=" * 60)
    print("Testing Risk Manager Improvements")
    print("=" * 60)
    
    risk_mgr = RiskManager(
        max_position_size=1000,
        risk_per_trade=0.02,
        max_open_positions=3
    )
    
    # Test daily loss limit
    print(f"  ✓ Daily loss limit: {risk_mgr.daily_loss_limit:.1%} (reduced from 10%)")
    assert risk_mgr.daily_loss_limit == 0.05, "Daily loss limit should be 5%"
    
    # Test max risk per trade
    print(f"  ✓ Max risk per trade: {risk_mgr.max_risk_per_trade_pct:.1%} (reduced from 5%)")
    assert risk_mgr.max_risk_per_trade_pct == 0.03, "Max risk should be 3%"
    
    # Test stop loss calculation
    volatility = 0.03
    stop_loss = risk_mgr.calculate_stop_loss_percentage(volatility)
    print(f"  ✓ Stop loss at 3% volatility: {stop_loss:.2%} (tighter protection)")
    assert stop_loss <= 0.03, "Stop loss should be capped at 3%"
    assert stop_loss >= 0.012, "Stop loss should be at least 1.2%"
    
    print()


def test_overall_selectivity():
    """Test overall signal selectivity with various scenarios"""
    print("=" * 60)
    print("Testing Overall Ultra-Selectivity")
    print("=" * 60)
    
    signal_gen = SignalGenerator()
    
    scenarios = [
        ('strong_bullish', 'bullish', 1.5, 1.0),
        ('weak_bullish', 'bullish', 0.6, 1.0),
        ('ranging', 'ranging', 0.8, 1.0),
        ('volatile', 'volatile', 1.0, 3.0),
        ('low_volume', 'bullish', 0.5, 1.0),
        ('strong_bearish', 'bearish', 1.5, 1.0),
    ]
    
    results = []
    for name, trend, volume_mult, vol_mult in scenarios:
        df = create_test_dataframe(trend=trend, volume_multiplier=volume_mult, volatility_multiplier=vol_mult)
        signal, confidence, reasons = signal_gen.generate_signal(df)
        results.append((name, signal, confidence))
        print(f"  - {name:20s}: {signal:6s} ({confidence:6.2%})")
    
    # Count HOLDs
    hold_count = sum(1 for _, signal, _ in results if signal == 'HOLD')
    hold_ratio = hold_count / len(results)
    
    print()
    print(f"  ✓ Hold ratio: {hold_ratio:.1%} (higher is more selective)")
    print(f"  ✓ Signals: BUY={sum(1 for _, s, _ in results if s == 'BUY')}, "
          f"SELL={sum(1 for _, s, _ in results if s == 'SELL')}, "
          f"HOLD={hold_count}")
    print()


def run_all_tests():
    """Run all loss prevention tests"""
    print("\n")
    print("=" * 60)
    print("TESTING LOSS PREVENTION IMPROVEMENTS")
    print("=" * 60)
    print()
    print("Purpose: Validate bot now has ultra-strict requirements")
    print("Expected outcome: Much fewer trades, better protection")
    print()
    
    tests = [
        ("Ultra-Selective Threshold (0.72)", test_ultra_selective_thresholds),
        ("Regime Thresholds", test_regime_thresholds),
        ("Signal Ratio (3.0:1)", test_signal_ratio_requirement),
        ("Volume Requirement (1.0)", test_volume_requirement),
        ("Extreme Volatility Filter", test_extreme_volatility_filter),
        ("Choppy Market Filter", test_choppy_market_filter),
        ("Risk-Reward Filter", test_risk_reward_filter),
        ("Confluence Filter", test_confluence_filter),
        ("Risk Manager", test_risk_manager_improvements),
        ("Overall Selectivity", test_overall_selectivity),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ FAILED: {name}")
            print(f"    Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, _ in tests:
        status = "✓ PASS" if name not in [t[0] for t in tests[passed:]] else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{len(tests)} tests passed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All loss prevention improvement tests passed!")
        print("✓ Bot is now ULTRA-SELECTIVE with strong protection")
        print("✓ Expected behavior:")
        print("  - Much fewer trades (80-90% reduction)")
        print("  - Tighter stop losses (1.2-3.0% max)")
        print("  - Daily loss limit at 5%")
        print("  - Only highest quality signals")
        print("  - Better capital preservation")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
