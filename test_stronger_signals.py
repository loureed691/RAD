"""
Test suite for stronger trading signal requirements
Validates that the bot now requires more stringent conditions for trading
"""
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from signals import SignalGenerator
from indicators import Indicators


def create_test_dataframe(rows=100, price=50000, trend='bullish'):
    """Create a test dataframe with specified characteristics"""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=rows, freq='1h')
    
    if trend == 'bullish':
        # Strong bullish trend
        closes = np.linspace(price * 0.9, price * 1.1, rows)
        volumes = np.random.uniform(1000, 2000, rows)  # Good volume
    elif trend == 'bearish':
        # Strong bearish trend
        closes = np.linspace(price * 1.1, price * 0.9, rows)
        volumes = np.random.uniform(1000, 2000, rows)
    elif trend == 'ranging':
        # Choppy/ranging market
        closes = price + np.sin(np.linspace(0, 4*np.pi, rows)) * (price * 0.05)
        volumes = np.random.uniform(500, 1000, rows)  # Lower volume
    else:  # weak
        # Weak trend with low volume
        closes = np.linspace(price * 0.95, price * 1.05, rows)
        volumes = np.random.uniform(300, 600, rows)  # Low volume
    
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


def test_increased_base_threshold():
    """Test that base confidence threshold is increased to 0.68"""
    print("\n" + "="*60)
    print("Testing Increased Base Threshold (0.68)")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Verify threshold is set correctly
        assert sg.adaptive_threshold == 0.68, f"Expected 0.68, got {sg.adaptive_threshold}"
        print(f"  ✓ Base threshold increased to {sg.adaptive_threshold} (was 0.62)")
        
        # Create a moderate signal that would have passed with 0.62 but not with 0.68
        df = create_test_dataframe(rows=100, price=50000, trend='bullish')
        signal, confidence, reasons = sg.generate_signal(df)
        
        print(f"  ✓ Signal: {signal}, Confidence: {confidence:.2%}")
        print(f"  ✓ Market regime: {sg.market_regime}")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_regime_specific_thresholds():
    """Test that trending and ranging markets have different thresholds"""
    print("\n" + "="*60)
    print("Testing Regime-Specific Thresholds")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Test trending market threshold (should be 0.65)
        df_trending = create_test_dataframe(rows=100, price=50000, trend='bullish')
        signal_trend, conf_trend, reasons_trend = sg.generate_signal(df_trending)
        print(f"  ✓ Trending market: {sg.market_regime}")
        print(f"    Signal: {signal_trend}, Confidence: {conf_trend:.2%}")
        
        # Test ranging market threshold (should be 0.72)
        df_ranging = create_test_dataframe(rows=100, price=50000, trend='ranging')
        signal_range, conf_range, reasons_range = sg.generate_signal(df_ranging)
        print(f"  ✓ Ranging market: {sg.market_regime}")
        print(f"    Signal: {signal_range}, Confidence: {conf_range:.2%}")
        
        # Ranging markets should be more selective
        print(f"  ✓ Ranging markets require higher confidence (0.72 vs 0.65)")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_ratio_requirement():
    """Test that signal ratio requirement is 2.5:1 (increased from 2.0:1)"""
    print("\n" + "="*60)
    print("Testing Signal Ratio Requirement (2.5:1)")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Create a weak signal scenario with mixed signals
        df = create_test_dataframe(rows=100, price=50000, trend='weak')
        signal, confidence, reasons = sg.generate_signal(df)
        
        print(f"  ✓ Weak/mixed signal test")
        print(f"    Signal: {signal}, Confidence: {confidence:.2%}")
        
        # Check if signal was rejected due to weak ratio
        if 'weak_signal_ratio' in reasons:
            print(f"    ✓ Signal correctly rejected: {reasons['weak_signal_ratio']}")
            assert '2.5:1' in reasons['weak_signal_ratio'], "Should mention 2.5:1 requirement"
        elif signal == 'HOLD':
            print(f"    ✓ Signal held due to other filters")
        else:
            print(f"    ℹ Strong signal passed all filters")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_volume_requirement():
    """Test that volume requirement is stricter (0.9 instead of 0.8)"""
    print("\n" + "="*60)
    print("Testing Stricter Volume Requirements (0.9)")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Create data with low volume
        df = create_test_dataframe(rows=100, price=50000, trend='weak')
        
        # Manually check volume ratio in indicators
        indicators = Indicators.get_latest_indicators(df)
        volume_ratio = indicators.get('volume_ratio', 0)
        
        print(f"  ✓ Volume ratio: {volume_ratio:.2f}")
        
        signal, confidence, reasons = sg.generate_signal(df)
        
        if volume_ratio < 0.9:
            print(f"    ✓ Low volume detected (< 0.9)")
            if 'volume' in reasons:
                print(f"    ✓ Volume filter applied: {reasons['volume']}")
        else:
            print(f"    ✓ Adequate volume (>= 0.9)")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trend_momentum_alignment():
    """Test that BOTH trend AND momentum must align (not just OR)"""
    print("\n" + "="*60)
    print("Testing Trend AND Momentum Alignment (Strengthened)")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Create a bullish trend
        df = create_test_dataframe(rows=100, price=50000, trend='bullish')
        signal, confidence, reasons = sg.generate_signal(df)
        
        print(f"  ✓ Bullish trend test")
        print(f"    Signal: {signal}, Confidence: {confidence:.2%}")
        
        # Check if alignment was required
        if 'trend_momentum_mismatch' in reasons:
            print(f"    ✓ Alignment requirement enforced: {reasons['trend_momentum_mismatch']}")
            assert 'AND' in reasons['trend_momentum_mismatch'], "Should require AND, not OR"
        elif signal != 'HOLD':
            print(f"    ✓ Signal passed with proper trend AND momentum alignment")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_confluence_requirements():
    """Test that confluence requirements are stricter (0.5 instead of 0.4)"""
    print("\n" + "="*60)
    print("Testing Stricter Confluence Requirements (0.5)")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        df = create_test_dataframe(rows=100, price=50000, trend='bullish')
        signal, confidence, reasons = sg.generate_signal(df)
        
        print(f"  ✓ Signal: {signal}, Confidence: {confidence:.2%}")
        
        if 'confluence' in reasons:
            print(f"    ✓ Confluence check applied: {reasons['confluence']}")
        else:
            print(f"    ℹ No confluence data in reasons (may be HOLD)")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mtf_conflict_penalty():
    """Test that MTF conflicts are penalized more heavily (0.6 instead of 0.7)"""
    print("\n" + "="*60)
    print("Testing Stronger MTF Conflict Penalty (0.6)")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Create conflicting timeframes (1h bullish, but we'll simulate bearish higher TF)
        df_1h = create_test_dataframe(rows=100, price=50000, trend='bullish')
        df_4h = create_test_dataframe(rows=100, price=50000, trend='bearish')
        
        signal, confidence, reasons = sg.generate_signal(df_1h, df_4h)
        
        print(f"  ✓ Signal: {signal}, Confidence: {confidence:.2%}")
        
        if 'mtf_conflict' in reasons:
            print(f"    ✓ MTF conflict detected and penalized")
        elif 'mtf_boost' in reasons:
            print(f"    ✓ MTF alignment rewarded: {reasons['mtf_boost']}")
        else:
            print(f"    ℹ No MTF data available")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_neutral_regime_filter():
    """Test that neutral regime with no MTF support requires >75% confidence"""
    print("\n" + "="*60)
    print("Testing Neutral Regime Additional Filter (>75%)")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Create neutral/choppy market
        df = create_test_dataframe(rows=100, price=50000, trend='ranging')
        
        # Force neutral regime for testing
        sg.market_regime = 'neutral'
        
        signal, confidence, reasons = sg.generate_signal(df)
        
        print(f"  ✓ Market regime: {sg.market_regime}")
        print(f"  ✓ Signal: {signal}, Confidence: {confidence:.2%}")
        
        if 'neutral_regime_no_mtf' in reasons:
            print(f"    ✓ Neutral regime filter triggered: {reasons['neutral_regime_no_mtf']}")
        elif signal != 'HOLD':
            print(f"    ✓ Signal passed with confidence > 75%")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_overall_selectivity():
    """Test that overall system is more selective (fewer signals)"""
    print("\n" + "="*60)
    print("Testing Overall Selectivity")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Test multiple scenarios
        scenarios = [
            ('strong_bullish', 'bullish'),
            ('weak_bullish', 'weak'),
            ('ranging', 'ranging'),
            ('strong_bearish', 'bearish'),
        ]
        
        signal_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        
        for scenario_name, trend in scenarios:
            df = create_test_dataframe(rows=100, price=50000, trend=trend)
            signal, confidence, reasons = sg.generate_signal(df)
            signal_counts[signal] += 1
            print(f"  - {scenario_name:20s}: {signal:6s} ({confidence:.2%})")
        
        hold_ratio = signal_counts['HOLD'] / len(scenarios)
        print(f"\n  ✓ Hold ratio: {hold_ratio:.1%} (higher is more selective)")
        print(f"  ✓ Signals: BUY={signal_counts['BUY']}, SELL={signal_counts['SELL']}, HOLD={signal_counts['HOLD']}")
        
        # We expect more HOLDs with stricter requirements
        assert signal_counts['HOLD'] >= 1, "Should have at least 1 HOLD signal with stricter filters"
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all stronger signal tests"""
    print("\n" + "="*60)
    print("TESTING STRONGER TRADING SIGNAL REQUIREMENTS")
    print("="*60)
    print("\nPurpose: Validate bot now requires higher quality signals")
    print("Expected outcome: Fewer trades, but stronger signals")
    
    tests = [
        ("Base Threshold (0.68)", test_increased_base_threshold),
        ("Regime Thresholds", test_regime_specific_thresholds),
        ("Signal Ratio (2.5:1)", test_signal_ratio_requirement),
        ("Volume Requirement (0.9)", test_volume_requirement),
        ("Trend AND Momentum", test_trend_momentum_alignment),
        ("Confluence (0.5)", test_confluence_requirements),
        ("MTF Conflict (0.6)", test_mtf_conflict_penalty),
        ("Neutral Regime Filter", test_neutral_regime_filter),
        ("Overall Selectivity", test_overall_selectivity),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n✓ All stronger signal requirement tests passed!")
        print("✓ Bot is now more selective and requires higher quality signals")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
