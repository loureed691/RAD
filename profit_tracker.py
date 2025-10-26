"""
Enhanced profit tracking and analytics for trading bot
Helps identify money loss issues and improve profitability
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from logger import Logger
import json
import os


class ProfitTracker:
    """Track and analyze profitability metrics to prevent money loss"""
    
    def __init__(self, data_file: str = 'logs/profit_tracking.json'):
        """Initialize profit tracker
        
        Args:
            data_file: Path to save profit tracking data
        """
        self.logger = Logger.get_logger()
        self.data_file = data_file
        
        # Trading statistics
        self.trades: List[Dict] = []
        self.daily_stats: Dict[str, Dict] = {}
        
        # Fee tracking
        self.total_fees_paid = 0.0
        self.total_volume_traded = 0.0
        
        # Profitability metrics
        self.total_gross_profit = 0.0  # Before fees
        self.total_net_profit = 0.0  # After fees
        self.winning_trades = 0
        self.losing_trades = 0
        self.breakeven_trades = 0
        
        # Load existing data
        self._load_data()
    
    def record_trade(self, symbol: str, side: str, entry_price: float, 
                    exit_price: float, amount: float, leverage: int,
                    entry_time: datetime, exit_time: datetime,
                    reason: str = '') -> Dict:
        """Record a completed trade with full details
        
        Args:
            symbol: Trading symbol
            side: 'long' or 'short'
            entry_price: Entry price
            exit_price: Exit price
            amount: Position size in contracts
            leverage: Leverage used
            entry_time: Entry timestamp
            exit_time: Exit timestamp
            reason: Reason for closing position
            
        Returns:
            Dict with trade statistics
        """
        # Calculate position value
        position_value = amount * entry_price
        
        # Calculate price movement
        if side == 'long':
            price_movement_pct = (exit_price - entry_price) / entry_price
        else:
            price_movement_pct = (entry_price - exit_price) / entry_price
        
        # Calculate fees (KuCoin: 0.06% taker on entry + 0.06% taker on exit)
        entry_fee = position_value * 0.0006
        exit_fee = (amount * exit_price) * 0.0006
        total_fees = entry_fee + exit_fee
        
        # Calculate P&L
        gross_pnl_usd = price_movement_pct * position_value * leverage
        net_pnl_usd = gross_pnl_usd - total_fees
        
        # ROI percentages
        gross_roi = price_movement_pct * leverage
        net_roi = net_pnl_usd / position_value
        
        # Trade duration
        duration_minutes = (exit_time - entry_time).total_seconds() / 60
        
        # Classify trade
        if net_roi > 0.001:  # >0.1% profit
            trade_result = 'win'
            self.winning_trades += 1
        elif net_roi < -0.001:  # >0.1% loss
            trade_result = 'loss'
            self.losing_trades += 1
        else:
            trade_result = 'breakeven'
            self.breakeven_trades += 1
        
        # Update totals
        self.total_fees_paid += total_fees
        self.total_volume_traded += position_value
        self.total_gross_profit += gross_pnl_usd
        self.total_net_profit += net_pnl_usd
        
        # Create trade record
        trade_record = {
            'timestamp': exit_time.isoformat(),
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'amount': amount,
            'leverage': leverage,
            'position_value_usd': position_value,
            'duration_minutes': duration_minutes,
            'price_movement_pct': price_movement_pct,
            'gross_pnl_usd': gross_pnl_usd,
            'fees_usd': total_fees,
            'net_pnl_usd': net_pnl_usd,
            'gross_roi': gross_roi,
            'net_roi': net_roi,
            'result': trade_result,
            'close_reason': reason
        }
        
        self.trades.append(trade_record)
        
        # Update daily statistics
        date_key = exit_time.date().isoformat()
        if date_key not in self.daily_stats:
            self.daily_stats[date_key] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'gross_profit': 0.0,
                'fees': 0.0,
                'net_profit': 0.0,
                'volume': 0.0
            }
        
        day_stats = self.daily_stats[date_key]
        day_stats['trades'] += 1
        day_stats['wins'] += 1 if trade_result == 'win' else 0
        day_stats['losses'] += 1 if trade_result == 'loss' else 0
        day_stats['gross_profit'] += gross_pnl_usd
        day_stats['fees'] += total_fees
        day_stats['net_profit'] += net_pnl_usd
        day_stats['volume'] += position_value
        
        # Log trade details
        self.logger.info(
            f"📊 Trade Recorded: {symbol} {side.upper()} - "
            f"Gross P/L: ${gross_pnl_usd:+.2f} ({gross_roi:+.2%}), "
            f"Fees: ${total_fees:.2f}, "
            f"Net P/L: ${net_pnl_usd:+.2f} ({net_roi:+.2%}), "
            f"Result: {trade_result.upper()}"
        )
        
        # Save data
        self._save_data()
        
        return trade_record
    
    def get_statistics(self, days: int = 7) -> Dict:
        """Get comprehensive profit statistics
        
        Args:
            days: Number of days to include in statistics
            
        Returns:
            Dict with profit statistics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent trades
        recent_trades = [
            t for t in self.trades 
            if datetime.fromisoformat(t['timestamp']) > cutoff_date
        ]
        
        if not recent_trades:
            return {
                'period_days': days,
                'total_trades': 0,
                'message': 'No trades in period'
            }
        
        # Calculate statistics
        total_trades = len(recent_trades)
        wins = sum(1 for t in recent_trades if t['result'] == 'win')
        losses = sum(1 for t in recent_trades if t['result'] == 'loss')
        
        total_gross = sum(t['gross_pnl_usd'] for t in recent_trades)
        total_fees = sum(t['fees_usd'] for t in recent_trades)
        total_net = sum(t['net_pnl_usd'] for t in recent_trades)
        total_volume = sum(t['position_value_usd'] for t in recent_trades)
        
        avg_gross = total_gross / total_trades if total_trades > 0 else 0
        avg_net = total_net / total_trades if total_trades > 0 else 0
        avg_fees = total_fees / total_trades if total_trades > 0 else 0
        
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        # Calculate average win/loss
        winning_trades = [t for t in recent_trades if t['result'] == 'win']
        losing_trades = [t for t in recent_trades if t['result'] == 'loss']
        
        avg_win = sum(t['net_pnl_usd'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['net_pnl_usd'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Profit factor
        total_wins_usd = sum(t['net_pnl_usd'] for t in winning_trades)
        total_losses_usd = abs(sum(t['net_pnl_usd'] for t in losing_trades))
        profit_factor = total_wins_usd / total_losses_usd if total_losses_usd > 0 else float('inf')
        
        # Fee impact analysis
        fee_percentage_of_gross = (total_fees / abs(total_gross)) * 100 if total_gross != 0 else 0
        
        return {
            'period_days': days,
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_gross_profit_usd': total_gross,
            'total_fees_usd': total_fees,
            'total_net_profit_usd': total_net,
            'total_volume_usd': total_volume,
            'avg_gross_profit_usd': avg_gross,
            'avg_fees_per_trade_usd': avg_fees,
            'avg_net_profit_usd': avg_net,
            'avg_win_usd': avg_win,
            'avg_loss_usd': avg_loss,
            'profit_factor': profit_factor,
            'fee_impact_pct': fee_percentage_of_gross
        }
    
    def print_report(self, days: int = 7):
        """Print comprehensive profit report
        
        Args:
            days: Number of days to include in report
        """
        stats = self.get_statistics(days)
        
        if stats['total_trades'] == 0:
            self.logger.info(f"📊 No trades in the last {days} days")
            return
        
        self.logger.info("=" * 80)
        self.logger.info(f"📊 PROFIT REPORT - Last {days} Days")
        self.logger.info("=" * 80)
        self.logger.info(f"Total Trades: {stats['total_trades']}")
        self.logger.info(f"Win Rate: {stats['win_rate']:.1%} ({stats['wins']} wins, {stats['losses']} losses)")
        self.logger.info(f"Profit Factor: {stats['profit_factor']:.2f}")
        self.logger.info("")
        self.logger.info(f"💰 Gross Profit: ${stats['total_gross_profit_usd']:+.2f}")
        self.logger.info(f"💸 Trading Fees: -${stats['total_fees_usd']:.2f} ({stats['fee_impact_pct']:.1f}% of gross)")
        self.logger.info(f"💵 Net Profit: ${stats['total_net_profit_usd']:+.2f}")
        self.logger.info("")
        self.logger.info(f"📈 Average Win: ${stats['avg_win_usd']:+.2f}")
        self.logger.info(f"📉 Average Loss: ${stats['avg_loss_usd']:+.2f}")
        self.logger.info(f"⚖️  Average Net P/L: ${stats['avg_net_profit_usd']:+.2f}")
        self.logger.info(f"💳 Average Fees/Trade: ${stats['avg_fees_per_trade_usd']:.2f}")
        self.logger.info("")
        self.logger.info(f"💼 Total Volume: ${stats['total_volume_usd']:.2f}")
        self.logger.info("=" * 80)
        
        # Warning if fees are eating too much profit
        if stats['fee_impact_pct'] > 50:
            self.logger.warning(
                f"⚠️  WARNING: Fees are consuming {stats['fee_impact_pct']:.1f}% of gross profit! "
                "Consider reducing trade frequency or increasing profit targets."
            )
    
    def _load_data(self):
        """Load profit tracking data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.trades = data.get('trades', [])
                    self.daily_stats = data.get('daily_stats', {})
                    self.total_fees_paid = data.get('total_fees_paid', 0.0)
                    self.total_volume_traded = data.get('total_volume_traded', 0.0)
                    self.total_gross_profit = data.get('total_gross_profit', 0.0)
                    self.total_net_profit = data.get('total_net_profit', 0.0)
                    self.winning_trades = data.get('winning_trades', 0)
                    self.losing_trades = data.get('losing_trades', 0)
                    self.breakeven_trades = data.get('breakeven_trades', 0)
                    self.logger.info(f"Loaded profit tracking data: {len(self.trades)} trades")
        except Exception as e:
            self.logger.error(f"Error loading profit tracking data: {e}")
    
    def _save_data(self):
        """Save profit tracking data to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            data = {
                'trades': self.trades,
                'daily_stats': self.daily_stats,
                'total_fees_paid': self.total_fees_paid,
                'total_volume_traded': self.total_volume_traded,
                'total_gross_profit': self.total_gross_profit,
                'total_net_profit': self.total_net_profit,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'breakeven_trades': self.breakeven_trades,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving profit tracking data: {e}")
