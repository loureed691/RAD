# Close Position Leverage Fix - Quick Reference

## Problem Summary
Bot was closing positions with 10x leverage regardless of the leverage they were opened with.

## Root Cause
- `kucoin_client.py`: `close_position()` didn't pass leverage parameter
- `position_manager.py`: `scale_out_position()` didn't pass leverage parameter
- Both methods called `create_market_order()` without leverage, causing default 10x to be used

## Solution
✅ Extract leverage from position data (CCXT unified or KuCoin realLeverage)
✅ Pass extracted leverage to `create_market_order()` and `create_limit_order()`
✅ Fallback to 10x with warning if leverage unavailable

## Code Changes

### kucoin_client.py - close_position()
```python
# Extract leverage from position
leverage = pos.get('leverage')
if leverage is None:
    leverage = pos.get('info', {}).get('realLeverage', 10)

# Pass leverage when closing
order = self.create_market_order(symbol, side, abs(contracts), leverage)
```

### position_manager.py - scale_out_position()
```python
# Use position's leverage for scale out
order = self.client.create_market_order(symbol, side, amount_to_close, position.leverage)
```

## Testing
- ✅ 5/5 new tests pass (`test_close_leverage_fix.py`)
- ✅ All existing tests pass (no regressions)
- ✅ Demo script available (`demo_close_leverage_fix.py`)

## Impact
| Before | After |
|--------|-------|
| 5x position → closed with 10x ❌ | 5x position → closed with 5x ✅ |
| 20x position → closed with 10x ❌ | 20x position → closed with 20x ✅ |
| 3x position → closed with 10x ❌ | 3x position → closed with 3x ✅ |

## Benefits
- ✅ No more leverage mismatch errors
- ✅ Consistent leverage throughout position lifecycle
- ✅ Correct margin calculations
- ✅ Better logging and monitoring

## Files
- **Modified**: `kucoin_client.py`, `position_manager.py`
- **Added**: `test_close_leverage_fix.py`, `CLOSE_LEVERAGE_FIX.md`, `demo_close_leverage_fix.py`

## Related Fixes
This complements the **Leverage Sync Fix** to ensure complete leverage consistency:
- Leverage Sync Fix: Tracks positions with correct leverage
- Close Leverage Fix: Closes positions with correct leverage

Together: **Open → Track → Update → Close** all use correct leverage ✅
