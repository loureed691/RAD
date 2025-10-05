# Web Dashboard - Live Bot Monitoring

## Overview

The RAD Trading Bot now includes a **live web dashboard** for real-time monitoring of your bot's performance, positions, and trading activity. No need to dig through log files - see everything at a glance in your browser!

## 🎯 Features

### Real-Time Monitoring
- **Bot Status**: Live status indicator (Running, Stopped, Initializing)
- **Balance**: Current USDT balance updates every 3 seconds
- **Uptime**: Track how long the bot has been running
- **Auto-Refresh**: Dashboard automatically updates every 3 seconds

### Position Management
- **Open Positions**: See all your active positions in real-time
  - Symbol, side (LONG/SHORT), entry/current price
  - Position size and leverage
  - Current profit/loss percentage
- **Live Updates**: P/L updates as prices change

### Trading Activity
- **Recent Trades**: View your last 20 completed trades
  - Entry and exit prices
  - P/L for each trade
  - Trade duration
- **Trade History**: Automatically tracked and displayed

### Performance Metrics
- **Win Rate**: Percentage of winning trades
- **Total P/L**: Overall profit/loss percentage
- **Win/Loss Stats**: Winning vs losing trade counts
- **Average Win/Loss**: Average profit on wins, loss on losses
- **Profit Factor**: Ratio of total profits to total losses

### Market Opportunities
- **Current Signals**: See top 5 trading opportunities the bot is evaluating
  - Trading pair and signal (BUY/SELL)
  - Confidence score and opportunity score
  - Current price

### Bot Configuration
- **Leverage**: Current leverage setting
- **Max Positions**: Maximum concurrent positions
- **Risk Per Trade**: Risk percentage per trade
- **Check Interval**: How often the bot scans markets

## 🚀 Quick Start

### Option 1: Use the Start Script (Recommended)

```bash
python start_with_dashboard.py
```

This will:
1. Check dependencies and configuration
2. Start the bot with the web dashboard
3. Automatically open the dashboard in your browser
4. Display the URL: http://localhost:5000

### Option 2: Standard Bot Start

```bash
python bot.py
```

The dashboard starts automatically when you run the bot. Just open http://localhost:5000 in your browser.

### Option 3: Manual Start with Custom Port

If you need to use a different port, modify the dashboard initialization in `bot.py`:

```python
self.dashboard = BotDashboard(port=8080)  # Use port 8080 instead of 5000
```

## 📊 Dashboard Interface

### Header Section
- **Bot Status Badge**: Color-coded status indicator
  - 🟢 Green = Running
  - 🔴 Red = Stopped
  - 🟡 Orange = Initializing
- **Balance Display**: Current USDT balance
- **Uptime Counter**: Hours and minutes bot has been running
- **Refresh Indicator**: Shows auto-refresh is active

### Performance Cards
Three metric cards showing:
1. **Performance**: Total trades, win rate, total P/L, profit factor
2. **Configuration**: Leverage, max positions, risk per trade, check interval
3. **Win/Loss Stats**: Winning/losing trade counts, average win/loss

### Position Table
Real-time table of open positions with:
- Symbol name
- Side (LONG/SHORT) with color coding
- Entry price vs current price
- Position size in contracts
- Leverage used
- Current P/L with color coding (green=profit, red=loss)

### Opportunities List
Scrollable list of current trading opportunities showing:
- Symbol and signal (BUY/SELL) badges
- Opportunity score and confidence percentage
- Current market price

### Recent Trades Table
Last 20 trades with:
- Timestamp
- Symbol and side
- Entry and exit prices
- P/L percentage
- Trade duration in minutes

## 🎨 Visual Design

- **Modern Interface**: Clean, professional design with gradient background
- **Color Coding**:
  - Green for profits and LONG positions
  - Red for losses and SHORT positions
  - Blue for neutral information
- **Responsive Layout**: Works on desktop, tablet, and mobile
- **Auto-Refresh**: No need to manually refresh the page
- **Empty States**: Clear messaging when no data is available

## 🔧 Technical Details

### Technology Stack
- **Backend**: Flask (Python web framework)
- **Frontend**: Pure HTML/CSS/JavaScript (no dependencies)
- **Communication**: REST API with JSON responses
- **Threading**: Dashboard runs in separate thread from bot

### API Endpoints

The dashboard provides the following API endpoints:

```
GET /                      - Main dashboard page
GET /api/status           - Bot status, balance, uptime
GET /api/positions        - Open positions
GET /api/trades?limit=N   - Recent trades (default 50)
GET /api/performance      - Performance metrics
GET /api/opportunities    - Current trading opportunities
GET /api/config           - Bot configuration
GET /api/health           - Health check endpoint
```

### Data Flow

1. **Bot → Dashboard**: Bot updates shared data structure after each cycle
2. **Dashboard → Browser**: Flask serves data via REST API
3. **Browser → Dashboard**: JavaScript polls API every 3 seconds
4. **Auto-Update**: Dashboard automatically refreshes all sections

## 📱 Accessing the Dashboard

### Local Access
```
http://localhost:5000
```

### Remote Access (Advanced)
If running on a server and want to access remotely:

1. **SSH Tunnel** (Recommended for security):
```bash
ssh -L 5000:localhost:5000 user@your-server
```
Then open http://localhost:5000 on your local machine.

2. **Firewall Configuration** (Less secure):
Open port 5000 in your firewall, then access via:
```
http://your-server-ip:5000
```
⚠️ **Security Warning**: This exposes the dashboard to the internet. Only use with proper authentication or in secure networks.

## 🛠️ Customization

### Change Dashboard Port

In `bot.py`, modify the dashboard initialization:

```python
self.dashboard = BotDashboard(port=8080)
```

### Adjust Refresh Rate

In `templates/dashboard.html`, modify the setInterval calls:

```javascript
// Change from 3000ms (3 seconds) to 5000ms (5 seconds)
setInterval(() => {
    updateStatus();
    updatePerformance();
    updatePositions();
    updateOpportunities();
}, 5000);
```

### Add Custom Metrics

1. Add data to `bot.py`:
```python
self.dashboard.bot_data['custom_metric'] = value
```

2. Create API endpoint in `dashboard.py`:
```python
@self.app.route('/api/custom')
def get_custom():
    return jsonify({'value': self.bot_data['custom_metric']})
```

3. Display in `templates/dashboard.html`:
```javascript
async function updateCustom() {
    const response = await fetch('/api/custom');
    const data = await response.json();
    document.getElementById('custom-value').textContent = data.value;
}
```

## 🔍 Troubleshooting

### Dashboard Won't Start

**Problem**: Port 5000 already in use
```
OSError: [Errno 48] Address already in use
```

**Solution**: Either:
1. Stop the process using port 5000: `lsof -ti:5000 | xargs kill -9`
2. Use a different port in `bot.py`

### Dashboard Shows No Data

**Problem**: All sections show "Loading..." or empty states

**Possible Causes**:
1. Bot hasn't completed first cycle yet - wait 30 seconds
2. API connection issue - check browser console for errors
3. Bot encountered an error - check `logs/bot.log`

**Solution**: 
1. Wait for first trading cycle to complete
2. Check browser console (F12) for JavaScript errors
3. Review bot logs for errors

### Can't Access Dashboard Remotely

**Problem**: Dashboard works locally but not from another machine

**Solution**:
1. Verify Flask is binding to 0.0.0.0 (it is by default)
2. Check firewall settings: `sudo ufw allow 5000`
3. Use SSH tunnel for secure access (see above)

### Dashboard Freezes or Stops Updating

**Problem**: Dashboard stops refreshing

**Solution**:
1. Refresh the browser page (F5)
2. Check if bot is still running: `ps aux | grep python`
3. Review bot logs for errors
4. Restart the bot if needed

## 📈 Performance Impact

The web dashboard has **minimal impact** on bot performance:

- **CPU**: <1% additional CPU usage
- **Memory**: ~20-30MB for Flask server
- **Network**: Negligible (local REST API calls)
- **Trading**: No impact on trading logic or decision-making

The dashboard runs in a separate daemon thread and doesn't block the main bot operations.

## 🔐 Security Considerations

### For Production Use:

1. **Authentication**: The dashboard has no built-in authentication. For production:
   - Use SSH tunneling for remote access
   - Or add authentication (Flask-Login, basic auth, etc.)
   
2. **HTTPS**: For remote access, use HTTPS:
   - Set up reverse proxy (nginx, Apache)
   - Use SSL certificates (Let's Encrypt)
   
3. **Firewall**: Don't expose dashboard port directly to internet
   - Use VPN or SSH tunnel
   - Or restrict access to specific IPs

4. **API Security**: The REST API has no authentication
   - Only expose to trusted networks
   - Consider adding API keys for production

## 🎯 Best Practices

1. **Monitor Regularly**: Check dashboard at least daily
2. **Track Performance**: Watch win rate and profit factor trends
3. **Review Positions**: Ensure open positions align with expectations
4. **Check Opportunities**: Verify bot is finding good trading signals
5. **Log Access**: Dashboard URL logged at bot startup
6. **Error Handling**: Dashboard continues working even if some data fails to update

## 📚 Related Documentation

- **Main README**: [README.md](README.md) - Bot overview and features
- **Setup Guide**: [API_SETUP.md](API_SETUP.md) - KuCoin API configuration
- **Quick Start**: [QUICK_START.md](QUICK_START.md) - Getting started guide
- **Auto Config**: [AUTO_CONFIG.md](AUTO_CONFIG.md) - Auto-configuration feature

## 🤝 Support

If you encounter issues:

1. Check this documentation
2. Review `logs/bot.log` for errors
3. Check browser console (F12) for JavaScript errors
4. Verify all dependencies installed: `pip install -r requirements.txt`
5. Test Flask installation: `python -c "import flask; print('OK')"`

## 🎉 Summary

The web dashboard transforms the RAD Trading Bot from a command-line tool into a modern, visual trading platform. With real-time monitoring, you can:

- ✅ See your bot's performance at a glance
- ✅ Monitor positions and P/L in real-time
- ✅ Track trade history and metrics
- ✅ Verify bot is finding good opportunities
- ✅ Ensure proper configuration

**No more digging through log files - everything you need is in your browser!** 🚀
