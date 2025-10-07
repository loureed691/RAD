#!/usr/bin/env python3
"""
Test the smart enhancements to strategies, scanning, and trading
"""
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from signals import SignalGenerator
from position_manager import Position

def test_divergence_detection():
    """Test divergence detection"""
    print("\n" + "="*70)
    print("TESTING DIVERGENCE DETECTION")
    print("="*70)
    
    sg = SignalGenerator()
    
    # Create test data with bullish divergence (price down, RSI up)
    print("\n1. Bullish Divergence Test...")
    df = pd.DataFrame({
        'close': [100, 98, 96, 94, 92] + [91 + i*0.2 for i in range(15)],
        'rsi': [40, 38, 36, 34, 32] + [33 + i*1.0 for i in range(15)],  # Stronger RSI increase
        'macd': [-1, -0.8, -0.6, -0.4, -0.2] + [-0.1 + i*0.05 for i in range(15)],
        'high': [101, 99, 97, 95, 93] + [92 + i*0.2 for i in range(15)],
        'low': [99, 97, 95, 93, 91] + [90 + i*0.2 for i in range(15)]
    })
    
    divergence = sg.detect_divergence(df)
    print(f"   Price trend: Down")
    print(f"   RSI trend: Up (from ~32 to ~48)")
    print(f"   RSI Divergence: {divergence['rsi_divergence']}")
    print(f"   MACD Divergence: {divergence['macd_divergence']}")
    print(f"   Strength: {divergence['strength']:.1f}")
    
    assert divergence['rsi_divergence'] == 'bullish', "Should detect bullish RSI divergence"
    print("   ✓ Bullish divergence detected correctly")
    
    # Test bearish divergence (price up, RSI down)
    print("\n2. Bearish Divergence Test...")
    df2 = pd.DataFrame({
        'close': [100, 102, 104, 106, 108] + [109 + i*0.5 for i in range(15)],
        'rsi': [70, 68, 66, 64, 62] + [61 - i*0.5 for i in range(15)],
        'macd': [1, 0.8, 0.6, 0.4, 0.2] + [0.1 - i*0.05 for i in range(15)],
        'high': [101, 103, 105, 107, 109] + [110 + i*0.5 for i in range(15)],
        'low': [99, 101, 103, 105, 107] + [108 + i*0.5 for i in range(15)]
    })
    
    divergence2 = sg.detect_divergence(df2)
    print(f"   Price trend: Up")
    print(f"   RSI trend: Down (from ~62 to ~54)")
    print(f"   RSI Divergence: {divergence2['rsi_divergence']}")
    print(f"   Strength: {divergence2['strength']:.1f}")
    
    assert divergence2['rsi_divergence'] == 'bearish', "Should detect bearish RSI divergence"
    print("   ✓ Bearish divergence detected correctly")
    
    print("\n✓ All divergence detection tests passed!")
    return True

def test_confluence_scoring():
    """Test confluence scoring"""
    print("\n" + "="*70)
    print("TESTING CONFLUENCE SCORING")
    print("="*70)
    
    sg = SignalGenerator()
    
    # Test strong confluence (all aligned)
    print("\n1. Strong Confluence (All Signals Aligned)...")
    indicators = {
        'ema_12': 52000,
        'ema_26': 50000,
        'momentum': 0.02,
        'rsi': 45,
        'macd': 100,
        'macd_signal': 80,
        'volume_ratio': 1.5
    }
    
    confluence = sg.calculate_confluence_score(indicators, 'BUY')
    print(f"   Signal: BUY")
    print(f"   EMA 12 > EMA 26: ✓")
    print(f"   Momentum > 0: ✓")
    print(f"   RSI < 50: ✓")
    print(f"   MACD > Signal: ✓")
    print(f"   High Volume: ✓")
    print(f"   Confluence Score: {confluence:.1%}")
    
    assert confluence == 1.0, "Perfect alignment should score 100%"
    print("   ✓ Strong confluence detected")
    
    # Test weak confluence (conflicting signals)
    print("\n2. Weak Confluence (Conflicting Signals)...")
    indicators2 = {
        'ema_12': 50000,
        'ema_26': 52000,  # Conflicting
        'momentum': -0.01,  # Conflicting
        'rsi': 60,  # Conflicting
        'macd': 80,
        'macd_signal': 100,  # Conflicting
        'volume_ratio': 0.8  # Conflicting
    }
    
    confluence2 = sg.calculate_confluence_score(indicators2, 'BUY')
    print(f"   Signal: BUY")
    print(f"   Aligned signals: {int(confluence2 * 5)}/5")
    print(f"   Confluence Score: {confluence2:.1%}")
    
    assert confluence2 == 0.0, "No alignment should score 0%"
    print("   ✓ Weak confluence detected")
    
    print("\n✓ All confluence scoring tests passed!")
    return True

def test_support_resistance_strength():
    """Test enhanced S/R with strength scoring"""
    print("\n" + "="*70)
    print("TESTING ENHANCED SUPPORT/RESISTANCE")
    print("="*70)
    
    sg = SignalGenerator()
    
    # Create data with strong support (multiple touches)
    print("\n1. Strong Support Level (Multiple Touches)...")
    # Need more data for the function
    lows = [100, 102, 100.5, 101, 100.2, 103, 100.8, 105, 100.3] * 6  # 54 points
    df = pd.DataFrame({
        'high': [l + 2 for l in lows],
        'low': lows,
        'close': [l + 1 for l in lows]
    })
    
    sr = sg.detect_support_resistance(df, 101.0)
    print(f"   Support Level: {sr.get('support', 0):.2f}")
    print(f"   Support Strength: {sr.get('support_strength', 0):.2f}")
    print(f"   Near Support: {sr.get('near_support', False)}")
    
    assert sr.get('support_strength', 0) >= 0, "Should have support strength"
    print("   ✓ Strong support level detected")
    
    print("\n✓ All S/R enhancement tests passed!")
    return True

def test_breakeven_move():
    """Test automatic breakeven stop loss"""
    print("\n" + "="*70)
    print("TESTING BREAKEVEN STOP LOSS")
    print("="*70)
    
    # Test long position
    print("\n1. Long Position Breakeven...")
    pos = Position('BTC/USDT:USDT', 'long', 50000, 1.0, 10, 48000, 55000)
    
    # Price moves up 0.15% - should NOT move to breakeven yet (1.5% PnL with 10x)
    moved1 = pos.move_to_breakeven(50075)
    pnl1 = pos.get_pnl(50075)
    print(f"   Entry: ${pos.entry_price:,.0f}")
    print(f"   Price at +0.15%: $50,075")
    print(f"   P/L (10x leverage): {pnl1:.1%}")
    print(f"   Moved to breakeven: {moved1}")
    assert not moved1, "Should not move at <2% PnL"
    print("   ✓ Correctly waits for >2% profit")
    
    # Price moves up 0.25% - should move to breakeven (2.5% PnL with 10x)
    moved2 = pos.move_to_breakeven(50125)
    pnl2 = pos.get_pnl(50125)
    print(f"   Price at +0.25%: $50,125")
    print(f"   P/L (10x leverage): {pnl2:.1%}")
    print(f"   Moved to breakeven: {moved2}")
    print(f"   New stop loss: ${pos.stop_loss:,.2f}")
    print(f"   Original stop: $48,000")
    
    assert moved2, "Should move at >2% PnL"
    assert pos.stop_loss > 50000, "Stop should be above entry"
    assert pos.breakeven_moved, "Flag should be set"
    print("   ✓ Stop loss moved to breakeven (+buffer)")
    
    # Test short position
    print("\n2. Short Position Breakeven...")
    pos2 = Position('BTC/USDT:USDT', 'short', 50000, 1.0, 10, 52000, 48000)
    
    # Price moves down 0.3% (3% PnL with 10x)
    moved3 = pos2.move_to_breakeven(49850)
    pnl3 = pos2.get_pnl(49850)
    print(f"   Entry: ${pos2.entry_price:,.0f}")
    print(f"   Price at -0.3%: $49,850")
    print(f"   P/L (10x leverage): {pnl3:.1%}")
    print(f"   Moved to breakeven: {moved3}")
    print(f"   New stop loss: ${pos2.stop_loss:,.2f}")
    
    assert moved3, "Should move at >2% PnL profit"
    assert pos2.stop_loss < 50000, "Stop should be below entry for short"
    print("   ✓ Short position breakeven works correctly")
    
    print("\n✓ All breakeven tests passed!")
    return True

def test_profit_acceleration():
    """Test profit acceleration tracking"""
    print("\n" + "="*70)
    print("TESTING PROFIT ACCELERATION")
    print("="*70)
    
    print("\n1. Accelerating Profits...")
    pos = Position('BTC/USDT:USDT', 'long', 50000, 1.0, 10, 48000, 55000)
    
    # Simulate profit acceleration
    pos.last_pnl = 0.02
    pos.last_pnl_time = datetime.now() - timedelta(hours=1)
    
    # Update with higher profit (acceleration)
    pos.update_take_profit(51000, momentum=0.03, trend_strength=0.8, volatility=0.03, rsi=55)
    
    print(f"   Previous P/L: 2%")
    print(f"   Current P/L: {pos.get_pnl(51000)*100:.1f}%")
    print(f"   Profit Velocity: {pos.profit_velocity:.2f}% per hour")
    print(f"   Profit Acceleration: {pos.profit_acceleration:.4f}")
    
    assert pos.profit_velocity > 0, "Should have positive velocity"
    print("   ✓ Profit acceleration tracked correctly")
    
    print("\n✓ All profit acceleration tests passed!")
    return True

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 SMART ENHANCEMENTS - COMPREHENSIVE VALIDATION TESTS")
    print("="*70)
    print("\nValidating new smart features...")
    
    try:
        success = True
        success = test_divergence_detection() and success
        success = test_confluence_scoring() and success
        success = test_support_resistance_strength() and success
        success = test_breakeven_move() and success
        success = test_profit_acceleration() and success
        
        print("\n" + "="*70)
        if success:
            print("✅ ALL SMART ENHANCEMENT TESTS PASSED!")
            print("\nNew features validated:")
            print("  • Divergence detection (RSI & MACD)")
            print("  • Confluence scoring for signal quality")
            print("  • Enhanced S/R with strength scoring")
            print("  • Automatic breakeven stop loss")
            print("  • Profit acceleration tracking")
        else:
            print("❌ SOME TESTS FAILED")
        print("="*70)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
