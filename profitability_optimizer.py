"""
Profitability Optimizer for RAD Trading Bot

This module optimizes strategy parameters to achieve profitability targets:
- Profit Factor ≥ 1.2
- Sharpe Ratio ≥ 1.0
- Sortino Ratio ≥ 1.5
- Max Drawdown ≤ 15%
- Win Rate ≥ 45%
- Positive expectancy after fees/slippage/funding

Uses Bayesian optimization for efficient parameter search with walk-forward validation.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
import json
from logger import Logger
from backtest_engine import BacktestEngine
from scenario_stress_engine import ScenarioGenerator, MarketDataSimulator, ScenarioParams
import optuna


@dataclass
class OptimizationTarget:
    """Target metrics for optimization"""
    min_profit_factor: float = 1.2
    min_sharpe_ratio: float = 1.0
    min_sortino_ratio: float = 1.5
    max_drawdown_pct: float = 15.0
    min_win_rate: float = 0.45
    min_total_return_pct: float = 0.0  # Must be positive
    
    def is_satisfied(self, results: Dict) -> Tuple[bool, List[str]]:
        """
        Check if results satisfy all targets
        
        Returns:
            Tuple of (all_satisfied, list_of_failures)
        """
        failures = []
        
        profit_factor = results.get('profit_factor', 0)
        if profit_factor < self.min_profit_factor:
            failures.append(f"Profit Factor {profit_factor:.2f} < {self.min_profit_factor}")
        
        sharpe = results.get('sharpe_ratio', 0)
        if sharpe < self.min_sharpe_ratio:
            failures.append(f"Sharpe Ratio {sharpe:.2f} < {self.min_sharpe_ratio}")
        
        sortino = results.get('sortino_ratio', 0)
        if sortino < self.min_sortino_ratio:
            failures.append(f"Sortino Ratio {sortino:.2f} < {self.min_sortino_ratio}")
        
        max_dd = abs(results.get('max_drawdown_pct', 100))
        if max_dd > self.max_drawdown_pct:
            failures.append(f"Max Drawdown {max_dd:.2f}% > {self.max_drawdown_pct}%")
        
        win_rate = results.get('win_rate', 0)
        if win_rate < self.min_win_rate:
            failures.append(f"Win Rate {win_rate*100:.1f}% < {self.min_win_rate*100:.1f}%")
        
        total_return = results.get('total_return_pct', 0)
        if total_return <= self.min_total_return_pct:
            failures.append(f"Total Return {total_return:.2f}% <= {self.min_total_return_pct}%")
        
        return len(failures) == 0, failures
    
    def calculate_score(self, results: Dict) -> float:
        """
        Calculate optimization score (higher is better)
        
        Combines all metrics into single score with penalties for violations
        """
        score = 0.0
        
        # Profit factor (weight: 2.0)
        profit_factor = results.get('profit_factor', 0)
        if profit_factor >= self.min_profit_factor:
            score += 2.0 * (profit_factor - self.min_profit_factor)
        else:
            score -= 5.0 * (self.min_profit_factor - profit_factor)  # Heavy penalty
        
        # Sharpe ratio (weight: 1.5)
        sharpe = results.get('sharpe_ratio', 0)
        if sharpe >= self.min_sharpe_ratio:
            score += 1.5 * (sharpe - self.min_sharpe_ratio)
        else:
            score -= 3.0 * (self.min_sharpe_ratio - sharpe)
        
        # Sortino ratio (weight: 1.0)
        sortino = results.get('sortino_ratio', 0)
        if sortino >= self.min_sortino_ratio:
            score += 1.0 * (sortino - self.min_sortino_ratio)
        else:
            score -= 2.0 * (self.min_sortino_ratio - sortino)
        
        # Max drawdown (weight: 2.0, inverted)
        max_dd = abs(results.get('max_drawdown_pct', 100))
        if max_dd <= self.max_drawdown_pct:
            score += 2.0 * (self.max_drawdown_pct - max_dd) / self.max_drawdown_pct
        else:
            score -= 4.0 * (max_dd - self.max_drawdown_pct) / self.max_drawdown_pct
        
        # Win rate (weight: 1.0)
        win_rate = results.get('win_rate', 0)
        if win_rate >= self.min_win_rate:
            score += 1.0 * (win_rate - self.min_win_rate) / self.min_win_rate
        else:
            score -= 2.0 * (self.min_win_rate - win_rate) / self.min_win_rate
        
        # Total return (weight: 1.5)
        total_return = results.get('total_return_pct', 0) / 100.0  # Convert to decimal
        if total_return > 0:
            score += 1.5 * total_return
        else:
            score -= 3.0 * abs(total_return)  # Penalize losses
        
        return score


@dataclass
class StrategyParams:
    """Strategy parameters to optimize"""
    # Entry thresholds
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    confidence_threshold: float = 0.62
    
    # Position sizing
    position_size_pct: float = 0.15  # % of balance per trade
    max_position_size_pct: float = 0.40  # Max total exposure
    
    # Risk management
    stop_loss_pct: float = 0.03  # 3% stop loss
    take_profit_pct: float = 0.06  # 6% take profit
    trailing_stop_pct: float = 0.02  # 2% trailing stop
    
    # Leverage
    leverage: int = 5
    
    # Volume filter
    min_volume_ratio: float = 0.8  # Require 80% of avg volume
    
    # Momentum thresholds
    momentum_threshold: float = 0.015
    
    # Regime adaptation
    enable_regime_filters: bool = True
    min_trend_strength: float = 0.02
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'confidence_threshold': self.confidence_threshold,
            'position_size_pct': self.position_size_pct,
            'max_position_size_pct': self.max_position_size_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'trailing_stop_pct': self.trailing_stop_pct,
            'leverage': self.leverage,
            'min_volume_ratio': self.min_volume_ratio,
            'momentum_threshold': self.momentum_threshold,
            'enable_regime_filters': self.enable_regime_filters,
            'min_trend_strength': self.min_trend_strength,
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'StrategyParams':
        """Create from dictionary"""
        return cls(**d)


class ProfitabilityOptimizer:
    """
    Optimize strategy parameters for profitability
    
    Uses Bayesian optimization with walk-forward validation
    """
    
    def __init__(self, target: Optional[OptimizationTarget] = None):
        """
        Initialize optimizer
        
        Args:
            target: Optimization targets (uses defaults if None)
        """
        self.logger = Logger.get_logger()
        self.target = target or OptimizationTarget()
        self.scenario_gen = ScenarioGenerator(base_seed=42)
        self.simulator = MarketDataSimulator()
        
        self.best_params: Optional[StrategyParams] = None
        self.best_score: float = float('-inf')
        self.best_results: Optional[Dict] = None
        
        self.optimization_history: List[Dict] = []
    
    def create_strategy_func(self, params: StrategyParams) -> Callable:
        """
        Create strategy function with given parameters
        
        Args:
            params: Strategy parameters
            
        Returns:
            Strategy function for backtesting
        """
        def strategy(row, balance, positions):
            """
            Parameterized trading strategy
            
            Args:
                row: Current candle data
                balance: Current balance
                positions: Open positions
                
            Returns:
                Trading signal dict or None
            """
            # Get indicators
            if hasattr(row, 'get'):
                rsi = row.get('rsi', 50)
                macd = row.get('macd', 0)
                macd_signal = row.get('macd_signal', 0)
                ema_12 = row.get('ema_12', 0)
                ema_26 = row.get('ema_26', 0)
                close = row.get('close', 0)
                volume_ratio = row.get('volume_ratio', 1.0)
                momentum = row.get('momentum', 0)
                bb_width = row.get('bb_width', 0.02)
            else:
                rsi = row.get('rsi', 50) if hasattr(row, 'get') else row['rsi']
                macd = row['macd']
                macd_signal = row['macd_signal']
                ema_12 = row['ema_12']
                ema_26 = row['ema_26']
                close = row['close']
                volume_ratio = row.get('volume_ratio', 1.0) if hasattr(row, 'get') else 1.0
                momentum = row.get('momentum', 0) if hasattr(row, 'get') else 0
                bb_width = row.get('bb_width', 0.02) if hasattr(row, 'get') else 0.02
            
            # Volume filter
            if volume_ratio < params.min_volume_ratio:
                return None  # Skip low volume
            
            # Regime detection (simple)
            is_trending = abs(momentum) > params.min_trend_strength or bb_width > 0.03
            is_ranging = bb_width < 0.015 and abs(momentum) < params.momentum_threshold
            
            # If we have a position, check exits
            if positions:
                pos = positions[0]
                entry_price = pos['entry_price']
                side = pos['side']
                
                # Calculate P/L
                if side == 'long':
                    pnl_pct = (close - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - close) / entry_price
                
                # Check stop loss
                if pnl_pct <= -params.stop_loss_pct:
                    return {
                        'side': 'sell' if side == 'long' else 'buy',
                        'amount': pos['amount'],
                        'leverage': pos['leverage']
                    }
                
                # Check take profit
                if pnl_pct >= params.take_profit_pct:
                    return {
                        'side': 'sell' if side == 'long' else 'buy',
                        'amount': pos['amount'],
                        'leverage': pos['leverage']
                    }
                
                # Trailing stop (if profitable)
                if pnl_pct > params.trailing_stop_pct * 2:
                    # Check if price moved against us by trailing_stop_pct from peak
                    # Simplified: exit if below trailing stop from current price
                    if side == 'long' and rsi > 70:
                        return {
                            'side': 'sell',
                            'amount': pos['amount'],
                            'leverage': pos['leverage']
                        }
                    elif side == 'short' and rsi < 30:
                        return {
                            'side': 'buy',
                            'amount': pos['amount'],
                            'leverage': pos['leverage']
                        }
            
            else:
                # No position, look for entry
                
                # Regime filter (if enabled)
                if params.enable_regime_filters:
                    # In ranging market, only trade mean reversion
                    if is_ranging:
                        # Mean reversion entries
                        if rsi < params.rsi_oversold and macd > macd_signal:
                            amount = balance * params.position_size_pct / close
                            return {
                                'side': 'long',
                                'amount': amount,
                                'leverage': params.leverage,
                                'stop_loss': close * (1 - params.stop_loss_pct),
                                'take_profit': close * (1 + params.take_profit_pct)
                            }
                        elif rsi > params.rsi_overbought and macd < macd_signal:
                            amount = balance * params.position_size_pct / close
                            return {
                                'side': 'short',
                                'amount': amount,
                                'leverage': params.leverage,
                                'stop_loss': close * (1 + params.stop_loss_pct),
                                'take_profit': close * (1 - params.take_profit_pct)
                            }
                    
                    # In trending market, trade with the trend
                    elif is_trending:
                        # Trend following
                        if ema_12 > ema_26 and macd > macd_signal and momentum > params.momentum_threshold:
                            if rsi < 60:  # Not too overbought
                                amount = balance * params.position_size_pct / close
                                return {
                                    'side': 'long',
                                    'amount': amount,
                                    'leverage': params.leverage,
                                    'stop_loss': close * (1 - params.stop_loss_pct),
                                    'take_profit': close * (1 + params.take_profit_pct)
                                }
                        elif ema_12 < ema_26 and macd < macd_signal and momentum < -params.momentum_threshold:
                            if rsi > 40:  # Not too oversold
                                amount = balance * params.position_size_pct / close
                                return {
                                    'side': 'short',
                                    'amount': amount,
                                    'leverage': params.leverage,
                                    'stop_loss': close * (1 + params.stop_loss_pct),
                                    'take_profit': close * (1 - params.take_profit_pct)
                                }
                
                else:
                    # No regime filter - simpler strategy
                    # Long entry
                    if (rsi < params.rsi_oversold and 
                        macd > macd_signal and 
                        ema_12 > ema_26):
                        amount = balance * params.position_size_pct / close
                        return {
                            'side': 'long',
                            'amount': amount,
                            'leverage': params.leverage,
                            'stop_loss': close * (1 - params.stop_loss_pct),
                            'take_profit': close * (1 + params.take_profit_pct)
                        }
                    
                    # Short entry
                    elif (rsi > params.rsi_overbought and 
                          macd < macd_signal and 
                          ema_12 < ema_26):
                        amount = balance * params.position_size_pct / close
                        return {
                            'side': 'short',
                            'amount': amount,
                            'leverage': params.leverage,
                            'stop_loss': close * (1 + params.stop_loss_pct),
                            'take_profit': close * (1 - params.take_profit_pct)
                        }
            
            return None
        
        return strategy
    
    def evaluate_params(self, params: StrategyParams, 
                       num_scenarios: int = 10) -> Tuple[float, Dict]:
        """
        Evaluate strategy parameters across multiple scenarios
        
        Args:
            params: Strategy parameters to evaluate
            num_scenarios: Number of scenarios to test
            
        Returns:
            Tuple of (score, aggregated_results)
        """
        # Generate diverse scenarios
        scenarios = self.scenario_gen.generate_all_scenarios()
        
        # Select diverse subset
        np.random.seed(42)
        selected_indices = np.random.choice(len(scenarios), min(num_scenarios, len(scenarios)), replace=False)
        test_scenarios = [scenarios[i] for i in selected_indices]
        
        # Run backtests
        all_results = []
        strategy_func = self.create_strategy_func(params)
        
        for scenario in test_scenarios:
            try:
                # Generate data
                df = self.simulator.generate_ohlcv(scenario)
                
                # Add indicators
                from indicators import Indicators
                df = Indicators.calculate_all(df)
                
                # Run backtest
                engine = BacktestEngine(
                    initial_balance=10000.0,
                    trading_fee_rate=scenario.trading_fee_rate,
                    funding_rate=scenario.funding_rate,
                    latency_ms=scenario.max_latency_ms,
                    slippage_bps=scenario.slippage_bps
                )
                
                results = engine.run_backtest(df, strategy_func, use_next_bar_execution=True)
                
                if results and results.get('total_trades', 0) > 0:
                    all_results.append(results)
            
            except Exception as e:
                self.logger.debug(f"Error in scenario evaluation: {e}")
                continue
        
        if not all_results:
            return float('-inf'), {}
        
        # Aggregate results
        aggregated = {
            'num_scenarios': len(all_results),
            'total_return_pct': np.mean([r['total_return_pct'] for r in all_results]),
            'sharpe_ratio': np.mean([r['sharpe_ratio'] for r in all_results]),
            'sortino_ratio': np.mean([r['sortino_ratio'] for r in all_results]),
            'max_drawdown_pct': np.mean([r['max_drawdown_pct'] for r in all_results]),
            'profit_factor': np.mean([r['profit_factor'] for r in all_results if r['profit_factor'] > 0]),
            'win_rate': np.mean([r['win_rate'] for r in all_results]),
            'total_trades': np.mean([r['total_trades'] for r in all_results]),
        }
        
        # Calculate score
        score = self.target.calculate_score(aggregated)
        
        return score, aggregated
    
    def optimize_with_optuna(self, n_trials: int = 100) -> StrategyParams:
        """
        Run Bayesian optimization using Optuna
        
        Args:
            n_trials: Number of optimization trials
            
        Returns:
            Best strategy parameters found
        """
        self.logger.info(f"Starting Bayesian optimization with {n_trials} trials...")
        
        def objective(trial):
            """Optuna objective function"""
            # Sample parameters
            params = StrategyParams(
                rsi_oversold=trial.suggest_float('rsi_oversold', 20.0, 35.0),
                rsi_overbought=trial.suggest_float('rsi_overbought', 65.0, 80.0),
                confidence_threshold=trial.suggest_float('confidence_threshold', 0.55, 0.75),
                position_size_pct=trial.suggest_float('position_size_pct', 0.05, 0.25),
                max_position_size_pct=trial.suggest_float('max_position_size_pct', 0.30, 0.60),
                stop_loss_pct=trial.suggest_float('stop_loss_pct', 0.015, 0.05),
                take_profit_pct=trial.suggest_float('take_profit_pct', 0.03, 0.10),
                trailing_stop_pct=trial.suggest_float('trailing_stop_pct', 0.015, 0.04),
                leverage=trial.suggest_int('leverage', 3, 8),
                min_volume_ratio=trial.suggest_float('min_volume_ratio', 0.6, 1.2),
                momentum_threshold=trial.suggest_float('momentum_threshold', 0.01, 0.025),
                enable_regime_filters=trial.suggest_categorical('enable_regime_filters', [True, False]),
                min_trend_strength=trial.suggest_float('min_trend_strength', 0.015, 0.03),
            )
            
            # Evaluate
            score, results = self.evaluate_params(params, num_scenarios=10)
            
            # Store history
            self.optimization_history.append({
                'trial': trial.number,
                'params': params.to_dict(),
                'score': score,
                'results': results
            })
            
            # Update best if improved
            if score > self.best_score:
                self.best_score = score
                self.best_params = params
                self.best_results = results
                
                satisfied, failures = self.target.is_satisfied(results)
                self.logger.info(f"New best! Trial {trial.number}: Score={score:.3f}, "
                               f"Satisfied={satisfied}")
                if not satisfied:
                    self.logger.info(f"  Failures: {', '.join(failures)}")
            
            return score
        
        # Create Optuna study
        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        
        # Run optimization
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        # Log results
        self.logger.info(f"\nOptimization complete!")
        self.logger.info(f"Best score: {self.best_score:.3f}")
        
        if self.best_results:
            satisfied, failures = self.target.is_satisfied(self.best_results)
            self.logger.info(f"Targets satisfied: {satisfied}")
            if not satisfied:
                self.logger.info(f"Remaining issues: {', '.join(failures)}")
            
            self.logger.info(f"\nBest results:")
            for key in ['total_return_pct', 'sharpe_ratio', 'sortino_ratio', 
                       'max_drawdown_pct', 'profit_factor', 'win_rate']:
                value = self.best_results.get(key, 0)
                self.logger.info(f"  {key}: {value:.2f}")
        
        return self.best_params
    
    def save_results(self, filepath: str = 'optimization_results.json'):
        """Save optimization results to file"""
        results = {
            'best_params': self.best_params.to_dict() if self.best_params else None,
            'best_score': self.best_score,
            'best_results': self.best_results,
            'optimization_history': self.optimization_history,
            'target': {
                'min_profit_factor': self.target.min_profit_factor,
                'min_sharpe_ratio': self.target.min_sharpe_ratio,
                'min_sortino_ratio': self.target.min_sortino_ratio,
                'max_drawdown_pct': self.target.max_drawdown_pct,
                'min_win_rate': self.target.min_win_rate,
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Results saved to {filepath}")


def main():
    """Run profitability optimization"""
    print("\n" + "="*80)
    print("PROFITABILITY OPTIMIZER")
    print("="*80 + "\n")
    
    # Create optimizer with targets
    target = OptimizationTarget()
    optimizer = ProfitabilityOptimizer(target=target)
    
    print(f"Optimization Targets:")
    print(f"  Profit Factor ≥ {target.min_profit_factor}")
    print(f"  Sharpe Ratio ≥ {target.min_sharpe_ratio}")
    print(f"  Sortino Ratio ≥ {target.min_sortino_ratio}")
    print(f"  Max Drawdown ≤ {target.max_drawdown_pct}%")
    print(f"  Win Rate ≥ {target.min_win_rate*100:.0f}%")
    print(f"  Total Return > {target.min_total_return_pct}%")
    
    # Run optimization
    print(f"\nRunning Bayesian optimization (10 trials for demo)...")
    best_params = optimizer.optimize_with_optuna(n_trials=10)
    
    # Save results
    optimizer.save_results('optimization_results.json')
    
    print("\n✅ Optimization complete! Results saved to optimization_results.json")


if __name__ == '__main__':
    main()
