# KuCoin Futures API Setup Guide

## Prerequisites

1. KuCoin account with Futures trading enabled
2. Sufficient balance (recommended minimum: $500 USDT)
3. API credentials with appropriate permissions

## Creating API Keys

### Step 1: Login to KuCoin

1. Go to [https://www.kucoin.com](https://www.kucoin.com)
2. Login to your account
3. Enable 2FA if not already enabled (required for API)

### Step 2: Create API Key

1. Navigate to **API Management**
   - Click on your profile icon
   - Select "API Management"
   
2. Click **Create API**
   - Choose API version: V2 (recommended)
   - Enter API name: "Trading Bot" (or any name)
   - Set API passphrase (save this - you'll need it!)

3. **Set API Permissions**
   - ✓ General
   - ✓ Trade (Required for placing orders)
   - ✓ Transfer (Optional, for fund management)
   - ✗ Withdraw (NOT recommended for security)

4. **IP Whitelist (Highly Recommended)**
   - Add your server's IP address
   - Prevents unauthorized access
   - Can be set to "Unrestricted" for testing (not recommended for production)

5. **Complete 2FA Verification**
   - Enter 2FA code
   - Confirm email code
   - Save your API Key, Secret, and Passphrase securely

### Step 3: Save Credentials

**IMPORTANT**: Save these immediately as the secret won't be shown again:
- API Key
- API Secret
- API Passphrase

## Enabling Futures Trading

1. Navigate to **Futures** section
2. Complete the Futures trading agreement
3. Transfer funds from Main account to Futures account
   - Go to "Transfer" or "Assets"
   - Select "Main" → "Futures"
   - Transfer desired amount

## API Permissions Required

### Minimum Permissions
- **General**: Read account information
- **Trade**: Place and cancel orders

### Recommended Permissions
- **General**: ✓
- **Trade**: ✓
- **Transfer**: ✓ (if you want automated fund transfers)

### NOT Recommended
- **Withdraw**: ✗ (Major security risk)

## Security Best Practices

### API Key Security

1. **Never Share Keys**
   - Don't commit to Git
   - Don't share in chat/email
   - Use `.env` file (already in `.gitignore`)

2. **Use IP Whitelist**
   - Limit API access to your server IP
   - Update when server IP changes
   - More secure than unrestricted access

3. **Limit Permissions**
   - Only enable required permissions
   - Never enable "Withdraw" for trading bots
   - Review permissions regularly

4. **Rotate Keys Regularly**
   - Change API keys every 3-6 months
   - Immediately rotate if compromised
   - Delete unused API keys

### Account Security

1. **Enable 2FA**
   - Use Google Authenticator or similar
   - Required for API creation
   - Adds extra security layer

2. **Strong Passphrase**
   - Use unique API passphrase
   - Don't reuse account password
   - Store securely

3. **Monitor Activity**
   - Regularly check API activity logs
   - Review trading history
   - Set up email notifications

## Configuring the Bot

### Step 1: Create .env File

```bash
cp .env.example .env
```

### Step 2: Edit .env File

```bash
# Open with your preferred editor
nano .env
# or
vim .env
```

### Step 3: Add Your Credentials

```env
# KuCoin API Configuration
KUCOIN_API_KEY=your_actual_api_key_here
KUCOIN_API_SECRET=your_actual_api_secret_here
KUCOIN_API_PASSPHRASE=your_actual_api_passphrase_here

# Bot Configuration (OPTIONAL - Auto-configured based on your balance!)
# These settings are now OPTIONAL and will be automatically determined
# based on your account balance for optimal risk management.
# 
# Only uncomment and set these if you want to override the smart defaults:
# LEVERAGE=10
# MAX_POSITION_SIZE=1000
# RISK_PER_TRADE=0.02
# MIN_PROFIT_THRESHOLD=0.005
#
# Auto-configuration tiers:
# - Micro ($10-$100): Leverage=5x, Risk=1%, Very conservative
# - Small ($100-$1000): Leverage=7x, Risk=1.5%, Conservative  
# - Medium ($1000-$10000): Leverage=10x, Risk=2%, Balanced
# - Large ($10000-$100000): Leverage=12x, Risk=2.5%, Moderate-aggressive
# - Very Large ($100000+): Leverage=15x, Risk=3%, Aggressive

# Trading Parameters
CHECK_INTERVAL=60
TRAILING_STOP_PERCENTAGE=0.02
MAX_OPEN_POSITIONS=3

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Machine Learning
RETRAIN_INTERVAL=86400
ML_MODEL_PATH=models/signal_model.pkl
```

### Step 4: Verify Configuration

```bash
python -c "from config import Config; Config.validate(); print('Configuration valid!')"
```

## Testing API Connection

### Test Script

Create a test file `test_api.py`:

```python
from config import Config
from kucoin_client import KuCoinClient
from logger import Logger

# Setup logger
logger = Logger.setup()

# Validate config
Config.validate()

# Initialize client
client = KuCoinClient(
    Config.API_KEY,
    Config.API_SECRET,
    Config.API_PASSPHRASE
)

# Test connection
print("Testing KuCoin API connection...")

# Get account balance
balance = client.get_balance()
print(f"Balance: {balance}")

# Get active futures
futures = client.get_active_futures()
print(f"Found {len(futures)} active futures pairs")

print("\nAPI connection successful!")
```

Run the test:
```bash
python test_api.py
```

## Common API Errors

### Invalid API Credentials
```
Error: 400 - Invalid KC-API-KEY
```
**Solution**: Verify API key is correct in `.env`

### Invalid Signature
```
Error: 400 - Invalid KC-API-SIGN
```
**Solution**: 
- Check API secret is correct
- Verify system time is synchronized
- Check for extra spaces in credentials

### Invalid Passphrase
```
Error: 400 - Invalid KC-API-PASSPHRASE
```
**Solution**: Verify API passphrase in `.env`

### Permission Denied
```
Error: 403 - Permission denied
```
**Solution**: Check API permissions in KuCoin dashboard

### IP Restricted
```
Error: 403 - IP restricted
```
**Solution**: 
- Add your server IP to whitelist
- Or temporarily disable IP restriction

### Rate Limit Exceeded
```
Error: 429 - Too Many Requests
```
**Solution**: 
- Bot has built-in rate limiting
- Reduce CHECK_INTERVAL if needed
- Wait a few minutes and retry

## API Rate Limits

### KuCoin Futures Rate Limits

- **Public Endpoints**: 100 requests per 10 seconds
- **Private Endpoints**: 40 requests per 10 seconds
- **Order Placement**: 30 requests per 10 seconds

The bot automatically handles rate limiting via ccxt.

## Production Checklist

Before running in production:

- [ ] API keys created with correct permissions
- [ ] IP whitelist configured (if applicable)
- [ ] Credentials added to `.env` file
- [ ] `.env` file NOT committed to Git
- [ ] API connection tested successfully
- [ ] Futures trading enabled on KuCoin
- [ ] Sufficient balance in Futures account
- [ ] 2FA enabled on KuCoin account
- [ ] Email notifications enabled
- [ ] Monitor logs for first 24 hours
- [ ] Start with small position sizes

## Monitoring API Usage

### Check API Activity

1. Login to KuCoin
2. Go to API Management
3. View API activity logs
4. Monitor for suspicious activity

### Review Trading Activity

1. Go to Futures section
2. Check "Order History"
3. Review "Trade History"
4. Monitor P/L

## Troubleshooting

### Bot Can't Connect

1. Check internet connection
2. Verify KuCoin API status
3. Check credentials in `.env`
4. Test with simple API call
5. Review error logs

### Orders Not Executing

1. Verify Futures trading is enabled
2. Check account balance
3. Verify API has trade permission
4. Check order size meets minimum
5. Review exchange status

### Unexpected Behavior

1. Check bot logs
2. Verify API permissions
3. Check for API changes (KuCoin announcements)
4. Update ccxt library if needed: `pip install -U ccxt`

## Support Resources

- KuCoin API Documentation: https://docs.kucoin.com/futures/
- KuCoin Support: support@kucoin.com
- CCXT Documentation: https://docs.ccxt.com/

## Important Notes

⚠️ **Security Warning**: 
- Never share your API keys
- Never commit `.env` to Git
- Use IP whitelist when possible
- Disable withdraw permission

⚠️ **Trading Risk**: 
- Start with small amounts
- Understand leverage risks
- Monitor the bot regularly
- Have emergency stop plan

⚠️ **API Maintenance**: 
- KuCoin may perform maintenance
- Bot will log errors during downtime
- Bot will resume automatically when API is back
