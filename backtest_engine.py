"""
Enhanced Backtesting Engine with Walk-Forward Optimization
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from logger import Logger

class BacktestEngine:
    """Advanced backtesting engine for strategy validation"""
    
    def __init__(self, initial_balance: float = 10000):
        self.logger = Logger.get_logger()
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = []
        self.closed_trades = []
        self.equity_curve = []
    
    def reset(self):
        """Reset backtesting state"""
        self.balance = self.initial_balance
        self.positions = []
        self.closed_trades = []
        self.equity_curve = []
    
    def run_backtest(self, data: pd.DataFrame, strategy_func,
                    initial_balance: float = None) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            data: DataFrame with OHLCV and indicator data
            strategy_func: Function that takes (row, balance, positions) and returns signal
            initial_balance: Starting balance (overrides init value if provided)
        
        Returns:
            Backtest results dictionary
        """
        if initial_balance:
            self.initial_balance = initial_balance
        
        self.reset()
        
        try:
            self.logger.info(f"Starting backtest with {len(data)} candles")
            
            for idx, row in data.iterrows():
                # Update equity curve
                current_equity = self.calculate_equity(row['close'])
                self.equity_curve.append({
                    'timestamp': row.get('timestamp', idx),
                    'balance': self.balance,
                    'equity': current_equity
                })
                
                # Check for position exits first
                self.check_exits(row)
                
                # Get signal from strategy
                signal = strategy_func(row, self.balance, self.positions)
                
                # Execute signal
                if signal and signal != 'HOLD':
                    self.execute_signal(signal, row)
            
            # Close any remaining positions at end
            if self.positions:
                final_row = data.iloc[-1]
                for pos in self.positions[:]:
                    self.close_position(pos, final_row['close'], 'backtest_end')
            
            # Calculate final metrics
            results = self.calculate_results()
            
            self.logger.info(
                f"Backtest complete: Total P&L: ${results['total_pnl']:.2f} "
                f"({results['total_pnl_pct']:.2%}), Win Rate: {results['win_rate']:.2%}, "
                f"Sharpe: {results['sharpe_ratio']:.2f}"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in backtest: {e}")
            return {}
    
    def walk_forward_optimization(self, data: pd.DataFrame, strategy_func,
                                 train_period_days: int = 30,
                                 test_period_days: int = 7,
                                 min_train_samples: int = 100) -> Dict:
        """
        Perform walk-forward optimization
        
        Args:
            data: Full dataset
            strategy_func: Strategy function to test
            train_period_days: Days to use for training
            test_period_days: Days to use for testing
            min_train_samples: Minimum samples needed for training
        
        Returns:
            Aggregated results from all test periods
        """
        try:
            self.logger.info(
                f"Starting walk-forward optimization: "
                f"train={train_period_days}d, test={test_period_days}d"
            )
            
            all_results = []
            
            # Ensure data has datetime index
            if 'timestamp' in data.columns:
                data = data.set_index('timestamp')
            
            # Calculate window sizes
            total_period = train_period_days + test_period_days
            
            start_idx = 0
            while start_idx + min_train_samples < len(data):
                # Define train and test windows
                train_end_idx = min(start_idx + train_period_days * 24, len(data))  # Assuming hourly data
                test_end_idx = min(train_end_idx + test_period_days * 24, len(data))
                
                if train_end_idx >= len(data):
                    break
                
                train_data = data.iloc[start_idx:train_end_idx]
                test_data = data.iloc[train_end_idx:test_end_idx]
                
                if len(train_data) < min_train_samples or len(test_data) < 10:
                    break
                
                # Run backtest on test period
                test_results = self.run_backtest(test_data, strategy_func)
                
                if test_results:
                    test_results['train_start'] = train_data.index[0]
                    test_results['train_end'] = train_data.index[-1]
                    test_results['test_start'] = test_data.index[0]
                    test_results['test_end'] = test_data.index[-1]
                    all_results.append(test_results)
                
                # Move window forward
                start_idx = train_end_idx
            
            # Aggregate results
            if all_results:
                aggregated = self.aggregate_walk_forward_results(all_results)
                
                self.logger.info(
                    f"Walk-forward optimization complete: "
                    f"{len(all_results)} periods tested, "
                    f"Avg P&L: ${aggregated['avg_pnl']:.2f}, "
                    f"Avg Win Rate: {aggregated['avg_win_rate']:.2%}"
                )
                
                return aggregated
            else:
                self.logger.warning("No results from walk-forward optimization")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error in walk-forward optimization: {e}")
            return {}
    
    def aggregate_walk_forward_results(self, results: List[Dict]) -> Dict:
        """Aggregate results from multiple walk-forward periods"""
        try:
            total_pnl = sum(r['total_pnl'] for r in results)
            avg_pnl = np.mean([r['total_pnl'] for r in results])
            avg_win_rate = np.mean([r['win_rate'] for r in results])
            avg_sharpe = np.mean([r['sharpe_ratio'] for r in results])
            total_trades = sum(r['total_trades'] for r in results)
            
            return {
                'num_periods': len(results),
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl,
                'avg_win_rate': avg_win_rate,
                'avg_sharpe': avg_sharpe,
                'total_trades': total_trades,
                'period_results': results
            }
        except Exception as e:
            self.logger.error(f"Error aggregating results: {e}")
            return {}
    
    def execute_signal(self, signal: Dict, row: pd.Series):
        """Execute a trading signal"""
        try:
            side = signal.get('side', 'long')
            amount = signal.get('amount', 100)
            entry_price = row['close']
            leverage = signal.get('leverage', 10)
            
            # Calculate position size
            position_value = amount * entry_price
            required_margin = position_value / leverage
            
            if required_margin > self.balance * 0.95:
                return  # Not enough balance
            
            # Create position
            position = {
                'side': side,
                'entry_price': entry_price,
                'amount': amount,
                'leverage': leverage,
                'entry_time': row.get('timestamp', None),
                'stop_loss': signal.get('stop_loss', entry_price * 0.95 if side == 'long' else entry_price * 1.05),
                'take_profit': signal.get('take_profit', entry_price * 1.05 if side == 'long' else entry_price * 0.95)
            }
            
            self.positions.append(position)
            self.balance -= required_margin
            
        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
    
    def check_exits(self, row: pd.Series):
        """Check if any positions should be closed"""
        current_price = row['close']
        
        for position in self.positions[:]:
            should_close = False
            exit_reason = None
            
            # Check stop loss
            if position['side'] == 'long':
                if current_price <= position['stop_loss']:
                    should_close = True
                    exit_reason = 'stop_loss'
                elif current_price >= position['take_profit']:
                    should_close = True
                    exit_reason = 'take_profit'
            else:  # short
                if current_price >= position['stop_loss']:
                    should_close = True
                    exit_reason = 'stop_loss'
                elif current_price <= position['take_profit']:
                    should_close = True
                    exit_reason = 'take_profit'
            
            if should_close:
                self.close_position(position, current_price, exit_reason)
    
    def close_position(self, position: Dict, exit_price: float, exit_reason: str):
        """Close a position and record the trade"""
        try:
            # Calculate P&L
            if position['side'] == 'long':
                price_change = (exit_price - position['entry_price']) / position['entry_price']
            else:  # short
                price_change = (position['entry_price'] - exit_price) / position['entry_price']
            
            position_value = position['amount'] * position['entry_price']
            pnl = price_change * position_value * position['leverage']
            
            # Return margin and add P&L
            required_margin = position_value / position['leverage']
            self.balance += required_margin + pnl
            
            # Record trade
            trade = {
                'side': position['side'],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'amount': position['amount'],
                'leverage': position['leverage'],
                'pnl': pnl,
                'pnl_pct': price_change * position['leverage'],
                'exit_reason': exit_reason
            }
            
            self.closed_trades.append(trade)
            self.positions.remove(position)
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
    
    def calculate_equity(self, current_price: float) -> float:
        """Calculate current equity including unrealized P&L"""
        equity = self.balance
        
        for position in self.positions:
            if position['side'] == 'long':
                price_change = (current_price - position['entry_price']) / position['entry_price']
            else:
                price_change = (position['entry_price'] - current_price) / position['entry_price']
            
            position_value = position['amount'] * position['entry_price']
            unrealized_pnl = price_change * position_value * position['leverage']
            equity += unrealized_pnl
        
        return equity
    
    def calculate_results(self) -> Dict:
        """Calculate backtest performance metrics"""
        try:
            if not self.closed_trades:
                return {
                    'total_trades': 0,
                    'total_pnl': 0,
                    'total_pnl_pct': 0,
                    'win_rate': 0,
                    'sharpe_ratio': 0
                }
            
            total_trades = len(self.closed_trades)
            winning_trades = sum(1 for t in self.closed_trades if t['pnl'] > 0)
            losing_trades = total_trades - winning_trades
            
            total_pnl = sum(t['pnl'] for t in self.closed_trades)
            total_pnl_pct = (self.balance - self.initial_balance) / self.initial_balance
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # Calculate Sharpe ratio
            returns = [t['pnl_pct'] for t in self.closed_trades]
            if len(returns) > 1:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Calculate max drawdown
            equity_values = [e['equity'] for e in self.equity_curve]
            peak = equity_values[0]
            max_drawdown = 0
            for equity in equity_values:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'total_pnl_pct': total_pnl_pct,
                'final_balance': self.balance,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'trades': self.closed_trades,
                'equity_curve': self.equity_curve
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating results: {e}")
            return {}
