# Scale-Out Order Validation Fix

## Problem
When executing partial exits (scale-out) on small positions, the calculated amount could be below the exchange's minimum order size, causing order validation failures.

### Example Error
```
14:55:34 ✓ INFO Partial exit signal: profit_scaling - First target reached (2.04%) (25%)
14:55:34 ✗ ERROR 🛑 Order validation failed: Amount 0.4285 below minimum 1.0
```

## Root Cause
- Position size: 1.714 contracts
- Profit target triggers 25% scale-out
- Calculated amount: 1.714 × 0.25 = 0.4285 contracts
- Exchange minimum: 1.0 contracts
- Result: Order rejected by exchange

## Solution
Added minimum order size validation in `position_manager.py` `scale_out_position()` method before submitting orders:

```python
# Check minimum order size before attempting to scale out
limits = self.client.get_market_limits(symbol)
if limits:
    min_amount = limits['amount']['min']
    if min_amount and amount_to_close < min_amount:
        self.logger.warning(
            f"Scale-out amount {amount_to_close:.4f} below minimum {min_amount} for {symbol}. "
            f"Skipping partial exit. Reason: {reason}"
        )
        return None
```

## Behavior
- **Before Fix**: Order submitted to exchange → Rejected → Error logged
- **After Fix**: Validated locally → Skipped with warning → Position remains open

## Benefits
1. Prevents unnecessary API calls to exchange
2. Avoids error logs from invalid orders
3. Position remains open to catch higher profit targets
4. Reduces API rate limit consumption

## Test Coverage
Added comprehensive tests in `test_scale_out_minimum_fix.py`:
- ✓ Below minimum: Rejected (0.4285 < 1.0)
- ✓ Above minimum: Accepted (1.25 > 1.0)
- ✓ Exactly at minimum: Accepted (1.0 == 1.0)
- ✓ No limits available: Allows order (graceful degradation)

## Edge Cases Handled
1. **Small positions**: Skip scale-out, wait for full exit signal
2. **No limit data**: Proceed with order (exchange validates)
3. **Exact minimum**: Allow scale-out (1.0 >= 1.0)
4. **Thread safety**: Maintained with existing lock mechanisms

## Files Modified
- `position_manager.py`: Added validation in `scale_out_position()` method
- `test_scale_out_minimum_fix.py`: New test file with 4 comprehensive tests

## Backward Compatibility
✓ No breaking changes
✓ Existing tests pass (test_profit_target_scaling)
✓ Graceful degradation if limits unavailable
✓ Existing behavior preserved for valid orders
