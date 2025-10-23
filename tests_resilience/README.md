# Resilience Tests

Chaos testing for failure scenarios.

## Run Tests
```bash
pytest tests_resilience/ -v
```

## Coverage
- Rate limit handling (429)
- Network errors with retries
- WebSocket reconnection
- Partial order fills
- Out-of-order messages
- Circuit breaker behavior
