#!/usr/bin/env python3
"""
Example demonstrating the new bot improvements:
- Health monitoring
- Error recovery with exponential backoff
- Circuit breaker
- Rate limiter
"""

# Example 1: Using retry decorator for API calls
from error_recovery import retry_with_backoff, safe_api_call
import time

print("=" * 60)
print("Example 1: Retry Decorator")
print("=" * 60)

@retry_with_backoff(max_retries=3, base_delay=0.5)
def fetch_market_data(symbol):
    """Simulated API call that might fail"""
    import random
    if random.random() < 0.7:  # 70% chance of failure
        raise Exception("API timeout")
    return {"symbol": symbol, "price": 50000}

try:
    print(f"Fetching data with auto-retry...")
    data = fetch_market_data("BTC-USDT")
    print(f"✅ Success: {data}")
except Exception as e:
    print(f"❌ Failed after retries: {e}")

print()

# Example 2: Circuit Breaker
print("=" * 60)
print("Example 2: Circuit Breaker")
print("=" * 60)

from error_recovery import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=2.0
)

def unreliable_service():
    """Simulated service that always fails"""
    raise Exception("Service unavailable")

# Simulate failures
for i in range(5):
    try:
        result = breaker.call(unreliable_service)
        print(f"Call {i+1}: Success")
    except Exception as e:
        state = breaker.get_state()
        print(f"Call {i+1}: Failed - Circuit: {state['state']} (failures: {state['failure_count']})")
    time.sleep(0.2)

print()

# Example 3: Rate Limiter
print("=" * 60)
print("Example 3: Rate Limiter")
print("=" * 60)

from error_recovery import RateLimiter

# Allow 3 calls per second
limiter = RateLimiter(max_calls=3, time_window=1.0)

print("Making 5 API calls (limit: 3 per second)...")
start = time.time()

for i in range(5):
    can_proceed, wait_time = limiter.can_proceed()
    
    if not can_proceed:
        print(f"  Call {i+1}: Rate limited! Waiting {wait_time:.2f}s...")
        time.sleep(wait_time)
        limiter.can_proceed()  # Try again after waiting
    
    print(f"  Call {i+1}: Proceeding")

elapsed = time.time() - start
print(f"Total time: {elapsed:.2f}s (should be ~1s due to rate limiting)")

print()

# Example 4: Safe API Call
print("=" * 60)
print("Example 4: Safe API Call")
print("=" * 60)

call_count = [0]

def flaky_api():
    """API that fails first 2 times"""
    call_count[0] += 1
    if call_count[0] < 3:
        raise Exception(f"API error (attempt {call_count[0]})")
    return {"status": "ok", "data": [1, 2, 3]}

print("Calling flaky API with safe wrapper...")
result = safe_api_call(
    flaky_api,
    max_retries=5,
    on_error=lambda e: print(f"  Retry needed: {e}")
)

if result:
    print(f"✅ Success after {call_count[0]} attempts: {result}")
else:
    print("❌ Failed after all retries")

print()

# Example 5: Health Monitoring
print("=" * 60)
print("Example 5: Health Monitoring")
print("=" * 60)

from health_monitor import HealthMonitor

monitor = HealthMonitor()

# Simulate some activity
print("Simulating bot activity...")

# API calls
for i in range(10):
    monitor.record_api_call(success=True)
monitor.record_api_call(success=False)

# Positions
monitor.record_position_opened("BTC-USDT")
monitor.record_position_opened("ETH-USDT")
monitor.record_position_closed("BTC-USDT", 0.05, True)  # +5% win

# Scans
monitor.record_scan_completed(5.2)
monitor.record_scan_completed(4.8)

# Thread heartbeats
monitor.heartbeat_main_loop()
monitor.heartbeat_scanner()
monitor.heartbeat_position_monitor()

# Get status summary
print("\n" + monitor.get_status_summary())

print()

# Example 6: Combining Features
print("=" * 60)
print("Example 6: Real-World Usage")
print("=" * 60)

print("""
In the actual bot, these features work together:

1. Health Monitor tracks all operations automatically
2. Retry logic handles transient API failures
3. Circuit breaker protects against persistent failures
4. Rate limiter prevents API throttling

Example from bot.py:

    # Health monitoring (automatic)
    self.health_monitor.record_api_call(success=True)
    self.health_monitor.heartbeat_scanner()
    
    # Error recovery (when needed)
    @retry_with_backoff(max_retries=3)
    def get_market_data():
        return self.client.get_ticker(symbol)
    
    # Circuit breaker for external services
    result = self.api_breaker.call(external_service)
    
    # Rate limiting for API calls
    self.api_limiter.wait_if_needed()
    
All of this happens transparently in the background! 🚀
""")

print("=" * 60)
print("✅ Examples Complete!")
print("=" * 60)
print("\nThese improvements make the bot:")
print("  ✅ More reliable (automatic retry)")
print("  ✅ More resilient (circuit breaker)")
print("  ✅ More observable (health monitoring)")
print("  ✅ More production-ready (rate limiting)")
print("\nSee BOT_IMPROVEMENTS.md for full documentation!")
