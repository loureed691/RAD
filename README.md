# RAD - KuCoin Futures Trading Bot

A production-grade, fully automated, self-learning KuCoin Futures trading bot with 10x leverage capability. This bot is designed to be hands-off and resilient, automatically discovering the best trading pairs and executing trades based on advanced technical indicators and machine learning signals.

## Features

- **Automated Trading Pair Discovery**: Automatically scans all available KuCoin Futures pairs and selects the best opportunities based on technical signals
- **Advanced Technical Analysis**: Uses multiple indicators including RSI, MACD, Bollinger Bands, Stochastic Oscillator, and volume analysis
- **Machine Learning Signal Optimization**: Self-learning ML model that improves over time based on trading outcomes
- **Dynamic Leverage Management**: Adjusts leverage (up to 10x) based on market volatility and signal confidence
- **Trailing Stop Loss**: Automatically trails profits to lock in gains while letting winners run
- **Risk Management**: Built-in position sizing, maximum position limits, and risk per trade controls
- **Resilient Architecture**: Error handling, logging, and graceful shutdown capabilities
- **Production-Ready**: Designed for 24/7 operation with comprehensive monitoring and logging

## Architecture

The bot consists of several key components:

- **bot.py**: Main orchestrator that coordinates all components
- **kucoin_client.py**: API wrapper for KuCoin Futures REST API using ccxt
- **market_scanner.py**: Scans all trading pairs in parallel to find best opportunities
- **indicators.py**: Calculates technical indicators (RSI, MACD, Bollinger Bands, etc.)
- **signals.py**: Generates trading signals based on multiple indicators
- **ml_model.py**: Machine learning model for signal optimization and self-learning
- **position_manager.py**: Manages open positions with trailing stops
- **risk_manager.py**: Handles position sizing and risk controls
- **config.py**: Configuration management
- **logger.py**: Logging utilities

## Installation

### Prerequisites

- Python 3.11 or higher
- KuCoin Futures account with API credentials
- Sufficient balance for trading (recommended minimum: $500)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/loureed691/RAD.git
cd RAD
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your environment:
```bash
cp .env.example .env
```

4. Edit `.env` and add your KuCoin API credentials:
```env
KUCOIN_API_KEY=your_api_key_here
KUCOIN_API_SECRET=your_api_secret_here
KUCOIN_API_PASSPHRASE=your_api_passphrase_here
```

## Configuration

Key configuration parameters in `.env`:

- **LEVERAGE**: Maximum leverage to use (default: 10)
- **MAX_POSITION_SIZE**: Maximum position size in USDT (default: 1000)
- **RISK_PER_TRADE**: Risk per trade as percentage of balance (default: 0.02 = 2%)
- **MIN_PROFIT_THRESHOLD**: Minimum profit threshold to consider (default: 0.005 = 0.5%)
- **CHECK_INTERVAL**: Seconds between market scans (default: 60)
- **TRAILING_STOP_PERCENTAGE**: Trailing stop percentage (default: 0.02 = 2%)
- **MAX_OPEN_POSITIONS**: Maximum concurrent positions (default: 3)
- **RETRAIN_INTERVAL**: Seconds between ML model retraining (default: 86400 = 24 hours)

## Usage

### Running the Bot

```bash
python bot.py
```

The bot will:
1. Initialize all components and validate configuration
2. Start scanning the market for trading opportunities
3. Execute trades based on the best signals
4. Monitor and update positions with trailing stops
5. Continuously learn and improve from trading outcomes

### Stopping the Bot

Press `Ctrl+C` to gracefully stop the bot. The bot will:
- Log the shutdown request
- Complete any pending operations
- Optionally close all positions (configurable)
- Save the ML model state

## How It Works

### Signal Generation

The bot generates trading signals using a multi-indicator approach:

1. **Trend Following**: EMA crossovers and moving averages
2. **Momentum**: MACD, RSI, and Stochastic Oscillator
3. **Volatility**: Bollinger Bands and ATR
4. **Volume**: Volume confirmation for signal strength
5. **Machine Learning**: ML model provides additional signal validation

Each indicator contributes to an overall score and confidence level. Trades are only executed when confidence exceeds the threshold (default: 60%).

### Position Management

The bot manages positions with the following features:

- **Dynamic Position Sizing**: Calculates safe position size based on account balance, risk per trade, and stop loss distance
- **Trailing Stops**: Automatically adjusts stop loss to lock in profits as price moves favorably
- **Take Profit**: Sets initial take profit targets based on risk-reward ratio
- **Maximum Positions**: Limits concurrent positions to manage risk

### Machine Learning

The bot includes a self-learning component:

1. Records all trading outcomes (entry indicators, signal, profit/loss)
2. Periodically retrains a Random Forest classifier on historical outcomes
3. Uses the ML model to validate and optimize future signals
4. Improves accuracy over time as it learns from experience

### Risk Management

Multiple layers of risk management:

- **Position Sizing**: Calculates safe position size based on account balance and risk tolerance
- **Stop Loss**: Dynamic stop loss based on market volatility
- **Leverage Adjustment**: Reduces leverage in high volatility or low confidence scenarios
- **Maximum Positions**: Limits total exposure
- **Balance Checks**: Ensures sufficient balance before opening positions

## Logging and Monitoring

Logs are written to both console and file (default: `logs/bot.log`):

- **INFO**: General operation logs (trades, signals, positions)
- **WARNING**: Important notices (insufficient balance, max positions reached)
- **ERROR**: Errors and exceptions with full stack traces

## Safety Features

- **API Error Handling**: Gracefully handles API errors and rate limits
- **Position Validation**: Validates all positions before execution
- **Balance Checks**: Ensures sufficient balance for trades
- **Confidence Thresholds**: Only trades high-confidence signals
- **Emergency Shutdown**: Can be stopped at any time with Ctrl+C

## Important Notes

⚠️ **Risk Warning**: Trading cryptocurrency futures with leverage involves significant risk. You can lose more than your initial investment. Only trade with money you can afford to lose.

- Start with small position sizes to test the bot
- Monitor the bot regularly, especially during the first days
- Adjust risk parameters based on your risk tolerance
- Consider running in paper trading mode first (if supported by exchange)
- Keep your API keys secure and never share them

## Troubleshooting

### Bot won't start
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify API credentials in `.env` file
- Check logs for specific error messages

### No trades being executed
- Check if confidence thresholds are too high
- Verify available balance is sufficient
- Check if maximum positions limit is reached
- Review logs for validation failures

### Positions not closing
- Verify trailing stop configuration
- Check network connectivity to exchange
- Review position status in logs

## Development

### Project Structure
```
RAD/
├── bot.py                 # Main bot orchestrator
├── kucoin_client.py       # KuCoin API wrapper
├── market_scanner.py      # Market scanning and pair selection
├── indicators.py          # Technical indicators
├── signals.py            # Signal generation
├── ml_model.py           # Machine learning model
├── position_manager.py   # Position management
├── risk_manager.py       # Risk management
├── config.py            # Configuration management
├── logger.py            # Logging utilities
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is provided as-is for educational and research purposes.

## Disclaimer

This software is for educational purposes only. Use at your own risk. The authors and contributors are not responsible for any financial losses incurred while using this bot.