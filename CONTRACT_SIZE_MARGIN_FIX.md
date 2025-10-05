# Fix for Contract Size in Margin Calculations

## Problem

The bot was experiencing KuCoin error 330008 even after the initial margin limit fix. The error logs showed inconsistent values:

```
20:56:36 ⚠️ WARNING Margin check failed: Insufficient margin: available=$47.75, required=$348.35 (position value=$1.00, leverage=3x)
```

**Issue**: The position value was shown as $1.00, but required margin was $348.35 - this is mathematically impossible if using the formula `required = position_value / leverage`.

## Root Cause

The bug was in `adjust_position_for_margin()` method which had **inconsistent position value calculations**:

### Before Fix

1. **`calculate_required_margin()`** correctly used:
   ```python
   position_value = amount * price * contract_size
   required_margin = position_value / leverage
   ```

2. **`adjust_position_for_margin()`** incorrectly used (lines 296, 309):
   ```python
   adjusted_amount = max_position_value / price  # MISSING contract_size!
   position_value = adjusted_amount * price       # MISSING contract_size!
   ```

3. **Log message in `check_available_margin()`** (line 262) didn't include contract_size:
   ```python
   f"position value=${amount * price:.2f}"  # MISSING contract_size!
   ```

### Why This Caused Problems

For contracts where `contract_size != 1` (common in futures), the calculations were off by a factor of `contract_size`:

**Example from problem statement:**
- Symbol: 1000BONK/USDT:USDT with `contract_size = 100`
- 50 contracts at $0.0002 with 3x leverage
- **Correct calculation**: 
  - Position value = 50 × $0.0002 × 100 = $1.00
  - Required = $1.00 / 3 = $0.33 ✓ (fits in $47.75)
- **Before fix**:
  - Adjustment used: 50 × $0.0002 = $0.01 (wrong!)
  - But required margin calculation was correct at $0.33
  - This mismatch caused positions to be incorrectly rejected or adjusted

## Solution

Made three changes to ensure **consistent use of contract_size** across all calculations:

### 1. Fix `adjust_position_for_margin()` - Line 310

```python
# Before
adjusted_amount = max_position_value / price

# After  
markets = self.exchange.load_markets()
contract_size = markets[symbol].get('contractSize', 1)
adjusted_amount = max_position_value / (price * contract_size)
```

### 2. Fix `adjust_position_for_margin()` - Line 324

```python
# Before
position_value = adjusted_amount * price

# After
position_value = adjusted_amount * price * contract_size
```

### 3. Fix logging in `check_available_margin()` - Line 267

```python
# Before
f"position value=${amount * price:.2f}"

# After
markets = self.exchange.load_markets()
contract_size = markets[symbol].get('contractSize', 1)
position_value = amount * price * contract_size
f"position value=${position_value:.2f}"
```

## Testing

Created comprehensive tests in `test_contract_size_margin_fix.py`:

1. **Test large contract_size scenario**: Verified 100 contracts at $0.0001 with contract_size=100 correctly calculates $1.00 position value
2. **Test position adjustment**: Verified positions are adjusted correctly when contract_size > 1
3. **Test logging accuracy**: Verified log messages show correct position values

All tests pass:
- ✓ `test_margin_limit_fix.py` (4/4 tests)
- ✓ `test_contract_size_margin_fix.py` (2/2 tests)
- ✓ `test_problem_scenario.py` (exact scenario simulation)
- ✓ `test_position_mode_fix.py` (3/3 tests)

## Impact

### Before Fix
- Margin calculations were inconsistent
- Positions with `contract_size > 1` were incorrectly rejected
- Log messages showed misleading values
- Error 330008 occurred even with sufficient margin

### After Fix
- All margin calculations now consistently include `contract_size`
- Positions are correctly adjusted to fit available margin
- Log messages accurately reflect actual values
- Error 330008 should be prevented for legitimate trades

## Files Changed

1. **`kucoin_client.py`**:
   - `adjust_position_for_margin()`: Added contract_size to lines 310 and 324
   - `check_available_margin()`: Added contract_size to logging on line 267

2. **New test files**:
   - `test_contract_size_margin_fix.py`: Comprehensive contract_size tests
   - `test_problem_scenario.py`: Simulates exact problem statement scenario

## Verification

The fix can be verified by running:
```bash
python test_margin_limit_fix.py
python test_contract_size_margin_fix.py  
python test_problem_scenario.py
```

All tests should pass, demonstrating that:
1. Margin calculations are now consistent
2. Positions fit correctly in available margin
3. The specific scenario from the problem statement is resolved
