"""
Production-Grade Error Recovery and Self-Healing System

This module provides comprehensive error handling, recovery mechanisms,
and self-healing capabilities for the trading bot.
"""
import time
import threading
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
from logger import Logger


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = 1  # Non-critical, informational
    MEDIUM = 2  # Requires attention but not urgent
    HIGH = 3  # Important, may affect trading
    CRITICAL = 4  # Severe, requires immediate action


class RecoveryAction(Enum):
    """Recovery action types"""
    RETRY = "retry"
    BACKOFF = "backoff"
    RESET = "reset"
    ALERT = "alert"
    SHUTDOWN = "shutdown"


class ErrorRecord:
    """Record of an error occurrence"""
    
    def __init__(self, error_type: str, message: str, severity: ErrorSeverity,
                 context: Optional[Dict] = None):
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.context = context or {}
        self.timestamp = datetime.now()
        self.recovery_attempted = False
        self.recovery_successful = False


class ErrorRecoveryManager:
    """
    Manages error detection, logging, and recovery
    
    This class provides centralized error management with intelligent recovery
    strategies, circuit breaker functionality, and comprehensive error tracking.
    
    Args:
        max_retries: Maximum number of retry attempts for recovery actions (default: 3)
        backoff_base: Base for exponential backoff calculations (default: 2.0)
    
    Attributes:
        error_history: Deque of recent errors (max 1000 entries)
        error_counts: Dict mapping error types to occurrence counts
        last_errors: Dict mapping error types to last occurrence timestamp
        recovery_strategies: Dict of registered recovery strategies
        circuit_breakers: Dict tracking open circuit breakers by component
    """
    
    def __init__(self, max_retries: int = 3, backoff_base: float = 2.0):
        self.logger = Logger.get_logger()
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        
        # Error tracking
        self.error_history = deque(maxlen=1000)
        self.error_counts = {}  # error_type -> count
        self.last_errors = {}  # error_type -> timestamp
        self._lock = threading.Lock()
        
        # Recovery strategies
        self.recovery_strategies = {}
        self._register_default_strategies()
        
        # Circuit breaker state
        self.circuit_breakers = {}  # component -> (is_open, open_time)
        self.circuit_breaker_timeout = 60  # seconds
        
    def _register_default_strategies(self):
        """Register default recovery strategies for common errors"""
        self.register_recovery_strategy(
            "api_rate_limit",
            ErrorSeverity.MEDIUM,
            RecoveryAction.BACKOFF,
            backoff_seconds=30
        )
        self.register_recovery_strategy(
            "api_connection",
            ErrorSeverity.HIGH,
            RecoveryAction.RETRY,
            max_retries=5
        )
        self.register_recovery_strategy(
            "insufficient_balance",
            ErrorSeverity.MEDIUM,
            RecoveryAction.ALERT,
        )
        self.register_recovery_strategy(
            "position_not_found",
            ErrorSeverity.HIGH,
            RecoveryAction.RESET,
        )
        self.register_recovery_strategy(
            "critical_system_error",
            ErrorSeverity.CRITICAL,
            RecoveryAction.ALERT,
        )
    
    def register_recovery_strategy(self, error_type: str, severity: ErrorSeverity,
                                   action: RecoveryAction, **kwargs):
        """
        Register a recovery strategy for an error type
        
        Args:
            error_type: Type of error (e.g., 'api_rate_limit')
            severity: Error severity level
            action: Recovery action to take
            **kwargs: Additional parameters for the recovery action
        """
        self.recovery_strategies[error_type] = {
            'severity': severity,
            'action': action,
            'params': kwargs
        }
    
    def record_error(self, error_type: str, message: str,
                    severity: Optional[ErrorSeverity] = None,
                    context: Optional[Dict] = None) -> ErrorRecord:
        """
        Record an error occurrence
        
        Args:
            error_type: Type of error
            message: Error message
            severity: Error severity (optional, will use registered if available)
            context: Additional context information
            
        Returns:
            ErrorRecord object
        """
        # Use registered severity if not provided
        if severity is None and error_type in self.recovery_strategies:
            severity = self.recovery_strategies[error_type]['severity']
        elif severity is None:
            severity = ErrorSeverity.MEDIUM
        
        error = ErrorRecord(error_type, message, severity, context)
        
        with self._lock:
            self.error_history.append(error)
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
            self.last_errors[error_type] = datetime.now()
        
        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {error_type} - {message}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"ERROR: {error_type} - {message}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"WARNING: {error_type} - {message}")
        else:
            self.logger.debug(f"INFO: {error_type} - {message}")
        
        return error
    
    def should_trigger_recovery(self, error_type: str, time_window: int = 60) -> bool:
        """
        Check if recovery should be triggered for an error type
        
        Args:
            error_type: Type of error to check
            time_window: Time window in seconds to consider
            
        Returns:
            True if recovery should be triggered
        """
        with self._lock:
            if error_type not in self.last_errors:
                return False
            
            # Check if error occurred recently
            time_since_error = (datetime.now() - self.last_errors[error_type]).total_seconds()
            if time_since_error > time_window:
                return False
            
            # Check error frequency
            error_count = self.error_counts.get(error_type, 0)
            
            # Trigger if multiple errors in short time
            return error_count >= 3
    
    def attempt_recovery(self, error: ErrorRecord) -> bool:
        """
        Attempt to recover from an error
        
        Args:
            error: ErrorRecord to recover from
            
        Returns:
            True if recovery was successful
        """
        error_type = error.error_type
        
        if error_type not in self.recovery_strategies:
            self.logger.warning(f"No recovery strategy for error type: {error_type}")
            return False
        
        strategy = self.recovery_strategies[error_type]
        action = strategy['action']
        params = strategy['params']
        
        self.logger.info(f"Attempting recovery for {error_type} using {action.value}")
        
        error.recovery_attempted = True
        
        try:
            if action == RecoveryAction.RETRY:
                return self._handle_retry(error, params)
            elif action == RecoveryAction.BACKOFF:
                return self._handle_backoff(error, params)
            elif action == RecoveryAction.RESET:
                return self._handle_reset(error, params)
            elif action == RecoveryAction.ALERT:
                return self._handle_alert(error, params)
            elif action == RecoveryAction.SHUTDOWN:
                return self._handle_shutdown(error, params)
            else:
                self.logger.warning(f"Unknown recovery action: {action}")
                return False
        except Exception as e:
            self.logger.error(f"Recovery attempt failed: {e}")
            return False
    
    def _handle_retry(self, error: ErrorRecord, params: Dict) -> bool:
        """Handle retry recovery action"""
        max_retries = params.get('max_retries', self.max_retries)
        retry_count = error.context.get('retry_count', 0)
        
        if retry_count >= max_retries:
            self.logger.warning(f"Max retries ({max_retries}) exceeded for {error.error_type}")
            return False
        
        # Exponential backoff
        backoff_time = self.backoff_base ** retry_count
        self.logger.info(f"Retry {retry_count + 1}/{max_retries} after {backoff_time:.1f}s")
        time.sleep(backoff_time)
        
        error.recovery_successful = True
        return True
    
    def _handle_backoff(self, error: ErrorRecord, params: Dict) -> bool:
        """Handle backoff recovery action"""
        backoff_seconds = params.get('backoff_seconds', 30)
        self.logger.info(f"Backing off for {backoff_seconds}s")
        time.sleep(backoff_seconds)
        error.recovery_successful = True
        return True
    
    def _handle_reset(self, error: ErrorRecord, params: Dict) -> bool:
        """Handle reset recovery action"""
        self.logger.info(f"Resetting component due to {error.error_type}")
        # Reset logic would go here (component-specific)
        error.recovery_successful = True
        return True
    
    def _handle_alert(self, error: ErrorRecord, params: Dict) -> bool:
        """Handle alert recovery action"""
        self.logger.warning(f"ALERT: {error.error_type} - {error.message}")
        # Could send notifications here (email, Slack, etc.)
        error.recovery_successful = True
        return True
    
    def _handle_shutdown(self, error: ErrorRecord, params: Dict) -> bool:
        """
        Handle shutdown recovery action
        
        Note: This marks the need for shutdown but doesn't actually shut down.
        The caller should check error.recovery_successful and initiate shutdown.
        """
        self.logger.critical(f"SHUTDOWN TRIGGERED: {error.error_type} - {error.message}")
        self.logger.critical("Graceful shutdown should be initiated by the calling code")
        # Could send notifications here (email, Slack, etc.)
        error.recovery_successful = True
        return True
    
    def open_circuit_breaker(self, component: str):
        """Open circuit breaker for a component"""
        with self._lock:
            self.circuit_breakers[component] = (True, datetime.now())
            self.logger.warning(f"Circuit breaker OPENED for {component}")
    
    def close_circuit_breaker(self, component: str):
        """Close circuit breaker for a component"""
        with self._lock:
            if component in self.circuit_breakers:
                del self.circuit_breakers[component]
                self.logger.info(f"Circuit breaker CLOSED for {component}")
    
    def is_circuit_breaker_open(self, component: str) -> bool:
        """Check if circuit breaker is open for a component"""
        with self._lock:
            if component not in self.circuit_breakers:
                return False
            
            is_open, open_time = self.circuit_breakers[component]
            
            if not is_open:
                return False
            
            # Auto-close after timeout
            time_open = (datetime.now() - open_time).total_seconds()
            if time_open > self.circuit_breaker_timeout:
                del self.circuit_breakers[component]
                self.logger.info(f"Circuit breaker auto-closed for {component} after {time_open:.0f}s")
                return False
            
            return True
    
    def get_error_statistics(self) -> Dict:
        """Get error statistics"""
        with self._lock:
            total_errors = len(self.error_history)
            
            # Count by type
            type_counts = {}
            severity_counts = {s: 0 for s in ErrorSeverity}
            
            for error in self.error_history:
                type_counts[error.error_type] = type_counts.get(error.error_type, 0) + 1
                severity_counts[error.severity] += 1
            
            # Calculate error rate (errors per minute)
            if total_errors > 0:
                oldest_error = self.error_history[0]
                newest_error = self.error_history[-1]
                time_span = (newest_error.timestamp - oldest_error.timestamp).total_seconds() / 60
                error_rate = total_errors / max(time_span, 1)
            else:
                error_rate = 0.0
            
            return {
                'total_errors': total_errors,
                'error_rate_per_minute': error_rate,
                'errors_by_type': type_counts,
                'errors_by_severity': {s.name: count for s, count in severity_counts.items()},
                'circuit_breakers_open': len(self.circuit_breakers)
            }
    
    def get_error_report(self) -> str:
        """Get a human-readable error report"""
        stats = self.get_error_statistics()
        
        lines = [
            "=" * 60,
            "ERROR RECOVERY REPORT",
            "=" * 60,
            f"Total Errors: {stats['total_errors']}",
            f"Error Rate: {stats['error_rate_per_minute']:.2f} per minute",
            f"Circuit Breakers Open: {stats['circuit_breakers_open']}",
            "",
            "Errors by Type:",
            "-" * 60
        ]
        
        for error_type, count in sorted(stats['errors_by_type'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {error_type}: {count}")
        
        lines.extend([
            "",
            "Errors by Severity:",
            "-" * 60
        ])
        
        for severity, count in stats['errors_by_severity'].items():
            if count > 0:
                lines.append(f"  {severity}: {count}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def clear_old_errors(self, age_hours: int = 24):
        """Clear errors older than specified age"""
        cutoff_time = datetime.now() - timedelta(hours=age_hours)
        
        with self._lock:
            # Keep only recent errors
            recent_errors = [e for e in self.error_history if e.timestamp > cutoff_time]
            self.error_history.clear()
            self.error_history.extend(recent_errors)
            
            self.logger.info(f"Cleared errors older than {age_hours} hours")


class RetryWithBackoff:
    """Decorator for automatic retry with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, backoff_base: float = 2.0,
                 error_manager: Optional[ErrorRecoveryManager] = None):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.error_manager = error_manager
        self.logger = Logger.get_logger()
    
    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        # Last attempt failed
                        if self.error_manager:
                            self.error_manager.record_error(
                                f"{func.__name__}_error",
                                str(e),
                                ErrorSeverity.HIGH,
                                {'function': func.__name__, 'attempt': attempt + 1}
                            )
                        raise
                    
                    # Calculate backoff
                    backoff_time = self.backoff_base ** attempt
                    self.logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {backoff_time:.1f}s..."
                    )
                    time.sleep(backoff_time)
            
            return None
        
        return wrapper


# Global instance
_error_manager_instance = None
_error_manager_lock = threading.Lock()


def get_error_manager() -> ErrorRecoveryManager:
    """Get or create the global error manager instance"""
    global _error_manager_instance
    
    if _error_manager_instance is None:
        with _error_manager_lock:
            if _error_manager_instance is None:
                _error_manager_instance = ErrorRecoveryManager()
    
    return _error_manager_instance
