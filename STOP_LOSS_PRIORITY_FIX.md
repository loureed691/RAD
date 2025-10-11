# Stop Loss Priority Fix - ROI and P&L with Leverage

## Problem Statement
Ensure that ROI (Return on Investment) and P&L (Profit and Loss) are calculated correctly with leverage for stop loss functionality.

## Issue Identified
The stop loss logic had an ordering issue where emergency ROI-based stops were checked BEFORE the regular stop loss price checks. This caused positions to report emergency stop reasons even when the actual stop loss price was hit.

### Example of the Issue
With 10x leverage:
- Entry: $100
- Stop Loss: $95
- Price drops to: $95 (stop loss hit)
- Price move: -5%
- Leveraged ROI: -50%

**Before Fix:**
- Checked emergency stops first
- Found ROI ≤ -50%, returned `'emergency_stop_liquidation_risk'`
- Never reached the stop loss price check

**After Fix:**
- Checks stop loss price first
- Price ≤ $95, returns `'stop_loss'`
- Emergency stops act as failsafe for when stop loss fails

## Root Cause
The emergency stop loss protection (added to prevent catastrophic losses like 130%+) was placed at the top of the `should_close()` method, checking ROI thresholds (-20%, -35%, -50%) before checking if the stop loss price was hit.

While this ensured no position could exceed -50% ROI loss, it caused incorrect reporting of the close reason when the actual stop loss price was hit.

## The Fix

### Changes to `position_manager.py`

**1. Moved stop loss price checks to top priority (lines 608-616)**

```python
def should_close(self, current_price: float) -> tuple[bool, str]:
    """Check if position should be closed"""
    current_pnl = self.get_leveraged_pnl(current_price)
    
    # PRIORITY CHECK: Regular stop loss price level check
    # Check this FIRST so that when the stop loss price is hit, it returns 'stop_loss'
    # rather than an emergency stop reason (which should only trigger if stop loss fails)
    if self.side == 'long':
        if current_price <= self.stop_loss:
            return True, 'stop_loss'
    else:  # short
        if current_price >= self.stop_loss:
            return True, 'stop_loss'
    
    # CRITICAL SAFETY: Tiered emergency stop loss based on ROI
    # These act as failsafe when regular stop loss fails
    # (e.g., price gaps, stop loss order fails, etc.)
    ...
```

**2. Updated comments to clarify emergency stops are failsafe (lines 619-621)**

Changed from:
```python
# These are absolute maximum loss caps that override all other logic
```

To:
```python
# These are absolute maximum loss caps that act as failsafe when regular stop loss fails
```

**3. Removed duplicate stop loss checks (lines 688-714)**

The duplicate checks were at lines 681-682 and 699-700. After moving the check to the top, these duplicates were removed and only the stalled position logic and take profit checks remain.

## Impact

### Correct Behavior Now
1. **Stop Loss Price Hit**: Returns `'stop_loss'` (correct reason)
2. **Stop Loss Not Hit, High Loss**: Returns `'emergency_stop_*'` (failsafe)
3. **Works with All Leverage**: Consistent behavior across 1x, 5x, 10x, 20x, etc.

### Example Scenarios

**Scenario 1: Normal Stop Loss (10x leverage)**
- Entry: $100, Stop: $95, Price: $95
- ROI: -50% (5% price × 10x leverage)
- Result: `'stop_loss'` ✅

**Scenario 2: Emergency Stop as Failsafe (10x leverage)**
- Entry: $100, Stop: $90, Price: $96
- Price hasn't hit stop loss yet
- ROI: -40% (4% price × 10x leverage)
- Result: `'emergency_stop_severe_loss'` ✅ (failsafe)

**Scenario 3: Stalled Position (10x leverage)**
- Entry: $100, Stop: $95, Current: $100.15 (5 hours old)
- ROI: 1.5% (< 2% threshold after 4+ hours)
- Price drops to: $99 (1% below entry)
- Result: `'stop_loss_stalled_position'` ✅

## ROI Calculation with Leverage

The system correctly uses leveraged ROI for all decision-making:

### Formulas
```python
# Unleveraged P&L (price movement only)
pnl = (current_price - entry_price) / entry_price

# Leveraged ROI (actual return on investment)
roi = pnl × leverage
```

### Examples
| Leverage | Price Move | Leveraged ROI |
|----------|-----------|---------------|
| 10x | +2% | +20% |
| 10x | -3% | -30% |
| 5x | +4% | +20% |
| 1x | +20% | +20% |

## Testing

### New Test File
Created `test_stop_loss_priority.py` to verify:
- ✅ Stop loss price check has priority over emergency stops
- ✅ When stop loss is hit, returns 'stop_loss' reason
- ✅ Emergency stops act as failsafe when stop loss not hit
- ✅ Works correctly for all leverage levels (1x, 5x, 10x, 20x)
- ✅ Works correctly for both LONG and SHORT positions

### All Tests Passing
- ✅ `test_stop_loss_priority.py` - New comprehensive test
- ✅ `test_stalled_stop_loss.py` - Stalled position logic
- ✅ `test_comprehensive_leveraged_pnl.py` - Complete P&L fix validation
- ✅ `test_leveraged_pnl_fix.py` - Original leveraged P&L tests
- ✅ `test_emergency_stops.py` - Emergency stop protection
- ✅ `test_trade_simulation.py` - Complete trade lifecycle

### Updated Test File
Modified `test_trade_simulation.py`:
- Changed test prices to avoid triggering emergency stops in basic tests
- LONG: Changed from $96 to $98.5 (above emergency -20% ROI threshold)
- SHORT: Changed from $104 to $101.5 (above emergency -20% ROI threshold)

## Summary

This fix ensures that:
1. **Stop loss price is checked first** - When the stop loss price is hit, the correct reason is returned
2. **Emergency stops act as failsafe** - They only trigger when stop loss hasn't been hit but ROI is dangerously negative
3. **ROI calculations use leverage** - All thresholds (2% for stalled, 20% for profit taking, -20%/-35%/-50% for emergency) use leveraged ROI
4. **Consistent across all leverage levels** - Works correctly with 1x, 5x, 10x, 20x, etc.
5. **Protection against catastrophic losses** - Emergency stops prevent losses exceeding 50% ROI

## Files Modified
1. `position_manager.py` - Reordered stop loss checks in `should_close()` method
2. `test_trade_simulation.py` - Updated test prices to avoid emergency stops
3. `test_stop_loss_priority.py` - NEW: Comprehensive test for stop loss priority

## Verification
To verify the fix is working:
```bash
python test_stop_loss_priority.py
python test_stalled_stop_loss.py
python test_comprehensive_leveraged_pnl.py
python test_leveraged_pnl_fix.py
python test_emergency_stops.py
python test_trade_simulation.py
```

All tests should pass ✅

---

**Status**: ✅ FIXED AND TESTED

This fix ensures stop loss and ROI calculations work correctly with leverage, providing both accurate reporting and emergency protection.
