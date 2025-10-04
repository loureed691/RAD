# Quick Reference: Managing Existing Positions

## What It Does

The bot **automatically syncs and manages** positions opened manually or by previous sessions.

## How It Works

### 1. On Startup
```
Bot starts → Fetches exchange positions → Imports to manager → Applies stops → Starts managing
```

### 2. During Operation
```
Every 10 cycles → Re-sync → Import new positions → Continue managing
```

## What Gets Applied

| Parameter | Long Positions | Short Positions |
|-----------|----------------|-----------------|
| **Stop Loss** | Current × 0.95 (5% below) | Current × 1.05 (5% above) |
| **Take Profit** | Current × 1.10 (10% above) | Current × 0.90 (10% below) |
| **Trailing Stop** | Activated if profitable | Activated if profitable |

## Example

**Before Bot:**
```
Manual Position: Long BTC @ $50k
Current Price: $51k (no protection)
```

**After Bot Syncs:**
```
✓ Managed Position: Long BTC @ $50k
✓ Stop Loss: $48,450 (protects capital)
✓ Take Profit: $56,100 (targets profit)
✓ Trailing Stop: Active at $51k (locks gains)
✓ P/L: +20% with 10x leverage
```

## Key Benefits

✅ **Zero Configuration** - Works automatically  
✅ **Risk Protection** - Immediate stop loss on all positions  
✅ **Profit Protection** - Trailing stops on profitable positions  
✅ **No Conflicts** - Never duplicates positions  
✅ **Mixed Trading** - Bot + manual positions work together  
✅ **Crash Recovery** - Resumes managing all positions after restart  

## Use Cases

### ✅ Starting Bot with Existing Positions
```
You have 3 positions → Start bot → All 3 managed automatically
```

### ✅ Opening Positions Manually While Bot Runs
```
Bot running → Open manual position → Next sync (≤10 min) → Managed automatically
```

### ✅ Bot Restart/Crash Recovery
```
Bot crashes → Restart bot → All positions recovered → Resume management
```

## Safety

- **Conservative Defaults**: 5% stop loss protects capital
- **No Duplicates**: Positions never synced twice
- **Error Handling**: Sync failures don't stop bot
- **Logging**: All sync operations logged

## Monitoring

Watch logs for:
```
INFO - Syncing existing positions from exchange...
INFO - Synced long position: BTC/USDT:USDT @ 50000.00...
INFO - Successfully synced 2 existing position(s)
INFO - Managing 2 existing position(s) from exchange
```

## Documentation

- Full details: [POSITION_SYNC.md](POSITION_SYNC.md)
- Feature list: [README.md](README.md)
- Tests: `python test_position_sync.py`
