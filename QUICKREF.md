# Quick Reference Guide

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your KuCoin API credentials

# 3. Run tests
python test_bot.py

# 4. Start the bot
python start.py
# or directly:
python bot.py
```

## File Structure

```
RAD/
├── README.md              # Main documentation
├── API_SETUP.md          # KuCoin API setup guide
├── STRATEGY.md           # Trading strategy details
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
│
├── bot.py               # Main bot orchestrator
├── start.py             # Quick start script
├── test_bot.py          # Test suite
│
├── config.py            # Configuration management
├── logger.py            # Logging utilities
├── monitor.py           # Performance monitoring
│
├── kucoin_client.py     # KuCoin API wrapper
├── market_scanner.py    # Market scanning
├── indicators.py        # Technical indicators
├── signals.py           # Signal generation
├── ml_model.py          # Machine learning
├── position_manager.py  # Position management
└── risk_manager.py      # Risk management
```

## Configuration Quick Reference

### Essential Settings (.env)

```env
# API (Required)
KUCOIN_API_KEY=your_key
KUCOIN_API_SECRET=your_secret
KUCOIN_API_PASSPHRASE=your_passphrase

# Trading (Recommended to adjust)
LEVERAGE=10                    # 1-10x
MAX_POSITION_SIZE=1000         # USDT
RISK_PER_TRADE=0.02           # 2% per trade
MAX_OPEN_POSITIONS=3          # Concurrent positions

# Bot Behavior
CHECK_INTERVAL=60             # Seconds between scans
TRAILING_STOP_PERCENTAGE=0.02 # 2% trailing stop
MIN_PROFIT_THRESHOLD=0.005    # 0.5% minimum profit

# ML
RETRAIN_INTERVAL=86400        # 24 hours
```

## Common Commands

### Start Bot
```bash
python bot.py
```

### Run Tests
```bash
python test_bot.py
```

### Test API Connection
```bash
python -c "from config import Config; from kucoin_client import KuCoinClient; Config.validate(); client = KuCoinClient(Config.API_KEY, Config.API_SECRET, Config.API_PASSPHRASE); print('Connected!')"
```

### Check Configuration
```bash
python -c "from config import Config; Config.validate(); print('Config OK')"
```

### View Logs
```bash
tail -f logs/bot.log
```

## Key Components

### Market Scanner
- Scans all KuCoin Futures pairs
- Calculates technical indicators
- Ranks by trading opportunity score
- Returns top N pairs

### Signal Generator
- Uses 7+ technical indicators
- Multi-factor scoring system
- Minimum 60% confidence threshold
- Volume confirmation

### Position Manager
- Dynamic position sizing
- Trailing stop loss
- Take profit targets
- Automatic position monitoring

### Risk Manager
- Maximum position limits
- Risk-based position sizing
- Dynamic leverage adjustment
- Balance validation

### ML Model
- Random Forest classifier
- Self-learning from outcomes
- Periodic retraining
- Signal validation

## Trading Flow

1. **Market Scan**
   - Fetch all active futures pairs
   - Calculate indicators for each
   - Score and rank opportunities

2. **Signal Generation**
   - Analyze top opportunities
   - Generate BUY/SELL signals
   - Calculate confidence scores

3. **Risk Check**
   - Validate available balance
   - Check position limits
   - Calculate safe position size

4. **Position Entry**
   - Set leverage
   - Place market order
   - Set stop loss
   - Set take profit

5. **Position Management**
   - Monitor price movements
   - Update trailing stops
   - Check exit conditions

6. **Position Exit**
   - Close on stop loss hit
   - Close on take profit hit
   - Close on signal reversal

7. **ML Learning**
   - Record trade outcome
   - Update training data
   - Retrain model periodically

## Indicators Used

| Indicator | Purpose | Signal |
|-----------|---------|--------|
| EMA 12/26 | Trend | Crossover |
| SMA 20/50 | Trend | Position vs MA |
| RSI | Momentum | <30 / >70 |
| MACD | Momentum | Line crossover |
| Stochastic | Momentum | <20 / >80 |
| Bollinger Bands | Volatility | Price vs bands |
| ATR | Volatility | Stop loss sizing |
| Volume | Confirmation | Ratio vs average |

## Risk Parameters

| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| Leverage | 10x | 1-10x | Position amplification |
| Risk per Trade | 2% | 1-5% | Max risk per position |
| Max Positions | 3 | 1-10 | Concurrent trades |
| Stop Loss | 3-10% | 2-15% | Loss limit |
| Trailing Stop | 2% | 1-5% | Profit protection |

## Monitoring

### Important Metrics
- **Win Rate**: % of profitable trades
- **Profit Factor**: Total profit / Total loss
- **Average P/L**: Mean profit per trade
- **Max Drawdown**: Largest loss
- **Sharpe Ratio**: Risk-adjusted returns

### Log Locations
- **Console**: Real-time output
- **File**: `logs/bot.log`
- **ML Model**: `models/signal_model.pkl`

## Troubleshooting

### Bot won't start
```bash
# Check dependencies
pip install -r requirements.txt

# Verify config
python -c "from config import Config; Config.validate()"

# Check logs
cat logs/bot.log
```

### No trades executing
- Lower confidence threshold in signals.py
- Verify sufficient balance
- Check max positions not reached
- Review signal generation logs

### API errors
- Verify credentials in .env
- Check KuCoin API status
- Verify API permissions
- Check IP whitelist

### Positions not closing
- Check trailing stop settings
- Verify stop loss configuration
- Check position_manager logs
- Ensure adequate margin

## Safety Tips

✅ **Do:**
- Start with small positions
- Monitor first 24 hours
- Use IP whitelist
- Enable 2FA
- Review logs regularly
- Test in paper mode first (if available)

❌ **Don't:**
- Use max leverage initially
- Ignore warning logs
- Share API keys
- Commit .env to Git
- Enable withdraw permission
- Run multiple instances

## Performance Tuning

### Conservative Settings
```env
LEVERAGE=5
RISK_PER_TRADE=0.01
MAX_OPEN_POSITIONS=2
TRAILING_STOP_PERCENTAGE=0.03
```

### Aggressive Settings
```env
LEVERAGE=10
RISK_PER_TRADE=0.03
MAX_OPEN_POSITIONS=5
TRAILING_STOP_PERCENTAGE=0.015
```

### High Frequency
```env
CHECK_INTERVAL=30
MIN_PROFIT_THRESHOLD=0.003
```

### Low Frequency
```env
CHECK_INTERVAL=300
MIN_PROFIT_THRESHOLD=0.01
```

## Emergency Stop

### Graceful Shutdown
```bash
# Press Ctrl+C
# Bot will log shutdown and optionally close positions
```

### Force Stop
```bash
# Find process
ps aux | grep bot.py

# Kill process
kill -9 <PID>
```

### Close All Positions
```python
from config import Config
from kucoin_client import KuCoinClient

client = KuCoinClient(Config.API_KEY, Config.API_SECRET, Config.API_PASSPHRASE)
positions = client.get_open_positions()

for pos in positions:
    client.close_position(pos['symbol'])
    print(f"Closed {pos['symbol']}")
```

## Resources

- **KuCoin Futures API**: https://docs.kucoin.com/futures/
- **CCXT Documentation**: https://docs.ccxt.com/
- **Technical Analysis (ta)**: https://github.com/bukosabino/ta
- **Scikit-learn**: https://scikit-learn.org/

## Support

For issues:
1. Check logs: `logs/bot.log`
2. Review documentation
3. Test individual components
4. Check KuCoin API status
5. Verify configuration

## Version Info

- **Python**: 3.11+
- **CCXT**: 4.0.0+
- **Pandas**: 2.0.0+
- **Scikit-learn**: 1.3.0+

## License

Educational purposes only. Use at your own risk.
