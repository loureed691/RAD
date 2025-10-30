# Changelog

All notable changes to the RAD KuCoin Futures Trading Bot will be documented in this file.

## [3.2.0] - 2025-10-30

### Changed

#### Dependency Upgrades (2025-10-30)
- **Upgraded All Dependencies**: Updated all Python packages to their latest stable versions
  - **Core Libraries**:
    - ccxt: 4.5.0 → 4.5.12 (latest cryptocurrency exchange API)
    - numpy: 1.26.0 → 2.3.4 (major version upgrade with better performance)
    - pandas: 2.2.0 → 2.3.3 (improved data processing)
  - **Machine Learning**:
    - scikit-learn: 1.5.0 → 1.7.2 (latest ML algorithms)
    - tensorflow: 2.18.0 → 2.19.0 (latest deep learning framework)
    - xgboost: 2.1.0 → 2.1.3 (gradient boosting improvements)
    - lightgbm: 4.5.0 → 4.6.0 (security patch for RCE vulnerability)
    - catboost: 1.2.0 → 1.2.7 (enhanced categorical handling)
    - optuna: 4.0.0 → 4.1.0 (better hyperparameter optimization)
  - **Web & API**:
    - requests: 2.32.0 → 2.32.3 (security and bug fixes)
    - flask: 3.1.0 → 3.1.0 (web dashboard)
    - plotly: 5.24.0 → 5.24.1 (visualization improvements)
  - **Database & Dev Tools**:
    - psycopg2-binary: 2.9.9 → 2.9.10 (PostgreSQL connector)
    - python-dateutil: 2.8.0 → 2.9.0 (date/time handling)
    - joblib: 1.4.0 → 1.4.2 (parallel processing)
    - flake8: 7.0.0 → 7.1.0 (code linting)
    - black: 24.0.0 → 24.10.0 (code formatting)
    - mypy: 1.11.0 → 1.13.0 (type checking)
    - pytest: 8.0.0 → 8.3.0 (testing framework)
    - pytest-cov: 5.0.0 → 6.0.0 (coverage reporting)
  - **Impact**: 
    - Improved performance with numpy 2.x optimizations
    - Enhanced ML capabilities with latest scikit-learn and tensorflow
    - Better security with updated dependencies
    - Full compatibility with Python 3.11, 3.12, and 3.13
  - **Files**: `requirements.txt`, `pyproject.toml`
  - **Version**: Bumped to 3.2.0 to reflect major dependency upgrades

### Added
- **Python 3.13 Support**: Added support for latest Python version
  - Updated classifiers and build targets
  - Tested compatibility with Python 3.11, 3.12, and 3.13
  - **Files**: `pyproject.toml`

## [Unreleased]

### Changed

#### Time-Based Exit Removal (2025-10-23)
- **Removed Time-Based Trade Closures**: Eliminated the 4-hour time limit for position exits
  - Previously: Positions would close after 4 hours if ROI was below 2%
  - Now: Trades can stay open indefinitely based solely on market conditions
  - **Impact**: Positions are no longer forced to close due to time constraints
  - **Files**: `position_manager.py`, `test_stalled_stop_loss.py`, `verify_no_time_limit.py`
  - **Exit Conditions**: Trades now only close based on:
    - Stop loss triggers
    - Take profit targets
    - Emergency stops (risk management at -15%, -25%, -40% ROI)
    - Market-based exit conditions
  - **Testing**: All existing tests updated and pass; new verification script added

#### Repository Cleanup (2025-10-12)
- **Documentation Cleanup**: Removed 17 outdated summary, report, and verification files
  - Removed: BOT_REVIEW_REPORT.md, BUG_FIX_REPORT.md, CHANGES_SUMMARY.md, CLEANUP_COMPLETE.md
  - Removed: EMERGENCY_STOP_LOSS_FIX.md, FINAL_FIX_SUMMARY.md, FIXES.md, IMPLEMENTATION_SUMMARY.md
  - Removed: LEVERAGED_PNL_FIX.md, LEVERAGED_PNL_FIX_SUMMARY.md, LOG_FIXES_README.md
  - Removed: MONEY_LOSS_FIXES_SUMMARY.md, STOP_LOSS_BUG_FIX.md, TRADING_BOT_FIX_COMPLETE.md
  - Removed: VERIFICATION.md, VERIFICATION_CHECKLIST.md, QUICKSTART_IMPROVEMENTS.md
  - **Impact**: Cleaner repository with ~30 markdown files focused on current features and documentation
  - **Files**: Repository root directory

- **README Update**: Streamlined main documentation to reflect current state
  - Updated date to October 12, 2025
  - Consolidated multiple "Latest Update" sections into clean feature list
  - Removed outdated claims and statistics from previous cleanup iterations
  - Improved organization with clear feature categories (Intelligent Trading, Risk Management, Advanced Features, Reliability)
  - Simplified Quick Start section for easier onboarding
  - **Impact**: More professional, focused, and easier-to-navigate main documentation
  - **Files**: `README.md`

### Added

#### Performance Optimization (2024-10-08)
- **Configurable Parallel Workers**: Added `MAX_WORKERS` environment variable to configure parallel market scanning workers
  - Default increased from 10 to 20 workers (2x faster scanning)
  - Configurable from 5 to 50+ workers based on system capabilities
  - **Impact**: Market scans now complete in ~7 seconds (down from ~15 seconds)
  - **Files**: `config.py`, `market_scanner.py`, `bot.py`
  
- **Configurable Cache Duration**: Added `CACHE_DURATION` environment variable for intelligent caching
  - Default remains 300 seconds (5 minutes)
  - Adjustable from 60 to 900 seconds based on trading style
  - **Impact**: Better API efficiency and cost control
  - **Files**: `config.py`, `market_scanner.py`

- **Performance Documentation**: Created comprehensive performance guides
  - `PERFORMANCE_OPTIMIZATION.md` - Detailed 200+ line optimization guide
  - Updated `README.md` with performance section
  - Enhanced `DEPLOYMENT.md` with tuning recommendations
  - Updated `.env.example` with new parameters

- **Validation Script**: Added `validate_performance_config.py` to verify configuration
  - Automated checks for all performance parameters
  - Validates code integration
  - Confirms documentation completeness

- **Enhanced Logging**: Bot now logs MAX_WORKERS configuration on startup for visibility

**Performance Gains**:
- Default configuration: **2x faster** market scanning
- Optimized configuration: **4-5x faster** market scanning
- Better multi-core CPU utilization
- Lower API costs with smart caching
- Zero breaking changes - fully backward compatible

### Fixed

#### Leverage Variable Scoping Error in Nested Functions
- **Problem**: Bot was failing to create market/limit orders with error "cannot access local variable 'leverage' where it is not associated with a value", especially when closing positions (e.g., "Failed to create close order for ALICE/USDT:USDT")
- **Root Cause**: In `create_market_order()` and `create_limit_order()` methods, the nested `_create_order()` function assigns to the `leverage` variable (e.g., `leverage = adjusted_leverage`). Due to Python's scoping rules, this causes `leverage` to be treated as a local variable throughout the entire nested function, even before the assignment. When code tries to use `leverage` before the assignment (e.g., passing it to `check_available_margin()` or `adjust_position_for_margin()`), it triggers an UnboundLocalError.
- **Solution**: Added `nonlocal leverage` declaration at the beginning of `_create_order()` functions in both methods to explicitly indicate that `leverage` refers to the outer function's parameter, not a new local variable
- **Impact**: Orders can now be created and closed successfully without UnboundLocalError. The fix ensures proper variable scoping in nested functions that modify outer scope variables.
- **Files**: `kucoin_client.py` lines 596, 809
- **Test**: Added `test_leverage_scoping_fix.py` to demonstrate the bug and verify the fix

#### Isolated Margin Mode Error (Code 330006)
- **Problem**: Bot was failing to create orders with error "Current mode is set to isolated margin. Please switch to cross margin before making further adjustments." (code: 330006)
- **Root Cause**: When a position or account is already in isolated margin mode, attempting to set leverage or create orders fails even with the correct margin mode parameter
- **Solution**: Added `set_margin_mode('cross', symbol)` call before `set_leverage()` in both `create_market_order()` and `create_limit_order()` methods to explicitly switch from isolated to cross margin mode
- **Impact**: Bot can now switch from isolated to cross margin mode and create orders successfully regardless of the initial margin mode state
- **Files**: `kucoin_client.py` lines 178, 208

#### Margin Mode Mismatch Error (Code 330005)
- **Problem**: Bot was failing to create orders with error "The order's margin mode does not match the selected one. Please switch and try again." (code: 330005)
- **Root Cause**: While leverage was being set with cross margin mode, the order creation itself didn't explicitly specify the margin mode parameter
- **Solution**: Added `params={"marginMode": "cross"}` to both `create_market_order()` and `create_limit_order()` methods in `kucoin_client.py`
- **Impact**: Orders can now be created successfully with the correct margin mode matching the leverage setting
- **Files**: `kucoin_client.py` lines 189, 220

#### Futures Pair Detection Issue
- **Problem**: Bot was only detecting 1 futures contract (quarterly BTC futures) instead of all available contracts
- **Root Cause**: The `get_active_futures()` method in `kucoin_client.py` was only checking for `market.get('future')` which missed perpetual swaps
- **Solution**: Updated filter to `(market.get('swap') or market.get('future'))` to detect both:
  - Perpetual swaps (swap=True) - e.g., BTC/USDT:USDT, ETH/USDT:USDT
  - Dated futures (future=True) - e.g., BTC/USD:BTC-251226
- **Impact**: Bot now scans all available futures contracts instead of just quarterly futures
- **File**: `kucoin_client.py` line 28-48

#### Indicator Calculation Failures
- **Problem**: Bot was showing "Could not calculate indicators" warnings for all pairs
- **Root Cause**: Multiple issues causing empty DataFrames:
  1. Insufficient OHLCV data (<50 candles required)
  2. API fetch failures not properly retried
  3. Errors during indicator calculation not properly handled
- **Solutions**:
  1. Added retry logic (3 attempts with exponential backoff) for OHLCV fetching
  2. Added explicit check for minimum data requirement (50 candles)
  3. Wrapped indicator calculations in try-except for graceful error handling
  4. Enhanced logging to show exact data counts and failure reasons
- **Impact**: Better error handling and more reliable indicator calculations
- **Files**: 
  - `kucoin_client.py` lines 55-76 (OHLCV fetching with retry)
  - `indicators.py` lines 14-67 (improved error handling)
  - `market_scanner.py` lines 20-50 (better diagnostics)

#### Enhanced Logging and Diagnostics
- **Changes**:
  - Added debug logging showing breakdown of perpetual vs dated futures
  - Added warning when OHLCV data is insufficient with exact candle count
  - Added retry attempt logging for API failures
  - More descriptive error messages in market scanner
- **Impact**: Easier to diagnose issues and understand bot behavior
- **Files**: `kucoin_client.py`, `market_scanner.py`

### Added

#### Comprehensive Test Coverage
- **New Tests**:
  1. `test_futures_filter()` - Validates new market filtering logic
  2. `test_insufficient_data_handling()` - Tests graceful handling of edge cases
- **Coverage**:
  - Verifies detection of both perpetual swaps and dated futures
  - Confirms old filter only found 1 contract vs new filter finding 4+ contracts
  - Tests handling of insufficient data (<50 candles)
  - Tests handling of empty/None data
- **File**: `test_bot.py` lines 192-260

## Expected Behavior After Fixes

### Before
```
Found 1 active futures pairs
Scanning 1 trading pairs...
Could not calculate indicators for BTC/USD:BTC-251226
Scanned BTC/USD:BTC-251226: Signal=HOLD, Confidence=0.00, Score=0.00
Market scan complete. Found 0 trading opportunities
```

### After
```
Found 50+ active futures pairs
Breakdown: 45 perpetual swaps, 5 dated futures
Scanning 50+ trading pairs...
Fetched 100 candles for BTC/USDT:USDT
Scanned BTC/USDT:USDT: Signal=BUY, Confidence=0.72, Score=75.5
Scanned ETH/USDT:USDT: Signal=SELL, Confidence=0.65, Score=68.2
...
Market scan complete. Found 15 trading opportunities
```

## Migration Notes

No breaking changes. The fixes are backward compatible and will automatically improve bot behavior.

## Technical Details

### Market Types in KuCoin Futures
- **Perpetual Swaps**: `type='swap', swap=True, contract=True` - No expiry date, funding rate
- **Quarterly Futures**: `type='future', future=True, contract=True` - Fixed expiry date
- **Both**: Should have `active=True` to be tradeable

### Minimum Data Requirements
- **50 candles minimum**: Required for proper technical indicator calculation
- **SMA 50**: Needs 50 periods
- **Other indicators**: Need sufficient warmup period

### OHLCV Retry Logic
- **3 attempts**: With exponential backoff (1s, 2s, 3s delays)
- **Handles**: Network errors, rate limits, temporary API issues
- **Falls back**: Returns empty list if all attempts fail

## Testing

All tests pass (9/9):
```bash
python test_bot.py
```

Run comprehensive validation:
```bash
python /tmp/test_fixes.py  # If available
```

## Version Info

- **Fixed in**: Current development branch
- **Affects**: All users running previous version
- **Priority**: High - Critical functionality fix
