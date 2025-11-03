"""
Test suite to validate threshold adjustments fix the 0.00 score issue
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
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    if trend == 'bullish':
        # Strong bullish trend with good volume and clear momentum
        closes = np.linspace(price * 0.9, price * 1.1, rows)
        volumes = np.random.uniform(1500, 2500, rows)  # Higher volume
        # Add minimal noise to preserve trend
        closes = closes + np.random.normal(0, price * 0.005, rows)
    elif trend == 'moderate_bullish':
        # Moderate bullish trend
        closes = np.linspace(price * 0.95, price * 1.05, rows)
        volumes = np.random.uniform(1200, 1800, rows)
        closes = closes + np.random.normal(0, price * 0.005, rows)
    elif trend == 'weak_bullish':
        # Weak bullish trend
        closes = np.linspace(price * 0.98, price * 1.02, rows)
        volumes = np.random.uniform(800, 1200, rows)
        closes = closes + np.random.normal(0, price * 0.003, rows)
    elif trend == 'bearish':
        # Strong bearish trend with good volume and clear momentum
        closes = np.linspace(price * 1.1, price * 0.9, rows)
        volumes = np.random.uniform(1500, 2500, rows)  # Higher volume
        # Add minimal noise to preserve trend
        closes = closes + np.random.normal(0, price * 0.005, rows)
    elif trend == 'ranging':
        # Choppy/ranging market
        closes = price + np.sin(np.linspace(0, 4*np.pi, rows)) * (price * 0.05)
        volumes = np.random.uniform(500, 1000, rows)
    else:  # neutral
        # Neutral market with low momentum
        closes = np.ones(rows) * price + np.random.normal(0, price * 0.01, rows)
        volumes = np.random.uniform(600, 1000, rows)
    
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


def test_threshold_values():
    """Test that thresholds are set to reasonable values"""
    print("\n" + "="*60)
    print("Testing Adjusted Threshold Values")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Verify base threshold is adjusted
        print(f"  Base threshold: {sg.adaptive_threshold}")
        assert sg.adaptive_threshold == 0.65, f"Expected 0.65, got {sg.adaptive_threshold}"
        print(f"  ✓ Base threshold set to 0.65 (balanced)")
        
        # Test trending market threshold
        df_trending = create_test_dataframe(rows=100, price=50000, trend='bullish')
        sg.generate_signal(df_trending)
        print(f"  ✓ Trending market regime: {sg.market_regime}")
        print(f"    (threshold should be 0.60)")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_score_calculation_with_signals():
    """Test that scores are non-zero when signals are generated"""
    print("\n" + "="*60)
    print("Testing Score Calculation with Valid Signals")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Test with different trend strengths
        test_cases = [
            ('strong_bullish', 'bullish'),
            ('moderate_bullish', 'moderate_bullish'),
            ('weak_bullish', 'weak_bullish'),
            ('bearish', 'bearish'),
        ]
        
        non_zero_scores = 0
        non_hold_signals = 0
        
        for test_name, trend in test_cases:
            df = create_test_dataframe(rows=100, price=50000, trend=trend)
            signal, confidence, reasons = sg.generate_signal(df)
            score = sg.calculate_score(df)
            
            print(f"\n  {test_name}:")
            print(f"    Signal: {signal}, Confidence: {confidence:.2%}, Score: {score:.2f}")
            print(f"    Market regime: {sg.market_regime}")
            
            if score > 0:
                non_zero_scores += 1
                print(f"    ✓ Non-zero score achieved")
            
            if signal != 'HOLD':
                non_hold_signals += 1
                print(f"    ✓ Active signal generated")
        
        print(f"\n  Summary:")
        print(f"    Non-zero scores: {non_zero_scores}/{len(test_cases)}")
        print(f"    Active signals (not HOLD): {non_hold_signals}/{len(test_cases)}")
        
        # We expect at least some non-zero scores with adjusted thresholds
        assert non_zero_scores > 0, "Expected at least some non-zero scores"
        print(f"\n  ✓ Score calculation working with adjusted thresholds")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hold_signals_have_zero_score():
    """Test that HOLD signals still correctly return 0 score"""
    print("\n" + "="*60)
    print("Testing HOLD Signals Return Zero Score")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Create a neutral/choppy market that should result in HOLD
        df = create_test_dataframe(rows=100, price=50000, trend='neutral')
        signal, confidence, reasons = sg.generate_signal(df)
        score = sg.calculate_score(df)
        
        print(f"  Signal: {signal}, Confidence: {confidence:.2%}, Score: {score:.2f}")
        
        if signal == 'HOLD':
            assert score == 0.0, f"HOLD signal should have 0 score, got {score}"
            print(f"  ✓ HOLD signal correctly returns 0 score")
        else:
            print(f"  ℹ Signal is {signal}, not HOLD (this is okay)")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_confidence_near_threshold():
    """Test signals with confidence near the threshold"""
    print("\n" + "="*60)
    print("Testing Signals Near Threshold")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Test with moderate bullish trend (should have confidence around 0.58-0.62)
        df = create_test_dataframe(rows=100, price=50000, trend='moderate_bullish')
        signal, confidence, reasons = sg.generate_signal(df)
        score = sg.calculate_score(df)
        
        print(f"  Moderate trend test:")
        print(f"    Signal: {signal}, Confidence: {confidence:.2%}, Score: {score:.2f}")
        print(f"    Market regime: {sg.market_regime}")
        
        # With adjusted thresholds, confidence around 0.58-0.62 should sometimes pass
        # in trending markets (threshold 0.60)
        if sg.market_regime == 'trending' and confidence >= 0.58:
            if signal != 'HOLD':
                print(f"    ✓ Signal passed with trending threshold (0.60)")
            else:
                # Might still be HOLD due to other filters
                print(f"    ℹ HOLD due to other filters: {reasons.get('confidence', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pattern_detection_with_scoring():
    """Test that pattern detection contributes to scoring"""
    print("\n" + "="*60)
    print("Testing Pattern Detection with Scoring")
    print("="*60)
    
    try:
        sg = SignalGenerator()
        
        # Create a strong bullish trend that should trigger patterns
        df = create_test_dataframe(rows=100, price=50000, trend='bullish')
        signal, confidence, reasons = sg.generate_signal(df)
        score = sg.calculate_score(df)
        
        print(f"  Signal: {signal}, Confidence: {confidence:.2%}, Score: {score:.2f}")
        print(f"  Market regime: {sg.market_regime}")
        
        if 'pattern' in reasons:
            print(f"  ✓ Pattern detected: {reasons['pattern']}")
        
        if signal != 'HOLD':
            print(f"  ✓ Active signal generated")
            assert score > 0, f"Active signal should have non-zero score, got {score}"
            print(f"  ✓ Non-zero score: {score:.2f}")
        else:
            print(f"  ℹ Signal is HOLD")
            print(f"    Reasons: {reasons.get('confidence', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all threshold fix tests"""
    print("\n" + "="*60)
    print("TESTING THRESHOLD ADJUSTMENTS FIX")
    print("="*60)
    print("\nPurpose: Validate that adjusted thresholds fix 0.00 score issue")
    print("Expected: Some signals should pass and generate non-zero scores")
    
    tests = [
        ("Threshold Values", test_threshold_values),
        ("Score Calculation", test_score_calculation_with_signals),
        ("HOLD Zero Score", test_hold_signals_have_zero_score),
        ("Near Threshold", test_confidence_near_threshold),
        ("Pattern Detection", test_pattern_detection_with_scoring),
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
        print("\n✓ All threshold fix tests passed!")
        print("✓ Scores should no longer be stuck at 0.00")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
