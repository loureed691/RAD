# Testing Guide

## Quick Start

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-timeout pytest-cov

# Run all tests
pytest tests_unit/ tests_integration/ tests_resilience/ -v

# Expected output: 13 passed in ~3.3s ✅
```

## Test Structure

```
tests_unit/          - Pure functions (4 tests, 0.03s)
tests_integration/   - Component interactions (4 tests, 0.03s)
tests_resilience/    - Failure scenarios (5 tests, 3.3s)
tests_contract/      - API contracts (placeholder)
tests_perf/          - Benchmarks (placeholder)
```

## Run Specific Tests

```bash
# Unit tests only
pytest tests_unit/ -v

# Integration tests only
pytest tests_integration/ -v

# Resilience tests only
pytest tests_resilience/ -v

# With coverage
pytest tests_unit/ tests_integration/ --cov=. --cov-report=term-missing

# Specific test file
pytest tests_unit/test_precision.py -v

# Specific test function
pytest tests_unit/test_precision.py::test_round_to_precision_basic -v
```

## CI/CD

Tests run automatically on:
- Push to main/develop/copilot branches
- Pull requests
- Manual trigger (Actions tab)

See: `.github/workflows/tests.yml`

## Documentation

- **Full Strategy**: `docs/TESTING_STRATEGY.md`
- **Test Coverage**: Precision, NaN guards, order validation, retry logic
- **Test Speed**: Fast (<5s total for unit+integration)

## Writing New Tests

1. Choose appropriate directory (unit/integration/resilience)
2. Use fixtures from `conftest.py`
3. Follow existing test patterns
4. Keep tests fast and deterministic
5. Run locally before pushing

## Legacy Tests

Old tests (47 files) were removed and archived in `tests-legacy-archive` branch.

For details, see: `docs/STABILIZATION_SUMMARY.md`
