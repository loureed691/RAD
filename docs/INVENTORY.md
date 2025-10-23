# Trading Bot Inventory & Risk Map

## Repository Overview
- **Language**: Python 3.12
- **Entry Point**: `start.py` (wrapper) → `bot.py` (main orchestrator)
- **Dependencies**: 18 packages (ccxt, pandas, numpy, scikit-learn, tensorflow, xgboost, lightgbm, catboost, optuna, etc.)
- **Test Files**: 47 test_*.py files (to be removed)

## Critical Modules (Hotspots)

### 1. API Client (`kucoin_client.py` - 1965 lines)
**Complexity**: HIGH
**Risk**: HIGH
**Key Features**:
- API call prioritization (CRITICAL, HIGH, NORMAL, LOW)
- Circuit breaker for API failures
- Symbol metadata caching
- Clock sync tracking
- Retry logic with exponential backoff
- WebSocket integration

**Potential Issues**:
- Clock skew handling (ms vs s timestamps)
- API signature generation
- Rate limiting (429 errors)
- Session reuse and timeout management
- Circuit breaker reset logic
- Retries with jitter needed

### 2. WebSocket Client (`kucoin_websocket.py` - 445 lines)
**Complexity**: MEDIUM
**Risk**: HIGH
**Key Features**:
- Real-time market data (tickers, candles, orderbooks)
- Thread-safe data storage
- Connection token management

**Potential Issues**:
- Reconnection state machine needs review
- Heartbeat/ping-pong handling
- Out-of-order message handling
- Memory leaks in data buffers
- Backpressure when messages arrive faster than processing
- Thread safety in data updates

### 3. Position Manager (`position_manager.py` - 1979 lines)
**Complexity**: HIGH
**Risk**: HIGH
**Key Features**:
- Trailing stop loss
- Breakeven moves
- Profit velocity tracking
- Partial exits
- Volume profile analysis

**Potential Issues**:
- Position state consistency
- Duplicate order prevention
- PnL calculation accuracy (fees, funding)
- Leverage-adjusted calculations
- NaN/Inf handling in calculations
- Thread safety for concurrent updates

### 4. Risk Manager (`risk_manager.py` - 1146 lines)
**Complexity**: MEDIUM
**Risk**: HIGH
**Key Features**:
- Position sizing
- Drawdown tracking
- Daily loss limits
- Kill switch
- Kelly Criterion
- Correlation groups

**Potential Issues**:
- Division by zero in Kelly calculations
- Floating point precision in risk calculations
- Kill switch activation/deactivation logic
- Daily reset timing (timezone aware)

### 5. Signal Generator (`signals.py` - 712 lines)
**Complexity**: MEDIUM
**Risk**: MEDIUM
**Key Features**:
- Technical indicators (RSI, MACD, etc.)
- Pattern recognition
- Support/resistance detection
- Divergence detection

**Potential Issues**:
- NaN/Inf from indicator calculations
- Empty DataFrame handling
- Rolling window with insufficient data
- CPU-intensive calculations blocking event loop

### 6. Main Bot (`bot.py` - 980 lines)
**Complexity**: HIGH
**Risk**: MEDIUM
**Key Features**:
- Component orchestration
- Main event loop
- Signal handling (SIGINT, SIGTERM)
- Auto-configuration from balance

**Potential Issues**:
- Thread coordination
- Graceful shutdown
- Balance fetch failure handling

## Symptom → Hypothesis Table

| Symptom | Hypothesis | Probability | Reason |
|---------|-----------|-------------|---------|
| Order rejections (precision) | Incorrect rounding/precision for minQty/stepSize | HIGH | Common issue with futures exchanges |
| API authentication failures | Clock skew, signature generation issue | HIGH | KuCoin requires precise timestamps |
| Rate limit errors (429) | Missing backoff, no jitter in retries | MEDIUM | Circuit breaker exists but may need tuning |
| WebSocket disconnects | Missing heartbeat, no reconnect backoff | MEDIUM | Common WS issue, needs investigation |
| Position tracking drift | PnL calculation excluding fees/funding | MEDIUM | Multiple devs, fee handling may be inconsistent |
| Memory leak | Unbounded data buffers in WS or indicators | LOW | Would need long-running test to confirm |
| NaN/Inf errors | Insufficient data validation in indicators | MEDIUM | Division by zero, log(0), etc. |
| Duplicate orders | Race condition in position checking | LOW | Priority system should prevent this |
| Event loop blocking | Synchronous heavy computation in async code | LOW | Most operations appear threaded |

## Code Complexity Analysis

### High Complexity Modules (>1000 lines)
1. `kucoin_client.py` (1965) - API wrapper, retries, circuit breaker
2. `position_manager.py` (1979) - Position tracking, exits
3. `risk_manager.py` (1146) - Risk calculations, Kelly Criterion

### Recent Changes
- Last commit: "Initial plan" (current work)
- Previous: Merge PR #178 "optimize-bot-trading-strategies"
- History suggests active development, multiple strategy improvements

## Dependencies Check
- ✅ ccxt >= 4.0.0 (API client)
- ✅ pandas >= 2.0.0 (data handling)
- ✅ numpy >= 1.24.0 (numerical operations)
- ✅ scikit-learn >= 1.3.0 (ML models)
- ✅ ta >= 0.11.0 (technical analysis)
- ✅ websocket-client >= 1.6.0 (WebSocket)
- ⚠️  Heavy ML deps: tensorflow, xgboost, lightgbm, catboost (may impact startup)

## Configuration Analysis
- `.env.example`: Well-documented, safe defaults
- Docker support: Basic Dockerfile and docker-compose.yml
- No CI workflow found (will need to create)

## Test Suite Analysis
- **Total test files**: 47
- **Categories**: Integration, unit, bug fixes, feature-specific
- **Status**: TO BE REMOVED (per requirements)
- **Test runners**: `run_all_tests.py`, `run_priority1_tests.sh`

## Recommendations Priority

### P0 (Critical - Must Fix)
1. Order precision validation before submission
2. Clock sync verification and adjustment
3. API retry with exponential backoff + jitter
4. WebSocket reconnection with backoff
5. NaN/Inf guards in all calculations

### P1 (High - Should Fix)
1. Fee and funding rate inclusion in PnL
2. Session reuse for API calls
3. Idempotency keys for order submissions
4. Timeout management (connection and read)
5. Thread-safe state updates

### P2 (Medium - Nice to Have)
1. Memory profiling for leak detection
2. Metrics/instrumentation for observability
3. Event loop lag monitoring
4. Better error messages with context

## Next Steps
1. Create dummy testnet environment
2. Run baseline profiling (10-15 min)
3. Implement P0 fixes
4. Remove old tests
5. Design new testing strategy
6. Implement new test suite
7. Re-run profiling for comparison
