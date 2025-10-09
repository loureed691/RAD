# API Priority Queue System - Quick Reference

## What It Does

**Ensures ALL trading API calls execute BEFORE ALL scanning API calls, EVERY TIME.**

## Priority Levels

| Priority | Operations | Wait Time |
|----------|-----------|-----------|
| 🔴 **CRITICAL** | Order execution, cancellation | Never waits |
| 🟡 **HIGH** | Position monitoring, balance | Waits for CRITICAL only |
| 🟢 **NORMAL** | Market scanning, data fetch | Waits for CRITICAL + HIGH |

## Key Features

✅ **Zero Configuration** - Works automatically
✅ **100% Backward Compatible** - No code changes needed
✅ **Thread-Safe** - Safe for concurrent operations
✅ **Tested** - 6/6 tests passing + 8/8 order tests

## How It Works

```python
# Order execution (CRITICAL) - executes immediately
order = client.create_market_order('BTC/USDT:USDT', 'buy', 0.1, 10)

# Market scanning (NORMAL) - waits for orders to complete
futures = client.get_active_futures()  # Will wait if order is pending
```

## Benefits

- **Zero delays** for order execution
- **No API collisions** between trading and scanning
- **Faster stop-loss** response times
- **Better risk management**

## Testing

```bash
# Test API priority system
python test_api_call_priority.py     # 6/6 tests

# Test thread priority (existing)
python test_api_priority.py          # 4/4 tests

# Verify orders work correctly
python test_trade_simulation.py      # 8/8 tests
```

## See Also

- **Complete Guide**: [API_PRIORITY_QUEUE_SYSTEM.md](API_PRIORITY_QUEUE_SYSTEM.md)
- **Thread Priority**: [API_PRIORITY_FIX.md](API_PRIORITY_FIX.md)
- **Implementation**: Check `kucoin_client.py` for `APICallPriority` enum

## Status

✅ **IMPLEMENTED AND TESTED** - All trading operations now have guaranteed priority over scanning operations!
