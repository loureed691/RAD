"""
Advanced Risk Management Module for 2026
Implements cutting-edge risk management techniques for maximum profitability
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger


class AdvancedRiskManager2026:
    """
    Next-generation risk management with:
    - Dynamic position sizing based on market volatility regime
    - Multi-factor risk assessment (volatility, liquidity, correlation)
    - Adaptive Kelly Criterion with regime awareness
    - Real-time portfolio heat map
    - Smart leverage adjustment based on market conditions
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        
        # Market regime detection
        self.current_regime = 'neutral'  # 'bull', 'bear', 'neutral', 'high_vol', 'low_vol'
        self.regime_history = []
        
        # Advanced position sizing parameters
        self.base_kelly_fraction = 0.25  # Conservative Kelly for 2026
        self.volatility_scalar = 1.0
        self.liquidity_scalar = 1.0
        self.correlation_penalty = 0.0
        
        # Portfolio heat metrics
        self.portfolio_heat = 0.0  # 0-100 scale
        self.max_portfolio_heat = 80.0  # Don't trade if heat > 80
        
        # Advanced volatility tracking
        self.volatility_ewma = None  # Exponentially weighted moving average
        self.volatility_std = None
        
        self.logger.info("🚀 Advanced Risk Manager 2026 initialized")
    
    def detect_market_regime(self, price_data: np.ndarray, 
                            volume_data: np.ndarray,
                            lookback: int = 50) -> str:
        """
        Detect current market regime using multiple factors
        
        Args:
            price_data: Recent price data
            volume_data: Recent volume data
            lookback: Number of periods to analyze
            
        Returns:
            Market regime: 'bull', 'bear', 'neutral', 'high_vol', 'low_vol'
        """
        if len(price_data) < lookback:
            return 'neutral'
        
        try:
            # Calculate returns
            returns = np.diff(price_data[-lookback:]) / price_data[-lookback:-1]
            
            # Volatility (annualized)
            volatility = np.std(returns) * np.sqrt(252)
            
            # Trend strength (linear regression slope)
            x = np.arange(lookback)
            y = price_data[-lookback:]
            slope = np.polyfit(x, y, 1)[0]
            trend_strength = slope / np.mean(y)  # Normalized
            
            # Volume trend
            vol_ma = np.mean(volume_data[-lookback:])
            recent_vol = np.mean(volume_data[-10:])
            volume_ratio = recent_vol / vol_ma if vol_ma > 0 else 1.0
            
            # Regime classification
            if volatility > 0.6:  # High volatility regime
                regime = 'high_vol'
            elif volatility < 0.2:  # Low volatility regime
                regime = 'low_vol'
            elif trend_strength > 0.002 and volume_ratio > 1.2:  # Strong uptrend
                regime = 'bull'
            elif trend_strength < -0.002 and volume_ratio > 1.2:  # Strong downtrend
                regime = 'bear'
            else:
                regime = 'neutral'
            
            # Update regime history
            self.regime_history.append({
                'timestamp': datetime.now(),
                'regime': regime,
                'volatility': volatility,
                'trend_strength': trend_strength,
                'volume_ratio': volume_ratio
            })
            
            # Keep last 100 regime observations
            if len(self.regime_history) > 100:
                self.regime_history.pop(0)
            
            self.current_regime = regime
            
            self.logger.debug(
                f"Market regime: {regime} (vol={volatility:.2f}, "
                f"trend={trend_strength:.4f}, vol_ratio={volume_ratio:.2f})"
            )
            
            return regime
            
        except Exception as e:
            self.logger.error(f"Error detecting market regime: {e}")
            return 'neutral'
    
    def calculate_regime_aware_kelly(self, win_rate: float, avg_win: float,
                                    avg_loss: float, market_regime: str,
                                    confidence: float = 0.7) -> float:
        """
        Calculate Kelly Criterion adjusted for market regime and confidence
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning percentage
            avg_loss: Average losing percentage
            market_regime: Current market regime
            confidence: Signal confidence (0-1)
            
        Returns:
            Optimal position fraction (0-1)
        """
        if win_rate <= 0 or avg_win <= 0 or avg_loss <= 0:
            return 0.15  # Default conservative sizing
        
        # Standard Kelly Criterion
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate
        kelly = (b * p - q) / b
        
        # Regime-based adjustments
        regime_multipliers = {
            'bull': 1.15,      # Slightly more aggressive in bull markets
            'bear': 0.75,      # Very conservative in bear markets
            'neutral': 1.0,    # Standard sizing
            'high_vol': 0.65,  # Much more conservative in high volatility
            'low_vol': 1.05    # Slightly more aggressive in low volatility
        }
        
        regime_mult = regime_multipliers.get(market_regime, 1.0)
        
        # Confidence adjustment (reduce size if confidence is low)
        confidence_mult = 0.5 + (confidence * 0.5)  # Scale 0.5-1.0
        
        # Apply fractional Kelly (conservative approach for 2026)
        fractional_kelly = kelly * self.base_kelly_fraction
        
        # Apply all adjustments
        final_kelly = fractional_kelly * regime_mult * confidence_mult
        
        # Clamp to reasonable bounds
        final_kelly = max(0.05, min(0.35, final_kelly))
        
        self.logger.debug(
            f"Regime-aware Kelly: {final_kelly:.3f} "
            f"(base={fractional_kelly:.3f}, regime_mult={regime_mult:.2f}, "
            f"conf_mult={confidence_mult:.2f})"
        )
        
        return final_kelly
    
    def calculate_portfolio_heat(self, open_positions: List[Dict],
                                correlations: Dict[str, float]) -> float:
        """
        Calculate portfolio heat score (risk concentration metric)
        
        Args:
            open_positions: List of current open positions
            correlations: Correlation coefficients between positions
            
        Returns:
            Portfolio heat score (0-100)
        """
        if not open_positions:
            return 0.0
        
        try:
            # Base heat from number of positions
            position_count = len(open_positions)
            base_heat = (position_count / 10) * 30  # Max 30 points from count
            
            # Heat from leverage
            total_leverage = sum(pos.get('leverage', 1) for pos in open_positions)
            avg_leverage = total_leverage / position_count
            leverage_heat = min((avg_leverage / 15) * 30, 30)  # Max 30 points
            
            # Heat from correlation (positions moving together = higher risk)
            correlation_heat = 0.0
            if correlations:
                avg_correlation = np.mean(list(correlations.values()))
                correlation_heat = min(avg_correlation * 40, 40)  # Max 40 points
            
            total_heat = base_heat + leverage_heat + correlation_heat
            
            self.portfolio_heat = min(total_heat, 100.0)
            
            if self.portfolio_heat > 70:
                self.logger.warning(
                    f"⚠️ High portfolio heat: {self.portfolio_heat:.1f} "
                    f"(positions={position_count}, avg_lev={avg_leverage:.1f})"
                )
            
            return self.portfolio_heat
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio heat: {e}")
            return 50.0  # Conservative default
    
    def should_open_position(self, signal_confidence: float,
                           market_regime: str,
                           portfolio_heat: float,
                           liquidity_score: float = 1.0) -> Tuple[bool, str]:
        """
        Determine if we should open a new position based on multiple factors
        
        Args:
            signal_confidence: Trading signal confidence (0-1)
            market_regime: Current market regime
            portfolio_heat: Current portfolio heat (0-100)
            liquidity_score: Market liquidity score (0-1)
            
        Returns:
            Tuple of (should_trade, reason)
        """
        # Regime-specific confidence thresholds
        confidence_thresholds = {
            'bull': 0.60,
            'bear': 0.70,      # More selective in bear markets
            'neutral': 0.65,
            'high_vol': 0.75,  # Very selective in high volatility
            'low_vol': 0.62
        }
        
        required_confidence = confidence_thresholds.get(market_regime, 0.65)
        
        # Check confidence
        if signal_confidence < required_confidence:
            return False, f"Confidence too low: {signal_confidence:.2f} < {required_confidence:.2f}"
        
        # Check portfolio heat
        if portfolio_heat > self.max_portfolio_heat:
            return False, f"Portfolio heat too high: {portfolio_heat:.1f} > {self.max_portfolio_heat:.1f}"
        
        # Check liquidity
        if liquidity_score < 0.5:
            return False, f"Insufficient liquidity: {liquidity_score:.2f}"
        
        # High volatility regime - extra caution
        if market_regime == 'high_vol' and portfolio_heat > 60:
            return False, f"High volatility + elevated portfolio heat ({portfolio_heat:.1f})"
        
        return True, "All risk checks passed"
    
    def calculate_dynamic_stop_loss(self, entry_price: float,
                                   atr: float,
                                   support_level: Optional[float] = None,
                                   market_regime: str = 'neutral',
                                   position_side: str = 'long') -> float:
        """
        Calculate intelligent stop loss using ATR and support/resistance
        
        Args:
            entry_price: Position entry price
            atr: Average True Range
            support_level: Nearest support level (for longs) or resistance (for shorts)
            market_regime: Current market regime
            position_side: 'long' or 'short'
            
        Returns:
            Stop loss price
        """
        # Base stop loss using ATR (2x ATR is common)
        atr_multiplier = {
            'bull': 1.5,      # Tighter stops in bull markets
            'bear': 2.5,      # Wider stops in bear markets
            'neutral': 2.0,
            'high_vol': 2.5,  # Wider stops in high volatility
            'low_vol': 1.5    # Tighter stops in low volatility
        }
        
        multiplier = atr_multiplier.get(market_regime, 2.0)
        atr_stop_distance = atr * multiplier
        
        if position_side == 'long':
            # For longs, stop below entry
            atr_stop = entry_price - atr_stop_distance
            
            # If we have support level, use it if it's closer than ATR stop
            if support_level and support_level > atr_stop:
                stop_loss = support_level * 0.995  # Slightly below support
                reason = "support-based"
            else:
                stop_loss = atr_stop
                reason = "ATR-based"
        else:
            # For shorts, stop above entry
            atr_stop = entry_price + atr_stop_distance
            
            # If we have resistance level, use it if it's closer than ATR stop
            if support_level and support_level < atr_stop:  # support_level is resistance for shorts
                stop_loss = support_level * 1.005  # Slightly above resistance
                reason = "resistance-based"
            else:
                stop_loss = atr_stop
                reason = "ATR-based"
        
        self.logger.debug(
            f"Dynamic stop loss: ${stop_loss:.2f} ({reason}, "
            f"regime={market_regime}, ATR={atr:.2f})"
        )
        
        return stop_loss
    
    def calculate_position_size_2026(self, account_balance: float,
                                    kelly_fraction: float,
                                    leverage: int,
                                    max_position_size: float,
                                    volatility_adjustment: float = 1.0) -> float:
        """
        Calculate optimal position size for 2026 with multiple safety factors
        
        Args:
            account_balance: Current account balance
            kelly_fraction: Kelly criterion fraction (0-1)
            leverage: Leverage to use
            max_position_size: Maximum allowed position size
            volatility_adjustment: Adjustment factor for volatility (0.5-1.5)
            
        Returns:
            Position size in USDT
        """
        # Kelly-based sizing
        kelly_size = account_balance * kelly_fraction
        
        # Volatility adjustment (reduce size in high volatility)
        vol_adjusted_size = kelly_size * volatility_adjustment
        
        # Leverage consideration (higher leverage = smaller position)
        leverage_adjusted = vol_adjusted_size * (10 / max(leverage, 1))
        
        # Apply maximum position size limit
        final_size = min(leverage_adjusted, max_position_size)
        
        # Ensure minimum position size (for fee efficiency)
        min_position_size = 10.0  # $10 minimum
        final_size = max(final_size, min_position_size)
        
        self.logger.debug(
            f"Position sizing: kelly=${kelly_size:.2f}, "
            f"vol_adj=${vol_adjusted_size:.2f}, "
            f"lev_adj=${leverage_adjusted:.2f}, "
            f"final=${final_size:.2f}"
        )
        
        return final_size
    
    def get_regime_statistics(self) -> Dict:
        """
        Get statistics about market regime history
        
        Returns:
            Dictionary with regime statistics
        """
        if not self.regime_history:
            return {
                'current_regime': self.current_regime,
                'regime_stability': 0.0,
                'avg_volatility': 0.0
            }
        
        recent_regimes = [r['regime'] for r in self.regime_history[-20:]]
        regime_counts = {}
        for regime in recent_regimes:
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        # Stability = how often current regime appears
        stability = regime_counts.get(self.current_regime, 0) / len(recent_regimes)
        
        # Average volatility
        recent_vols = [r['volatility'] for r in self.regime_history[-20:]]
        avg_vol = np.mean(recent_vols) if recent_vols else 0.0
        
        return {
            'current_regime': self.current_regime,
            'regime_stability': stability,
            'avg_volatility': avg_vol,
            'regime_distribution': regime_counts,
            'portfolio_heat': self.portfolio_heat
        }
