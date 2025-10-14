"""
Example: Using Historical Training

This example shows how to use the historical training feature
to pre-train the bot's ML model before starting live trading.
"""

# Step 1: Configure in .env file
# Add these lines to your .env:

"""
# Historical Training Configuration
ENABLE_HISTORICAL_TRAINING=true
HISTORICAL_TRAINING_SYMBOLS=BTC/USDT:USDT,ETH/USDT:USDT,SOL/USDT:USDT
HISTORICAL_TRAINING_TIMEFRAME=1h
HISTORICAL_TRAINING_DAYS=30
HISTORICAL_TRAINING_MIN_SAMPLES=100
"""

# Step 2: Start the bot normally
# The historical training will happen automatically in the background

# python bot.py

# You'll see log output like this:

"""
============================================================
🤖 INITIALIZING ADVANCED KUCOIN FUTURES TRADING BOT
============================================================
...
🚀 BOT STARTED SUCCESSFULLY!
============================================================
⏱️  Opportunity scan interval: 60s
⚡ Position monitoring: DEDICATED THREAD (independent of scanning)
🔥 Position update throttle: 3s minimum between API calls
============================================================
👁️ Starting dedicated position monitor thread (PRIORITY: CRITICAL)...
🔍 Starting background scanner thread (PRIORITY: NORMAL)...
🎓 Starting historical training thread (PRIORITY: LOW)...
============================================================
✅ All threads started - Position Monitor has API priority
============================================================

# Historical training runs in background:

============================================================
🎓 STARTING HISTORICAL TRAINING
============================================================
Symbols: 3
Timeframe: 1h
History: 30 days
Min samples: 100
============================================================
Processing BTC/USDT:USDT...
Fetching 720 candles of BTC/USDT:USDT (1h) for training...
✓ Fetched 720 candles for BTC/USDT:USDT
✓ Generated 350 training samples from BTC/USDT:USDT
Processing ETH/USDT:USDT...
✓ Fetched 720 candles for ETH/USDT:USDT
✓ Generated 340 training samples from ETH/USDT:USDT
Processing SOL/USDT:USDT...
✓ Fetched 720 candles for SOL/USDT:USDT
✓ Generated 320 training samples from SOL/USDT:USDT
============================================================
📊 Total training samples generated: 1010
============================================================
🤖 Training ML model with historical data...
Modern gradient boosting ensemble trained - Train accuracy: 0.98, Test accuracy: 0.85
✅ Historical training completed successfully!
💾 Model saved to disk
"""

# Step 3: The bot continues trading with the pre-trained model
# All future trades will benefit from the historical training

# To disable historical training, set in .env:
# ENABLE_HISTORICAL_TRAINING=false

print(__doc__)
