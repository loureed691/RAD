"""
Error recovery utilities with exponential backoff
"""
import time
import functools
from typing import Callable, Any, Optional, Tuple, Type
from datetime import datetime, timedelta


class ExponentialBackoff:
    """Implements exponential backoff for error recovery"""
    
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        max_retries: int = 5,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize exponential backoff
        
        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            max_retries: Maximum number of retry attempts
            exponential_base: Base for exponential calculation (default: 2.0)
            jitter: Whether to add random jitter to prevent thundering herd
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.attempt = 0
    
    def get_delay(self) -> float:
        """Calculate delay for current attempt"""
        import random
        
        # Calculate exponential delay
        delay = min(
            self.base_delay * (self.exponential_base ** self.attempt),
            self.max_delay
        )
        
        # Add jitter (±25% randomness)
        if self.jitter:
            jitter_amount = delay * 0.25
            delay = delay + random.uniform(-jitter_amount, jitter_amount)
            delay = max(0.1, delay)  # Ensure minimum delay
        
        return delay
    
    def should_retry(self) -> bool:
        """Check if should retry"""
        return self.attempt < self.max_retries
    
    def reset(self):
        """Reset the backoff counter"""
        self.attempt = 0
    
    def sleep(self):
        """Sleep for the calculated delay and increment attempt counter"""
        if self.should_retry():
            delay = self.get_delay()
            time.sleep(delay)
            self.attempt += 1
            return True
        return False


def retry_with_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry with (exception, attempt)
    
    Example:
        @retry_with_backoff(max_retries=3, base_delay=2.0)
        def fetch_data():
            # Network call that might fail
            return api.get_data()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            backoff = ExponentialBackoff(
                base_delay=base_delay,
                max_delay=max_delay,
                max_retries=max_retries
            )
            
            last_exception = None
            
            while True:
                try:
                    result = func(*args, **kwargs)
                    # Success - reset backoff for next time
                    backoff.reset()
                    return result
                
                except exceptions as e:
                    last_exception = e
                    
                    if not backoff.should_retry():
                        # Max retries reached
                        raise
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, backoff.attempt + 1)
                    
                    # Sleep with exponential backoff
                    delay = backoff.get_delay()
                    time.sleep(delay)
                    backoff.attempt += 1
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing cascading failures
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold exceeded, all requests fail fast
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        
        # Check if we should attempt recovery
        if self.state == 'OPEN':
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception(f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}")
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset failure count and close circuit
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
            self.failure_count = 0
            
            return result
        
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            # Check if we've exceeded failure threshold
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            
            raise
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.failure_count = 0
        self.state = 'CLOSED'
        self.last_failure_time = None
    
    def get_state(self) -> dict:
        """Get current state of circuit breaker"""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time,
            'threshold': self.failure_threshold
        }


class RateLimiter:
    """Rate limiter with token bucket algorithm"""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_proceed(self) -> Tuple[bool, Optional[float]]:
        """
        Check if can proceed with operation
        
        Returns:
            Tuple of (can_proceed, wait_time)
            - can_proceed: True if operation can proceed
            - wait_time: Seconds to wait if cannot proceed (None if can proceed)
        """
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [t for t in self.calls if now - t < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True, None
        else:
            # Calculate wait time
            oldest_call = min(self.calls)
            wait_time = self.time_window - (now - oldest_call)
            return False, wait_time
    
    def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        can_proceed, wait_time = self.can_proceed()
        
        if not can_proceed and wait_time:
            time.sleep(wait_time)
            # Try again after waiting
            self.calls.append(time.time())


def safe_api_call(
    func: Callable,
    *args,
    max_retries: int = 3,
    on_error: Optional[Callable[[Exception], None]] = None,
    **kwargs
) -> Optional[Any]:
    """
    Safely execute an API call with retries and error handling
    
    Args:
        func: Function to call
        *args: Positional arguments for function
        max_retries: Maximum number of retry attempts
        on_error: Optional callback for error handling
        **kwargs: Keyword arguments for function
    
    Returns:
        Result of function call, or None if all retries failed
    """
    backoff = ExponentialBackoff(max_retries=max_retries)
    
    attempt = 0
    while attempt <= max_retries:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if on_error:
                on_error(e)
            
            attempt += 1
            if attempt <= max_retries:
                backoff.sleep()
    
    return None
