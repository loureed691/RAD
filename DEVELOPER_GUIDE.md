# Developer Quick Reference - Modern Python Standards

## Quick Setup
```bash
# Python 3.12+ recommended
python --version  # Should be 3.11+

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_bot.py
python test_integration.py

# Start bot
python bot.py
```

## Code Style

### String Formatting
```python
# ✅ Good - Use f-strings
name = "Bitcoin"
price = 45000.50
message = f"Current {name} price: ${price:.2f}"

# ❌ Avoid - Old style
message = "Current %s price: $%.2f" % (name, price)
message = "Current {} price: ${:.2f}".format(name, price)
```

### Type Hints
```python
# ✅ Good - Use type hints
def calculate_position_size(
    balance: float,
    risk_percent: float,
    stop_loss: float
) -> float:
    return balance * risk_percent / stop_loss

# ❌ Missing - No type hints
def calculate_position_size(balance, risk_percent, stop_loss):
    return balance * risk_percent / stop_loss
```

### Exception Handling
```python
# ✅ Good - Specific exceptions
try:
    result = api_call()
except requests.RequestException as e:
    logger.error(f"API error: {e}")
except ValueError as e:
    logger.error(f"Invalid value: {e}")

# ❌ Avoid - Bare except
try:
    result = api_call()
except:
    logger.error("Error occurred")
```

### Modern Features (Python 3.10+)
```python
# ✅ Use match/case for complex conditionals
match signal_type:
    case "BUY":
        execute_buy_order()
    case "SELL":
        execute_sell_order()
    case _:
        logger.warning("Unknown signal")

# ✅ Use walrus operator for assignments in conditions
if (price := get_current_price()) > threshold:
    logger.info(f"Price {price} exceeds threshold")

# ✅ Use | for Union types
from typing import Union
def process_data(data: dict | None) -> str | None:
    return data.get("key") if data else None
```

## Testing

### Run All Tests
```bash
# Basic tests
python test_bot.py

# Integration tests  
python test_integration.py

# Risk management tests
python test_risk_management.py

# Specific test file
python test_YOUR_MODULE.py
```

### Write Tests
```python
def test_calculate_position_size():
    """Test position size calculation"""
    balance = 1000.0
    risk_percent = 0.02
    stop_loss = 0.05
    
    size = calculate_position_size(balance, risk_percent, stop_loss)
    
    assert size > 0
    assert size == 400.0  # Expected: 1000 * 0.02 / 0.05
    print("✓ Position size calculation works")
```

## Code Quality Tools

### Flake8 (Style Checking)
```bash
# Check all files
flake8 .

# Check specific file
flake8 bot.py

# With specific rules
flake8 . --select=E9,F63,F7,F82
```

### Black (Auto-formatting)
```bash
# Format all files
black .

# Check without formatting
black . --check

# Format specific file
black bot.py
```

### MyPy (Type Checking)
```bash
# Type check all files
mypy .

# Specific file
mypy bot.py

# With strict mode
mypy . --strict
```

## Git Workflow

### Before Commit
```bash
# 1. Run tests
python test_bot.py

# 2. Check code style (optional)
flake8 .

# 3. Stage changes
git add .

# 4. Commit with descriptive message
git commit -m "Add feature: description"

# 5. Push
git push
```

### Commit Message Format
```
<type>: <description>

Examples:
- feat: Add new trading strategy
- fix: Fix position sizing bug
- docs: Update README with examples
- refactor: Improve code structure
- test: Add integration tests
- chore: Update dependencies
```

## Performance Tips

### Profiling
```python
import time

# Simple timing
start = time.time()
result = heavy_computation()
duration = time.time() - start
logger.debug(f"Computation took {duration:.2f}s")

# Performance monitoring (built-in)
from performance_monitor import get_monitor
monitor = get_monitor()
# Automatically tracks API calls and performance
```

### Optimization
```python
# ✅ Use list comprehensions
squares = [x**2 for x in range(100)]

# ✅ Use generator expressions for large data
sum_squares = sum(x**2 for x in range(1000000))

# ✅ Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(n):
    return n ** 2 + n ** 3
```

## Debugging

### Logging Levels
```python
from logger import Logger

logger = Logger.get_logger()

logger.debug("Detailed debug information")      # Development
logger.info("General information")              # Normal operation
logger.warning("Warning message")               # Potential issues
logger.error("Error occurred")                  # Errors
logger.critical("Critical failure")             # System failures
```

### Debug Mode
```python
# In config.py
LOG_LEVEL = 'DEBUG'  # Show all logs

# In .env
LOG_LEVEL=DEBUG
DETAILED_LOG_LEVEL=DEBUG
```

## Common Patterns

### Safe Dictionary Access
```python
# ✅ Good - Use .get() with default
value = data.get('key', default_value)

# ✅ Good - Check existence
if 'key' in data:
    value = data['key']

# ❌ Risky - Direct access
value = data['key']  # KeyError if missing
```

### Threading
```python
import threading

# Always use locks for shared data
lock = threading.Lock()

def modify_shared_data():
    with lock:
        # Modify shared variables here
        shared_data['key'] = value
```

### Resource Management
```python
# ✅ Good - Use context managers
with open('file.txt', 'r') as f:
    content = f.read()

# ✅ Good - Explicit try/finally
try:
    resource = acquire_resource()
    use_resource(resource)
finally:
    release_resource(resource)
```

## Environment Configuration

### .env File Structure
```bash
# API Configuration (Required)
KUCOIN_API_KEY=your_key
KUCOIN_API_SECRET=your_secret
KUCOIN_API_PASSPHRASE=your_passphrase

# WebSocket (Optional, default: true)
ENABLE_WEBSOCKET=true

# Trading Parameters (Optional, auto-configured)
# LEVERAGE=10
# MAX_POSITION_SIZE=1000
# RISK_PER_TRADE=0.02

# Performance (Optional)
CHECK_INTERVAL=60
MAX_WORKERS=20
CACHE_DURATION=300

# Logging (Optional)
LOG_LEVEL=INFO
DETAILED_LOG_LEVEL=DEBUG
```

## Troubleshooting

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify installation
python -c "import ccxt; import pandas; print('OK')"
```

### Test Failures
```bash
# Run with verbose output
python test_bot.py -v

# Check specific test
python -c "from test_bot import test_specific; test_specific()"
```

### Performance Issues
```bash
# Check workers configuration
MAX_WORKERS=20  # Increase for faster scanning

# Check cache duration
CACHE_DURATION=300  # Adjust based on trading style
```

## Quick Reference - Key Files

| File | Purpose |
|------|---------|
| `bot.py` | Main bot orchestrator |
| `config.py` | Configuration management |
| `kucoin_client.py` | Exchange API wrapper |
| `risk_manager.py` | Risk management |
| `position_manager.py` | Position tracking |
| `market_scanner.py` | Market analysis |
| `ml_model.py` | Machine learning |
| `indicators.py` | Technical indicators |
| `signals.py` | Signal generation |

## Resources

- [Python 3.12 Docs](https://docs.python.org/3.12/)
- [Type Hints Guide](https://docs.python.org/3/library/typing.html)
- [CCXT Documentation](https://docs.ccxt.com/)
- [Project README](README.md)
- [Modernization Summary](MODERNIZATION_SUMMARY.md)

---
**Quick Tip**: Run `python test_bot.py` regularly to ensure everything works!
