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
    
    def __init__(self, initial_balance: float = 10000, 
                 trading_fee_rate: float = 0.0006,  # 0.06% taker fee
                 funding_rate: float = 0.0001,  # 0.01% per 8 hours
                 latency_ms: int = 200,  # Network latency in milliseconds
                 slippage_bps: float = 5.0):  # Slippage in basis points (0.05%)
        """
        Initialize backtest engine with realistic fees, latency, and slippage
        
        PRIORITY 1: Include trading fees, funding rates, latency, and slippage for realistic PnL
        
        Args:
            initial_balance: Starting capital
            trading_fee_rate: Trading fee as decimal (default: 0.0006 = 0.06%)
            funding_rate: Funding rate per 8 hours (default: 0.0001 = 0.01%)
            latency_ms: Network and exchange latency in milliseconds (default: 200ms)
            slippage_bps: Expected slippage in basis points (default: 5 bps = 0.05%)
        """
        self.logger = Logger.get_logger()
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = []
        self.closed_trades = []
        self.equity_curve = []
        
        # PRIORITY 1: Track fees for realistic backtesting
        self.trading_fee_rate = trading_fee_rate  # Taker fee (conservative)
        self.funding_rate = funding_rate  # Default 0.01% per 8h
        self.total_trading_fees = 0.0
        self.total_funding_fees = 0.0
        self.funding_payments = []  # Track all funding payments
        
        # AUDIT FIX: Add latency and slippage simulation
        self.latency_ms = latency_ms
        self.slippage_bps = slippage_bps
        self.total_slippage_cost = 0.0
    
    def reset(self):
        """Reset backtesting state"""
        self.balance = self.initial_balance
        self.positions = []
        self.closed_trades = []
        self.equity_curve = []
        self.total_trading_fees = 0.0
        self.total_funding_fees = 0.0
        self.total_slippage_cost = 0.0
        self.funding_payments = []
    
    def run_backtest(self, data: pd.DataFrame, strategy_func,
                    initial_balance: float = None,
                    use_next_bar_execution: bool = True) -> Dict:
        """
        Run backtest on historical data with realistic execution
        
        AUDIT FIX: Add latency simulation by using next bar's open price
        
        Args:
            data: DataFrame with OHLCV and indicator data
            strategy_func: Function that takes (row, balance, positions) and returns signal
            initial_balance: Starting balance (overrides init value if provided)
            use_next_bar_execution: If True, execute signals at next bar's open (realistic)
        
        Returns:
            Backtest results dictionary
        """
        if initial_balance:
            self.initial_balance = initial_balance
        
        self.reset()
        
        try:
            self.logger.info(f"Starting backtest with {len(data)} candles")
            self.logger.info(f"Latency simulation: {self.latency_ms}ms, "
                           f"Slippage: {self.slippage_bps} bps, "
                           f"Next bar execution: {use_next_bar_execution}")
            
            pending_signals = []  # Queue for signals to execute next bar
            
            for i, (idx, row) in enumerate(data.iterrows()):
                # Update equity curve
                current_equity = self.calculate_equity(row['close'])
                self.equity_curve.append({
                    'timestamp': row.get('timestamp', idx),
                    'balance': self.balance,
                    'equity': current_equity
                })
                
                # AUDIT FIX: Execute pending signals from previous bar
                # This simulates latency - signal generated on bar N, executed on bar N+1
                if use_next_bar_execution and pending_signals:
                    for signal in pending_signals:
                        # Use current bar's open price (next bar after signal)
                        signal_row = row.copy()
                        signal_row['close'] = row['open']  # Execute at open
                        self.execute_signal(signal, signal_row)
                    pending_signals = []
                
                # Check for position exits first
                self.check_exits(row)
                
                # Get signal from strategy
                signal = strategy_func(row, self.balance, self.positions)
                
                # AUDIT FIX: Queue signal for next bar execution (realistic latency)
                # Handle both dict and string signals
                if signal:
                    # Convert string signals to dict format
                    if isinstance(signal, str) and signal.upper() not in ['HOLD', 'NONE', '']:
                        # Simple string signal, convert to dict
                        close_price = row['close']
                        amount = self.balance * 0.1 / close_price  # 10% of balance
                        signal = {
                            'side': signal.lower(),
                            'amount': amount,
                            'leverage': 5,
                            'stop_loss': close_price * 0.97 if signal.lower() == 'long' else close_price * 1.03,
                            'take_profit': close_price * 1.05 if signal.lower() == 'long' else close_price * 0.95
                        }
                    
                    if isinstance(signal, dict):
                        if use_next_bar_execution:
                            pending_signals.append(signal)
                        else:
                            # Immediate execution (less realistic)
                            self.execute_signal(signal, row)
            
            # Close any remaining positions at end
            if self.positions:
                final_row = data.iloc[-1]
                for pos in self.positions[:]:
                    self.close_position(pos, final_row['close'], 'backtest_end')
            
            # Calculate final metrics
            results = self.calculate_results()
            
            # PRIORITY 1: Log fee and slippage impact
            self.logger.info(
                f"Backtest complete: Net P&L: ${results['total_pnl']:.2f} "
                f"({results['total_pnl_pct']:.2%}), Win Rate: {results['win_rate']:.2%}, "
                f"Sharpe: {results['sharpe_ratio']:.2f}"
            )
            self.logger.info(
                f"Costs: Trading Fees: ${results['total_trading_fees']:.2f}, "
                f"Funding: ${results['total_funding_fees']:.2f}, "
                f"Slippage: ${results.get('total_slippage', 0):.2f}, "
                f"Total: ${results['total_fees']:.2f} ({results['fee_impact_pct']:.1f}% of gross PnL)"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in backtest: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
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
            while start_idx + train_period_days * 24 + test_period_days * 24 <= len(data):
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
    
    def calculate_slippage(self, price: float, amount: float, side: str, 
                          volume: float = None) -> float:
        """
        Calculate realistic slippage based on order size and liquidity
        
        AUDIT FIX: Implement realistic slippage estimation
        
        Args:
            price: Current market price
            amount: Order size in base currency
            side: 'buy' or 'sell'
            volume: Recent volume (optional, used for liquidity-based slippage)
            
        Returns:
            Slippage-adjusted execution price
        """
        # Base slippage from bid-ask spread (in basis points)
        base_slippage_bps = self.slippage_bps
        
        # Additional slippage for large orders (if volume provided)
        if volume is not None and volume > 0:
            # If order size > 1% of recent volume, add impact slippage
            order_value = price * amount
            volume_value = price * volume
            impact_ratio = order_value / volume_value if volume_value > 0 else 0
            
            if impact_ratio > 0.01:  # > 1% of volume
                # Square root market impact model
                impact_slippage_bps = base_slippage_bps * np.sqrt(impact_ratio * 100)
                base_slippage_bps += impact_slippage_bps
        
        # Cap maximum slippage at 50 bps (0.5%)
        total_slippage_bps = min(base_slippage_bps, 50.0)
        
        # Apply slippage direction
        slippage_factor = total_slippage_bps / 10000.0  # Convert bps to decimal
        
        if side in ['buy', 'long']:
            # Buying: pay more (slippage increases price)
            slippage_price = price * (1 + slippage_factor)
        else:
            # Selling: receive less (slippage decreases price)
            slippage_price = price * (1 - slippage_factor)
        
        return slippage_price
    
    def execute_signal(self, signal: Dict, row: pd.Series):
        """
        Execute a trading signal with realistic latency and slippage
        
        AUDIT FIX: Add latency simulation and slippage
        """
        try:
            side = signal.get('side', 'long')
            amount = signal.get('amount', 100)
            entry_price = row['close']
            leverage = signal.get('leverage', 10)
            
            # AUDIT FIX: Apply slippage based on order size and liquidity
            volume = row.get('volume', None)
            slippage_price = self.calculate_slippage(entry_price, amount, side, volume)
            
            # Calculate slippage cost
            slippage_cost = abs(slippage_price - entry_price) * amount
            self.total_slippage_cost += slippage_cost
            
            # Use slippage-adjusted price for execution
            execution_price = slippage_price
            
            # Calculate position size
            position_value = amount * execution_price
            required_margin = position_value / leverage
            
            if required_margin > self.balance * 0.95:
                return  # Not enough balance
            
            # PRIORITY 1: Calculate and deduct trading fee
            trading_fee = position_value * self.trading_fee_rate
            self.total_trading_fees += trading_fee
            self.balance -= trading_fee
            
            # Create position
            position = {
                'side': side,
                'entry_price': execution_price,  # Use slippage-adjusted price
                'amount': amount,
                'leverage': leverage,
                'entry_time': row.get('timestamp', None),
                'stop_loss': signal.get('stop_loss', execution_price * 0.95 if side == 'long' else execution_price * 1.05),
                'take_profit': signal.get('take_profit', execution_price * 1.05 if side == 'long' else execution_price * 0.95)
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
        """
        Close a position and record the trade
        
        PRIORITY 1: Include trading fees and funding in PnL calculation
        """
        try:
            # Calculate P&L
            if position['side'] == 'long':
                price_change = (exit_price - position['entry_price']) / position['entry_price']
            else:  # short
                price_change = (position['entry_price'] - exit_price) / position['entry_price']
            
            position_value = position['amount'] * position['entry_price']
            gross_pnl = price_change * position_value * position['leverage']
            
            # PRIORITY 1: Calculate trading fees (entry + exit)
            entry_fee = position_value * self.trading_fee_rate
            exit_value = position['amount'] * exit_price
            exit_fee = exit_value * self.trading_fee_rate
            trading_fees = entry_fee + exit_fee
            
            # PRIORITY 1: Calculate funding fees
            # Estimate funding based on position hold time (if available)
            funding_fees = 0.0
            if 'entry_time' in position and 'exit_time' in position:
                # Calculate number of 8-hour funding periods
                hold_hours = (position['exit_time'] - position['entry_time']).total_seconds() / 3600
                funding_periods = hold_hours / 8  # Funding every 8 hours
                funding_fees = position_value * self.funding_rate * funding_periods
            else:
                # Fallback: assume 1 funding period per position
                funding_fees = position_value * self.funding_rate
            
            # Net PnL after fees
            net_pnl = gross_pnl - trading_fees - funding_fees
            
            # Track fees
            self.total_trading_fees += trading_fees
            self.total_funding_fees += funding_fees
            
            # Return margin and add net P&L
            required_margin = position_value / position['leverage']
            self.balance += required_margin + net_pnl
            
            # Record trade with fee details
            trade = {
                'side': position['side'],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'amount': position['amount'],
                'leverage': position['leverage'],
                'gross_pnl': gross_pnl,
                'trading_fees': trading_fees,
                'funding_fees': funding_fees,
                'net_pnl': net_pnl,
                'pnl_pct': (net_pnl / required_margin) if required_margin > 0 else 0,
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
        """
        Calculate backtest performance metrics
        
        PRIORITY 1: Include fee impact in metrics
        """
        try:
            if not self.closed_trades:
                return {
                    'total_trades': 0,
                    'total_pnl': 0,
                    'total_pnl_pct': 0,
                    'win_rate': 0,
                    'sharpe_ratio': 0,
                    'sortino_ratio': 0,
                    'max_drawdown': 0,
                    'max_drawdown_pct': 0,
                    'profit_factor': 0,
                    'total_trading_fees': 0,
                    'total_funding_fees': 0,
                    'total_slippage': 0,
                    'total_fees': 0,
                    'fee_impact_pct': 0,
                    'gross_pnl': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'final_balance': self.balance,
                    'total_return_pct': 0,
                    'trades': [],
                    'equity_curve': self.equity_curve
                }
            
            total_trades = len(self.closed_trades)
            
            # PRIORITY 1: Use net_pnl (after fees) for metrics
            winning_trades = sum(1 for t in self.closed_trades if t.get('net_pnl', t.get('pnl', 0)) > 0)
            losing_trades = total_trades - winning_trades
            
            # Calculate with net PnL (includes fees)
            total_pnl = sum(t.get('net_pnl', t.get('pnl', 0)) for t in self.closed_trades)
            total_pnl_pct = (self.balance - self.initial_balance) / self.initial_balance
            
            # Calculate gross PnL (before fees) for comparison
            gross_pnl = sum(t.get('gross_pnl', t.get('pnl', 0)) for t in self.closed_trades)
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # Calculate profit factor
            total_profit = sum(t.get('net_pnl', 0) for t in self.closed_trades if t.get('net_pnl', 0) > 0)
            total_loss = abs(sum(t.get('net_pnl', 0) for t in self.closed_trades if t.get('net_pnl', 0) < 0))
            profit_factor = total_profit / total_loss if total_loss > 0 else 0
            
            # Calculate Sharpe ratio using net PnL percentages
            returns = [t['pnl_pct'] for t in self.closed_trades]
            if len(returns) > 1:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
                
                # Calculate Sortino ratio (downside deviation only)
                downside_returns = [r for r in returns if r < 0]
                if downside_returns:
                    downside_std = np.std(downside_returns)
                    sortino_ratio = (avg_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0
                else:
                    sortino_ratio = sharpe_ratio  # No downside, use Sharpe
            else:
                sharpe_ratio = 0
                sortino_ratio = 0
            
            # Calculate max drawdown
            max_drawdown = 0
            if self.equity_curve:
                equity_values = [e['equity'] for e in self.equity_curve]
                peak = equity_values[0]
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
                'profit_factor': profit_factor,
                'total_pnl': total_pnl,  # Net PnL (after fees)
                'gross_pnl': gross_pnl,  # Gross PnL (before fees)
                'total_pnl_pct': total_pnl_pct,
                'total_return_pct': total_pnl_pct * 100,  # As percentage
                'final_balance': self.balance,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': max_drawdown * 100,
                # PRIORITY 1: Fee metrics
                'total_trading_fees': self.total_trading_fees,
                'total_funding_fees': self.total_funding_fees,
                'total_slippage': self.total_slippage_cost,  # AUDIT FIX: Add slippage
                'total_fees': self.total_trading_fees + self.total_funding_fees + self.total_slippage_cost,
                'fee_impact_pct': ((gross_pnl - total_pnl) / gross_pnl * 100) if gross_pnl != 0 else 0,
                'trades': self.closed_trades,
                'equity_curve': self.equity_curve
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating results: {e}")
            return {}
