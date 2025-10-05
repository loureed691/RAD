# Web Dashboard Quick Reference

## 🚀 Quick Start

### Start Bot with Dashboard
```bash
python start_with_dashboard.py
```
Dashboard automatically opens at: **http://localhost:5000**

### Alternative Start
```bash
python bot.py
```
Then manually open: **http://localhost:5000**

---

## 📊 Dashboard Sections

### Top Bar
- **Status Badge**: 🟢 Running / 🔴 Stopped / 🟡 Initializing
- **Balance**: Current USDT balance
- **Uptime**: Bot running time
- **Auto-Refresh**: Updates every 3 seconds

### Performance Card
- Total Trades
- Win Rate (%)
- Total P/L (%)
- Profit Factor

### Configuration Card
- Leverage (e.g., 10x)
- Max Positions
- Risk Per Trade (%)
- Check Interval (seconds)

### Win/Loss Stats Card
- Winning Trades (green)
- Losing Trades (red)
- Average Win (%)
- Average Loss (%)

### Open Positions Table
- Symbol
- Side (LONG/SHORT)
- Entry Price
- Current Price
- Position Size
- Leverage
- Current P/L (%)

### Current Opportunities List
- Trading pairs being evaluated
- BUY/SELL signals
- Opportunity score
- Confidence percentage
- Current price

### Recent Trades Table
- Last 20 completed trades
- Timestamp
- Symbol and side
- Entry/exit prices
- P/L percentage
- Trade duration

---

## 🎨 Color Coding

- **Green**: Profits, LONG positions, winning trades
- **Red**: Losses, SHORT positions, losing trades
- **Blue**: Neutral information, headers
- **Orange**: Warnings, initializing state

---

## 🔧 Troubleshooting

### Dashboard Won't Open
1. Check bot is running: `ps aux | grep python`
2. Verify port 5000 is free: `lsof -ti:5000`
3. Check logs: `tail -f logs/bot.log`

### Dashboard Shows "Loading..."
- Wait 30 seconds for first cycle to complete
- Refresh browser (F5)

### Can't Access Remotely
Use SSH tunnel:
```bash
ssh -L 5000:localhost:5000 user@server
```
Then open http://localhost:5000 on your local machine

---

## 📱 API Endpoints

For custom integrations:

```
GET /api/status          - Bot status and balance
GET /api/positions       - Open positions
GET /api/trades?limit=N  - Recent trades
GET /api/performance     - Performance metrics
GET /api/opportunities   - Trading opportunities
GET /api/config          - Bot configuration
GET /api/health          - Health check
```

Example:
```bash
curl http://localhost:5000/api/status | jq
```

---

## 💡 Pro Tips

1. **Bookmark**: Save http://localhost:5000 for quick access
2. **Second Monitor**: Keep dashboard open while working
3. **Mobile Access**: Use SSH tunnel to view on phone
4. **Screenshots**: Capture dashboard for performance reviews
5. **Browser Console**: Press F12 to see live data updates

---

## 🔐 Security Notes

- Dashboard has **no authentication** - secure your server
- Use **SSH tunnel** for remote access
- Don't expose port 5000 to internet directly
- Run on trusted networks only

---

## 📚 Full Documentation

- Complete guide: [WEB_DASHBOARD.md](WEB_DASHBOARD.md)
- Bot documentation: [README.md](README.md)
- Setup guide: [API_SETUP.md](API_SETUP.md)

---

**Built with Flask + Pure JavaScript - No frameworks needed!** 🎉
