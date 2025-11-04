#!/usr/bin/env python3
"""
Example: Using the Enhanced Dashboard

This script demonstrates how to use the enhanced dashboard with all its new features.
The dashboard now includes comprehensive information about trading performance, positions,
risk metrics, strategy status, market conditions, and system health.
"""

from dashboard import TradingDashboard
from datetime import datetime, timedelta
import time
import random

def simulate_trading_data(dashboard):
    """Simulate realistic trading data for demonstration"""

    # Update performance statistics
    dashboard.update_stats({
        'balance': 12350.50,
        'initial_balance': 10000.00,
        'total_pnl': 2350.50,
        'win_rate': 0.78,
        'winning_trades': 39,
        'total_trades': 50,
        'active_positions': 2,
        'total_exposure': 7500.00,
        'sharpe_ratio': 2.8,
        'sortino_ratio': 3.5,
        'calmar_ratio': 2.1,
        'profit_factor': 2.65
    })

    # Update open positions
    dashboard.update_positions([
        {
            'symbol': 'BTC-USDT',
            'side': 'long',
            'entry_price': 67234.50,
            'current_price': 68125.30,
            'amount': 0.05,
            'leverage': 5,
            'unrealized_pnl': 44.54,
            'pnl_percent': 1.32,
            'stop_loss': 66500.00,
            'take_profit': 69000.00,
            'duration': '3h 45m'
        },
        {
            'symbol': 'ETH-USDT',
            'side': 'long',
            'entry_price': 3245.80,
            'current_price': 3312.15,
            'amount': 1.2,
            'leverage': 3,
            'unrealized_pnl': 79.62,
            'pnl_percent': 2.04,
            'stop_loss': 3180.00,
            'take_profit': 3400.00,
            'duration': '1h 22m'
        }
    ])

    # Update risk metrics
    dashboard.update_risk_metrics({
        'max_drawdown': 14.8,
        'current_drawdown': 2.3,
        'portfolio_heat': 0.32,
        'total_exposure': 7500.00,
        'available_capital': 4850.50,
        'daily_pnl': 287.35,
        'avg_volatility': 3.2
    })

    # Update strategy information
    dashboard.update_strategy_info({
        'active_strategy': 'Adaptive Momentum',
        'performance': 23.5
    })

    # Update market information
    dashboard.update_market_info({
        'regime': 'bull',
        'signal_strength': 0.82,
        'volatility': 'normal',
        'trend': 'upward',
        'last_signal': 'BUY ETH-USDT @ 3245.80'
    })

    # Update system status
    dashboard.update_system_status({
        'bot_active': True,
        'api_connected': True,
        'websocket_active': True,
        'last_trade_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'uptime': '8h 42m',
        'error_count': 3
    })

    # Add historical equity curve data
    base_time = datetime.now() - timedelta(hours=24)
    balance = 10000
    for i in range(48):
        balance += random.uniform(-50, 100)
        timestamp = base_time + timedelta(minutes=i*30)
        dashboard.add_equity_point(balance, timestamp)

    # Add drawdown data
    for i in range(48):
        drawdown = -random.uniform(0, 5)
        timestamp = base_time + timedelta(minutes=i*30)
        dashboard.add_drawdown_point(drawdown, timestamp)

    # Add some recent trades
    trades = [
        ('BTC-USDT', 'long', 66800.00, 67500.00, 0.05, 35.00, 0.0105, '2h 15m'),
        ('ETH-USDT', 'short', 3300.00, 3250.00, 1.5, 75.00, 0.0152, '1h 45m'),
        ('SOL-USDT', 'long', 142.50, 145.80, 20.0, 66.00, 0.0232, '3h 10m'),
    ]

    for i, (symbol, side, entry, exit, amount, pnl, pnl_pct, duration) in enumerate(trades):
        dashboard.add_trade({
            'symbol': symbol,
            'side': side,
            'entry_price': entry,
            'exit_price': exit,
            'amount': amount,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'duration': duration,
            'timestamp': (datetime.now() - timedelta(hours=i+1)).strftime('%Y-%m-%d %H:%M:%S')
        })


if __name__ == '__main__':
    print("Starting Enhanced RAD Trading Bot Dashboard...")
    print("=" * 80)

    # Create dashboard instance on port 5000
    dashboard = TradingDashboard(port=5000)

    # Populate with simulated trading data
    simulate_trading_data(dashboard)

    print("\n✓ Dashboard is ready with enhanced features:")
    print("  - 📊 Performance Overview (8 key metrics)")
    print("  - 💼 Open Positions (detailed position tracking)")
    print("  - 🛡️ Risk Metrics (comprehensive risk analysis)")
    print("  - 🎯 Strategy & Market (strategy and regime info)")
    print("  - 📈 Recent Trades (enhanced trade history)")
    print("  - ⚙️ System Status (bot health monitoring)")
    print("  - 📉 Charts (equity curve & drawdown)")
    print("\n✓ Open http://localhost:5000 in your browser")
    print("✓ Press Ctrl+C to stop\n")
    print("=" * 80)

    # Run the dashboard server
    try:
        dashboard.run(debug=False, host='0.0.0.0')
    except KeyboardInterrupt:
        print("\n\nDashboard stopped by user")
