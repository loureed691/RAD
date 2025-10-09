# Kelly Criterion Usage Guide

## Quick Reference for Developers

This guide explains how to use the Kelly Criterion implementation after the collision resolution.

---

## ⚠️ Important Change

**OLD (Removed):**
```python
kelly_fraction = ml_model.get_kelly_fraction()
```

**NEW (Current):**
```python
# Get metrics from risk_manager
win_rate = risk_manager.get_win_rate()
avg_profit = risk_manager.get_avg_win()
avg_loss = risk_manager.get_avg_loss()

# Calculate Kelly with adaptive logic
kelly_fraction = risk_manager.calculate_kelly_criterion(
    win_rate, avg_profit, avg_loss, use_fractional=True
)
```

---

## How It Works

### 1. Trade Recording

Every time a trade closes, record the outcome:

```python
# In bot.py or position_manager
pnl = 0.03  # 3% profit (or -0.02 for 2% loss)
risk_manager.record_trade_outcome(pnl)
```

This automatically tracks:
- Win/loss streaks
- Total wins and losses
- Average profit and loss
- Recent trades (rolling window)

### 2. Getting Performance Metrics

```python
# Get overall performance
win_rate = risk_manager.get_win_rate()        # e.g., 0.60 (60%)
avg_win = risk_manager.get_avg_win()          # e.g., 0.04 (4%)
avg_loss = risk_manager.get_avg_loss()        # e.g., 0.02 (2%)
total_trades = risk_manager.total_trades      # e.g., 25
```

### 3. Calculating Kelly Fraction

```python
# Only use Kelly after sufficient trade history
if total_trades >= 20 and win_rate > 0 and avg_win > 0 and avg_loss > 0:
    kelly = risk_manager.calculate_kelly_criterion(
        win_rate, 
        avg_win, 
        avg_loss, 
        use_fractional=True  # Use adaptive fractional Kelly (recommended)
    )
else:
    kelly = None  # Fall back to default risk_per_trade
```

### 4. Using Kelly in Position Sizing

```python
# Apply drawdown adjustment
risk_adjustment = risk_manager.update_drawdown(balance)

# Calculate position size
position_size = risk_manager.calculate_position_size(
    balance=balance,
    entry_price=entry_price,
    stop_loss_price=stop_loss_price,
    leverage=leverage,
    kelly_fraction=kelly * risk_adjustment if kelly else None
)
```

---

## Adaptive Fractional Kelly

The `calculate_kelly_criterion()` method uses adaptive fractional Kelly, which adjusts based on:

### Base Fractional Multiplier
- Starts at **0.5** (half-Kelly, conservative baseline)

### Performance Consistency
- **90%+ consistency**: 0.65 multiplier (more aggressive)
- **85-90% consistency**: 0.60 multiplier
- **70-85% consistency**: 0.55 multiplier
- **60-70% consistency**: 0.50 multiplier (baseline)
- **50-60% consistency**: 0.45 multiplier
- **<50% consistency**: 0.35 multiplier (very conservative)

*Consistency = 1.0 - abs(recent_win_rate - overall_win_rate)*

### Win Rate Quality
- **≥65% win rate**: +10% to multiplier (max 0.7)
- **≤45% win rate**: -15% to multiplier (min 0.3)

### Streak Adjustments
- **Loss Streak**:
  - 3+ losses: -35% to multiplier
  - 2 losses: -15% to multiplier
- **Win Streak**:
  - 5+ wins: +15% to multiplier (max 0.7)
  - 3-4 wins: +8% to multiplier

### Safety Bounds
- **Minimum**: 0.5% of portfolio
- **Maximum**: 3.5% of portfolio

---

## Example Calculation

### Scenario
- Total trades: 25
- Wins: 15 (60% win rate)
- Avg profit: 4%
- Avg loss: 2%
- Recent win rate: 65% (good consistency)
- Win streak: 0
- Loss streak: 0

### Full Kelly
```
b = avg_profit / avg_loss = 4% / 2% = 2.0
p = win_rate = 0.60
q = 1 - p = 0.40

Full Kelly = (b*p - q) / b
           = (2.0 * 0.60 - 0.40) / 2.0
           = (1.20 - 0.40) / 2.0
           = 0.80 / 2.0
           = 0.40 (40% of capital)
```

### Adaptive Fractional Kelly
```
Base fraction: 0.5 (half-Kelly)
Consistency: 1.0 - abs(0.65 - 0.60) = 0.95 (excellent)
→ Use 0.65 multiplier

Fractional Kelly = 0.40 * 0.65 = 0.26 (26%)

Capped at maximum: min(0.26, 0.035) = 0.035 (3.5%)
```

**Result**: Risk 3.5% of portfolio (safer than full Kelly)

---

## Testing

### Unit Test Example
```python
from risk_manager import RiskManager

def test_kelly():
    rm = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
    
    # Record 25 trades (60% win rate, 2:1 R/R)
    for i in range(25):
        if i < 15:
            rm.record_trade_outcome(0.04)  # 4% profit
        else:
            rm.record_trade_outcome(-0.02)  # 2% loss
    
    # Calculate Kelly
    kelly = rm.calculate_kelly_criterion(
        win_rate=rm.get_win_rate(),
        avg_win=rm.get_avg_win(),
        avg_loss=rm.get_avg_loss(),
        use_fractional=True
    )
    
    assert 0 < kelly <= 0.035, f"Kelly should be between 0 and 3.5%, got {kelly}"
    print(f"✓ Kelly: {kelly:.4f}")
```

---

## FAQs

### Q: Why was ml_model.get_kelly_fraction() removed?
**A**: It was a duplicate implementation with inferior logic. The risk_manager version is superior because it:
- Uses adaptive fractional adjustment (not fixed half-Kelly)
- Considers performance consistency
- Adjusts for win/loss streaks
- Has better safety bounds (3.5% vs 25%)

### Q: When should I use Kelly Criterion?
**A**: Only after at least 20 trades. Before that, use default risk_per_trade.

### Q: What if I want more aggressive Kelly?
**A**: Set `use_fractional=False` for standard half-Kelly, but this is NOT recommended. The adaptive fractional approach is safer.

### Q: How do I disable Kelly?
**A**: Simply pass `kelly_fraction=None` to `calculate_position_size()`.

### Q: Does Kelly replace risk_per_trade?
**A**: No, Kelly is OPTIONAL. If not provided or conditions aren't met, the system falls back to risk_per_trade.

---

## Best Practices

✅ **DO**:
- Record every trade outcome with `record_trade_outcome()`
- Wait for 20+ trades before using Kelly
- Use `use_fractional=True` (adaptive)
- Apply drawdown adjustments before Kelly

❌ **DON'T**:
- Manually set performance metrics (use record_trade_outcome)
- Use Kelly with < 20 trades
- Set use_fractional=False (unless you know what you're doing)
- Bypass safety bounds

---

## Related Files
- `risk_manager.py` - Implementation
- `bot.py` - Usage example
- `test_smarter_bot.py` - Unit tests
- `FEATURE_COLLISION_RESOLUTION.md` - Detailed technical docs

---

**Last Updated**: 2024
**Version**: 2.0 (Post-collision resolution)
