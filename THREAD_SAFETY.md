# Thread Safety Documentation

## Overview

The RAD trading bot uses multiple threads for concurrent operations. This document outlines the thread safety guarantees and best practices.

## Threading Architecture

### Main Threads

1. **Main Thread**: Bot orchestration and coordination
2. **Background Scanner Thread**: Continuous market scanning for opportunities
3. **Position Monitor Thread**: Real-time position monitoring and trailing stops

### Thread Communication

```
Main Thread
    ├─> Background Scanner Thread (reads: market data, writes: opportunities)
    └─> Position Monitor Thread (reads: positions, writes: position updates)
```

## Thread-Safe Components

### 1. PositionManager (`position_manager.py`)

**Shared State**: `self.positions` dictionary

**Protection**: `threading.Lock` via `self._positions_lock`

**Thread-Safe Operations**:
- `open_position()` - Acquires lock before modifying positions
- `close_position()` - Acquires lock before removing positions
- `update_positions()` - Uses lock for position snapshots and updates

**Usage Pattern**:
```python
with self._positions_lock:
    # Critical section - modify positions here
    self.positions[symbol] = position
```

**Safety Guarantees**:
✅ No race conditions when opening/closing positions
✅ Snapshot iteration prevents modification during iteration
✅ Position count is always accurate

### 2. MarketScanner (`market_scanner.py`)

**Shared State**: `self.cache` dictionary, `self._latest_opportunities` list

**Protection**: `threading.Lock` via `self._cache_lock`

**Thread-Safe Operations**:
- `scan_pair()` - Acquires cache lock for reads/writes
- `get_best_pairs()` - Thread-safe cache access

**Usage Pattern**:
```python
with self._cache_lock:
    self.cache[key] = (data, timestamp)
```

**Safety Guarantees**:
✅ Cache reads/writes are atomic
✅ No stale data issues
✅ Concurrent scans don't corrupt cache

### 3. KuCoinClient (`kucoin_client.py`)

**Shared State**: `self._pending_critical_calls`, `self._symbol_metadata_cache`

**Protection**: Multiple locks:
- `self._critical_call_lock` - For API priority management
- `self._metadata_lock` - For symbol metadata cache

**Thread-Safe Operations**:
- `_wait_for_critical_calls()` - Coordinated API priority
- All API methods use appropriate locking

**Safety Guarantees**:
✅ Critical trading operations have priority over scanning
✅ Rate limiting is thread-safe
✅ Metadata cache prevents race conditions

### 4. PerformanceMonitor (`performance_monitor.py`)

**Shared State**: Timing metrics in deque structures

**Protection**: `threading.Lock` via `self._lock`

**Thread-Safe Operations**:
- All `record_*()` methods acquire lock
- `get_stats()` provides atomic snapshot

**Safety Guarantees**:
✅ Metrics collection is thread-safe
✅ No lost updates
✅ Statistics are always consistent

## Thread Safety Best Practices

### DO ✅

1. **Always use locks for shared state**:
   ```python
   with self._lock:
       self.shared_data = new_value
   ```

2. **Use snapshots for iteration**:
   ```python
   with self._lock:
       items_snapshot = list(self.items.keys())
   
   for item in items_snapshot:
       # Safe to iterate without holding lock
       process(item)
   ```

3. **Keep critical sections small**:
   ```python
   # Good - lock only for data access
   with self._lock:
       value = self.data[key]
   expensive_computation(value)  # Outside lock
   ```

4. **Use thread-safe data structures when possible**:
   - `collections.deque` with maxlen (atomic append/popleft)
   - `queue.Queue` for producer-consumer patterns

### DON'T ❌

1. **Don't hold locks during I/O**:
   ```python
   # Bad - I/O inside lock
   with self._lock:
       data = api_call()  # DON'T!
       self.cache[key] = data
   
   # Good - I/O outside lock
   data = api_call()
   with self._lock:
       self.cache[key] = data
   ```

2. **Don't nest locks (risk of deadlock)**:
   ```python
   # Bad - nested locks
   with self._lock_a:
       with self._lock_b:  # DEADLOCK RISK!
           pass
   ```

3. **Don't modify shared state without locks**:
   ```python
   # Bad - race condition
   self.counter += 1  # NOT ATOMIC!
   
   # Good
   with self._lock:
       self.counter += 1
   ```

## Synchronization Patterns

### Pattern 1: Producer-Consumer (Background Scanner)

```python
# Producer (background scanner)
with self._scan_lock:
    self._latest_opportunities = new_opportunities
    self._last_opportunity_update = datetime.now()

# Consumer (main thread)
with self._scan_lock:
    if self._latest_opportunities:
        opportunities = self._latest_opportunities.copy()
```

### Pattern 2: Snapshot Iteration (Position Updates)

```python
# Get thread-safe snapshot
with self._positions_lock:
    positions_snapshot = list(self.positions.keys())

# Iterate without holding lock
for symbol in positions_snapshot:
    with self._positions_lock:
        # Re-check existence (may have been closed)
        if symbol not in self.positions:
            continue
        position = self.positions[symbol]
    
    # Process position outside lock
    process_position(position)
```

### Pattern 3: Priority Coordination (API Calls)

```python
# Critical call increments counter
with self._critical_call_lock:
    self._pending_critical_calls += 1

try:
    # Execute critical operation
    result = execute_trade()
finally:
    with self._critical_call_lock:
        self._pending_critical_calls -= 1

# Non-critical calls wait
def _wait_for_critical_calls(self, priority):
    if priority > CRITICAL:
        while self._pending_critical_calls > 0:
            time.sleep(0.05)
```

## Debugging Thread Issues

### Detecting Deadlocks

If the bot appears frozen:

1. Check thread status:
   ```python
   import threading
   for thread in threading.enumerate():
       print(f"{thread.name}: {thread.is_alive()}")
   ```

2. Look for lock contention in logs (enable DEBUG level)

3. Check for nested lock acquisitions

### Detecting Race Conditions

Symptoms:
- Inconsistent position counts
- Cache corruption
- Unexpected KeyErrors

Solutions:
1. Add lock assertions: `assert self._lock.locked()`
2. Use thread-safe containers: `queue.Queue`, `collections.deque`
3. Review all shared state access

## Performance Considerations

### Lock Overhead

- Locks add ~50-100ns overhead per acquisition
- Keep critical sections minimal
- Use lock-free data structures when possible

### Optimal Thread Count

Current configuration:
- 1 main thread (coordination)
- 1 background scanner (market scanning)
- 1 position monitor (position updates)
- ThreadPoolExecutor with 20 workers (parallel pair scanning)

This configuration balances:
- Responsiveness (sub-second position updates)
- Throughput (parallel market scanning)
- API rate limits (controlled concurrent requests)

## Testing Thread Safety

Run the thread safety tests:

```bash
python test_thread_safety.py
```

This tests:
- Concurrent position updates
- Parallel cache access
- API priority coordination
- No deadlocks under load

## Summary

✅ **Position management**: Fully thread-safe with locks
✅ **Market scanning**: Thread-safe cache with locks
✅ **API client**: Priority coordination with locks
✅ **Performance monitoring**: Thread-safe metrics collection

⚠️ **When adding new shared state**: Always protect with locks
⚠️ **When modifying existing code**: Review lock usage carefully
⚠️ **When debugging hangs**: Check for deadlocks and lock contention
