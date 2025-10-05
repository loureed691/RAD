# Production Deployment Checklist

Use this checklist when deploying the KuCoin Futures Trading Bot to production.

## Pre-Deployment

- [ ] Server/VPS ready (Ubuntu/Debian recommended)
- [ ] KuCoin account created and verified
- [ ] KuCoin Futures API keys generated with correct permissions:
  - [ ] General permission enabled
  - [ ] Trade permission enabled
  - [ ] Withdraw permission **DISABLED** (security)
  - [ ] IP whitelist configured (if using static IP)
- [ ] Sufficient trading balance (minimum $100, recommended $500+)
- [ ] Domain/IP address for server (if applicable)
- [ ] SSH access to server configured

## Installation

- [ ] Clone repository: `git clone https://github.com/loureed691/RAD.git`
- [ ] Navigate to directory: `cd RAD`
- [ ] Run automated deployment: `./deploy.sh`
  - [ ] System packages updated
  - [ ] Python 3.11 installed
  - [ ] Dependencies installed
  - [ ] Directories created (logs/, models/)
  - [ ] .env file created
  - [ ] Tests passed
  - [ ] Systemd service installed

## Configuration

- [ ] Edit .env file: `nano .env`
- [ ] Add KuCoin API credentials:
  - [ ] KUCOIN_API_KEY
  - [ ] KUCOIN_API_SECRET
  - [ ] KUCOIN_API_PASSPHRASE
- [ ] Review/customize trading parameters (optional - auto-configured by default):
  - [ ] LEVERAGE (optional override)
  - [ ] MAX_POSITION_SIZE (optional override)
  - [ ] RISK_PER_TRADE (optional override)
  - [ ] CHECK_INTERVAL
  - [ ] MAX_OPEN_POSITIONS
- [ ] Set file permissions: `chmod 600 .env`

## Testing

- [ ] Run health check: `python3 health_check.py`
- [ ] Verify all checks pass
- [ ] Test API connection: `python3 production_start.py` (Ctrl+C to stop)
- [ ] Check balance is detected correctly
- [ ] Run bot tests: `python3 test_bot.py`
- [ ] All tests should pass (12/12)

## Service Deployment

- [ ] Enable service: `sudo systemctl enable kucoin-bot`
- [ ] Start service: `sudo systemctl start kucoin-bot`
- [ ] Check status: `sudo systemctl status kucoin-bot`
- [ ] Service should show "active (running)"
- [ ] View real-time logs: `sudo journalctl -u kucoin-bot -f`
- [ ] Verify bot is initializing correctly

## Initial Monitoring (First 24 Hours)

- [ ] Check logs every 2-4 hours
- [ ] Monitor bot log file: `tail -f logs/bot.log`
- [ ] Verify market scanning is working
- [ ] Watch for first trade signals
- [ ] Confirm trades execute correctly
- [ ] Monitor balance changes
- [ ] Check for any error messages
- [ ] Verify trailing stops are working

## Post-Deployment Setup

- [ ] Set up automated health checks:
  ```bash
  (crontab -l 2>/dev/null; echo "0 * * * * cd /path/to/RAD && python3 health_check.py >> logs/health.log 2>&1") | crontab -
  ```
- [ ] Configure log rotation (prevents disk filling):
  ```bash
  sudo nano /etc/logrotate.d/kucoin-bot
  # Add configuration for logs/bot.log
  ```
- [ ] Set up disk space monitoring
- [ ] Configure email alerts (optional)
- [ ] Document your setup for future reference

## Security Hardening

- [ ] Verify .env file permissions: `ls -la .env` (should show -rw-------)
- [ ] Ensure .env is in .gitignore
- [ ] Configure firewall (ufw/iptables) if applicable
- [ ] Enable automatic security updates: `sudo apt install unattended-upgrades`
- [ ] Disable password SSH authentication (use keys only)
- [ ] Review KuCoin API key permissions regularly
- [ ] Keep backup of API keys in secure location (offline)

## Ongoing Maintenance

Weekly:
- [ ] Review logs for errors: `grep ERROR logs/bot.log`
- [ ] Check performance metrics
- [ ] Verify balance is growing as expected
- [ ] Run health check: `python3 health_check.py`

Monthly:
- [ ] Update bot: `git pull && sudo systemctl restart kucoin-bot`
- [ ] Review and optimize parameters if needed
- [ ] Check server disk space: `df -h`
- [ ] Review API key security
- [ ] Analyze trading performance

Quarterly:
- [ ] Rotate API keys (generate new, delete old)
- [ ] Review server security updates
- [ ] Consider scaling up if performance is good
- [ ] Backup configuration and model files

## Troubleshooting Checklist

If bot stops working:
- [ ] Check service status: `sudo systemctl status kucoin-bot`
- [ ] View recent logs: `sudo journalctl -u kucoin-bot -n 100`
- [ ] Run health check: `python3 health_check.py`
- [ ] Check API credentials are still valid
- [ ] Verify internet connectivity
- [ ] Check KuCoin API status
- [ ] Review available balance
- [ ] Restart service: `sudo systemctl restart kucoin-bot`

## Emergency Procedures

If you need to stop trading immediately:
```bash
# Stop the service
sudo systemctl stop kucoin-bot

# Manually close all positions (optional)
# Log into KuCoin and close positions manually
```

## Success Criteria

Your deployment is successful when:
- [x] Service runs without errors for 24+ hours
- [x] Bot successfully scans markets
- [x] Trades execute and close properly
- [x] Trailing stops adjust correctly
- [x] Balance increases over time (after initial learning period)
- [x] No critical errors in logs
- [x] Health checks pass consistently

## Support Resources

- **Quick Deployment**: [QUICK_DEPLOY.md](QUICK_DEPLOY.md)
- **Full Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Setup**: [API_SETUP.md](API_SETUP.md)
- **Configuration**: [AUTO_CONFIG.md](AUTO_CONFIG.md)
- **Bot Features**: [README.md](README.md)
- **Troubleshooting**: Check logs and documentation

---

**Good luck with your deployment! Start small, monitor closely, and scale up gradually.** 🚀
