# State Persistence Guide

## Overview

The trading bot now includes comprehensive state persistence to ensure all important data is tracked during operation and saved when shutting down. This prevents data loss in case of unexpected crashes or shutdowns.

## What Is Saved

### 1. Analytics State (`models/analytics_state.pkl`)
- **Trade History**: All executed trades with entry/exit prices, P&L, duration, leverage
- **Equity Curve**: Balance snapshots over time for performance tracking
- **Limits**: Keeps last 10,000 records to prevent unbounded growth

### 2. Risk Manager State (`models/risk_manager_state.pkl`)
- **Performance Metrics**: Total trades, wins, losses, profit/loss totals
- **Drawdown Tracking**: Peak balance, current drawdown
- **Streaks**: Win/loss streaks for adaptive risk management
- **Recent Trades**: Last 10 trades for rolling performance metrics
- **Daily Loss Tracking**: Automatically resets each trading day

### 3. ML Model State (`models/signal_model.pkl`)
- **Model**: Trained ML model for signal prediction
- **Scaler**: Feature scaling parameters
- **Training Data**: Last 10,000 training examples
- **Feature Importance**: Which features matter most
- **Performance Metrics**: Win rate, average profit, total trades

### 4. Deep Learning Model (`models/deep_signal_model.h5`)
- **Neural Network Weights**: LSTM and dense layer weights
- **Architecture**: Model structure for temporal pattern recognition

### 5. Reinforcement Learning (`models/q_table.pkl`)
- **Q-Table**: Strategy selection Q-values by market regime
- **Epsilon**: Exploration rate for strategy selection

### 6. Attention Weights (`models/attention_weights.npy`)
- **Feature Weights**: Dynamic feature importance learned over time
- **Attention Scores**: Which indicators are most predictive

## When State Is Saved

### Periodic Auto-Save (Every 5 Minutes)
During normal operation, all state is automatically saved every 5 minutes to prevent data loss in case of crashes.

### Shutdown Save
When the bot shuts down gracefully (Ctrl+C, SIGTERM), all state is saved:
```python
# Shutdown sequence saves:
1. ML model
2. Deep learning model
3. RL Q-table
4. Attention weights
5. Analytics state
6. Risk manager state
```

## When State Is Loaded

### Startup Load
On bot initialization, all components automatically load their saved state:
- Analytics loads trade history and equity curve
- Risk manager loads performance metrics and drawdown tracking
- ML models load trained weights
- Attention selector loads learned feature importance

### Graceful Handling
If state files don't exist (first run), components initialize with defaults:
- No errors or warnings
- Clean slate for new trading session
- State will be created on first save

## Testing State Persistence

### Unit Tests
```bash
python3 test_state_persistence.py
```
Tests individual component save/load functionality.

### Lifecycle Test
```bash
python3 test_bot_state_lifecycle.py
```
Tests complete bot lifecycle: startup → operation → shutdown → restart.

## Benefits

1. **Data Loss Prevention**: Periodic saves prevent data loss on crashes
2. **Continuous Learning**: ML models maintain learned patterns across sessions
3. **Performance Tracking**: All trading metrics survive restarts
4. **Risk Management Continuity**: Drawdown tracking persists across sessions
5. **Graceful Recovery**: Bot can resume operations after unexpected shutdowns

## File Locations

All state files are stored in the `models/` directory:
```
models/
├── analytics_state.pkl          # Trade history and equity curve
├── risk_manager_state.pkl       # Performance metrics and drawdown
├── signal_model.pkl             # ML model and training data
├── deep_signal_model.h5         # Deep learning neural network
├── q_table.pkl                  # RL strategy selection Q-table
└── attention_weights.npy        # Feature importance weights
```

## Memory Management

To prevent unbounded memory growth:
- Analytics keeps last 10,000 trades and equity points
- ML model keeps last 10,000 training examples
- Risk manager keeps last 10 recent trades
- Periodic cleanup (every 30 minutes) removes old data

## Troubleshooting

### State Not Loading
- Check that `models/` directory exists
- Verify file permissions (must be readable)
- Check logs for error messages

### Large State Files
- Files grow with trading activity
- Analytics limited to 10,000 records (~2-5 MB)
- ML model limited to 10,000 examples (~5-10 MB)
- Total state usually < 50 MB

### Corrupted State
If state files become corrupted:
1. Stop the bot
2. Backup `models/` directory
3. Delete corrupted files
4. Restart bot (will use defaults)

## Code Example

### Manual State Save
```python
# Save all states manually
bot.analytics.save_state()
bot.risk_manager.save_state()
bot.ml_model.save_model()
bot.attention_features_2025.save_weights()
```

### Manual State Load
```python
# Load states manually (done automatically on init)
analytics = AdvancedAnalytics()  # Loads state in __init__
risk = RiskManager(...)          # Loads state in __init__
```

## Best Practices

1. **Regular Backups**: Backup `models/` directory periodically
2. **Monitor State Size**: Check file sizes if bot runs for extended periods
3. **Clean Shutdown**: Always use Ctrl+C for graceful shutdown
4. **Test After Restart**: Verify bot resumes correctly after restart

## Future Enhancements

Potential improvements:
- Compress state files to reduce disk usage
- Add state versioning for compatibility
- Implement state migration for upgrades
- Add state validation on load
- Cloud backup integration
