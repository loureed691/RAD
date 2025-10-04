# Auto-Configuration Feature

## Overview

The trading bot now features **intelligent auto-configuration** that automatically determines optimal trading parameters based on your account balance. This eliminates the need to manually configure `LEVERAGE`, `MAX_POSITION_SIZE`, `RISK_PER_TRADE`, `MIN_PROFIT_THRESHOLD`, `TRAILING_STOP_PERCENTAGE`, and `MAX_OPEN_POSITIONS` in your `.env` file.

## How It Works

When the bot starts, it:
1. Fetches your current USDT balance from KuCoin
2. Analyzes the balance tier (Micro, Small, Medium, Large, Very Large)
3. Automatically configures optimal parameters for that tier
4. Applies risk-appropriate settings based on account size

## Balance Tiers

### Micro Account ($10-$100)
**Purpose:** Learning and testing with minimal capital

- **Leverage:** 5x (very conservative)
- **Max Position Size:** 30% of balance
- **Risk Per Trade:** 1.0% (very careful)
- **Min Profit Threshold:** 0.8% (account for fees)
- **Trailing Stop:** 1.5% (tighter to protect capital)
- **Max Open Positions:** 1 (focus on one trade)

**Rationale:** Micro accounts need maximum protection. Lower leverage and risk percentage preserve capital while you learn. Single position limit ensures focused risk management.

### Small Account ($100-$1,000)
**Purpose:** Growing a small account carefully

- **Leverage:** 7x (conservative)
- **Max Position Size:** 40% of balance
- **Risk Per Trade:** 1.5% (cautious)
- **Min Profit Threshold:** 0.6%
- **Trailing Stop:** 1.8% (still conservative)
- **Max Open Positions:** 2 (limited diversification)

**Rationale:** Small accounts benefit from conservative settings to build confidence and track record. Two positions allow some diversification while maintaining control.

### Medium Account ($1,000-$10,000)
**Purpose:** Balanced growth with moderate risk

- **Leverage:** 10x (balanced)
- **Max Position Size:** 50% of balance
- **Risk Per Trade:** 2.0% (standard)
- **Min Profit Threshold:** 0.5%
- **Trailing Stop:** 2.0% (standard)
- **Max Open Positions:** 3 (balanced diversification)

**Rationale:** Standard risk management principles apply. This is the "sweet spot" for most traders. Three positions provide good diversification without over-complexity.

### Large Account ($10,000-$100,000)
**Purpose:** Experienced trading with moderate-aggressive settings

- **Leverage:** 12x (moderate-aggressive)
- **Max Position Size:** 60% of balance
- **Risk Per Trade:** 2.5% (aggressive)
- **Min Profit Threshold:** 0.5%
- **Trailing Stop:** 2.5% (wider to let winners run)
- **Max Open Positions:** 4 (good diversification)

**Rationale:** Larger accounts can handle slightly more aggressive settings while maintaining good risk management. Four positions provide excellent diversification.

### Very Large Account ($100,000+)
**Purpose:** Professional-level trading

- **Leverage:** 15x (aggressive)
- **Max Position Size:** 60% of balance (capped at $50,000)
- **Risk Per Trade:** 3.0% (professional)
- **Min Profit Threshold:** 0.5%
- **Trailing Stop:** 3.0% (maximum flexibility)
- **Max Open Positions:** 5 (maximum diversification)

**Rationale:** Very large accounts benefit from maximum efficiency while still maintaining professional risk management. Five positions provide optimal diversification for large portfolios.

## Overriding Auto-Configuration

If you prefer to manually set any parameter, simply add it to your `.env` file:

```env
# Override specific parameters
LEVERAGE=8
RISK_PER_TRADE=0.015

# Other parameters will still be auto-configured
```

The bot will:
- Use your custom value for overridden parameters
- Auto-configure the remaining parameters

## Startup Logs

When the bot starts with auto-configuration, you'll see logs like:

```
💰 Available balance: $5000.00 USDT
🤖 Auto-configured LEVERAGE: 10x (balance: $5000.00)
🤖 Auto-configured MAX_POSITION_SIZE: $2500.00 (balance: $5000.00)
🤖 Auto-configured RISK_PER_TRADE: 2.00% (balance: $5000.00)
🤖 Auto-configured MIN_PROFIT_THRESHOLD: 0.50% (balance: $5000.00)
🤖 Auto-configured TRAILING_STOP_PERCENTAGE: 2.00% (balance: $5000.00)
🤖 Auto-configured MAX_OPEN_POSITIONS: 3 (balance: $5000.00)
```

With overrides:

```
💰 Available balance: $5000.00 USDT
📌 Using user-defined LEVERAGE: 8x
🤖 Auto-configured MAX_POSITION_SIZE: $2500.00 (balance: $5000.00)
📌 Using user-defined TRAILING_STOP_PERCENTAGE: 2.50%
🤖 Auto-configured MAX_OPEN_POSITIONS: 3 (balance: $5000.00)
```
📌 Using user-defined RISK_PER_TRADE: 1.50%
🤖 Auto-configured MIN_PROFIT_THRESHOLD: 0.50% (balance: $5000.00)
```

## Benefits

1. **No Manual Configuration Required:** Just set up API keys and start trading
2. **Risk-Appropriate Settings:** Automatically scales risk with account size
3. **Prevents Over-Leveraging:** Smaller accounts get lower leverage for safety
4. **Dynamic Adaptation:** Settings adjust as your balance grows
5. **Flexible Overrides:** Manual control still available when needed
6. **Beginner-Friendly:** New traders get safe defaults automatically

## Migration from Manual Configuration

If you're upgrading from a previous version:

### Option 1: Use Auto-Configuration (Recommended)
Simply comment out or remove these lines from your `.env`:
```env
# LEVERAGE=10
# MAX_POSITION_SIZE=1000
# RISK_PER_TRADE=0.02
# MIN_PROFIT_THRESHOLD=0.005
```

### Option 2: Keep Your Settings
Do nothing - your existing `.env` values will override auto-configuration.

## Testing Auto-Configuration

To test the auto-configuration with different balance amounts:

```python
from config import Config

# Test with different balances
Config.auto_configure_from_balance(500)   # Small account
Config.auto_configure_from_balance(5000)  # Medium account
Config.auto_configure_from_balance(50000) # Large account

print(f"Leverage: {Config.LEVERAGE}x")
print(f"Risk: {Config.RISK_PER_TRADE:.2%}")
```

## Safety Features

1. **Balance Validation:** Falls back to safe defaults if balance fetch fails
2. **Reasonable Bounds:** All parameters capped at safe min/max values
3. **Position Size Caps:** MAX_POSITION_SIZE capped at $50,000 regardless of account size
4. **Risk Limits:** Risk per trade capped between 0.5% and 3%
5. **Leverage Limits:** Leverage capped between 3x and 15x

## FAQ

**Q: Can I still use manual configuration?**  
A: Yes! Just set values in your `.env` file and they'll override auto-configuration.

**Q: What happens if balance fetch fails?**  
A: The bot falls back to safe defaults (10x leverage, $1000 max position, 2% risk).

**Q: Will settings change while the bot is running?**  
A: No, settings are determined at startup based on initial balance.

**Q: Is this suitable for beginners?**  
A: Yes! The auto-configuration is specifically designed to give beginners safe, appropriate settings.

**Q: What if I want more aggressive settings?**  
A: Simply set your preferred values in `.env` to override the auto-configuration.

## Recommendations

- **Start with auto-configuration** to learn appropriate risk levels
- **Monitor performance** for at least 30 days before making adjustments
- **Only override** if you understand the risks and have a specific strategy
- **Be conservative** - it's better to grow slowly than to blow up your account

## Technical Details

The auto-configuration logic is in `config.py`:

```python
Config.auto_configure_from_balance(available_balance)
```

This method:
1. Checks for environment variable overrides
2. Determines balance tier
3. Applies tier-specific settings
4. Logs all configuration decisions
5. Ensures all values are within safe bounds

The settings are applied once during bot initialization in `bot.py`.
