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
        self.open_positions = []
        self.risk_metrics = {}
        self.strategy_info = {}
        self.market_info = {}
        self.system_status = {}
        self.drawdown_data = []
        
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
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #0f0f0f;
                    color: #ffffff;
                }
                .container {
                    max-width: 1800px;
                    margin: 0 auto;
                }
                h1 {
                    color: #00ff88;
                    text-align: center;
                    margin-bottom: 10px;
                    font-size: 36px;
                    text-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
                }
                .subtitle {
                    text-align: center;
                    color: #888;
                    margin-bottom: 30px;
                    font-size: 14px;
                }
                h2 {
                    color: #00ff88;
                    font-size: 22px;
                    margin-top: 0;
                    margin-bottom: 15px;
                    border-bottom: 2px solid #00ff88;
                    padding-bottom: 8px;
                }
                h3 {
                    color: #00ccff;
                    font-size: 18px;
                    margin-top: 0;
                    margin-bottom: 12px;
                }
                .section {
                    background: #1a1a1a;
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 25px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.4);
                    border: 1px solid #2a2a2a;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 30px;
                }
                .stat-card {
                    background: linear-gradient(135deg, #2a2a2a 0%, #1f1f1f 100%);
                    padding: 18px;
                    border-radius: 10px;
                    box-shadow: 0 3px 6px rgba(0,0,0,0.3);
                    border: 1px solid #333;
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                .stat-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 12px rgba(0,255,136,0.2);
                }
                .stat-label {
                    color: #888;
                    font-size: 13px;
                    margin-bottom: 8px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .stat-value {
                    font-size: 26px;
                    font-weight: bold;
                    color: #00ff88;
                }
                .stat-value.negative {
                    color: #ff4444;
                }
                .stat-value.warning {
                    color: #ffaa00;
                }
                .stat-value.info {
                    color: #00ccff;
                }
                .stat-subvalue {
                    font-size: 12px;
                    color: #666;
                    margin-top: 5px;
                }
                .chart-container {
                    background: #1a1a1a;
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    border: 1px solid #2a2a2a;
                }
                .two-column {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 25px;
                    margin-bottom: 25px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }
                th {
                    background: #252525;
                    padding: 14px 12px;
                    text-align: left;
                    color: #00ff88;
                    font-weight: 600;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    border-bottom: 2px solid #00ff88;
                }
                td {
                    padding: 12px;
                    border-bottom: 1px solid #2a2a2a;
                    font-size: 14px;
                }
                tr:hover {
                    background: #222;
                }
                .profit {
                    color: #00ff88;
                    font-weight: 600;
                }
                .loss {
                    color: #ff4444;
                    font-weight: 600;
                }
                .badge {
                    display: inline-block;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .badge.long {
                    background: #00ff8833;
                    color: #00ff88;
                    border: 1px solid #00ff88;
                }
                .badge.short {
                    background: #ff444433;
                    color: #ff4444;
                    border: 1px solid #ff4444;
                }
                .badge.active {
                    background: #00ccff33;
                    color: #00ccff;
                    border: 1px solid #00ccff;
                }
                .badge.bull {
                    background: #00ff8833;
                    color: #00ff88;
                }
                .badge.bear {
                    background: #ff444433;
                    color: #ff4444;
                }
                .badge.neutral {
                    background: #ffaa0033;
                    color: #ffaa00;
                }
                .status-indicator {
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    margin-right: 8px;
                    animation: pulse 2s infinite;
                }
                .status-indicator.online {
                    background: #00ff88;
                }
                .status-indicator.offline {
                    background: #ff4444;
                }
                .status-indicator.warning {
                    background: #ffaa00;
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                .info-grid {
                    display: grid;
                    grid-template-columns: auto 1fr;
                    gap: 12px 20px;
                    font-size: 14px;
                }
                .info-label {
                    color: #888;
                    font-weight: 600;
                }
                .info-value {
                    color: #fff;
                }
                .no-data {
                    text-align: center;
                    color: #666;
                    padding: 30px;
                    font-style: italic;
                }
                @media (max-width: 1200px) {
                    .two-column {
                        grid-template-columns: 1fr;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 RAD Trading Bot Dashboard</h1>
                <div class="subtitle">
                    <span class="status-indicator {% if system_status.bot_active %}online{% else %}offline{% endif %}"></span>
                    Last Updated: {{ system_status.last_update|default('N/A') }}
                </div>
                
                <!-- Performance Overview -->
                <div class="section">
                    <h2>📊 Performance Overview</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Balance</div>
                            <div class="stat-value">${{ stats.balance|default(0)|round(2) }}</div>
                            <div class="stat-subvalue">Initial: ${{ stats.initial_balance|default(0)|round(2) }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Total P&L</div>
                            <div class="stat-value {% if stats.total_pnl|default(0) < 0 %}negative{% endif %}">
                                ${{ stats.total_pnl|default(0)|round(2) }}
                            </div>
                            <div class="stat-subvalue">{{ ((stats.total_pnl|default(0) / stats.initial_balance|default(1)) * 100)|round(2) }}% ROI</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Win Rate</div>
                            <div class="stat-value">{{ (stats.win_rate|default(0) * 100)|round(1) }}%</div>
                            <div class="stat-subvalue">{{ stats.winning_trades|default(0) }}/{{ stats.total_trades|default(0) }} trades</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Active Positions</div>
                            <div class="stat-value info">{{ stats.active_positions|default(0) }}</div>
                            <div class="stat-subvalue">Exposure: ${{ stats.total_exposure|default(0)|round(2) }}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Sharpe Ratio</div>
                            <div class="stat-value">{{ stats.sharpe_ratio|default(0)|round(2) }}</div>
                            <div class="stat-subvalue">Risk-adjusted return</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Sortino Ratio</div>
                            <div class="stat-value">{{ stats.sortino_ratio|default(0)|round(2) }}</div>
                            <div class="stat-subvalue">Downside risk metric</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Calmar Ratio</div>
                            <div class="stat-value">{{ stats.calmar_ratio|default(0)|round(2) }}</div>
                            <div class="stat-subvalue">Return vs drawdown</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Profit Factor</div>
                            <div class="stat-value {% if stats.profit_factor|default(0) < 1 %}negative{% elif stats.profit_factor|default(0) >= 2 %}positive{% endif %}">
                                {{ stats.profit_factor|default(0)|round(2) }}
                            </div>
                            <div class="stat-subvalue">Win/Loss ratio</div>
                        </div>
                    </div>
                </div>
                
                <!-- Charts -->
                <div class="two-column">
                    <div class="chart-container">
                        <h3>Equity Curve</h3>
                        {{ equity_chart_html|safe }}
                    </div>
                    <div class="chart-container">
                        <h3>Drawdown</h3>
                        {{ drawdown_chart_html|safe }}
                    </div>
                </div>
                
                <!-- Open Positions -->
                <div class="section">
                    <h2>💼 Open Positions</h2>
                    {% if open_positions %}
                    <table>
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Entry Price</th>
                                <th>Current Price</th>
                                <th>Amount</th>
                                <th>Leverage</th>
                                <th>Unrealized P&L</th>
                                <th>P&L %</th>
                                <th>Stop Loss</th>
                                <th>Take Profit</th>
                                <th>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for pos in open_positions %}
                            <tr>
                                <td><strong>{{ pos.symbol }}</strong></td>
                                <td><span class="badge {{ pos.side }}">{{ pos.side }}</span></td>
                                <td>${{ pos.entry_price|round(4) }}</td>
                                <td>${{ pos.current_price|default(0)|round(4) }}</td>
                                <td>{{ pos.amount|round(4) }}</td>
                                <td>{{ pos.leverage }}x</td>
                                <td class="{% if pos.unrealized_pnl|default(0) >= 0 %}profit{% else %}loss{% endif %}">
                                    ${{ pos.unrealized_pnl|default(0)|round(2) }}
                                </td>
                                <td class="{% if pos.pnl_percent|default(0) >= 0 %}profit{% else %}loss{% endif %}">
                                    {{ pos.pnl_percent|default(0)|round(2) }}%
                                </td>
                                <td>${{ pos.stop_loss|round(4) }}</td>
                                <td>{% if pos.take_profit %}${{ pos.take_profit|round(4) }}{% else %}N/A{% endif %}</td>
                                <td>{{ pos.duration|default('N/A') }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <div class="no-data">No open positions</div>
                    {% endif %}
                </div>
                
                <!-- Risk Metrics & Strategy Info -->
                <div class="two-column">
                    <div class="section">
                        <h2>🛡️ Risk Metrics</h2>
                        <div class="info-grid">
                            <div class="info-label">Max Drawdown:</div>
                            <div class="info-value">
                                <span class="{% if risk_metrics.max_drawdown|default(0) > 15 %}loss{% elif risk_metrics.max_drawdown|default(0) > 10 %}warning{% endif %}">
                                    {{ risk_metrics.max_drawdown|default(0)|round(2) }}%
                                </span>
                            </div>
                            <div class="info-label">Current Drawdown:</div>
                            <div class="info-value">
                                <span class="{% if risk_metrics.current_drawdown|default(0) > 10 %}loss{% elif risk_metrics.current_drawdown|default(0) > 5 %}warning{% endif %}">
                                    {{ risk_metrics.current_drawdown|default(0)|round(2) }}%
                                </span>
                            </div>
                            <div class="info-label">Portfolio Heat:</div>
                            <div class="info-value">
                                <span class="{% if risk_metrics.portfolio_heat|default(0) > 0.5 %}loss{% elif risk_metrics.portfolio_heat|default(0) > 0.3 %}warning{% endif %}">
                                    {{ (risk_metrics.portfolio_heat|default(0) * 100)|round(1) }}%
                                </span>
                            </div>
                            <div class="info-label">Total Exposure:</div>
                            <div class="info-value">${{ risk_metrics.total_exposure|default(0)|round(2) }}</div>
                            <div class="info-label">Available Capital:</div>
                            <div class="info-value">${{ risk_metrics.available_capital|default(0)|round(2) }}</div>
                            <div class="info-label">Daily P&L:</div>
                            <div class="info-value">
                                <span class="{% if risk_metrics.daily_pnl|default(0) >= 0 %}profit{% else %}loss{% endif %}">
                                    ${{ risk_metrics.daily_pnl|default(0)|round(2) }}
                                </span>
                            </div>
                            <div class="info-label">Volatility (ATR):</div>
                            <div class="info-value">{{ risk_metrics.avg_volatility|default(0)|round(2) }}%</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>🎯 Strategy & Market</h2>
                        <div class="info-grid">
                            <div class="info-label">Active Strategy:</div>
                            <div class="info-value">
                                <span class="badge active">{{ strategy_info.active_strategy|default('N/A') }}</span>
                            </div>
                            <div class="info-label">Market Regime:</div>
                            <div class="info-value">
                                <span class="badge {{ market_info.regime|default('neutral') }}">
                                    {{ market_info.regime|default('Unknown')|upper }}
                                </span>
                            </div>
                            <div class="info-label">Strategy Performance:</div>
                            <div class="info-value">
                                <span class="{% if strategy_info.performance|default(0) >= 0 %}profit{% else %}loss{% endif %}">
                                    {{ strategy_info.performance|default(0)|round(2) }}%
                                </span>
                            </div>
                            <div class="info-label">Signal Strength:</div>
                            <div class="info-value">{{ (market_info.signal_strength|default(0) * 100)|round(0) }}%</div>
                            <div class="info-label">Market Volatility:</div>
                            <div class="info-value">
                                <span class="{% if market_info.volatility|default('normal') == 'high' %}warning{% endif %}">
                                    {{ market_info.volatility|default('Normal')|upper }}
                                </span>
                            </div>
                            <div class="info-label">Trend Direction:</div>
                            <div class="info-value">{{ market_info.trend|default('Neutral')|title }}</div>
                            <div class="info-label">Last Signal:</div>
                            <div class="info-value">{{ market_info.last_signal|default('N/A') }}</div>
                        </div>
                    </div>
                </div>
                
                <!-- Recent Trades -->
                <div class="section">
                    <h2>📈 Recent Trades</h2>
                    {% if recent_trades %}
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Entry Price</th>
                                <th>Exit Price</th>
                                <th>Amount</th>
                                <th>P&L</th>
                                <th>P&L %</th>
                                <th>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for trade in recent_trades %}
                            <tr>
                                <td>{{ trade.timestamp }}</td>
                                <td><strong>{{ trade.symbol }}</strong></td>
                                <td><span class="badge {{ trade.side }}">{{ trade.side }}</span></td>
                                <td>${{ trade.entry_price|round(4) }}</td>
                                <td>${{ trade.exit_price|round(4) }}</td>
                                <td>{{ trade.amount|default(0)|round(4) }}</td>
                                <td class="{% if trade.pnl >= 0 %}profit{% else %}loss{% endif %}">
                                    ${{ trade.pnl|round(2) }}
                                </td>
                                <td class="{% if trade.pnl_pct >= 0 %}profit{% else %}loss{% endif %}">
                                    {{ (trade.pnl_pct * 100)|round(2) }}%
                                </td>
                                <td>{{ trade.duration|default('N/A') }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <div class="no-data">No trades yet</div>
                    {% endif %}
                </div>
                
                <!-- System Status -->
                <div class="section">
                    <h2>⚙️ System Status</h2>
                    <div class="info-grid">
                        <div class="info-label">Bot Status:</div>
                        <div class="info-value">
                            <span class="status-indicator {% if system_status.bot_active %}online{% else %}offline{% endif %}"></span>
                            {{ 'Active' if system_status.bot_active else 'Inactive' }}
                        </div>
                        <div class="info-label">API Connection:</div>
                        <div class="info-value">
                            <span class="status-indicator {% if system_status.api_connected %}online{% else %}offline{% endif %}"></span>
                            {{ 'Connected' if system_status.api_connected else 'Disconnected' }}
                        </div>
                        <div class="info-label">WebSocket Status:</div>
                        <div class="info-value">
                            <span class="status-indicator {% if system_status.websocket_active %}online{% else %}offline{% endif %}"></span>
                            {{ 'Active' if system_status.websocket_active else 'Inactive' }}
                        </div>
                        <div class="info-label">Last Trade:</div>
                        <div class="info-value">{{ system_status.last_trade_time|default('N/A') }}</div>
                        <div class="info-label">Uptime:</div>
                        <div class="info-value">{{ system_status.uptime|default('N/A') }}</div>
                        <div class="info-label">Error Count (24h):</div>
                        <div class="info-value">
                            <span class="{% if system_status.error_count|default(0) > 10 %}loss{% elif system_status.error_count|default(0) > 5 %}warning{% endif %}">
                                {{ system_status.error_count|default(0) }}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        @self.app.route('/')
        def dashboard():
            # Generate equity and drawdown charts as HTML
            equity_chart_html = self.generate_equity_chart_html()
            drawdown_chart_html = self.generate_drawdown_chart_html()
            
            return render_template_string(
                dashboard_html,
                stats=self.stats,
                recent_trades=self.recent_trades[-20:],  # Last 20 trades
                equity_chart_html=equity_chart_html,
                drawdown_chart_html=drawdown_chart_html,
                open_positions=self.open_positions,
                risk_metrics=self.risk_metrics,
                strategy_info=self.strategy_info,
                market_info=self.market_info,
                system_status=self.system_status
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
        
        return {
            'data': [{
                'x': timestamps,
                'y': balances,
                'mode': 'lines',
                'name': 'Balance',
                'type': 'scatter',
                'line': {'color': '#00ff88', 'width': 2}
            }],
            'layout': {
                'title': '',
                'xaxis': {'title': 'Time', 'color': '#ffffff'},
                'yaxis': {'title': 'Balance (USDT)', 'color': '#ffffff'},
                'plot_bgcolor': '#1a1a1a',
                'paper_bgcolor': '#2a2a2a',
                'font': {'color': '#ffffff'},
                'margin': {'l': 50, 'r': 20, 't': 20, 'b': 50}
            }
        }
    
    def generate_equity_chart_html(self) -> str:
        """Generate Plotly equity curve chart as HTML"""
        if not self.equity_data:
            return '<div class="no-data">No equity data available</div>'
        
        timestamps = [point['timestamp'] for point in self.equity_data]
        balances = [point['balance'] for point in self.equity_data]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=balances,
            mode='lines',
            name='Balance',
            line=dict(color='#00ff88', width=2)
        ))
        
        fig.update_layout(
            xaxis=dict(title='Time', color='#ffffff', gridcolor='#333'),
            yaxis=dict(title='Balance (USDT)', color='#ffffff', gridcolor='#333'),
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='#ffffff'),
            margin=dict(l=50, r=20, t=20, b=50),
            height=300,
            hovermode='x unified'
        )
        
        # Generate HTML with Plotly.js embedded (self-contained, no CDN)
        return fig.to_html(include_plotlyjs=True, full_html=False, config={'responsive': True})
    
    def generate_drawdown_chart_html(self) -> str:
        """Generate Plotly drawdown chart as HTML"""
        if not self.drawdown_data:
            return '<div class="no-data">No drawdown data available</div>'
        
        timestamps = [point['timestamp'] for point in self.drawdown_data]
        drawdowns = [point['drawdown'] for point in self.drawdown_data]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=drawdowns,
            mode='lines',
            name='Drawdown',
            line=dict(color='#ff4444', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 68, 68, 0.2)'
        ))
        
        fig.update_layout(
            xaxis=dict(title='Time', color='#ffffff', gridcolor='#333'),
            yaxis=dict(title='Drawdown (%)', color='#ffffff', gridcolor='#333'),
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#1a1a1a',
            font=dict(color='#ffffff'),
            margin=dict(l=50, r=20, t=20, b=50),
            height=300,
            hovermode='x unified'
        )
        
        # Generate HTML without Plotly.js (already included by first chart)
        return fig.to_html(include_plotlyjs=False, full_html=False, config={'responsive': True})
    
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
        if 'timestamp' not in trade:
            trade['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(trade['timestamp'], datetime):
            trade['timestamp'] = trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        # If it's already a string, leave it as is
        
        self.recent_trades.append(trade)
        
        # Keep only last 100 trades
        if len(self.recent_trades) > 100:
            self.recent_trades = self.recent_trades[-100:]
    
    def generate_drawdown_chart(self) -> Dict:
        """Generate Plotly drawdown chart"""
        if not self.drawdown_data:
            return {
                'data': [],
                'layout': {'title': 'No data available'}
            }
        
        timestamps = [point['timestamp'] for point in self.drawdown_data]
        drawdowns = [point['drawdown'] for point in self.drawdown_data]
        
        return {
            'data': [{
                'x': timestamps,
                'y': drawdowns,
                'mode': 'lines',
                'name': 'Drawdown',
                'type': 'scatter',
                'line': {'color': '#ff4444', 'width': 2},
                'fill': 'tozeroy',
                'fillcolor': 'rgba(255, 68, 68, 0.2)'
            }],
            'layout': {
                'title': '',
                'xaxis': {'title': 'Time', 'color': '#ffffff'},
                'yaxis': {'title': 'Drawdown (%)', 'color': '#ffffff'},
                'plot_bgcolor': '#1a1a1a',
                'paper_bgcolor': '#2a2a2a',
                'font': {'color': '#ffffff'},
                'margin': {'l': 50, 'r': 20, 't': 20, 'b': 50}
            }
        }
    
    def update_positions(self, positions: List[Dict]):
        """Update open positions"""
        self.open_positions = positions
    
    def update_risk_metrics(self, metrics: Dict):
        """Update risk metrics"""
        self.risk_metrics = metrics
    
    def update_strategy_info(self, info: Dict):
        """Update strategy information"""
        self.strategy_info = info
    
    def update_market_info(self, info: Dict):
        """Update market information"""
        self.market_info = info
    
    def update_system_status(self, status: Dict):
        """Update system status"""
        status['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.system_status = status
    
    def add_drawdown_point(self, drawdown: float, timestamp: datetime = None):
        """Add drawdown data point"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.drawdown_data.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'drawdown': drawdown
        })
        
        # Keep only last 1000 points
        if len(self.drawdown_data) > 1000:
            self.drawdown_data = self.drawdown_data[-1000:]
    
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
