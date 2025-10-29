# Production Readiness Runbook for RAD Trading Bot

**Version:** 1.0  
**Date:** 2025-10-29  
**Status:** Pre-Production Validation Phase

---

## Executive Summary

This runbook provides step-by-step procedures for deploying and operating the RAD trading bot in production. The bot has been significantly upgraded with:

- 500-scenario stress testing framework
- Strategy collision detection and prevention
- Profitability optimization with Bayesian search
- Enhanced backtesting with realistic fees, latency, and slippage
- Comprehensive risk management and safety features

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [GO/NO-GO Decision Criteria](#gono-go-decision-criteria)
4. [Deployment Procedures](#deployment-procedures)
5. [Monitoring and Alerts](#monitoring-and-alerts)
6. [Emergency Procedures](#emergency-procedures)
7. [Performance Validation](#performance-validation)
8. [Rollback Plan](#rollback-plan)

---

## System Requirements

### Hardware
- **CPU:** Minimum 4 cores, recommended 8+ cores
- **RAM:** Minimum 8GB, recommended 16GB+
- **Storage:** 50GB+ free space for logs and data
- **Network:** Stable connection with <200ms latency to exchange

### Software
- **OS:** Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Python:** 3.12+ (tested on 3.12.3)
- **Dependencies:** All packages in requirements.lock

### Exchange Requirements
- **KuCoin Futures Account** with API access
- **API Key/Secret/Passphrase** with futures trading permissions
- **Minimum Balance:** Recommended $500+ for effective operation
- **IP Whitelisting:** Configure if required by exchange

---

## Pre-Deployment Checklist

### Phase 1: Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/loureed691/RAD.git
cd RAD

# 2. Install dependencies
make setup
make install

# 3. Configure environment
cp .env.example .env
# Edit .env with your API credentials

# 4. Validate configuration
make validate-config
```

**Checklist:**
- [ ] Repository cloned successfully
- [ ] All dependencies installed without errors
- [ ] `.env` file created with valid API credentials
- [ ] Configuration validation passed

### Phase 2: Safety & Testing

```bash
# 1. Run unit tests
make test-unit

# 2. Run integration tests
make test-integration

# 3. Run comprehensive tests
make test

# 4. Validate backtest engine
make backtest
```

**Checklist:**
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Backtest completes without errors
- [ ] Performance metrics are calculated correctly

### Phase 3: Stress Testing

```bash
# 1. Run stress test suite (500 scenarios)
make stress

# 2. Review stress test report
cat stress_test_results/STRESS_TEST_REPORT.txt

# 3. Analyze failures
python -c "
import json
with open('stress_test_results/results.json') as f:
    results = json.load(f)
    failed = [r for r in results if not r['success']]
    print(f'Failed scenarios: {len(failed)}')
    for r in failed[:5]:
        print(f'  - {r[\"scenario_name\"]}: {r[\"error_message\"]}')
"
```

**Checklist:**
- [ ] Stress test completes all 500 scenarios
- [ ] Failure rate < 5%
- [ ] No unhandled exceptions
- [ ] No strategy collisions detected
- [ ] Performance metrics within acceptable ranges

### Phase 4: Profitability Validation

```bash
# 1. Run profitability optimization
make optimize

# 2. Review optimization results
cat optimization_results.json

# 3. Validate metrics meet targets
python -c "
import json
with open('optimization_results.json') as f:
    data = json.load(f)
    results = data['best_results']
    print(f'Profit Factor: {results.get(\"profit_factor\", 0):.2f} (target: ≥1.2)')
    print(f'Sharpe Ratio: {results.get(\"sharpe_ratio\", 0):.2f} (target: ≥1.0)')
    print(f'Sortino Ratio: {results.get(\"sortino_ratio\", 0):.2f} (target: ≥1.5)')
    print(f'Max Drawdown: {abs(results.get(\"max_drawdown_pct\", 100)):.2f}% (target: ≤15%)')
    print(f'Win Rate: {results.get(\"win_rate\", 0)*100:.1f}% (target: ≥45%)')
"
```

**Checklist:**
- [ ] Optimization completes successfully
- [ ] Profit Factor ≥ 1.2
- [ ] Sharpe Ratio ≥ 1.0
- [ ] Sortino Ratio ≥ 1.5
- [ ] Max Drawdown ≤ 15%
- [ ] Win Rate ≥ 45%
- [ ] Positive expectancy after fees

### Phase 5: Paper Trading Validation

```bash
# 1. Enable paper trading mode
echo "TEST_MODE=true" >> .env

# 2. Start bot in paper trading mode
make paper-trade

# 3. Monitor for 24-48 hours
# Watch logs, dashboard, and metrics

# 4. Review paper trading results
# Check for stability, correct behavior, no crashes
```

**Checklist:**
- [ ] Bot runs for 24+ hours without crashes
- [ ] Orders are placed correctly (paper only)
- [ ] Position management works as expected
- [ ] Risk limits are respected
- [ ] No memory leaks or resource issues
- [ ] Dashboard shows correct data

---

## GO/NO-GO Decision Criteria

### GO Criteria (All must be YES)

**Testing & Validation:**
- [ ] ✅ All unit and integration tests pass
- [ ] ✅ Stress test failure rate < 5%
- [ ] ✅ Profitability targets met in optimization
- [ ] ✅ Paper trading successful for 24+ hours
- [ ] ✅ No critical bugs or exceptions

**Performance Metrics:**
- [ ] ✅ Profit Factor ≥ 1.2
- [ ] ✅ Sharpe Ratio ≥ 1.0
- [ ] ✅ Sortino Ratio ≥ 1.5
- [ ] ✅ Max Drawdown ≤ 15%
- [ ] ✅ Win Rate ≥ 45%

**Infrastructure:**
- [ ] ✅ API credentials valid and tested
- [ ] ✅ Network connectivity stable
- [ ] ✅ Monitoring and alerts configured
- [ ] ✅ Backup and recovery plan in place
- [ ] ✅ Emergency stop procedures documented

**Risk Management:**
- [ ] ✅ Position limits configured
- [ ] ✅ Daily loss limits active
- [ ] ✅ Kill switch functional
- [ ] ✅ Circuit breakers tested
- [ ] ✅ Portfolio exposure limits set

**Operational:**
- [ ] ✅ Team trained on operations
- [ ] ✅ Escalation procedures defined
- [ ] ✅ 24/7 monitoring capability
- [ ] ✅ Rollback plan tested
- [ ] ✅ Sufficient account balance ($500+)

### NO-GO Criteria (Any one triggers NO-GO)

**Critical Issues:**
- [ ] ❌ Test failure rate > 5%
- [ ] ❌ Critical bugs in production code
- [ ] ❌ Profitability targets not met
- [ ] ❌ Paper trading failures or crashes
- [ ] ❌ Strategy collision issues detected

**Infrastructure Problems:**
- [ ] ❌ API connection unstable
- [ ] ❌ Network latency > 500ms
- [ ] ❌ Monitoring not functional
- [ ] ❌ Insufficient account balance

**Regulatory/Compliance:**
- [ ] ❌ API permissions insufficient
- [ ] ❌ Exchange restrictions in place
- [ ] ❌ Legal/compliance issues

### Decision Matrix

| Criteria Category | Weight | Required Score | Current Score |
|-------------------|--------|----------------|---------------|
| Testing & Validation | 30% | 28/30 | ___ |
| Performance Metrics | 25% | 23/25 | ___ |
| Infrastructure | 20% | 19/20 | ___ |
| Risk Management | 15% | 14/15 | ___ |
| Operational | 10% | 9/10 | ___ |
| **TOTAL** | **100%** | **≥90%** | **___** |

**GO Decision:** Total Score ≥ 90% AND no NO-GO criteria triggered

---

## Deployment Procedures

### Step 1: Final Verification

```bash
# Run complete validation suite
make test
make stress
make validate-config

# Check system resources
free -h
df -h
```

### Step 2: Start Production Bot

```bash
# Remove test mode flag
sed -i '/TEST_MODE/d' .env

# OR explicitly set to false
echo "TEST_MODE=false" >> .env

# Start bot with logging
nohup make live > bot_live.log 2>&1 &

# Get process ID
PID=$!
echo $PID > bot.pid
echo "Bot started with PID: $PID"
```

### Step 3: Immediate Monitoring (First 30 Minutes)

```bash
# Watch logs in real-time
tail -f logs/bot.log

# Monitor system resources
watch -n 5 'ps aux | grep bot.py'

# Check for errors
grep -i "error\|exception\|critical" logs/bot.log | tail -20

# Access dashboard
# Open http://localhost:5000 in browser
```

**Verify:**
- [ ] Bot is running (check PID)
- [ ] No immediate errors in logs
- [ ] Dashboard accessible and showing data
- [ ] First market scan completes successfully
- [ ] Memory usage is stable
- [ ] No API rate limit errors

### Step 4: First Hour Monitoring

**Check every 15 minutes:**
- [ ] Bot is still running
- [ ] No critical errors in logs
- [ ] Positions opened/closed correctly (if any)
- [ ] Risk limits are respected
- [ ] Dashboard metrics updating

### Step 5: First 24 Hours

**Check every 4 hours:**
- [ ] Overall P/L is reasonable
- [ ] No unexpected crashes or restarts
- [ ] Order execution is working
- [ ] Risk management is functioning
- [ ] No exchange API issues

---

## Monitoring and Alerts

### Key Metrics to Monitor

**Real-Time (Every Minute):**
- Bot process status (running/stopped)
- Active positions count
- Current P/L %
- API connection status

**Short-Term (Every 15 Minutes):**
- Win rate (last 10 trades)
- Average trade duration
- Drawdown %
- Position sizes

**Long-Term (Daily):**
- Total P/L
- Sharpe ratio
- Max drawdown
- Win rate %
- Total fees paid

### Alert Thresholds

**CRITICAL (Immediate Action Required):**
- ❗ Bot process stopped unexpectedly
- ❗ Daily loss > 10%
- ❗ Drawdown > 15%
- ❗ API connection lost > 5 minutes
- ❗ Exchange errors > 10 in 1 hour
- ❗ Position size > max allowed

**WARNING (Monitor Closely):**
- ⚠️ Daily loss > 5%
- ⚠️ Drawdown > 10%
- ⚠️ Win rate < 40% (last 20 trades)
- ⚠️ API latency > 2 seconds
- ⚠️ Memory usage > 80%

**INFO (Log for Review):**
- ℹ️ Position opened/closed
- ℹ️ Strategy change
- ℹ️ Configuration update
- ℹ️ Market regime change

### Dashboard Monitoring

Access dashboard at `http://localhost:5000`

**Key Dashboard Sections:**
- Real-time P/L chart
- Active positions table
- Recent trades history
- Performance metrics
- Risk metrics
- System health

---

## Emergency Procedures

### Emergency Stop (Kill Switch)

**Immediate Stop (Closes All Positions):**

```bash
# Method 1: Via Python (graceful)
python -c "
from risk_manager import RiskManager
rm = RiskManager(1000, 0.02, 3)
rm.activate_kill_switch('Emergency stop by operator')
print('Kill switch activated')
"

# Method 2: Stop bot process (immediate)
kill -SIGTERM $(cat bot.pid)

# Method 3: Force stop (last resort)
kill -9 $(cat bot.pid)
```

**Verify Stop:**
```bash
ps aux | grep bot.py
# Should show no running processes

# Check positions on exchange
# Log into KuCoin and verify all positions closed
```

### Partial Stop (Close Specific Position)

```bash
# Close position for specific symbol
python -c "
from position_manager import PositionManager
from kucoin_client import KuCoinClient
from config import Config

client = KuCoinClient(Config.API_KEY, Config.API_SECRET, Config.API_PASSPHRASE)
pm = PositionManager(client, 1000, 5, 10)

# Close position for BTC/USDT
pm.close_position('BTC/USDT:USDT', 'Manual close by operator')
"
```

### Handling Specific Emergencies

**1. Exchange API Down:**
- Bot will log errors but continue running
- Positions are safe on exchange
- Wait for API to recover
- If extended outage (>1 hour), manually close positions via exchange UI

**2. Rapid Drawdown (>10%):**
```bash
# Activate kill switch
python -c "
from risk_manager import RiskManager
rm = RiskManager(1000, 0.02, 3)
rm.activate_kill_switch('Rapid drawdown detected')
"

# Stop bot
kill $(cat bot.pid)

# Review logs for cause
grep -i "error\|loss\|drawdown" logs/bot.log | tail -50
```

**3. Unexpected Behavior:**
```bash
# Stop bot
kill $(cat bot.pid)

# Check open positions
python -c "
from kucoin_client import KuCoinClient
from config import Config
client = KuCoinClient(Config.API_KEY, Config.API_SECRET, Config.API_PASSPHRASE)
positions = client.get_positions()
for pos in positions:
    print(f'{pos[\"symbol\"]}: {pos[\"side\"]} {pos[\"size\"]} @ {pos[\"entry_price\"]}')
"

# Manually close positions if needed via exchange UI
```

**4. Memory Leak:**
```bash
# Check memory usage
ps aux | grep bot.py

# If memory usage > 2GB, restart bot
kill $(cat bot.pid)

# Wait for graceful shutdown
sleep 10

# Restart
nohup make live > bot_live.log 2>&1 &
echo $! > bot.pid
```

---

## Performance Validation

### Daily Review Checklist

**Review each morning:**
- [ ] Check 24h P/L
- [ ] Review closed trades
- [ ] Analyze win/loss ratio
- [ ] Check max drawdown
- [ ] Verify risk limits respected
- [ ] Review any errors in logs
- [ ] Check system resources

**Key Questions:**
- Are trades following strategy logic?
- Are position sizes appropriate?
- Are stop losses being hit correctly?
- Are take profits working?
- Any pattern in losses?
- Any API issues?

### Weekly Performance Report

**Generate Weekly Report:**

```bash
python -c "
import json
from datetime import datetime, timedelta

# Load trade history from analytics
# Calculate weekly metrics
# Generate report

print('Weekly Performance Report')
print('=' * 50)
print(f'Period: {start_date} to {end_date}')
print(f'Total Trades: {total_trades}')
print(f'Win Rate: {win_rate:.1f}%')
print(f'Total P/L: ${total_pnl:.2f}')
print(f'Sharpe Ratio: {sharpe:.2f}')
print(f'Max Drawdown: {max_dd:.2f}%')
print(f'Avg Trade Duration: {avg_duration:.1f} hours')
"
```

**Review Points:**
- Is performance meeting targets?
- Are there any concerning trends?
- Do parameters need adjustment?
- Should strategy be modified?

### Monthly Optimization

**Monthly Tasks:**
```bash
# 1. Run full stress test
make stress

# 2. Run optimization
make optimize

# 3. Compare current vs optimal parameters
# 4. Decide if parameter update needed
# 5. If updating, test in paper mode first
```

---

## Rollback Plan

### When to Rollback

**Immediate Rollback If:**
- Performance significantly worse than expected
- Frequent crashes or errors
- Risk management failures
- Strategy collisions occurring
- Daily loss > 15%

### Rollback Procedure

**Step 1: Stop Current Version**
```bash
# Stop bot
kill $(cat bot.pid)

# Wait for graceful shutdown
sleep 10

# Verify stopped
ps aux | grep bot.py
```

**Step 2: Close All Positions**
```bash
# Close all positions
python -c "
from position_manager import PositionManager
from kucoin_client import KuCoinClient
from config import Config

client = KuCoinClient(Config.API_KEY, Config.API_SECRET, Config.API_PASSPHRASE)
pm = PositionManager(client, 1000, 5, 10)

for symbol in pm.positions.keys():
    pm.close_position(symbol, 'Rollback procedure')
"
```

**Step 3: Revert Code**
```bash
# Checkout previous stable version
git fetch origin
git checkout <previous_stable_commit>

# Restore previous configuration
cp .env.backup .env

# Reinstall dependencies (if changed)
make install
```

**Step 4: Validate Rollback**
```bash
# Run tests
make test

# Run backtest
make backtest

# Verify configuration
make validate-config
```

**Step 5: Restart (Optional)**
```bash
# Only restart if validation passes
make paper-trade

# Monitor for 24 hours before going live again
```

### Post-Rollback

**Immediate Actions:**
1. Document reason for rollback
2. Analyze what went wrong
3. Create incident report
4. Fix issues in new version
5. Retest thoroughly before redeployment

**Long-Term Actions:**
1. Improve testing procedures
2. Add monitoring for failure cause
3. Update runbook with lessons learned
4. Consider additional safeguards

---

## Contact and Escalation

### Support Levels

**Level 1 - Operator:**
- Monitor dashboard and logs
- Handle routine alerts
- Execute standard procedures

**Level 2 - Engineering:**
- Investigate technical issues
- Modify parameters if needed
- Deploy hot fixes

**Level 3 - Senior Engineering:**
- Make GO/NO-GO decisions
- Approve rollbacks
- Major architecture changes

### Escalation Triggers

**Escalate to Level 2 if:**
- Multiple WARNING alerts in 1 hour
- Any CRITICAL alert
- Unexpected bot behavior
- Performance significantly off target

**Escalate to Level 3 if:**
- Emergency stop required
- Rollback needed
- Major exchange issues
- Significant financial loss

---

## Appendix

### Useful Commands

```bash
# Check bot status
ps aux | grep bot.py
cat bot.pid

# View recent logs
tail -100 logs/bot.log

# Search for errors
grep -i error logs/bot.log | tail -20

# Check system resources
top -p $(cat bot.pid)

# View active positions
python -c "from kucoin_client import KuCoinClient; from config import Config; c = KuCoinClient(Config.API_KEY, Config.API_SECRET, Config.API_PASSPHRASE); print(c.get_positions())"

# Check account balance
python -c "from kucoin_client import KuCoinClient; from config import Config; c = KuCoinClient(Config.API_KEY, Config.API_SECRET, Config.API_PASSPHRASE); print(c.get_balance())"
```

### Configuration Files

- `.env` - Main configuration
- `config.py` - Configuration class
- `requirements.txt` - Python dependencies
- `Makefile` - Task runner commands

### Log Files

- `logs/bot.log` - Main bot log
- `bot_live.log` - Live mode console output
- `stress_test_results/` - Stress test results
- `optimization_results.json` - Optimization results

### Important Limits

- **Max Open Positions:** 3 (configurable)
- **Max Position Size:** 30-60% of balance (auto-configured)
- **Daily Loss Limit:** 10%
- **Stop Loss:** 2-5% (configurable)
- **Leverage:** 4-12x (based on account size)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-29 | System | Initial runbook creation |

---

**End of Runbook**
