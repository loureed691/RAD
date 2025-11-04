# Avellaneda-Stoikov Market Making Guide

## Overview

This document describes the implementation of the Avellaneda-Stoikov market making strategy with microstructure enhancements, automatic delta hedging, and cross-venue support.

## Table of Contents

1. [Introduction](#introduction)
2. [Core Components](#core-components)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Advanced Features](#advanced-features)
6. [Exchange Connectors](#exchange-connectors)
7. [Backtesting](#backtesting)
8. [Best Practices](#best-practices)

## Introduction

### What is Market Making?

Market making is a trading strategy where you simultaneously quote bid and ask prices, earning the spread between them. Unlike directional trading, market makers aim to be inventory-neutral and profit from providing liquidity to the market.

### Avellaneda-Stoikov Model

The Avellaneda-Stoikov (A-S) model is a mathematically rigorous approach to market making that:

- Dynamically adjusts spreads based on inventory and risk
- Accounts for adverse selection
- Manages inventory risk through optimal pricing
- Maximizes expected utility while controlling risk

Reference: "High-frequency trading in a limit order book" (Avellaneda & Stoikov, 2008)

## Core Components

### 1. Avellaneda-Stoikov Market Maker

**File:** `avellaneda_stoikov.py`

The core market making engine that generates optimal bid/ask quotes.

**Key Features:**
- Inventory-aware pricing (skews quotes to manage inventory)
- Volatility-adaptive spreads
- Microstructure signal integration
- Risk aversion parameter tuning

**Example Usage:**

```python
from avellaneda_stoikov import AvellanedaStoikovMarketMaker

# Initialize market maker
mm = AvellanedaStoikovMarketMaker(
    risk_aversion=0.1,        # Gamma parameter (0.01-1.0)
    terminal_time=1.0,        # Time horizon in years
    target_inventory=0.0,     # Target position (0 = neutral)
    max_inventory=10.0,       # Maximum inventory deviation
    min_spread=0.0001,        # Minimum spread (0.01%)
    max_spread=0.01           # Maximum spread (1%)
)

# Update with market data
mm.update_market_data(
    mid_price=50000.0,
    volatility=0.5,
    inventory=current_position,
    microprice=49999.5,          # Optional: more accurate than mid
    order_flow_imbalance=0.3,    # Optional: -1 to 1
    kyle_lambda=0.001,           # Optional: price impact
    short_volatility=0.6         # Optional: short-term vol
)

# Get optimal quotes
bid_price, ask_price = mm.compute_quotes()
```

### 2. Market Microstructure Analysis

**File:** `market_microstructure_2026.py`

Enhanced with additional signals for market making:

**New Methods:**
- `calculate_microprice()` - More accurate reference price
- `calculate_kyle_lambda()` - Price impact coefficient
- `calculate_queue_imbalance()` - Order flow imbalance
- `calculate_short_horizon_volatility()` - Short-term vol estimate

**Example:**

```python
from market_microstructure_2026 import MarketMicrostructure2026

ms = MarketMicrostructure2026()

# Get all signals at once
signals = ms.get_microstructure_signals(
    orderbook=current_orderbook,
    trades=recent_trades,
    volume_24h=volume_usd
)

# Signals include:
# - microprice
# - kyle_lambda
# - queue_imbalance
# - short_horizon_volatility
# - spread_bps
```

### 3. Delta Hedger

**File:** `delta_hedger.py`

Automatically maintains near-flat delta exposure by hedging inventory.

**Features:**
- Threshold-based hedging
- Cost-aware execution
- Smart timing (opportunistic vs. forced)
- Cross-venue support

**Example:**

```python
from delta_hedger import DeltaHedger

hedger = DeltaHedger(
    hedge_threshold=5.0,      # Hedge when |inventory| > 5
    target_delta=0.0,         # Target position
    hedge_ratio=0.8,          # Hedge 80% of excess
    min_hedge_size=0.1,       # Minimum hedge size
    max_hedge_latency=60.0    # Force hedge after 60s
)

# Update inventory
hedger.update_inventory(current_position)

# Check if hedging needed
if hedger.should_hedge():
    rec = hedger.get_hedge_recommendation(
        current_price=50000.0,
        microprice=49999.5
    )
    
    # Execute hedge
    # rec contains: side, hedge_size, urgency, strategy, limit_price
```

### 4. Funding Arbitrage

**File:** `funding_arbitrage.py`

Captures funding rate premiums and basis between markets.

**Strategies:**
1. **Perp-Spot Arbitrage:** Long spot + short perp (or vice versa)
2. **Cross-Venue Arbitrage:** Exploit funding differences between exchanges

**Example:**

```python
from funding_arbitrage import FundingArbitrage

arb = FundingArbitrage(
    min_funding_rate=0.0001,  # 0.01% per period
    min_apr_threshold=0.05,   # 5% annual minimum
    max_basis_risk=0.002      # 0.2% max basis risk
)

# Evaluate opportunity
opp = arb.evaluate_perp_spot_opportunity(
    perp_price=50100.0,
    spot_price=50000.0,
    funding_rate=0.0005,      # 0.05% = ~54% APR
    predicted_funding=0.0004
)

if opp:
    # Open position
    pos_id = arb.open_position(opp, position_size=10000.0)
```

## Quick Start

### Basic Market Making Setup

```python
from avellaneda_stoikov import AvellanedaStoikovMarketMaker
from delta_hedger import DeltaHedger
from market_microstructure_2026 import MarketMicrostructure2026

# 1. Initialize components
mm = AvellanedaStoikovMarketMaker(
    risk_aversion=0.1,
    max_inventory=10.0
)

hedger = DeltaHedger(
    hedge_threshold=5.0,
    hedge_ratio=0.8
)

ms = MarketMicrostructure2026()

# 2. Main loop
while trading:
    # Fetch market data
    orderbook = exchange.get_orderbook(symbol)
    trades = exchange.get_recent_trades(symbol)
    
    # Get microstructure signals
    signals = ms.get_microstructure_signals(orderbook, trades)
    
    # Update market maker
    mm.update_market_data(
        mid_price=mid_price,
        volatility=volatility,
        inventory=current_position,
        microprice=signals['microprice'],
        order_flow_imbalance=signals['queue_imbalance'],
        kyle_lambda=signals['kyle_lambda']
    )
    
    # Get quotes
    bid, ask = mm.compute_quotes()
    
    # Place orders
    if mm.should_quote_side('bid'):
        place_limit_order('buy', bid, size)
    
    if mm.should_quote_side('ask'):
        place_limit_order('sell', ask, size)
    
    # Check hedging
    hedger.update_inventory(current_position)
    if hedger.should_hedge():
        hedge_rec = hedger.get_hedge_recommendation(mid_price)
        execute_hedge(hedge_rec)
    
    time.sleep(update_interval)
```

## Configuration

### Risk Aversion (γ)

Controls how aggressive the market maker is:

- **γ = 0.01:** Very aggressive (tight spreads, high inventory tolerance)
- **γ = 0.1:** Balanced (moderate spreads, moderate inventory)
- **γ = 1.0:** Very conservative (wide spreads, low inventory)

**Recommendation:** Start with γ = 0.1 and adjust based on:
- Market volatility (higher vol → higher γ)
- Capital size (smaller capital → higher γ)
- Risk tolerance

### Inventory Limits

Set `max_inventory` based on:
- Position size limits
- Liquidation risk
- Capital allocation

**Example:** For $100k capital:
```python
max_inventory = 10.0  # 10 units
# At $50k/unit = $500k notional = 5x leverage
```

### Spread Bounds

```python
min_spread = 0.0001  # 0.01% = 1 bps minimum
max_spread = 0.01    # 1% = 100 bps maximum
```

Adjust based on:
- Market liquidity
- Trading fees
- Competition

## Advanced Features

### Funding Rate Capture

Combine market making with funding arbitrage:

```python
from funding_arbitrage import FundingArbitrage

# Setup funding arb
arb = FundingArbitrage(min_apr_threshold=0.05)

# In trading loop
funding_rate = exchange.get_funding_rate(symbol)
funding_apr = arb.calculate_funding_apr(funding_rate)

if funding_apr > 0.05:
    # Evaluate opportunity
    opp = arb.evaluate_perp_spot_opportunity(...)
    if opp:
        # Open funding position
        pos_id = arb.open_position(opp, size)
```

### Cross-Venue Trading

Use the Smart Order Router to execute across multiple venues:

```python
from exchange_connectors.venue_manager import VenueManager
from smart_order_router import SmartOrderRouter

# Setup venues
venue_manager = VenueManager()
venue_manager.add_venue('binance', binance_connector)
venue_manager.add_venue('okx', okx_connector)

# Connect all
venue_manager.connect_all()

# Setup SOR
sor = SmartOrderRouter(venue_manager)

# Route order
routing_plan = sor.route_order(
    symbol='BTC/USDT',
    side='buy',
    amount=1.0,
    strategy='min_cost'  # or 'best_price', 'split'
)

# Execute
results = sor.execute_routing_plan(
    symbol='BTC/USDT',
    side='buy',
    routing_plan=routing_plan,
    order_type='limit'
)
```

## Exchange Connectors

### CEX Connector (CCXT)

Supports multiple centralized exchanges:

```python
from exchange_connectors.cex_connector import CEXConnector

# Binance Futures
binance = CEXConnector(
    exchange_id='binancefutures',
    api_key=API_KEY,
    api_secret=API_SECRET,
    testnet=False
)
binance.connect()

# KuCoin Futures
kucoin = CEXConnector(
    exchange_id='kucoinfutures',
    api_key=API_KEY,
    api_secret=API_SECRET,
    api_passphrase=API_PASSPHRASE
)
kucoin.connect()
```

### DEX Connectors (Stubs)

**dYdX v4** and **Hyperliquid** connectors are provided as stubs with integration guides.

To implement:
1. Install respective SDK
2. Follow integration guide in connector file
3. Implement methods using SDK

## Backtesting

### Market Making Backtest

Use specialized backtesting for market making:

```python
from market_making_backtest import MarketMakingBacktest
from avellaneda_stoikov import AvellanedaStoikovMarketMaker

# Setup backtest
backtest = MarketMakingBacktest(
    initial_capital=100000.0,
    maker_fee=0.0002,
    taker_fee=0.0006
)

# Setup strategy
mm = AvellanedaStoikovMarketMaker(
    risk_aversion=0.1,
    max_inventory=10.0
)

# Run backtest
results = backtest.run_backtest(
    market_data=historical_df,
    market_maker=mm,
    hedger=hedger,
    apply_funding=True
)

# Results include:
# - total_pnl, sharpe_ratio, max_drawdown
# - maker_fills, taker_fills, win_rate
# - total_fees_paid, total_funding_paid
# - equity_curve, inventory_curve
```

### Preparing Market Data

Required columns for backtesting:
```python
df = pd.DataFrame({
    'timestamp': timestamps,
    'bid': bid_prices,
    'ask': ask_prices,
    'volume': volumes,
    'volatility': volatilities,
    'orderbook_snapshot': orderbooks,  # List of dicts
    'microprice': microprices,         # Optional
    'ofi': order_flow_imbalances,      # Optional
    'kyle_lambda': kyle_lambdas,       # Optional
    'short_vol': short_volatilities    # Optional
})
```

## Best Practices

### 1. Start Small

Begin with small position sizes and tight inventory limits:
```python
max_inventory = 1.0  # Very small
risk_aversion = 0.5  # Conservative
```

### 2. Monitor Metrics

Track key metrics:
- **Inventory:** Should oscillate around 0
- **Fill rate:** Target 30-50% of quotes
- **Spread captured:** Should exceed fees + funding
- **Sharpe ratio:** Target > 2.0

### 3. Risk Management

Always implement:
- Maximum inventory limits
- Automatic delta hedging
- Stop-loss on large adverse moves
- Position timeout (don't hold indefinitely)

### 4. Fee Awareness

Ensure spreads cover costs:
```python
min_spread >= 2 * maker_fee + safety_margin
# E.g., maker_fee = 0.02% -> min_spread >= 0.05%
```

### 5. Market Selection

Choose markets with:
- Tight spreads (< 0.1%)
- High volume (> $1M daily)
- Stable funding rates
- Low Kyle's lambda (< 0.01)

### 6. Regular Rebalancing

- Hedge inventory regularly (every 5-10 minutes)
- Cancel and replace quotes frequently (every 10-30 seconds)
- Adjust parameters based on market conditions

### 7. Testing

Always:
- Backtest thoroughly with realistic fill assumptions
- Paper trade before live deployment
- Start with small capital
- Monitor closely for first days

## Troubleshooting

### High Inventory

**Problem:** Inventory keeps growing in one direction

**Solutions:**
- Reduce `max_inventory`
- Increase `risk_aversion` (γ)
- Strengthen hedging (lower `hedge_threshold`)
- Check quote skewing logic

### Low Fill Rate

**Problem:** Orders not filling

**Solutions:**
- Reduce spreads (lower `risk_aversion`)
- Check if quotes are competitive
- Verify order placement is correct
- Ensure sufficient order book depth

### Losses from Adverse Selection

**Problem:** Losing money on fills

**Solutions:**
- Increase spreads
- Use microprice instead of mid-price
- Cancel quotes during high volatility
- Implement adverse selection protection

### High Hedging Costs

**Problem:** Too much hedging cost

**Solutions:**
- Increase `hedge_threshold`
- Reduce `hedge_ratio`
- Use opportunistic hedging strategy
- Consider funding arbitrage instead

## Further Reading

### Academic Papers

1. Avellaneda & Stoikov (2008) - "High-frequency trading in a limit order book"
2. Kyle (1985) - "Continuous Auctions and Insider Trading"
3. Glosten & Milgrom (1985) - "Bid, ask and transaction prices in a specialist market"

### Implementation Resources

- CCXT Documentation: https://docs.ccxt.com/
- dYdX v4 Docs: https://docs.dydx.exchange/
- Hyperliquid Docs: https://hyperliquid.gitbook.io/

### Community

For questions and discussions:
- GitHub Issues: [repository]/issues
- Trading Strategy Discord: [link]

---

**Disclaimer:** Market making involves significant risk. This implementation is for educational purposes. Always test thoroughly and understand the risks before deploying with real capital.
