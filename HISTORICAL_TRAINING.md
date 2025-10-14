# Historical Training Feature

## Overview

The bot now supports automatic background training with historical data from KuCoin. This feature allows the ML model to learn from past market patterns before it starts live trading.

## How It Works

1. **On Startup**: When the bot starts, it launches a background thread that fetches historical OHLCV data from KuCoin
2. **Data Processing**: For each candle, the bot:
   - Calculates technical indicators (RSI, MACD, Bollinger Bands, etc.)
   - Looks ahead 5 candles to determine if the price went up or down
   - Labels the data as BUY, SELL, or HOLD based on the outcome
3. **Model Training**: Once enough samples are collected (default: 100), the bot trains the ML model
4. **Continuous Operation**: The bot continues with normal trading operations while training runs in the background

## Configuration

Add these environment variables to your `.env` file:

```bash
# Enable/disable historical training (default: true)
ENABLE_HISTORICAL_TRAINING=true

# Symbols to use for training (comma-separated)
# Default: BTC/USDT:USDT,ETH/USDT:USDT
HISTORICAL_TRAINING_SYMBOLS=BTC/USDT:USDT,ETH/USDT:USDT,SOL/USDT:USDT

# Timeframe for historical data (default: 1h)
# Options: 1m, 5m, 15m, 30m, 1h, 4h, 1d
HISTORICAL_TRAINING_TIMEFRAME=1h

# Number of days of history to fetch (default: 30)
HISTORICAL_TRAINING_DAYS=30

# Minimum samples required before training (default: 100)
HISTORICAL_TRAINING_MIN_SAMPLES=100
```

## Benefits

1. **Faster Learning**: The bot starts with pre-trained knowledge instead of learning from scratch
2. **Better Initial Decisions**: More accurate predictions from the first trade
3. **Diverse Training Data**: Learns from multiple market conditions and symbols
4. **Non-Intrusive**: Runs in the background without affecting trading operations

## Logging

The historical training process logs detailed information:

```
🎓 STARTING HISTORICAL TRAINING
Symbols: 3
Timeframe: 1h
History: 30 days
Min samples: 100
============================================================
Processing BTC/USDT:USDT...
✓ Fetched 720 candles for BTC/USDT:USDT
✓ Generated 350 training samples from BTC/USDT:USDT
Processing ETH/USDT:USDT...
✓ Fetched 720 candles for ETH/USDT:USDT
✓ Generated 340 training samples from ETH/USDT:USDT
============================================================
📊 Total training samples generated: 690
============================================================
🤖 Training ML model with historical data...
✅ Historical training completed successfully!
💾 Model saved to disk
```

## Smart Behavior

The bot intelligently handles training:

- **Skip if Trained**: If the model already exists with enough samples, historical training is skipped
- **Graceful Shutdown**: Training can be interrupted during shutdown without corrupting the model
- **Rate Limiting**: Small delays between symbol fetches to avoid API rate limits
- **Error Recovery**: Individual symbol failures don't stop the entire training process

## Technical Details

### Training Algorithm

The historical trainer uses a look-forward approach:

1. For each historical candle, calculate all technical indicators
2. Look ahead 5 candles to see the actual price movement
3. If price increased >1%, label as a BUY signal with profit = price_change
4. If price decreased >1%, label as a SELL signal with profit = abs(price_change)
5. Otherwise, skip as neutral/HOLD

This creates realistic training data that reflects actual trading outcomes.

### Model Integration

The historical training integrates seamlessly with the existing ML model:

- Uses the same feature extraction pipeline
- Records outcomes using the standard `record_outcome()` method
- Trains using the existing gradient boosting ensemble (XGBoost/LightGBM/CatBoost)
- Saves to the same model file for persistence

## Testing

Run the included test to verify the feature:

```bash
python test_historical_training.py
```

This test:
1. Verifies configuration loading
2. Tests historical data fetching
3. Tests training sample generation
4. Tests full model training
5. Verifies the model can make predictions

## Disabling the Feature

To disable historical training, set in your `.env`:

```bash
ENABLE_HISTORICAL_TRAINING=false
```

Or remove the environment variable entirely (it will still default to `true`).

## Performance Impact

- **Startup Time**: Adds 30-60 seconds during bot initialization
- **Memory**: Uses ~10-50 MB for historical data processing
- **CPU**: Training uses all available CPU cores but runs in background
- **API Calls**: Makes ~2-5 API calls per symbol (respects rate limits)

## Troubleshooting

### "Not enough training data"

Increase `HISTORICAL_TRAINING_DAYS` or add more symbols to `HISTORICAL_TRAINING_SYMBOLS`.

### "Failed to fetch historical data"

Check:
- Your API credentials are valid
- The symbol format is correct (must be futures format: `BTC/USDT:USDT`)
- Your API has permission to access historical data

### Training takes too long

Reduce:
- Number of days: `HISTORICAL_TRAINING_DAYS=7`
- Number of symbols: Use 1-2 major pairs only
- Timeframe: Use larger timeframes like `4h` or `1d`

## Example Configuration

For a balanced setup that works well for most users:

```bash
ENABLE_HISTORICAL_TRAINING=true
HISTORICAL_TRAINING_SYMBOLS=BTC/USDT:USDT,ETH/USDT:USDT
HISTORICAL_TRAINING_TIMEFRAME=1h
HISTORICAL_TRAINING_DAYS=14
HISTORICAL_TRAINING_MIN_SAMPLES=100
```

This fetches 2 weeks of hourly data from 2 major pairs, generating 200-300 training samples in about 30 seconds.
