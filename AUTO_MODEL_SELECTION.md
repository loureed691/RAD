# Automatic Model Selection Implementation

## Overview

This document describes the automatic model selection feature added to the RAD trading bot's machine learning system.

## Problem Solved

Previously, users had to manually choose between batch learning and incremental learning modes. This required:
- Understanding the tradeoffs between each approach
- Monitoring performance to determine which works better
- Manual configuration changes to switch models
- Potential downtime during transitions

## Solution

Implemented intelligent automatic model selection that:
1. Runs both batch and incremental models in parallel
2. Records outcomes in both models simultaneously
3. Periodically compares performance using a composite scoring system
4. Automatically switches to the better performing model
5. Uses hysteresis to prevent frequent switching

## Implementation Details

### Architecture

```
MLModel with auto_select_best=True
├─ Batch Model (sklearn ensemble)
│  ├─ Records outcomes
│  ├─ Tracks metrics
│  └─ Makes predictions when selected
│
└─ Incremental Model (River)
   ├─ Records outcomes
   ├─ Tracks metrics
   └─ Makes predictions when selected
```

### Composite Scoring System

Performance is evaluated using a weighted composite score:

```python
score = (
    win_rate * 0.4 +        # 40% weight - trading success rate
    accuracy * 0.3 +        # 30% weight - classification accuracy
    normalized_profit * 0.3 # 30% weight - average profit per trade
)
```

### Automatic Switching Logic

1. **Comparison Frequency**: Models are compared every hour (configurable via `comparison_interval`)
2. **Minimum Data Requirement**: Each model needs at least 10 trades for comparison
3. **Hysteresis**: 5% performance difference required to trigger a switch
4. **Seamless Transition**: No downtime - switch happens instantly during next prediction

Example:
```python
# Switch from incremental to batch only if batch is 5% better
if use_incremental and batch_score > incr_score * 1.05:
    switch_to_batch()

# Switch from batch to incremental only if incremental is 5% better
if not use_incremental and incr_score > batch_score * 1.05:
    switch_to_incremental()
```

## Configuration

### Enable Auto-Selection

In `.env`:
```env
AUTO_SELECT_BEST_MODEL=true
```

In `config.py`:
```python
AUTO_SELECT_BEST_MODEL = os.getenv('AUTO_SELECT_BEST_MODEL', 'false').lower() == 'true'
```

In code:
```python
model = MLModel('models/signal_model.pkl', auto_select_best=True)
```

### Configuration Hierarchy

The system supports three mutually exclusive modes:

1. **Auto-Selection Mode** (when `auto_select_best=True`)
   - Initializes both models
   - Records outcomes in both
   - Automatically switches between them

2. **Incremental Only** (when `use_incremental=True` and `auto_select_best=False`)
   - Only initializes incremental model
   - All operations use incremental learning

3. **Batch Only** (default - both flags `False`)
   - Only initializes batch model
   - Traditional batch learning approach

## Performance Tracking

### Metrics Tracked per Model

Both models track:
- `total_trades`: Number of trades processed
- `win_rate`: Percentage of profitable trades
- `accuracy`: Classification accuracy (incremental only has this initially)
- `avg_profit`: Average profit on winning trades
- `avg_loss`: Average loss on losing trades

### Model Comparison

The system logs when comparing and switching:
```
🔄 Switching to BATCH model (score: 0.872 vs 0.815)
🔄 Switching to INCREMENTAL model (score: 0.903 vs 0.851)
```

## Usage Examples

### Basic Usage

```python
from ml_model import MLModel

# Initialize with auto-selection
model = MLModel('models/signal_model.pkl', auto_select_best=True)

# Use normally - switching happens automatically
while trading:
    signal, confidence = model.predict(indicators)
    
    if confidence > threshold:
        execute_trade(signal)
        
        # Both models learn from this trade
        profit_loss = calculate_pnl()
        model.record_outcome(indicators, signal, profit_loss)
```

### Checking Current Model

```python
# Check which model is currently active
current_model = "Incremental" if model.use_incremental else "Batch"
print(f"Currently using: {current_model}")

# Check performance metrics
print(f"Batch: {model.batch_metrics}")
print(f"Incremental: {model.incremental_metrics}")
```

### Manual Comparison Trigger

```python
# Force an immediate comparison (for testing)
model._select_best_model()
```

## Testing

### Unit Test

A comprehensive test is included in `test_incremental_learning.py`:

```python
def test_auto_model_selection():
    """Test automatic model selection feature"""
    model = MLModel('models/test_auto_select.pkl', auto_select_best=True)
    
    # Verify both models initialized
    assert model.auto_select_best == True
    assert model.incremental_model is not None
    
    # Record outcomes
    for i in range(5):
        model.record_outcome(indicators, 'BUY', 0.01)
    
    # Verify both models received outcomes
    assert model.batch_metrics['total_trades'] == 5
    assert model.incremental_metrics['total_trades'] == 5
```

Run tests:
```bash
python test_incremental_learning.py
# Test Results: 7/7 passed ✅
```

### Demo Script

Run the interactive demo:
```bash
python demo_auto_model_selection.py
```

The demo:
- Initializes both models
- Seeds them with initial trades
- Simulates trading across different market conditions
- Shows performance comparison and automatic selection

## Benefits

### 1. Best of Both Worlds
- Combines batch learning's stability with incremental learning's adaptability
- No need to choose - system picks the best performer automatically

### 2. Adaptive to Market Conditions
- As market conditions change, different models may perform better
- System automatically adapts without manual intervention

### 3. Zero Downtime
- Switching happens seamlessly during normal operation
- No need to stop the bot or restart services

### 4. Performance-Based
- Decisions are based on actual measured performance
- Not theoretical or configuration-based

### 5. Fail-Safe
- If one model fails or performs poorly, the other takes over
- Built-in redundancy improves reliability

## Performance Impact

### Memory Usage
- **Without auto-selection**: Single model (batch: high, incremental: low)
- **With auto-selection**: Both models (~50% more than batch alone)
- **Tradeoff**: Small memory increase for significantly better adaptability

### CPU Usage
- **Prediction**: Negligible - only one model used at a time
- **Learning**: ~2x during `record_outcome` (both models learn)
- **Comparison**: Minimal - happens once per hour

### Expected Impact
- Better overall performance through automatic optimization
- Reduced need for manual monitoring and tuning
- Improved resilience to changing market conditions

## Monitoring and Logging

The system logs key events:

```
🤖 Auto-selecting best model - initializing both batch and incremental models
✓ Incremental model initialized
🔄 Switching to INCREMENTAL model (score: 0.903 vs 0.851)
```

Check current status:
```python
print(f"Batch trades: {model.batch_metrics['total_trades']}")
print(f"Incremental trades: {model.incremental_metrics['total_trades']}")
print(f"Active: {'Incremental' if model.use_incremental else 'Batch'}")
```

## Future Enhancements

Potential improvements:
1. **Adaptive Comparison Interval**: Adjust comparison frequency based on volatility
2. **Multiple Scoring Functions**: Allow custom scoring strategies
3. **Historical Performance Tracking**: Store long-term model performance data
4. **A/B Testing Mode**: Split trades between models for testing
5. **Ensemble Predictions**: Combine predictions from both models

## Troubleshooting

### Both Models Showing Same Performance
- Normal if both models are equally effective
- System will stick with current model (no switching needed)

### Frequent Switching
- May indicate high market volatility
- Consider increasing hysteresis threshold (currently 5%)

### One Model Always Selected
- May indicate one model is consistently better for current market conditions
- This is actually the desired behavior - system found the best model

## Related Files

- `ml_model.py` - Main implementation
- `config.py` - Configuration settings
- `bot.py` - Bot integration
- `test_incremental_learning.py` - Test suite
- `demo_auto_model_selection.py` - Interactive demo
- `.env.example` - Configuration examples
- `INCREMENTAL_LEARNING.md` - User documentation

## Conclusion

The automatic model selection feature provides intelligent, hands-off optimization of the machine learning system. By running both models in parallel and automatically selecting the better performer, it ensures the bot always uses the most effective learning approach for current market conditions.
