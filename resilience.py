"""
Resilience utilities for the trading bot
Provides retry logic, circuit breaker, and error handling
"""
import time
import functools
from typing import Callable, Any, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger


class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds before attempting to close circuit again
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = Logger.get_logger()
    
    def call(self, func: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """
        Execute function through circuit breaker
        
        Returns:
            Tuple of (success: bool, result: Any)
        """
        if self.state == "OPEN":
            # Check if timeout has passed
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.logger.info(f"Circuit breaker transitioning to HALF_OPEN")
                self.state = "HALF_OPEN"
            else:
                self.logger.warning(f"Circuit breaker is OPEN, rejecting call to {func.__name__}")
                return False, None
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset or close circuit
            if self.state == "HALF_OPEN":
                self.logger.info(f"Circuit breaker transitioning to CLOSED")
                self.state = "CLOSED"
                self.failure_count = 0
            
            return True, result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                if self.state != "OPEN":
                    self.logger.error(
                        f"Circuit breaker opening after {self.failure_count} failures. "
                        f"Will retry in {self.timeout} seconds"
                    )
                self.state = "OPEN"
            
            return False, None


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: Tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = Logger.get_logger()
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(initial_delay * (exponential_base ** attempt), max_delay)
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            
            return None
        
        return wrapper
    return decorator


def timeout_protection(timeout_seconds: int = 120):
    """
    Decorator to add timeout protection to long-running functions
    Note: This uses a simple time-based check, not true thread interruption
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = Logger.get_logger()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                
                if elapsed > timeout_seconds:
                    logger.warning(
                        f"{func.__name__} took {elapsed:.1f}s (exceeded timeout of {timeout_seconds}s)"
                    )
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {elapsed:.1f}s: {e}"
                )
                raise
        
        return wrapper
    return decorator


class RateLimiter:
    """Simple rate limiter to prevent API abuse"""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.logger = Logger.get_logger()
    
    def can_call(self) -> bool:
        """Check if call is allowed"""
        now = time.time()
        
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls 
                      if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            wait_time = self.time_window - (now - self.calls[0])
            self.logger.warning(
                f"Rate limit reached ({self.max_calls} calls/{self.time_window}s). "
                f"Wait {wait_time:.1f}s"
            )
            return False
        
        return True
    
    def record_call(self):
        """Record a call"""
        self.calls.append(time.time())
    
    def wait_if_needed(self):
        """Wait if rate limit is reached"""
        while not self.can_call():
            time.sleep(1)
        self.record_call()


class PerformanceMonitor:
    """Monitor performance metrics of operations"""
    
    def __init__(self):
        self.metrics = {}
        self.logger = Logger.get_logger()
    
    def record(self, operation: str, duration: float, success: bool):
        """Record operation metrics"""
        if operation not in self.metrics:
            self.metrics[operation] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0
            }
        
        metrics = self.metrics[operation]
        metrics['total_calls'] += 1
        
        if success:
            metrics['successful_calls'] += 1
        else:
            metrics['failed_calls'] += 1
        
        metrics['total_duration'] += duration
        metrics['min_duration'] = min(metrics['min_duration'], duration)
        metrics['max_duration'] = max(metrics['max_duration'], duration)
    
    def get_summary(self, operation: str = None) -> str:
        """Get performance summary"""
        if operation and operation in self.metrics:
            m = self.metrics[operation]
            avg_duration = m['total_duration'] / m['total_calls'] if m['total_calls'] > 0 else 0
            success_rate = m['successful_calls'] / m['total_calls'] if m['total_calls'] > 0 else 0
            
            return (
                f"{operation}: "
                f"{m['total_calls']} calls, "
                f"{success_rate:.1%} success rate, "
                f"avg {avg_duration:.2f}s, "
                f"min {m['min_duration']:.2f}s, "
                f"max {m['max_duration']:.2f}s"
            )
        
        # Return summary for all operations
        summaries = []
        for op in sorted(self.metrics.keys()):
            summaries.append(self.get_summary(op))
        
        return "\n".join(summaries) if summaries else "No metrics recorded"


def monitored_call(monitor: PerformanceMonitor, operation_name: str):
    """Decorator to monitor function calls"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                raise
            finally:
                duration = time.time() - start_time
                monitor.record(operation_name, duration, success)
        
        return wrapper
    return decorator
