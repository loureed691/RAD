# Quick Deployment Guide

This guide helps you deploy the KuCoin Futures Trading Bot to production in minutes.

## 🚀 One-Line Deployment (Ubuntu/Debian)

For a fresh Ubuntu/Debian server:

```bash
./deploy.sh
```

This automated script will:
- ✅ Update system packages
- ✅ Install Python 3.11
- ✅ Install all dependencies
- ✅ Create necessary directories
- ✅ Setup .env configuration file
- ✅ Install systemd service
- ✅ Run tests

## 📋 Manual Deployment Steps

### 1. Clone Repository

```bash
git clone https://github.com/loureed691/RAD.git
cd RAD
```

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Configure API Credentials

```bash
cp .env.example .env
nano .env  # Add your KuCoin API credentials
```

### 4. Test Bot

```bash
python3 test_bot.py
```

### 5. Start Bot (Development)

```bash
python3 production_start.py
```

### 6. Deploy as Service (Production)

```bash
# Run automated deployment
./deploy.sh

# Enable service to start on boot
sudo systemctl enable kucoin-bot

# Start the service
sudo systemctl start kucoin-bot

# Check status
sudo systemctl status kucoin-bot
```

## 🔍 Health Monitoring

Check bot health at any time:

```bash
python3 health_check.py
```

This checks:
- Service status
- Configuration
- Log files
- Dependencies
- System resources

## 📊 View Logs

### Application Logs
```bash
tail -f logs/bot.log
```

### Service Logs (systemd)
```bash
sudo journalctl -u kucoin-bot -f
```

## 🎛️ Service Management

```bash
# Start bot
sudo systemctl start kucoin-bot

# Stop bot
sudo systemctl stop kucoin-bot

# Restart bot
sudo systemctl restart kucoin-bot

# View status
sudo systemctl status kucoin-bot

# Enable auto-start on boot
sudo systemctl enable kucoin-bot

# Disable auto-start
sudo systemctl disable kucoin-bot
```

## 🐳 Docker Deployment

### Quick Start

```bash
# Create .env file
cp .env.example .env
nano .env  # Add credentials

# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Docker Commands

```bash
# Rebuild after code changes
docker-compose build

# Restart container
docker-compose restart

# View logs
docker-compose logs -f trading-bot

# Execute command in container
docker-compose exec trading-bot python3 health_check.py
```

## 🔒 Security Checklist

Before going live:

- [ ] API keys have correct permissions (General, Trade - NOT Withdraw)
- [ ] IP whitelist configured on KuCoin (if using fixed IP)
- [ ] .env file permissions set correctly (600)
- [ ] Logs directory has sufficient space
- [ ] System has adequate memory (minimum 1GB RAM)
- [ ] Monitoring/alerting configured
- [ ] Backup API keys stored securely offline

## 📈 Post-Deployment

1. **Monitor for first 24 hours**
   - Check logs every few hours
   - Verify trades are executing correctly
   - Monitor balance changes

2. **Run health check daily**
   ```bash
   python3 health_check.py
   ```

3. **Review logs weekly**
   ```bash
   grep ERROR logs/bot.log
   ```

4. **Update bot regularly**
   ```bash
   git pull
   sudo systemctl restart kucoin-bot
   ```

## 🆘 Troubleshooting

### Bot Won't Start

1. Check configuration:
   ```bash
   python3 production_start.py
   ```

2. Check service logs:
   ```bash
   sudo journalctl -u kucoin-bot -n 50
   ```

3. Run health check:
   ```bash
   python3 health_check.py
   ```

### No Trades Executing

- Check available balance (minimum $100 recommended)
- Verify API permissions include "Trade"
- Review logs for validation errors
- Check market conditions (may not find opportunities)

### High Memory Usage

- Check for memory leaks in logs
- Restart service: `sudo systemctl restart kucoin-bot`
- Monitor system: `htop`

## 📞 Support

- **Full Documentation**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Setup**: See [API_SETUP.md](API_SETUP.md)
- **Configuration**: See [AUTO_CONFIG.md](AUTO_CONFIG.md)
- **Features**: See [README.md](README.md)

## ⚠️ Important Notes

- **Start small**: Test with minimal capital first ($100-500)
- **Monitor regularly**: Especially first week
- **Risk management**: Bot auto-configures based on balance
- **Never share API keys**: Keep .env file secure
- **Backup configuration**: Keep a copy of .env securely

---

**Ready to go live? Run `./deploy.sh` and follow the prompts!** 🚀
