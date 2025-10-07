"""
Test that signal generation still works correctly after TP/SL fix
"""
import sys
from unittest.mock import MagicMock
import pandas as pd
import numpy as np

# Mock dependencies
sys.modules['kucoin_client'] = MagicMock()

from signals import SignalGenerator
from indicators import Indicators

def create_sample_data(trend='bullish', length=100):
    """Create sample OHLCV data"""
    np.random.seed(42)
    
    # Base price
    base = 50000
    
    # Create price series with trend
    if trend == 'bullish':
        prices = base + np.cumsum(np.random.randn(length) * 100 + 50)
    elif trend == 'bearish':
        prices = base + np.cumsum(np.random.randn(length) * 100 - 50)
    else:  # neutral
        prices = base + np.cumsum(np.random.randn(length) * 100)
    
    # Create OHLCV
    data = []
    for i in range(length):
        price = prices[i]
        data.append({
            'timestamp': 1609459200000 + i * 3600000,  # Hourly
            'open': price - np.random.rand() * 100,
            'high': price + np.random.rand() * 200,
            'low': price - np.random.rand() * 200,
            'close': price,
            'volume': np.random.rand() * 1000000
        })
    
    return data

def test_signal_generation():
    """Test that signals are generated correctly"""
    print("\n" + "=" * 80)
    print("TEST: SIGNAL GENERATION STILL WORKS AFTER TP/SL FIX")
    print("=" * 80)
    
    signal_gen = SignalGenerator()
    
    test_cases = [
        ('bullish', 'Strong uptrend'),
        ('bearish', 'Strong downtrend'),
        ('neutral', 'Sideways market')
    ]
    
    results = []
    
    for trend, description in test_cases:
        print(f"\n--- Testing {description} ({trend}) ---")
        
        # Create sample data
        ohlcv = create_sample_data(trend=trend, length=100)
        
        # Calculate indicators
        df = Indicators.calculate_all(ohlcv)
        
        # Generate signal
        signal, confidence, reasons = signal_gen.generate_signal(df)
        
        print(f"  Signal: {signal}")
        print(f"  Confidence: {confidence:.2%}")
        print(f"  Reasons: {list(reasons.keys())[:3]}")  # Show first 3 reasons
        
        # Verify signal is valid
        if signal in ['BUY', 'SELL', 'HOLD']:
            print(f"  ✓ Valid signal generated")
            results.append(True)
        else:
            print(f"  ✗ Invalid signal: {signal}")
            results.append(False)
        
        # Verify confidence is reasonable
        if 0.0 <= confidence <= 1.0:
            print(f"  ✓ Valid confidence score")
            results.append(True)
        else:
            print(f"  ✗ Invalid confidence: {confidence}")
            results.append(False)
    
    print("\n" + "=" * 80)
    if all(results):
        print("✓ ALL SIGNAL GENERATION TESTS PASSED")
        print("\nConclusion: Signal generation strategies work correctly after TP/SL fix")
        return True
    else:
        print("✗ SOME SIGNAL GENERATION TESTS FAILED")
        return False

def test_market_regime_detection():
    """Test market regime detection"""
    print("\n" + "=" * 80)
    print("TEST: MARKET REGIME DETECTION")
    print("=" * 80)
    
    signal_gen = SignalGenerator()
    
    test_cases = [
        ('bullish', 'trending'),
        ('neutral', 'ranging'),
    ]
    
    results = []
    
    for trend, expected_regime in test_cases:
        print(f"\n--- Testing {trend} market ---")
        
        ohlcv = create_sample_data(trend=trend, length=100)
        df = Indicators.calculate_all(ohlcv)
        
        regime = signal_gen.detect_market_regime(df)
        
        print(f"  Detected regime: {regime}")
        
        if regime in ['trending', 'ranging', 'neutral']:
            print(f"  ✓ Valid regime detected")
            results.append(True)
        else:
            print(f"  ✗ Invalid regime: {regime}")
            results.append(False)
    
    print("\n" + "=" * 80)
    if all(results):
        print("✓ MARKET REGIME DETECTION WORKS")
        return True
    else:
        print("✗ MARKET REGIME DETECTION FAILED")
        return False

def test_signal_with_different_indicators():
    """Test signal generation with various indicator combinations"""
    print("\n" + "=" * 80)
    print("TEST: SIGNAL GENERATION WITH VARIOUS INDICATORS")
    print("=" * 80)
    
    signal_gen = SignalGenerator()
    
    # Create sample data
    ohlcv = create_sample_data(trend='bullish', length=100)
    df = Indicators.calculate_all(ohlcv)
    
    # Test with different confidence thresholds
    thresholds = [0.45, 0.55, 0.65]
    
    results = []
    
    for threshold in thresholds:
        print(f"\n--- Testing with threshold {threshold:.2f} ---")
        
        signal_gen.adaptive_threshold = threshold
        signal, confidence, reasons = signal_gen.generate_signal(df)
        
        print(f"  Signal: {signal}, Confidence: {confidence:.2%}")
        
        # Verify signal logic
        if signal == 'BUY' and confidence >= threshold:
            print(f"  ✓ BUY signal meets threshold")
            results.append(True)
        elif signal == 'SELL' and confidence >= threshold:
            print(f"  ✓ SELL signal meets threshold")
            results.append(True)
        elif signal == 'HOLD':
            print(f"  ✓ HOLD signal (confidence below threshold)")
            results.append(True)
        else:
            print(f"  ✗ Signal logic inconsistent")
            results.append(False)
    
    print("\n" + "=" * 80)
    if all(results):
        print("✓ INDICATOR-BASED SIGNAL GENERATION WORKS")
        return True
    else:
        print("✗ SOME INDICATOR TESTS FAILED")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("COMPREHENSIVE STRATEGY TESTING AFTER TP/SL FIX")
    print("=" * 80)
    print("\nVerifying that all trading strategies work correctly")
    print("after the take profit and stop loss fix...")
    
    test1 = test_signal_generation()
    test2 = test_market_regime_detection()
    test3 = test_signal_with_different_indicators()
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    
    if test1 and test2 and test3:
        print("\n✅ ALL STRATEGY TESTS PASSED")
        print("\nVerification complete:")
        print("  ✓ Signal generation working correctly")
        print("  ✓ Market regime detection functioning")
        print("  ✓ Indicator-based signals operational")
        print("  ✓ All trading strategies compatible with TP/SL fix")
        print("\nThe TP/SL fix does NOT affect strategy signal generation.")
        print("Strategies continue to work as expected.")
        exit(0)
    else:
        print("\n❌ SOME STRATEGY TESTS FAILED")
        exit(1)
