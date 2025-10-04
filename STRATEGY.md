# Trading Strategy Documentation

## Overview

The RAD trading bot implements a multi-layered trading strategy that combines technical analysis, risk management, and machine learning for automated KuCoin Futures trading.

## Signal Generation Strategy

### Technical Indicators Used

1. **Trend Following**
   - EMA 12 and EMA 26 crossovers
   - SMA 20 and SMA 50 for longer-term trends
   - Trend strength confirmation

2. **Momentum Indicators**
   - **RSI (Relative Strength Index)**
     - Oversold: < 30 (Buy signal)
     - Overbought: > 70 (Sell signal)
     - Neutral: 40-60
   
   - **MACD (Moving Average Convergence Divergence)**
     - Bullish: MACD > Signal line and MACD diff > 0
     - Bearish: MACD < Signal line and MACD diff < 0
   
   - **Stochastic Oscillator**
     - Bullish crossover: %K < 20 and %K crosses above %D
     - Bearish crossover: %K > 80 and %K crosses below %D

3. **Volatility Indicators**
   - **Bollinger Bands**
     - Buy signal: Price below lower band
     - Sell signal: Price above upper band
     - Band width for volatility measurement
   
   - **ATR (Average True Range)**
     - Used for dynamic stop loss calculation
     - Higher ATR = wider stops

4. **Volume Analysis**
   - Volume ratio vs 20-period SMA
   - High volume (>1.5x) confirms signals
   - Low volume signals are treated with caution

### Signal Scoring System

Each indicator contributes to an overall signal score:
- Trend indicators: 2 points
- MACD: 2 points
- RSI: 1.5 points
- Stochastic: 1 point
- Bollinger Bands: 1 point
- Volume: 0.5 points (bonus)
- Momentum: 1 point

**Total possible points: ~9-10**

Confidence = (Signal points / Total points)
- Minimum confidence for trading: 60%

## Position Management

### Entry Strategy

1. **Market Scanning**
   - Scan all active KuCoin Futures pairs in parallel
   - Calculate indicators and signals for each
   - Score and rank all opportunities
   - Select top N pairs (default: top 5)

2. **Position Sizing**
   ```
   Risk Amount = Account Balance × Risk Per Trade
   Price Distance = |Entry Price - Stop Loss| / Entry Price
   Position Value = Risk Amount / (Price Distance × Leverage)
   Position Size = min(Position Value, Max Position Size) / Entry Price
   ```

3. **Leverage Selection**
   - Base leverage: 10x
   - Reduced to 7x for moderate volatility (>3%)
   - Reduced to 5x for high volatility (>5%)
   - Further reduced for low confidence signals (<70%)

### Exit Strategy

1. **Stop Loss**
   - Dynamic based on market volatility (ATR)
   - Base: 3% from entry
   - Adjusted for volatility: +0-5%
   - Range: 2-10% from entry

2. **Take Profit (Dynamic)**
   - Initial target: 2x stop loss distance
   - Example: 5% stop = 10% take profit target
   - **Dynamic Adjustments**:
     - **Momentum Extension**: Strong momentum (>3%) extends target by 50%
     - **Trend Extension**: Strong trend (>0.7) adds 30% to target
     - **Volatility Extension**: High volatility (>5%) adds 20% to capture bigger moves
     - **Profit Protection**: Already profitable positions cap extensions at 20%
   - Only adjusts upward (more favorable direction)
   - Adapts to market conditions to maximize profit potential

3. **Trailing Stop (Adaptive)**
   - Automatically adapts to market conditions
   - Base trail: 2% from highest/lowest price
   - **Volatility Adjustment**: 
     - High volatility (>5%): Widens by 50% to avoid premature stops
     - Low volatility (<2%): Tightens by 20% for better risk/reward
   - **Profit-Based Adjustment**:
     - >10% profit: Tightens to 70% to lock in gains
     - >5% profit: Moderate tightening to 85%
   - **Momentum Adjustment**:
     - Strong momentum (>3%): Widens by 20% to let trend run
     - Weak momentum (<1%): Tightens by 10% when momentum fades
   - Only moves in favorable direction
   - Adapts between 0.5% and 5% range based on conditions

### Position Monitoring

- Continuous monitoring every cycle (default: 60s)
- **Adaptive trailing stops** with real-time volatility and momentum analysis
- **Dynamic take profit** adjustments based on trend strength
- **Max Favorable Excursion (MFE)** tracking for performance analysis
- Check stop loss and take profit conditions
- Record outcomes for ML model training

#### Real-Time Adaptations

For each position update cycle, the bot:
1. Fetches current market data (OHLCV for past 100 periods)
2. Calculates technical indicators (volatility, momentum, trend strength)
3. Adjusts trailing stop based on:
   - Market volatility (BB width or ATR)
   - Current price momentum
   - Position profit level
4. Adjusts take profit based on:
   - Momentum strength
   - Trend strength (SMA divergence)
   - Market volatility
5. Tracks maximum favorable excursion for each position
6. Executes exits when conditions are met

## Risk Management

### Position Limits

- **Max Open Positions**: 3 (configurable)
- **Max Position Size**: $1000 USDT (configurable)
- **Risk Per Trade**: 2% of account balance (configurable)
- **Min Balance**: $100 USDT to open new positions

### Risk Controls

1. **Pre-Trade Validation**
   - Check available balance
   - Verify position count limit
   - Validate signal confidence
   - Confirm market conditions

2. **Position Sizing**
   - Never risk more than configured % per trade
   - Cap position size at maximum limit
   - Account for leverage in calculations
   - Scale down for low confidence signals

3. **Leverage Management**
   - Dynamic adjustment based on volatility
   - Reduced leverage for uncertain signals
   - Maximum leverage cap (10x)

## Machine Learning Component

### Self-Learning Process

1. **Data Collection**
   - Record all entry indicators
   - Track entry signal (BUY/SELL)
   - Record exit profit/loss
   - Store timestamp for analysis

2. **Labeling**
   - Profitable trades (>1% P/L): Positive label
   - Losing trades (<-1% P/L): Negative label
   - Neutral trades: Neutral label

3. **Training**
   - Minimum samples required: 100
   - Algorithm: Random Forest Classifier
   - Train/Test split: 80/20
   - Periodic retraining: Every 24 hours (configurable)

4. **Prediction**
   - Validates rule-based signals
   - Provides confidence score
   - Can override low-confidence signals
   - Improves accuracy over time

### Feature Engineering

Features used in ML model:
- RSI
- MACD, MACD Signal, MACD Difference
- Stochastic %K and %D
- Bollinger Band Width
- Volume Ratio
- Momentum
- Rate of Change (ROC)
- ATR

## Performance Optimization

### Parallel Processing

- Market scanning uses ThreadPoolExecutor
- Concurrent analysis of multiple pairs
- Default: 10 worker threads
- Significantly reduces scan time

### API Rate Limiting

- ccxt built-in rate limiting enabled
- Prevents API bans
- Automatic retry on rate limit errors
- Exponential backoff on failures

### Error Handling

- Comprehensive try-catch blocks
- Graceful degradation on errors
- Logging of all errors for debugging
- Automatic recovery from transient failures

## Monitoring and Logging

### Log Levels

- **INFO**: Normal operations (trades, signals, positions)
- **WARNING**: Important notices (balance issues, limits reached)
- **ERROR**: Errors and exceptions
- **DEBUG**: Detailed diagnostic information

### Key Metrics Tracked

- Number of trades executed
- Win rate and profit factor
- Average profit/loss per trade
- Position durations
- Signal confidence levels
- API errors and retries

## Best Practices

### Initial Setup

1. Start with small position sizes
2. Monitor for first 24-48 hours
3. Adjust risk parameters based on performance
4. Let ML model accumulate data before relying on it

### Ongoing Operation

1. Review logs daily
2. Monitor win rate and profit factor
3. Adjust parameters for market conditions
4. Retrain ML model with sufficient data
5. Keep API keys secure

### Risk Management

1. Never invest more than you can afford to lose
2. Start with lower leverage (5x) until confident
3. Reduce position sizes during high volatility
4. Keep sufficient balance for margin calls
5. Monitor open positions regularly

## Advanced Configuration

### Customization Options

All parameters in `.env` can be adjusted:
- Trading intervals
- Risk parameters
- Position limits
- Leverage settings
- ML retraining frequency
- Trailing stop percentages

### Strategy Modifications

The signal generation logic in `signals.py` can be customized:
- Add new indicators
- Adjust indicator weights
- Change confidence thresholds
- Implement custom logic

## Troubleshooting

### Common Issues

1. **No trades executing**
   - Lower confidence threshold
   - Increase check interval
   - Verify sufficient balance
   - Check if max positions reached

2. **Frequent stop losses**
   - Increase stop loss percentage
   - Reduce leverage
   - Increase trailing stop distance
   - Improve signal selection criteria

3. **API errors**
   - Check API credentials
   - Verify API permissions
   - Check rate limiting settings
   - Review exchange status

## Disclaimer

This bot is for educational purposes. Trading cryptocurrency futures involves substantial risk. Past performance does not guarantee future results. Always trade responsibly.
