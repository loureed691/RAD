# Training ML Model with Historical Data

This guide explains how to train the ML model with historical trading data to improve prediction accuracy before live trading.

## Overview

The ML model can now be trained with historical OHLCV (Open, High, Low, Close, Volume) data from CSV files or directly from the exchange. This allows you to:

- Train the model before starting live trading
- Improve prediction accuracy with real market patterns
- Test different timeframes and trading pairs
- Build a robust model with diverse market conditions

## Quick Start

### Method 1: Fetch and Train Automatically

Use the provided scripts to fetch historical data and train your model:

```bash
# Step 1: Fetch historical data from KuCoin
python fetch_historical_data.py

# This will prompt you for:
# - Symbol (e.g., BTC/USDT:USDT)
# - Timeframe (e.g., 1h, 4h, 1d)
# - Number of days to fetch (e.g., 30)

# Step 2: Train the model with the fetched data
python train_with_historical_data.py

# This will automatically find and use the CSV files
```

### Method 2: Use Your Own CSV Data

If you have your own historical data in CSV format:

```bash
python train_with_historical_data.py path/to/your/data.csv
```

**CSV Requirements:**
- Must have columns: `timestamp`, `open`, `high`, `low`, `close`, `volume`
- Timestamp should be in milliseconds (Unix epoch)
- All price columns should be numeric
- At least 100 candles recommended for meaningful training

## Command Line Usage

### Fetch Historical Data

```bash
# Fetch with command line arguments
python fetch_historical_data.py "BTC/USDT:USDT" "1h" 30

# Arguments:
# 1. Symbol (trading pair)
# 2. Timeframe (1h, 4h, 1d, etc.)
# 3. Days back (number of days of history)
```

### Train Model

```bash
# Train with a specific CSV file
python train_with_historical_data.py historical_data/BTC_USDT_USDT_1h_30days.csv

# Train with a custom model path
python train_with_historical_data.py data.csv models/custom_model.pkl

# Train with multiple files (interactive)
python train_with_historical_data.py
# Then select option 2
```

## Programmatic Usage

You can also use the ML model's methods directly in your own scripts:

```python
from ml_model import MLModel
import pandas as pd

# Initialize model
model = MLModel('models/signal_model.pkl')

# Load historical data from CSV
historical_data = model.load_historical_data_from_csv('data/btc_1h.csv')

# Train with the data
success = model.train_with_historical_data(historical_data, min_samples=100)

if success:
    print("Model trained successfully!")
    print(f"Training samples: {len(model.training_data)}")
else:
    print("Training failed")
```

### Training with Exchange Data

```python
from ml_model import MLModel
from kucoin_client import KuCoinClient
from config import Config
import pandas as pd

# Initialize client
client = KuCoinClient(Config.API_KEY, Config.API_SECRET, Config.API_PASSPHRASE)

# Fetch historical data
ohlcv = client.get_ohlcv('BTC/USDT:USDT', timeframe='1h', limit=500)

# Train model
model = MLModel()
success = model.train_with_historical_data(ohlcv, min_samples=100)
```

## Understanding the Training Process

### What Happens During Training

1. **Data Loading**: Historical OHLCV data is loaded from CSV or list
2. **Indicator Calculation**: Technical indicators (RSI, MACD, Bollinger Bands, etc.) are calculated for each candle
3. **Label Generation**: Labels are created based on future price movement:
   - Label 1 (BUY): Price increased >0.5% in next candle
   - Label 2 (SELL): Price decreased >0.5% in next candle
   - Label 0 (HOLD): Price stayed relatively flat
4. **Feature Extraction**: 26 features are extracted from indicators
5. **Model Training**: Gradient Boosting classifier is trained with the data
6. **Model Saving**: Trained model is saved to disk for future use

### Features Used (26 total)

**Base Indicators (11):**
- RSI, MACD, MACD Signal, MACD Difference
- Stochastic K & D
- Bollinger Band Width, Volume Ratio
- Momentum, Rate of Change (ROC), ATR

**Derived Features (15):**
- RSI strength, MACD strength, Stochastic momentum
- Volume surge, Volatility normalized
- RSI zones, MACD bullish/bearish signals
- Price position in Bollinger Bands
- Distance from EMAs, EMA separation
- RSI momentum, Volume trend, Volatility regime

## Best Practices

### Data Selection

1. **Timeframe**: Use the same timeframe you plan to trade on (typically 1h or 4h)
2. **History Length**: 
   - Minimum: 30 days (720 hourly candles)
   - Recommended: 60-90 days for diverse market conditions
   - Maximum: The model keeps only the last 10,000 training samples
3. **Market Conditions**: Include various market conditions (bull, bear, sideways)
4. **Multiple Pairs**: Train on multiple trading pairs for better generalization

### Training Strategy

```bash
# Example: Train on multiple pairs
python fetch_historical_data.py "BTC/USDT:USDT" "1h" 60
python fetch_historical_data.py "ETH/USDT:USDT" "1h" 60
python fetch_historical_data.py "SOL/USDT:USDT" "1h" 60

# Then train with all files
python train_with_historical_data.py
# Select option 2 for multiple files
```

### Model Validation

After training, check the logs for:
- **Training accuracy**: Should be >60% for decent performance
- **Test accuracy**: Should be close to training accuracy (within 5-10%)
- **Top features**: Review which indicators are most important

Example output:
```
Model trained - Train accuracy: 0.723, Test accuracy: 0.681
Top features: rsi:0.154, macd_diff:0.110, price_to_ema26:0.204
```

## Troubleshooting

### "Not enough historical data"
- Fetch more days of data (increase the days_back parameter)
- Use a shorter timeframe (1h instead of 4h)

### "Training failed" or low accuracy
- Increase the amount of historical data
- Include multiple trading pairs
- Try different timeframes

### CSV format errors
- Ensure your CSV has the required columns
- Check that timestamp is in milliseconds
- Verify all values are numeric (no missing data)

### Memory issues with large datasets
- The model automatically limits training data to 10,000 samples
- If you need more, modify `ml_model.py` line 198

## Advanced Usage

### Custom CSV Format

If your CSV has different column names:

```python
import pandas as pd
from ml_model import MLModel

# Load your CSV
df = pd.read_csv('your_data.csv')

# Rename columns to match expected format
df = df.rename(columns={
    'time': 'timestamp',
    'o': 'open',
    'h': 'high',
    'l': 'low',
    'c': 'close',
    'v': 'volume'
})

# Train
model = MLModel()
model.train_with_historical_data(df)
```

### Combining Real-Time and Historical Training

The model continues learning during live trading. Historical training gives it a head start:

```python
# 1. Train with historical data (one-time)
model = MLModel()
historical_data = model.load_historical_data_from_csv('historical_data/btc_1h.csv')
model.train_with_historical_data(historical_data)

# 2. Bot uses this model and continues learning
# As the bot trades, it calls model.record_outcome() which adds new samples
# The model retrains periodically with both historical and live data
```

## Examples

### Example 1: Quick Setup for BTC Trading

```bash
# Fetch 60 days of BTC hourly data
python fetch_historical_data.py "BTC/USDT:USDT" "1h" 60

# Train the model
python train_with_historical_data.py historical_data/BTC_USDT_USDT_1h_60days.csv

# Start trading
python start.py
```

### Example 2: Multi-Pair Training

```bash
# Fetch data for multiple pairs
for symbol in "BTC/USDT:USDT" "ETH/USDT:USDT" "SOL/USDT:USDT"; do
    python fetch_historical_data.py "$symbol" "1h" 45
done

# Train with all files
python train_with_historical_data.py
# Select option 2 to train with all CSV files
```

### Example 3: Different Timeframes

```bash
# 4-hour strategy with more history
python fetch_historical_data.py "BTC/USDT:USDT" "4h" 120

# Daily strategy
python fetch_historical_data.py "BTC/USDT:USDT" "1d" 365
```

## Integration with Bot

Once trained, the bot automatically uses the trained model:

1. The model is saved to `models/signal_model.pkl`
2. When you start the bot with `python start.py`, it loads this model
3. The model continues learning from live trading
4. Periodically retrain with new historical data to refresh patterns

## Performance Metrics

After training, you can check model performance:

```python
from ml_model import MLModel

model = MLModel()
metrics = model.get_performance_metrics()

print(f"Win rate: {metrics['win_rate']:.2%}")
print(f"Total trades: {metrics['total_trades']}")
print(f"Average profit: {metrics['avg_profit']:.2%}")
```

## Notes

- Training time depends on data size (typically 10-60 seconds for 30 days)
- The model is automatically saved after training
- You can retrain anytime with new data - it will merge with existing training data
- Historical data is stored in `historical_data/` directory
- Model files are stored in `models/` directory
- Training logs are saved to `logs/train_model.log`

## Next Steps

After training your model:
1. Review the training logs and accuracy metrics
2. Test the bot in paper trading mode first
3. Monitor performance and retrain periodically with new data
4. Experiment with different timeframes and pairs
5. Adjust `min_samples` parameter if needed (default: 100)

For more information, see:
- `ml_model.py` - Core ML model implementation
- `fetch_historical_data.py` - Data fetching script
- `train_with_historical_data.py` - Training script
- `test_historical_data_training.py` - Test examples
