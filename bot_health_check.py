"""
Production-Grade Bot Health Check and Diagnostics System

This module provides comprehensive health checks, diagnostics, and
self-healing capabilities for the trading bot.
"""
import time
import threading
import psutil
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import deque
from logger import Logger


class HealthStatus:
    """Health status levels"""
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class PerformanceMonitor:
    """Monitor bot performance metrics"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.scan_times = deque(maxlen=window_size)
        self.api_call_times = deque(maxlen=window_size)
        self.memory_usage = deque(maxlen=window_size)
        self.error_count = 0
        self.warning_count = 0
        self.last_error_time = None
        self.logger = Logger.get_logger()
        self._lock = threading.Lock()
        
    def record_scan_time(self, duration: float):
        """Record a market scan duration"""
        with self._lock:
            self.scan_times.append(duration)
    
    def record_api_call(self, duration: float):
        """Record an API call duration"""
        with self._lock:
            self.api_call_times.append(duration)
    
    def record_error(self):
        """Record an error occurrence"""
        with self._lock:
            self.error_count += 1
            self.last_error_time = datetime.now()
    
    def record_warning(self):
        """Record a warning occurrence"""
        with self._lock:
            self.warning_count += 1
    
    def update_memory_usage(self):
        """Update current memory usage"""
        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            with self._lock:
                self.memory_usage.append(memory_mb)
        except Exception as e:
            self.logger.debug(f"Could not get memory usage: {e}")
    
    def get_metrics(self) -> Dict:
        """Get current performance metrics"""
        with self._lock:
            metrics = {
                'avg_scan_time': sum(self.scan_times) / len(self.scan_times) if self.scan_times else 0,
                'max_scan_time': max(self.scan_times) if self.scan_times else 0,
                'min_scan_time': min(self.scan_times) if self.scan_times else 0,
                'avg_api_call_time': sum(self.api_call_times) / len(self.api_call_times) if self.api_call_times else 0,
                'avg_memory_mb': sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
                'current_memory_mb': self.memory_usage[-1] if self.memory_usage else 0,
                'error_count': self.error_count,
                'warning_count': self.warning_count,
                'last_error_time': self.last_error_time
            }
        return metrics


class BotHealthCheck:
    """
    Comprehensive bot health monitoring and diagnostics
    
    This class provides health checks for all bot components including:
    - Scan performance monitoring
    - Memory usage tracking
    - Error rate analysis
    - API performance monitoring
    
    Attributes:
        performance_monitor: PerformanceMonitor instance for metric tracking
        health_history: Deque of historical health reports (max 100 entries)
        max_scan_time: Maximum acceptable scan time in seconds (default: 30.0)
        max_memory_mb: Maximum acceptable memory usage in MB (default: 1024)
        max_error_rate: Maximum acceptable error rate as decimal (default: 0.05)
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.performance_monitor = PerformanceMonitor()
        self.last_health_check = datetime.now()
        self.health_history = deque(maxlen=100)
        self._lock = threading.Lock()
        
        # Thresholds
        self.max_scan_time = 30.0  # seconds
        self.max_memory_mb = 1024  # MB
        self.max_error_rate = 0.05  # 5% error rate
        
    def check_scan_performance(self, metrics: Dict) -> Tuple[str, str]:
        """
        Check if market scanning performance is acceptable
        
        Returns:
            Tuple of (status, message)
        """
        avg_scan_time = metrics.get('avg_scan_time', 0)
        max_scan_time = metrics.get('max_scan_time', 0)
        
        if max_scan_time > self.max_scan_time * 3:
            return (
                HealthStatus.CRITICAL,
                f"Scan time critically slow: max={max_scan_time:.1f}s (threshold={self.max_scan_time*3}s)"
            )
        elif avg_scan_time > self.max_scan_time:
            return (
                HealthStatus.WARNING,
                f"Scan time above threshold: avg={avg_scan_time:.1f}s (threshold={self.max_scan_time}s)"
            )
        else:
            return (
                HealthStatus.HEALTHY,
                f"Scan performance good: avg={avg_scan_time:.1f}s"
            )
    
    def check_memory_usage(self, metrics: Dict) -> Tuple[str, str]:
        """
        Check if memory usage is acceptable
        
        Returns:
            Tuple of (status, message)
        """
        current_memory = metrics.get('current_memory_mb', 0)
        avg_memory = metrics.get('avg_memory_mb', 0)
        
        if current_memory > self.max_memory_mb:
            return (
                HealthStatus.CRITICAL,
                f"Memory usage critical: {current_memory:.1f}MB (threshold={self.max_memory_mb}MB)"
            )
        elif current_memory > self.max_memory_mb * 0.8:
            return (
                HealthStatus.WARNING,
                f"Memory usage high: {current_memory:.1f}MB (threshold={self.max_memory_mb}MB)"
            )
        else:
            return (
                HealthStatus.HEALTHY,
                f"Memory usage normal: {current_memory:.1f}MB"
            )
    
    def check_error_rate(self, metrics: Dict) -> Tuple[str, str]:
        """
        Check if error rate is acceptable
        
        Returns:
            Tuple of (status, message)
        """
        error_count = metrics.get('error_count', 0)
        warning_count = metrics.get('warning_count', 0)
        last_error_time = metrics.get('last_error_time')
        
        # Check recent error rate
        if last_error_time:
            time_since_error = (datetime.now() - last_error_time).total_seconds()
            if time_since_error < 60:  # Error in last minute
                return (
                    HealthStatus.WARNING,
                    f"Recent error detected ({time_since_error:.0f}s ago)"
                )
        
        if error_count > 10:
            return (
                HealthStatus.CRITICAL,
                f"High error count: {error_count} errors"
            )
        elif error_count > 5:
            return (
                HealthStatus.WARNING,
                f"Elevated error count: {error_count} errors"
            )
        else:
            return (
                HealthStatus.HEALTHY,
                f"Error rate normal: {error_count} errors"
            )
    
    def check_api_performance(self, metrics: Dict) -> Tuple[str, str]:
        """
        Check if API call performance is acceptable
        
        Returns:
            Tuple of (status, message)
        """
        avg_api_time = metrics.get('avg_api_call_time', 0)
        
        if avg_api_time > 5.0:
            return (
                HealthStatus.CRITICAL,
                f"API calls critically slow: avg={avg_api_time:.2f}s"
            )
        elif avg_api_time > 2.0:
            return (
                HealthStatus.WARNING,
                f"API calls slower than expected: avg={avg_api_time:.2f}s"
            )
        else:
            return (
                HealthStatus.HEALTHY,
                f"API performance good: avg={avg_api_time:.2f}s"
            )
    
    def run_full_health_check(self) -> Dict:
        """
        Run a comprehensive health check
        
        Returns:
            Dict with health status and details
        """
        with self._lock:
            self.last_health_check = datetime.now()
            
            # Update memory before checking
            self.performance_monitor.update_memory_usage()
            
            # Get current metrics
            metrics = self.performance_monitor.get_metrics()
            
            # Run all checks
            checks = {
                'scan_performance': self.check_scan_performance(metrics),
                'memory_usage': self.check_memory_usage(metrics),
                'error_rate': self.check_error_rate(metrics),
                'api_performance': self.check_api_performance(metrics)
            }
            
            # Determine overall health status based on component statuses
            statuses = [check[0] for check in checks.values()]
            
            # Priority: CRITICAL > WARNING > HEALTHY
            if HealthStatus.CRITICAL in statuses:
                overall_status = HealthStatus.CRITICAL
            elif HealthStatus.WARNING in statuses:
                overall_status = HealthStatus.WARNING
            else:
                overall_status = HealthStatus.HEALTHY
            
            health_report = {
                'timestamp': self.last_health_check,
                'overall_status': overall_status,
                'checks': checks,
                'metrics': metrics
            }
            
            # Store in history
            self.health_history.append(health_report)
            
            return health_report
    
    def get_health_summary(self) -> str:
        """Get a human-readable health summary"""
        report = self.run_full_health_check()
        
        lines = [
            "=" * 60,
            "BOT HEALTH CHECK SUMMARY",
            "=" * 60,
            f"Timestamp: {report['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
            f"Overall Status: {report['overall_status']}",
            "",
            "Component Health:",
            "-" * 60
        ]
        
        for component, (status, message) in report['checks'].items():
            status_icon = "✅" if status == HealthStatus.HEALTHY else "⚠️" if status == HealthStatus.WARNING else "❌"
            lines.append(f"{status_icon} {component}: {status}")
            lines.append(f"   {message}")
        
        lines.extend([
            "",
            "Key Metrics:",
            "-" * 60
        ])
        
        metrics = report['metrics']
        lines.append(f"  Avg Scan Time: {metrics['avg_scan_time']:.2f}s")
        lines.append(f"  Memory Usage: {metrics['current_memory_mb']:.1f}MB")
        lines.append(f"  Errors: {metrics['error_count']}")
        lines.append(f"  Warnings: {metrics['warning_count']}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def log_health_status(self):
        """Log current health status"""
        summary = self.get_health_summary()
        self.logger.info(f"\n{summary}")


# Global instance
_health_check_instance = None
_health_check_lock = threading.Lock()


def get_health_check() -> BotHealthCheck:
    """Get or create the global health check instance"""
    global _health_check_instance
    
    if _health_check_instance is None:
        with _health_check_lock:
            if _health_check_instance is None:
                _health_check_instance = BotHealthCheck()
    
    return _health_check_instance
