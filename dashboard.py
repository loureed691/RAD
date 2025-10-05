"""
Web dashboard for live monitoring of the trading bot
"""
import json
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from logger import Logger

class BotDashboard:
    """Web dashboard for bot monitoring"""
    
    def __init__(self, port=5000):
        """Initialize the dashboard"""
        self.app = Flask(__name__)
        CORS(self.app)
        self.port = port
        self.logger = Logger.get_logger()
        
        # Shared data between bot and dashboard
        self.bot_data = {
            'status': 'initializing',
            'uptime': 0,
            'balance': 0.0,
            'open_positions': [],
            'trade_history': [],
            'performance': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0
            },
            'current_opportunities': [],
            'last_cycle': None,
            'config': {}
        }
        
        self.server_thread = None
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            """Get current bot status"""
            return jsonify({
                'status': self.bot_data['status'],
                'uptime': self.bot_data['uptime'],
                'balance': self.bot_data['balance'],
                'last_cycle': self.bot_data['last_cycle'],
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/positions')
        def get_positions():
            """Get open positions"""
            return jsonify({
                'positions': self.bot_data['open_positions'],
                'count': len(self.bot_data['open_positions'])
            })
        
        @self.app.route('/api/trades')
        def get_trades():
            """Get trade history"""
            limit = request.args.get('limit', 50, type=int)
            return jsonify({
                'trades': self.bot_data['trade_history'][-limit:],
                'total': len(self.bot_data['trade_history'])
            })
        
        @self.app.route('/api/performance')
        def get_performance():
            """Get performance metrics"""
            return jsonify(self.bot_data['performance'])
        
        @self.app.route('/api/opportunities')
        def get_opportunities():
            """Get current trading opportunities"""
            return jsonify({
                'opportunities': self.bot_data['current_opportunities']
            })
        
        @self.app.route('/api/config')
        def get_config():
            """Get bot configuration"""
            return jsonify(self.bot_data['config'])
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat()
            })
    
    def update_status(self, status: str):
        """Update bot status"""
        self.bot_data['status'] = status
        self.bot_data['last_cycle'] = datetime.now().isoformat()
    
    def update_balance(self, balance: float):
        """Update balance"""
        self.bot_data['balance'] = balance
    
    def update_positions(self, positions: list):
        """Update open positions"""
        self.bot_data['open_positions'] = positions
    
    def add_trade(self, trade: dict):
        """Add a completed trade to history"""
        trade['timestamp'] = datetime.now().isoformat()
        self.bot_data['trade_history'].append(trade)
        
        # Keep only last 500 trades in memory
        if len(self.bot_data['trade_history']) > 500:
            self.bot_data['trade_history'] = self.bot_data['trade_history'][-500:]
    
    def update_performance(self, metrics: dict):
        """Update performance metrics"""
        self.bot_data['performance'] = metrics
    
    def update_opportunities(self, opportunities: list):
        """Update current trading opportunities"""
        self.bot_data['current_opportunities'] = opportunities
    
    def update_config(self, config: dict):
        """Update bot configuration"""
        self.bot_data['config'] = config
    
    def update_uptime(self, seconds: float):
        """Update bot uptime"""
        self.bot_data['uptime'] = seconds
    
    def start(self):
        """Start the dashboard server in a separate thread"""
        def run_server():
            try:
                self.logger.info(f"🌐 Starting web dashboard on http://localhost:{self.port}")
                self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
            except Exception as e:
                self.logger.error(f"Dashboard error: {e}", exc_info=True)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.logger.info(f"✅ Dashboard started at http://localhost:{self.port}")
    
    def stop(self):
        """Stop the dashboard server"""
        # Flask doesn't have a clean shutdown method when running in thread
        # The daemon thread will stop when main program exits
        self.logger.info("🛑 Dashboard will stop with main program")
