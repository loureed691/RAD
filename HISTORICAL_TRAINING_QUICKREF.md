# Historical Data Training - Quick Reference

## Quick Start (3 Steps)

### 1. Fetch Historical Data
```bash
python fetch_historical_data.py "BTC/USDT:USDT" "1h" 30
```
- **Symbol**: Trading pair (e.g., BTC/USDT:USDT, ETH/USDT:USDT)
- **Timeframe**: 1h, 4h, 1d, etc.
- **Days**: Number of days of historical data

### 2. Train the Model
```bash
python train_with_historical_data.py
```
- Select option 1 for a single CSV file
- Select option 2 to train with all CSV files in historical_data/

### 3. Start Trading
```bash
python start.py
```
- The bot automatically loads and uses the trained model

## Common Commands

### Fetch Multiple Pairs
```bash
python fetch_historical_data.py "BTC/USDT:USDT" "1h" 60
python fetch_historical_data.py "ETH/USDT:USDT" "1h" 60
python fetch_historical_data.py "SOL/USDT:USDT" "1h" 60
```

### Train with Specific File
```bash
python train_with_historical_data.py historical_data/BTC_USDT_USDT_1h_30days.csv
```

### Train with All Files
```bash
python train_with_historical_data.py
# Then select option 2
```

## Programmatic Usage

### Simple Training
```python
from ml_model import MLModel

model = MLModel()
historical_data = model.load_historical_data_from_csv('data.csv')
model.train_with_historical_data(historical_data)
```

### Train with Exchange Data
```python
from ml_model import MLModel
from kucoin_client import KuCoinClient
from config import Config

client = KuCoinClient(Config.API_KEY, Config.API_SECRET, Config.API_PASSPHRASE)
ohlcv = client.get_ohlcv('BTC/USDT:USDT', '1h', 500)

model = MLModel()
model.train_with_historical_data(ohlcv)
```

## CSV Format

Required columns (case-insensitive):
- `timestamp` - Unix timestamp in milliseconds
- `open` - Opening price
- `high` - Highest price
- `low` - Lowest price
- `close` - Closing price
- `volume` - Trading volume

Example:
```csv
timestamp,open,high,low,close,volume
1696118400000,27543.2,27650.5,27500.1,27612.3,1234.56
1696122000000,27612.3,27680.0,27590.0,27655.8,1345.67
```

## Recommendations

### Data Amount
- **Minimum**: 30 days (720 hourly candles)
- **Recommended**: 60-90 days
- **Maximum**: Model keeps last 10,000 training samples

### Timeframes
- **1h**: Good for short-term trading, day trading
- **4h**: Good for swing trading
- **1d**: Good for position trading

### Multiple Pairs
Train on 3-5 different pairs for better generalization:
```bash
for symbol in BTC ETH SOL BNB MATIC; do
    python fetch_historical_data.py "${symbol}/USDT:USDT" "1h" 45
done
python train_with_historical_data.py
# Select option 2
```

## Validation

### Check Training Results
Look for these in the logs:
- **Train accuracy**: Should be >60%
- **Test accuracy**: Should be within 5-10% of train accuracy
- **Top features**: Shows which indicators matter most

Example output:
```
Model trained - Train accuracy: 0.723, Test accuracy: 0.681
Top features: rsi:0.154, macd_diff:0.110, price_to_ema26:0.204
```

### Test Predictions
```python
from ml_model import MLModel

model = MLModel()
sample_indicators = {
    'rsi': 55, 'macd': 0.5, 'macd_signal': 0.3,
    'stoch_k': 60, 'stoch_d': 55,
    # ... other indicators
}
signal, confidence = model.predict(sample_indicators)
print(f"Signal: {signal}, Confidence: {confidence:.2%}")
```

## Troubleshooting

### "Not enough historical data"
```bash
# Fetch more days
python fetch_historical_data.py "BTC/USDT:USDT" "1h" 60
```

### "CSV missing required columns"
Check your CSV has: timestamp, open, high, low, close, volume

### Low accuracy (<50%)
- Fetch more historical data (60+ days)
- Train on multiple pairs
- Try different timeframes

### Training takes too long
- Normal for large datasets (30-60 seconds for 30 days)
- Model auto-limits to 10,000 samples

## Files & Directories

- `historical_data/` - CSV files with historical data
- `models/` - Trained model files (.pkl)
- `logs/train_model.log` - Training logs
- `logs/fetch_data.log` - Data fetching logs

## Demo & Tests

### Run Demo
```bash
python demo_historical_training.py
```
Shows complete workflow with sample data

### Run Tests
```bash
python test_historical_data_training.py
```
Validates all historical training functionality

## Integration with Bot

The bot automatically:
1. Loads the trained model on startup
2. Uses it for predictions
3. Continues learning from live trades
4. Saves updates periodically

To refresh the model with new data:
```bash
python fetch_historical_data.py "BTC/USDT:USDT" "1h" 30
python train_with_historical_data.py
```
Then restart the bot.

## Next Steps

1. **Read full docs**: `HISTORICAL_DATA_TRAINING.md`
2. **Run demo**: `python demo_historical_training.py`
3. **Fetch your data**: `python fetch_historical_data.py`
4. **Train model**: `python train_with_historical_data.py`
5. **Start bot**: `python start.py`

## Need Help?

- Check `HISTORICAL_DATA_TRAINING.md` for detailed documentation
- Review `test_historical_data_training.py` for code examples
- Run `demo_historical_training.py` to see it in action
