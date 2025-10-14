"""
Bayesian Adaptive Kelly Criterion - 2025 Enhancement
Dynamic position sizing with Bayesian win rate estimation
"""
import numpy as np
from typing import Dict, List, Tuple
from logger import Logger


class BayesianAdaptiveKelly:
    """
    Enhanced Kelly Criterion with Bayesian updates and dynamic adjustment
    
    Improvements over standard Kelly:
    - Bayesian posterior estimation of win rate
    - Dynamic fractional Kelly based on uncertainty
    - Rolling window for market regime adaptation
    - Confidence-based position sizing
    """
    
    def __init__(self, 
                 base_kelly_fraction: float = 0.25,
                 prior_alpha: float = 20.0,
                 prior_beta: float = 20.0,
                 window_size: int = 50):
        """
        Initialize Bayesian Kelly Calculator
        
        Args:
            base_kelly_fraction: Base Kelly fraction (0.15-0.35 recommended)
            prior_alpha: Prior for Beta distribution (wins)
            prior_beta: Prior for Beta distribution (losses)
            window_size: Number of recent trades to emphasize
        """
        self.logger = Logger.get_logger()
        self.base_kelly_fraction = base_kelly_fraction
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.window_size = window_size
        
        # Trade history for Bayesian updates
        self.trade_history = []
        
    def update_trade_outcome(self, win: bool, profit_loss_pct: float):
        """
        Record a trade outcome for Bayesian learning
        
        Args:
            win: True if trade was profitable
            profit_loss_pct: Profit/loss as percentage (e.g., 0.05 = 5%)
        """
        self.trade_history.append({
            'win': win,
            'profit_loss_pct': profit_loss_pct,
            'timestamp': np.datetime64('now')
        })
        
        # Keep limited history (recent trades more relevant)
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]
    
    def calculate_bayesian_win_rate(self, window_trades: int = None) -> Dict:
        """
        Calculate Bayesian posterior win rate using Beta distribution
        
        Uses conjugate prior (Beta) + binomial likelihood = Beta posterior
        
        Args:
            window_trades: Number of recent trades to use (None = all)
            
        Returns:
            Dictionary with win rate statistics
        """
        try:
            if not self.trade_history:
                # Use prior only (no data)
                posterior_alpha = self.prior_alpha
                posterior_beta = self.prior_beta
                mean_win_rate = posterior_alpha / (posterior_alpha + posterior_beta)
                return {
                    'mean': mean_win_rate,
                    'std': np.sqrt((posterior_alpha * posterior_beta) / 
                                  ((posterior_alpha + posterior_beta)**2 * 
                                   (posterior_alpha + posterior_beta + 1))),
                    'lower_95': 0.3,  # Conservative
                    'upper_95': 0.7,
                    'n_trades': 0
                }
            
            # Use recent window or all trades
            if window_trades:
                recent_trades = self.trade_history[-window_trades:]
            else:
                recent_trades = self.trade_history
            
            # Count wins and losses
            wins = sum(1 for t in recent_trades if t['win'])
            losses = len(recent_trades) - wins
            
            # Update posterior (prior + observed data)
            posterior_alpha = self.prior_alpha + wins
            posterior_beta = self.prior_beta + losses
            
            # Calculate statistics
            mean_win_rate = posterior_alpha / (posterior_alpha + posterior_beta)
            
            # Variance of Beta distribution
            variance = (posterior_alpha * posterior_beta) / \
                      ((posterior_alpha + posterior_beta)**2 * 
                       (posterior_alpha + posterior_beta + 1))
            std = np.sqrt(variance)
            
            # 95% credible interval (approximately)
            lower_95 = max(0.0, mean_win_rate - 1.96 * std)
            upper_95 = min(1.0, mean_win_rate + 1.96 * std)
            
            self.logger.debug(f"Bayesian win rate: {mean_win_rate:.3f} ± {std:.3f} "
                            f"(95% CI: [{lower_95:.3f}, {upper_95:.3f}], n={len(recent_trades)})")
            
            return {
                'mean': mean_win_rate,
                'std': std,
                'lower_95': lower_95,
                'upper_95': upper_95,
                'posterior_alpha': posterior_alpha,
                'posterior_beta': posterior_beta,
                'n_trades': len(recent_trades)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating Bayesian win rate: {e}")
            return {
                'mean': 0.5,
                'std': 0.2,
                'lower_95': 0.3,
                'upper_95': 0.7,
                'n_trades': 0
            }
    
    def calculate_avg_win_loss(self, window_trades: int = None) -> Tuple[float, float]:
        """
        Calculate average win and loss percentages
        
        Args:
            window_trades: Number of recent trades to use
            
        Returns:
            Tuple of (avg_win_pct, avg_loss_pct)
        """
        try:
            if not self.trade_history:
                return 0.02, 0.01  # Default 2% avg win, 1% avg loss
            
            if window_trades:
                recent_trades = self.trade_history[-window_trades:]
            else:
                recent_trades = self.trade_history
            
            wins = [abs(t['profit_loss_pct']) for t in recent_trades if t['win']]
            losses = [abs(t['profit_loss_pct']) for t in recent_trades if not t['win']]
            
            avg_win = np.mean(wins) if wins else 0.02
            avg_loss = np.mean(losses) if losses else 0.01
            
            return avg_win, avg_loss
            
        except Exception as e:
            self.logger.error(f"Error calculating avg win/loss: {e}")
            return 0.02, 0.01
    
    def calculate_dynamic_kelly_fraction(self, uncertainty: float,
                                        market_volatility: float = 0.03) -> float:
        """
        Calculate dynamic Kelly fraction based on uncertainty and volatility
        
        More uncertain = more conservative (lower fraction)
        Higher volatility = more conservative (lower fraction)
        
        Args:
            uncertainty: Standard deviation of win rate estimate
            market_volatility: Current market volatility
            
        Returns:
            Dynamic Kelly fraction
        """
        try:
            # Start with base fraction
            kelly_fraction = self.base_kelly_fraction
            
            # Adjust for uncertainty
            # High uncertainty (std > 0.15) = reduce by up to 40%
            if uncertainty > 0.15:
                kelly_fraction *= 0.6
            elif uncertainty > 0.10:
                kelly_fraction *= 0.75
            elif uncertainty > 0.05:
                kelly_fraction *= 0.9
            else:
                kelly_fraction *= 1.0  # Low uncertainty, use base
            
            # Adjust for market volatility
            # High volatility (> 0.06) = reduce by up to 35%
            if market_volatility > 0.08:
                kelly_fraction *= 0.65
            elif market_volatility > 0.06:
                kelly_fraction *= 0.75
            elif market_volatility > 0.04:
                kelly_fraction *= 0.85
            elif market_volatility < 0.02:
                kelly_fraction *= 1.10  # Low volatility, can be slightly more aggressive
            
            # Clamp to reasonable range
            kelly_fraction = max(0.10, min(0.40, kelly_fraction))
            
            self.logger.debug(f"Dynamic Kelly fraction: {kelly_fraction:.3f} "
                            f"(uncertainty={uncertainty:.3f}, vol={market_volatility:.3f})")
            
            return kelly_fraction
            
        except Exception as e:
            self.logger.error(f"Error calculating dynamic Kelly fraction: {e}")
            return self.base_kelly_fraction
    
    def calculate_optimal_position_size(self,
                                       balance: float,
                                       confidence: float = 0.7,
                                       market_volatility: float = 0.03,
                                       use_recent_window: bool = True) -> Dict:
        """
        Calculate optimal position size using Bayesian Adaptive Kelly
        
        Args:
            balance: Account balance in USDT
            confidence: Signal confidence (0-1)
            market_volatility: Current market volatility measure
            use_recent_window: Use recent trades window (adaptive) vs all trades
            
        Returns:
            Dictionary with position sizing recommendation
        """
        try:
            # Get Bayesian win rate estimate
            window = self.window_size if use_recent_window else None
            win_stats = self.calculate_bayesian_win_rate(window)
            
            # Get average win/loss
            avg_win, avg_loss = self.calculate_avg_win_loss(window)
            
            # Calculate Kelly fraction dynamically
            uncertainty = win_stats['std']
            kelly_fraction = self.calculate_dynamic_kelly_fraction(
                uncertainty, market_volatility
            )
            
            # Classic Kelly formula: f* = (p*b - q) / b
            # where p = win prob, q = loss prob, b = win/loss ratio
            p = win_stats['mean']
            q = 1 - p
            b = avg_win / avg_loss if avg_loss > 0 else 2.0
            
            # Kelly percentage
            if b > 0:
                kelly_pct = (p * b - q) / b
            else:
                kelly_pct = 0
            
            # Apply Kelly fraction for safety
            fractional_kelly_pct = kelly_pct * kelly_fraction
            
            # Adjust for signal confidence
            # Low confidence = further reduce position
            confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5 to 1.0
            adjusted_kelly_pct = fractional_kelly_pct * confidence_multiplier
            
            # Calculate position size
            # Kelly gives fraction of bankroll to risk
            # For leveraged trades, this is the position size
            position_size = balance * adjusted_kelly_pct
            
            # Safety bounds
            max_position_pct = 0.10  # Never risk more than 10% of balance
            min_position_pct = 0.005  # Minimum 0.5% position
            
            position_size = max(
                balance * min_position_pct,
                min(balance * max_position_pct, position_size)
            )
            
            # Use conservative estimate if uncertain
            if win_stats['n_trades'] < 20:
                # Not enough data, use conservative sizing
                position_size = balance * 0.01 * confidence
                recommendation = "conservative (insufficient data)"
            elif uncertainty > 0.15:
                # High uncertainty, be more conservative
                position_size *= 0.7
                recommendation = "conservative (high uncertainty)"
            elif p < 0.45:
                # Low win rate, be very conservative
                position_size *= 0.5
                recommendation = "very conservative (low win rate)"
            else:
                recommendation = "optimal"
            
            result = {
                'position_size': position_size,
                'position_pct': position_size / balance,
                'kelly_pct': kelly_pct,
                'fractional_kelly_pct': fractional_kelly_pct,
                'adjusted_kelly_pct': adjusted_kelly_pct,
                'kelly_fraction_used': kelly_fraction,
                'win_rate_mean': p,
                'win_rate_std': uncertainty,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'win_loss_ratio': b,
                'confidence_multiplier': confidence_multiplier,
                'n_trades': win_stats['n_trades'],
                'recommendation': recommendation
            }
            
            self.logger.info(f"Bayesian Kelly sizing: ${position_size:.2f} "
                           f"({(position_size/balance)*100:.2f}% of balance) - {recommendation}")
            self.logger.debug(f"  Win rate: {p:.3f}±{uncertainty:.3f}, "
                            f"W/L ratio: {b:.2f}, Kelly fraction: {kelly_fraction:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating optimal position size: {e}")
            # Return safe default
            return {
                'position_size': balance * 0.01,
                'position_pct': 0.01,
                'recommendation': 'fallback (error)'
            }
    
    def get_risk_recommendation(self, balance: float,
                               confidence: float,
                               market_regime: str = 'neutral',
                               market_volatility: float = 0.03) -> Dict:
        """
        Get comprehensive risk management recommendation
        
        Args:
            balance: Account balance
            confidence: Signal confidence
            market_regime: Current market regime
            market_volatility: Market volatility measure
            
        Returns:
            Comprehensive risk recommendation
        """
        try:
            # Get base Kelly sizing
            kelly_result = self.calculate_optimal_position_size(
                balance, confidence, market_volatility
            )
            
            # Adjust for market regime
            regime_multipliers = {
                'bull_trending': 1.15,  # More aggressive in bull
                'bear_trending': 0.80,  # More conservative in bear
                'ranging': 0.90,        # Slightly conservative in range
                'high_volatility': 0.70,  # Very conservative in high vol
                'low_volatility': 1.05,   # Slightly more aggressive in low vol
                'neutral': 1.0
            }
            
            regime_mult = regime_multipliers.get(market_regime, 1.0)
            adjusted_size = kelly_result['position_size'] * regime_mult
            
            # Calculate risk metrics
            win_rate = kelly_result['win_rate_mean']
            avg_loss = kelly_result['avg_loss']
            
            # Expected loss on this trade (if it loses)
            expected_loss = adjusted_size * avg_loss
            
            # Risk of ruin approximation
            # Simplified formula for risk of ruin over N trades
            n_trades = 100
            if win_rate > 0.5:
                risk_of_ruin = ((1 - win_rate) / win_rate) ** n_trades
            else:
                risk_of_ruin = 1.0  # Very high if win rate < 50%
            
            recommendation = {
                'position_size': adjusted_size,
                'position_pct': (adjusted_size / balance) * 100,
                'regime_adjustment': regime_mult,
                'regime': market_regime,
                'expected_loss_if_wrong': expected_loss,
                'expected_loss_pct': (expected_loss / balance) * 100,
                'risk_of_ruin': risk_of_ruin,
                'kelly_details': kelly_result,
                'max_recommended_leverage': self._calculate_max_leverage(
                    kelly_result, market_volatility
                )
            }
            
            self.logger.info(f"Risk recommendation: ${adjusted_size:.2f} "
                           f"({(adjusted_size/balance)*100:.2f}%), "
                           f"regime={market_regime}, max_lev={recommendation['max_recommended_leverage']}x")
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error getting risk recommendation: {e}")
            return {
                'position_size': balance * 0.01,
                'position_pct': 1.0,
                'recommendation': 'fallback (error)'
            }
    
    def _calculate_max_leverage(self, kelly_result: Dict,
                               market_volatility: float) -> int:
        """
        Calculate maximum recommended leverage based on Kelly sizing
        
        Args:
            kelly_result: Kelly calculation results
            market_volatility: Market volatility
            
        Returns:
            Maximum recommended leverage (3-15x)
        """
        try:
            win_rate = kelly_result['win_rate_mean']
            uncertainty = kelly_result['win_rate_std']
            
            # Base leverage on win rate and uncertainty
            if win_rate > 0.65 and uncertainty < 0.10 and market_volatility < 0.04:
                max_lev = 12
            elif win_rate > 0.60 and uncertainty < 0.12:
                max_lev = 10
            elif win_rate > 0.55:
                max_lev = 8
            elif win_rate > 0.50:
                max_lev = 6
            else:
                max_lev = 5
            
            # Further reduce for high volatility
            if market_volatility > 0.06:
                max_lev = max(3, max_lev - 3)
            
            return max_lev
            
        except Exception as e:
            self.logger.error(f"Error calculating max leverage: {e}")
            return 5  # Safe default
