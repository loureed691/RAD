"""
Test suite for resilience module
"""
import time
import unittest
from resilience import (
    CircuitBreaker, 
    retry_with_backoff, 
    RateLimiter, 
    PerformanceMonitor
)


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker functionality"""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker starts in CLOSED state"""
        cb = CircuitBreaker(failure_threshold=3, timeout=5)
        self.assertEqual(cb.state, "CLOSED")
        
        # Successful call should keep it closed
        success, result = cb.call(lambda: "success")
        self.assertTrue(success)
        self.assertEqual(result, "success")
        self.assertEqual(cb.state, "CLOSED")
    
    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = CircuitBreaker(failure_threshold=3, timeout=5)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Fail 3 times to reach threshold
        for _ in range(3):
            success, result = cb.call(failing_func)
            self.assertFalse(success)
            self.assertIsNone(result)
        
        # Circuit should be open now
        self.assertEqual(cb.state, "OPEN")
        
        # Next call should be rejected immediately
        success, result = cb.call(lambda: "success")
        self.assertFalse(success)
        self.assertIsNone(result)
    
    def test_circuit_breaker_half_open(self):
        """Test circuit breaker transitions to HALF_OPEN"""
        cb = CircuitBreaker(failure_threshold=2, timeout=1)
        
        def failing_func():
            raise Exception("Test failure")
        
        # Open the circuit
        for _ in range(2):
            cb.call(failing_func)
        
        self.assertEqual(cb.state, "OPEN")
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Next successful call should transition to HALF_OPEN then CLOSED
        success, result = cb.call(lambda: "success")
        self.assertTrue(success)
        self.assertEqual(cb.state, "CLOSED")


class TestRetryWithBackoff(unittest.TestCase):
    """Test retry with exponential backoff"""
    
    def test_retry_success_first_attempt(self):
        """Test successful call on first attempt"""
        call_count = [0]
        
        @retry_with_backoff(max_retries=3)
        def success_func():
            call_count[0] += 1
            return "success"
        
        result = success_func()
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 1)
    
    def test_retry_success_after_failures(self):
        """Test successful call after some failures"""
        call_count = [0]
        
        @retry_with_backoff(max_retries=3, initial_delay=0.1)
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = flaky_func()
        self.assertEqual(result, "success")
        self.assertEqual(call_count[0], 3)
    
    def test_retry_max_retries_exceeded(self):
        """Test failure after max retries"""
        call_count = [0]
        
        @retry_with_backoff(max_retries=2, initial_delay=0.1)
        def always_fail():
            call_count[0] += 1
            raise ValueError("Permanent failure")
        
        with self.assertRaises(ValueError):
            always_fail()
        
        self.assertEqual(call_count[0], 3)  # Initial + 2 retries


class TestRateLimiter(unittest.TestCase):
    """Test rate limiter functionality"""
    
    def test_rate_limiter_allows_within_limit(self):
        """Test rate limiter allows calls within limit"""
        limiter = RateLimiter(max_calls=5, time_window=1)
        
        for _ in range(5):
            self.assertTrue(limiter.can_call())
            limiter.record_call()
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test rate limiter blocks calls over limit"""
        limiter = RateLimiter(max_calls=3, time_window=1)
        
        # Use up the limit
        for _ in range(3):
            limiter.record_call()
        
        # Next call should be blocked
        self.assertFalse(limiter.can_call())
    
    def test_rate_limiter_resets_after_window(self):
        """Test rate limiter resets after time window"""
        limiter = RateLimiter(max_calls=2, time_window=1)
        
        # Use up the limit
        limiter.record_call()
        limiter.record_call()
        self.assertFalse(limiter.can_call())
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be able to call again
        self.assertTrue(limiter.can_call())


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring"""
    
    def test_performance_monitor_records_metrics(self):
        """Test performance monitor records metrics correctly"""
        monitor = PerformanceMonitor()
        
        monitor.record('test_op', 1.0, True)
        monitor.record('test_op', 2.0, True)
        monitor.record('test_op', 0.5, False)
        
        metrics = monitor.metrics['test_op']
        self.assertEqual(metrics['total_calls'], 3)
        self.assertEqual(metrics['successful_calls'], 2)
        self.assertEqual(metrics['failed_calls'], 1)
        self.assertEqual(metrics['min_duration'], 0.5)
        self.assertEqual(metrics['max_duration'], 2.0)
    
    def test_performance_monitor_summary(self):
        """Test performance monitor generates summary"""
        monitor = PerformanceMonitor()
        
        monitor.record('api_call', 1.5, True)
        monitor.record('api_call', 2.0, True)
        
        summary = monitor.get_summary('api_call')
        self.assertIn('api_call', summary)
        self.assertIn('2 calls', summary)
        self.assertIn('100.0% success rate', summary)


def run_tests():
    """Run all tests"""
    print("=" * 70)
    print("RESILIENCE MODULE TEST SUITE")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCircuitBreaker))
    suite.addTests(loader.loadTestsFromTestCase(TestRetryWithBackoff))
    suite.addTests(loader.loadTestsFromTestCase(TestRateLimiter))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceMonitor))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
