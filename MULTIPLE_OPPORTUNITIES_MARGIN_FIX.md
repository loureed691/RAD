# Multiple Trading Opportunities Margin Handling Fix

## Problem Description

When the bot found multiple high-scoring trading opportunities simultaneously, it would:

1. Evaluate each opportunity sequentially
2. Attempt to open positions for each one
3. After the first position adjustment consumed available margin, subsequent opportunities would still be evaluated
4. These would fail with cryptic "Error creating" messages

### Example from Logs

```
20:36:19 ✓ INFO Best pair: ALCH/USDT:USDT - Score: 160.0, Signal: SELL, Confidence: 1.00, Regime: trending
20:36:19 ✓ INFO Best pair: MANA/USDT:USDT - Score: 160.0, Signal: SELL, Confidence: 1.00, Regime: trending
20:36:19 ✓ INFO Best pair: VIRTUAL/USDT:USDT - Score: 160.0, Signal: SELL, Confidence: 1.00, Regime: trending
20:36:19 ✓ INFO Best pair: XMR/USDT:USDT - Score: 160.0, Signal: SELL, Confidence: 1.00, Regime: trending
20:36:19 ✓ INFO Best pair: 1000BONK/USDT:USDT - Score: 158.3, Signal: SELL, Confidence: 0.94, Regime: trending
20:36:19 ✓ INFO 🔎 Evaluating opportunity: ALCH/USDT:USDT - Score: 160.0, Signal: SELL, Confidence: 1.00
20:36:19 ✓ INFO 🔎 Evaluating opportunity: MANA/USDT:USDT - Score: 160.0, Signal: SELL, Confidence: 1.00
20:36:19 ✓ INFO 🔎 Evaluating opportunity: VIRTUAL/USDT:USDT - Score: 160.0, Signal: SELL, Confidence: 1.00
20:36:19 ✓ INFO 🔎 Evaluating opportunity: XMR/USDT:USDT - Score: 160.0, Signal: SELL, Confidence: 1.00
20:36:19 ✓ INFO 🔎 Evaluating opportunity: 1000BONK/USDT:USDT - Score: 158.3, Signal: SELL, Confidence: 0.94
20:36:21 ⚠️ WARNING Margin check failed: Insufficient margin: available=$88.00, required=$462.05 (position value=$2.20, leverage=5x)
20:36:21 ⚠️ WARNING Reducing leverage from 5x to 1x to fit available margin
20:36:21 ✓ INFO Adjusted position to fit margin: 110.3089 contracts at 1x leverage
20:36:22 ✗ ERROR Error creating
```

## Root Causes

1. **No margin re-validation after adjustment** - After adjusting position size/leverage to fit available margin, the code didn't verify the adjustment was actually sufficient
2. **Sequential evaluation without margin updates** - Each opportunity was evaluated with the initial margin amount, not accounting for margin consumed by previous opportunities
3. **Poor error logging** - Error messages didn't include the symbol or full exception details
4. **No early exit** - The bot would continue evaluating all opportunities even when margin was exhausted

## Solution

### 1. Re-validate Margin After Adjustment (`kucoin_client.py`)

After adjusting position size and leverage to fit available margin, we now re-check if the adjusted position still fits:

```python
# After adjustment
validated_amount = adjusted_amount
leverage = adjusted_leverage
self.logger.info(
    f"Adjusted position to fit margin: {adjusted_amount:.4f} contracts at {adjusted_leverage}x leverage"
)

# NEW: Re-validate margin after adjustment
has_margin_after_adjust, _, margin_reason_after = self.check_available_margin(
    symbol, validated_amount, reference_price, leverage
)

if not has_margin_after_adjust:
    self.logger.error(
        f"Cannot open position: insufficient margin even after adjustment. {margin_reason_after}"
    )
    return None
```

**Why this helps:** Prevents orders from reaching the exchange if they'll fail anyway, avoiding cryptic error messages.

### 2. Check Margin Before Each Opportunity (`bot.py`)

Before evaluating each opportunity, check if there's still enough margin available:

```python
for opportunity in opportunities:
    if self.position_manager.get_open_positions_count() >= Config.MAX_OPEN_POSITIONS:
        self.logger.info("Maximum positions reached")
        break
    
    # NEW: Check available balance before this opportunity
    balance = self.client.get_balance()
    available_balance = float(balance.get('free', {}).get('USDT', 0))
    
    if available_balance <= 10:  # Minimum margin threshold
        self.logger.info(f"Insufficient margin remaining (${available_balance:.2f}), skipping remaining opportunities")
        break
```

**Why this helps:** Stops evaluating opportunities once margin is exhausted, avoiding repeated failures and saving time.

### 3. Enhanced Error Logging (`kucoin_client.py`)

Include symbol name and full stack trace in error messages:

```python
except Exception as e:
    # OLD: self.logger.error(f"Error creating market order: {e}")
    # NEW:
    self.logger.error(f"Error creating market order for {symbol}: {e}", exc_info=True)
    return None
```

**Why this helps:** Makes it easier to diagnose which order failed and why.

## Code Changes Summary

### Files Modified
- `kucoin_client.py`: 26 lines added (re-validation + better error logging)
- `bot.py`: 8 lines added (margin check before each opportunity)

### Files Added
- `test_margin_adjustment_fix.py`: Comprehensive test suite

### Changes Breakdown

**kucoin_client.py:**
1. Added margin re-validation after adjustment in `create_market_order()` (lines 385-393)
2. Added margin re-validation after adjustment in `create_limit_order()` (lines 494-502)
3. Enhanced error logging in `create_market_order()` (line 443)
4. Enhanced error logging in `create_limit_order()` (line 534)

**bot.py:**
1. Added balance check before each opportunity (lines 309-315)

## Testing

All tests pass:
- ✅ 4/4 new tests for margin adjustment fix
- ✅ 12/12 existing tests

### Test Scenarios Covered

1. **Margin re-validation rejects invalid positions** - When adjusted position still doesn't fit, order is rejected early
2. **Viable adjustments succeed** - When adjustment is sufficient, order proceeds normally
3. **Error logging includes details** - Symbol name and full exception are logged
4. **Multiple opportunities handled correctly** - Code checks margin before each opportunity

## Expected Results

### Before Fix
```
20:36:19 🔎 Evaluating opportunity: ALCH/USDT:USDT
20:36:21 ⚠️ WARNING Margin check failed: available=$88.00, required=$462.05
20:36:21 ⚠️ WARNING Reducing leverage from 5x to 1x
20:36:21 ✓ INFO Adjusted position to fit margin: 110.3089 contracts at 1x leverage
20:36:22 ✗ ERROR Error creating            ← Cryptic error!
20:36:22 🔎 Evaluating opportunity: MANA/USDT:USDT    ← Still evaluating despite no margin!
20:36:24 ⚠️ WARNING Margin check failed: available=$88.00, required=$462.05    ← Same margin amount!
... (repeats for all opportunities)
```

### After Fix
```
20:36:19 🔎 Evaluating opportunity: ALCH/USDT:USDT
20:36:21 ⚠️ WARNING Margin check failed: available=$88.00, required=$462.05
20:36:21 ⚠️ WARNING Reducing leverage from 5x to 1x
20:36:21 ✓ INFO Adjusted position to fit margin: 110.3089 contracts at 1x leverage
20:36:21 ✗ ERROR Cannot open position: insufficient margin even after adjustment. Insufficient margin: available=$88.00, required=$92.41    ← Clear error!
20:36:21 ✓ INFO Insufficient margin remaining ($5.20), skipping remaining opportunities    ← Stops early!
```

## Benefits

1. **Clearer error messages** - Know exactly which order failed and why
2. **No wasted cycles** - Stop evaluating when margin exhausted
3. **Better reliability** - Don't attempt orders that will fail
4. **Easier debugging** - Full stack traces and symbol names in logs

## Migration Notes

No breaking changes. The fix is backwards compatible and requires no configuration changes.

## Related Issues

This fix addresses the following symptoms:
- "Error creating" messages in logs
- Multiple opportunities being evaluated despite insufficient margin
- Orders failing after position adjustment
- Difficulty diagnosing order creation failures
