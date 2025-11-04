# Advanced Quantitative Trading Features

## Overview

This document describes the advanced quantitative trading features implemented in the RAD trading bot.

## Table of Contents

1. [Avellaneda-Stoikov Market Making](#avellaneda-stoikov-market-making)
2. [Market Microstructure Analytics](#market-microstructure-analytics)
3. [Delta Hedging](#delta-hedging)
4. [Funding/Basis Arbitrage](#funding-basis-arbitrage)
5. [Smart Order Routing](#smart-order-routing)
6. [Observability](#observability)
7. [Paper Trading](#paper-trading)
8. [Async Support](#async-support)

---

## Avellaneda-Stoikov Market Making

### Overview

The Avellaneda-Stoikov (AS) model is a sophisticated market making strategy that optimally sets bid/ask spreads based on:
- Volatility estimation
- Inventory risk
- Time horizon
- Risk aversion

### Usage

```python
from avellaneda_stoikov import AvellanedaStoikovStrategy

# Initialize strategy
strategy = AvellanedaStoikovStrategy(
    risk_aversion=0.1,          # Higher = more conservative
    time_horizon_minutes=60.0,  # Trading session length
    order_arrival_rate=1.0,     # Orders per minute
    max_inventory=5,            # Maximum position size
    min_spread_bps=5.0,         # Minimum spread (5 bps)
    max_spread_bps=100.0        # Maximum spread (100 bps)
)

# Calculate optimal quotes
mid_price = 100.0
inventory = 2  # Current inventory position
price_history = [99.5, 100.0, 100.5]  # Recent prices

quotes = strategy.calculate_quotes(mid_price, inventory, price_history)

print(f"Bid: ${quotes['bid']:.2f}")
print(f"Ask: ${quotes['ask']:.2f}")
print(f"Spread: {quotes['spread_bps']:.1f} bps")
```

### Key Features

1. **Optimal Spread Calculation**: Dynamically adjusts spreads based on market conditions
2. **Inventory Management**: Skews quotes to rebalance inventory
3. **Volatility Adaptive**: Wider spreads in volatile markets
4. **Time Decay**: Adjusts urgency as session progresses

### Parameters

- `risk_aversion` (γ): Controls spread width (0.01-1.0)
- `time_horizon_minutes` (T): Session length
- `order_arrival_rate` (k): Expected order flow
- `max_inventory`: Position size limit
- `min/max_spread_bps`: Spread constraints

---

## Market Microstructure Analytics

### Overview

Advanced order flow and liquidity analysis including:
- **Microprice**: Volume-weighted mid-price
- **Queue Imbalance (QI)**: Depth-based order book pressure
- **Order Flow Imbalance (OFI)**: Trade flow direction
- **Kyle's Lambda (λ)**: Price impact coefficient

### Usage

```python
from market_microstructure_2026 import MarketMicrostructure2026

microstructure = MarketMicrostructure2026(history_length=100)

# Get comprehensive metrics
orderbook = {
    'bids': [[100.0, 10.0], [99.9, 8.0]],
    'asks': [[100.1, 9.0], [100.2, 11.0]]
}
recent_trades = [
    {'side': 'buy', 'size': 5.0, 'time': datetime.now()}
]

metrics = microstructure.get_comprehensive_metrics(
    orderbook, recent_trades, price=100.05
)

print(f"Microprice: ${metrics['microprice']:.2f}")
print(f"Queue Imbalance: {metrics['queue_imbalance']['queue_imbalance']:.3f}")
print(f"Order Flow Imbalance: {metrics['order_flow_imbalance']['order_flow_imbalance']:.3f}")
print(f"Kyle's Lambda: {metrics['kyle_lambda']:.6f}")
```

### Metrics Explained

#### Microprice
Formula: `(ask_vol * bid + bid_vol * ask) / (bid_vol + ask_vol)`

Better estimate of true price than simple mid-price as it accounts for depth.

#### Queue Imbalance (QI)
Formula: `(bid_qty - ask_qty) / (bid_qty + ask_qty)`

- QI > 0.2: Strong buy pressure
- QI < -0.2: Strong sell pressure

#### Order Flow Imbalance (OFI)
Formula: `(buy_volume - sell_volume) / total_volume`

Measures aggressive buying vs. selling pressure from recent trades.

#### Kyle's Lambda (λ)
Formula: `ΔP = λ * Q`

Estimates price impact per unit of order flow. Higher λ means more price impact.

---

## Delta Hedging

### Overview

Manages directional risk through automatic hedging of portfolio delta.

### Usage

```python
from delta_hedger import DeltaHedger

hedger = DeltaHedger(
    hedge_symbol="BTCUSDT",
    delta_threshold=0.1,        # Rehedge when |delta| > 0.1
    rehedge_frequency_minutes=15,
    enable_auto_hedge=True
)

# Update positions
hedger.update_position(
    symbol="ETHUSDT",
    size=10.0,
    side="long",
    price=2000.0
)

# Check if hedging needed
should_hedge, reason = hedger.should_rehedge()
if should_hedge:
    hedge_size = hedger.calculate_hedge_size()
    print(f"Need to hedge: {hedge_size:.4f} {hedger.hedge_symbol}")
    hedge_order = hedger.execute_hedge(hedge_size)
```

### Features

- **Automatic Rehedging**: Triggers when delta exceeds threshold
- **Greeks Calculation**: Delta, gamma, vega
- **Multi-Symbol Support**: Aggregates delta across portfolio
- **Frequency Control**: Avoids over-hedging

---

## Funding/Basis Arbitrage

### Overview

Captures funding rate premiums and basis spreads through market-neutral positions.

### Usage

```python
from funding_basis_arb import FundingBasisArbitrage

arb = FundingBasisArbitrage(
    min_funding_rate=0.01,   # 1% APR minimum
    min_basis_bps=10.0,      # 10 bps minimum
    max_leverage=3.0,
    capital_allocation=0.3   # 30% of portfolio
)

# Check funding opportunity
opportunity = arb.check_funding_opportunity(
    symbol="BTCUSDT",
    spot_price=50000.0,
    perp_price=50100.0,
    capital_available=10000.0
)

if opportunity['opportunity']:
    print(f"Strategy: {opportunity['strategy']}")
    print(f"Expected APR: {opportunity['expected_apr']:.2f}%")
    print(f"Position Size: ${opportunity['position_size_usd']:.2f}")
```

### Strategies

1. **Funding Rate Arbitrage**:
   - Positive funding: Short perp, long spot
   - Negative funding: Long perp, short spot

2. **Basis Trading**:
   - Price divergence between exchanges
   - Convergence trade when basis exceeds threshold

---

## Smart Order Routing

### Overview

Routes orders to achieve best execution across multiple venues.

### Usage

```python
from smart_order_router import SmartOrderRouter, Venue

# Create router
sor = SmartOrderRouter(
    enable_order_splitting=True,
    max_venues_per_order=3
)

# Define venues
venues = [
    Venue("Binance", bid=100.0, ask=100.1, bid_size=50, ask_size=50, fee=0.001),
    Venue("KuCoin", bid=100.05, ask=100.15, bid_size=30, ask_size=30, fee=0.001),
    Venue("Bybit", bid=99.95, ask=100.05, bid_size=40, ask_size=40, fee=0.001)
]

# Route order
routing = sor.route_order(venues, side='buy', size=100, symbol='BTCUSDT')

if routing['success']:
    if routing['strategy'] == 'split':
        for alloc in routing['allocations']:
            print(f"{alloc['venue']}: {alloc['size']:.2f} @ ${alloc['price']:.2f}")
```

### Features

- **Price Comparison**: Finds best prices across venues
- **Order Splitting**: Divides large orders for better execution
- **Latency Awareness**: Factors in venue latency
- **Transaction Cost Analysis**: Includes fees and slippage

---

## Observability

### ClickHouse Logging

High-performance columnar database for time-series data.

```python
from clickhouse_logger import ClickHouseLogger

logger = ClickHouseLogger(
    host='localhost',
    port=9000,
    database='trading',
    use_sqlite_fallback=True  # Falls back to SQLite if CH unavailable
)

# Log trade
logger.log_trade({
    'symbol': 'BTCUSDT',
    'side': 'buy',
    'price': 50000.0,
    'size': 1.0,
    'value': 50000.0,
    'fee': 50.0
})

# Log metric
logger.log_metric('win_rate', 0.75, tags={'strategy': 'momentum'})
```

### Prometheus Metrics

Exports metrics for monitoring dashboards.

```python
from prometheus_metrics import PrometheusMetrics

metrics = PrometheusMetrics(port=8000, enable_http_server=True)

# Record trades
metrics.record_trade('BTCUSDT', 'buy', pnl=100.0, duration_seconds=3600)

# Update positions
metrics.update_positions(num_positions=5)
metrics.update_pnl(realized_pnl=500.0, unrealized_pnl=150.0)

# Metrics available at http://localhost:8000/metrics
```

---

## Paper Trading

### Overview

Simulates trading without real orders for strategy testing.

### Usage

```python
from paper_trading import PaperTradingEngine

paper = PaperTradingEngine(
    initial_balance=10000.0,
    fee_rate=0.001,
    slippage_bps=5.0
)

# Place order
order = paper.place_order(
    symbol='BTCUSDT',
    side='buy',
    size=1.0,
    order_type='market',
    current_price=50000.0
)

# Update prices
paper.update_prices({'BTCUSDT': 50500.0})

# Get performance
perf = paper.get_performance()
print(f"Total Return: {perf['total_return_pct']:.2f}%")
print(f"Win Rate: {perf['win_rate_pct']:.1f}%")
```

### Features

- **Realistic Fills**: Simulates slippage and fees
- **Position Tracking**: Full portfolio management
- **Performance Metrics**: P&L, win rate, drawdown
- **Order Types**: Market and limit orders

---

## Async Support

### Overview

Concurrent execution for I/O-bound operations.

### Usage

```python
import asyncio
from async_support import AsyncTrading, AsyncEventBus, RateLimiter

async def main():
    # Concurrent price fetching
    async_trading = AsyncTrading(max_workers=10)
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    prices = await async_trading.fetch_prices_concurrent(client, symbols)
    
    # Event-driven architecture
    event_bus = AsyncEventBus()
    event_bus.subscribe('price_update', on_price_update)
    await event_bus.publish('price_update', {'symbol': 'BTC', 'price': 50000})
    
    # Rate limiting
    rate_limiter = RateLimiter(max_calls=10, period=1.0)
    async with rate_limiter:
        # API call
        pass

asyncio.run(main())
```

### Components

1. **AsyncTrading**: Concurrent market data and orders
2. **AsyncEventBus**: Pub/sub event system
3. **RateLimiter**: API rate limiting

---

## Testing

Run the comprehensive test suite:

```bash
# All tests
pytest -v

# Specific module
pytest test_avellaneda_stoikov.py -v
pytest test_market_microstructure.py -v

# With coverage
pytest --cov=. --cov-report=html
```

---

## Configuration

Add to `.env`:

```bash
# Avellaneda-Stoikov
AS_RISK_AVERSION=0.1
AS_TIME_HORIZON_MINUTES=60
AS_MAX_INVENTORY=5

# Microstructure
MICROSTRUCTURE_HISTORY_LENGTH=100

# Delta Hedging
DELTA_THRESHOLD=0.1
HEDGE_SYMBOL=BTCUSDT

# Funding Arbitrage
MIN_FUNDING_RATE=0.01
MIN_BASIS_BPS=10

# Paper Trading
PAPER_TRADING_MODE=false
PAPER_INITIAL_BALANCE=10000

# Observability
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
PROMETHEUS_PORT=8000

# Async
MAX_ASYNC_WORKERS=10
```

---

## Performance Considerations

1. **Avellaneda-Stoikov**: Low latency, suitable for HFT
2. **Microstructure**: Moderate overhead, run at 1-10Hz
3. **Delta Hedging**: Low frequency, check every 1-15 minutes
4. **SOR**: Sub-second routing decisions
5. **Async**: 5-10x throughput improvement for I/O operations

---

## References

- Avellaneda, M., & Stoikov, S. (2008). "High-frequency trading in a limit order book"
- Kyle, A. S. (1985). "Continuous Auctions and Insider Trading"
- Cont, R., et al. (2013). "The Price Impact of Order Book Events"

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/loureed691/RAD/issues
- Documentation: See README.md and individual module files
