"""
Advanced performance analytics and risk metrics
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from logger import Logger

class AdvancedAnalytics:
    """Calculate advanced risk and performance metrics"""
    
    def __init__(self, max_history_size: int = 10000):
        self.logger = Logger.get_logger()
        self.trade_history = []
        self.equity_curve = []
        self.max_history_size = max_history_size
    
    def record_trade(self, trade_data: Dict):
        """
        Record a trade for analytics
        
        Args:
            trade_data: Dict with trade info (entry, exit, pnl, duration, etc.)
        """
        self.trade_history.append({
            'timestamp': datetime.now(),
            'symbol': trade_data.get('symbol'),
            'side': trade_data.get('side'),
            'entry_price': trade_data.get('entry_price'),
            'exit_price': trade_data.get('exit_price'),
            'pnl': trade_data.get('pnl', 0),
            'pnl_pct': trade_data.get('pnl_pct', 0),
            'duration': trade_data.get('duration', 0),
            'leverage': trade_data.get('leverage', 1)
        })
        
        # MEMORY: Limit history size to prevent unbounded growth
        if len(self.trade_history) > self.max_history_size:
            self.trade_history = self.trade_history[-self.max_history_size:]
    
    def record_equity(self, balance: float):
        """Record current equity for curve tracking"""
        self.equity_curve.append({
            'timestamp': datetime.now(),
            'balance': balance
        })
        
        # MEMORY: Limit equity curve size to prevent unbounded growth
        if len(self.equity_curve) >= self.max_history_size:
            self.equity_curve = self.equity_curve[-self.max_history_size:]
    
    def calculate_sortino_ratio(self, risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sortino ratio (only penalizes downside volatility)
        
        Args:
            risk_free_rate: Annual risk-free rate (default 0%)
            
        Returns:
            Sortino ratio (higher is better)
        """
        if len(self.trade_history) < 10:
            return 0.0
        
        returns = [t['pnl_pct'] for t in self.trade_history]
        
        if not returns:
            return 0.0
        
        # Calculate average return
        avg_return = np.mean(returns)
        
        # Calculate downside deviation (only negative returns)
        downside_returns = [r for r in returns if r < 0]
        if not downside_returns:
            return float('inf')  # No losses
        
        downside_std = np.std(downside_returns)
        
        if downside_std == 0:
            return float('inf')
        
        # Annualize assuming 365 trading days
        trading_days_per_year = 365
        avg_trades_per_day = len(self.trade_history) / max(1, (datetime.now() - self.trade_history[0]['timestamp']).days)
        
        annualized_return = avg_return * avg_trades_per_day * trading_days_per_year
        annualized_downside_std = downside_std * np.sqrt(avg_trades_per_day * trading_days_per_year)
        
        sortino_ratio = (annualized_return - risk_free_rate) / annualized_downside_std
        
        return sortino_ratio
    
    def calculate_calmar_ratio(self, period_days: int = 365) -> float:
        """
        Calculate Calmar ratio (return / max drawdown)
        
        Args:
            period_days: Period for calculation (default 365 days)
            
        Returns:
            Calmar ratio (higher is better)
        """
        if len(self.equity_curve) < 2:
            return 0.0
        
        # Filter recent data
        cutoff_date = datetime.now() - timedelta(days=period_days)
        recent_equity = [e for e in self.equity_curve if e['timestamp'] >= cutoff_date]
        
        if len(recent_equity) < 2:
            recent_equity = self.equity_curve
        
        balances = [e['balance'] for e in recent_equity]
        
        # Calculate return
        initial_balance = balances[0]
        final_balance = balances[-1]
        
        # Defensive: Handle zero initial balance
        if initial_balance == 0:
            return 0.0
        
        total_return = (final_balance - initial_balance) / initial_balance
        
        # Calculate max drawdown
        peak = balances[0]
        max_dd = 0.0
        
        for balance in balances:
            if balance > peak:
                peak = balance
            # Handle zero peak: if peak is zero and balance > 0, treat drawdown as 100%
            if peak == 0:
                dd = 1.0 if balance > 0 else 0.0
            else:
                dd = (peak - balance) / peak
            if dd > max_dd:
                max_dd = dd
        
        if max_dd == 0:
            return float('inf')
        
        # Annualize return
        days_elapsed = max(1, (recent_equity[-1]['timestamp'] - recent_equity[0]['timestamp']).days)
        # SAFETY: Prevent division by zero in edge cases
        if days_elapsed <= 0:
            days_elapsed = 1
        annualized_return = total_return * (365 / days_elapsed)
        
        calmar_ratio = annualized_return / max_dd
        
        return calmar_ratio
    
    def calculate_information_ratio(self, benchmark_returns: List[float] = None) -> float:
        """
        Calculate Information ratio (excess return / tracking error)
        
        Args:
            benchmark_returns: List of benchmark returns (default: 0% risk-free)
            
        Returns:
            Information ratio (higher is better)
        """
        if len(self.trade_history) < 10:
            return 0.0
        
        returns = [t['pnl_pct'] for t in self.trade_history]
        
        if not returns:
            return 0.0
        
        # If no benchmark, use risk-free rate (0%)
        if benchmark_returns is None:
            benchmark_returns = [0.0] * len(returns)
        
        # Calculate excess returns
        excess_returns = [r - b for r, b in zip(returns, benchmark_returns[:len(returns)])]
        
        avg_excess_return = np.mean(excess_returns)
        tracking_error = np.std(excess_returns)
        
        # SAFETY: Guard against division by zero
        if tracking_error == 0 or np.isnan(tracking_error):
            return float('inf') if avg_excess_return > 0 else 0.0
        
        information_ratio = avg_excess_return / tracking_error
        
        return information_ratio
    
    def calculate_profit_factor(self) -> float:
        """
        Calculate profit factor (gross profit / gross loss)
        
        Returns:
            Profit factor (>1 is profitable)
        """
        if not self.trade_history:
            return 0.0
        
        gross_profit = sum(t['pnl'] for t in self.trade_history if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in self.trade_history if t['pnl'] < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def calculate_consecutive_wins_losses(self) -> Dict:
        """
        Calculate max consecutive wins and losses
        
        Returns:
            Dict with max consecutive wins and losses
        """
        if not self.trade_history:
            return {'max_wins': 0, 'max_losses': 0, 'current_streak': 0}
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in self.trade_history:
            if trade['pnl'] > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif trade['pnl'] < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        # Determine current streak
        if self.trade_history:
            last_trade = self.trade_history[-1]
            current_streak = current_wins if last_trade['pnl'] > 0 else -current_losses
        else:
            current_streak = 0
        
        return {
            'max_wins': max_wins,
            'max_losses': max_losses,
            'current_streak': current_streak
        }
    
    def calculate_recovery_factor(self) -> float:
        """
        Calculate recovery factor (net profit / max drawdown)
        
        Returns:
            Recovery factor (higher is better)
        """
        if not self.equity_curve or len(self.equity_curve) < 2:
            return 0.0
        
        balances = [e['balance'] for e in self.equity_curve]
        
        initial_balance = balances[0]
        final_balance = balances[-1]
        net_profit = final_balance - initial_balance
        
        # Calculate max drawdown in dollar terms
        peak = balances[0]
        max_dd_dollars = 0.0
        
        for balance in balances:
            if balance > peak:
                peak = balance
            dd = peak - balance
            if dd > max_dd_dollars:
                max_dd_dollars = dd
        
        if max_dd_dollars == 0:
            return float('inf') if net_profit > 0 else 0.0
        
        return net_profit / max_dd_dollars
    
    def calculate_ulcer_index(self) -> float:
        """
        Calculate Ulcer Index (measure of downside volatility)
        
        Returns:
            Ulcer Index (lower is better)
        """
        if not self.equity_curve or len(self.equity_curve) < 2:
            return 0.0
        
        balances = [e['balance'] for e in self.equity_curve]
        
        # Calculate percentage drawdown from peak for each point
        drawdowns = []
        peak = balances[0]
        
        for balance in balances:
            if balance > peak:
                peak = balance
            # Defensive: Handle zero peak to avoid division by zero
            if peak > 0:
                dd_pct = ((peak - balance) / peak) * 100
            else:
                dd_pct = 0.0
            drawdowns.append(dd_pct)
        
        # Ulcer Index is RMS of drawdowns
        ulcer_index = np.sqrt(np.mean([dd ** 2 for dd in drawdowns]))
        
        return ulcer_index
    
    def get_trade_distribution(self) -> Dict:
        """
        Analyze trade distribution by profit/loss ranges
        
        Returns:
            Dict with trade distribution stats
        """
        if not self.trade_history:
            return {}
        
        pnls = [t['pnl_pct'] * 100 for t in self.trade_history]  # Convert to percentage
        
        distribution = {
            'huge_wins': len([p for p in pnls if p > 5]),  # >5%
            'big_wins': len([p for p in pnls if 2 < p <= 5]),  # 2-5%
            'small_wins': len([p for p in pnls if 0 < p <= 2]),  # 0-2%
            'small_losses': len([p for p in pnls if -2 <= p < 0]),  # 0 to -2%
            'big_losses': len([p for p in pnls if -5 <= p < -2]),  # -2 to -5%
            'huge_losses': len([p for p in pnls if p < -5])  # <-5%
        }
        
        return distribution
    
    def get_comprehensive_metrics(self) -> Dict:
        """
        Get all advanced metrics in one call
        
        Returns:
            Dict with all calculated metrics
        """
        metrics = {
            'sortino_ratio': self.calculate_sortino_ratio(),
            'calmar_ratio': self.calculate_calmar_ratio(),
            'information_ratio': self.calculate_information_ratio(),
            'profit_factor': self.calculate_profit_factor(),
            'recovery_factor': self.calculate_recovery_factor(),
            'ulcer_index': self.calculate_ulcer_index(),
            'consecutive_stats': self.calculate_consecutive_wins_losses(),
            'trade_distribution': self.get_trade_distribution(),
            'total_trades': len(self.trade_history)
        }
        
        # Calculate additional basic metrics
        if self.trade_history:
            wins = [t for t in self.trade_history if t['pnl'] > 0]
            losses = [t for t in self.trade_history if t['pnl'] < 0]
            
            metrics['win_rate'] = len(wins) / len(self.trade_history) if self.trade_history else 0
            metrics['avg_win'] = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
            metrics['avg_loss'] = np.mean([t['pnl_pct'] for t in losses]) if losses else 0
            metrics['avg_duration_minutes'] = np.mean([t['duration'] for t in self.trade_history])
            
            if metrics['avg_loss'] != 0:
                metrics['risk_reward_ratio'] = abs(metrics['avg_win'] / metrics['avg_loss'])
            else:
                metrics['risk_reward_ratio'] = float('inf') if metrics['avg_win'] > 0 else 0
        
        return metrics
    
    def get_performance_summary(self) -> str:
        """
        Generate a human-readable performance summary
        
        Returns:
            Formatted string with performance metrics
        """
        metrics = self.get_comprehensive_metrics()
        
        summary = "\n" + "=" * 70 + "\n"
        summary += "ADVANCED PERFORMANCE ANALYTICS\n"
        summary += "=" * 70 + "\n"
        
        if metrics['total_trades'] == 0:
            summary += "No trades recorded yet.\n"
            return summary
        
        summary += f"\n📊 BASIC METRICS:\n"
        summary += f"  Total Trades: {metrics['total_trades']}\n"
        summary += f"  Win Rate: {metrics.get('win_rate', 0):.2%}\n"
        summary += f"  Avg Win: {metrics.get('avg_win', 0):.2%}\n"
        summary += f"  Avg Loss: {metrics.get('avg_loss', 0):.2%}\n"
        summary += f"  Risk/Reward: {metrics.get('risk_reward_ratio', 0):.2f}:1\n"
        summary += f"  Avg Duration: {metrics.get('avg_duration_minutes', 0):.1f} minutes\n"
        
        summary += f"\n📈 ADVANCED RISK METRICS:\n"
        summary += f"  Sortino Ratio: {metrics['sortino_ratio']:.2f} (>2 is excellent)\n"
        summary += f"  Calmar Ratio: {metrics['calmar_ratio']:.2f} (>3 is excellent)\n"
        summary += f"  Information Ratio: {metrics['information_ratio']:.2f} (>0.5 is good)\n"
        summary += f"  Profit Factor: {metrics['profit_factor']:.2f} (>1.5 is good)\n"
        summary += f"  Recovery Factor: {metrics['recovery_factor']:.2f} (>2 is good)\n"
        summary += f"  Ulcer Index: {metrics['ulcer_index']:.2f} (lower is better)\n"
        
        streak = metrics['consecutive_stats']
        summary += f"\n🔥 STREAK ANALYSIS:\n"
        summary += f"  Max Consecutive Wins: {streak['max_wins']}\n"
        summary += f"  Max Consecutive Losses: {streak['max_losses']}\n"
        summary += f"  Current Streak: {streak['current_streak']} "
        summary += f"({'wins' if streak['current_streak'] > 0 else 'losses'})\n"
        
        dist = metrics['trade_distribution']
        summary += f"\n📊 TRADE DISTRIBUTION:\n"
        summary += f"  Huge Wins (>5%): {dist.get('huge_wins', 0)}\n"
        summary += f"  Big Wins (2-5%): {dist.get('big_wins', 0)}\n"
        summary += f"  Small Wins (0-2%): {dist.get('small_wins', 0)}\n"
        summary += f"  Small Losses (0 to -2%): {dist.get('small_losses', 0)}\n"
        summary += f"  Big Losses (-2 to -5%): {dist.get('big_losses', 0)}\n"
        summary += f"  Huge Losses (<-5%): {dist.get('huge_losses', 0)}\n"
        
        summary += "=" * 70 + "\n"
        
        return summary
