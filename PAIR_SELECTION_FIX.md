# Pair Selection Fix Summary

## Problem
The pair selection filter appeared "stuck" - always selecting the same pairs regardless of market conditions.

## Root Causes
1. **Incorrect data structure access**: The `get_active_futures()` method returned futures with structure `{'symbol': str, 'info': dict}`, but the filter tried to access `swap` and `quoteVolume` at the top level (they were nested in `'info'`).

2. **Volume filtering broken**: `future.get('quoteVolume', 0)` always returned 0, so volume filtering never worked.

3. **Swap detection broken**: `future.get('swap', False)` always returned False, so only hardcoded major coins were selected.

4. **Over-broad major coin filter**: The filter matched any symbol containing "BTC", "ETH", etc., including dated futures like `BTC/USD:BTC-251226`.

## Solutions Applied

### 1. Fixed Data Structure (kucoin_client.py)
```python
# BEFORE
futures = [
    {'symbol': symbol, 'info': market}
]

# AFTER
futures = [
    {
        'symbol': symbol,
        'info': market,
        'swap': market.get('swap', False),
        'future': market.get('future', False),
        'quoteVolume': ticker_data  # optionally fetched
    }
]
```

### 2. Added Optional Volume Fetching
- Added `include_volume` parameter to `get_active_futures()`
- Fetches tickers to get real 24h volume data
- Falls back gracefully if ticker fetch fails

### 3. Improved Major Coin Filter (market_scanner.py)
```python
# BEFORE
if any(major in symbol for major in ['BTC', 'ETH', ...]):
    priority_symbols.append(symbol)  # Includes dated futures!

# AFTER
if any(major in symbol for major in ['BTC', 'ETH', ...]):
    if future_info.get('swap', False):  # Only perpetual swaps
        priority_symbols.append(symbol)
```

### 4. Smarter Fallback Logic
```python
# BEFORE
if len(priority_symbols) < 10:
    return symbols  # Returns ALL pairs, even low volume ones

# AFTER
if len(priority_symbols) < 5 and len(symbols) > 10:
    # Include all perpetual swaps, but still respect volume filter
    return [s for s in symbols if is_swap(s) and volume_ok(s)]
```

## Benefits

1. **Dynamic pair selection**: No longer stuck on the same pairs
2. **Volume-aware filtering**: Excludes low-liquidity pairs (< $1M daily volume)
3. **Better trade quality**: Only trades high-volume perpetual swaps
4. **Improved liquidity**: Better fills with less slippage
5. **Correct filtering**: Only includes appropriate trading instruments

## Testing

All existing tests pass:
- ✅ `test_strategy_optimizations.py` (5/5 tests)
- ✅ `test_bot.py` (12/12 tests)
- ✅ Volume filtering test validates correct behavior
- ✅ Major coin filter excludes dated futures

## Impact

The bot will now:
- Select a diverse range of pairs based on volume and type
- Avoid low-volume pairs that could have poor execution
- Only trade perpetual swaps (not dated futures)
- Dynamically adjust pair selection as market conditions change

This resolves the "stuck" behavior where the same pairs were always selected.
