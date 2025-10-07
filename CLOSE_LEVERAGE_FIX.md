# Close Position Leverage Bug Fix - Summary

## Problem
When closing positions, the bot was always using 10x leverage regardless of the leverage the position was opened with.

### Root Causes
1. In `kucoin_client.py` line 739, the `close_position` method called `create_market_order` without passing the leverage parameter
2. In `position_manager.py` line 1168, the `scale_out_position` method also called `create_market_order` without passing the leverage parameter

Both `create_market_order` and `create_limit_order` have a default leverage parameter of 10x. When no leverage is passed, they always use 10x.

### Impact
- Positions opened with 5x leverage were closed with 10x leverage
- Positions opened with 20x leverage were closed with 10x leverage
- **Scale out operations** also used 10x leverage regardless of position leverage
- This could cause:
  - Unexpected exchange errors if the leverage doesn't match
  - Incorrect margin calculations during close
  - Potential failed close operations
  - Confusion in logs and monitoring

## Solution

### Code Changes

#### 1. Fixed `close_position()` in `kucoin_client.py`
Modified to extract and use the position's actual leverage:

```python
# Extract leverage from position data (multi-source)
# 1. Try CCXT unified 'leverage' field
leverage = pos.get('leverage')
if leverage is not None:
    try:
        leverage = int(leverage)
    except (ValueError, TypeError):
        self.logger.warning(
            f"Invalid leverage value '{leverage}' for {symbol}, defaulting to 10x"
        )
        leverage = 10
else:
    # 2. Try KuCoin-specific 'realLeverage' in raw info
    info = pos.get('info', {})
    real_leverage = info.get('realLeverage')
    if real_leverage is not None:
        try:
            leverage = int(real_leverage)
        except (ValueError, TypeError):
            self.logger.warning(
                f"Invalid realLeverage value '{real_leverage}' for {symbol}, defaulting to 10x"
            )
            leverage = 10
    else:
        # 3. Default to 10x with warning
        leverage = 10
        self.logger.warning(
            f"Leverage not found for {symbol} when closing, defaulting to 10x"
        )

# Pass leverage when closing
order = self.create_market_order(symbol, side, abs(contracts), leverage)
```

#### 2. Fixed `scale_out_position()` in `position_manager.py`
Modified to use the position's leverage when scaling out:

```python
# Close partial position with correct leverage
side = 'sell' if position.side == 'long' else 'buy'
order = self.client.create_market_order(symbol, side, amount_to_close, position.leverage)
```

### Features
1. **Multi-source extraction**: Checks both CCXT unified field and KuCoin-specific field (consistent with leverage sync fix)
2. **Clear warnings**: Logs warning when leverage is missing and defaulting to 10x
3. **Better logging**: Logs what leverage was used when closing position
4. **Backward compatible**: Still defaults to 10x if leverage truly isn't available
5. **Handles both market and limit orders**: Applies to both close order types

## Testing

### New Test Suite
Created `test_close_leverage_fix.py` with 5 comprehensive tests:

1. ✅ **Extract leverage from unified field** - Verifies standard CCXT leverage field works
2. ✅ **Extract leverage from KuCoin realLeverage** - Verifies KuCoin-specific field works
3. ✅ **Handle string conversion** - Verifies string leverage values are converted to int
4. ✅ **Default to 10x when missing** - Verifies safe fallback with warning
5. ✅ **Scale out uses position leverage** - Verifies scale out operations use correct leverage

All tests pass.

### Validation
- Existing `test_leverage_sync_fix.py` tests still pass
- Existing `test_position_sync.py` tests still pass
- No regression in other position management features

## Example

### Before Fix
```
Exchange positions:
  BTC: opened with 5x leverage  →  closed with 10x leverage ❌
  ETH: opened with 20x leverage →  closed with 10x leverage ❌
  SOL: opened with 3x leverage  →  closed with 10x leverage ❌
```

### After Fix
```
Exchange positions:
  BTC: opened with 5x leverage  →  closed with 5x leverage ✅
  ETH: opened with 20x leverage →  closed with 20x leverage ✅
  SOL: opened with 3x leverage  →  closed with 3x leverage ✅
```

## Impact

### Consistency
- Positions are now closed with the same leverage they were opened with
- Prevents potential exchange errors from leverage mismatch
- Ensures correct margin calculations throughout position lifecycle

### Logging
- Better visibility into what leverage is being used
- Warnings when leverage information is missing
- Easier debugging and monitoring

## Files Modified
- `kucoin_client.py`: Enhanced leverage extraction in `close_position()` method
- `position_manager.py`: Fixed `scale_out_position()` to use position leverage

## Files Added
- `test_close_leverage_fix.py`: Test suite for close leverage fix
- `CLOSE_LEVERAGE_FIX.md`: This documentation

## Deployment
- No configuration changes needed
- No API changes
- No breaking changes
- Safe to deploy immediately
- Backward compatible (still defaults to 10x if leverage unavailable)

## Related Fixes
This fix complements the earlier **Leverage Sync Fix** (documented in `LEVERAGE_SYNC_FIX.md`):
- Leverage Sync Fix: Ensures positions are **tracked** with correct leverage
- Close Leverage Fix: Ensures positions are **closed** with correct leverage

Together, these fixes ensure consistent leverage handling throughout the entire position lifecycle: open → track → update → close.
