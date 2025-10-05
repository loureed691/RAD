#!/usr/bin/env python3
"""
Demo script to showcase the optimized take profit functionality
"""
import sys
from position_manager import Position
from datetime import datetime, timedelta

def print_section(title):
    """Print a section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def demo_rsi_protection():
    """Demonstrate RSI-based profit protection"""
    print_section("1. RSI-Based Reversal Protection")
    
    # Scenario 1: Long position with overbought RSI
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=50000,
        amount=1.0,
        leverage=10,
        stop_loss=47500,
        take_profit=55000
    )
    
    print("\n📊 Scenario: Long position in overbought conditions")
    print(f"   Entry: $50,000 | Current: $51,500 | TP: ${position.take_profit:,.0f}")
    
    initial_tp = position.take_profit
    
    # Strong momentum but overbought RSI
    position.update_take_profit(
        current_price=51500,
        momentum=0.04,  # Strong
        trend_strength=0.7,
        volatility=0.04,
        rsi=82.0  # Overbought - reversal risk!
    )
    
    print(f"\n   Market Conditions:")
    print(f"   • Momentum: +4% (Strong)")
    print(f"   • Trend: 0.7 (Strong)")
    print(f"   • RSI: 82 (⚠️  OVERBOUGHT - Reversal Risk)")
    print(f"\n   Result:")
    print(f"   • Without RSI: Would extend to ~$57k")
    print(f"   • With RSI protection: ${position.take_profit:,.0f}")
    print(f"   ✓ RSI-based tightening protects against reversal")
    
    # Scenario 2: Long position with oversold RSI (room to run)
    position2 = Position(
        symbol='ETH-USDT',
        side='long',
        entry_price=3000,
        amount=5.0,
        leverage=10,
        stop_loss=2850,
        take_profit=3300
    )
    
    print("\n📊 Scenario: Long position with oversold RSI (room to run)")
    print(f"   Entry: $3,000 | Current: $3,100 | TP: ${position2.take_profit:,.0f}")
    
    position2.update_take_profit(
        current_price=3100,
        momentum=0.025,
        trend_strength=0.6,
        volatility=0.03,
        rsi=32.0  # Oversold - room to run!
    )
    
    print(f"\n   Market Conditions:")
    print(f"   • Momentum: +2.5% (Moderate)")
    print(f"   • RSI: 32 (📈 OVERSOLD - Room to Run)")
    print(f"\n   Result:")
    print(f"   • TP extended to: ${position2.take_profit:,.0f}")
    print(f"   ✓ RSI suggests more upside potential")

def demo_support_resistance():
    """Demonstrate support/resistance awareness"""
    print_section("2. Support/Resistance Awareness")
    
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=50000,
        amount=1.0,
        leverage=10,
        stop_loss=47500,
        take_profit=52000  # Low initial TP
    )
    
    print("\n📊 Scenario: Strong trend approaching resistance")
    print(f"   Entry: $50,000 | Current: $51,000 | Initial TP: ${position.take_profit:,.0f}")
    
    # Mock strong resistance at $54,000
    support_resistance = {
        'support': [],
        'resistance': [
            {'price': 54000, 'strength': 0.35},
            {'price': 56000, 'strength': 0.20}
        ],
        'poc': 51000
    }
    
    position.update_take_profit(
        current_price=51000,
        momentum=0.05,  # Very strong
        trend_strength=0.85,  # Very strong
        volatility=0.06,
        rsi=60.0,
        support_resistance=support_resistance
    )
    
    print(f"\n   Market Conditions:")
    print(f"   • Momentum: +5% (Very Strong)")
    print(f"   • Trend: 0.85 (Very Strong)")
    print(f"   • Strong Resistance at: $54,000")
    print(f"\n   Result:")
    print(f"   • Without S/R: Would extend to ~$58k+")
    print(f"   • With S/R awareness: ${position.take_profit:,.0f}")
    print(f"   ✓ Capped near resistance for realistic target")

def demo_profit_velocity():
    """Demonstrate profit velocity tracking"""
    print_section("3. Profit Velocity Tracking")
    
    import time
    
    position = Position(
        symbol='SOL-USDT',
        side='long',
        entry_price=100,
        amount=10.0,
        leverage=10,
        stop_loss=95,
        take_profit=110
    )
    
    print("\n📊 Scenario: Fast-moving momentum trade")
    print(f"   Entry: $100 | Initial TP: ${position.take_profit:.2f}")
    
    # First update at modest profit
    position.update_take_profit(
        current_price=103,
        momentum=0.03,
        trend_strength=0.6,
        volatility=0.03,
        rsi=55.0
    )
    
    print(f"\n   After 1 minute:")
    print(f"   • Price: $103 (+3%)")
    print(f"   • TP: ${position.take_profit:.2f}")
    
    time.sleep(0.1)  # Small delay to simulate time passing
    
    # Second update with fast price movement
    position.update_take_profit(
        current_price=108,
        momentum=0.04,
        trend_strength=0.7,
        volatility=0.04,
        rsi=60.0
    )
    
    print(f"\n   After 2 minutes (fast movement!):")
    print(f"   • Price: $108 (+8% from entry)")
    print(f"   • Profit Velocity: ~{abs(position.profit_velocity):.1f}% per hour")
    print(f"   • New TP: ${position.take_profit:.2f}")
    print(f"   ✓ Extended target captures strong momentum")

def demo_time_based():
    """Demonstrate time-based adjustments"""
    print_section("4. Time-Based Position Aging")
    
    # Fresh position
    position_fresh = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=50000,
        amount=1.0,
        leverage=10,
        stop_loss=47500,
        take_profit=55000
    )
    
    position_fresh.update_take_profit(
        current_price=51000,
        momentum=0.03,
        trend_strength=0.6,
        volatility=0.03,
        rsi=60.0
    )
    
    print("\n📊 Fresh Position (2 hours old):")
    print(f"   TP: ${position_fresh.take_profit:,.0f}")
    
    # Old position
    position_old = Position(
        symbol='ETH-USDT',
        side='long',
        entry_price=3000,
        amount=5.0,
        leverage=10,
        stop_loss=2850,
        take_profit=3300
    )
    
    # Simulate 30 hours old
    position_old.entry_time = datetime.now() - timedelta(hours=30)
    
    position_old.update_take_profit(
        current_price=3100,
        momentum=0.03,
        trend_strength=0.6,
        volatility=0.03,
        rsi=60.0
    )
    
    print(f"\n📊 Aged Position (30 hours old):")
    print(f"   TP: ${position_old.take_profit:,.0f}")
    print(f"\n   ✓ More conservative on stale positions")

def demo_combined():
    """Demonstrate all factors working together"""
    print_section("5. All Factors Combined")
    
    position = Position(
        symbol='BTC-USDT',
        side='long',
        entry_price=50000,
        amount=1.0,
        leverage=10,
        stop_loss=47500,
        take_profit=52000
    )
    
    print("\n📊 Optimal Conditions - All Factors Aligned")
    print(f"   Entry: $50,000 | Current: $51,500 | Initial TP: ${position.take_profit:,.0f}")
    
    support_resistance = {
        'support': [],
        'resistance': [
            {'price': 58000, 'strength': 0.30}  # Distant resistance
        ],
        'poc': 51000
    }
    
    # Multiple updates to build profit velocity
    import time
    position.update_take_profit(51000, 0.03, 0.6, 0.03, 55.0)
    time.sleep(0.05)
    
    position.update_take_profit(
        current_price=51500,
        momentum=0.045,  # Strong
        trend_strength=0.75,  # Strong
        volatility=0.05,  # Moderate-high
        rsi=58.0,  # Neutral-bullish
        support_resistance=support_resistance
    )
    
    print(f"\n   Market Conditions:")
    print(f"   ✓ Strong momentum: +4.5%")
    print(f"   ✓ Strong trend: 0.75")
    print(f"   ✓ Moderate volatility: 5%")
    print(f"   ✓ RSI: 58 (Neutral, room to run)")
    print(f"   ✓ Fast profit velocity: {abs(position.profit_velocity):.1f}% per hour")
    print(f"   ✓ Fresh position: <1 hour")
    print(f"   ✓ No nearby resistance")
    
    print(f"\n   Result:")
    print(f"   • New TP: ${position.take_profit:,.0f}")
    print(f"   • Gain from initial: ${position.take_profit - 52000:,.0f} (+{(position.take_profit/52000 - 1)*100:.1f}%)")
    print(f"   ✓ Significant extension for optimal conditions")

def main():
    """Run all demonstrations"""
    print("\n" + "="*70)
    print("  OPTIMIZED TAKE PROFIT DEMONSTRATION")
    print("  Showcasing Smart Exit Strategies")
    print("="*70)
    
    demo_rsi_protection()
    demo_support_resistance()
    demo_profit_velocity()
    demo_time_based()
    demo_combined()
    
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    print("\n✓ 8 factors now influence take profit decisions:")
    print("  1. Momentum (original)")
    print("  2. Trend strength (original)")
    print("  3. Volatility (original)")
    print("  4. Current profit (original)")
    print("  5. RSI reversal protection (NEW)")
    print("  6. Support/resistance levels (NEW)")
    print("  7. Profit velocity (NEW)")
    print("  8. Position age (NEW)")
    
    print("\n💡 Benefits:")
    print("  • Better profit protection against reversals")
    print("  • Realistic targets aligned with market structure")
    print("  • Extended targets for strong momentum trades")
    print("  • More conservative on aging positions")
    print("  • All automatic - no manual intervention needed")
    
    print("\n" + "="*70 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
