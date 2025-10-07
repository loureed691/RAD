# Fix Summary: Error 330008 on Reduce-Only Orders

## Issue
Bot failed to close positions with error 330008: "Your current margin and leverage have reached the maximum open limit"

## Root Cause
`set_leverage()` was called even for reduce_only (close) orders, which fails when all margin is in the position being closed.

## Solution
Skip `set_leverage()` and `set_margin_mode()` for reduce_only orders.

## Changes (2 lines modified in 2 methods)

### `create_market_order()` - Line 489
```python
# Before: Always set leverage
self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})

# After: Skip for reduce_only
if not reduce_only:
    self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})
```

### `create_limit_order()` - Line 644
```python
# Before: Always set leverage
self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})

# After: Skip for reduce_only
if not reduce_only:
    self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})
```

## Testing
✅ 6/6 tests pass:
- test_reduce_only_leverage_fix.py (NEW)
- test_zero_margin_fix.py
- test_exact_problem_scenario.py
- test_close_leverage_fix.py
- test_margin_limit_fix.py
- test_contract_size_margin_fix.py

## Result
✅ Positions can always be closed
✅ No more error 330008 on close
✅ Exit signals work reliably
✅ Backward compatible
