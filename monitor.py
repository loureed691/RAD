"""
Monitoring and statistics for the trading bot
"""
from typing import Dict, List
from datetime import datetime, timedelta
from logger import Logger

class Monitor:
    """Monitor bot performance and generate statistics"""

    def __init__(self):
        self.logger = Logger.get_logger()
        self.trades: List[Dict] = []
        self.start_time = datetime.now()
        self.initial_balance = 0.0

    def record_trade(self, symbol: str, side: str, entry_price: float,
                    exit_price: float, pnl: float, duration: timedelta):
        """Record a completed trade"""
        trade = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'duration': duration
        }
        self.trades.append(trade)
        profit_icon = "📈" if pnl > 0 else "📉"
        self.logger.info(f"{profit_icon} Recorded trade: {symbol} {side} P/L: {pnl:.2%}")

    def get_statistics(self) -> Dict:
        """Calculate performance statistics"""
        if not self.trades:
            return {}

        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        total_pnl = sum(t['pnl'] for t in self.trades)
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0

        # Calculate profit factor
        total_profit = sum(t['pnl'] for t in winning_trades)
        total_loss = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        # Calculate average trade duration
        avg_duration = sum((t['duration'].total_seconds() for t in self.trades), 0) / total_trades

        uptime = datetime.now() - self.start_time

        stats = {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'avg_duration_seconds': avg_duration,
            'uptime_seconds': uptime.total_seconds()
        }

        return stats

    def print_statistics(self):
        """Print formatted statistics"""
        stats = self.get_statistics()

        if not stats:
            self.logger.info("📊 No trades recorded yet")
            return

        self.logger.info("=" * 60)
        self.logger.info("📊 TRADING STATISTICS")
        self.logger.info("=" * 60)
        self.logger.info(f"📈 Total Trades: {stats['total_trades']}")
        self.logger.info(f"✅ Winning Trades: {stats['winning_trades']}")
        self.logger.info(f"❌ Losing Trades: {stats['losing_trades']}")
        self.logger.info(f"🎯 Win Rate: {stats['win_rate']:.1%}")
        self.logger.info(f"💰 Total P/L: {stats['total_pnl']:.2%}")
        self.logger.info(f"📊 Average Win: {stats['avg_win']:.2%}")
        self.logger.info(f"📉 Average Loss: {stats['avg_loss']:.2%}")
        self.logger.info(f"🔢 Profit Factor: {stats['profit_factor']:.2f}")
        self.logger.info(f"⏱️  Avg Trade Duration: {stats['avg_duration_seconds']/3600:.1f} hours")
        self.logger.info(f"⏰ Uptime: {stats['uptime_seconds']/3600:.1f} hours")
        self.logger.info("=" * 60)
