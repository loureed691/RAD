# Deployment Guide

## Overview

This guide covers deploying the KuCoin Futures Trading Bot to production environments.

## Deployment Options

### 1. Local Machine / Server

**Pros:**
- Full control
- Easy debugging
- No additional costs

**Cons:**
- Must stay online 24/7
- No redundancy
- Manual updates

### 2. Cloud VPS (Recommended)

**Providers:**
- AWS EC2
- DigitalOcean
- Google Cloud
- Linode
- Vultr

**Pros:**
- 99.9%+ uptime
- Scalable
- Professional infrastructure

**Cons:**
- Monthly cost ($5-20/month)
- Requires server management

### 3. Docker Container

**Pros:**
- Consistent environment
- Easy deployment
- Portable

**Cons:**
- Docker learning curve
- Additional layer of complexity

## Production Deployment

### Option A: Direct Python Deployment

#### Step 1: Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3-pip -y

# Install system dependencies
sudo apt install git -y
```

#### Step 2: Clone Repository

```bash
# Clone the repo
git clone https://github.com/loureed691/RAD.git
cd RAD

# Install Python dependencies
pip3 install -r requirements.txt
```

#### Step 3: Configure

```bash
# Create .env file
cp .env.example .env

# Edit with your credentials
nano .env
```

#### Step 4: Test

```bash
# Run tests
python3 test_bot.py

# Test backtest
python3 example_backtest.py
```

#### Step 5: Run as Service

Create systemd service file:

```bash
sudo nano /etc/systemd/system/kucoin-bot.service
```

Add content:

```ini
[Unit]
Description=KuCoin Futures Trading Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/RAD
Environment="PATH=/home/ubuntu/.local/bin:/usr/bin"
ExecStart=/usr/bin/python3 /home/ubuntu/RAD/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable kucoin-bot

# Start service
sudo systemctl start kucoin-bot

# Check status
sudo systemctl status kucoin-bot

# View logs
journalctl -u kucoin-bot -f
```

### Option B: Docker Deployment

#### Step 1: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group
sudo usermod -aG docker $USER
```

#### Step 2: Build and Run

```bash
# Clone repository
git clone https://github.com/loureed691/RAD.git
cd RAD

# Create .env file
cp .env.example .env
nano .env

# Build image
docker-compose build

# Start container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down
```

#### Docker Management Commands

```bash
# View running containers
docker ps

# View logs
docker-compose logs -f trading-bot

# Restart container
docker-compose restart

# Stop container
docker-compose stop

# Start container
docker-compose start

# Remove container
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## Monitoring

### System Monitoring

#### Check Bot Status

```bash
# If using systemd
sudo systemctl status kucoin-bot

# If using Docker
docker ps
```

#### View Logs

```bash
# Real-time logs
tail -f logs/bot.log

# Last 100 lines
tail -n 100 logs/bot.log

# Search for errors
grep ERROR logs/bot.log

# With systemd
journalctl -u kucoin-bot -f

# With Docker
docker-compose logs -f
```

#### Monitor Resources

```bash
# CPU and Memory usage
htop

# Disk usage
df -h

# Network usage
iftop
```

### Application Monitoring

Create monitoring script `monitor.sh`:

```bash
#!/bin/bash

echo "=== KuCoin Bot Status ==="
echo

# Check if running
if pgrep -f "python.*bot.py" > /dev/null; then
    echo "✓ Bot is running"
else
    echo "✗ Bot is not running"
fi

# Check recent errors
ERROR_COUNT=$(tail -n 1000 logs/bot.log | grep -c ERROR)
echo "Recent errors: $ERROR_COUNT"

# Check disk space
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}')
echo "Disk usage: $DISK_USAGE"

# Check log file size
LOG_SIZE=$(du -h logs/bot.log | cut -f1)
echo "Log file size: $LOG_SIZE"

# Last log entry
echo
echo "Last log entry:"
tail -n 1 logs/bot.log
```

Make executable and run:

```bash
chmod +x monitor.sh
./monitor.sh
```

### Set Up Alerts

#### Email Alerts (using sendmail)

```bash
# Install sendmail
sudo apt install sendmail -y

# Create alert script
cat > alert.sh << 'EOF'
#!/bin/bash
ERROR_COUNT=$(tail -n 100 logs/bot.log | grep -c ERROR)
if [ $ERROR_COUNT -gt 5 ]; then
    echo "High error count detected: $ERROR_COUNT" | mail -s "Bot Alert" your@email.com
fi
EOF

chmod +x alert.sh

# Add to crontab (runs every hour)
(crontab -l 2>/dev/null; echo "0 * * * * /path/to/RAD/alert.sh") | crontab -
```

## Backup and Recovery

### Backup Strategy

Create backup script `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configuration
cp .env $BACKUP_DIR/.env.$DATE

# Backup ML model
cp -r models $BACKUP_DIR/models.$DATE

# Backup logs (last 7 days)
find logs -mtime -7 -type f -exec cp {} $BACKUP_DIR/logs.$DATE/ \;

# Keep only last 7 backups
ls -t $BACKUP_DIR | tail -n +8 | xargs -I {} rm -rf $BACKUP_DIR/{}

echo "Backup completed: $BACKUP_DIR"
```

Schedule daily backups:

```bash
chmod +x backup.sh
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/RAD/backup.sh") | crontab -
```

### Recovery

```bash
# Restore configuration
cp /home/ubuntu/backups/.env.YYYYMMDD_HHMMSS .env

# Restore ML model
cp -r /home/ubuntu/backups/models.YYYYMMDD_HHMMSS models/

# Restart bot
sudo systemctl restart kucoin-bot
# or
docker-compose restart
```

## Security

### Firewall Setup

```bash
# Install UFW
sudo apt install ufw -y

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Secure .env File

```bash
# Set restrictive permissions
chmod 600 .env

# Verify
ls -l .env
```

### Regular Updates

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update Python packages
pip install -U -r requirements.txt

# Update CCXT (important for API changes)
pip install -U ccxt
```

## Optimization

### Performance Tuning

1. **Reduce Check Interval** for faster reactions:
   ```env
   CHECK_INTERVAL=30
   ```

2. **Increase Workers** for faster scanning:
   Add to your `.env` file:
   ```env
   MAX_WORKERS=30  # Default is 20, increase for faster market scanning
   ```
   
   Higher values = faster market scanning but more system resources used.
   Recommended values:
   - Conservative: 10-15 workers
   - **Recommended: 20 workers** (default)
   - Aggressive: 30-40 workers (requires good CPU/network)

3. **Optimize Logging**:
   ```env
   LOG_LEVEL=WARNING  # Less verbose
   ```

### Resource Limits

Set memory and CPU limits with systemd:

```ini
[Service]
MemoryLimit=512M
CPUQuota=50%
```

Or with Docker:

```yaml
services:
  trading-bot:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

## Troubleshooting

### Bot Crashes

1. Check logs for errors
2. Verify API credentials
3. Check available balance
4. Verify network connectivity
5. Check KuCoin API status

### High Memory Usage

1. Reduce check interval
2. Limit historical data
3. Clear old logs
4. Restart periodically

### Slow Performance

1. Reduce number of pairs scanned
2. Increase check interval
3. Optimize indicator calculations
4. Use faster server

## Maintenance

### Daily Tasks

- [ ] Check bot status
- [ ] Review trading performance
- [ ] Check for errors in logs
- [ ] Verify API connectivity

### Weekly Tasks

- [ ] Review win rate and P/L
- [ ] Analyze signal quality
- [ ] Check ML model performance
- [ ] Update parameters if needed

### Monthly Tasks

- [ ] System updates
- [ ] Review and optimize strategy
- [ ] Backup configuration and models
- [ ] Check for bot updates
- [ ] Rotate API keys (optional)

## Scaling

### Running Multiple Instances

To trade multiple strategies or accounts:

1. Clone to different directories
2. Use different .env files
3. Configure different ports (if needed)
4. Use different log files

```bash
# Instance 1 (Conservative)
cp -r RAD RAD-conservative
cd RAD-conservative
# Edit .env with conservative settings

# Instance 2 (Aggressive)
cp -r RAD RAD-aggressive
cd RAD-aggressive
# Edit .env with aggressive settings
```

### Load Balancing

For high-frequency trading:
- Use multiple servers
- Distribute across regions
- Implement failover

## Support

### Getting Help

1. Check logs first
2. Review documentation
3. Test individual components
4. Check KuCoin API status
5. Verify configuration

### Reporting Issues

Include:
- Log excerpts
- Configuration (without credentials)
- Steps to reproduce
- Expected vs actual behavior
- Environment details

## Legal and Compliance

### Important Notes

- Automated trading may be regulated in your jurisdiction
- Ensure compliance with local laws
- KuCoin terms of service apply
- Use at your own risk
- No warranty provided

### Disclaimer

This bot is for educational purposes only. Trading cryptocurrency futures involves substantial risk of loss. Past performance does not guarantee future results. The authors are not responsible for any financial losses.

## Production Checklist

Before going live:

- [ ] API credentials configured
- [ ] Firewall enabled
- [ ] Bot tested successfully
- [ ] Monitoring set up
- [ ] Backup strategy in place
- [ ] Logs being collected
- [ ] Resource limits configured
- [ ] Security measures implemented
- [ ] Emergency stop procedure documented
- [ ] Contact information updated
- [ ] Insurance/risk management considered

## Next Steps

1. Start with paper trading (if available)
2. Use small position sizes initially
3. Monitor closely for first week
4. Gradually increase position sizes
5. Optimize based on performance
6. Scale up as confident

Good luck with your deployment! 🚀
