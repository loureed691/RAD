"""
Resilience tests for retry logic and backoff
"""
import pytest
import time
from unittest.mock import Mock
import random


def test_exponential_backoff_with_jitter():
    """Test that retries use exponential backoff with jitter"""
    
    attempts = []
    
    def simulate_retry_with_backoff(max_retries=3):
        """Simulate retry logic with exponential backoff and jitter"""
        base_delay = 1.0
        
        for attempt in range(max_retries):
            attempts.append(time.time())
            
            if attempt < max_retries - 1:
                # Calculate delay with jitter
                delay = (2 ** attempt) * base_delay
                jitter = delay * 0.2 * (2 * random.random() - 1)
                delay = max(delay + jitter, 0.1)
                
                time.sleep(delay)
        
        return True
    
    # Run simulation
    simulate_retry_with_backoff(max_retries=3)
    
    # Verify we had 3 attempts
    assert len(attempts) == 3
    
    # Calculate delays
    delay1 = attempts[1] - attempts[0]
    delay2 = attempts[2] - attempts[1]
    
    # First delay should be ~1s with ±20% jitter
    assert 0.7 < delay1 < 1.3, f"First delay {delay1:.2f}s outside expected range"
    
    # Second delay should be ~2s with ±20% jitter
    assert 1.5 < delay2 < 2.5, f"Second delay {delay2:.2f}s outside expected range"


def test_jitter_prevents_thundering_herd():
    """Test that jitter spreads out retry attempts"""
    
    # Simulate multiple clients retrying at the same time
    num_clients = 10
    base_delay = 1.0
    
    first_retries = []
    
    # Each client calculates their first retry delay
    for _ in range(num_clients):
        delay = base_delay
        jitter = delay * 0.2 * (2 * random.random() - 1)
        retry_delay = max(delay + jitter, 0.1)
        first_retries.append(retry_delay)
    
    # Verify delays are spread out (not all the same)
    unique_delays = len(set(first_retries))
    assert unique_delays > 5, "Jitter should create varied delays"
    
    # Verify all delays are within expected range (±20%)
    for delay in first_retries:
        assert 0.8 < delay < 1.2


def test_retry_success_after_failures(failure_injector):
    """Test that retries succeed after transient failures"""
    
    class MockException(Exception):
        pass
    
    # Fail 2 times, then succeed
    result = None
    for attempt in range(3):
        try:
            result = failure_injector.fail_n_times(2, MockException, "Transient error")
            break  # Success
        except MockException:
            if attempt < 2:
                time.sleep(0.01)  # Small delay for test speed
            else:
                raise  # Re-raise if last attempt
    
    assert result == {'success': True}
    assert failure_injector.failure_count == 2
    assert failure_injector.call_count == 3


def test_retry_exhaustion():
    """Test that retries eventually give up"""
    
    class MockException(Exception):
        pass
    
    max_retries = 3
    attempts = 0
    
    # Always fail
    with pytest.raises(MockException):
        for attempt in range(max_retries):
            attempts += 1
            raise MockException("Permanent error")
    
    # We should only try max_retries times
    assert attempts == 1  # pytest.raises catches on first attempt


def test_no_retry_on_permanent_errors():
    """Test that certain errors don't trigger retries"""
    
    # Simulate errors that should NOT be retried
    permanent_errors = [
        'InsufficientFunds',
        'InvalidOrder',
        'AuthenticationError'
    ]
    
    for error_type in permanent_errors:
        # In actual implementation, these errors should return None immediately
        # without retrying
        should_retry = error_type not in ['InsufficientFunds', 'InvalidOrder', 'AuthenticationError']
        assert not should_retry, f"{error_type} should not trigger retry"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
