# Fix for Position Viability Check Bug

## Issue
The bot was rejecting margin-adjusted positions that were viable but appeared small relative to the originally desired size.

### Problem Scenario from Logs
```
2025-10-05 21:21:56 - Calculated position size: 11634.2087 contracts
2025-10-05 21:21:57 - Margin check failed: available=$46.96, required=$24651.97
2025-10-05 21:21:57 - Reducing position size from 11634.2087 to 20.9416 contracts
2025-10-05 21:21:57 - ERROR - Cannot open position: adjusted position too small (0.18% of desired)
```

**Why this was wrong:**
- Adjusted position: 20.9416 contracts @ $0.000100901 with contract_size=100,000
- Position value: $211.30
- Required margin: $17.61 (at 12x leverage)
- **This is a perfectly viable trade!**

## Root Cause

The code was using a flawed viability check:
```python
if adjusted_amount < validated_amount * 0.1:  # Reject if < 10% of desired
    return None
```

This compared the adjusted size to the desired size. The problem:
1. The desired size was calculated **without** considering available margin
2. A small adjusted position (20 contracts) was rejected just because the desired size was large (11,634 contracts)
3. The adjusted position was actually viable by all objective measures

## Solution

Replaced the relative "10% of desired" check with **absolute minimum checks**:

### New Method: `is_position_viable()`
```python
def is_position_viable(self, symbol: str, amount: float, price: float, leverage: int) -> tuple[bool, str]:
    """Check if a position size is viable for trading"""
    # 1. Check exchange minimum amount
    if amount < exchange_min_amount:
        return False, "Below exchange minimum"
    
    # 2. Check exchange minimum cost
    position_value = amount * price * contract_size
    if position_value < exchange_min_cost:
        return False, "Below exchange minimum cost"
    
    # 3. Check meaningful position value (at least $1)
    if position_value < 1.0:
        return False, "Position value too small"
    
    # 4. Check meaningful required margin (at least $0.10)
    required_margin = position_value / leverage
    if required_margin < 0.10:
        return False, "Required margin too small"
    
    return True, "Position is viable"
```

### Key Changes

**Before:**
```python
if adjusted_amount < validated_amount * 0.1:
    reject_trade()
```

**After:**
```python
is_viable, reason = self.is_position_viable(symbol, adjusted_amount, price, adjusted_leverage)
if not is_viable:
    reject_trade(reason)
```

## Files Changed

1. **kucoin_client.py**
   - Added `is_position_viable()` method (lines 282-333)
   - Updated `create_market_order()` viability check (line ~438)
   - Updated `create_limit_order()` viability check (line ~539)

2. **test_problem_scenario_fix.py**
   - New test file that reproduces the exact problem scenario
   - Tests that 20-contract position is correctly accepted

## Test Results

### Problem Scenario Test
```
✓ Position from problem statement (20.9416 contracts @ $0.000100901):
  - Position value: $211.30
  - Required margin: $17.61
  - Result: ✓ VIABLE (correctly accepted, was previously rejected)
```

### Viability Checks
```
✓ Test 1: 20.94 contracts with contract_size=100k → VIABLE ✓
✓ Test 2: 0.005 contracts (below min) → NOT VIABLE ✓
✓ Test 3: 0.001 contracts (tiny margin) → NOT VIABLE ✓
✓ Test 4: 100 contracts normal → VIABLE ✓
```

### Existing Tests
All existing margin limit fix tests still pass:
```
✓ test_margin_limit_fix.py: 4/4 tests passed
✓ test_position_mode_fix.py: 3/3 tests passed
✓ test_contract_size_margin_fix.py: 2/2 tests passed
```

## Impact

### Before Fix
- Positions rejected based on **relative size** to originally desired position
- Example: 20-contract position rejected because desired was 11,634 contracts (0.18%)
- Lost trading opportunities due to false rejections

### After Fix
- Positions accepted if they meet **absolute minimum requirements**
- Example: 20-contract position accepted because it meets all minimums
- Only reject if truly non-viable (below exchange limits or meaningless size)

## Edge Cases Handled

1. **Large contract_size symbols** (like FLOKI with 100,000x multiplier)
   - Correctly calculates position value including contract_size
   - Example: 20 contracts × $0.0001 × 100,000 = $200 value ✓

2. **Exchange minimum amounts**
   - Respects exchange min/max limits
   - Rejects if below exchange minimums ✓

3. **Meaningful trade sizes**
   - Requires position value >= $1.00 (prevents dust trades)
   - Requires margin >= $0.10 (prevents trivial positions)

4. **Error handling**
   - If viability check fails, assumes viable and lets exchange reject
   - Prevents blocking legitimate trades due to check errors

## Benefits

1. **No More False Rejections**: Viable small positions are now accepted
2. **Better Capital Utilization**: Bot can take smaller positions when margin is limited
3. **Clearer Error Messages**: Specific reasons why positions are rejected
4. **Objective Criteria**: Uses absolute minimums rather than arbitrary relative thresholds

## Verification

To verify the fix:
```bash
python3 test_problem_scenario_fix.py
python3 test_margin_limit_fix.py
python3 test_contract_size_margin_fix.py
```

Expected: All tests pass ✓
