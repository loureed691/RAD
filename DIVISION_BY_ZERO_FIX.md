# Division by Zero Fix in adjust_position_for_margin

## Problem Description

The trading bot was crashing with the following error:

```
2025-10-07 13:41:48 - TradingBot - WARNING - Margin check failed: Insufficient margin: available=$0.00, required=$8.95 (position value=$59.67, leverage=7x)
2025-10-07 13:41:48 - TradingBot - WARNING - Amount 0.0000 below minimum 1.0, adjusting to minimum
2025-10-07 13:41:48 - TradingBot - ERROR - Error adjusting position for margin: float division by zero
```

### Root Cause

The `adjust_position_for_margin()` method in `kucoin_client.py` was attempting to divide by zero when:
1. **Line 378**: `adjusted_leverage = int(position_value / usable_margin)` 
   - When `available_margin = 0.0`, then `usable_margin = 0.0 * 0.90 = 0.0`
   - Division by zero occurred: `position_value / 0.0`

2. **Line 364**: `adjusted_amount = max_position_value / (price * contract_size)`
   - Could also fail if `price = 0.0` or `contract_size = 0.0`

## Solution

Added guard checks at the beginning of the method to validate inputs before performing calculations:

### Changes Made

```python
def adjust_position_for_margin(self, symbol: str, amount: float, price: float, 
                               leverage: int, available_margin: float) -> tuple[float, int]:
    try:
        # Guard: Check for insufficient margin early
        if available_margin <= 0:
            self.logger.error(
                f"Cannot adjust position: no margin available (available=${available_margin:.2f})"
            )
            return 0.0, 1
        
        # Guard: Check for invalid price
        if price <= 0:
            self.logger.error(
                f"Cannot adjust position: invalid price (price=${price:.4f})"
            )
            return 0.0, 1
        
        # Get contract size for accurate calculations
        markets = self.exchange.load_markets()
        contract_size = 1
        if symbol in markets:
            contract_size = markets[symbol].get('contractSize', 1)
        
        # Guard: Check for invalid contract size
        if contract_size <= 0:
            self.logger.error(
                f"Cannot adjust position: invalid contract size (contract_size={contract_size})"
            )
            return 0.0, 1
        
        # Reserve 10% of available margin for safety and fees
        usable_margin = available_margin * 0.90
        
        # Guard: Ensure usable_margin is positive
        if usable_margin <= 0:
            self.logger.error(
                f"Cannot adjust position: insufficient usable margin after buffer (usable=${usable_margin:.2f})"
            )
            return 0.0, 1
        
        # ... rest of the method with safe divisions
        
        # Additional guard before division at line 378
        if usable_margin > 0:
            adjusted_leverage = int(position_value / usable_margin)
            adjusted_leverage = max(1, min(adjusted_leverage, leverage))
        else:
            adjusted_leverage = 1
```

## Behavior Changes

### Before Fix
- **Crash**: Division by zero error when available_margin = $0.00
- **No error message**: Silent crash with generic exception
- **Bot continues**: May attempt invalid orders

### After Fix
- **Graceful handling**: Returns (0.0, 1) for invalid inputs
- **Clear error message**: Logs specific reason for rejection
- **Early return**: Prevents downstream errors

## Test Coverage

Created comprehensive test suite in `test_division_by_zero_fix.py`:

1. **Zero available margin** ✅
   - Input: available_margin = 0.0
   - Expected: Returns (0.0, 1) with error message
   - Result: PASS

2. **Negative available margin** ✅
   - Input: available_margin = -10.0
   - Expected: Returns (0.0, 1) with error message
   - Result: PASS

3. **Zero price** ✅
   - Input: price = 0.0
   - Expected: Returns (0.0, 1) with error message
   - Result: PASS

4. **Very small margin** ✅
   - Input: available_margin = 0.001
   - Expected: Calculates adjusted position without crash
   - Result: PASS

5. **Normal case** ✅
   - Input: Normal values (margin=50.0, price=1.0, etc.)
   - Expected: Functions normally
   - Result: PASS

## Verification

### Simulating Original Error Scenario

```python
# Original error:
# "Margin check failed: Insufficient margin: available=$0.00, required=$8.95"
# "Error adjusting position for margin: float division by zero"

adjusted_amount, adjusted_leverage = client.adjust_position_for_margin(
    symbol='BAN/USDT:USDT',
    amount=44.0,
    price=1.356,
    leverage=7,
    available_margin=0.0  # The problematic case
)

# Result: (0.0, 1) - No crash!
# Log: "Cannot adjust position: no margin available (available=$0.00)"
```

### Existing Test Results

- ✅ `test_margin_limit_fix.py`: 4/4 tests passed
- ✅ `test_contract_size_margin_fix.py`: 2/2 tests passed
- ✅ `test_division_by_zero_fix.py`: 5/5 tests passed

## Impact

### What Changed
1. Method now validates inputs before performing calculations
2. Returns (0.0, 1) for invalid inputs instead of crashing
3. Logs clear error messages for debugging

### What Didn't Change
1. Normal operation with sufficient margin works identically
2. Position adjustment logic remains the same
3. Contract size handling unchanged
4. Leverage reduction logic unchanged

### Benefits
- **Stability**: No more crashes from division by zero
- **Clarity**: Clear error messages help identify issues
- **Safety**: Prevents invalid orders from being created
- **Robustness**: Handles edge cases gracefully

## Related Documentation

- `MARGIN_LIMIT_FIX.md` - Original margin checking implementation
- `CONTRACT_SIZE_MARGIN_FIX.md` - Contract size calculation fixes
- `MARGIN_LIMIT_FIX_FLOW.txt` - Flow diagram of margin checking
