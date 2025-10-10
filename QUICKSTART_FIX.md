# Quick Start Guide - Bot Not Trading Fix

## What Was Fixed

Your bot stopped trading because confidence thresholds were too high (55-60%). Most signals were being rejected as "confidence too low."

**Fix Applied**: Reduced thresholds to 50-55% so the bot can trade in normal market conditions.

## Quick Verification (2 minutes)

### 1. Run Diagnostics
```bash
python diagnose_bot.py
```
Expected: "No critical issues found" ✅

### 2. Run Tests
```bash
python test_bot_not_trading_fix.py
```
Expected: "ALL TESTS PASSED" ✅

### 3. Check What Changed
```bash
git diff HEAD~3 config.py signals.py risk_manager.py
```

## Start Trading

### Option A: Use Default Settings (Recommended)
Just start the bot - no configuration needed:
```bash
python bot.py
```

### Option B: Customize Thresholds
Edit `.env` file:
```env
# Trade more (45-50%)
MIN_SIGNAL_CONFIDENCE=0.45
MIN_TRADE_CONFIDENCE=0.50

# Default (50-55%) - balanced
MIN_SIGNAL_CONFIDENCE=0.50
MIN_TRADE_CONFIDENCE=0.55

# Trade less (55-60%) - conservative
MIN_SIGNAL_CONFIDENCE=0.55
MIN_TRADE_CONFIDENCE=0.60
```

Then start:
```bash
python bot.py
```

## Monitor Activity

### Watch Logs in Real-Time
```bash
tail -f logs/bot.log logs/scanning.log
```

### Look For These Messages
✅ **Good Signs**:
- `🔎 Evaluating opportunity: BTCUSDT - Confidence: 52%` - Finding signals
- `✅ Trade executed for BTCUSDT` - Trading is working!
- `📈 Position closed: BTCUSDT, P/L: +2.34%` - Successful trade

❌ **Problems**:
- `❌ Trade rejected for BTCUSDT: Confidence too low` - Threshold still too high
- `⚠️ Opportunities are stale` - Scan interval too high
- `💰 No available balance` - Need to fund account

## Troubleshooting

### Still No Trades After 1 Hour?

**Check 1: Are signals being generated?**
```bash
grep "Evaluating opportunity" logs/bot.log
```
If no results: Market is quiet, wait longer or lower CHECK_INTERVAL

**Check 2: Why are they rejected?**
```bash
grep "Trade rejected" logs/bot.log | tail -10
```

Common rejections and fixes:
- "Confidence too low" → Lower MIN_TRADE_CONFIDENCE
- "Maximum positions reached" → Increase MAX_OPEN_POSITIONS
- "Insufficient balance" → Add funds or reduce position size

**Check 3: API connectivity**
```bash
python diagnose_bot.py
```
Verify API connection is working

### Too Many Trades?

Raise thresholds in `.env`:
```env
MIN_SIGNAL_CONFIDENCE=0.55
MIN_TRADE_CONFIDENCE=0.60
```

### Adjust Other Settings

```env
# Scan more frequently (faster trading)
CHECK_INTERVAL=30  # 30 seconds instead of 60

# Allow more positions
MAX_OPEN_POSITIONS=5  # Instead of 3

# More lenient stale data
STALE_DATA_MULTIPLIER=4  # Instead of 3
```

## Key Changes Summary

| Setting | Before | After | Impact |
|---------|--------|-------|--------|
| MIN_SIGNAL_CONFIDENCE | N/A (hardcoded 55%) | 50% | Configurable, 5% lower |
| MIN_TRADE_CONFIDENCE | N/A (hardcoded 60%) | 55% | Configurable, 5% lower |
| STALE_DATA_MULTIPLIER | 2x | 3x | 50% more tolerance |
| Signal acceptance rate | ~50% | ~70% | +20% more trades |

## Expected Timeline

- **0-5 min**: Bot starts, begins scanning
- **5-15 min**: First opportunities found
- **15-60 min**: First trade executed (market dependent)
- **1-2 hours**: Multiple trades if market is active

## Need Help?

1. Run diagnostics: `python diagnose_bot.py`
2. Check logs: `tail -f logs/bot.log`
3. Review rejection reasons in logs
4. Adjust thresholds in `.env`
5. See `SOLUTION_SUMMARY.md` for detailed explanation

## Rollback

If you need to undo changes:
```bash
git checkout main config.py signals.py risk_manager.py bot.py
```

Or set high thresholds in `.env`:
```env
MIN_SIGNAL_CONFIDENCE=0.55
MIN_TRADE_CONFIDENCE=0.60
```

---

**Your bot should now be trading! 🚀**

Monitor logs for the next hour to verify activity. Adjust thresholds as needed for your risk tolerance.
