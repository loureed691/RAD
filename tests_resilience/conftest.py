"""
Shared fixtures for resilience tests
"""
import pytest
from unittest.mock import Mock
import time


@pytest.fixture
def failure_injector():
    """Helper to inject controlled failures"""
    class FailureInjector:
        def __init__(self):
            self.call_count = 0
            self.failure_count = 0
            
        def fail_n_times(self, n, exception_class, message="Test failure"):
            """Fail the first n calls, then succeed"""
            self.call_count += 1
            if self.call_count <= n:
                self.failure_count += 1
                raise exception_class(message)
            return {'success': True}
        
        def reset(self):
            self.call_count = 0
            self.failure_count = 0
    
    return FailureInjector()


@pytest.fixture
def rate_limit_tracker():
    """Track retry timing for rate limit tests"""
    class RateLimitTracker:
        def __init__(self):
            self.attempts = []
            
        def record_attempt(self):
            self.attempts.append(time.time())
            
        def get_delays(self):
            """Get delays between attempts"""
            if len(self.attempts) < 2:
                return []
            return [self.attempts[i] - self.attempts[i-1] 
                    for i in range(1, len(self.attempts))]
        
        def verify_exponential_backoff(self, base_delay=1.0, tolerance=0.3):
            """Verify delays follow exponential backoff pattern"""
            delays = self.get_delays()
            expected_delays = [base_delay * (2 ** i) for i in range(len(delays))]
            
            for actual, expected in zip(delays, expected_delays):
                # Allow for jitter (±20%) plus tolerance
                min_delay = expected * (1 - 0.2 - tolerance)
                max_delay = expected * (1 + 0.2 + tolerance)
                assert min_delay <= actual <= max_delay, \
                    f"Delay {actual:.2f}s not in expected range [{min_delay:.2f}, {max_delay:.2f}]"
    
    return RateLimitTracker()
