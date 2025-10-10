# Stop Loss Bug Fix - Stalled Position Logic

## Problem

The "stalled position" stop loss logic (lines 667 and 685 in `position_manager.py`) had a bug where it was **double-leveraging** the ROI threshold.

### The Bug

After the initial leveraged P&L fix (commit 530027e), the code set:
```python
current_pnl = self.get_leveraged_pnl(current_price)  # Already leveraged ROI
```

But then the stalled position check was:
```python
if time_in_trade >= 4.0 and current_pnl < 0.02 * self.leverage:
```

This created the wrong threshold:
- With 10x leverage: `0.02 * 10 = 0.20` (20% threshold instead of 2%)
- With 5x leverage: `0.02 * 5 = 0.10` (10% threshold instead of 2%)
- With 1x leverage: `0.02 * 1 = 0.02` (2% - correct by coincidence)

### Why This Happened

The original code (before commit 530027e) used:
```python
current_pnl = self.get_pnl(current_price)  # Unleveraged price movement
```

So multiplying by `self.leverage` made sense to convert to ROI.

But after the fix changed `current_pnl` to use `get_leveraged_pnl()`, the multiplication was no longer needed and created a bug.

## The Fix

**Before:**
```python
# Use leveraged P&L for ROI checks (2% ROI, not 2% price movement)
if time_in_trade >= 4.0 and current_pnl < 0.02 * self.leverage:  # BUG!
```

**After:**
```python
# current_pnl is already leveraged ROI, so check against 2% ROI directly
if time_in_trade >= 4.0 and current_pnl < 0.02:  # 4 hours with < 2% ROI
```

## Impact

### Before Fix (with 10x leverage):
- Stalled position stop triggered only when ROI < **20%** after 4 hours
- Position with 15% ROI after 5 hours would NOT trigger tighter stop (wrong!)

### After Fix (with 10x leverage):
- Stalled position stop triggers correctly when ROI < **2%** after 4 hours
- Position with 1.5% ROI after 5 hours correctly triggers tighter stop

### Example

**Scenario:** 10x leverage position, been open for 5 hours
- Entry: $100.00
- Current: $100.15 (0.15% price move = 1.5% ROI with 10x)

**Before Fix:**
- Threshold: 20% (0.02 × 10)
- 1.5% ROI < 20% ✓
- But stalled stop doesn't trigger because threshold is too high
- Result: Position stays open despite poor performance ❌

**After Fix:**
- Threshold: 2% (0.02)
- 1.5% ROI < 2% ✓
- Stalled stop triggers correctly
- Result: Position closes with tighter stop ✅

## Files Changed

- `position_manager.py` (lines 666, 684): Fixed stalled position threshold
- `test_stalled_stop_loss.py`: New test validating the fix
- `LEVERAGED_PNL_FIX.md`: Updated documentation

## Testing

New test file `test_stalled_stop_loss.py` validates:
1. ✅ 10x leverage position with 1.5% ROI triggers stalled stop
2. ✅ 10x leverage position with 2.5% ROI does NOT trigger stalled stop
3. ✅ All leverage levels (1x, 5x, 10x, 20x) use consistent 2% ROI threshold

All existing tests continue to pass.

## Root Cause

This was a subtle interaction between two changes:
1. The initial fix correctly changed `current_pnl` to use leveraged ROI
2. But the stalled position checks still had the `* self.leverage` multiplication from the original code
3. This created double-leveraging: `leveraged_ROI * leverage` instead of just `leveraged_ROI`

## Verification

To verify the fix is working:
```bash
python test_stalled_stop_loss.py
python test_leveraged_pnl_fix.py
python test_comprehensive_leveraged_pnl.py
```

All tests should pass ✅
