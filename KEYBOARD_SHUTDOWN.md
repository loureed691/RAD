# Keyboard Shutdown Feature

## Overview

The trading bot now includes comprehensive keyboard interrupt (Ctrl+C) handling for safe and graceful shutdown.

## Features

### ✅ Graceful Shutdown
- Detects keyboard interrupt (Ctrl+C) or SIGTERM signals
- Stops the trading cycle gracefully after current iteration
- Completes any ongoing operations safely
- Saves ML model training data automatically
- Optionally closes all open positions
- No data loss or corruption

### 🔔 Clear User Feedback
When you press Ctrl+C, the bot displays:
```
============================================================
🛑 Shutdown signal received: SIGINT (Ctrl+C)
============================================================
⏳ Gracefully stopping bot...
   - Stopping trading cycle
   - Will complete current operations
   - Then proceed to shutdown
============================================================
```

### 💾 Automatic Data Preservation
On shutdown, the bot automatically:
1. Saves ML model data (training history, performance metrics)
2. Flushes all log buffers
3. Optionally closes positions (if configured)
4. Exits cleanly with no orphaned resources

## Usage

### Standard Shutdown (Recommended)
```bash
# While bot is running, press:
Ctrl+C

# Or send SIGINT from another terminal:
kill -SIGINT $(pgrep -f bot.py)
```

### Configuration Options

Add to your `.env` file:
```env
# Close all positions when shutting down (default: False)
CLOSE_POSITIONS_ON_SHUTDOWN=True
```

**Note**: By default, positions remain open when you stop the bot. This allows you to:
- Restart the bot without closing positions
- Manually manage positions
- Keep running positions monitored by exchange stop-loss orders

## Testing

Run the test suite to verify keyboard shutdown:
```bash
python3 test_keyboard_shutdown.py
```

Expected output:
```
============================================================
Keyboard Shutdown Tests
============================================================

Testing signal handler registration...
✓ Signal handlers registered successfully

Testing signal handler behavior...
✓ Bot not running initially
✓ Bot running state set
✓ Signal handler stopped bot

Testing KeyboardInterrupt handling...
✓ Shutdown called after KeyboardInterrupt

Testing shutdown method...
✓ ML model save called during shutdown

============================================================
Test Summary
============================================================
✓ PASS: Signal Handler Registration
✓ PASS: Signal Handler Behavior
✓ PASS: KeyboardInterrupt Handling
✓ PASS: Shutdown Method

Results: 4/4 tests passed
============================================================
```

## Demo

Run the interactive demo to see how keyboard shutdown works:
```bash
python3 demo_keyboard_shutdown.py

# Press Ctrl+C to trigger shutdown
```

The demo shows:
- Signal detection
- Graceful cycle termination
- Clear shutdown messages
- Data saving
- Clean exit

## Technical Details

### Signal Handlers
The bot registers handlers for:
- **SIGINT (2)**: Keyboard interrupt (Ctrl+C)
- **SIGTERM (15)**: Termination signal

Both trigger the same graceful shutdown process.

### Implementation
1. `signal_handler(sig, frame)`: Detects signals and sets `self.running = False`
2. Main loop in `run()`: Checks `self.running` and exits when False
3. `finally` block: Always calls `shutdown()` regardless of exit reason
4. `shutdown()`: Performs cleanup and saves data

### Code Changes
- **bot.py**: Enhanced `signal_handler()` and KeyboardInterrupt logging
- **test_keyboard_shutdown.py**: Comprehensive test suite (NEW)
- **demo_keyboard_shutdown.py**: Interactive demonstration (NEW)
- **QUICKREF.md**: Updated Emergency Stop documentation

## Safety Considerations

✅ **Safe Practices:**
- Use Ctrl+C for normal shutdown
- Configure `CLOSE_POSITIONS_ON_SHUTDOWN` based on your strategy
- Monitor logs during shutdown
- Verify positions are closed (if configured)

⚠️ **Avoid:**
- Force kill (`kill -9`) unless absolutely necessary
- Stopping bot during critical operations without understanding impact
- Assuming positions are always closed (check configuration)

## Troubleshooting

### Bot doesn't stop on Ctrl+C
- Check if bot is stuck in long operation
- Use `kill -SIGTERM <PID>` as alternative
- Last resort: `kill -9 <PID>` (may lose data)

### Positions not closing on shutdown
- Verify `CLOSE_POSITIONS_ON_SHUTDOWN=True` in `.env`
- Check logs for errors during position closure
- Manually close positions via exchange or script

### ML model not saving
- Check write permissions on models directory
- Verify disk space available
- Review error logs for details

## See Also

- **QUICKREF.md**: Emergency Stop section (detailed documentation)
- **bot.py**: Implementation details
- **test_keyboard_shutdown.py**: Test cases
- **demo_keyboard_shutdown.py**: Interactive demo
