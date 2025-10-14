# Historical Training - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       Bot Startup                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Initialize Components                            │
│  • KuCoinClient  • MLModel  • HistoricalTrainer                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Start Threads                                   │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Position    │  │ Background   │  │ Historical   │          │
│  │  Monitor     │  │  Scanner     │  │  Training    │          │
│  │ (CRITICAL)   │  │  (NORMAL)    │  │   (LOW)      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         │ API Priority     │                  │                   │
│         └──────────────────┴──────────────────┘                   │
└───────────────────────────────────────────────────────────────────┘
                                                 │
                   ┌─────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│            Historical Training Process                            │
│                                                                   │
│  1. Check if training needed                                     │
│     • Skip if model has enough samples                           │
│     • Skip if ENABLE_HISTORICAL_TRAINING=false                   │
│                                                                   │
│  2. For each symbol in HISTORICAL_TRAINING_SYMBOLS:              │
│     ┌──────────────────────────────────────────────┐            │
│     │ Fetch Historical OHLCV Data                  │            │
│     │   (via KuCoin API)                           │            │
│     └──────────────┬───────────────────────────────┘            │
│                    │                                              │
│                    ▼                                              │
│     ┌──────────────────────────────────────────────┐            │
│     │ Calculate Technical Indicators                │            │
│     │  • RSI, MACD, Bollinger Bands                │            │
│     │  • Stochastic, Volume, ATR                   │            │
│     │  • 26 features total                          │            │
│     └──────────────┬───────────────────────────────┘            │
│                    │                                              │
│                    ▼                                              │
│     ┌──────────────────────────────────────────────┐            │
│     │ Generate Training Samples                     │            │
│     │                                               │            │
│     │ For each candle (i):                          │            │
│     │   • Get indicators at time i                  │            │
│     │   • Look ahead 5 candles (i+5)               │            │
│     │   • Calculate price change                    │            │
│     │                                               │            │
│     │   If price_change > +1%:                     │            │
│     │     → Label: BUY                             │            │
│     │     → Profit: price_change                   │            │
│     │                                               │            │
│     │   If price_change < -1%:                     │            │
│     │     → Label: SELL                            │            │
│     │     → Profit: abs(price_change)              │            │
│     │                                               │            │
│     │   Else: Skip (neutral)                       │            │
│     │                                               │            │
│     └──────────────┬───────────────────────────────┘            │
│                    │                                              │
│                    ▼                                              │
│     ┌──────────────────────────────────────────────┐            │
│     │ Record Outcomes                               │            │
│     │   ml_model.record_outcome()                  │            │
│     └──────────────────────────────────────────────┘            │
│                                                                   │
│  3. Train ML Model                                               │
│     ┌──────────────────────────────────────────────┐            │
│     │ Gradient Boosting Ensemble                    │            │
│     │  • XGBoost (weight: 3)                       │            │
│     │  • LightGBM (weight: 2)                      │            │
│     │  • CatBoost (weight: 2)                      │            │
│     │                                               │            │
│     │ Calibrated with CalibratedClassifierCV       │            │
│     └──────────────┬───────────────────────────────┘            │
│                    │                                              │
│                    ▼                                              │
│     ┌──────────────────────────────────────────────┐            │
│     │ Save Trained Model                            │            │
│     │   models/signal_model.pkl                    │            │
│     └──────────────────────────────────────────────┘            │
│                                                                   │
└──────────────────────┬────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Bot Continues Trading                                │
│                                                                   │
│  • All three threads running                                     │
│  • ML model has historical knowledge                             │
│  • Better predictions from first trade                           │
│  • Continues learning from live trades                           │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                    Configuration (.env)                           │
│                                                                   │
│  ENABLE_HISTORICAL_TRAINING=true                                 │
│  HISTORICAL_TRAINING_SYMBOLS=BTC/USDT:USDT,ETH/USDT:USDT        │
│  HISTORICAL_TRAINING_TIMEFRAME=1h                                │
│  HISTORICAL_TRAINING_DAYS=30                                     │
│  HISTORICAL_TRAINING_MIN_SAMPLES=100                             │
│                                                                   │
│  Results in:                                                     │
│  • 720 candles per symbol (30 days × 24 hours)                  │
│  • ~350 training samples per symbol                              │
│  • Total: ~700 samples from 2 symbols                            │
│  • Training time: 30-60 seconds                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
KuCoin API → Historical Data → Indicators → Training Samples → ML Model → Trading Decisions
     ↑                                                             ↓
     │                                                             │
     └─────────────────────────────────────────────────────────────┘
              Model can request fresh data for predictions
```

## Thread Priority

```
Priority 1 (CRITICAL): Position Monitor
    ↓ Has API priority - executes first
Priority 2 (NORMAL):   Background Scanner
    ↓ Waits for critical operations
Priority 3 (LOW):      Historical Training
    ↓ Runs only when others are idle
Background: No impact on trading
```

## Training Algorithm

```
For symbol in [BTC, ETH, SOL]:
    candles = fetch_ohlcv(symbol, 1h, 720)  # 30 days
    
    for i in range(len(candles) - 5):
        current_indicators = calculate_indicators(candles[i])
        future_price = candles[i+5].close
        price_change = (future_price - candles[i].close) / candles[i].close
        
        if price_change > 0.01:  # +1%
            record_outcome(indicators, signal='BUY', profit=price_change)
        elif price_change < -0.01:  # -1%
            record_outcome(indicators, signal='SELL', profit=abs(price_change))
        # else: skip neutral

train_model(min_samples=100)
save_model()
```

## Key Benefits

1. **Pre-trained Knowledge**: Model starts with 700+ training samples
2. **Realistic Data**: Uses actual historical price movements
3. **Non-Blocking**: Runs in background, doesn't delay trading
4. **Automatic**: Zero configuration needed (smart defaults)
5. **Configurable**: Full control via environment variables
