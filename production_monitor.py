"""
Production-grade monitoring and alerting system

Tracks critical metrics and triggers alerts when thresholds are exceeded.
Essential for production deployment to detect issues before they become critical.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger
import json
import os

class ProductionMonitor:
    """Monitor bot health and performance in production"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.start_time = datetime.now()
        
        # Health metrics
        self.api_failures = 0
        self.consecutive_scan_failures = 0
        self.consecutive_position_update_failures = 0
        self.last_successful_scan = datetime.now()
        self.last_successful_position_update = datetime.now()
        self.last_trade_time = None
        
        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_balance = 0.0
        
        # Alert thresholds
        self.max_api_failures = 10  # Alert if more than 10 API failures
        self.max_scan_age_minutes = 10  # Alert if no scans for 10 minutes
        self.max_position_update_age_minutes = 5  # Alert if no position updates for 5 minutes
        self.max_consecutive_losses = 5  # Alert on 5 consecutive losses
        self.max_drawdown_pct = 0.20  # Alert on 20% drawdown
        
        # State file
        self.state_file = 'models/production_monitor_state.json'
        
        # Load saved state
        self.load_state()
    
    def record_api_failure(self):
        """Record an API failure"""
        self.api_failures += 1
        
        if self.api_failures >= self.max_api_failures:
            self.trigger_alert('critical', 'excessive_api_failures', 
                             f'{self.api_failures} API failures detected')
    
    def record_api_success(self):
        """Record successful API call"""
        # Reset failure counter on success
        if self.api_failures > 0:
            self.logger.debug(f"API recovered after {self.api_failures} failures")
        self.api_failures = 0
    
    def record_scan_success(self):
        """Record successful market scan"""
        self.last_successful_scan = datetime.now()
        self.consecutive_scan_failures = 0
    
    def record_scan_failure(self):
        """Record failed market scan"""
        self.consecutive_scan_failures += 1
        
        # Check if scans have been failing for too long
        time_since_scan = (datetime.now() - self.last_successful_scan).total_seconds() / 60
        if time_since_scan > self.max_scan_age_minutes:
            self.trigger_alert('high', 'no_recent_scans',
                             f'No successful scans for {time_since_scan:.1f} minutes')
    
    def record_position_update_success(self):
        """Record successful position update"""
        self.last_successful_position_update = datetime.now()
        self.consecutive_position_update_failures = 0
    
    def record_position_update_failure(self):
        """Record failed position update"""
        self.consecutive_position_update_failures += 1
        
        # Check if updates have been failing
        time_since_update = (datetime.now() - self.last_successful_position_update).total_seconds() / 60
        if time_since_update > self.max_position_update_age_minutes:
            self.trigger_alert('critical', 'no_position_updates',
                             f'No successful position updates for {time_since_update:.1f} minutes')
    
    def record_trade(self, pnl: float, balance: float):
        """
        Record trade outcome
        
        Args:
            pnl: Profit/loss percentage
            balance: Current balance
        """
        self.total_trades += 1
        self.last_trade_time = datetime.now()
        self.total_pnl += pnl
        
        # Track wins/losses
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Update peak balance and drawdown
        if balance > self.peak_balance:
            self.peak_balance = balance
        
        current_drawdown = (self.peak_balance - balance) / self.peak_balance if self.peak_balance > 0 else 0
        
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
        
        # Alert on excessive drawdown
        if current_drawdown >= self.max_drawdown_pct:
            self.trigger_alert('high', 'excessive_drawdown',
                             f'Drawdown: {current_drawdown:.1%} (peak: ${self.peak_balance:.2f}, current: ${balance:.2f})')
        
        # Check for consecutive losses
        if self.losing_trades >= self.max_consecutive_losses:
            recent_wins = self.winning_trades - (self.total_trades - self.max_consecutive_losses)
            if recent_wins == 0:  # All recent trades are losses
                self.trigger_alert('high', 'consecutive_losses',
                                 f'{self.losing_trades} consecutive losing trades')
    
    def trigger_alert(self, severity: str, alert_type: str, message: str):
        """
        Trigger an alert
        
        Args:
            severity: 'critical', 'high', 'medium', or 'low'
            alert_type: Type of alert
            message: Alert message
        """
        alert_msg = f"🚨 ALERT [{severity.upper()}] {alert_type}: {message}"
        
        if severity == 'critical':
            self.logger.error(alert_msg)
        elif severity == 'high':
            self.logger.warning(alert_msg)
        else:
            self.logger.info(alert_msg)
        
        # In production, this would send Telegram/email/SMS alerts
        # For now, just log to file
        try:
            alert_file = 'logs/alerts.log'
            os.makedirs(os.path.dirname(alert_file), exist_ok=True)
            
            with open(alert_file, 'a') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] [{severity}] {alert_type}: {message}\n")
        except Exception as e:
            self.logger.debug(f"Failed to write alert to file: {e}")
    
    def check_health(self) -> Tuple[bool, List[str]]:
        """
        Check overall system health
        
        Returns:
            (is_healthy, list of issues)
        """
        issues = []
        
        # Check API health
        if self.api_failures > 0:
            issues.append(f'API failures: {self.api_failures}')
        
        # Check scan health
        time_since_scan = (datetime.now() - self.last_successful_scan).total_seconds() / 60
        if time_since_scan > self.max_scan_age_minutes:
            issues.append(f'No scans for {time_since_scan:.1f} minutes')
        
        # Check position update health
        time_since_update = (datetime.now() - self.last_successful_position_update).total_seconds() / 60
        if time_since_update > self.max_position_update_age_minutes:
            issues.append(f'No position updates for {time_since_update:.1f} minutes')
        
        # Check performance
        if self.total_trades > 10:  # Need sufficient data
            win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
            if win_rate < 0.40:  # Less than 40% win rate is concerning
                issues.append(f'Low win rate: {win_rate:.1%}')
        
        # Check drawdown
        if self.max_drawdown > self.max_drawdown_pct:
            issues.append(f'High drawdown: {self.max_drawdown:.1%}')
        
        is_healthy = len(issues) == 0
        return is_healthy, issues
    
    def get_status_report(self) -> Dict:
        """
        Get comprehensive status report
        
        Returns:
            Dictionary with status information
        """
        uptime = datetime.now() - self.start_time
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        is_healthy, issues = self.check_health()
        
        return {
            'status': 'healthy' if is_healthy else 'unhealthy',
            'uptime_hours': uptime.total_seconds() / 3600,
            'issues': issues,
            'metrics': {
                'total_trades': self.total_trades,
                'win_rate': win_rate,
                'total_pnl': self.total_pnl,
                'max_drawdown': self.max_drawdown,
                'api_failures': self.api_failures,
                'consecutive_scan_failures': self.consecutive_scan_failures,
            },
            'timestamps': {
                'last_scan': self.last_successful_scan.isoformat(),
                'last_position_update': self.last_successful_position_update.isoformat(),
                'last_trade': self.last_trade_time.isoformat() if self.last_trade_time else None,
            }
        }
    
    def print_status(self):
        """Print status report to log"""
        status = self.get_status_report()
        
        self.logger.info("=" * 60)
        self.logger.info("📊 PRODUCTION MONITOR STATUS")
        self.logger.info("=" * 60)
        self.logger.info(f"Status: {status['status'].upper()}")
        self.logger.info(f"Uptime: {status['uptime_hours']:.1f} hours")
        
        if status['issues']:
            self.logger.warning("Issues:")
            for issue in status['issues']:
                self.logger.warning(f"  - {issue}")
        
        metrics = status['metrics']
        self.logger.info(f"Total Trades: {metrics['total_trades']}")
        if metrics['total_trades'] > 0:
            self.logger.info(f"Win Rate: {metrics['win_rate']:.1%}")
            self.logger.info(f"Total P/L: {metrics['total_pnl']:.2%}")
            self.logger.info(f"Max Drawdown: {metrics['max_drawdown']:.1%}")
        
        self.logger.info(f"API Failures: {metrics['api_failures']}")
        self.logger.info("=" * 60)
    
    def save_state(self):
        """Save monitor state to disk"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            state = {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'total_pnl': self.total_pnl,
                'max_drawdown': self.max_drawdown,
                'peak_balance': self.peak_balance,
                'last_trade_time': self.last_trade_time.isoformat() if self.last_trade_time else None,
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            self.logger.debug(f"Failed to save monitor state: {e}")
    
    def load_state(self):
        """Load monitor state from disk"""
        try:
            if not os.path.exists(self.state_file):
                return
            
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.total_trades = state.get('total_trades', 0)
            self.winning_trades = state.get('winning_trades', 0)
            self.losing_trades = state.get('losing_trades', 0)
            self.total_pnl = state.get('total_pnl', 0.0)
            self.max_drawdown = state.get('max_drawdown', 0.0)
            self.peak_balance = state.get('peak_balance', 0.0)
            
            last_trade = state.get('last_trade_time')
            if last_trade:
                self.last_trade_time = datetime.fromisoformat(last_trade)
            
            self.logger.debug("Production monitor state loaded")
            
        except Exception as e:
            self.logger.debug(f"Failed to load monitor state: {e}")
