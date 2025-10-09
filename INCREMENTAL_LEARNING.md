# Online/Incremental Learning Implementation

## Overview

The RAD trading bot now supports **Online/Incremental Learning** using the [River](https://riverml.xyz/) library. This enables the model to learn continuously from new data without requiring full retraining, making it more adaptive to changing market conditions.

## What is Online/Incremental Learning?

Traditional machine learning (batch learning):
- Collects all training data
- Trains a model on the entire dataset
- Model is static until next full retraining
- Requires significant memory and computation

Online/Incremental learning:
- Learns from one data point at a time
- Updates the model immediately after each trade
- Continuously adapts to new market patterns
- Lower memory footprint and faster updates

## Key Benefits

1. **Real-time Adaptation**: Model learns from each trade outcome immediately
2. **No Retraining Delays**: No need to wait for batch retraining cycles
3. **Memory Efficient**: Doesn't store large training datasets
4. **Concept Drift Detection**: ADWIN algorithm detects when market conditions change
5. **Always Up-to-Date**: Model reflects the latest market behavior

## Technical Implementation

### Architecture

The incremental learning system uses:

- **River Library**: Python library for online machine learning
- **ADWIN Bagging Classifier**: Adaptive Windowing ensemble method
  - Automatically detects concept drift (market regime changes)
  - Replaces underperforming models in the ensemble
- **Hoeffding Tree Classifiers**: Decision trees optimized for streaming data
  - Fast learning from single examples
  - Adaptive to changing patterns

### Features

The incremental model uses the same 31 features as the batch model:
- Base technical indicators (RSI, MACD, Stochastic, Bollinger Bands, etc.)
- Derived features (momentum strength, volatility regime, sentiment score)
- Multi-timeframe trend indicators
- Breakout and mean reversion signals

## Usage

### Enabling Incremental Learning

In your bot configuration:

```python
from ml_model import MLModel

# Enable incremental learning mode
ml_model = MLModel('models/signal_model.pkl', use_incremental=True)
```

### API Compatibility

The incremental model maintains full API compatibility with the batch model:

```python
# Predict signal
signal, confidence = ml_model.predict(indicators)

# Record trade outcome (automatically learns incrementally)
ml_model.record_outcome(indicators, signal, profit_loss)

# Get performance metrics
metrics = ml_model.get_performance_metrics()

# Get adaptive threshold
threshold = ml_model.get_adaptive_confidence_threshold()
```

### Direct Usage of Incremental Model

You can also use the incremental model directly:

```python
from incremental_ml_model import IncrementalMLModel

model = IncrementalMLModel('models/incremental_model.pkl')

# Make prediction
signal, confidence = model.predict(indicators)

# Learn from single trade (this is the core of online learning)
model.learn_one(indicators, signal, profit_loss)
```

## Performance Metrics

The incremental model tracks additional metrics:

```python
metrics = model.get_performance_metrics()

print(metrics['accuracy'])      # Real-time classification accuracy
print(metrics['f1_score'])      # F1 score for trade classification
print(metrics['precision'])     # Precision of predictions
print(metrics['recall'])        # Recall of predictions
print(metrics['win_rate'])      # Trading win rate
print(metrics['total_trades'])  # Number of trades learned from
```

## Configuration in config.py

Add to your `config.py`:

```python
class Config:
    # ML Model settings
    ML_MODEL_PATH = 'models/signal_model.pkl'
    USE_INCREMENTAL_LEARNING = True  # Enable incremental learning
    
    # Incremental learning parameters
    INCREMENTAL_GRACE_PERIOD = 50    # Number of samples before splitting
    INCREMENTAL_MAX_DEPTH = 10       # Maximum tree depth
    INCREMENTAL_N_MODELS = 10        # Number of models in ensemble
```

## Comparison: Batch vs Incremental Learning

| Feature | Batch Learning | Incremental Learning |
|---------|---------------|---------------------|
| Training Speed | Slow (full dataset) | Fast (single sample) |
| Memory Usage | High | Low |
| Adaptation | Periodic retraining | Continuous |
| Concept Drift | Manual detection | Automatic (ADWIN) |
| Prediction Latency | Low | Very Low |
| Data Storage | Stores history | Minimal storage |

## When to Use Each Mode

### Use Batch Learning When:
- You have limited historical data
- Market conditions are relatively stable
- You prefer periodic, controlled retraining
- You want to analyze training performance in detail

### Use Incremental Learning When:
- You want real-time adaptation to market changes
- Memory efficiency is important
- Market conditions change frequently
- You want to minimize retraining overhead
- You're trading in fast-moving markets

## Testing

Run the incremental learning tests:

```bash
python test_incremental_learning.py
```

Tests include:
- Model initialization and feature preparation
- Incremental learning from trade outcomes
- Model persistence (save/load)
- API compatibility with MLModel
- Comparison between batch and incremental modes

## Example: Complete Trading Loop

```python
from ml_model import MLModel
from indicators import Indicators

# Initialize with incremental learning
ml_model = MLModel('models/signal_model.pkl', use_incremental=True)

# Trading loop
while trading:
    # Get market data and calculate indicators
    ohlcv = client.get_ohlcv(symbol)
    df = Indicators.calculate_all(ohlcv)
    indicators = Indicators.get_latest_indicators(df)
    
    # Get ML signal
    signal, confidence = ml_model.predict(indicators)
    
    # Execute trade if confidence is high enough
    if confidence > ml_model.get_adaptive_confidence_threshold():
        execute_trade(signal)
        
        # Later, when trade closes...
        profit_loss = calculate_pnl()
        
        # Model learns immediately from this trade (incremental learning!)
        ml_model.record_outcome(indicators, signal, profit_loss)
        # No retraining needed - model already updated
```

## Advanced: Model Ensemble

You can combine batch and incremental learning:

```python
# Create both models
batch_model = MLModel('models/batch_model.pkl', use_incremental=False)
incr_model = MLModel('models/incr_model.pkl', use_incremental=True)

# Get predictions from both
batch_signal, batch_conf = batch_model.predict(indicators)
incr_signal, incr_conf = incr_model.predict(indicators)

# Combine predictions (e.g., take the higher confidence)
if incr_conf > batch_conf:
    final_signal, final_conf = incr_signal, incr_conf
else:
    final_signal, final_conf = batch_signal, batch_conf

# Record outcomes in both models
batch_model.record_outcome(indicators, final_signal, profit_loss)
incr_model.record_outcome(indicators, final_signal, profit_loss)
```

## Monitoring

Monitor incremental learning performance:

```python
# Get metrics
metrics = ml_model.get_performance_metrics()

# Log important metrics
logger.info(f"Incremental Model Stats:")
logger.info(f"  Total Trades: {metrics['total_trades']}")
logger.info(f"  Win Rate: {metrics['win_rate']:.2%}")
logger.info(f"  Accuracy: {metrics['accuracy']:.2%}")
logger.info(f"  F1 Score: {metrics['f1_score']:.2%}")
logger.info(f"  Recent Performance: {metrics.get('recent_trades', [])[-5:]}")
```

## Troubleshooting

### Model Not Learning
- Check that `record_outcome()` is being called after trades
- Verify profit_loss values are reasonable (-1 to 1 range)
- Ensure indicators dict has all required features

### Low Accuracy Initially
- Normal for online learning - needs ~50-100 samples to stabilize
- Model adapts over time, initial predictions may be uncertain
- Consider starting with a pre-trained batch model, then switching to incremental

### Memory Issues
- Incremental learning should use minimal memory
- If issues persist, check for memory leaks in data pipelines
- River models are designed to be memory-efficient

## References

- [River Library Documentation](https://riverml.xyz/)
- [ADWIN Algorithm Paper](https://www.cs.waikato.ac.nz/~abifet/ADWIN.pdf)
- [Hoeffding Trees](https://homes.cs.washington.edu/~pedrod/papers/kdd00.pdf)

## Future Enhancements

Potential improvements to explore:
- Multiple incremental models with voting
- Adaptive learning rate based on market volatility
- Feature importance tracking in real-time
- Automatic hyperparameter tuning for River models
- Integration with other River algorithms (PARegressor, AMRules, etc.)
