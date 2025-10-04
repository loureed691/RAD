# Margin Mode Error 330006 - Fix Summary

## Problem
Bot was failing with error:
```
ERROR - Error creating market order: kucoinfutures {"msg":"Current mode is set to isolated margin. Please switch to cross margin before making further adjustments.","code":"330006"}
```

## Root Cause
When a KuCoin position is in **isolated margin mode**, the bot cannot set leverage or create orders even with the correct `marginMode` parameter. The margin mode must be explicitly switched first.

## Solution Applied
Added `self.exchange.set_margin_mode('cross', symbol)` before `set_leverage()` calls.

### Changes to `kucoin_client.py`

Two methods were updated with minimal changes:

1. **`create_market_order()` (line 178)**:
   - Added: `self.exchange.set_margin_mode('cross', symbol)`
   - Position: Before `set_leverage()` call

2. **`create_limit_order()` (line 208)**:
   - Added: `self.exchange.set_margin_mode('cross', symbol)`
   - Position: Before `set_leverage()` call

## Code Sequence (After Fix)

```python
# 1. Switch margin mode to cross
self.exchange.set_margin_mode('cross', symbol)

# 2. Set leverage with cross margin mode
self.exchange.set_leverage(leverage, symbol, params={"marginMode": "cross"})

# 3. Create order with cross margin mode
order = self.exchange.create_order(
    symbol=symbol,
    type='market',
    side=side,
    amount=validated_amount,
    params={"marginMode": "cross"}
)
```

## Testing Results
- ✅ All 12 existing tests pass
- ✅ Verification script confirms fix is properly implemented
- ✅ Both error 330005 and 330006 are now handled

## Files Modified
- `kucoin_client.py` - Added margin mode switching (2 lines)
- `CHANGELOG.md` - Documented the fix
- `MARGIN_330006_FIX.md` - Comprehensive documentation
- `verify_margin_330006_fix.py` - Verification script (new)

## Impact
- Minimal code change (2 lines added)
- No breaking changes
- Fixes the isolated margin mode error
- Works in combination with existing 330005 fix
- Production ready
