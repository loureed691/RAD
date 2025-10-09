# Trading Bot Diagnostic Logging Guide

## Overview

The trading bot has been enhanced with comprehensive diagnostic logging to help identify why trades are not being executed. This guide explains how to interpret the logs and diagnose common issues.

## Enhanced Logging Features

### 1. Execute Trade Logging

Every trade attempt now logs detailed information at each validation step:

**Successful Validation Steps (✓):**
```
🔍 EVALUATING TRADE: BTC-USDT
   Signal: BUY, Confidence: 0.75
   Available balance: $1000.00 USDT
   ✓ Diversification check passed
   ✓ Position limit check passed (0/3)
   ✓ Trade validation passed (confidence: 0.75)
   Entry price: $43250.500000
   ✓ All validation checks passed - Attempting to open position
   Leverage: 10x, Position size: $450.00
   Stop loss: $41288.000000 (4.54%)
✅ TRADE EXECUTED - Successfully opened BUY position for BTC-USDT
```

**Rejected Trade Examples:**

```
❌ TRADE REJECTED - Invalid opportunity data: {'symbol': None, 'signal': 'BUY'}
   Symbol: None, Signal: BUY, Confidence: None
```

```
❌ TRADE REJECTED - Already have position for BTC-USDT
```

```
❌ TRADE REJECTED - No available balance
```

```
❌ TRADE REJECTED - Diversification check failed for BTC-USDT: Too many positions in crypto group (2/2)
   Current positions: ['BTC-USDT', 'ETH-USDT']
```

```
❌ TRADE REJECTED - Not opening position: Maximum positions reached (3)
   Current positions: 3/3
```

```
❌ TRADE REJECTED - Trade validation failed: Confidence too low (0.45 < 0.6)
   Signal: BUY, Confidence: 0.45
```

```
❌ TRADE REJECTED - Failed to fetch ticker for BTC-USDT
```

```
❌ TRADE REJECTED - Invalid entry price for BTC-USDT: 0
```

### 2. Scanner Logging

**Background Scanner:**
```
🔍 Background scanner thread started
   Scan interval: 60s
   Max workers: 20
🔍 [Background] Beginning market scans (position monitor has priority)
🔍 [Background] Scanning market for opportunities...
✅ [Background] Found 3 opportunities (scan took 12.3s)
   1. BTC-USDT: Signal=BUY, Confidence=0.82, Score=85.5
   2. ETH-USDT: Signal=SELL, Confidence=0.75, Score=78.3
   3. SOL-USDT: Signal=BUY, Confidence=0.68, Score=72.1
```

**No Opportunities:**
```
ℹ️  [Background] No opportunities found in this scan (scan took 15.2s)
```

**Market Scanner:**
```
📊 Returning top 3 trading opportunities:
   1. BTC-USDT: Score=85.5, Signal=BUY, Confidence=0.82, Regime=trending
   2. ETH-USDT: Score=78.3, Signal=SELL, Confidence=0.75, Regime=ranging
   3. SOL-USDT: Score=72.1, Signal=BUY, Confidence=0.68, Regime=trending
```

**No Opportunities Found:**
```
⚠️  No trading opportunities found in market scan
   This could mean:
   - All signals have low confidence (< threshold)
   - Market conditions are unfavorable
   - All pairs returned HOLD signals
```

### 3. Scan Processing Logging

```
📊 Processing 3 opportunities from background scanner (age: 45s)
   ✓ Opportunity data is fresh (age: 45s <= max: 120s)
🔎 Evaluating opportunity 1/3: BTC-USDT - Score: 85.5, Signal: BUY, Confidence: 0.82
... (execute_trade logs for each opportunity)
📊 SCAN SUMMARY: Attempted 3 trades, executed 1
```

**Stale Data:**
```
⚠️  OPPORTUNITIES REJECTED - Data is stale (age: 150s > max: 120s)
   Background scanner may be slow or encountering errors
```

### 4. Signal Generation Logging

Low confidence signals are logged with details:
```
Signal rejected: BTC-USDT - Confidence 0.45 < threshold 0.60
```

## Common Issues and How to Diagnose

### Issue 1: No Trades Being Executed

**Check the logs for:**

1. **Scanner finding no opportunities:**
   - Look for: `⚠️  No trading opportunities found in market scan`
   - **Cause:** Market conditions unfavorable, all signals have low confidence
   - **Solution:** Lower `min_confidence` threshold in signals.py or wait for better market conditions

2. **Low confidence signals:**
   - Look for: `❌ TRADE REJECTED - Trade validation failed: Confidence too low`
   - **Cause:** Signal confidence below minimum threshold (default 0.6)
   - **Solution:** Adjust signal generation parameters or confidence thresholds

3. **Maximum positions reached:**
   - Look for: `❌ TRADE REJECTED - Not opening position: Maximum positions reached`
   - **Cause:** Already at MAX_OPEN_POSITIONS limit
   - **Solution:** Increase MAX_OPEN_POSITIONS in config or close existing positions

4. **No balance:**
   - Look for: `❌ TRADE REJECTED - No available balance`
   - **Cause:** Insufficient USDT balance
   - **Solution:** Deposit more funds or close profitable positions

5. **Diversification limits:**
   - Look for: `❌ TRADE REJECTED - Diversification check failed`
   - **Cause:** Too many positions in same asset group
   - **Solution:** Wait for positions to close or adjust diversification limits

6. **Stale opportunity data:**
   - Look for: `⚠️  OPPORTUNITIES REJECTED - Data is stale`
   - **Cause:** Background scanner running slowly or errors
   - **Solution:** Check for scanner errors, reduce CHECK_INTERVAL, increase STALE_DATA_MULTIPLIER

### Issue 2: Scanner Finding No Opportunities

**Check the logs for:**

1. **All HOLD signals:**
   - Look in `logs/scanning.log` for signal details
   - **Cause:** No strong buy/sell signals in market
   - **Solution:** Adjust signal generation logic or wait for market movement

2. **Scanner errors:**
   - Look for: `❌ Error in background scanner`
   - **Cause:** API errors, network issues, or code bugs
   - **Solution:** Fix the error, check API credentials, network connectivity

### Issue 3: Trades Attempted But Not Executed

**Check the logs for:**

1. **Position manager failures:**
   - Look for: `❌ TRADE FAILED - Position manager failed to open position`
   - **Cause:** Exchange API errors, insufficient margin, invalid order parameters
   - **Solution:** Check `logs/positions.log` and `logs/orders.log` for details

2. **API errors:**
   - Look for: `❌ TRADE REJECTED - Failed to fetch ticker`
   - **Cause:** Exchange API issues
   - **Solution:** Check network, API rate limits, exchange status

## Log Files

The bot writes to multiple log files for different purposes:

1. **logs/bot.log** - Main bot operations and high-level events
2. **logs/positions.log** - Detailed position management (open, update, close)
3. **logs/scanning.log** - Market scanning and pair analysis details
4. **logs/orders.log** - Exchange order execution details
5. **logs/strategy.log** - Trading strategy analysis and signal reasons

## Configuration Parameters

Key parameters affecting trade execution:

```python
# Risk Management
MIN_CONFIDENCE = 0.6  # Minimum signal confidence (in risk_manager.validate_trade)
MAX_OPEN_POSITIONS = 3  # Maximum concurrent positions
MAX_POSITION_SIZE = 1000  # Maximum position size in USDT
RISK_PER_TRADE = 0.02  # Risk per trade (2%)

# Scanner Settings  
CHECK_INTERVAL = 60  # Seconds between scans
STALE_DATA_MULTIPLIER = 2  # Max age = CHECK_INTERVAL * STALE_DATA_MULTIPLIER
MAX_WORKERS = 20  # Parallel workers for scanning

# Signal Generation
min_confidence (in signals.py):
- 0.52 for trending markets
- 0.58 for ranging markets
- adaptive_threshold from ML model
```

## Troubleshooting Steps

1. **Start the bot and wait for one full cycle (60 seconds)**
2. **Check logs/bot.log for high-level status:**
   - Are opportunities being found?
   - Are trades being attempted?
   - What's the scan summary showing?

3. **Check logs/scanning.log for scanner details:**
   - How many pairs are being scanned?
   - What signals are being generated?
   - What are the confidence levels?

4. **If trades are attempted but rejected, check the rejection reason:**
   - Follow the specific guidance for that rejection type above

5. **If no opportunities are found:**
   - Check logs/strategy.log for signal analysis
   - Verify market conditions are suitable for trading
   - Consider adjusting confidence thresholds

## Quick Diagnostic Commands

```bash
# View latest bot log
tail -f logs/bot.log

# Search for trade rejections
grep "TRADE REJECTED" logs/bot.log

# Search for successful trades
grep "TRADE EXECUTED" logs/bot.log

# View scan summaries
grep "SCAN SUMMARY" logs/bot.log

# Check for opportunities found
grep "Found.*opportunities" logs/bot.log

# Check for errors
grep "Error\|ERROR" logs/bot.log

# View all rejection reasons
grep "❌" logs/bot.log

# View all successful validations
grep "✓" logs/bot.log
```

## Summary

The enhanced logging provides complete visibility into:
- ✅ Why trades are being executed
- ❌ Why trades are being rejected
- 📊 What opportunities are being found
- 🔍 How the scanner is performing
- ⚠️  What errors are occurring

Use the rejection messages and this guide to quickly identify and resolve trading issues.
