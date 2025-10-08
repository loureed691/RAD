#!/usr/bin/env python3
"""
Test suite for error recovery functionality
"""
import time
from error_recovery import (
    ExponentialBackoff,
    retry_with_backoff,
    CircuitBreaker,
    RateLimiter,
    safe_api_call
)


def test_exponential_backoff():
    """Test exponential backoff calculation"""
    print("Testing exponential backoff...")
    
    backoff = ExponentialBackoff(
        base_delay=1.0,
        max_delay=10.0,
        max_retries=5,
        jitter=False  # Disable jitter for predictable testing
    )
    
    # First attempt
    delay1 = backoff.get_delay()
    assert delay1 == 1.0, f"First delay should be 1.0s, got {delay1}"
    backoff.attempt += 1
    
    # Second attempt
    delay2 = backoff.get_delay()
    assert delay2 == 2.0, f"Second delay should be 2.0s, got {delay2}"
    backoff.attempt += 1
    
    # Third attempt
    delay3 = backoff.get_delay()
    assert delay3 == 4.0, f"Third delay should be 4.0s, got {delay3}"
    backoff.attempt += 1
    
    # Fourth attempt
    delay4 = backoff.get_delay()
    assert delay4 == 8.0, f"Fourth delay should be 8.0s, got {delay4}"
    backoff.attempt += 1
    
    # Fifth attempt - should cap at max_delay
    delay5 = backoff.get_delay()
    assert delay5 == 10.0, f"Fifth delay should be capped at 10.0s, got {delay5}"
    
    # Test should_retry
    assert backoff.should_retry(), "Should still be able to retry"
    backoff.attempt += 1
    assert not backoff.should_retry(), "Should not be able to retry after max attempts"
    
    # Test reset
    backoff.reset()
    assert backoff.attempt == 0, "Attempt counter should be reset"
    assert backoff.should_retry(), "Should be able to retry after reset"
    
    print("✅ Exponential backoff test passed")


def test_retry_decorator():
    """Test retry decorator"""
    print("Testing retry decorator...")
    
    call_count = [0]
    
    @retry_with_backoff(max_retries=3, base_delay=0.1, max_delay=1.0)
    def flaky_function():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError("Simulated error")
        return "success"
    
    result = flaky_function()
    
    assert result == "success", "Should eventually succeed"
    assert call_count[0] == 3, f"Should have called function 3 times, got {call_count[0]}"
    
    print("✅ Retry decorator test passed")


def test_retry_decorator_failure():
    """Test retry decorator with persistent failure"""
    print("Testing retry decorator with persistent failure...")
    
    call_count = [0]
    
    @retry_with_backoff(max_retries=2, base_delay=0.1)
    def always_fails():
        call_count[0] += 1
        raise ValueError("Always fails")
    
    try:
        always_fails()
        assert False, "Should have raised exception"
    except ValueError as e:
        assert "Always fails" in str(e), "Should raise original exception"
        assert call_count[0] == 3, f"Should have called 3 times (initial + 2 retries), got {call_count[0]}"
    
    print("✅ Retry decorator failure test passed")


def test_circuit_breaker():
    """Test circuit breaker pattern"""
    print("Testing circuit breaker...")
    
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=1.0
    )
    
    # Initial state should be CLOSED
    assert breaker.state == 'CLOSED', "Initial state should be CLOSED"
    
    # Simulate failures
    for i in range(3):
        try:
            breaker.call(lambda: (_ for _ in ()).throw(Exception("Simulated failure")))
        except Exception:
            pass
    
    # Circuit should now be OPEN
    assert breaker.state == 'OPEN', "Circuit should be OPEN after failures"
    
    # Calls should fail fast
    try:
        breaker.call(lambda: "test")
        assert False, "Should have raised exception when circuit is OPEN"
    except Exception as e:
        assert "Circuit breaker is OPEN" in str(e), "Should indicate circuit is open"
    
    # Wait for recovery timeout
    time.sleep(1.1)
    
    # Successful call should close circuit
    result = breaker.call(lambda: "success")
    assert result == "success", "Call should succeed in HALF_OPEN state"
    assert breaker.state == 'CLOSED', "Circuit should be CLOSED after successful call"
    
    print("✅ Circuit breaker test passed")


def test_rate_limiter():
    """Test rate limiter"""
    print("Testing rate limiter...")
    
    # Allow 3 calls per second
    limiter = RateLimiter(max_calls=3, time_window=1.0)
    
    # First 3 calls should succeed
    for i in range(3):
        can_proceed, wait_time = limiter.can_proceed()
        assert can_proceed, f"Call {i+1} should be allowed"
        assert wait_time is None, "Wait time should be None"
    
    # 4th call should be rate limited
    can_proceed, wait_time = limiter.can_proceed()
    assert not can_proceed, "4th call should be rate limited"
    assert wait_time is not None, "Should have a wait time"
    assert wait_time > 0, "Wait time should be positive"
    
    # Wait and try again
    time.sleep(1.1)
    
    # Should be able to proceed now
    can_proceed, wait_time = limiter.can_proceed()
    assert can_proceed, "Should be allowed after waiting"
    
    print("✅ Rate limiter test passed")


def test_safe_api_call():
    """Test safe API call wrapper"""
    print("Testing safe API call...")
    
    call_count = [0]
    
    def flaky_api():
        call_count[0] += 1
        if call_count[0] < 2:
            raise Exception("API error")
        return {"data": "success"}
    
    result = safe_api_call(flaky_api, max_retries=3)
    
    assert result is not None, "Should return result"
    assert result["data"] == "success", "Should return correct data"
    assert call_count[0] == 2, "Should have retried once"
    
    print("✅ Safe API call test passed")


def test_safe_api_call_failure():
    """Test safe API call with persistent failure"""
    print("Testing safe API call with persistent failure...")
    
    call_count = [0]
    
    def always_fails_api():
        call_count[0] += 1
        raise Exception("API always fails")
    
    result = safe_api_call(always_fails_api, max_retries=2)
    
    assert result is None, "Should return None on persistent failure"
    assert call_count[0] == 3, "Should have tried 3 times (initial + 2 retries)"
    
    print("✅ Safe API call failure test passed")


def test_retry_callback():
    """Test retry callback"""
    print("Testing retry callback...")
    
    retries = []
    
    def on_retry(exception, attempt):
        retries.append((str(exception), attempt))
    
    call_count = [0]
    
    @retry_with_backoff(max_retries=2, base_delay=0.1, on_retry=on_retry)
    def flaky():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError(f"Error {call_count[0]}")
        return "ok"
    
    result = flaky()
    
    assert result == "ok", "Should succeed"
    assert len(retries) == 2, "Should have 2 retries"
    assert retries[0][1] == 1, "First retry should be attempt 1"
    assert retries[1][1] == 2, "Second retry should be attempt 2"
    
    print("✅ Retry callback test passed")


def run_all_tests():
    """Run all error recovery tests"""
    print("=" * 60)
    print("🧪 ERROR RECOVERY TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_exponential_backoff,
        test_retry_decorator,
        test_retry_decorator_failure,
        test_circuit_breaker,
        test_rate_limiter,
        test_safe_api_call,
        test_safe_api_call_failure,
        test_retry_callback,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{len(tests)} passed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
