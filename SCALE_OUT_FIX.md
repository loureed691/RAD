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
Modified `position_manager.py` `scale_out_position()` method to automatically adjust order size to meet minimum requirements:

```python
# Check minimum order size before attempting to scale out
limits = self.client.get_market_limits(symbol)
if limits:
    min_amount = limits['amount']['min']
    if min_amount and amount_to_close < min_amount:
        # Adjust order size to meet minimum instead of skipping
        original_amount = amount_to_close
        amount_to_close = min_amount
        
        # Check if adjusted amount exceeds position size (thread-safe check)
        with self._positions_lock:
            if symbol not in self.positions:
                self.logger.error(f"No position found for {symbol} to scale out of")
                return None
            position = self.positions[symbol]
            should_close_entire = amount_to_close >= position.amount
        
        # If adjusted amount would close entire position, use close_position instead
        if should_close_entire:
            self.logger.info(
                f"Adjusted scale-out amount {amount_to_close:.4f} would close entire position "
                f"for {symbol} (position size: {position.amount:.4f}). Closing full position."
            )
            return self.close_position(symbol, reason)
        
        self.logger.warning(
            f"Scale-out amount {original_amount:.4f} below minimum {min_amount} for {symbol}. "
            f"Adjusting to minimum {amount_to_close:.4f}. Reason: {reason}"
        )
```

## Behavior
- **Before Fix**: Validated locally → Skipped with warning → Position remains unchanged
- **After Fix**: Validated locally → Adjusted to minimum → Order executed at minimum size

## Benefits
1. Ensures profit targets are captured even on small positions
2. Prevents missed exit opportunities
3. Automatically closes entire position if adjustment would exceed position size
4. Maintains exchange compliance with minimum order requirements
5. Reduces API rate limit consumption by avoiding invalid orders

## Test Coverage
Added comprehensive tests in `test_scale_out_minimum_fix.py`:
- ✓ Below minimum: Adjusted to minimum (0.4285 → 1.0)
- ✓ Above minimum: Accepted as-is (1.25 > 1.0)
- ✓ Exactly at minimum: Accepted (1.0 == 1.0)
- ✓ No limits available: Allows order (graceful degradation)
- ✓ Adjusted exceeds position: Closes entire position (0.2 → 1.0 > 0.8 position)

## Edge Cases Handled
1. **Small positions**: Adjust scale-out to minimum, execute partial exit
2. **Very small positions**: If adjusted amount exceeds position size, close entire position
3. **No limit data**: Proceed with order (exchange validates)
4. **Exact minimum**: Allow scale-out (1.0 >= 1.0)
5. **Thread safety**: Maintained with existing lock mechanisms, avoided deadlock by releasing lock before calling close_position

## Files Modified
- `position_manager.py`: Modified validation in `scale_out_position()` method to adjust to minimum instead of skipping
- `test_scale_out_minimum_fix.py`: Updated test file with 5 comprehensive tests including new adjustment scenarios

## Backward Compatibility
✓ No breaking changes
✓ Existing tests updated to reflect new behavior
✓ Graceful degradation if limits unavailable
✓ More aggressive profit-taking on small positions (improvement over skipping)
