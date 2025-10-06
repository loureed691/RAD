# Price Formatting Fix

## Problem
Position logging was using `.2f` format specifier which loses precision for small cryptocurrency prices:
- Prices like 0.001234 were displayed as "0.00"
- P/L amounts like $0.00417 were displayed as "$0.00"
- This made it impossible to see actual values for low-priced cryptocurrencies

## Solution
Implemented dynamic precision formatting based on price magnitude:

### `format_price(price)` function
- Prices ≥ $1,000: 2 decimals (e.g., 1213.68)
- Prices ≥ $1: 2 decimals (e.g., 5.33, 16.78)
- Prices ≥ $0.1: 2 decimals (e.g., 0.88, 0.50)
- Prices $0.01-$0.1: 4 decimals (e.g., 0.0567, 0.0200)
- Prices $0.001-$0.01: 5 decimals (e.g., 0.00123)
- Prices < $0.001: 6 decimals (e.g., 0.000568)

### `format_pnl_usd(pnl_usd)` function
Formats P/L amounts with sign and appropriate precision:
- Examples: "$+0.00154", "$-0.00295", "$+10.50"

## Results

### Before (using `.2f`):
```
Entry Price: 0.00
Current Price: 0.00
Current P/L: -1.25% ($-0.00)
```

### After (using dynamic formatting):
```
Entry Price: 0.00123
Current Price: 0.00122
Current P/L: -1.25% ($-0.000828)
```

## Testing
Run `python3 test_price_formatting.py` to verify formatting logic.
Run `python3 test_realistic_formatting.py` to see real-world examples.

## Files Modified
- `position_manager.py`: Added formatting functions and updated all price logging statements
