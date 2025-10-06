# Logging Improvements

## Overview

This document describes the improvements made to the logging system to provide better visibility into trading decisions, order execution, and risk management.

## Changes Made

### 1. Fixed Order Details Being None

**Problem**: Order logs were showing `Average Fill Price: None`, `Status: None`, and `Timestamp: None` because the order details weren't being fetched after creation.

**Solution**: 
- Added a brief wait (0.5s) after market order creation to allow exchange to process the order
- Fetch the order status immediately after creation to get actual fill details
- Properly format timestamp for human readability
- Fall back to reference price if average price is unavailable

**Example Output**:
```
================================================================================
BUY ORDER EXECUTED: BTC/USDT:USDT
--------------------------------------------------------------------------------
  Order ID: 364606264291926016
  Type: MARKET
  Side: BUY
  Symbol: BTC/USDT:USDT
  Amount: 0.5 contracts
  Leverage: 10x
  Reference Price: 50000.00
  Average Fill Price: 50025.50
  Filled Amount: 0.5
  Total Cost: 25012.75
  Status: closed
  Timestamp: 2025-10-06 11:15:09
  Slippage: 0.0510%
================================================================================
```

### 2. Trading Strategy Logging

**New Feature**: Added comprehensive logging of trading strategy analysis to help understand why trades are being executed.

**Log File**: `logs/strategy.log`

**What's Logged**:
- Signal type (BUY/SELL)
- Confidence level
- Market regime (trending/ranging/neutral)
- Buy and sell signal strengths
- Multi-timeframe alignment
- Individual strategy components (MA trend, MACD, RSI, volume, momentum, patterns, etc.)

**Example Output**:
```
================================================================================
TRADING STRATEGY ANALYSIS
--------------------------------------------------------------------------------
  Signal: BUY
  Confidence: 67.50%
  Market Regime: trending
  Buy Signals: 6.50 / 10.00
  Sell Signals: 3.50 / 10.00
  Multi-Timeframe Alignment: bullish

  Strategy Components:
    - ma_trend: bullish
    - macd: bullish
    - rsi: weak (38.5)
    - volume: high volume confirmation
    - momentum: strong positive
    - pattern: hammer (bullish)
================================================================================
```

**When It Logs**: Only when a BUY or SELL signal is generated (not for HOLD signals to reduce noise).

### 3. Stop Loss & Take Profit Logging

**New Feature**: Added logging for stop loss and take profit levels when they are set and when they are triggered.

**Log File**: `logs/orders.log`

#### 3.1 When SL/TP Levels Are Set

Logged when a position is opened:

```
================================================================================
STOP LOSS & TAKE PROFIT SET: BTC/USDT:USDT
--------------------------------------------------------------------------------
  Symbol: BTC/USDT:USDT
  Position Side: BUY (LONG)
  Entry Price: 50000.00
  Amount: 0.5 contracts
  Leverage: 10x

  Stop Loss Price: 47500.00
  Stop Loss %: 5.00% from entry
  Stop Loss Type: Monitored (closes position when price reaches SL)

  Take Profit Price: 55000.00
  Take Profit %: 10.00% from entry
  Take Profit Type: Monitored (closes position when price reaches TP)

  Risk/Reward Ratio: 1:2.00
  Timestamp: 2025-10-06 11:15:09
================================================================================
```

#### 3.2 When SL/TP Is Triggered

Logged when stop loss or take profit causes position closure:

```
================================================================================
STOP LOSS TRIGGERED: BTC/USDT:USDT
--------------------------------------------------------------------------------
  Symbol: BTC/USDT:USDT
  Position Side: LONG
  Entry Price: 50000.00
  Exit Price: 47500.00
  Amount: 0.5 contracts
  Leverage: 10x
  Stop Loss Price: 47500.00
  Trigger: Price fell below stop loss
  P/L: -5.00% ($-125.00)
  Duration: 15.5 minutes
  Timestamp: 2025-10-06 11:30:42
================================================================================
```

## Log Files Summary

| Log File | Purpose | Contents |
|----------|---------|----------|
| `logs/bot.log` | Main bot activity | High-level events, initialization, errors |
| `logs/positions.log` | Position tracking | Position opens, closes, P/L details |
| `logs/orders.log` | Order execution & SL/TP | All order details, stop loss/take profit events |
| `logs/strategy.log` | Trading decisions | Strategy analysis, signal generation details |
| `logs/scanning.log` | Market scanning | Pair evaluation, opportunity detection |

## Configuration

New configuration added to `config.py`:

```python
STRATEGY_LOG_FILE = os.getenv('STRATEGY_LOG_FILE', 'logs/strategy.log')
```

Can be customized via `.env` file:
```bash
STRATEGY_LOG_FILE=logs/my_strategy.log
```

## Code Changes

### Files Modified

1. **kucoin_client.py**
   - Enhanced `create_market_order()` to fetch order status after creation
   - Added timestamp formatting
   - Added brief wait for order processing

2. **config.py**
   - Added `STRATEGY_LOG_FILE` configuration

3. **logger.py**
   - Added `get_strategy_logger()` method

4. **signals.py**
   - Added `strategy_logger` initialization in `__init__()`
   - Added comprehensive strategy logging in `generate_signal()`

5. **position_manager.py**
   - Added stop loss/take profit setup logging in `open_position()`
   - Added stop loss/take profit trigger logging in `close_position()`

6. **bot.py**
   - Added strategy logger initialization

## Testing

Run the test suite to verify all improvements:

```bash
python test_logging_improvements.py
```

Tests verify:
- ✓ Logger setup and configuration
- ✓ Strategy logging functionality
- ✓ Stop loss/take profit logging
- ✓ Order details fix
- ✓ Signal generator integration

## Benefits

1. **Better Debugging**: Clear visibility into why trades are executed
2. **Performance Analysis**: Can review what strategies work best
3. **Risk Management**: Track all stop loss and take profit events
4. **Complete Audit Trail**: Full details of every order execution
5. **Troubleshooting**: Quickly identify issues with order fills

## Backward Compatibility

All changes are backward compatible:
- Existing code continues to work without modifications
- New logging is additive, doesn't replace existing logs
- Configuration has sensible defaults
- No breaking changes to API or function signatures
