# Fix Summary: Short Position Take Profit Update

## Problem
The `test_adaptive_stops.py` test was failing on the support/resistance awareness test for short positions. Specifically, when the current price equaled the take profit target, the TP was not being extended even with strong favorable conditions.

## Root Cause
In the `Position.update_take_profit()` method in `position_manager.py`, the logic for short positions had three branches:
1. `current_price > take_profit` - Price hasn't reached TP yet
2. `else` - Price at or past TP

When `current_price == take_profit` (price exactly at TP), the condition evaluated to False and entered the `else` branch. This branch only allowed TP updates if the new TP was closer to the current price, which prevented extending the TP further down even with strong downward momentum.

## Solution
Added a specific case to handle when `current_price == take_profit` for short positions. This allows the TP to be extended when:
- Price is exactly at the target
- There are strong favorable conditions (momentum, trend strength, volatility)
- Support/resistance levels cap the extension appropriately

## Changes Made
File: `position_manager.py`
- Added 4 lines after line 297 to handle the `current_price == self.take_profit` case
- This allows TP extension when price exactly equals TP, enabling the support/resistance capping logic to work correctly

## Test Results
- All 9/9 adaptive stops tests now pass
- All 50 tests across 9 test suites pass
- No regressions introduced

## Example Scenario
```python
# Short position
entry_price: 3000
initial_tp: 2900
current_price: 2900  # Exactly at TP

# With strong conditions:
# - momentum: -0.04 (strong downward)
# - trend_strength: 0.8
# - volatility: 0.06
# - support at 2800

# Result:
# TP extended from 2900 to 2897 (moving down)
# Capped by support at 2800 (doesn't go below)
```

## Impact
This fix ensures that when a short position's price reaches the take profit target, if market conditions suggest further favorable movement (strong downward momentum, high trend strength), the TP can be extended to capture more profit while respecting support/resistance levels.
