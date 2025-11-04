"""
Prometheus Metrics Exporter

Exports trading bot metrics in Prometheus format for monitoring and alerting.

Features:
- Standard trading metrics (PnL, positions, orders)
- Performance metrics (latency, throughput)
- Custom business metrics
- HTTP endpoint for scraping
- Integration with Grafana
"""

from typing import Dict
from logger import Logger
import threading
import time

# Try to import prometheus client
try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
    from prometheus_client import CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Gauge = Histogram = None


class PrometheusMetrics:
    """
    Prometheus metrics exporter for trading bot.
    
    Exposes metrics via HTTP endpoint for Prometheus scraping.
    """
    
    def __init__(
        self,
        port: int = 8000,
        enable_http_server: bool = True
    ):
        """
        Initialize Prometheus metrics exporter.
        
        Args:
            port: HTTP port for metrics endpoint
            enable_http_server: Start HTTP server for scraping
        """
        self.port = port
        self.enable_http_server = enable_http_server
        self.logger = Logger.get_logger()
        self.server_started = False
        
        if not PROMETHEUS_AVAILABLE:
            self.logger.warning("⚠️  prometheus_client not installed - metrics disabled")
            self.enabled = False
            return
        
        self.enabled = True
        self.registry = CollectorRegistry()
        
        # Initialize metrics
        self._init_trading_metrics()
        self._init_performance_metrics()
        self._init_system_metrics()
        
        # Start HTTP server if enabled
        if enable_http_server:
            self._start_http_server()
        
        self.logger.info(f"📊 Prometheus Metrics initialized")
        if self.server_started:
            self.logger.info(f"   Metrics endpoint: http://localhost:{port}/metrics")
    
    def _init_trading_metrics(self):
        """Initialize trading-related metrics."""
        if not self.enabled:
            return
        
        # Counters
        self.trades_total = Counter(
            'trades_total',
            'Total number of trades executed',
            ['symbol', 'side'],
            registry=self.registry
        )
        
        self.orders_total = Counter(
            'orders_total',
            'Total number of orders placed',
            ['symbol', 'side', 'type'],
            registry=self.registry
        )
        
        self.orders_filled = Counter(
            'orders_filled',
            'Number of orders filled',
            ['symbol', 'side'],
            registry=self.registry
        )
        
        self.orders_cancelled = Counter(
            'orders_cancelled',
            'Number of orders cancelled',
            ['symbol'],
            registry=self.registry
        )
        
        # Gauges
        self.positions_open = Gauge(
            'positions_open',
            'Number of open positions',
            registry=self.registry
        )
        
        self.total_pnl = Gauge(
            'total_pnl_usd',
            'Total realized PnL in USD',
            registry=self.registry
        )
        
        self.unrealized_pnl = Gauge(
            'unrealized_pnl_usd',
            'Unrealized PnL in USD',
            registry=self.registry
        )
        
        self.account_balance = Gauge(
            'account_balance_usd',
            'Account balance in USD',
            registry=self.registry
        )
        
        self.position_size = Gauge(
            'position_size_usd',
            'Position size in USD',
            ['symbol', 'side'],
            registry=self.registry
        )
        
        self.win_rate = Gauge(
            'win_rate',
            'Percentage of winning trades',
            registry=self.registry
        )
        
        # Histograms
        self.trade_pnl = Histogram(
            'trade_pnl_usd',
            'Distribution of trade PnL',
            buckets=[-1000, -500, -100, -50, 0, 50, 100, 500, 1000, 5000],
            registry=self.registry
        )
        
        self.trade_duration = Histogram(
            'trade_duration_seconds',
            'Distribution of trade holding times',
            buckets=[60, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400],
            registry=self.registry
        )
    
    def _init_performance_metrics(self):
        """Initialize performance-related metrics."""
        if not self.enabled:
            return
        
        # Order execution latency
        self.order_latency = Histogram(
            'order_execution_latency_seconds',
            'Order execution latency',
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry
        )
        
        # API latency
        self.api_latency = Histogram(
            'api_request_latency_seconds',
            'API request latency',
            ['endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
            registry=self.registry
        )
        
        # Signal generation latency
        self.signal_latency = Histogram(
            'signal_generation_latency_seconds',
            'Time to generate trading signals',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry
        )
    
    def _init_system_metrics(self):
        """Initialize system-related metrics."""
        if not self.enabled:
            return
        
        self.errors_total = Counter(
            'errors_total',
            'Total number of errors',
            ['component', 'error_type'],
            registry=self.registry
        )
        
        self.uptime_seconds = Gauge(
            'uptime_seconds',
            'Bot uptime in seconds',
            registry=self.registry
        )
        
        self.loop_iterations = Counter(
            'loop_iterations_total',
            'Number of main loop iterations',
            registry=self.registry
        )
    
    def _start_http_server(self):
        """Start HTTP server for metrics endpoint."""
        if not self.enabled:
            return
        
        try:
            # Start server in background thread
            def run_server():
                try:
                    start_http_server(self.port, registry=self.registry)
                except Exception as e:
                    self.logger.error(f"Error starting Prometheus HTTP server: {e}")
            
            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            time.sleep(0.5)  # Give server time to start
            
            self.server_started = True
            
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus HTTP server: {e}")
    
    # Trading metrics methods
    def record_trade(self, symbol: str, side: str, pnl: float, duration_seconds: float):
        """Record a completed trade."""
        if not self.enabled:
            return
        
        self.trades_total.labels(symbol=symbol, side=side).inc()
        self.trade_pnl.observe(pnl)
        self.trade_duration.observe(duration_seconds)
    
    def record_order(self, symbol: str, side: str, order_type: str):
        """Record an order placement."""
        if not self.enabled:
            return
        
        self.orders_total.labels(symbol=symbol, side=side, type=order_type).inc()
    
    def record_order_fill(self, symbol: str, side: str):
        """Record an order fill."""
        if not self.enabled:
            return
        
        self.orders_filled.labels(symbol=symbol, side=side).inc()
    
    def record_order_cancel(self, symbol: str):
        """Record an order cancellation."""
        if not self.enabled:
            return
        
        self.orders_cancelled.labels(symbol=symbol).inc()
    
    def update_positions(self, num_positions: int):
        """Update number of open positions."""
        if not self.enabled:
            return
        
        self.positions_open.set(num_positions)
    
    def update_pnl(self, realized_pnl: float, unrealized_pnl: float):
        """Update PnL metrics."""
        if not self.enabled:
            return
        
        self.total_pnl.set(realized_pnl)
        self.unrealized_pnl.set(unrealized_pnl)
    
    def update_balance(self, balance: float):
        """Update account balance."""
        if not self.enabled:
            return
        
        self.account_balance.set(balance)
    
    def update_position_size(self, symbol: str, side: str, size_usd: float):
        """Update position size for a symbol."""
        if not self.enabled:
            return
        
        self.position_size.labels(symbol=symbol, side=side).set(size_usd)
    
    def update_win_rate(self, win_rate: float):
        """Update win rate percentage."""
        if not self.enabled:
            return
        
        self.win_rate.set(win_rate)
    
    # Performance metrics methods
    def record_order_latency(self, latency_seconds: float):
        """Record order execution latency."""
        if not self.enabled:
            return
        
        self.order_latency.observe(latency_seconds)
    
    def record_api_latency(self, endpoint: str, latency_seconds: float):
        """Record API request latency."""
        if not self.enabled:
            return
        
        self.api_latency.labels(endpoint=endpoint).observe(latency_seconds)
    
    def record_signal_latency(self, latency_seconds: float):
        """Record signal generation latency."""
        if not self.enabled:
            return
        
        self.signal_latency.observe(latency_seconds)
    
    # System metrics methods
    def record_error(self, component: str, error_type: str):
        """Record an error."""
        if not self.enabled:
            return
        
        self.errors_total.labels(component=component, error_type=error_type).inc()
    
    def update_uptime(self, uptime_seconds: float):
        """Update bot uptime."""
        if not self.enabled:
            return
        
        self.uptime_seconds.set(uptime_seconds)
    
    def increment_loop(self):
        """Increment main loop counter."""
        if not self.enabled:
            return
        
        self.loop_iterations.inc()
    
    def get_metrics_text(self) -> str:
        """
        Get metrics in Prometheus text format.
        
        Returns:
            Metrics as text string
        """
        if not self.enabled:
            return "# Prometheus metrics disabled"
        
        return generate_latest(self.registry).decode('utf-8')
    
    def get_status(self) -> Dict:
        """
        Get metrics exporter status.
        
        Returns:
            Dictionary with status info
        """
        return {
            'enabled': self.enabled,
            'prometheus_available': PROMETHEUS_AVAILABLE,
            'http_server_enabled': self.enable_http_server,
            'http_server_started': self.server_started,
            'port': self.port,
            'endpoint': f'http://localhost:{self.port}/metrics' if self.server_started else None
        }


# Example Grafana dashboard JSON configuration
GRAFANA_DASHBOARD_CONFIG = '''
{
  "dashboard": {
    "title": "Trading Bot Metrics",
    "panels": [
      {
        "title": "Total PnL",
        "type": "graph",
        "targets": [
          {
            "expr": "total_pnl_usd"
          }
        ]
      },
      {
        "title": "Open Positions",
        "type": "stat",
        "targets": [
          {
            "expr": "positions_open"
          }
        ]
      },
      {
        "title": "Win Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "win_rate"
          }
        ]
      },
      {
        "title": "Trades by Symbol",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(trades_total[5m])"
          }
        ]
      },
      {
        "title": "Order Latency",
        "type": "heatmap",
        "targets": [
          {
            "expr": "order_execution_latency_seconds"
          }
        ]
      }
    ]
  }
}
'''
