"""
Test the EXACT scenario from the production logs
Signal: HOLD, Confidence: 0.61, Regime: trending, Buy: 5.0/12.6, Sell: 7.6/12.6
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from signals import SignalGenerator
from indicators import Indicators
import pandas as pd
import numpy as np

print("\n" + "="*80)
print("TESTING EXACT PRODUCTION SCENARIO")
print("="*80)
print("\nProduction Log:")
print("  Signal: HOLD, Confidence: 0.61, Regime: trending")
print("  Buy: 5.0/12.6, Sell: 7.6/12.6")
print("  Score: 0.00")
print("\nWith old thresholds:")
print("  Trending threshold: 0.65")
print("  0.61 < 0.65 → HOLD → Score 0.00")
print("\nWith new thresholds:")
print("  Trending threshold: 0.60")
print("  0.61 > 0.60 → SELL → Score > 0.00")

# Create strong downtrend to match the production scenario
# (stronger sell signals: 7.6 vs buy: 5.0)
# Need momentum > 3% for trending detection
np.random.seed(100)
dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='1h')
price = 50000

# VERY strong downtrend with high momentum (>3%)
closes = np.linspace(price * 1.20, price * 0.85, 100)  # 35% drop
volumes = np.random.uniform(2000, 3000, 100)  # High volume
# Minimal noise to maintain strong trend
closes = closes + np.random.normal(0, price * 0.001, 100)

df = pd.DataFrame({
    'timestamp': dates,
    'open': closes * 1.01,
    'high': closes * 1.02,
    'low': closes * 0.98,
    'close': closes,
    'volume': volumes
})

df = Indicators.calculate_all(df)
sg = SignalGenerator()

print("\n" + "="*80)
print("TEST CASE: Strong Bearish Trend (matching production)")
print("="*80)

signal, confidence, reasons = sg.generate_signal(df)
score = sg.calculate_score(df)

print(f"\nResults:")
print(f"  Signal: {signal}")
print(f"  Confidence: {confidence:.2%}")
print(f"  Market Regime: {sg.market_regime}")
print(f"  Score: {score:.2f}")

indicators = Indicators.get_latest_indicators(df)
print(f"\nKey Indicators:")
print(f"  RSI: {indicators.get('rsi', 0):.1f}")
print(f"  Momentum: {indicators.get('momentum', 0):.2%}")
print(f"  Volume Ratio: {indicators.get('volume_ratio', 0):.2f}")

print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

if sg.market_regime == 'trending':
    trending_threshold = 0.60
    print(f"\n✓ Market regime correctly detected as: {sg.market_regime}")
    print(f"✓ Trending threshold: {trending_threshold:.2%}")
    
    if confidence >= trending_threshold and signal != 'HOLD':
        print(f"✅ FIXED:")
        print(f"   Confidence {confidence:.2%} >= {trending_threshold:.2%}")
        print(f"   Signal: {signal}")
        print(f"   Score: {score:.2f}")
        print("   ✓ Scores are no longer stuck at 0.00 for trending markets!")
    elif confidence < trending_threshold:
        print(f"⚠️  Confidence {confidence:.2%} < {trending_threshold:.2%}")
        print(f"   Signal correctly held due to low confidence")
    else:
        print(f"⚠️  Signal is {signal} but score is {score:.2f}")
        if signal == 'HOLD':
            print(f"   Filtered by: {reasons.get('confidence', 'other filters')}")
else:
    print(f"\n⚠️  Market regime is: {sg.market_regime} (expected trending)")
    print(f"   Test data didn't generate a trending market")
    print(f"   Threshold used: 0.65 (neutral) or 0.68 (ranging)")

print("\n" + "="*80)
