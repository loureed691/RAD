# Leveraged P&L Fix Summary

## Problem
The closing positions logic and orders were using **unleveraged P&L** (raw price movement) instead of **leveraged P&L** (actual ROI) in several places, leading to:
- Inconsistent logging (some logs showed ROI, others showed price movement)
- `scale_out_position` returning unleveraged P&L
- Advanced exit strategies receiving unleveraged P&L despite being labeled as leveraged

## Solution
Updated all position closing logic and logging to consistently use leveraged P&L (ROI):

### Files Changed
- `position_manager.py` - 5 fixes across different methods
- `LEVERAGED_PNL_FIX.md` - Updated documentation
- Added 2 new comprehensive test files

### Specific Fixes

#### 1. close_position Logging (Lines 1156, 1164)
**Before:**
```python
orders_logger.info(f"  P/L: {pnl:+.2%} ({format_pnl_usd(pnl_usd)})")
self.logger.info(f"...P/L: {pnl:.2%}, Reason: {reason}")
```

**After:**
```python
orders_logger.info(f"  P/L: {leveraged_pnl:+.2%} ({format_pnl_usd(pnl_usd)})")
self.logger.info(f"...P/L: {leveraged_pnl:.2%}, Reason: {reason}")
```

**Impact:** Logs now show actual ROI (e.g., 20%) instead of price movement (e.g., 2% with 10x leverage)

#### 2. scale_out_position Return Value (Lines 1813-1830)
**Before:**
```python
pnl = position.get_pnl(current_price)
return pnl
```

**After:**
```python
pnl = position.get_pnl(current_price)  # Base price change %
leveraged_pnl = position.get_leveraged_pnl(current_price)  # Actual ROI %
return leveraged_pnl
```

**Impact:** Partial position closes now return and log correct ROI

#### 3. Advanced Exit Strategy Input (Line 1348)
**Before:**
```python
current_pnl = position.get_pnl(current_price)
position_data = {
    'current_pnl_pct': current_pnl,  # Leveraged P&L (WRONG - was unleveraged)
}
```

**After:**
```python
current_pnl = position.get_pnl(current_price)  # Base price change %
leveraged_pnl = position.get_leveraged_pnl(current_price)  # Actual ROI %
position_data = {
    'current_pnl_pct': leveraged_pnl,  # Leveraged P&L (ROI)
}
```

**Impact:** Advanced exit strategies now make decisions based on actual ROI

#### 4. Partial Exit Logging (Line 1389)
**Before:**
```python
pnl = self.scale_out_position(symbol, amount_to_close, exit_reason)
self.logger.info(f"...P/L: {pnl:.2%}, Reason: {exit_reason}")
```

**After:**
```python
leveraged_pnl_result = self.scale_out_position(symbol, amount_to_close, exit_reason)
self.logger.info(f"...P/L: {leveraged_pnl_result:.2%}, Reason: {exit_reason}")
```

**Impact:** Consistent ROI reporting for partial exits

#### 5. Position Sync Logging (Line 890)
**Before:**
```python
pnl = position.get_pnl(current_price)
self.logger.info(f"...P/L: {pnl:.2%}, ...")
```

**After:**
```python
pnl = position.get_pnl(current_price)  # Base price change %
leveraged_pnl = position.get_leveraged_pnl(current_price)  # Actual ROI %
self.logger.info(f"...P/L: {leveraged_pnl:.2%}, ...")
```

**Impact:** Synced positions show correct ROI in logs

## Examples

### Example 1: 10x Leverage Position
- Entry: $100
- Current: $102 (2% price movement)
- **Before Fix:** Logs showed "P/L: 2.00%"
- **After Fix:** Logs show "P/L: 20.00%" (correct ROI)

### Example 2: scale_out_position
- 10x leverage, 2% price up
- **Before Fix:** Returned 0.02 (2%)
- **After Fix:** Returns 0.20 (20% ROI)

### Example 3: Advanced Exit Strategy
- 10x leverage, 2% price up
- **Before Fix:** Received current_pnl_pct=0.02
- **After Fix:** Receives current_pnl_pct=0.20

## Testing
All existing tests pass + 2 new comprehensive test suites:
- `test_scale_out_leveraged_pnl.py` - Validates scale_out returns leveraged P&L
- `test_comprehensive_leveraged_pnl.py` - Demonstrates all fixes end-to-end

## Verification Commands
```bash
# Run all leveraged P&L tests
python test_leveraged_pnl_fix.py
python test_scale_out_leveraged_pnl.py
python test_comprehensive_leveraged_pnl.py

# Run existing tests to ensure no regressions
python test_bot.py
python test_integration.py
```

## Key Takeaways
✅ All position closing logic now uses leveraged P&L (ROI)
✅ All logging now shows leveraged P&L (ROI) 
✅ scale_out_position returns leveraged P&L
✅ Advanced exit strategies receive leveraged P&L
✅ Consistent behavior across all leverage levels
✅ No changes to position closing decision logic (already fixed in commit 530027e)
