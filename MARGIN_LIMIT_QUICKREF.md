# Margin Limit Fix - Quick Reference

## What Was Fixed

**Error 330008**: "Your current margin and leverage have reached the maximum open limit"

## Solution

The bot now checks available margin before creating orders and automatically adjusts position size/leverage to fit.

## New Methods in KuCoinClient

### 1. `calculate_required_margin(symbol, amount, price, leverage)`
Calculates margin needed: `(amount × price) / leverage`

### 2. `check_available_margin(symbol, amount, price, leverage)`
Checks if sufficient margin exists (with 5% buffer)

Returns: `(has_sufficient, available_amount, reason)`

### 3. `adjust_position_for_margin(symbol, amount, price, leverage, available_margin)`
Adjusts position to fit available margin (uses 90% of available)

Returns: `(adjusted_amount, adjusted_leverage)`

## Updated Methods

### `create_market_order(...)` 
- Now checks margin before creating order
- Auto-adjusts if insufficient
- Rejects if adjusted position < 10% of desired

### `create_limit_order(...)`
- Same margin checking as market orders
- **Skips check** for `reduce_only=True` orders

## Behavior

### With Sufficient Margin
```
✓ Created buy order for 2086.4044 contracts at 12x leverage
```

### With Insufficient Margin (Auto-Adjusted)
```
⚠️ WARNING Insufficient margin: available=$0.50, required=$0.24
⚠️ WARNING Reducing position size to 1800.0000 contracts
✓ Created buy order for 1800.0000 contracts at 12x leverage
```

### With Very Limited Margin (Rejected)
```
⚠️ WARNING Insufficient margin: available=$0.01, required=$0.24
✗ ERROR Cannot open position: adjusted position too small
```

## Testing

Run: `python3 test_margin_limit_fix.py`

Expected: `4/4 tests passed`

## Key Features

- ✓ Prevents error 330008
- ✓ Automatic position adjustment
- ✓ 5% safety buffer for fees
- ✓ 10% reserve when adjusting
- ✓ Transparent logging
- ✓ Graceful when balance unavailable
- ✓ No breaking changes

## Files Modified

- `kucoin_client.py` - Added 3 methods, updated 2 methods
- `test_margin_limit_fix.py` - New test suite
- `MARGIN_LIMIT_FIX.md` - Full documentation

## See Also

- Full documentation: `MARGIN_LIMIT_FIX.md`
- Other fixes: `MARGIN_MODE_FIX.md`, `POSITION_MODE_FIX.md`
