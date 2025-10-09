#!/usr/bin/env python3
"""
Demonstration of the P&L bug impact and fix
"""

def get_pnl_buggy(entry_price, current_price, leverage, side='long'):
    """Buggy version - multiplies by leverage"""
    if side == 'long':
        return ((current_price - entry_price) / entry_price) * leverage
    else:
        return ((entry_price - current_price) / entry_price) * leverage

def get_pnl_fixed(entry_price, current_price, side='long'):
    """Fixed version - no leverage multiplication"""
    if side == 'long':
        return (current_price - entry_price) / entry_price
    else:
        return (entry_price - current_price) / entry_price

print("=" * 80)
print("P&L BUG IMPACT DEMONSTRATION")
print("=" * 80)
print()
print("Scenario: Long position with 10x leverage")
print("  Entry: $100")
print("  Position: 40 contracts ($4,000 value)")
print("  Balance: $10,000")
print()

prices = [101, 102, 105, 110, 115, 120]
entry_price = 100
leverage = 10

print(f"{'Price':<10} {'Move':<10} {'Buggy PNL':<15} {'Fixed PNL':<15} {'Impact':<30}")
print("-" * 80)

for price in prices:
    move_pct = (price - entry_price) / entry_price
    buggy_pnl = get_pnl_buggy(entry_price, price, leverage)
    fixed_pnl = get_pnl_fixed(entry_price, price)
    
    # Determine impact
    if buggy_pnl >= 0.20:
        impact = "❌ Exit at 'exceptional' 20%"
    elif buggy_pnl >= 0.15:
        impact = "⚠️  Exit at 'far_tp' 15%"
    elif buggy_pnl >= 0.10:
        impact = "⚠️  Exit at '10pct'"
    else:
        impact = "✓ Continues running"
    
    print(f"${price:<9} {move_pct:<9.1%} {buggy_pnl:<14.1%} {fixed_pnl:<14.1%} {impact}")

print()
print("=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print()
print("The BUGGY code makes the bot think:")
print("  • 1% price move = 10% profit → Exits at 'take_profit_10pct'")
print("  • 2% price move = 20% profit → Exits at 'take_profit_20pct_exceptional'")
print("  • 5% price move = 50% profit → Way too high!")
print()
print("The FIXED code correctly reports:")
print("  • 1% price move = 1% profit → Position continues")
print("  • 2% price move = 2% profit → Position continues")
print("  • 5% price move = 5% profit → Position continues")
print("  • 10% price move = 10% profit → Take profit logic works correctly")
print()
print("Result: Positions can now reach their full profit potential!")
print()
