# Position Close Race Condition Fix

## Problem Description

The bot was attempting to close positions that were already closed, causing errors and unnecessary API calls. This occurred in the `update_positions()` method in `position_manager.py`.

## Symptoms

- Error messages about positions not found
- Attempts to close already-closed positions
- Multiple close attempts for the same position in a single update cycle
- Potential KeyError exceptions

## Root Cause

The `update_positions()` method has multiple exit conditions that can trigger sequentially:

1. **OHLCV API Error Fallback** (~line 1315): When market data fetch fails, uses simple trailing stop
2. **Advanced Exit Strategy** (~line 1459): Checks momentum reversal, profit protection, etc.
3. **Smart Exit Optimizer** (~line 1507): ML-based exit timing optimization
4. **Standard Stop Loss/Take Profit** (~line 1527): Traditional SL/TP checks

When one condition triggers and closes a position, subsequent conditions in the same iteration might still attempt to close it, causing the error.

## Solution

Added **thread-safe position existence checks** before each `close_position()` call. This ensures that if a position has already been closed by an earlier exit condition, subsequent conditions skip the close attempt gracefully.

### Implementation

Each of the 4 critical locations now has this check:

```python
# Thread-safe check: verify position still exists before closing
with self._positions_lock:
    if symbol not in self.positions:
        self.position_logger.debug(f"  ℹ Position {symbol} already closed, skipping")
        continue
```

### Why This Works

1. **Thread-Safe**: Uses `_positions_lock` to prevent race conditions
2. **Early Exit**: `continue` statement skips to next position immediately
3. **Clear Logging**: Debug message explains why close was skipped
4. **No Side Effects**: Doesn't interfere with normal operation

## Testing

### Verification Script

Run `verify_position_close_fix.py` to verify the fix:

```bash
python verify_position_close_fix.py
```

This script:
- Checks that all 4 critical locations have the fix
- Verifies thread safety (checks are inside locks)
- Confirms the fix pattern is correctly applied

### Unit Tests

The `test_position_close_race_condition.py` file contains comprehensive unit tests:

1. **test_position_not_closed_twice_on_ohlcv_error**: Verifies position isn't closed twice when OHLCV API fails
2. **test_position_not_closed_twice_on_multiple_exit_conditions**: Tests multiple exit conditions triggering
3. **test_concurrent_position_close_prevention**: Tests concurrent close prevention
4. **test_position_removal_check_before_close**: Verifies existence check before close

## Impact

### Before Fix
- Multiple close attempts per position possible
- API errors from closing already-closed positions
- Log spam from repeated close attempts
- Potential unexpected behavior

### After Fix
- Maximum one close attempt per position per update cycle
- Clean handling when position already closed
- Clear debug logging for skipped closes
- Consistent, predictable behavior

## Files Changed

- `position_manager.py`: Added 4 position existence checks
- `verify_position_close_fix.py`: Verification script (NEW)
- `test_position_close_race_condition.py`: Unit tests (NEW)

## Verification Results

```
✅ All verifications passed
✅ 4 critical locations fixed
✅ Thread safety verified (position checks inside locks)
✅ Python syntax check passed
```

## Maintenance Notes

When adding new exit conditions to `update_positions()`:

1. Always check position existence before calling `close_position()`
2. Use the thread-safe pattern shown above
3. Add a clear debug log message
4. Use `continue` to skip to next position after close

## Related Issues

This fix addresses the issue: "the bot sometimes tries to close positions that are already closed"
