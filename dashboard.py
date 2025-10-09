"""
Real-Time Trading Dashboard
Flask-based web interface for monitoring bot performance
"""
import os
from typing import Dict, List
from datetime import datetime, timedelta
from logger import Logger

try:
    from flask import Flask, render_template_string, jsonify
    import plotly
    import plotly.graph_objs as go
    import json
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Logger.get_logger().warning("Flask/Plotly not available. Dashboard features disabled.")

class TradingDashboard:
    """Real-time web dashboard for trading bot monitoring"""
    
    def __init__(self, port: int = 5000):
        self.logger = Logger.get_logger()
        self.port = port
        self.app = None
        self.stats = {}
        self.equity_data = []
        self.recent_trades = []
        
        if not FLASK_AVAILABLE:
            self.logger.warning("Dashboard features disabled (Flask not installed)")
            return
        
        self.setup_app()
    
    def setup_app(self):
        """Setup Flask application and routes"""
        if not FLASK_AVAILABLE:
            return
        
        self.app = Flask(__name__)
        
        # Dashboard HTML template
        dashboard_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>RAD Trading Bot Dashboard</title>
            <meta http-equiv="refresh" content="30">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                h1 {
                    color: #00ff88;
                    text-align: center;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .stat-card {
                    background: #2a2a2a;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }
                .stat-label {
                    color: #888;
                    font-size: 14px;
                    margin-bottom: 5px;
                }
                .stat-value {
                    font-size: 28px;
                    font-weight: bold;
                    color: #00ff88;
                }
                .stat-value.negative {
                    color: #ff4444;
                }
                .chart-container {
                    background: #2a2a2a;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }
                .trades-table {
                    width: 100%;
                    background: #2a2a2a;
                    border-radius: 8px;
                    padding: 20px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th {
                    background: #333;
                    padding: 12px;
                    text-align: left;
                    color: #00ff88;
                }
                td {
                    padding: 10px;
                    border-bottom: 1px solid #333;
                }
                .profit {
                    color: #00ff88;
                }
                .loss {
                    color: #ff4444;
                }
            </style>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <div class="container">
                <h1>🚀 RAD Trading Bot Dashboard</h1>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Balance</div>
                        <div class="stat-value">${{ stats.balance|default(0)|round(2) }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Total P&L</div>
                        <div class="stat-value {% if stats.total_pnl < 0 %}negative{% endif %}">
                            ${{ stats.total_pnl|default(0)|round(2) }}
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Win Rate</div>
                        <div class="stat-value">{{ (stats.win_rate|default(0) * 100)|round(1) }}%</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Total Trades</div>
                        <div class="stat-value">{{ stats.total_trades|default(0) }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Active Positions</div>
                        <div class="stat-value">{{ stats.active_positions|default(0) }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Sharpe Ratio</div>
                        <div class="stat-value">{{ stats.sharpe_ratio|default(0)|round(2) }}</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <h2>Equity Curve</h2>
                    <div id="equityChart"></div>
                </div>
                
                <div class="trades-table">
                    <h2>Recent Trades</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Entry</th>
                                <th>Exit</th>
                                <th>P&L</th>
                                <th>P&L %</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for trade in recent_trades %}
                            <tr>
                                <td>{{ trade.timestamp }}</td>
                                <td>{{ trade.symbol }}</td>
                                <td>{{ trade.side }}</td>
                                <td>{{ trade.entry_price|round(2) }}</td>
                                <td>{{ trade.exit_price|round(2) }}</td>
                                <td class="{% if trade.pnl >= 0 %}profit{% else %}loss{% endif %}">
                                    ${{ trade.pnl|round(2) }}
                                </td>
                                <td class="{% if trade.pnl_pct >= 0 %}profit{% else %}loss{% endif %}">
                                    {{ (trade.pnl_pct * 100)|round(2) }}%
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <script>
                // Equity curve chart
                var equityData = {{ equity_chart_data|safe }};
                Plotly.newPlot('equityChart', equityData.data, equityData.layout);
            </script>
        </body>
        </html>
        """
        
        @self.app.route('/')
        def dashboard():
            # Generate equity chart
            equity_chart = self.generate_equity_chart()
            
            return render_template_string(
                dashboard_html,
                stats=self.stats,
                recent_trades=self.recent_trades[-20:],  # Last 20 trades
                equity_chart_data=json.dumps(equity_chart)
            )
        
        @self.app.route('/api/stats')
        def api_stats():
            return jsonify(self.stats)
        
        @self.app.route('/api/trades')
        def api_trades():
            return jsonify(self.recent_trades[-50:])  # Last 50 trades
    
    def generate_equity_chart(self) -> Dict:
        """Generate Plotly equity curve chart"""
        if not self.equity_data:
            return {
                'data': [],
                'layout': {'title': 'No data available'}
            }
        
        timestamps = [point['timestamp'] for point in self.equity_data]
        balances = [point['balance'] for point in self.equity_data]
        
        trace = go.Scatter(
            x=timestamps,
            y=balances,
            mode='lines',
            name='Balance',
            line=dict(color='#00ff88', width=2)
        )
        
        layout = go.Layout(
            title='',
            xaxis=dict(title='Time', color='#ffffff'),
            yaxis=dict(title='Balance (USDT)', color='#ffffff'),
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#2a2a2a',
            font=dict(color='#ffffff')
        )
        
        return {
            'data': [trace],
            'layout': layout
        }
    
    def update_stats(self, stats: Dict):
        """Update dashboard statistics"""
        self.stats = stats
    
    def add_equity_point(self, balance: float, timestamp: datetime = None):
        """Add equity curve data point"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.equity_data.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'balance': balance
        })
        
        # Keep only last 1000 points
        if len(self.equity_data) > 1000:
            self.equity_data = self.equity_data[-1000:]
    
    def add_trade(self, trade: Dict):
        """Add recent trade to dashboard"""
        trade['timestamp'] = trade.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
        self.recent_trades.append(trade)
        
        # Keep only last 100 trades
        if len(self.recent_trades) > 100:
            self.recent_trades = self.recent_trades[-100:]
    
    def run(self, debug: bool = False, host: str = '0.0.0.0'):
        """Start dashboard server"""
        if not FLASK_AVAILABLE or not self.app:
            self.logger.error("Cannot start dashboard: Flask not available")
            return
        
        try:
            self.logger.info(f"Starting dashboard on http://{host}:{self.port}")
            self.app.run(host=host, port=self.port, debug=debug)
        except Exception as e:
            self.logger.error(f"Error starting dashboard: {e}")
