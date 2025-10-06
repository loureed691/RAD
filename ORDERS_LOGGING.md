# Orders Logging Feature

## Overview

All buy and sell orders executed through the KuCoin client are now automatically logged to a dedicated orders log file (`logs/orders.log`). This provides a complete audit trail of all trading activity.

## Configuration

The orders log is configured in `.env` (optional):

```bash
# Orders log file (default: logs/orders.log)
ORDERS_LOG_FILE=logs/orders.log
```

If not specified, the default `logs/orders.log` will be used.

## What is Logged

The orders logger tracks all order lifecycle events:

### 1. Market Orders (Immediate Execution)
- Order ID, symbol, side (BUY/SELL)
- Contract amount and leverage
- Reference price and actual fill price
- Slippage percentage
- Total cost and fill amount
- Execution timestamp

### 2. Limit Orders (Price-Specific)
- Order ID, symbol, side (BUY/SELL)
- Contract amount and limit price
- Leverage setting
- Post-only flag (maker-only orders)
- Reduce-only flag (position closing only)
- Order status and timestamp

### 3. Stop-Limit Orders (Conditional)
- Order ID, symbol, side (BUY/SELL)
- Contract amount
- Stop trigger price
- Limit execution price
- Leverage setting
- Reduce-only flag
- Order status and timestamp

### 4. Order Cancellations
- Order ID and symbol
- Cancellation timestamp

## Log Format

Each order entry is clearly formatted with separators for easy reading:

```
================================================================================
BUY ORDER EXECUTED: BTC/USDT:USDT
--------------------------------------------------------------------------------
  Order ID: 123456789
  Type: MARKET
  Side: BUY
  Symbol: BTC/USDT:USDT
  Amount: 0.001 contracts
  Leverage: 10x
  Reference Price: 50000.00
  Average Fill Price: 50050.00
  Filled Amount: 0.001
  Total Cost: 50.05
  Status: closed
  Timestamp: 1696608000000
  Slippage: 0.1000%
================================================================================

```

## Benefits

1. **Complete Audit Trail**: Every order is logged, making it easy to review trading history
2. **Performance Analysis**: Analyze slippage, execution quality, and order patterns
3. **Debugging**: Quickly identify and debug order execution issues
4. **Compliance**: Maintain records for tax reporting or regulatory requirements
5. **Separated Logs**: Orders are logged separately from general bot operations for clarity

## Accessing the Log

The orders log is located at `logs/orders.log` by default. You can:

- View it directly: `cat logs/orders.log`
- Tail it in real-time: `tail -f logs/orders.log`
- Filter by order type: `grep "MARKET" logs/orders.log`
- Filter by symbol: `grep "BTC/USDT" logs/orders.log`
- Filter by side: `grep "BUY ORDER" logs/orders.log`

## Log Rotation

For production environments, consider setting up log rotation to prevent the orders log from growing too large:

```bash
# Example logrotate configuration
/path/to/logs/orders.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 user group
}
```

## Integration with Existing Logs

The orders log complements the existing logging system:

- **logs/bot.log** - General bot operations and high-level trading decisions
- **logs/positions.log** - Position lifecycle (open, update, close)
- **logs/scanning.log** - Market scanning and opportunity detection
- **logs/orders.log** - Order execution details (NEW)

Together, these logs provide comprehensive visibility into all aspects of the trading bot's operations.

## Testing

To verify the orders logging is working correctly, run:

```bash
python test_orders_logging.py
```

This test will:
- Verify the configuration is correct
- Test all order types (market, limit, stop-limit, cancel)
- Display sample log entries
- Confirm the log file is created and written properly

## Example Usage in Code

The orders logging is automatic - no changes needed to existing code. It works with all order creation methods:

```python
# Market order - automatically logged
order = client.create_market_order('BTC/USDT:USDT', 'buy', 0.001, leverage=10)

# Limit order - automatically logged
order = client.create_limit_order('ETH/USDT:USDT', 'sell', 0.1, 3000.0, 
                                  leverage=5, post_only=True)

# Stop-limit order - automatically logged
order = client.create_stop_limit_order('BTC/USDT:USDT', 'buy', 0.01, 
                                       stop_price=49000.0, 
                                       limit_price=49500.0)

# Cancel order - automatically logged
success = client.cancel_order('order_id', 'BTC/USDT:USDT')
```

All of these operations will be logged to `logs/orders.log` automatically.
