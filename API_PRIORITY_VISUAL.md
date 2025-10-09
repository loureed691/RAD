# API Call Priority - Visual Guide

## Thread Startup Sequence

### Before (Risk of Collision)

```
Time     Position Monitor          Scanner
────     ────────────────          ───────
0.0s     [Thread created]          [Thread created]
         ↓                         ↓
0.1s     [Starting...]             [Starting...]
         ↓                         ↓
0.2s     API: get_ticker()         API: get_active_futures()
         ↓                         ↓
0.3s     [Processing...]           API: get_ohlcv() × 20
         ↓                         ↓
0.4s     API: get_ticker()         API: get_ohlcv() × 20
         
         ⚠️  COLLISION RISK!
         Both threads competing for API access
```

### After (Priority Enforced)

```
Time     Position Monitor          Scanner
────     ────────────────          ───────
0.0s     [Thread created]          [Not started yet]
         ↓                         
0.1s     [Running]                 [Not started yet]
         ↓                         
0.2s     API: get_ticker() ✅       [Not started yet]
         ↓                         
0.3s     API: get_ohlcv() ✅        [Not started yet]
         ↓                         
0.4s     API: get_ticker() ✅       [Not started yet]
         ↓                         
0.5s     [Running normally]        [Thread created]
         ↓                         ↓
0.6s     API: get_ticker() ✅       [Starting...]
         ↓                         ↓
1.0s     API: get_ticker() ✅       [Waiting...]
         ↓                         ↓
1.5s     API: get_ticker() ✅       API: get_active_futures()
         ↓                         ↓
2.0s     API: get_ticker() ✅       API: get_ohlcv() × 20
         
         ✅ NO COLLISION!
         Position Monitor established priority
         Scanner makes calls AFTER critical ops complete
```

## Code Flow

### Main Thread (bot.py run method)

```
┌─────────────────────────────────────────────┐
│         Bot Initialization                  │
│  - Load config                              │
│  - Initialize components                    │
│  - Sync existing positions                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│      🚨 THREAD START PRIORITY               │
│   1️⃣  Position Monitor (CRITICAL)           │
│   2️⃣  Background Scanner (NORMAL)            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  👁️  Start Position Monitor Thread          │
│  Priority: CRITICAL                         │
│  - Starts immediately                       │
│  - Makes first API calls                    │
└─────────────────────────────────────────────┘
                    ↓
                ⏱ WAIT 500ms
                    ↓
┌─────────────────────────────────────────────┐
│  🔍 Start Background Scanner Thread         │
│  Priority: NORMAL                           │
│  - Starts after delay                       │
│  - Waits 1s before first scan               │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Main Loop Running                   │
│  - Both threads operating independently     │
│  - Position Monitor has priority            │
│  - No collisions                            │
└─────────────────────────────────────────────┘
```

### Position Monitor Thread

```
┌─────────────────────────────────────────────┐
│  👁️  Position Monitor Thread Started        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Check: Do we have open positions?          │
└─────────────────────────────────────────────┘
         ↓ YES                    ↓ NO
┌──────────────────┐    ┌──────────────────┐
│ Check timing     │    │ Skip update      │
│ (last update)    │    │ (nothing to do)  │
└──────────────────┘    └──────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│  Time since last >= POSITION_UPDATE_INTERVAL? │
└─────────────────────────────────────────────┘
         ↓ YES                    ↓ NO
┌──────────────────┐    ┌──────────────────┐
│ Update positions │    │ Wait             │
│ API calls:       │    │ (short sleep)    │
│ - get_ticker() ✅ │    └──────────────────┘
│ - get_ohlcv() ✅  │              ↓
│ - check stops    │         (loop back)
└──────────────────┘
         ↓
    (loop back)
```

### Background Scanner Thread

```
┌─────────────────────────────────────────────┐
│  🔍 Background Scanner Thread Started       │
└─────────────────────────────────────────────┘
                    ↓
        ⏱ WAIT 1 SECOND (Priority delay)
                    ↓
┌─────────────────────────────────────────────┐
│  Beginning market scans                     │
│  (Position Monitor has priority)            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Scan market for opportunities              │
│  API calls:                                 │
│  - get_active_futures()                     │
│  - get_ohlcv() × N (parallel)               │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Update shared opportunities list           │
│  (thread-safe with lock)                    │
└─────────────────────────────────────────────┘
                    ↓
        ⏱ WAIT CHECK_INTERVAL (60s)
                    ↓
               (loop back)
```

## API Call Distribution

### Before Priority Fix

```
API Calls Over Time (10 seconds)
═══════════════════════════════════════════════

Second:  1    2    3    4    5    6    7    8    9    10
         │    │    │    │    │    │    │    │    │    │
Pos Mon: █    █    █    █    █    █    █    █    █    █
Scanner: ████████████████████████████████████████████████

Legend:
█ = API call
⚠️  Calls overlap - potential collision!
```

### After Priority Fix

```
API Calls Over Time (10 seconds)
═══════════════════════════════════════════════

Second:  1    2    3    4    5    6    7    8    9    10
         │    │    │    │    │    │    │    │    │    │
Pos Mon: █    █    █    █    █    █    █    █    █    █
Scanner:                ████████████████████████████████

Legend:
█ = API call
✅ Pos Mon calls first - no collision!
✅ Scanner delayed - priority established!
```

## Shutdown Sequence

```
┌─────────────────────────────────────────────┐
│         Shutdown Signal Received            │
│         (Ctrl+C or SIGTERM)                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Stop Scanner Thread FIRST                  │
│  (Less critical - can stop immediately)     │
│  - Set flag: _scan_thread_running = False   │
│  - Wait up to 5s for clean stop             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Stop Position Monitor Thread SECOND        │
│  (Critical - may have pending operations)   │
│  - Set flag: _position_monitor_running = False │
│  - Wait up to 5s for clean stop             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Close Open Positions (if configured)       │
│  Save ML Model                              │
│  Clean Shutdown Complete                    │
└─────────────────────────────────────────────┘
```

## Priority Levels

```
╔═══════════════════════════════════════════╗
║        CRITICAL PRIORITY                  ║
║  👁️  Position Monitor Thread              ║
║                                           ║
║  • Starts FIRST (time 0)                  ║
║  • Makes API calls immediately            ║
║  • Never blocked by scanner               ║
║  • Monitors stop-loss/take-profit         ║
║  • Updates trailing stops                 ║
║  • Stops LAST in shutdown                 ║
╚═══════════════════════════════════════════╝
                   ↕
              500ms delay
                   ↕
┌───────────────────────────────────────────┐
│        NORMAL PRIORITY                    │
│  🔍 Background Scanner Thread             │
│                                           │
│  • Starts SECOND (time +500ms)            │
│  • Waits 1s before first API call         │
│  • Makes API calls for scanning           │
│  • Finds trading opportunities            │
│  • Never blocks position monitor          │
│  • Stops FIRST in shutdown                │
└───────────────────────────────────────────┘
```

## Key Takeaways

1. **Position Monitor = CRITICAL**: Always gets priority
2. **Scanner = NORMAL**: Waits for position monitor to establish priority
3. **500ms inter-thread delay**: Ensures clean startup
4. **1s scanner delay**: Gives position monitor time to make several calls
5. **Clear logging**: Shows priority order at startup
6. **Proper shutdown order**: Scanner first, position monitor last

## Result

✅ No more API call collisions!
✅ Critical operations always happen first!
✅ Better risk management!
✅ Clearer system behavior!
