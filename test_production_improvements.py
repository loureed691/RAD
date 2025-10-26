"""
Test suite for production-grade bot improvements

Tests health monitoring, error recovery, and self-healing capabilities.
"""
import pytest
import time
from bot_health_check import (
    get_health_check, BotHealthCheck, HealthStatus, PerformanceMonitor
)
from error_recovery import (
    get_error_manager, ErrorRecoveryManager, ErrorSeverity,
    RecoveryAction, RetryWithBackoff
)


class TestHealthCheck:
    """Test health monitoring system"""
    
    def test_health_check_singleton(self):
        """Test that get_health_check returns singleton"""
        hc1 = get_health_check()
        hc2 = get_health_check()
        assert hc1 is hc2, "Health check should be singleton"
    
    def test_performance_monitor_recording(self):
        """Test performance metric recording"""
        monitor = PerformanceMonitor(window_size=10)
        
        # Record some metrics
        monitor.record_scan_time(25.5)
        monitor.record_scan_time(30.2)
        monitor.record_api_call(1.5)
        monitor.record_error()
        monitor.record_warning()
        
        metrics = monitor.get_metrics()
        assert metrics['avg_scan_time'] > 0
        assert metrics['max_scan_time'] >= metrics['avg_scan_time']
        assert metrics['error_count'] == 1
        assert metrics['warning_count'] == 1
    
    def test_scan_performance_check(self):
        """Test scan performance health check"""
        health_check = BotHealthCheck()
        
        # Good performance
        metrics = {'avg_scan_time': 15.0, 'max_scan_time': 20.0}
        status, message = health_check.check_scan_performance(metrics)
        assert status == HealthStatus.HEALTHY
        
        # Warning level
        metrics = {'avg_scan_time': 35.0, 'max_scan_time': 45.0}
        status, message = health_check.check_scan_performance(metrics)
        assert status == HealthStatus.WARNING
        
        # Critical level
        metrics = {'avg_scan_time': 50.0, 'max_scan_time': 95.0}
        status, message = health_check.check_scan_performance(metrics)
        assert status == HealthStatus.CRITICAL
    
    def test_memory_usage_check(self):
        """Test memory usage health check"""
        health_check = BotHealthCheck()
        
        # Good memory usage
        metrics = {'current_memory_mb': 200.0, 'avg_memory_mb': 180.0}
        status, message = health_check.check_memory_usage(metrics)
        assert status == HealthStatus.HEALTHY
        
        # Warning level
        metrics = {'current_memory_mb': 900.0, 'avg_memory_mb': 850.0}
        status, message = health_check.check_memory_usage(metrics)
        assert status == HealthStatus.WARNING
        
        # Critical level
        metrics = {'current_memory_mb': 1100.0, 'avg_memory_mb': 1050.0}
        status, message = health_check.check_memory_usage(metrics)
        assert status == HealthStatus.CRITICAL
    
    def test_full_health_check(self):
        """Test comprehensive health check"""
        health_check = get_health_check()
        
        # Record some metrics
        health_check.performance_monitor.record_scan_time(20.0)
        health_check.performance_monitor.record_api_call(1.0)
        
        # Run health check
        report = health_check.run_full_health_check()
        
        assert 'timestamp' in report
        assert 'overall_status' in report
        assert 'checks' in report
        assert 'metrics' in report
        assert report['overall_status'] in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.CRITICAL]


class TestErrorRecovery:
    """Test error recovery system"""
    
    def test_error_manager_singleton(self):
        """Test that get_error_manager returns singleton"""
        em1 = get_error_manager()
        em2 = get_error_manager()
        assert em1 is em2, "Error manager should be singleton"
    
    def test_error_recording(self):
        """Test error recording"""
        manager = ErrorRecoveryManager()
        
        error = manager.record_error(
            'test_error',
            'Test message',
            ErrorSeverity.MEDIUM,
            {'context': 'test'}
        )
        
        assert error.error_type == 'test_error'
        assert error.message == 'Test message'
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.context['context'] == 'test'
    
    def test_recovery_strategy_registration(self):
        """Test recovery strategy registration"""
        manager = ErrorRecoveryManager()
        
        manager.register_recovery_strategy(
            'custom_error',
            ErrorSeverity.HIGH,
            RecoveryAction.RETRY,
            max_retries=5
        )
        
        assert 'custom_error' in manager.recovery_strategies
        strategy = manager.recovery_strategies['custom_error']
        assert strategy['severity'] == ErrorSeverity.HIGH
        assert strategy['action'] == RecoveryAction.RETRY
        assert strategy['params']['max_retries'] == 5
    
    def test_should_trigger_recovery(self):
        """Test recovery trigger logic"""
        manager = ErrorRecoveryManager()
        
        # Record multiple errors
        for _ in range(3):
            manager.record_error('repeated_error', 'Test', ErrorSeverity.MEDIUM)
        
        # Should trigger recovery after 3 errors
        assert manager.should_trigger_recovery('repeated_error', time_window=60)
        
        # Should not trigger for non-existent error
        assert not manager.should_trigger_recovery('nonexistent_error', time_window=60)
    
    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        manager = ErrorRecoveryManager()
        
        # Circuit should be closed initially
        assert not manager.is_circuit_breaker_open('test_component')
        
        # Open circuit breaker
        manager.open_circuit_breaker('test_component')
        assert manager.is_circuit_breaker_open('test_component')
        
        # Close circuit breaker
        manager.close_circuit_breaker('test_component')
        assert not manager.is_circuit_breaker_open('test_component')
    
    def test_error_statistics(self):
        """Test error statistics generation"""
        manager = ErrorRecoveryManager()
        
        # Record various errors
        manager.record_error('error1', 'Test 1', ErrorSeverity.LOW)
        manager.record_error('error1', 'Test 2', ErrorSeverity.LOW)
        manager.record_error('error2', 'Test 3', ErrorSeverity.HIGH)
        
        stats = manager.get_error_statistics()
        
        assert stats['total_errors'] == 3
        assert stats['errors_by_type']['error1'] == 2
        assert stats['errors_by_type']['error2'] == 1
        assert stats['errors_by_severity']['LOW'] == 2
        assert stats['errors_by_severity']['HIGH'] == 1
    
    def test_retry_decorator_success(self):
        """Test retry decorator on successful function"""
        manager = ErrorRecoveryManager()
        retry = RetryWithBackoff(max_retries=3, backoff_base=1.5, error_manager=manager)
        
        call_count = [0]
        
        @retry
        def test_function():
            call_count[0] += 1
            return "success"
        
        result = test_function()
        assert result == "success"
        assert call_count[0] == 1
    
    def test_retry_decorator_eventual_success(self):
        """Test retry decorator on function that succeeds after failures"""
        manager = ErrorRecoveryManager()
        retry = RetryWithBackoff(max_retries=3, backoff_base=1.1, error_manager=manager)
        
        call_count = [0]
        
        @retry
        def test_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = test_function()
        assert result == "success"
        assert call_count[0] == 2  # Failed once, succeeded on second attempt


class TestIntegration:
    """Integration tests for production improvements"""
    
    def test_health_and_error_integration(self):
        """Test health check and error recovery work together"""
        health_check = get_health_check()
        error_manager = get_error_manager()
        
        # Simulate slow scans
        for _ in range(3):
            health_check.performance_monitor.record_scan_time(35.0)
        
        # Run health check
        report = health_check.run_full_health_check()
        
        # If health is not good, error should be recorded
        if report['overall_status'] != HealthStatus.HEALTHY:
            error_manager.record_error(
                'health_degradation',
                'System health degraded',
                ErrorSeverity.MEDIUM
            )
        
        # Verify error was recorded
        stats = error_manager.get_error_statistics()
        assert stats['total_errors'] >= 1
    
    def test_performance_tracking(self):
        """Test that performance is tracked over time"""
        health_check = get_health_check()
        monitor = health_check.performance_monitor
        
        # Simulate multiple scans
        for i in range(10):
            monitor.record_scan_time(20.0 + i)
            monitor.record_api_call(0.5 + i * 0.1)
        
        metrics = monitor.get_metrics()
        assert metrics['avg_scan_time'] > 20.0
        assert metrics['max_scan_time'] >= metrics['avg_scan_time']
        assert metrics['min_scan_time'] <= metrics['avg_scan_time']
        assert metrics['avg_api_call_time'] > 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
