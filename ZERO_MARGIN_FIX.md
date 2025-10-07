# Fix for Division by Zero Error in Margin Adjustment

## Problem Statement

When closing a position with zero available margin, the system encountered a division by zero error:

```
13:51:12 ⚠️ WARNING Margin check failed: Insufficient margin: available=$0.00, required=$8.95
13:51:12 ⚠️ WARNING Amount 0.0000 below minimum 1.0, adjusting to minimum
13:51:12 ✗ ERROR Error adjusting position for margin: float division by zero
13:51:12 ✓ INFO Adjusted position to fit margin: 44.0000 contracts at 3x leverage
13:51:13 ✗ ERROR Error creating market order: kucoinfutures {"msg":"Current leverage is too low...","code":"330009"}
13:51:13 ✗ ERROR Failed to create close order for BAN/USDT:USDT
```

## Root Causes

1. **Missing `reduce_only` parameter**: The `create_market_order` method didn't support a `reduce_only` parameter, so close orders went through the same margin checks as opening orders.

2. **Division by zero in margin adjustment**: In `adjust_position_for_margin` at line 378:
   ```python
   adjusted_leverage = int(position_value / usable_margin)
   ```
   When `available_margin = $0.00`, then `usable_margin = 0.00 * 0.90 = 0.00`, causing division by zero.

3. **Unnecessary margin checks for closing**: Closing positions don't require available margin since they reduce exposure, but the code checked margin anyway.

## Solution

### 1. Added `reduce_only` Parameter to `create_market_order`

**File**: `kucoin_client.py`, line 413

```python
def create_market_order(self, symbol: str, side: str, amount: float, 
                       leverage: int = 10, max_slippage: float = 0.01,
                       validate_depth: bool = True, reduce_only: bool = False) -> Optional[Dict]:
```

### 2. Skip Margin Checks for `reduce_only` Orders

**File**: `kucoin_client.py`, lines 442-472

```python
# Skip margin check for reduce_only orders as they close positions
if not reduce_only:
    # Check if we have enough margin for this position (error 330008 prevention)
    has_margin, available_margin, margin_reason = self.check_available_margin(
        symbol, validated_amount, reference_price, leverage
    )

    if not has_margin:
        # ... margin adjustment logic ...
```

### 3. Added Zero-Margin Guard in `adjust_position_for_margin`

**File**: `kucoin_client.py`, lines 351-358

```python
# Check for zero or near-zero margin early to prevent division by zero
if available_margin <= 0.01:
    self.logger.error(
        f"Cannot adjust position: available margin ${available_margin:.4f} is too low "
        f"(minimum required: $0.01)"
    )
    # Return minimal viable values that will fail viability check
    return 0.0, 1
```

### 4. Added Zero-Price Guard

**File**: `kucoin_client.py`, lines 366-369

```python
# Check for zero price to prevent division by zero
if price <= 0:
    self.logger.error(f"Cannot adjust position: invalid price {price}")
    return 0.0, 1
```

### 5. Updated `close_position` to Use `reduce_only=True`

**File**: `kucoin_client.py`, lines 772, 787

```python
# When closing with market order
order = self.create_market_order(symbol, side, abs(contracts), leverage, reduce_only=True)

# When falling back to market order from limit
order = self.create_market_order(symbol, side, abs(contracts), leverage, reduce_only=True)
```

## Expected Behavior After Fix

### Scenario 1: Closing Position with Zero Margin

**Before:**
```
⚠️ WARNING Margin check failed: Insufficient margin: available=$0.00, required=$8.95
✗ ERROR Error adjusting position for margin: float division by zero
✗ ERROR Failed to create close order
```

**After:**
```
✓ INFO Creating close order for BAN/USDT:USDT (reduce_only=True)
✓ INFO Closed position for BAN/USDT:USDT with 7x leverage
```

### Scenario 2: Opening Position with Zero Margin

**Before:**
```
⚠️ WARNING Margin check failed: Insufficient margin: available=$0.00
✗ ERROR Error adjusting position for margin: float division by zero
```

**After:**
```
⚠️ WARNING Margin check failed: Insufficient margin: available=$0.00, required=$8.95
✗ ERROR Cannot adjust position: available margin $0.0000 is too low (minimum required: $0.01)
✗ ERROR Cannot open position: adjusted position not viable - Position size 0.0000 below exchange minimum 1.0
```

## Testing

Created comprehensive test suite in `test_zero_margin_fix.py`:

### Test 1: Zero Margin Adjustment
```python
# Tests that zero margin doesn't cause division by zero
adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
    'BAN/USDT:USDT', 100, 1.0, 7, 0.00
)
# Result: amount=0.0, leverage=1 (safe failure without exception)
```

### Test 2: reduce_only Parameter
```python
# Tests that reduce_only=True bypasses margin check
order = client.create_market_order(
    'BAN/USDT:USDT', 'sell', 44.0, leverage=3, reduce_only=True
)
# Result: order succeeds even with zero margin
```

### Test 3: Zero Price Protection
```python
# Tests that zero price doesn't cause division by zero
adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
    'TEST/USDT:USDT', 100, 0.0, 7, 10.00
)
# Result: amount=0.0, leverage=1 (safe failure without exception)
```

## Test Results

```
✓ test_zero_margin_fix.py: 3/3 tests passed
✓ test_margin_limit_fix.py: 4/4 tests passed  
✓ test_contract_size_margin_fix.py: 2/2 tests passed
```

## Files Changed

1. **kucoin_client.py**:
   - Line 413: Added `reduce_only` parameter to `create_market_order` method
   - Lines 351-369: Added zero-margin and zero-price guards in `adjust_position_for_margin`
   - Lines 442-472: Added conditional margin check skip for `reduce_only` orders
   - Lines 772, 787: Updated `close_position` to pass `reduce_only=True`

2. **test_zero_margin_fix.py** (new):
   - Comprehensive test coverage for division by zero fixes
   - Tests zero margin, reduce_only parameter, and zero price protection

## Impact

### Before Fix
- ❌ Division by zero errors when closing positions with zero margin
- ❌ Unnecessary margin checks for closing orders
- ❌ System crashes with exception instead of graceful failure

### After Fix
- ✅ Closing positions works even with zero available margin
- ✅ Graceful error handling for edge cases (zero margin, zero price)
- ✅ Clear error messages explaining why positions are rejected
- ✅ No more division by zero exceptions

## Verification

To verify the fix works:

```bash
python3 test_zero_margin_fix.py
```

Expected output: All 3 tests pass ✓
