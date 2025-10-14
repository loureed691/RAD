"""
Advanced Performance Metrics for 2026
Comprehensive performance tracking and analysis
"""
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from logger import Logger


class AdvancedPerformanceMetrics2026:
    """
    Institutional-grade performance metrics:
    - Sharpe Ratio (risk-adjusted returns)
    - Sortino Ratio (downside risk)
    - Calmar Ratio (return/max drawdown)
    - Maximum Drawdown tracking
    - Win/Loss streaks
    - Trade quality metrics
    - Profit factor
    - Expectancy
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        
        # Equity curve tracking
        self.equity_curve = []
        self.returns = []
        
        # Trade tracking
        self.trades = []
        
        # Drawdown tracking
        self.peak_equity = 0.0
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        self.drawdown_duration = timedelta(0)
        self.max_drawdown_duration = timedelta(0)
        self.in_drawdown_since = None
        
        # Risk-free rate (annual, for Sharpe calculation)
        self.risk_free_rate = 0.04  # 4% annual
        
        self.logger.info("📈 Advanced Performance Metrics 2026 initialized")
    
    def record_equity(self, equity: float, timestamp: Optional[datetime] = None):
        """
        Record equity value for performance tracking
        
        Args:
            equity: Current account equity
            timestamp: Time of recording (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': equity
        })
        
        # Calculate return if we have previous equity
        if len(self.equity_curve) > 1:
            prev_equity = self.equity_curve[-2]['equity']
            if prev_equity > 0:
                ret = (equity - prev_equity) / prev_equity
                self.returns.append(ret)
        
        # Update peak and drawdown
        if equity > self.peak_equity:
            self.peak_equity = equity
            if self.in_drawdown_since:
                # Exiting drawdown
                drawdown_length = timestamp - self.in_drawdown_since
                if drawdown_length > self.max_drawdown_duration:
                    self.max_drawdown_duration = drawdown_length
                self.in_drawdown_since = None
        else:
            # In drawdown
            if self.peak_equity > 0:
                self.current_drawdown = (self.peak_equity - equity) / self.peak_equity
                if self.current_drawdown > self.max_drawdown:
                    self.max_drawdown = self.current_drawdown
                
                if self.in_drawdown_since is None:
                    self.in_drawdown_since = timestamp
        
        # Trim old data (keep last 10000 points)
        if len(self.equity_curve) > 10000:
            self.equity_curve.pop(0)
        if len(self.returns) > 10000:
            self.returns.pop(0)
    
    def record_trade(self, entry_price: float, exit_price: float,
                    side: str, size: float, pnl: float,
                    entry_time: datetime, exit_time: datetime,
                    strategy: str = 'unknown'):
        """
        Record trade for analysis
        
        Args:
            entry_price: Entry price
            exit_price: Exit price
            side: 'long' or 'short'
            size: Position size
            pnl: Profit/Loss as decimal (0.05 = 5%)
            entry_time: Entry timestamp
            exit_time: Exit timestamp
            strategy: Strategy used
        """
        duration = (exit_time - entry_time).total_seconds() / 3600  # hours
        
        trade = {
            'entry_price': entry_price,
            'exit_price': exit_price,
            'side': side,
            'size': size,
            'pnl': pnl,
            'pnl_dollar': size * pnl,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'duration_hours': duration,
            'strategy': strategy
        }
        
        self.trades.append(trade)
        
        # Trim old trades (keep last 1000)
        if len(self.trades) > 1000:
            self.trades.pop(0)
    
    def calculate_sharpe_ratio(self, period_days: int = 30) -> float:
        """
        Calculate Sharpe Ratio (risk-adjusted return)
        
        Sharpe = (Mean Return - Risk Free Rate) / Std Dev of Returns
        
        Args:
            period_days: Period to calculate over (days)
            
        Returns:
            Sharpe Ratio (annualized)
        """
        if len(self.returns) < 2:
            return 0.0
        
        try:
            # Get returns for period
            num_points = min(len(self.returns), period_days * 24)  # Hourly data
            recent_returns = self.returns[-num_points:]
            
            if not recent_returns:
                return 0.0
            
            # Calculate mean return and std dev
            mean_return = np.mean(recent_returns)
            std_return = np.std(recent_returns)
            
            if std_return == 0:
                return 0.0
            
            # Annualize (assuming hourly returns)
            periods_per_year = 24 * 365
            annual_return = mean_return * periods_per_year
            annual_std = std_return * np.sqrt(periods_per_year)
            
            # Risk-free rate (daily)
            daily_rf = self.risk_free_rate / 365
            
            # Sharpe ratio
            sharpe = (annual_return - self.risk_free_rate) / annual_std
            
            return sharpe
            
        except Exception as e:
            self.logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0
    
    def calculate_sortino_ratio(self, period_days: int = 30) -> float:
        """
        Calculate Sortino Ratio (downside risk-adjusted return)
        
        Like Sharpe but only considers downside volatility
        
        Args:
            period_days: Period to calculate over (days)
            
        Returns:
            Sortino Ratio (annualized)
        """
        if len(self.returns) < 2:
            return 0.0
        
        try:
            # Get returns for period
            num_points = min(len(self.returns), period_days * 24)
            recent_returns = self.returns[-num_points:]
            
            if not recent_returns:
                return 0.0
            
            # Calculate mean return
            mean_return = np.mean(recent_returns)
            
            # Calculate downside deviation (only negative returns)
            negative_returns = [r for r in recent_returns if r < 0]
            
            if not negative_returns:
                return float('inf')  # No downside risk
            
            downside_std = np.std(negative_returns)
            
            if downside_std == 0:
                return 0.0
            
            # Annualize
            periods_per_year = 24 * 365
            annual_return = mean_return * periods_per_year
            annual_downside_std = downside_std * np.sqrt(periods_per_year)
            
            # Sortino ratio
            sortino = (annual_return - self.risk_free_rate) / annual_downside_std
            
            return sortino
            
        except Exception as e:
            self.logger.error(f"Error calculating Sortino ratio: {e}")
            return 0.0
    
    def calculate_calmar_ratio(self, period_days: int = 365) -> float:
        """
        Calculate Calmar Ratio (return / max drawdown)
        
        Args:
            period_days: Period to calculate over (days)
            
        Returns:
            Calmar Ratio
        """
        if len(self.equity_curve) < 2 or self.max_drawdown == 0:
            return 0.0
        
        try:
            # Get equity curve for period
            cutoff_time = datetime.now() - timedelta(days=period_days)
            period_equity = [
                e for e in self.equity_curve
                if e['timestamp'] > cutoff_time
            ]
            
            if len(period_equity) < 2:
                return 0.0
            
            # Calculate return
            start_equity = period_equity[0]['equity']
            end_equity = period_equity[-1]['equity']
            
            if start_equity == 0:
                return 0.0
            
            total_return = (end_equity - start_equity) / start_equity
            
            # Annualize return
            days_elapsed = (period_equity[-1]['timestamp'] - period_equity[0]['timestamp']).days
            if days_elapsed == 0:
                return 0.0
            
            annual_return = total_return * (365 / days_elapsed)
            
            # Calmar = annual return / max drawdown
            calmar = annual_return / self.max_drawdown if self.max_drawdown > 0 else 0.0
            
            return calmar
            
        except Exception as e:
            self.logger.error(f"Error calculating Calmar ratio: {e}")
            return 0.0
    
    def calculate_profit_factor(self) -> float:
        """
        Calculate profit factor (gross profit / gross loss)
        
        Returns:
            Profit factor (>1 is profitable)
        """
        if not self.trades:
            return 0.0
        
        winning_trades = [t['pnl_dollar'] for t in self.trades if t['pnl_dollar'] > 0]
        losing_trades = [abs(t['pnl_dollar']) for t in self.trades if t['pnl_dollar'] < 0]
        
        gross_profit = sum(winning_trades) if winning_trades else 0.0
        gross_loss = sum(losing_trades) if losing_trades else 0.0
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def calculate_expectancy(self) -> float:
        """
        Calculate expectancy (average $ per trade)
        
        Returns:
            Expected value per trade
        """
        if not self.trades:
            return 0.0
        
        total_pnl = sum(t['pnl_dollar'] for t in self.trades)
        return total_pnl / len(self.trades)
    
    def get_win_rate(self) -> float:
        """Calculate win rate from trades"""
        if not self.trades:
            return 0.0
        
        winners = sum(1 for t in self.trades if t['pnl'] > 0)
        return winners / len(self.trades)
    
    def get_avg_win_loss(self) -> Tuple[float, float]:
        """Get average win and loss percentages"""
        if not self.trades:
            return 0.0, 0.0
        
        winners = [t['pnl'] for t in self.trades if t['pnl'] > 0]
        losers = [abs(t['pnl']) for t in self.trades if t['pnl'] < 0]
        
        avg_win = np.mean(winners) if winners else 0.0
        avg_loss = np.mean(losers) if losers else 0.0
        
        return avg_win, avg_loss
    
    def get_comprehensive_metrics(self) -> Dict:
        """
        Get all performance metrics in one call
        
        Returns:
            Dictionary with all metrics
        """
        sharpe = self.calculate_sharpe_ratio()
        sortino = self.calculate_sortino_ratio()
        calmar = self.calculate_calmar_ratio()
        profit_factor = self.calculate_profit_factor()
        expectancy = self.calculate_expectancy()
        win_rate = self.get_win_rate()
        avg_win, avg_loss = self.get_avg_win_loss()
        
        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'win_rate': win_rate,
            'avg_win_pct': avg_win * 100,
            'avg_loss_pct': avg_loss * 100,
            'max_drawdown_pct': self.max_drawdown * 100,
            'current_drawdown_pct': self.current_drawdown * 100,
            'total_trades': len(self.trades),
            'peak_equity': self.peak_equity,
            'drawdown_duration_days': self.drawdown_duration.days if self.in_drawdown_since else 0,
            'max_drawdown_duration_days': self.max_drawdown_duration.days
        }
    
    def log_performance_report(self):
        """Log comprehensive performance report"""
        metrics = self.get_comprehensive_metrics()
        
        self.logger.info("=" * 60)
        self.logger.info("📊 PERFORMANCE METRICS REPORT")
        self.logger.info("=" * 60)
        self.logger.info(f"Sharpe Ratio:      {metrics['sharpe_ratio']:.2f}")
        self.logger.info(f"Sortino Ratio:     {metrics['sortino_ratio']:.2f}")
        self.logger.info(f"Calmar Ratio:      {metrics['calmar_ratio']:.2f}")
        self.logger.info(f"Profit Factor:     {metrics['profit_factor']:.2f}")
        self.logger.info(f"Expectancy:        ${metrics['expectancy']:.2f}")
        self.logger.info(f"Win Rate:          {metrics['win_rate']:.1%}")
        self.logger.info(f"Avg Win:           {metrics['avg_win_pct']:.2f}%")
        self.logger.info(f"Avg Loss:          {metrics['avg_loss_pct']:.2f}%")
        self.logger.info(f"Max Drawdown:      {metrics['max_drawdown_pct']:.2f}%")
        self.logger.info(f"Current Drawdown:  {metrics['current_drawdown_pct']:.2f}%")
        self.logger.info(f"Total Trades:      {metrics['total_trades']}")
        self.logger.info("=" * 60)
