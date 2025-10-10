# Position Closing Bug Fix - Leveraged P&L

## Issue Report
User reported that positions were not closing at expected profit/loss levels:
- Positions with >20% profit weren't closing
- Positions with >30% loss weren't closing properly

## Root Cause Analysis

The `should_close()` method in `position_manager.py` was using **unleveraged P&L** (raw price movement percentage) to check profit/loss thresholds, instead of **leveraged ROI** (return on investment).

### The Problem

When trading with leverage, there's a critical difference:
- **Unleveraged P&L**: The raw price movement (e.g., price moved from $100 to $102 = 2%)
- **Leveraged ROI**: The actual return on your investment (e.g., 2% price × 10x leverage = 20% ROI)

The code was checking: `if current_pnl >= 0.20` expecting to trigger at 20% profit.

But `current_pnl` was the **unleveraged** value, so:
- With 10x leverage: Needed 20% **price movement** to trigger (which is 200% ROI!)
- User expected: 20% **ROI** (which is only 2% price movement with 10x leverage)

### Real-World Example

**Scenario**: Position with 10x leverage
- Entry price: $100
- Price moves to $102 (2% price movement)
- Actual ROI: 2% × 10x = **20% profit**

**Before Fix:**
- Code checked: `if 0.02 >= 0.20` → False
- Position stayed open despite user having 20% profit
- Would need price to move to $120 (20% movement = 200% ROI!) to close

**After Fix:**
- Code checks: `if 0.20 >= 0.20` → True  
- Position closes at 20% ROI as expected ✅

## The Fix

### Changed in `position_manager.py` (line 597)

**Before:**
```python
current_pnl = self.get_pnl(current_price)  # Unleveraged price movement
```

**After:**
```python
current_pnl = self.get_leveraged_pnl(current_price)  # Leveraged ROI
```

### Also Updated Stalled Position Checks (lines 666, 683)

**IMPORTANT NOTE:** This section describes a fix from commit 530027e that had a bug which was corrected in this PR.

**Original (before 530027e):**
```python
if time_in_trade >= 4.0 and current_pnl < 0.02:  # 4 hours with < 2% profit
```

**After 530027e (BUG - double leveraging):**
```python
if time_in_trade >= 4.0 and current_pnl < 0.02 * self.leverage:  # 4 hours with < 2% ROI
```
This was WRONG because `current_pnl` was already leveraged ROI from `get_leveraged_pnl()`, so multiplying by leverage again created a threshold of 20% for 10x leverage instead of 2%.

**After this PR (FIXED):**
```python
# current_pnl is already leveraged ROI, so check against 2% ROI directly
if time_in_trade >= 4.0 and current_pnl < 0.02:  # 4 hours with < 2% ROI
```
Now correctly checks for 2% ROI regardless of leverage level.

## Impact

This fix ensures positions close at the **correct ROI levels** regardless of leverage:

| Leverage | Price Movement | ROI | Before Fix | After Fix |
|----------|---------------|-----|------------|-----------|
| 10x | 2% up | 20% | ❌ Stayed open | ✅ Closes at 20% |
| 10x | 3% down | -30% | ❌ May not hit stop | ✅ Hits stop loss |
| 5x | 4% up | 20% | ❌ Stayed open | ✅ Closes at 20% |
| 1x | 20% up | 20% | ✅ Closed | ✅ Closes at 20% |

## Profit Taking Thresholds Now Work Correctly

All profit-taking thresholds now use leveraged ROI:
- ✅ 20% ROI → Exceptional profit, always close
- ✅ 15% ROI → High profit, close if TP far away  
- ✅ 10% ROI → Good profit, close if TP far away
- ✅ 8% ROI → Moderate profit, close if TP far away
- ✅ 5% ROI → Take profit if TP far away

## Stop Loss Behavior

Stop loss continues to work correctly as it's **price-based**, not ROI-based:
- Stop loss set at X% below entry price (e.g., 3% below)
- With 10x leverage, 3% price move = 30% ROI loss
- Position closes when price hits stop loss level ✅

## Testing

Created comprehensive test suite: `test_leveraged_pnl_fix.py`

**All tests pass:**
1. ✅ 10x leverage, 2% price up → 20% ROI → closes
2. ✅ 10x leverage, 3% price down → 30% loss → hits stop loss
3. ✅ 5x leverage, 4% price up → 20% ROI → closes
4. ✅ 1x leverage, 20% price up → 20% ROI → closes
5. ✅ SHORT 10x leverage, 2% price down → 20% ROI → closes

**Total test coverage: 22/22 tests passing (100%)**
- Core bot tests: 12/12 ✅
- Bug fix tests: 5/5 ✅
- Integration tests: 4/4 ✅
- Leveraged P&L tests: 5/5 ✅ (NEW)

## Verification

To verify the fix is working in production:
1. Check position logs for closing reasons
2. Positions should close at expected ROI levels
3. "take_profit_20pct_exceptional" should trigger at 20% ROI, not 200%
4. Stop loss should trigger at expected loss levels (e.g., 30% with 10x leverage)

## Files Modified
- `position_manager.py` - Updated `should_close()` method, `close_position()` logging, `scale_out_position()` calculation and return value, `update_positions()` advanced exit strategy input, and `sync_positions_from_exchange()` logging
- `test_leveraged_pnl_fix.py` - New comprehensive test suite
- `test_scale_out_leveraged_pnl.py` - Test for scale_out_position leveraged P&L
- `test_comprehensive_leveraged_pnl.py` - Comprehensive test demonstrating all fixes

## Commits
- Hash: 530027e - Message: "Fix position closing: use leveraged P&L for ROI thresholds"
- Hash: 93a5fd4 - Message: "Fix leveraged P&L in close_position, scale_out_position, and logging"

## Additional Fixes (93a5fd4)

Beyond the initial `should_close()` fix, the following issues were also corrected:

### 1. **close_position logging** (lines 1156, 1164)
- **Before:** Logged unleveraged P&L in orders logger and main logger
- **After:** Logs leveraged P&L (ROI) for accurate reporting
- **Impact:** Users now see correct ROI percentages in logs

### 2. **scale_out_position return value** (lines 1813-1830)
- **Before:** Calculated and returned only unleveraged P&L
- **After:** Calculates and returns leveraged P&L (ROI)
- **Impact:** Partial position closes now report correct ROI

### 3. **Advanced exit strategy input** (line 1348)
- **Before:** Passed unleveraged P&L despite comment saying "Leveraged P&L"
- **After:** Correctly passes leveraged P&L to advanced exit strategy
- **Impact:** Exit strategies now make decisions based on actual ROI

### 4. **Partial exit logging** (line 1389)
- **Before:** Logged unleveraged P&L from scale_out_position
- **After:** Logs leveraged P&L returned from scale_out_position
- **Impact:** Consistent reporting of ROI for partial exits

### 5. **Position sync logging** (line 890)
- **Before:** Logged unleveraged P&L for synced positions
- **After:** Logs leveraged P&L for synced positions
- **Impact:** Synced position logs now show accurate ROI

---

**Status:** ✅ FIXED AND TESTED

This critical bug fix ensures positions close at the correct profit/loss levels that users expect when trading with leverage. All position closing logic, orders, and logging now use correctly calculated leveraged P&L (ROI) instead of unleveraged price movement.
