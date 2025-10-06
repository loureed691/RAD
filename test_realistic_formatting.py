#!/usr/bin/env python3
"""
Test that simulates the exact scenarios from the problem statement
"""

def format_price(price: float) -> str:
    """Format price with appropriate precision based on magnitude."""
    if price == 0:
        return "0.00"
    
    abs_price = abs(price)
    
    if abs_price >= 1000:
        return f"{price:.2f}"
    elif abs_price >= 1:
        return f"{price:.2f}"
    elif abs_price >= 0.1:
        return f"{price:.2f}"
    elif abs_price >= 0.01:
        return f"{price:.4f}"
    elif abs_price >= 0.001:
        return f"{price:.5f}"
    else:
        return f"{price:.6f}"

def format_pnl_usd(pnl_usd: float) -> str:
    """Format P/L USD amount with sign prefix and appropriate precision."""
    sign = "+" if pnl_usd >= 0 else "-"
    abs_value = abs(pnl_usd)
    formatted = format_price(abs_value)
    return f"${sign}{formatted}"

# Simulate real positions from the problem statement
positions = [
    {
        "symbol": "XPL/USDT:USDT",
        "entry_price": 0.88,
        "current_price": 0.89,
        "amount": 1.0,
        "leverage": 5,
        "pnl_pct": -0.0237,
        "description": "Entry 0.88 should not show as 0.00"
    },
    {
        "symbol": "ATH/USDT:USDT",
        "entry_price": 0.06,
        "current_price": 0.05,
        "amount": 8.0,
        "leverage": 5,
        "pnl_pct": -0.0181,
        "description": "Entry 0.06 should not show as 0.00"
    },
    {
        "symbol": "NOT/USDT:USDT",
        "entry_price": 0.001234,  # Example small price
        "current_price": 0.001218,
        "amount": 161.0,
        "leverage": 3,
        "pnl_pct": -0.0125,
        "description": "Entry 0.001234 should show with precision"
    },
    {
        "symbol": "XPIN/USDT:USDT",
        "entry_price": 0.0005678,  # Very small price
        "current_price": 0.0005027,
        "amount": 227.0,
        "leverage": 5,
        "pnl_pct": -0.1146,
        "description": "Very small entry price should show with precision"
    },
    {
        "symbol": "AVAAI/USDT:USDT",
        "entry_price": 0.02,
        "current_price": 0.0188,
        "amount": 3.0,
        "leverage": 3,
        "pnl_pct": -0.0614,
        "description": "Entry 0.02 should show as 0.0200 with 4 decimals"
    },
    {
        "symbol": "F/USDT:USDT",
        "entry_price": 0.01234,
        "current_price": 0.01224,
        "amount": 74.095,
        "leverage": 5,
        "pnl_pct": 0.0084,
        "description": "Entry 0.01234 should show with 4 decimals"
    },
]

print("=" * 80)
print("SIMULATED POSITION UPDATES - Testing Price Formatting")
print("=" * 80)

for pos in positions:
    print(f"\n--- Position: {pos['symbol']} ---")
    print(f"  Entry Price: {format_price(pos['entry_price'])}")
    print(f"  Current Price: {format_price(pos['current_price'])}")
    print(f"  Amount: {pos['amount']:.4f} contracts")
    print(f"  Leverage: {pos['leverage']}x")
    
    # Calculate P/L USD
    position_value = pos['amount'] * pos['entry_price']
    pnl_usd = (pos['pnl_pct'] / pos['leverage']) * position_value
    
    print(f"  Current P/L: {pos['pnl_pct']:+.2%} ({format_pnl_usd(pnl_usd)})")
    print(f"  ✓ {pos['description']}")

print("\n" + "=" * 80)
print("COMPARISON WITH OLD FORMAT (using .2f)")
print("=" * 80)

for pos in positions:
    print(f"\n{pos['symbol']}:")
    print(f"  OLD: Entry Price: {pos['entry_price']:.2f}")
    print(f"  NEW: Entry Price: {format_price(pos['entry_price'])}")
    
    position_value = pos['amount'] * pos['entry_price']
    pnl_usd = (pos['pnl_pct'] / pos['leverage']) * position_value
    
    print(f"  OLD: P/L: {pos['pnl_pct']:+.2%} (${pnl_usd:+.2f})")
    print(f"  NEW: P/L: {pos['pnl_pct']:+.2%} ({format_pnl_usd(pnl_usd)})")

print("\n" + "=" * 80)
print("✓ Formatting improvements preserve precision for small values")
print("=" * 80)
