# Position Viability Fix - Quick Reference

## What Was Fixed
❌ **OLD**: Reject if `adjusted_amount < desired_amount × 10%`
✅ **NEW**: Reject only if position doesn't meet absolute minimums

## The Problem
```python
# Bot wanted: 11,634 contracts
# Available margin: $46.96
# Adjusted to: 20.94 contracts
# OLD BEHAVIOR: ❌ REJECTED (only 0.18% of desired)
# NEW BEHAVIOR: ✅ ACCEPTED (meets all minimums)
```

## New Viability Checks
A position is viable if:
1. ✅ Amount >= exchange minimum (e.g., 1 contract)
2. ✅ Position value >= exchange minimum cost (e.g., $1)
3. ✅ Position value >= $1.00 (meaningful trade)
4. ✅ Required margin >= $0.10 (meaningful margin)

## Code Changes

### New Method
```python
is_viable, reason = client.is_position_viable(symbol, amount, price, leverage)
if not is_viable:
    logger.error(f"Position not viable: {reason}")
    return None
```

### Updated Locations
- `create_market_order()` - line ~438
- `create_limit_order()` - line ~539

## Testing
```bash
# Test the fix
python3 test_problem_scenario_fix.py

# Verify existing tests
python3 test_margin_limit_fix.py
```

## Examples

### Example 1: Small but viable (NOW ACCEPTED ✅)
```
Amount: 20.94 contracts
Price: $0.000100901
Contract Size: 100,000
Position Value: 20.94 × $0.000100901 × 100,000 = $211.30 ✅
Required Margin: $211.30 / 12 = $17.61 ✅
Result: ACCEPTED (was previously rejected)
```

### Example 2: Too small (CORRECTLY REJECTED ❌)
```
Amount: 0.005 contracts (below exchange min of 1)
Result: REJECTED - "Below exchange minimum"
```

### Example 3: Dust trade (CORRECTLY REJECTED ❌)
```
Amount: 5 contracts
Price: $0.0001
Contract Size: 1
Position Value: $0.0005 < $1.00
Result: REJECTED - "Position value too small"
```

## Key Benefits
- ✅ No more false rejections of viable positions
- ✅ Better capital utilization with limited margin
- ✅ Clear, specific rejection reasons
- ✅ Works correctly with large contract_size symbols
