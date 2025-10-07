# Zero Margin Fix - Quick Reference

## What Was Fixed
**Division by zero error** when closing positions with zero available margin.

## Key Changes

### 1. New Parameter: `reduce_only`
```python
# Close positions now use reduce_only=True
order = client.create_market_order(
    symbol='BAN/USDT:USDT',
    side='sell',
    amount=44.0,
    leverage=3,
    reduce_only=True  # ← Bypasses margin checks
)
```

### 2. Zero-Margin Protection
```python
# In adjust_position_for_margin()
if available_margin <= 0.01:
    return 0.0, 1  # Safe failure instead of division by zero
```

### 3. Zero-Price Protection
```python
# In adjust_position_for_margin()
if price <= 0:
    return 0.0, 1  # Safe failure instead of division by zero
```

## When to Use reduce_only

### ✅ Use reduce_only=True for:
- Closing positions (full or partial)
- Taking profit orders
- Stop loss orders
- Any order that reduces your exposure

### ❌ Use reduce_only=False for:
- Opening new positions
- Adding to existing positions
- Any order that increases your exposure

## Error Messages

### Before Fix
```
✗ ERROR Error adjusting position for margin: float division by zero
✗ ERROR Failed to create close order
```

### After Fix
```
✗ ERROR Cannot adjust position: available margin $0.0000 is too low (minimum required: $0.01)
✓ INFO Close order created successfully (with reduce_only=True)
```

## Testing

Run tests to verify the fix:
```bash
python3 test_zero_margin_fix.py
python3 test_exact_problem_scenario.py
```

Expected: All tests pass ✓

## Files Changed

| File | Change |
|------|--------|
| `kucoin_client.py` | Added reduce_only parameter and zero guards |
| `test_zero_margin_fix.py` | Comprehensive test suite |
| `test_exact_problem_scenario.py` | Exact error reproduction test |
| `ZERO_MARGIN_FIX.md` | Full documentation |

## Impact

- ✅ No more crashes when closing positions with zero margin
- ✅ Graceful error handling for edge cases
- ✅ Clear, actionable error messages
- ✅ All existing functionality preserved
