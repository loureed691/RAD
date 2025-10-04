# Managing Existing Positions

## Overview

The bot now automatically detects and manages positions that were opened outside of the bot (manually or by a previous bot session). This feature ensures all your KuCoin Futures positions are intelligently managed with trailing stops and risk controls.

## How It Works

### 1. Initial Sync on Startup

When the bot starts, it automatically:
- Fetches all open positions from your KuCoin Futures account
- Imports them into the position management system
- Applies intelligent stop loss and take profit levels
- Activates trailing stops for profitable positions

Example log output:
```
15:16:29 - INFO - Syncing existing positions from exchange...
15:16:29 - INFO - Synced long position: BTC/USDT:USDT @ 50000.00, Current: 51000.00, Amount: 0.5, Leverage: 10x, P/L: 20.00%
15:16:29 - INFO - Successfully synced 2 existing position(s)
15:16:29 - INFO - Managing 2 existing position(s) from exchange
```

### 2. Periodic Sync During Operation

Every 10 trading cycles (approximately every 10 minutes with default settings), the bot:
- Re-syncs positions from the exchange
- Detects any new positions opened manually
- Adds them to the management system automatically

This ensures the bot never misses a position and can manage everything seamlessly.

### 3. Smart Position Import

When importing existing positions, the bot:

**Stop Loss Calculation:**
- Uses a conservative 5% stop loss from current price (not entry price)
- For long positions: Stop loss = Current Price × 0.95
- For short positions: Stop loss = Current Price × 1.05

**Take Profit Calculation:**
- Sets take profit at 2× the stop loss distance
- For long positions: Take profit = Current Price × 1.10
- For short positions: Take profit = Current Price × 0.90

**Trailing Stop Activation:**
- If a long position is already profitable (current > entry), highest price is set to current price
- If a short position is already profitable (current < entry), lowest price is set to current price
- This immediately activates the trailing stop mechanism

**Duplicate Prevention:**
- Positions already tracked by the bot are never duplicated
- Only new positions from the exchange are imported

## Benefits

1. **Seamless Management**: No need to manually close positions before starting the bot
2. **Risk Protection**: All positions get stop loss protection automatically
3. **Profit Protection**: Trailing stops lock in gains for profitable positions
4. **Flexibility**: You can open positions manually and let the bot manage them
5. **Recovery**: If the bot crashes and restarts, it picks up all positions automatically

## Example Scenarios

### Scenario 1: Manual Position to Bot Management
```
You manually open:
- Long BTC/USDT:USDT @ 50,000 with 0.5 contracts

Bot starts and detects:
- Current price: 51,000 (2% profit)
- Sets stop loss: 48,450 (5% below current)
- Sets take profit: 56,100 (10% above current)
- Activates trailing stop at 51,000
- Manages position automatically
```

### Scenario 2: Bot Restart Recovery
```
Bot was managing:
- Long ETH/USDT:USDT @ 3,000
- Long SOL/USDT:USDT @ 100

Bot crashes and restarts:
- Syncs both positions from exchange
- Resumes management with current market prices
- Applies trailing stops based on current state
- Continues managing both positions
```

### Scenario 3: Mixed Management
```
You have:
- Position opened by bot: BTC/USDT:USDT
- Position opened manually: ETH/USDT:USDT

Bot behavior:
- Continues managing BTC position normally
- Syncs and imports ETH position
- Manages both with same risk controls
- No conflicts or duplicates
```

## Technical Details

### Position Sync Method

The `sync_existing_positions()` method in `PositionManager`:
```python
def sync_existing_positions(self):
    """Sync existing positions from the exchange"""
    # Fetches positions via KuCoin API
    # Creates Position objects for tracking
    # Applies stop loss and take profit
    # Logs all imported positions
    # Returns count of synced positions
```

### API Usage

Uses the KuCoin Futures API endpoint:
- `exchange.fetch_positions()` - Gets all open positions
- Includes: symbol, contracts, side, entry price, leverage
- No additional API calls needed beyond normal operations

### Performance Impact

- **Startup**: Adds ~0.5-1 second to bot initialization
- **Runtime**: Negligible (sync every ~10 minutes)
- **API calls**: +1 call at startup, +1 call every 10 cycles

## Configuration

No additional configuration needed! The feature works automatically with existing settings:

- `TRAILING_STOP_PERCENTAGE`: Applied to synced positions
- `MAX_OPEN_POSITIONS`: Includes synced positions in count
- All risk management settings apply equally

## Safety Features

1. **No Duplicate Syncing**: Positions are never synced twice
2. **Error Handling**: Sync failures don't stop bot operation
3. **Conservative Defaults**: 5% stop loss protects capital
4. **Graceful Degradation**: If sync fails, bot continues normally
5. **Detailed Logging**: All sync operations are logged for transparency

## Monitoring

Watch for these log messages:
- `"Syncing existing positions from exchange..."` - Sync starting
- `"Synced {side} position: {symbol}..."` - Position imported
- `"Successfully synced N existing position(s)"` - Sync completed
- `"No existing positions found on exchange"` - No positions to import
- `"Position {symbol} already tracked, skipping sync"` - Duplicate prevention

## Testing

Run the position sync tests:
```bash
python test_position_sync.py
```

Expected output:
```
============================================================
Test Results: 3/3 passed
============================================================
✓ All position sync tests passed!
```

## Limitations

1. **Position Details**: Some position details (like original stop loss) are not preserved
2. **Manual Orders**: Pending orders are not imported (only open positions)
3. **Cross/Isolated Margin**: Bot assumes cross margin mode for all positions

## Future Enhancements

Possible improvements for future versions:
- Preserve original stop loss if available from exchange
- Import and manage pending limit orders
- More sophisticated P/L-based stop loss calculation
- Per-position risk assessment and adjustment
