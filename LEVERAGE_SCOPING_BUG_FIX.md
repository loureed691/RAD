# Leverage Variable Scoping Bug Fix

## Problem Statement

The bot was failing to create market and limit orders with the error:
```
ERROR Error creating market order: cannot access local variable 'leverage' where it is not associated with a value
ERROR Failed to create close order for ALICE/USDT:USDT
```

This error occurred when trying to close positions or create new orders.

## Root Cause

The issue was caused by Python's variable scoping rules in nested functions. In both `create_market_order()` and `create_limit_order()` methods in `kucoin_client.py`:

1. The `_create_order()` nested function is defined inside these methods
2. The nested function uses the `leverage` parameter from the outer function
3. Later in the nested function, there's a conditional assignment: `leverage = adjusted_leverage` (lines 636 and 839)
4. **Python's scoping rule**: When a variable is assigned anywhere in a function, Python treats it as a local variable for the *entire* function, even before the assignment line
5. This caused `UnboundLocalError` when code tried to use `leverage` before the assignment (e.g., at lines 613, 620, 816, 823)

### Example Demonstrating the Bug

```python
def outer(leverage=10):
    def inner():
        # This line fails with UnboundLocalError
        print(f"Using leverage: {leverage}")
        
        # Because this assignment makes leverage "local" to inner()
        if some_condition:
            leverage = 20
    
    inner()
```

## Solution

Add `nonlocal leverage` declaration at the beginning of the `_create_order()` nested functions. This tells Python that `leverage` refers to the outer function's parameter, not a new local variable.

### Fixed Code

```python
def create_market_order(self, symbol: str, side: str, amount: float, 
                       leverage: int = 10, ...):
    def _create_order():
        nonlocal leverage  # <-- The fix
        try:
            # Now leverage can be read and modified
            ...
            leverage = adjusted_leverage  # This works now
```

## Changes Made

### Files Modified

1. **kucoin_client.py**:
   - Line 596: Added `nonlocal leverage` in `create_market_order._create_order()`
   - Line 809: Added `nonlocal leverage` in `create_limit_order._create_order()`

2. **CHANGELOG.md**:
   - Documented the bug, root cause, and fix

3. **test_leverage_scoping_fix.py** (NEW):
   - Comprehensive test demonstrating the bug and verifying the fix
   - Tests all three order creation methods
   - Shows that `create_stop_limit_order` doesn't need the fix (no conditional assignment)

## Verification

### Compilation Check
```bash
python3 -m py_compile kucoin_client.py position_manager.py
# ✓ All affected files compile successfully
```

### Test Results
```bash
python3 test_leverage_scoping_fix.py
# ✅ ALL TESTS PASSED - The leverage scoping bug is fixed!
```

### Test Coverage

The test file covers:
1. **Basic scoping demonstration**: Shows the bug without `nonlocal` and fix with `nonlocal`
2. **create_market_order scenario**: Tests both `reduce_only=True` and `reduce_only=False` paths
3. **create_limit_order scenario**: Tests both `reduce_only=True` and `reduce_only=False` paths
4. **create_stop_limit_order scenario**: Verifies it doesn't have the issue (no fix needed)

## Impact

This fix resolves the error that was preventing:
- Closing positions (especially with market orders)
- Creating new positions when margin adjustments are needed
- Any scenario where the leverage variable needed to be read and potentially modified

The fix is minimal, surgical, and follows Python best practices for variable scoping in nested functions.

## Related Issues

This bug only affected scenarios where:
1. A nested function needs to both read and modify a variable from an outer scope
2. The modification is conditional (not always executed)
3. The variable is read before the potential modification

The `create_stop_limit_order` method doesn't have this issue because it only reads the `leverage` variable, never modifying it.
