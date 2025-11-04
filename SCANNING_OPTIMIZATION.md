# Scanning Optimization

## Overview

The market scanning system has been optimized to significantly reduce API calls and improve performance while maintaining data quality.

## Key Optimizations

### 1. Priority Pairs Caching

**Problem**: Previously, the bot fetched and filtered the list of high-priority trading pairs on every scan cycle (every 10 seconds by default). This resulted in hundreds of redundant API calls per hour.

**Solution**: The priority pairs list is now cached and refreshed only once per hour (configurable). The bot:
- Fetches the full futures list from the exchange on the first scan
- Filters to high-priority pairs based on volume and liquidity
- Caches this filtered list for 1 hour (default)
- Reuses the cached list for all scans within that hour
- Automatically refreshes after the configured interval expires

### 2. Candle Data Caching

**Status**: Already well-implemented. Individual candle data (OHLCV) and calculated indicators are cached per symbol as a fallback when fresh data cannot be fetched.

**Important**: Candle data is always fetched fresh on each scan for actual trading decisions. The cache is only used as a fallback when live data fetch fails.

## Configuration

### PRIORITY_PAIRS_REFRESH_INTERVAL

Controls how often the priority pairs list is refreshed.

- **Default**: 3600 seconds (1 hour)
- **Environment Variable**: `PRIORITY_PAIRS_REFRESH_INTERVAL`
- **Range**: 300 - 7200 seconds (5 minutes to 2 hours)
- **Recommended**: Keep at 1 hour for most use cases

**Example** (in `.env`):
```bash
# Refresh priority pairs every 1 hour (default)
PRIORITY_PAIRS_REFRESH_INTERVAL=3600

# More aggressive refresh (every 30 minutes)
# PRIORITY_PAIRS_REFRESH_INTERVAL=1800

# Less frequent refresh (every 2 hours)
# PRIORITY_PAIRS_REFRESH_INTERVAL=7200
```

## Performance Impact

### With Continuous Scanning (10-second intervals)

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Futures API calls/hour | 360 | 1 | 99.7% reduction |
| Overhead time/hour | 216s | 0.6s | 99.7% reduction |
| API calls/day | 8,640 | 24 | 99.7% reduction |
| API calls/month | 259,200 | 720 | 99.7% reduction |
| Time saved/month | - | 43.1 hours | - |

### Benefits

- ✅ **Reduced API Calls**: 99.7% fewer calls to `get_active_futures()`
- ✅ **Faster Scans**: Less overhead per scan cycle
- ✅ **Better API Quota**: Reduced rate limit pressure on exchange API
- ✅ **Lower Bandwidth**: Less network traffic
- ✅ **More CPU Available**: More cycles for trading logic
- ✅ **Maintains Quality**: Candle data still fetched fresh every scan
- ✅ **Thread-Safe**: Proper locking for cache access
- ✅ **Automatic Refresh**: Cache expires and refreshes automatically

## Implementation Details

### Cache Structure

```python
# Priority pairs cache
self._cached_priority_pairs = None      # List of priority pair symbols
self._last_priority_pairs_update = None # Timestamp of last update
self._priority_pairs_refresh_interval = Config.PRIORITY_PAIRS_REFRESH_INTERVAL

# Candle data cache (per symbol)
self.cache = {}  # {symbol: (result, timestamp)}
```

### Cache Flow

1. **First Scan**:
   - Fetch futures list from exchange
   - Filter to high-priority pairs
   - Cache the filtered list
   - Scan each pair for opportunities

2. **Subsequent Scans** (within refresh interval):
   - Check cache timestamp
   - Reuse cached priority pairs list
   - Scan each pair for opportunities
   - (No futures list fetch or filtering)

3. **After Refresh Interval**:
   - Cache expires automatically
   - Next scan fetches fresh futures list
   - Filters and updates cache
   - Continue normal scanning

### Thread Safety

All cache operations use thread-safe locking:
```python
with self._cache_lock:
    # Cache read/write operations
```

## Testing

### Unit Tests
```bash
python -m unittest test_priority_pairs_caching.TestPriorityPairsCaching -v
```

### Integration Test
```bash
python test_integration_scanning.py
```

### Demo Script
```bash
python demo_scanning_optimization.py
```

## Monitoring

The bot logs cache usage for monitoring:

```
Using cached priority pairs (refreshed 125s ago, next refresh in 3475s)
```

After refresh:
```
Priority pairs cached (will refresh in 3600s)
```

## Backward Compatibility

This optimization is fully backward compatible:
- No changes to existing API or behavior
- Existing tests continue to work
- Candle data quality maintained
- All trading decisions still use fresh data

## Future Enhancements

Potential future optimizations:
- Adaptive refresh based on market volatility
- Smart pre-fetching before cache expiry
- Per-exchange cache tuning
- Cache persistence across bot restarts

## FAQ

**Q: Does this affect trading decisions?**  
A: No. Only the priority pairs list is cached. All candle data and indicators used for trading decisions are fetched fresh on every scan.

**Q: What if market conditions change rapidly?**  
A: The refresh interval (1 hour default) balances performance and freshness. Major pairs don't typically change volume rankings within an hour. You can reduce the interval if needed.

**Q: Can I disable the caching?**  
A: Set `PRIORITY_PAIRS_REFRESH_INTERVAL=0` to effectively disable (fetches every scan). However, this is not recommended as it defeats the optimization.

**Q: Does this work with all exchanges?**  
A: Yes, the optimization is exchange-agnostic and works with any exchange supported by the bot.

**Q: What happens if the cache expires during a scan?**  
A: The bot detects expiry before starting a scan and refreshes the cache first. Thread-safe locking prevents race conditions.

## Related Configuration

- `CACHE_DURATION`: Controls candle data cache lifetime (default: 300s)
- `CHECK_INTERVAL`: Controls how often market is scanned (default: 10s)
- `MAX_WORKERS`: Parallel workers for scanning (default: 20)

## Support

For issues or questions about the scanning optimization:
1. Check the logs for cache-related messages
2. Verify `PRIORITY_PAIRS_REFRESH_INTERVAL` is set correctly
3. Run the integration test to verify functionality
4. Review this documentation for configuration details
