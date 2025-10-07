# Reduce-Only Leverage Fix - Quick Reference

## Problem
Error 330008 when closing positions: "Your current margin and leverage have reached the maximum open limit"

## Root Cause
`set_leverage()` was called even for reduce_only (close) orders, which fails when all margin is in use.

## Solution
Skip `set_leverage()` and `set_margin_mode()` for reduce_only orders.

## Changes
- `kucoin_client.py::create_market_order()` - Skip leverage setting for reduce_only
- `kucoin_client.py::create_limit_order()` - Skip leverage setting for reduce_only

## Code Changes

### Before
```python
# Always set leverage
self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})
order = self.exchange.create_order(...)
```

### After
```python
# Skip for reduce_only (closing positions)
if not reduce_only:
    self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})

params = {"marginMode": "cross"}
if reduce_only:
    params["reduceOnly"] = True
order = self.exchange.create_order(..., params=params)
```

## Test Results
✅ All tests pass (3/3 new tests + all existing tests)

## Impact
- ✅ Positions can always be closed
- ✅ No more error 330008 on close
- ✅ Exit signals work reliably
- ✅ Backward compatible

## Files
- `kucoin_client.py` - Implementation
- `test_reduce_only_leverage_fix.py` - Tests
- `REDUCE_ONLY_LEVERAGE_FIX.md` - Full documentation
