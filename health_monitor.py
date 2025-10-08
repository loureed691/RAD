"""
Health monitoring and performance tracking for the trading bot
"""
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import deque


class HealthMonitor:
    """Monitor bot health and performance metrics"""
    
    def __init__(self):
        """Initialize the health monitor"""
        self._lock = threading.Lock()
        self._start_time = datetime.now()
        
        # API call tracking
        self._api_calls = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'rate_limited': 0,
            'last_call': None,
            'calls_per_minute': deque(maxlen=60)  # Track last 60 seconds
        }
        
        # Position tracking
        self._position_metrics = {
            'total_opened': 0,
            'total_closed': 0,
            'currently_open': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0,
            'last_trade': None
        }
        
        # Performance tracking
        self._performance_metrics = {
            'scans_completed': 0,
            'scan_errors': 0,
            'avg_scan_duration': 0.0,
            'last_scan_time': None,
            'position_updates': 0,
            'position_update_errors': 0
        }
        
        # Thread health
        self._thread_health = {
            'main_loop_active': False,
            'scanner_active': False,
            'position_monitor_active': False,
            'last_main_loop_heartbeat': None,
            'last_scanner_heartbeat': None,
            'last_position_monitor_heartbeat': None
        }
        
        # Error tracking
        self._error_log = deque(maxlen=100)  # Keep last 100 errors
    
    def record_api_call(self, success: bool = True, rate_limited: bool = False):
        """Record an API call"""
        with self._lock:
            self._api_calls['total'] += 1
            self._api_calls['last_call'] = datetime.now()
            self._api_calls['calls_per_minute'].append(time.time())
            
            if success:
                self._api_calls['successful'] += 1
            else:
                self._api_calls['failed'] += 1
            
            if rate_limited:
                self._api_calls['rate_limited'] += 1
    
    def record_position_opened(self, symbol: str):
        """Record a position opening"""
        with self._lock:
            self._position_metrics['total_opened'] += 1
            self._position_metrics['currently_open'] += 1
            self._position_metrics['last_trade'] = {
                'action': 'opened',
                'symbol': symbol,
                'time': datetime.now()
            }
    
    def record_position_closed(self, symbol: str, pnl: float, is_win: bool):
        """Record a position closing"""
        with self._lock:
            self._position_metrics['total_closed'] += 1
            self._position_metrics['currently_open'] -= 1
            self._position_metrics['total_pnl'] += pnl
            
            if is_win:
                self._position_metrics['wins'] += 1
            else:
                self._position_metrics['losses'] += 1
            
            self._position_metrics['last_trade'] = {
                'action': 'closed',
                'symbol': symbol,
                'pnl': pnl,
                'is_win': is_win,
                'time': datetime.now()
            }
    
    def record_scan_completed(self, duration: float):
        """Record a completed market scan"""
        with self._lock:
            self._performance_metrics['scans_completed'] += 1
            self._performance_metrics['last_scan_time'] = datetime.now()
            
            # Update running average
            n = self._performance_metrics['scans_completed']
            current_avg = self._performance_metrics['avg_scan_duration']
            self._performance_metrics['avg_scan_duration'] = (
                (current_avg * (n - 1) + duration) / n
            )
    
    def record_scan_error(self):
        """Record a scan error"""
        with self._lock:
            self._performance_metrics['scan_errors'] += 1
    
    def record_position_update(self, success: bool = True):
        """Record a position update"""
        with self._lock:
            if success:
                self._performance_metrics['position_updates'] += 1
            else:
                self._performance_metrics['position_update_errors'] += 1
    
    def record_error(self, error_type: str, message: str):
        """Record an error"""
        with self._lock:
            self._error_log.append({
                'type': error_type,
                'message': message,
                'time': datetime.now()
            })
    
    def heartbeat_main_loop(self):
        """Record main loop heartbeat"""
        with self._lock:
            self._thread_health['main_loop_active'] = True
            self._thread_health['last_main_loop_heartbeat'] = datetime.now()
    
    def heartbeat_scanner(self):
        """Record scanner thread heartbeat"""
        with self._lock:
            self._thread_health['scanner_active'] = True
            self._thread_health['last_scanner_heartbeat'] = datetime.now()
    
    def heartbeat_position_monitor(self):
        """Record position monitor thread heartbeat"""
        with self._lock:
            self._thread_health['position_monitor_active'] = True
            self._thread_health['last_position_monitor_heartbeat'] = datetime.now()
    
    def get_api_calls_per_minute(self) -> int:
        """Get current API calls per minute rate"""
        with self._lock:
            now = time.time()
            # Count calls in the last 60 seconds
            recent_calls = [t for t in self._api_calls['calls_per_minute'] if now - t <= 60]
            return len(recent_calls)
    
    def get_uptime(self) -> timedelta:
        """Get bot uptime"""
        return datetime.now() - self._start_time
    
    def get_win_rate(self) -> float:
        """Get win rate percentage"""
        with self._lock:
            total_trades = self._position_metrics['wins'] + self._position_metrics['losses']
            if total_trades == 0:
                return 0.0
            return (self._position_metrics['wins'] / total_trades) * 100
    
    def check_thread_health(self, timeout_seconds: int = 30) -> Dict[str, bool]:
        """Check if all threads are healthy (received heartbeat within timeout)"""
        with self._lock:
            now = datetime.now()
            health_status = {}
            
            for thread_name in ['main_loop', 'scanner', 'position_monitor']:
                last_heartbeat = self._thread_health.get(f'last_{thread_name}_heartbeat')
                if last_heartbeat is None:
                    health_status[thread_name] = False
                else:
                    time_since_heartbeat = (now - last_heartbeat).total_seconds()
                    health_status[thread_name] = time_since_heartbeat < timeout_seconds
            
            return health_status
    
    def get_health_report(self) -> Dict:
        """Get comprehensive health report"""
        with self._lock:
            uptime = datetime.now() - self._start_time
            
            # Calculate win rate
            total_trades = self._position_metrics['wins'] + self._position_metrics['losses']
            win_rate = (self._position_metrics['wins'] / total_trades * 100) if total_trades > 0 else 0.0
            
            # Get API rate
            now = time.time()
            recent_calls = [t for t in self._api_calls['calls_per_minute'] if now - t <= 60]
            api_rate = len(recent_calls)
            
            # Check thread health
            now_dt = datetime.now()
            thread_health = {}
            for thread_name in ['main_loop', 'scanner', 'position_monitor']:
                last_heartbeat = self._thread_health.get(f'last_{thread_name}_heartbeat')
                if last_heartbeat is None:
                    thread_health[thread_name] = False
                else:
                    time_since_heartbeat = (now_dt - last_heartbeat).total_seconds()
                    thread_health[thread_name] = time_since_heartbeat < 30
            
            # Calculate API success rate
            total_api = self._api_calls['total']
            api_success_rate = (
                (self._api_calls['successful'] / total_api * 100) 
                if total_api > 0 else 100.0
            )
            
            # Get recent errors
            recent_errors = list(self._error_log)[-10:]  # Last 10 errors
            
            return {
                'uptime': {
                    'seconds': int(uptime.total_seconds()),
                    'formatted': str(uptime).split('.')[0]
                },
                'api': {
                    'total_calls': self._api_calls['total'],
                    'successful': self._api_calls['successful'],
                    'failed': self._api_calls['failed'],
                    'rate_limited': self._api_calls['rate_limited'],
                    'success_rate': round(api_success_rate, 2),
                    'calls_per_minute': api_rate,
                    'last_call': self._api_calls['last_call']
                },
                'positions': {
                    'total_opened': self._position_metrics['total_opened'],
                    'total_closed': self._position_metrics['total_closed'],
                    'currently_open': self._position_metrics['currently_open'],
                    'wins': self._position_metrics['wins'],
                    'losses': self._position_metrics['losses'],
                    'win_rate': round(win_rate, 2),
                    'total_pnl': round(self._position_metrics['total_pnl'], 2),
                    'last_trade': self._position_metrics['last_trade']
                },
                'performance': {
                    'scans_completed': self._performance_metrics['scans_completed'],
                    'scan_errors': self._performance_metrics['scan_errors'],
                    'avg_scan_duration': round(self._performance_metrics['avg_scan_duration'], 2),
                    'last_scan_time': self._performance_metrics['last_scan_time'],
                    'position_updates': self._performance_metrics['position_updates'],
                    'position_update_errors': self._performance_metrics['position_update_errors']
                },
                'threads': thread_health,
                'recent_errors': recent_errors,
                'overall_health': all(thread_health.values()) and api_success_rate > 90
            }
    
    def get_status_summary(self) -> str:
        """Get a formatted status summary string"""
        report = self.get_health_report()
        
        lines = [
            "=" * 60,
            "🏥 BOT HEALTH STATUS",
            "=" * 60,
            f"⏱️  Uptime: {report['uptime']['formatted']}",
            "",
            "📊 POSITIONS:",
            f"   Currently Open: {report['positions']['currently_open']}",
            f"   Total Trades: {report['positions']['total_closed']}",
            f"   Win Rate: {report['positions']['win_rate']:.1f}%",
            f"   Total P/L: ${report['positions']['total_pnl']:.2f}",
            "",
            "🔌 API HEALTH:",
            f"   Total Calls: {report['api']['total_calls']}",
            f"   Success Rate: {report['api']['success_rate']:.1f}%",
            f"   Rate Limited: {report['api']['rate_limited']}",
            f"   Calls/Min: {report['api']['calls_per_minute']}",
            "",
            "🧵 THREADS:",
            f"   Main Loop: {'✅' if report['threads']['main_loop'] else '❌'}",
            f"   Scanner: {'✅' if report['threads']['scanner'] else '❌'}",
            f"   Position Monitor: {'✅' if report['threads']['position_monitor'] else '❌'}",
            "",
            "📈 PERFORMANCE:",
            f"   Scans: {report['performance']['scans_completed']} (avg: {report['performance']['avg_scan_duration']:.1f}s)",
            f"   Position Updates: {report['performance']['position_updates']}",
            "",
            f"Overall Health: {'🟢 HEALTHY' if report['overall_health'] else '🔴 UNHEALTHY'}",
            "=" * 60
        ]
        
        return "\n".join(lines)
