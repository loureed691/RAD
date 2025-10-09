# WebSocket Close Warning Fix

## Problem
The WebSocket connection was frequently logging warning messages:
```
22:40:56 ⚠️ WARNING WebSocket connection closed: 1000 - Bye
```

This was happening "too much" and creating unnecessary noise in the logs.

## Root Cause
- WebSocket close code **1000** is a **normal/graceful close**, not an error
- The code was logging ALL disconnections at WARNING level
- Normal reconnections during operation were spamming the warning logs

## Solution
Modified the `_on_close()` method in `kucoin_websocket.py` to log at appropriate levels based on the WebSocket close code:

| Close Code | Meaning | Log Level | Impact |
|------------|---------|-----------|---------|
| 1000 | Normal close (graceful) | **DEBUG** | Not shown in production (INFO level) |
| 1001 | Going away | **INFO** | Shown but not as warning |
| None | Unknown | **INFO** | Shown but not as warning |
| Other (1006, etc.) | Errors | **WARNING** | Shown as warning (correct behavior) |

## Changes Made
**File:** `kucoin_websocket.py`

**Before:**
```python
def _on_close(self, ws, close_status_code, close_msg):
    """Handle WebSocket connection closed"""
    self.connected = False
    self.logger.warning(f"WebSocket connection closed: {close_status_code} - {close_msg}")
    # ... reconnection logic
```

**After:**
```python
def _on_close(self, ws, close_status_code, close_msg):
    """Handle WebSocket connection closed"""
    self.connected = False
    
    # Log at appropriate level based on close code
    if close_status_code == 1000:
        # Normal close - log at DEBUG level to reduce noise
        self.logger.debug(f"WebSocket connection closed normally: {close_status_code} - {close_msg}")
    elif close_status_code in (1001, None):
        # Going away or unknown - log at INFO level
        self.logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
    else:
        # Abnormal close - log at WARNING level
        self.logger.warning(f"WebSocket connection closed unexpectedly: {close_status_code} - {close_msg}")
    
    # ... reconnection logic (unchanged)
```

## Benefits
✅ **Cleaner logs**: Normal WebSocket disconnections no longer spam WARNING logs  
✅ **Better signal-to-noise**: Real errors still show as warnings  
✅ **No behavior change**: Reconnection logic works exactly as before  
✅ **Debug-friendly**: Set `LOG_LEVEL=DEBUG` to see all connection events when troubleshooting  
✅ **Standards-compliant**: Follows WebSocket RFC close code semantics  

## Testing
Verified with custom tests that:
- Code 1000 logs at DEBUG level ✓
- Code 1001 logs at INFO level ✓
- Code 1006 logs at WARNING level ✓
- Reconnection logic still works ✓
- No syntax errors ✓

## Production Impact
With default production log level (INFO):
- **Before:** Constant warning messages cluttering logs
- **After:** Clean logs, only actual errors show warnings

To see normal disconnections when troubleshooting, set in `.env`:
```bash
LOG_LEVEL=DEBUG
```

## Commit
- **Branch:** `copilot/fix-websocket-connection-issue`
- **Commit:** `ffb0a82` - Fix WebSocket warning for normal close (code 1000)
- **Files changed:** `kucoin_websocket.py` (15 insertions, 1 deletion)

---

**Status:** ✅ Complete and tested  
**Impact:** Minimal, surgical change to logging only  
**Risk:** None - no functional changes to WebSocket behavior
