"""
Health monitoring and status reporting for the trading bot
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from logger import Logger


class HealthMonitor:
    """Monitor bot health and status"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.start_time = datetime.now()
        self.last_successful_scan = None
        self.last_successful_trade = None
        self.last_api_error = None
        self.error_count = 0
        self.warning_count = 0
        self.successful_cycles = 0
        self.failed_cycles = 0
        self.health_checks = []
        
    def record_successful_cycle(self):
        """Record a successful trading cycle"""
        self.successful_cycles += 1
        self.last_successful_scan = datetime.now()
    
    def record_failed_cycle(self):
        """Record a failed trading cycle"""
        self.failed_cycles += 1
    
    def record_error(self, error_msg: str):
        """Record an error"""
        self.error_count += 1
        self.last_api_error = {
            'message': error_msg,
            'timestamp': datetime.now()
        }
    
    def record_warning(self):
        """Record a warning"""
        self.warning_count += 1
    
    def record_trade(self):
        """Record a trade execution"""
        self.last_successful_trade = datetime.now()
    
    def get_uptime(self) -> timedelta:
        """Get bot uptime"""
        return datetime.now() - self.start_time
    
    def get_health_status(self) -> Dict:
        """Get comprehensive health status"""
        uptime = self.get_uptime()
        total_cycles = self.successful_cycles + self.failed_cycles
        success_rate = (
            self.successful_cycles / total_cycles * 100 
            if total_cycles > 0 else 0
        )
        
        # Determine overall health
        health_score = 100
        health_issues = []
        
        # Check for recent errors
        if self.last_api_error:
            error_age = (datetime.now() - self.last_api_error['timestamp']).total_seconds()
            if error_age < 300:  # Error in last 5 minutes
                health_score -= 20
                health_issues.append(f"Recent API error: {self.last_api_error['message']}")
        
        # Check cycle success rate
        if success_rate < 80 and total_cycles > 10:
            health_score -= 30
            health_issues.append(f"Low cycle success rate: {success_rate:.1f}%")
        
        # Check for stale scan
        if self.last_successful_scan:
            scan_age = (datetime.now() - self.last_successful_scan).total_seconds()
            if scan_age > 600:  # No successful scan in 10 minutes
                health_score -= 25
                health_issues.append(f"No successful scan in {int(scan_age/60)} minutes")
        
        # Determine status
        if health_score >= 80:
            status = "HEALTHY"
        elif health_score >= 50:
            status = "DEGRADED"
        else:
            status = "UNHEALTHY"
        
        return {
            'status': status,
            'health_score': health_score,
            'uptime': str(uptime),
            'uptime_seconds': uptime.total_seconds(),
            'total_cycles': total_cycles,
            'successful_cycles': self.successful_cycles,
            'failed_cycles': self.failed_cycles,
            'success_rate': success_rate,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'last_successful_scan': self.last_successful_scan.isoformat() if self.last_successful_scan else None,
            'last_successful_trade': self.last_successful_trade.isoformat() if self.last_successful_trade else None,
            'last_api_error': self.last_api_error,
            'health_issues': health_issues
        }
    
    def get_health_summary(self) -> str:
        """Get formatted health summary"""
        status = self.get_health_status()
        
        summary = []
        summary.append("=" * 60)
        summary.append("🏥 BOT HEALTH STATUS")
        summary.append("=" * 60)
        
        # Status indicator
        status_icon = {
            'HEALTHY': '✅',
            'DEGRADED': '⚠️',
            'UNHEALTHY': '❌'
        }.get(status['status'], '❓')
        
        summary.append(f"Status: {status_icon} {status['status']} (Score: {status['health_score']}/100)")
        summary.append(f"Uptime: {status['uptime']}")
        summary.append(f"Cycles: {status['successful_cycles']}/{status['total_cycles']} successful ({status['success_rate']:.1f}%)")
        summary.append(f"Errors: {status['error_count']}, Warnings: {status['warning_count']}")
        
        if status['last_successful_scan']:
            summary.append(f"Last scan: {status['last_successful_scan']}")
        
        if status['last_successful_trade']:
            summary.append(f"Last trade: {status['last_successful_trade']}")
        
        if status['health_issues']:
            summary.append("\n⚠️  Health Issues:")
            for issue in status['health_issues']:
                summary.append(f"  • {issue}")
        
        summary.append("=" * 60)
        
        return "\n".join(summary)


class ConfigValidator:
    """Enhanced configuration validation"""
    
    @staticmethod
    def validate_trading_config(config) -> List[str]:
        """
        Validate trading configuration and return warnings/errors
        
        Returns:
            List of warning/error messages
        """
        issues = []
        logger = Logger.get_logger()
        
        # Check leverage
        if hasattr(config, 'LEVERAGE'):
            if config.LEVERAGE < 1:
                issues.append(f"⚠️  Leverage too low: {config.LEVERAGE}x (minimum: 1x)")
            elif config.LEVERAGE > 20:
                issues.append(f"⚠️  Leverage very high: {config.LEVERAGE}x (maximum recommended: 20x)")
            elif config.LEVERAGE > 15:
                issues.append(f"⚠️  High leverage warning: {config.LEVERAGE}x (use with caution)")
        
        # Check risk per trade
        if hasattr(config, 'RISK_PER_TRADE'):
            if config.RISK_PER_TRADE < 0.005:
                issues.append(f"⚠️  Risk per trade very low: {config.RISK_PER_TRADE:.2%} (may limit profitability)")
            elif config.RISK_PER_TRADE > 0.05:
                issues.append(f"⚠️  Risk per trade very high: {config.RISK_PER_TRADE:.2%} (recommended: 1-3%)")
        
        # Check position size
        if hasattr(config, 'MAX_POSITION_SIZE'):
            if config.MAX_POSITION_SIZE < 10:
                issues.append(f"⚠️  Max position size very low: ${config.MAX_POSITION_SIZE} (may limit trading)")
        
        # Check intervals
        if hasattr(config, 'CHECK_INTERVAL'):
            if config.CHECK_INTERVAL < 30:
                issues.append(f"⚠️  Check interval very short: {config.CHECK_INTERVAL}s (may hit API rate limits)")
            elif config.CHECK_INTERVAL > 300:
                issues.append(f"⚠️  Check interval very long: {config.CHECK_INTERVAL}s (may miss opportunities)")
        
        # Check max positions
        if hasattr(config, 'MAX_OPEN_POSITIONS'):
            if config.MAX_OPEN_POSITIONS < 1:
                issues.append(f"❌ Max open positions must be at least 1")
            elif config.MAX_OPEN_POSITIONS > 10:
                issues.append(f"⚠️  Many concurrent positions: {config.MAX_OPEN_POSITIONS} (increases risk)")
        
        # Log issues
        if issues:
            logger.warning("Configuration validation found issues:")
            for issue in issues:
                logger.warning(f"  {issue}")
        else:
            logger.info("✅ Configuration validation passed")
        
        return issues
    
    @staticmethod
    def get_config_summary(config) -> str:
        """Get formatted configuration summary"""
        summary = []
        summary.append("=" * 60)
        summary.append("⚙️  CONFIGURATION SUMMARY")
        summary.append("=" * 60)
        
        if hasattr(config, 'LEVERAGE'):
            summary.append(f"Leverage: {config.LEVERAGE}x")
        
        if hasattr(config, 'MAX_POSITION_SIZE'):
            summary.append(f"Max Position Size: ${config.MAX_POSITION_SIZE:.2f}")
        
        if hasattr(config, 'RISK_PER_TRADE'):
            summary.append(f"Risk Per Trade: {config.RISK_PER_TRADE:.2%}")
        
        if hasattr(config, 'MIN_PROFIT_THRESHOLD'):
            summary.append(f"Min Profit Threshold: {config.MIN_PROFIT_THRESHOLD:.2%}")
        
        if hasattr(config, 'MAX_OPEN_POSITIONS'):
            summary.append(f"Max Open Positions: {config.MAX_OPEN_POSITIONS}")
        
        if hasattr(config, 'CHECK_INTERVAL'):
            summary.append(f"Check Interval: {config.CHECK_INTERVAL}s")
        
        if hasattr(config, 'TRAILING_STOP_PERCENTAGE'):
            summary.append(f"Trailing Stop: {config.TRAILING_STOP_PERCENTAGE:.2%}")
        
        summary.append("=" * 60)
        
        return "\n".join(summary)


class AlertManager:
    """Manage and track alerts"""
    
    def __init__(self):
        self.alerts = []
        self.logger = Logger.get_logger()
        self.max_alerts = 100
    
    def add_alert(self, severity: str, message: str, category: str = "general"):
        """
        Add an alert
        
        Args:
            severity: 'info', 'warning', 'error', 'critical'
            message: Alert message
            category: Alert category (e.g., 'api', 'trading', 'risk')
        """
        alert = {
            'timestamp': datetime.now(),
            'severity': severity.upper(),
            'category': category,
            'message': message
        }
        
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Log based on severity
        log_msg = f"[{category.upper()}] {message}"
        if severity == 'critical' or severity == 'error':
            self.logger.error(log_msg)
        elif severity == 'warning':
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)
    
    def get_recent_alerts(self, count: int = 10, severity: str = None) -> List[Dict]:
        """Get recent alerts, optionally filtered by severity"""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity.upper()]
        
        return alerts[-count:]
    
    def get_alert_summary(self, minutes: int = 60) -> str:
        """Get summary of alerts in the last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent_alerts = [a for a in self.alerts if a['timestamp'] > cutoff]
        
        if not recent_alerts:
            return f"No alerts in the last {minutes} minutes"
        
        # Count by severity
        severity_counts = {}
        for alert in recent_alerts:
            severity = alert['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        summary = [f"Alerts in last {minutes} minutes:"]
        for severity in ['CRITICAL', 'ERROR', 'WARNING', 'INFO']:
            if severity in severity_counts:
                summary.append(f"  {severity}: {severity_counts[severity]}")
        
        return "\n".join(summary)
