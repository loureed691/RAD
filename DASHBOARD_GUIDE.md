# Enhanced Dashboard Guide

## Overview

The RAD Trading Bot includes a **comprehensive web-based dashboard** for real-time monitoring of all trading activities, positions, risk metrics, and system health. **The dashboard now starts automatically when you run the bot!**

## Quick Start

Simply start your bot:
```bash
python bot.py
```

The dashboard will automatically start and be available at:
```
http://localhost:5000
```

**That's it!** No additional configuration needed.

## Features

### 📊 Performance Overview
- **Balance & P&L**: Current balance with initial balance comparison and ROI percentage
- **Win Rate**: Percentage of winning trades with win/loss breakdown
- **Active Positions**: Number of open positions with total exposure
- **Advanced Metrics**: Sharpe Ratio, Sortino Ratio, Calmar Ratio, and Profit Factor

### 💼 Open Positions
Detailed table showing all currently open positions:
- Symbol and trading side (long/short)
- Entry and current prices
- Position size and leverage
- Unrealized P&L (dollar amount and percentage)
- Stop loss and take profit levels
- Position duration

### 🛡️ Risk Metrics
Comprehensive risk monitoring:
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Current Drawdown**: Current decline from peak
- **Portfolio Heat**: Risk exposure as percentage of capital
- **Total Exposure**: Total position size across all trades
- **Available Capital**: Remaining trading capital
- **Daily P&L**: Today's profit/loss
- **Volatility (ATR)**: Average True Range volatility metric

### 🎯 Strategy & Market Analysis
- **Active Strategy**: Currently selected trading strategy
- **Market Regime**: Detected market condition (bull/bear/neutral)
- **Strategy Performance**: Active strategy's performance percentage
- **Signal Strength**: Current signal confidence level
- **Market Volatility**: Volatility classification (low/normal/high)
- **Trend Direction**: Current market trend
- **Last Signal**: Most recent trading signal generated

### 📈 Recent Trades
Enhanced trade history showing:
- Trade timestamp
- Symbol and side
- Entry and exit prices
- Position size
- Profit/loss in dollars and percentage
- Trade duration

### ⚙️ System Status
Real-time system health monitoring:
- **Bot Status**: Active/Inactive indicator
- **API Connection**: Exchange API connection status
- **WebSocket Status**: Live data feed status
- **Last Trade Time**: Timestamp of most recent trade
- **Uptime**: Bot running duration
- **Error Count**: Number of errors in last 24 hours

### 📉 Charts
- **Equity Curve**: Visual representation of balance over time
- **Drawdown Chart**: Visual representation of drawdown periods

## Configuration

The dashboard is **enabled by default** and starts automatically with the bot.

### Environment Variables

You can customize the dashboard behavior in your `.env` file:

```env
# Dashboard Configuration
ENABLE_DASHBOARD=true       # Enable/disable dashboard (default: true)
DASHBOARD_PORT=5000         # Port for web dashboard (default: 5000)
DASHBOARD_HOST=0.0.0.0      # Host for dashboard (0.0.0.0 = accessible from any IP)
```

### Disabling the Dashboard

If you want to disable the dashboard, set `ENABLE_DASHBOARD=false` in your `.env` file:

```env
ENABLE_DASHBOARD=false
```

### Changing the Port

If port 5000 is already in use, you can change it:

```env
DASHBOARD_PORT=8080
```

Then access the dashboard at http://localhost:8080

### Network Access and Security

By default, `DASHBOARD_HOST=0.0.0.0` makes the dashboard accessible from any network interface, which is convenient but exposes your trading data on your local network.

**For local-only access (recommended):**
```env
DASHBOARD_HOST=127.0.0.1
```

This restricts access to localhost only, preventing network access.

**For network access (use with caution):**
```env
DASHBOARD_HOST=0.0.0.0
```

⚠️ **Security Warning**: Setting `DASHBOARD_HOST=0.0.0.0` exposes your trading dashboard to your local network. Only use this if:
- You're on a trusted private network
- You understand the security implications
- You need to access the dashboard from other devices

For production deployments, see the [Security Notes](#security-notes) section below.

## Usage

### Starting the Dashboard

#### Automatic Start (Recommended)

The dashboard **starts automatically** when you run the bot:

```bash
python bot.py
# or
python start.py
```

The bot will display a message like:
```
============================================================
✅ DASHBOARD STARTED SUCCESSFULLY!
   🌐 Access dashboard at: http://localhost:5000
   🌐 Or from network: http://YOUR_IP:5000
============================================================
```

#### Manual Start (For Testing Only)

If you want to test the dashboard without running the bot, you can use the example script:

```bash
python3 example_enhanced_dashboard.py
```

This runs the dashboard with simulated data for demonstration purposes.

#### Method 2: Custom Integration (Advanced)
```python
from dashboard import TradingDashboard

# Initialize dashboard
dashboard = TradingDashboard(port=5000)

# Update various metrics
dashboard.update_stats({
    'balance': 10000,
    'total_pnl': 500,
    'win_rate': 0.75,
    # ... more stats
})

dashboard.update_positions([
    {
        'symbol': 'BTC-USDT',
        'side': 'long',
        'entry_price': 50000,
        'current_price': 51000,
        # ... more position details
    }
])

dashboard.update_risk_metrics({
    'max_drawdown': 12.5,
    'current_drawdown': 3.2,
    # ... more risk metrics
})

dashboard.update_strategy_info({
    'active_strategy': 'Trend Following',
    'performance': 15.5
})

dashboard.update_market_info({
    'regime': 'bull',
    'signal_strength': 0.82,
    # ... more market info
})

dashboard.update_system_status({
    'bot_active': True,
    'api_connected': True,
    # ... more status info
})

# Add data points
dashboard.add_equity_point(10500)
dashboard.add_drawdown_point(-3.2)
dashboard.add_trade({
    'symbol': 'ETH-USDT',
    'side': 'long',
    'entry_price': 3000,
    'exit_price': 3100,
    'pnl': 100,
    'pnl_pct': 0.033
})

# Run dashboard server
dashboard.run(host='0.0.0.0', port=5000)
```

### Accessing the Dashboard

Once started, open your web browser and navigate to:
```
http://localhost:5000
```

Or from another computer on your network:
```
http://YOUR_SERVER_IP:5000
```

## Auto-Refresh

The dashboard automatically refreshes every 30 seconds to show the latest data.

## API Endpoints

The dashboard also exposes REST API endpoints:

- `GET /` - Main dashboard HTML page
- `GET /api/stats` - JSON endpoint for statistics
- `GET /api/trades` - JSON endpoint for recent trades (last 50)

## Design Features

- **Dark Theme**: Eye-friendly dark color scheme
- **Responsive Layout**: Adapts to different screen sizes
- **Color Coding**: 
  - Green for profits and positive metrics
  - Red for losses and negative metrics
  - Orange/Yellow for warnings
- **Status Indicators**: Animated pulse indicators for connection status
- **Hover Effects**: Interactive cards with hover animations
- **Badge System**: Visual badges for trade types and market regimes

## Requirements

- Flask >= 3.1.0
- Plotly >= 5.24.0

Install with:
```bash
pip install flask plotly
```

## Security Notes

⚠️ **Important**: The dashboard is intended for **local monitoring** or use within a **trusted network**. 

For production deployments:
1. Use authentication (consider adding Flask-Login)
2. Enable HTTPS (use a reverse proxy like Nginx)
3. Restrict access via firewall rules
4. Consider using a production WSGI server (e.g., Gunicorn)

## Troubleshooting

### Dashboard Won't Start
- Check if the port is already in use
- Ensure Flask and Plotly are installed
- Check logs for error messages

### Dashboard Shows No Data
- Ensure you're calling the update methods regularly
- Check that the bot is running and generating data
- Verify network connectivity if accessing remotely

### Charts Not Displaying
- Check browser console for JavaScript errors
- Ensure Plotly CDN is accessible
- Try a different browser

## Integration Example

For continuous updates in your trading bot:

```python
# In your main trading loop
while bot_running:
    # ... trading logic ...
    
    # Update dashboard every iteration
    dashboard.update_stats(bot.get_statistics())
    dashboard.update_positions(bot.get_open_positions())
    dashboard.update_risk_metrics(bot.get_risk_metrics())
    dashboard.update_system_status(bot.get_system_status())
    
    # Add new trades when closed
    if new_trade_closed:
        dashboard.add_trade(trade_details)
    
    # Add equity point periodically
    dashboard.add_equity_point(bot.get_balance())
```

## Future Enhancements

Potential improvements for future versions:
- Real-time updates via WebSockets
- Historical data export
- Custom alert thresholds
- Multi-bot dashboard support
- Mobile-responsive improvements
- Dark/light theme toggle
- Customizable chart timeframes
- Trade notes and annotations

## Support

For issues or questions about the dashboard:
1. Check the logs in `bot.log`
2. Review this documentation
3. Check the example script for proper usage patterns
4. Open an issue on GitHub with details about your problem
