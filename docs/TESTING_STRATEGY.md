# Testing Strategy for KuCoin Futures Trading Bot

## Overview

This document defines the comprehensive testing strategy for the RAD KuCoin Futures Trading Bot. The strategy is designed to be **practical, maintainable, and production-focused**, ensuring the bot is stable, reliable, and robust under real-world market conditions.

## Goals

1. **Stability Under Market Noise**: Ensure the bot handles irregular market data, price spikes, and data gaps gracefully
2. **Network Resilience**: Handle API failures, rate limits, timeouts, and reconnections without data loss
3. **Order Precision**: Validate all orders meet exchange requirements (precision, step size, min/max limits)
4. **Reconnect Behavior**: Ensure WebSocket reconnections don't lose state or create duplicate orders
5. **Performance**: Maintain acceptable CPU/memory usage and response times under load

## Test Pyramid

We follow a lean test pyramid focused on high-value, maintainable tests:

```
          ╱╲
         ╱ E2E/Contract ╲   ← Few, critical paths only
        ╱─────────────────╲
       ╱   Integration    ╲  ← Core workflows
      ╱───────────────────╲
     ╱        Unit         ╲ ← Pure logic, minimal
    ╱───────────────────────╲
```

### Unit Tests (Minimal, Targeted)
- **Purpose**: Test pure functions and calculations in isolation
- **Scope**: 
  - Precision rounding functions
  - NaN/Inf guards in indicators
  - Kelly Criterion calculations
  - Price formatting utilities
- **Location**: `tests_unit/`
- **Characteristics**: Fast (<1ms each), no I/O, deterministic

### Integration Tests (Core Workflow)
- **Purpose**: Test component interactions with mocked external dependencies
- **Scope**:
  - Order creation with mocked API client
  - WebSocket message handling with mock data
  - Position manager state transitions
  - Risk manager decision logic
  - Signal generation with fixed seed data
- **Location**: `tests_integration/`
- **Characteristics**: Fast (<100ms each), mocked API/WebSocket, deterministic
- **Tools**: 
  - `respx` or `vcrpy` for HTTP mocking
  - Custom WebSocket replay fixtures
  - `freezegun` for time control
  - `hypothesis` for property-based testing

### Contract Tests (Sandbox/Testnet)
- **Purpose**: Validate assumptions about KuCoin API behavior
- **Scope**:
  - Sandbox time sync check
  - Symbol metadata fetching
  - Dry-run order placement (testnet, no actual trades)
  - Order validation rejection reasons
- **Location**: `tests_contract/`
- **Characteristics**: Slower (1-5s each), uses testnet/sandbox, network-dependent
- **Run Cadence**: Nightly or on-demand (not on every push)

### Resilience Tests (Chaos Testing)
- **Purpose**: Verify bot handles failures gracefully
- **Scope**:
  - 429 rate limit handling (with backoff/jitter)
  - 5xx server errors (with retries)
  - Network timeouts
  - Partial order fills
  - WebSocket disconnections
  - Out-of-order messages
- **Location**: `tests_resilience/`
- **Characteristics**: Medium speed (100ms-1s), controlled failure injection
- **Tools**: Mock API with configurable error rates

### Performance Tests (Benchmarking)
- **Purpose**: Ensure bot meets performance requirements
- **Scope**:
  - Signal pipeline throughput (ticks/second)
  - Indicator calculation latency (p50, p95, p99)
  - Memory usage over time (leak detection)
  - API call latency tracking
  - 10-15 minute soak test
- **Location**: `tests_perf/`
- **Characteristics**: Long-running (10-15 min), resource monitoring
- **Tools**: `pytest-benchmark`, `tracemalloc`, `cProfile`
- **Run Cadence**: Nightly or before releases

## Test Infrastructure

### Directory Structure
```
tests_unit/
  conftest.py              # Shared fixtures
  test_precision.py        # Rounding and precision
  test_indicators.py       # NaN/Inf guards
  test_risk_calcs.py       # Kelly, position sizing

tests_integration/
  conftest.py              # Mocked API/WS fixtures
  test_order_flow.py       # Order creation pipeline
  test_position_manager.py # State transitions
  test_risk_manager.py     # Risk decisions
  test_signals.py          # Signal generation
  test_websocket.py        # WS message handling

tests_contract/
  conftest.py              # Testnet configuration
  test_api_contract.py     # KuCoin API assumptions
  test_time_sync.py        # Clock drift
  test_order_validation.py # Exchange rejection reasons

tests_resilience/
  conftest.py              # Failure injection fixtures
  test_retries.py          # Backoff and jitter
  test_circuit_breaker.py  # Circuit breaker behavior
  test_reconnect.py        # WebSocket reconnection
  test_partial_fills.py    # Partial order handling

tests_perf/
  conftest.py              # Performance fixtures
  test_throughput.py       # Signal pipeline throughput
  test_latency.py          # API and indicator latency
  test_memory.py           # Memory leak detection
  test_soak.py             # Long-running stability test
```

### Shared Fixtures (conftest.py)

#### Test Configuration
```python
@pytest.fixture
def testnet_config():
    """Dummy testnet configuration"""
    return {
        'api_key': 'dummy_test_key',
        'api_secret': 'dummy_test_secret',
        'api_passphrase': 'dummy_test_passphrase',
        'base_url': 'https://api-sandbox-futures.kucoin.com',
        'use_testnet': True
    }
```

#### Time Control
```python
@pytest.fixture
def frozen_time():
    """Freeze time for deterministic tests"""
    with freeze_time("2025-01-15 12:00:00 UTC"):
        yield
```

#### Mock API Client
```python
@pytest.fixture
def mock_api_client():
    """Mocked KuCoin API client"""
    # Use respx or vcrpy to mock HTTP calls
    pass
```

#### WebSocket Replay
```python
@pytest.fixture
def ws_replay_fixture():
    """Pre-recorded WebSocket messages for replay"""
    # Load fixture data from JSON
    pass
```

#### Deterministic Market Data
```python
@pytest.fixture
def market_data_fixture():
    """Fixed OHLCV data for testing indicators"""
    # Use fixed seed for reproducibility
    np.random.seed(42)
    return generate_synthetic_ohlcv(periods=100)
```

## Test Tooling

### Core Framework
- **pytest**: Test runner
- **pytest-asyncio**: Async test support
- **pytest-timeout**: Prevent hanging tests
- **pytest-benchmark**: Performance benchmarking

### Mocking & Fixtures
- **respx**: Modern HTTP mocking for httpx
- **vcrpy**: Record/replay HTTP interactions (alternative)
- **freezegun**: Time mocking for deterministic tests
- **unittest.mock**: Standard library mocking

### Property-Based Testing
- **hypothesis**: Generate test cases automatically
  - Example: Test precision rounding with random floats
  - Example: Verify NaN guards with generated edge cases

### Performance & Profiling
- **pytest-benchmark**: Automated benchmarking
- **tracemalloc**: Memory profiling
- **cProfile** / **pyinstrument**: CPU profiling

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM UTC
  workflow_dispatch:     # Manual trigger

jobs:
  unit-integration:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-timeout pytest-benchmark hypothesis freezegun respx
      - name: Run unit tests
        run: pytest tests_unit/ -v --tb=short --timeout=5
      - name: Run integration tests
        run: pytest tests_integration/ -v --tb=short --timeout=30

  contract:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-timeout
      - name: Run contract tests (testnet)
        run: pytest tests_contract/ -v --tb=short --timeout=60
        env:
          KUCOIN_API_KEY: ${{ secrets.TESTNET_API_KEY }}
          KUCOIN_API_SECRET: ${{ secrets.TESTNET_API_SECRET }}
          KUCOIN_API_PASSPHRASE: ${{ secrets.TESTNET_API_PASSPHRASE }}
          USE_TESTNET: true

  resilience:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-timeout
      - name: Run resilience tests
        run: pytest tests_resilience/ -v --tb=short --timeout=120

  performance:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-benchmark
      - name: Run performance tests
        run: pytest tests_perf/ -v --benchmark-only --benchmark-autosave
      - name: Archive benchmarks
        uses: actions/upload-artifact@v3
        with:
          name: benchmarks
          path: .benchmarks/
```

## Metrics & Thresholds

### Performance Budgets
- **Signal Pipeline**: ≤100ms p95 latency
- **Order Creation**: ≤500ms p95 latency
- **Indicator Calculation**: ≤50ms p95 latency
- **Memory Usage**: ≤500MB RSS for 15-minute soak test
- **CPU Usage**: ≤50% average over 15 minutes

### Reliability Metrics
- **API Success Rate**: ≥99% (excluding intentional 429s)
- **WebSocket Reconnection**: <5 attempts within 2 minutes
- **Order Validation**: 100% precision compliance
- **No Crashes**: 0 uncaught exceptions in 15-minute soak test

## Example Tests

### Unit Test: Precision Rounding
```python
def test_round_to_precision():
    """Test precision rounding for order amounts"""
    client = KuCoinClient(...)
    
    assert client._round_to_precision(1.23456, 2) == 1.23
    assert client._round_to_precision(1.23456, 4) == 1.2345
    assert client._round_to_precision(1.23456, None) == 1.23456
    
@given(st.floats(min_value=0.001, max_value=10000), st.integers(min_value=0, max_value=8))
def test_round_to_precision_property(value, precision):
    """Property: rounding should never increase value"""
    client = KuCoinClient(...)
    rounded = client._round_to_precision(value, precision)
    assert rounded <= value
```

### Integration Test: Order Creation
```python
@pytest.mark.asyncio
async def test_create_order_with_mock(mock_api_client):
    """Test order creation with mocked API"""
    mock_api_client.post('/api/v1/orders').mock(
        return_value={'orderId': '123', 'status': 'success'}
    )
    
    order = await mock_api_client.create_market_order('BTC-USDT', 'buy', 1.0, leverage=10)
    
    assert order['orderId'] == '123'
    assert order['status'] == 'success'
```

### Resilience Test: Rate Limit Handling
```python
def test_rate_limit_with_jitter(mock_api_client):
    """Test retry with jitter after rate limit"""
    attempts = []
    
    def mock_api_call():
        attempts.append(time.time())
        if len(attempts) < 3:
            raise ccxt.RateLimitExceeded("429 Rate Limit")
        return {'success': True}
    
    result = mock_api_client._handle_api_error(
        mock_api_call, max_retries=3, exponential_backoff=True
    )
    
    assert result['success']
    assert len(attempts) == 3
    
    # Verify exponential backoff with jitter
    delay1 = attempts[1] - attempts[0]
    delay2 = attempts[2] - attempts[1]
    
    # Should be roughly 1s and 2s with ±20% jitter
    assert 0.8 < delay1 < 1.2
    assert 1.6 < delay2 < 2.4
```

### Performance Test: Signal Pipeline Throughput
```python
def test_signal_pipeline_throughput(benchmark, market_data_fixture):
    """Benchmark signal generation throughput"""
    signal_gen = SignalGenerator()
    
    result = benchmark(signal_gen.generate_signal, market_data_fixture, 'BTC-USDT')
    
    # Should process at least 20 signals/second
    assert benchmark.stats['mean'] < 0.05  # 50ms = 20/s
```

## Maintenance Guidelines

1. **Keep Tests Fast**: Unit and integration tests should run in <5 minutes total
2. **Avoid Flaky Tests**: Use deterministic seeds, fixed time, and proper mocking
3. **Test Behavior, Not Implementation**: Focus on outcomes, not internal details
4. **Update Fixtures Regularly**: Keep test data representative of real market conditions
5. **Monitor Test Coverage**: Aim for >80% coverage on critical paths (API, orders, risk)
6. **Review Benchmark Trends**: Track performance metrics over time to detect regressions

## Migration Plan

1. ✅ Remove legacy tests (archived in `tests-legacy-archive` branch)
2. Create new directory structure
3. Implement shared fixtures (conftest.py)
4. Write minimal example tests for each category
5. Set up GitHub Actions workflow
6. Run initial baseline performance tests
7. Gradually add more tests as needed (don't over-test!)

## Success Criteria

- ✅ Old tests removed
- ✅ New test structure documented
- ⏳ Core fixtures implemented
- ⏳ Minimal tests passing
- ⏳ CI workflow operational
- ⏳ Performance baseline established

## Conclusion

This testing strategy prioritizes **practical, maintainable tests** over comprehensive coverage. We focus on:
- Critical paths (order flow, risk management)
- Edge cases (NaN/Inf, rate limits, reconnections)
- Performance regressions
- Real-world failure scenarios

The strategy avoids:
- Over-mocking (test actual behavior when feasible)
- Brittle tests (coupled to implementation details)
- Slow test suites (optimize for developer productivity)
- False sense of security (100% coverage ≠ bug-free)
