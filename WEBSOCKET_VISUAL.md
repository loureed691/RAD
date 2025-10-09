# WebSocket Integration Visual Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TRADING BOT                                  │
│                                                                      │
│  ┌───────────────┐    ┌──────────────┐    ┌───────────────┐       │
│  │ Market        │    │ Position     │    │ Risk          │       │
│  │ Scanner       │    │ Manager      │    │ Manager       │       │
│  └───────┬───────┘    └──────┬───────┘    └───────┬───────┘       │
│          │                    │                     │               │
│          └────────────────────┼─────────────────────┘               │
│                               │                                     │
│                    ┌──────────▼──────────┐                         │
│                    │   KuCoinClient      │                         │
│                    │  (API Coordinator)  │                         │
│                    └──────────┬──────────┘                         │
│                               │                                     │
│              ┌────────────────┴────────────────┐                   │
│              │                                  │                   │
│    ┌─────────▼─────────┐            ┌─────────▼─────────┐         │
│    │  WebSocket Client │            │   REST API Client │         │
│    │  (Market Data)    │            │   (Trading)       │         │
│    └─────────┬─────────┘            └─────────┬─────────┘         │
│              │                                  │                   │
└──────────────┼──────────────────────────────────┼───────────────────┘
               │                                  │
               │                                  │
      ┌────────▼────────┐                ┌───────▼────────┐
      │  KuCoin Futures │                │  KuCoin Futures│
      │  WebSocket API  │                │   REST API     │
      │                 │                │                │
      │ wss://...       │                │ https://...    │
      └─────────────────┘                └────────────────┘
```

## Data Flow: get_ticker()

```
1. Market Scanner needs ticker for BTC/USDT:USDT
   ↓
2. Call client.get_ticker('BTC/USDT:USDT')
   ↓
3. Check: Is WebSocket connected? → YES
   ↓
4. Query WebSocket cache
   ↓
5. Cache hit? → YES → Return cached data (Fast! <1ms)
   │
   └─→ NO → Is subscribed? → YES → Wait 500ms → Return
           │
           └─→ NO → Subscribe to ticker → Wait 500ms
                   │
                   └─→ Still no data? → Fallback to REST API
```

## Data Flow: Trading Operation

```
1. Bot decides to place order for BTC/USDT:USDT
   ↓
2. Call client.create_market_order(...)
   ↓
3. ALWAYS use REST API (no WebSocket involved)
   ↓
4. Place order via REST API
   ↓
5. Return order confirmation
```

## WebSocket Lifecycle

```
Startup:
┌────────────────────────────────────────────────────────┐
│ 1. Bot starts                                          │
│ 2. Initialize KuCoinClient                             │
│ 3. Create WebSocket client                             │
│ 4. Get connection token from REST API                  │
│ 5. Connect to WebSocket endpoint                       │
│ 6. Receive "welcome" message                           │
│ 7. Start ping thread (keep-alive every 20s)           │
│ 8. Ready to subscribe to channels                      │
└────────────────────────────────────────────────────────┘

Normal Operation:
┌────────────────────────────────────────────────────────┐
│ 1. Scanner requests ticker for symbol                  │
│ 2. Check if already subscribed                         │
│    └─ NO: Subscribe to /contractMarket/ticker:{symbol} │
│ 3. Receive real-time updates                           │
│ 4. Cache updates in thread-safe dict                   │
│ 5. Subsequent requests use cache (very fast)           │
└────────────────────────────────────────────────────────┘

Disconnection:
┌────────────────────────────────────────────────────────┐
│ 1. WebSocket connection drops                          │
│ 2. Set connected = False                               │
│ 3. Wait 5 seconds                                       │
│ 4. Reconnect to WebSocket                              │
│ 5. Resubscribe to all previous channels                │
│ 6. Resume normal operation                             │
│ 7. Meanwhile: REST API used as fallback                │
└────────────────────────────────────────────────────────┘

Shutdown:
┌────────────────────────────────────────────────────────┐
│ 1. Bot receives shutdown signal                        │
│ 2. Call client.close()                                 │
│ 3. Set should_reconnect = False                        │
│ 4. Close WebSocket connection                          │
│ 5. Stop ping thread                                    │
│ 6. Clean up resources                                  │
└────────────────────────────────────────────────────────┘
```

## Subscription Model

```
Symbol: BTC/USDT:USDT
  │
  ├─► Ticker Channel
  │   Topic: /contractMarket/ticker:BTCUSDTUSDT
  │   Updates: Every price change (~100ms)
  │   Cached: Last 1 ticker (10s freshness)
  │
  ├─► Candle Channel
  │   Topic: /contractMarket/candle:BTCUSDTUSDT_1hour
  │   Updates: Every candle close (1 hour)
  │   Cached: Last 500 candles
  │
  └─► Orderbook Channel (Optional)
      Topic: /contractMarket/level2:BTCUSDTUSDT
      Updates: Every orderbook change
      Cached: Full orderbook
```

## Priority System (Unchanged)

```
API Call Priority Queue:

CRITICAL (Priority 1)
├─► create_market_order()
├─► create_limit_order()
└─► close_position()
    ↓ Execute immediately, block other operations

HIGH (Priority 2)
├─► get_balance()
├─► get_positions()
└─► get_order_status()
    ↓ Execute after CRITICAL

NORMAL (Priority 3)
├─► get_ticker() → Try WebSocket first
├─► get_ohlcv() → Try WebSocket first
└─► get_active_futures()
    ↓ Execute after CRITICAL and HIGH

Note: WebSocket reads don't use priority queue (always available)
```

## Thread Safety

```
Main Thread:
├─► Market Scanner (requests ticker)
├─► Position Manager (requests ticker)
└─► Risk Manager (requests data)
     │
     └─► All read from WebSocket cache
         (Lock-protected, thread-safe)

Background Thread 1:
└─► WebSocket Connection
    ├─► Receive messages
    ├─► Update cache (with lock)
    └─► Handle reconnection

Background Thread 2:
└─► Position Monitor
    └─► Periodic position updates

Background Thread 3:
└─► Ping Thread
    └─► Send ping every 20s
```

## Fallback Decision Tree

```
Need ticker data?
├─► WebSocket enabled?
│   ├─► YES: Connected?
│   │   ├─► YES: Has ticker?
│   │   │   ├─► YES: Fresh (<10s)?
│   │   │   │   ├─► YES: ✅ Use WebSocket (FAST!)
│   │   │   │   └─► NO: ⚠️ Use REST API
│   │   │   └─► NO: Subscribe → Wait → Check again
│   │   └─► NO: ⚠️ Use REST API
│   └─► NO: ⚠️ Use REST API
└─► ✅ Got ticker data!
```

## Performance Comparison

```
Operation: Get ticker for BTC/USDT:USDT

REST API Only:
┌─────────────────────────────────────────────────────┐
│ Request → Network → KuCoin → Processing → Response  │
│                                                      │
│ Time: 500-1000ms                                     │
│ Freshness: 1-5 seconds old                           │
│ Cost: 1 API call                                     │
└─────────────────────────────────────────────────────┘

WebSocket:
┌─────────────────────────────────────────────────────┐
│ Check cache → Return                                 │
│                                                      │
│ Time: <1ms                                           │
│ Freshness: Real-time (< 100ms)                       │
│ Cost: 0 API calls (already subscribed)              │
└─────────────────────────────────────────────────────┘

Speed Improvement: 500-1000x faster! ⚡
```

## Configuration Examples

### Enabled (Default)
```env
ENABLE_WEBSOCKET=true
```
Result:
- ✅ Real-time market data via WebSocket
- ✅ Automatic fallback to REST if needed
- ✅ 10x faster ticker/OHLCV updates

### Disabled
```env
ENABLE_WEBSOCKET=false
```
Result:
- ✅ All operations use REST API
- ✅ Still works perfectly
- ⚠️ Slower market data updates

### Not Set (Default: Enabled)
```env
# No ENABLE_WEBSOCKET setting
```
Result:
- ✅ Defaults to enabled
- ✅ WebSocket used automatically
