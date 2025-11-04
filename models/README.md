# Models Directory - Protected Learning Data

This directory stores all machine learning models and training data for the RAD trading bot. **All files in this directory are automatically protected from git tracking** to ensure you never lose your learning progress.

## 🛡️ Protection Status

The following files are **automatically ignored by git** and will **never be overwritten** by `git pull`:

- `*.pkl` - ML models, scalers, and training data (joblib format)
- `*.h5` - Keras/TensorFlow models (legacy format)
- `*.pt` - PyTorch models
- `*.keras` - Keras models (current format)
- `*.npy` - NumPy arrays (attention weights, etc.)
- `catboost_info/` - CatBoost training artifacts

## 📁 Expected Files

After your bot has been running, you should see these files:

1. **signal_model.pkl** - Main ML model for signal prediction
   - Trained RandomForest/XGBoost/LightGBM/CatBoost ensemble
   - Feature scaler and training history
   - Performance metrics and feature importance

2. **deep_signal_model.keras** - Deep learning neural network
   - LSTM and dense layer weights
   - Temporal pattern recognition model

3. **q_table.pkl** - Reinforcement learning Q-table
   - Strategy selection Q-values by market regime
   - Exploration rate (epsilon)

4. **attention_weights.npy** - Attention-based feature weights
   - Dynamic feature importance learned over time

5. **analytics_state.pkl** - Trading analytics
   - Trade history (last 10,000 trades)
   - Equity curve data

6. **risk_manager_state.pkl** - Risk management state
   - Performance metrics and drawdown tracking
   - Win/loss streaks

## ✅ Your Data is Safe

When you run `git pull`:
- ✅ Your model files stay exactly as they are
- ✅ No learning data is lost
- ✅ Training progress is preserved
- ✅ Performance metrics remain intact

## 🔄 Backup Recommendations

Although your models are protected from git operations, it's good practice to backup regularly:

```bash
# Create a timestamped backup
./backup_models.sh

# Or manually backup the entire directory
cp -r models/ "models_backup_$(date +%Y%m%d_%H%M%S)/"
```

## 🆕 First Time Setup

If this is a fresh installation:
1. The directory will be empty (this is normal)
2. Models will be created automatically when the bot runs
3. Learning data accumulates over time
4. No manual setup required!

## 📊 Model File Sizes

Typical file sizes after training:
- `signal_model.pkl`: 5-10 MB (10,000 training examples)
- `deep_signal_model.keras`: 1-5 MB (neural network weights)
- `q_table.pkl`: < 1 MB (Q-table and epsilon)
- `attention_weights.npy`: < 1 MB (feature weights)
- `analytics_state.pkl`: 2-5 MB (10,000 trades)
- `risk_manager_state.pkl`: < 1 MB (metrics and state)

**Total: Usually less than 50 MB**

## 🔧 Troubleshooting

### Models not loading after restart
- Check file permissions (must be readable)
- Check logs for error messages
- If corrupted, delete the file and let it retrain

### Want to start fresh
```bash
# Backup first (just in case)
cp -r models/ models_backup/

# Remove all models to start fresh
rm models/*.pkl models/*.keras models/*.npy

# Restart the bot - it will create new models
python bot.py
```

### Want to share models with another instance
Models are specific to your trading history and market conditions. Sharing is not recommended as:
- Each instance should learn from its own experience
- Models may be overfitted to specific conditions
- Better to let each instance train independently

## 📖 More Information

See [STATE_PERSISTENCE.md](../STATE_PERSISTENCE.md) for complete details on:
- What data is saved in each file
- When models are saved (every 5 minutes + on shutdown)
- Memory management and cleanup
- Testing and validation

## 🚨 Important Notes

1. **Never commit model files to git** - They're personal to your instance
2. **Backup before major updates** - Although protected, backups are always good
3. **Models directory must exist** - This .gitkeep file ensures it does
4. **Let models train naturally** - Don't copy models between instances

---

Your learning data is safe! The bot automatically protects your progress. 🎉
