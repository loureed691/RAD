# Trading Fee Accounting

## Overview

This bot now includes **comprehensive trading fee accounting** in all profit/loss calculations. Previously, the bot was making decisions based on gross price movements without considering trading costs, which led to unprofitable trades being executed.

## The Problem

### Before Fix
The bot calculated P/L as pure price movement without deducting trading fees:

**Example:**
- Position: $5,000 with 10x leverage ($500 margin)
- Price move: +1% = $50 gross profit
- Gross ROI: 10% (due to 10x leverage)
- **Trading fees NOT deducted**: $6.00 (0.12% round-trip)
- **Reported P/L: 10%** ❌ WRONG
- **Actual P/L: 8.8%** ✓ CORRECT (after fees)

Many "profitable" trades were actually break-even or losing after fees.

## The Solution

### After Fix
All P/L calculations now include trading fees:

**Same Example:**
- Position: $5,000 with 10x leverage ($500 margin)
- Price move: +1% = $50 gross profit
- Entry fee: $5,000 × 0.06% = $3.00
- Exit fee: $5,000 × 0.06% = $3.00
- **Total fees: $6.00 (0.12% of position)**
- Net profit: $50 - $6 = $44
- **Net ROI: 8.8%** ✓ CORRECT

## Fee Structure

### KuCoin Futures Fees
```
Taker Fee (Market Orders): 0.06%
Maker Fee (Limit Orders):  0.02%
Round-Trip Cost:           0.12% (conservative estimate)
```

The bot uses **0.06% taker fee** as the default because:
1. Most orders are market orders for fast execution
2. Conservative estimate ensures we don't underestimate costs
3. Some positions may require market orders for exit

## Impact on Trading Decisions

### 1. Profit Taking
**Old behavior:** Take profit at 5% gross ROI  
**New behavior:** Take profit at 5% **net** ROI (after fees)

With 10x leverage:
- Old: Would close at 0.5% price move
- New: Would close at ~0.62% price move (to account for fees)

### 2. Breakeven Stop Loss
**Old behavior:** Move stop to entry price after 1.5% gross profit  
**New behavior:** Move stop to entry price after **0.74% gross profit** (0.62% net after fees)

This ensures true breakeven protection.

### 3. Trailing Stops
**Old behavior:** Tighten stops based on gross profit levels  
**New behavior:** Tighten stops based on **net profit** after fees

Example with 10% gross profit:
- Gross: 10.0%
- Fees: 1.2% (on 10x leverage)
- Net: 8.8% ← Used for trailing stop decisions

### 4. Take Profit Extensions
**Old behavior:** Extend TP based on gross profit thresholds  
**New behavior:** Extend TP based on **net profit** thresholds

This prevents over-optimistic TP extensions.

## Configuration

### Environment Variables
```bash
# Optional: Override default fees (defaults shown)
TAKER_FEE=0.0006    # 0.06%
MAKER_FEE=0.0002    # 0.02%
```

### Minimum Profit Threshold
The bot automatically sets `MIN_PROFIT_THRESHOLD` based on your balance:

```python
# Small accounts ($10-$100)
MIN_PROFIT_THRESHOLD = 0.92%  # 0.12% fees + 0.8% profit

# Medium accounts ($100-$1000)
MIN_PROFIT_THRESHOLD = 0.72%  # 0.12% fees + 0.6% profit

# Large accounts ($1000+)
MIN_PROFIT_THRESHOLD = 0.62%  # 0.12% fees + 0.5% profit
```

This ensures you only take profit when actually profitable after fees.

## Log Output

### Position Close Logs
```
============================================================
CLOSING POSITION: BTC/USDT:USDT
  Entry Price: $50,000.00
  Exit Price: $50,500.00
  Gross P/L: +10.00% ($+500.00)
  Trading Fees: 1.20% ($-60.00)
  Net P/L: +8.80% ($+440.00) ⚠️ AFTER FEES
  Duration: 45.3 minutes
============================================================
```

### Bot Main Log
```
📈 Position closed: BTC/USDT:USDT, Net P/L: +8.80% (after fees)
```

## Technical Details

### Fee Calculation
```python
# Round-trip fees (entry + exit)
total_fees = TRADING_FEE_RATE * 2  # 0.12%

# For leveraged positions
position_value = amount * entry_price
fees_usd = position_value * total_fees
leveraged_fee_impact = total_fees * leverage  # As % of margin
```

### Net P/L Calculation
```python
# Base price movement
pnl = (exit_price - entry_price) / entry_price

# Deduct fees
net_pnl = pnl - (TRADING_FEE_RATE * 2)

# Apply leverage for ROI
net_roi = net_pnl * leverage
```

## Testing

Run the fee accounting tests to verify everything works:

```bash
python test_fee_accounting.py
```

**Expected output:**
```
✓ Fee Calculation - PASSED
✓ P/L with Fees - PASSED
✓ Breakeven with Fees - PASSED
✓ Profit Thresholds - PASSED

All 4/4 tests passing
```

## FAQs

### Q: Will this reduce my profits?
**A:** No, it won't reduce your **actual** profits. It will make the bot more accurate by showing your **real** profits after costs. Previously, the bot was showing inflated numbers.

### Q: Why are some trades closing earlier now?
**A:** The bot now waits for true profitability before closing. A position that would have closed at "5% gross ROI" (which might be 3.8% net) will now wait until it reaches 5% **net** ROI for better returns.

### Q: Can I disable fee accounting?
**A:** No, it's always enabled because trading without accounting for costs leads to unprofitable strategies. However, fees are factored into all thresholds automatically.

### Q: What if I use limit orders (maker fees)?
**A:** The bot uses the conservative taker fee (0.06%) as default. If most of your orders are limit orders filled as maker (0.02%), you'll actually do slightly better than calculated.

### Q: How much do fees impact my returns?
**A:** With 10x leverage and 0.12% round-trip fees:
- 1% price move: 10% gross → 8.8% net (-1.2%)
- 2% price move: 20% gross → 18.8% net (-1.2%)
- 5% price move: 50% gross → 48.8% net (-1.2%)

The fee impact is constant at 1.2% of margin (with 10x leverage).

## Recommendations

1. **Monitor MIN_PROFIT_THRESHOLD** - Ensure it's set appropriately for your account size
2. **Check logs regularly** - Verify positions are closing at true profit
3. **Run tests** - Periodically run `test_fee_accounting.py` to verify behavior
4. **Compare results** - Track your actual exchange balance vs bot reports

## Support

If you notice discrepancies between bot-reported P/L and actual exchange balance:

1. Check the position logs for detailed fee breakdown
2. Verify fee configuration matches your exchange tier
3. Run test suite to ensure fee calculations are correct
4. Review MIN_PROFIT_THRESHOLD setting

## Summary

✅ **More accurate P/L reporting**  
✅ **True profitability analysis**  
✅ **Better trading decisions**  
✅ **No more hidden fee losses**  
✅ **Comprehensive test coverage**

The bot now operates with full awareness of trading costs, ensuring every trade is truly profitable after fees.
