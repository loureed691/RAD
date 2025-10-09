# Trading Bot Diagnostic Logging - Quick Start

## Problem
Bot not trading? Can't figure out why?

## Solution
We've added comprehensive diagnostic logging that shows exactly why trades are or aren't executing.

## Quick Diagnosis (30 seconds)

### Step 1: Start the bot
```bash
python bot.py
```

### Step 2: Check the logs
```bash
# In another terminal
tail -f logs/bot.log
```

### Step 3: Look for these messages

**✅ Trade Executed:**
```
✅ TRADE EXECUTED - Successfully opened BUY position for BTC-USDT
```

**❌ Trade Rejected (with reason):**
```
❌ TRADE REJECTED - Trade validation failed: Confidence too low (0.45 < 0.6)
❌ TRADE REJECTED - Not opening position: Maximum positions reached (3)
❌ TRADE REJECTED - No available balance
❌ TRADE REJECTED - Diversification check failed for BTC-USDT: Too many positions in crypto group (2/2)
```

**📊 Scan Summary:**
```
📊 SCAN SUMMARY: Attempted 3 trades, executed 1
```

## Common Issues

### 1. No Opportunities Found
**Message:** `⚠️  No trading opportunities found in market scan`

**Fix:** Lower confidence threshold or wait for better market conditions

### 2. Low Confidence Signals  
**Message:** `❌ TRADE REJECTED - Confidence too low (0.45 < 0.6)`

**Fix:** Adjust `min_confidence` in `risk_manager.py` line 393, or wait for stronger signals

### 3. Maximum Positions
**Message:** `❌ TRADE REJECTED - Maximum positions reached (3)`

**Fix:** Increase `MAX_OPEN_POSITIONS` in `.env` or close existing positions

### 4. No Balance
**Message:** `❌ TRADE REJECTED - No available balance`

**Fix:** Deposit more funds or close profitable positions

## Detailed Documentation

- **BOT_NOT_TRADING_SOLUTION.md** - Complete solution guide with all scenarios
- **DIAGNOSTIC_LOGGING_GUIDE.md** - Full logging reference and troubleshooting
- **demo_diagnostic_logging.py** - Interactive demo showing logging in action

## Test the Logging

```bash
python demo_diagnostic_logging.py
```

This shows how the logging works in 5 different scenarios.

## Grep Commands for Quick Diagnosis

```bash
# Why are trades being rejected?
grep "TRADE REJECTED" logs/bot.log

# Are opportunities being found?
grep "Found.*opportunities" logs/bot.log

# What's the success rate?
grep "SCAN SUMMARY" logs/bot.log

# Any errors?
grep "ERROR" logs/bot.log
```

## What Changed

Every validation step now logs clearly:
- ✓ Shows when checks pass
- ❌ Shows exactly why checks fail (with values and thresholds)
- 📊 Shows summaries of trade attempts vs executions
- 🔍 Shows what opportunities the scanner found

**Before:** "Trade not valid" 😕
**After:** "❌ TRADE REJECTED - Trade validation failed: Confidence too low (0.45 < 0.6)" 💡

## Files Modified

- `bot.py` - Enhanced trade execution and scanning logging
- `risk_manager.py` - Added validation logging
- `market_scanner.py` - Enhanced opportunity reporting
- `signals.py` - Added confidence rejection logging

## Need Help?

1. Run the demo: `python demo_diagnostic_logging.py`
2. Check the logs: `tail -f logs/bot.log`
3. Review: **BOT_NOT_TRADING_SOLUTION.md**
4. Share the rejection messages for specific help

The bot now tells you exactly why it's not trading! 🎯
