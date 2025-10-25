# Unified Logging Feature

## Overview

All bot operations are now logged to a **single unified log file** (`logs/bot.log`) with clear component tags for better visibility. This makes it much easier to understand what's happening across all bot components in chronological order.

## What Changed

**Before:** The bot created 5 separate log files:
- `logs/bot.log` - Main bot operations
- `logs/positions.log` - Position tracking
- `logs/scanning.log` - Market scanning
- `logs/orders.log` - Order execution  
- `logs/strategy.log` - Strategy analysis

**Now:** Everything goes to **one log file** with clear component tags:
- `logs/bot.log` - **All bot operations with component tags**

## Configuration

The unified log is configured in `.env` (optional):

```bash
# Main log file (default: logs/bot.log)
LOG_FILE=logs/bot.log

# Log level for main operations (default: INFO)
LOG_LEVEL=INFO

# Log level for detailed component logs (default: DEBUG)
DETAILED_LOG_LEVEL=DEBUG
```

## Component Tags

All log entries are now tagged by component for easy identification:

- **[POSITION]** - Position lifecycle (open, update, close)
- **[SCANNING]** - Market scanning and opportunity detection
- **[ORDER]** - Order execution details (buy/sell/cancel)
- **[STRATEGY]** - Strategy analysis and recommendations
- **No tag** - General bot operations

## What is Logged

### 1. Position Events [POSITION]
- Position opened/closed
- Stop loss updates
- Take profit triggers
- Position size changes
- P&L calculations

### 2. Market Scanning [SCANNING]
- Markets being analyzed
- Opportunity detection
- Technical indicator values
- Signal generation

### 3. Order Execution [ORDER]
- Market orders (immediate execution)
- Limit orders (price-specific)
- Stop-limit orders (conditional)
- Order cancellations
- Fill prices and slippage
- Execution timestamps

### 4. Strategy Analysis [STRATEGY]
- Strategy recommendations
- Confidence scores
- Risk assessments
- Entry/exit signals

## Log Format

### Console Output (with colors)
```
14:53:03 [POSITION] ✓ INFO Position opened: BTC/USDT at $50,000
14:53:03 [SCANNING] ✓ INFO Scanning 100 markets for opportunities
14:53:03 [ORDER] ✓ INFO Market buy order executed: 0.001 BTC
14:53:03 [STRATEGY] ✓ INFO Strategy recommendation: LONG
```

Component tags are color-coded in the console:
- **[POSITION]** - Bright magenta
- **[SCANNING]** - Bright cyan
- **[ORDER]** - Bright yellow
- **[STRATEGY]** - Bright blue

### File Output (plain text)
```
2025-10-25 14:53:03 - [POSITION] INFO - Position opened: BTC/USDT at $50,000
2025-10-25 14:53:03 - [SCANNING] INFO - Scanning 100 markets for opportunities
2025-10-25 14:53:03 - [ORDER] INFO - Market buy order executed: 0.001 BTC
2025-10-25 14:53:03 - [STRATEGY] INFO - Strategy recommendation: LONG
```

## Benefits

1. **Single Source of Truth**: Everything in one chronological log
2. **Better Context**: See how different components interact in real-time
3. **Easier Debugging**: Follow the complete flow of events in one place
4. **Clear Labels**: Component tags make it easy to filter and find specific types of events
5. **Simplified Management**: Only one log file to monitor, rotate, and backup

## Accessing the Log

The unified log is located at `logs/bot.log`. You can:

- **View it directly**: `cat logs/bot.log`
- **Tail in real-time**: `tail -f logs/bot.log`
- **Filter by component**: 
  - `grep "\[POSITION\]" logs/bot.log` - Only position events
  - `grep "\[SCANNING\]" logs/bot.log` - Only scanning events
  - `grep "\[ORDER\]" logs/bot.log` - Only order events
  - `grep "\[STRATEGY\]" logs/bot.log` - Only strategy events
- **Filter by level**: 
  - `grep "ERROR" logs/bot.log` - Only errors
  - `grep "WARNING" logs/bot.log` - Only warnings
- **Combine filters**: 
  - `grep "\[ORDER\]" logs/bot.log | grep "ERROR"` - Only order errors

## Log Rotation

For production environments, consider setting up log rotation:

```bash
# Example logrotate configuration
/path/to/logs/bot.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 user group
}
```

## Example Log Sequence

Here's an example of how different components interact in the unified log:

```
2025-10-25 14:50:00 - INFO - Bot started, scanning markets...
2025-10-25 14:50:05 - [SCANNING] INFO - Found opportunity: BTC/USDT (confidence: 85%)
2025-10-25 14:50:06 - [STRATEGY] INFO - Strategy recommendation: LONG BTC/USDT
2025-10-25 14:50:07 - [ORDER] INFO - Placing market buy order for BTC/USDT
2025-10-25 14:50:08 - [ORDER] INFO - Order executed at $50,050 (slippage: 0.1%)
2025-10-25 14:50:09 - [POSITION] INFO - Position opened: BTC/USDT, size: 0.001, leverage: 10x
2025-10-25 14:51:00 - [POSITION] INFO - Updated stop loss: $49,500 -> $49,800
2025-10-25 14:55:00 - [POSITION] INFO - Take profit triggered at $51,000
2025-10-25 14:55:01 - [ORDER] INFO - Placing market sell order to close position
2025-10-25 14:55:02 - [ORDER] INFO - Order executed at $50,980
2025-10-25 14:55:03 - [POSITION] INFO - Position closed, P&L: +$93.00 (1.86%)
```

## Testing

To verify the unified logging is working correctly, run:

```bash
python test_unified_logging.py
```

This test will:
- Verify all components write to the same log file
- Check that component tags are present and correct
- Display sample log entries
- Confirm the unified logging system is working

## Migration from Old System

If you were using the old multi-file logging system:

1. **Old log files are no longer created**: The bot won't create separate `positions.log`, `scanning.log`, `orders.log`, or `strategy.log` files
2. **All logs are in bot.log**: Check `logs/bot.log` for everything
3. **No configuration changes needed**: The bot automatically uses the new unified system
4. **Component tags provide filtering**: Use `grep` to filter by component if you need specialized views

## Benefits Summary

✅ **One log file** instead of five separate files  
✅ **Better visibility** - see the complete picture in chronological order  
✅ **Clear component tags** - easily identify the source of each log entry  
✅ **Color-coded console output** - visually distinguish components at a glance  
✅ **Easier debugging** - follow the flow of events across all components  
✅ **Simpler management** - only one file to monitor, rotate, and backup

