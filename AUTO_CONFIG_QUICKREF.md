# Auto-Configuration Quick Reference

## TL;DR

**You no longer need to set LEVERAGE, MAX_POSITION_SIZE, RISK_PER_TRADE, or MIN_PROFIT_THRESHOLD in your .env file!**

The bot automatically configures these based on your account balance.

## Quick Start

1. Set up your API keys in `.env`:
   ```env
   KUCOIN_API_KEY=your_key
   KUCOIN_API_SECRET=your_secret
   KUCOIN_API_PASSPHRASE=your_passphrase
   ```

2. Start the bot:
   ```bash
   python bot.py
   ```

3. The bot will:
   - Fetch your balance
   - Auto-configure optimal settings
   - Start trading immediately

## Balance Tiers Quick Reference

| Balance Range | Tier | Leverage | Risk % | Position Size % |
|---------------|------|----------|--------|-----------------|
| $10-$100 | 🐣 Micro | 5x | 1.0% | 30% |
| $100-$1K | 💼 Small | 7x | 1.5% | 40% |
| $1K-$10K | 📈 Medium | 10x | 2.0% | 50% |
| $10K-$100K | 💰 Large | 12x | 2.5% | 60% |
| $100K+ | 🏆 Very Large | 15x | 3.0% | 60% |

## Manual Override

Want to use custom settings? Just add them to `.env`:

```env
# Override specific parameters (others will still auto-configure)
LEVERAGE=8
RISK_PER_TRADE=0.015
```

## Startup Logs

Look for these logs to confirm auto-configuration:

```
💰 Available balance: $5000.00 USDT
🤖 Auto-configured LEVERAGE: 10x (balance: $5000.00)
🤖 Auto-configured MAX_POSITION_SIZE: $2500.00 (balance: $5000.00)
🤖 Auto-configured RISK_PER_TRADE: 2.00% (balance: $5000.00)
🤖 Auto-configured MIN_PROFIT_THRESHOLD: 0.50% (balance: $5000.00)
```

With overrides:
```
📌 Using user-defined LEVERAGE: 8x
```

## Benefits

✅ **No manual configuration**  
✅ **Risk-appropriate for your account size**  
✅ **Prevents over-leveraging**  
✅ **Automatically adapts as balance grows**  
✅ **Still allows manual control when needed**

## Safety

- Balance fetch failure → Safe defaults (10x, 2% risk)
- All values bounded to safe ranges
- Position size capped at $50,000
- Risk capped between 0.5-3%
- Leverage capped between 3-15x

## More Information

- Full details: [AUTO_CONFIG.md](AUTO_CONFIG.md)
- Setup guide: [API_SETUP.md](API_SETUP.md)
- Main README: [README.md](README.md)
