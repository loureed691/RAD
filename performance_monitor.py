"""
Performance monitoring and profiling utilities for the trading bot
"""
import time
import functools
from typing import Dict, List, Callable
from logger import Logger
from datetime import datetime


class PerformanceMonitor:
    """Monitor and track bot performance metrics"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.metrics = {}
        self.call_counts = {}
        
    def time_function(self, func: Callable) -> Callable:
        """
        Decorator to time function execution
        
        Usage:
            @monitor.time_function
            def my_function():
                pass
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            func_name = func.__name__
            
            # Update metrics
            if func_name not in self.metrics:
                self.metrics[func_name] = {
                    'total_time': 0.0,
                    'call_count': 0,
                    'avg_time': 0.0,
                    'min_time': elapsed,
                    'max_time': elapsed
                }
            
            m = self.metrics[func_name]
            m['total_time'] += elapsed
            m['call_count'] += 1
            m['avg_time'] = m['total_time'] / m['call_count']
            m['min_time'] = min(m['min_time'], elapsed)
            m['max_time'] = max(m['max_time'], elapsed)
            
            # Log slow functions (>5 seconds)
            if elapsed > 5.0:
                self.logger.warning(f"⏱️  Slow function {func_name}: {elapsed:.2f}s")
            
            return result
        
        return wrapper
    
    def get_report(self) -> str:
        """Generate a performance report"""
        if not self.metrics:
            return "No performance data available"
        
        lines = ["=" * 80]
        lines.append("PERFORMANCE REPORT")
        lines.append("=" * 80)
        
        # Sort by total time
        sorted_metrics = sorted(
            self.metrics.items(),
            key=lambda x: x[1]['total_time'],
            reverse=True
        )
        
        for func_name, m in sorted_metrics:
            lines.append(f"\n{func_name}:")
            lines.append(f"  Calls: {m['call_count']}")
            lines.append(f"  Total Time: {m['total_time']:.3f}s")
            lines.append(f"  Avg Time: {m['avg_time']:.3f}s")
            lines.append(f"  Min/Max: {m['min_time']:.3f}s / {m['max_time']:.3f}s")
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    def log_report(self):
        """Log the performance report"""
        self.logger.info(self.get_report())
    
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.call_counts.clear()


class TimingContext:
    """Context manager for timing code blocks"""
    
    def __init__(self, name: str, logger=None):
        self.name = name
        self.logger = logger or Logger.get_logger()
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        if elapsed > 1.0:
            self.logger.debug(f"⏱️  {self.name}: {elapsed:.2f}s")
        return False


# Global performance monitor instance
_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return _monitor


def time_function(func: Callable) -> Callable:
    """Decorator to time function execution (uses global monitor)"""
    return _monitor.time_function(func)
