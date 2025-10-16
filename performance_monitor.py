"""
Performance monitoring and metrics collection for the trading bot

This module provides real-time performance monitoring to identify bottlenecks
and ensure the bot operates within acceptable performance parameters.
"""
import time
import threading
from collections import deque
from datetime import datetime
from typing import Dict, Optional
from logger import Logger


class PerformanceMonitor:
    """
    Monitor bot performance metrics in real-time
    
    PERFORMANCE: Tracks execution times, API call latency, and system health
    RELIABILITY: Detects performance degradation and potential issues
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        
        # Timing metrics (use deque for efficient O(1) append/popleft)
        self._scan_times = deque(maxlen=100)  # Last 100 scans
        self._trade_execution_times = deque(maxlen=50)  # Last 50 trades
        self._api_call_times = deque(maxlen=200)  # Last 200 API calls
        self._position_update_times = deque(maxlen=100)  # Last 100 position updates
        
        # API call tracking
        self._api_call_count = 0
        self._api_error_count = 0
        self._api_retry_count = 0
        self._last_api_reset = time.time()
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Performance thresholds (in seconds)
        self.SCAN_THRESHOLD = 30.0  # Warn if scan takes > 30s
        self.TRADE_THRESHOLD = 5.0   # Warn if trade execution takes > 5s
        self.API_THRESHOLD = 2.0     # Warn if API call takes > 2s
        self.UPDATE_THRESHOLD = 1.0  # Warn if position update takes > 1s
    
    def record_scan_time(self, duration: float):
        """Record market scan duration"""
        with self._lock:
            self._scan_times.append(duration)
            
        if duration > self.SCAN_THRESHOLD:
            self.logger.warning(f"⚠️  SLOW SCAN: {duration:.2f}s (threshold: {self.SCAN_THRESHOLD}s)")
    
    def record_trade_execution(self, duration: float):
        """Record trade execution duration"""
        with self._lock:
            self._trade_execution_times.append(duration)
            
        if duration > self.TRADE_THRESHOLD:
            self.logger.warning(f"⚠️  SLOW TRADE EXECUTION: {duration:.2f}s (threshold: {self.TRADE_THRESHOLD}s)")
    
    def record_api_call(self, duration: float, success: bool = True, retried: bool = False):
        """Record API call metrics"""
        with self._lock:
            self._api_call_times.append(duration)
            self._api_call_count += 1
            
            if not success:
                self._api_error_count += 1
            if retried:
                self._api_retry_count += 1
            
        if duration > self.API_THRESHOLD:
            self.logger.debug(f"Slow API call: {duration:.2f}s")
    
    def record_position_update(self, duration: float):
        """Record position update duration"""
        with self._lock:
            self._position_update_times.append(duration)
            
        if duration > self.UPDATE_THRESHOLD:
            self.logger.debug(f"Slow position update: {duration:.2f}s")
    
    def get_stats(self) -> Dict:
        """
        Get current performance statistics
        
        Returns:
            Dict with performance metrics
        """
        with self._lock:
            # Calculate averages
            avg_scan_time = sum(self._scan_times) / len(self._scan_times) if self._scan_times else 0
            avg_trade_time = sum(self._trade_execution_times) / len(self._trade_execution_times) if self._trade_execution_times else 0
            avg_api_time = sum(self._api_call_times) / len(self._api_call_times) if self._api_call_times else 0
            avg_update_time = sum(self._position_update_times) / len(self._position_update_times) if self._position_update_times else 0
            
            # Calculate API error rate
            time_since_reset = time.time() - self._last_api_reset
            api_calls_per_minute = (self._api_call_count / time_since_reset) * 60 if time_since_reset > 0 else 0
            api_error_rate = (self._api_error_count / self._api_call_count) if self._api_call_count > 0 else 0
            api_retry_rate = (self._api_retry_count / self._api_call_count) if self._api_call_count > 0 else 0
            
            return {
                'scan': {
                    'avg_time': avg_scan_time,
                    'samples': len(self._scan_times),
                    'last_time': self._scan_times[-1] if self._scan_times else None
                },
                'trade_execution': {
                    'avg_time': avg_trade_time,
                    'samples': len(self._trade_execution_times),
                    'last_time': self._trade_execution_times[-1] if self._trade_execution_times else None
                },
                'api': {
                    'avg_time': avg_api_time,
                    'samples': len(self._api_call_times),
                    'total_calls': self._api_call_count,
                    'calls_per_minute': api_calls_per_minute,
                    'error_rate': api_error_rate,
                    'retry_rate': api_retry_rate,
                    'errors': self._api_error_count,
                    'retries': self._api_retry_count
                },
                'position_update': {
                    'avg_time': avg_update_time,
                    'samples': len(self._position_update_times),
                    'last_time': self._position_update_times[-1] if self._position_update_times else None
                }
            }
    
    def print_summary(self):
        """Print a summary of performance metrics"""
        stats = self.get_stats()
        
        self.logger.info("=" * 80)
        self.logger.info("PERFORMANCE SUMMARY")
        self.logger.info("=" * 80)
        
        # Scan performance
        scan = stats['scan']
        if scan['samples'] > 0:
            self.logger.info(f"Market Scanning:")
            self.logger.info(f"  Average time: {scan['avg_time']:.2f}s")
            self.logger.info(f"  Last scan: {scan['last_time']:.2f}s")
            self.logger.info(f"  Samples: {scan['samples']}")
            if scan['avg_time'] > self.SCAN_THRESHOLD:
                self.logger.warning(f"  ⚠️  SLOW: Average exceeds {self.SCAN_THRESHOLD}s threshold!")
        
        # Trade execution
        trade = stats['trade_execution']
        if trade['samples'] > 0:
            self.logger.info(f"Trade Execution:")
            self.logger.info(f"  Average time: {trade['avg_time']:.2f}s")
            self.logger.info(f"  Last trade: {trade['last_time']:.2f}s")
            self.logger.info(f"  Samples: {trade['samples']}")
            if trade['avg_time'] > self.TRADE_THRESHOLD:
                self.logger.warning(f"  ⚠️  SLOW: Average exceeds {self.TRADE_THRESHOLD}s threshold!")
        
        # API performance
        api = stats['api']
        self.logger.info(f"API Calls:")
        self.logger.info(f"  Average time: {api['avg_time']:.3f}s")
        self.logger.info(f"  Total calls: {api['total_calls']}")
        self.logger.info(f"  Calls/minute: {api['calls_per_minute']:.1f}")
        self.logger.info(f"  Error rate: {api['error_rate']:.1%}")
        self.logger.info(f"  Retry rate: {api['retry_rate']:.1%}")
        
        if api['error_rate'] > 0.05:  # > 5% errors
            self.logger.warning(f"  ⚠️  HIGH ERROR RATE: {api['error_rate']:.1%}")
        
        if api['retry_rate'] > 0.10:  # > 10% retries
            self.logger.warning(f"  ⚠️  HIGH RETRY RATE: {api['retry_rate']:.1%}")
        
        # Position updates
        update = stats['position_update']
        if update['samples'] > 0:
            self.logger.info(f"Position Updates:")
            self.logger.info(f"  Average time: {update['avg_time']:.3f}s")
            self.logger.info(f"  Samples: {update['samples']}")
        
        self.logger.info("=" * 80)
    
    def reset_api_counters(self):
        """Reset API call counters (useful for tracking over specific periods)"""
        with self._lock:
            self._api_call_count = 0
            self._api_error_count = 0
            self._api_retry_count = 0
            self._last_api_reset = time.time()
    
    def check_health(self) -> tuple[bool, str]:
        """
        Check if bot performance is healthy
        
        Returns:
            Tuple of (is_healthy, reason)
        """
        stats = self.get_stats()
        
        # Check scan performance
        if stats['scan']['samples'] > 5 and stats['scan']['avg_time'] > self.SCAN_THRESHOLD:
            return False, f"Market scanning too slow: {stats['scan']['avg_time']:.1f}s avg"
        
        # Check API error rate
        if stats['api']['total_calls'] > 50 and stats['api']['error_rate'] > 0.15:  # > 15% errors
            return False, f"High API error rate: {stats['api']['error_rate']:.1%}"
        
        # Check API retry rate
        if stats['api']['total_calls'] > 50 and stats['api']['retry_rate'] > 0.25:  # > 25% retries
            return False, f"High API retry rate: {stats['api']['retry_rate']:.1%}"
        
        return True, "Performance healthy"


# Global singleton instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
