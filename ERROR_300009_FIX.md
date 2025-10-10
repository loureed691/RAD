# Fix for Error 300009: "No open positions to close"

## Problem Statement

The trading bot was encountering the following error when trying to close positions:

```
14:47:59 ✗ ERROR Invalid order parameters for create_market_order(ENS/USDT:USDT, sell): 
kucoinfutures {"msg":"No open positions to close.","code":"300009"}
```

This error occurs when the bot attempts to close a position that doesn't exist on the exchange (either because it was already closed, never opened, or there's a sync issue between the local position tracking and the exchange).

## Root Cause

The error code `300009` from KuCoin Futures means "No open positions to close". This was being caught by the error handling in `_handle_api_error()` and treated as a hard failure, causing:

1. Error logging
2. Retries (which would also fail)
3. Eventually returning `None`, which propagates the failure up the call stack

## Solution

The fix recognizes that if a position doesn't exist to close, that's actually a **success state** - the desired end result (position closed) has already been achieved. 

### Changes Made

**File: `kucoin_client.py`**

Added special handling for error code 300009 in two exception handlers:

1. **In `ccxt.InvalidOrder` exception handler** (line 176-184):
```python
except ccxt.InvalidOrder as e:
    # Check for "No open positions to close" error (code 300009)
    # This is actually a success case for reduce_only orders
    if '300009' in str(e) or 'no open positions to close' in str(e).lower():
        self.logger.info(
            f"Position already closed for {operation_name} (code 300009). "
            f"Treating as success."
        )
        return {'status': 'closed', 'info': 'Position already closed'}
```

2. **In `ccxt.ExchangeError` exception handler** (line 227-233):
```python
# 300009 - "No open positions to close" - treat as success for reduce_only orders
if '300009' in str(e) or 'no open positions to close' in error_str:
    self.logger.info(
        f"Position already closed for {operation_name} (code 300009). "
        f"Treating as success."
    )
    return {'status': 'closed', 'info': 'Position already closed'}
```

**File: `test_enhanced_trading_methods.py`**

Added comprehensive test case `test_error_300009_handling()` to verify the fix works correctly.

**File: `test_error_300009_fix.py`** (New)

Created integration test to demonstrate the fix in action.

## Behavior Changes

### Before Fix
```
14:47:59 ✗ ERROR Invalid order parameters for create_market_order(ENS/USDT:USDT, sell): 
kucoinfutures {"msg":"No open positions to close.","code":"300009"}
```
- Logged as ERROR
- Returned `None` (failure)
- Caused unnecessary retries
- Could cause position tracking to become out of sync

### After Fix
```
14:47:59 ✓ INFO Position already closed for create_market_order(ENS/USDT:USDT, sell) 
(code 300009). Treating as success.
```
- Logged as INFO (not an error)
- Returns `{'status': 'closed', 'info': 'Position already closed'}` (success)
- No retries needed
- Position tracking remains consistent

## Testing

All tests pass successfully:

1. **test_enhanced_trading_methods.py**: 12/12 tests passed ✅
   - Including new `test_error_300009_handling` test
   
2. **test_position_closing_retry.py**: 5/5 tests passed ✅
   - Verifies position closing retry logic still works

3. **test_scale_out_leveraged_pnl.py**: All tests passed ✅
   - Verifies P&L calculations remain correct

4. **test_error_300009_fix.py**: 2/2 tests passed ✅
   - Integration test verifying the exact scenario from problem statement

## Impact

This is a **minimal, surgical fix** that:
- ✅ Eliminates false error messages
- ✅ Improves system reliability by handling an edge case gracefully
- ✅ Reduces unnecessary API calls (retries)
- ✅ Makes position tracking more robust
- ✅ Does not change any other behavior
- ✅ Backward compatible

## Use Cases Handled

1. **Already closed position**: Position was closed by another process/manual intervention
2. **Never opened position**: Order failed to open but local tracking recorded it
3. **Sync issues**: Temporary desync between local state and exchange state
4. **Manual interventions**: User manually closed position via exchange UI

## Related Error Codes

This fix specifically handles error code `300009`. Other KuCoin error codes continue to be handled as before:
- `330008`: Insufficient margin
- `330006`: Margin mode issues  
- `400xxx`: General bad request errors
- etc.
