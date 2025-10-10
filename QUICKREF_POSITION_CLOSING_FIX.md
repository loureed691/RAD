# Quick Reference: Position Closing Fix

## The Problem
Positions were opening but never closing - orders were not going through.

## The Root Cause
`position_manager.scale_out_position()` was missing `reduce_only=True` parameter when calling `create_market_order()`.

## The Fix (One Line Change)
```python
# Line 1755 in position_manager.py
# BEFORE:
order = self.client.create_market_order(symbol, side, amount_to_close, position.leverage)

# AFTER:
order = self.client.create_market_order(symbol, side, amount_to_close, position.leverage, reduce_only=True)
```

## Why This Matters
Without `reduce_only=True`:
- ❌ Orders fail when margin is fully utilized
- ❌ Exchange validates margin as if opening NEW position
- ❌ Stop losses and take profits cannot execute
- ❌ Positions remain open indefinitely

With `reduce_only=True`:
- ✅ Orders bypass margin validation
- ✅ Exchange knows this is closing an existing position
- ✅ Stop losses and take profits work correctly
- ✅ Positions close as expected

## Verification
```bash
# Run the validation test
python3 test_reduce_only_fix.py

# Expected: ALL TESTS PASSED ✓
```

## Documentation
- **Full Details**: `REDUCE_ONLY_BUG_FIX.md`
- **Test File**: `test_reduce_only_fix.py`
- **Changed File**: `position_manager.py` (line 1755)

## Impact
- **Severity**: CRITICAL (positions couldn't close)
- **Change Size**: 1 line
- **Risk**: LOW (well-tested pattern)
- **Status**: ✅ FIXED

---

**Fixed**: 2025-10-10  
**Commit**: dc1d24c
