"""
Strategy Optimizer - Advanced optimizations for buy/sell strategies

This module provides:
- Dynamic threshold adjustment based on market conditions
- Enhanced entry/exit signal filtering
- Multi-factor position sizing optimization
- Adaptive strategy parameter tuning
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from logger import Logger


class StrategyOptimizer:
    """
    Optimizes trading strategies for better performance
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        
        # Performance tracking for optimization
        self.recent_trades = []
        self.max_history = 100
        
        # Adaptive thresholds
        self.base_confidence_threshold = 0.62
        self.current_confidence_threshold = 0.62
        
        # Optimization parameters
        self.win_rate_target = 0.75
        self.min_risk_reward = 2.0
        
        self.logger.info("🔧 Strategy Optimizer initialized")
    
    def optimize_entry_signal(self, signal: str, confidence: float,
                             indicators: Dict, reasons: Dict) -> Tuple[str, float, Dict]:
        """
        Optimize entry signal with additional filters and adjustments
        
        Returns:
            (optimized_signal, optimized_confidence, enhanced_reasons)
        """
        if signal == 'HOLD':
            return signal, confidence, reasons
        
        optimized_signal = signal
        optimized_confidence = confidence
        enhanced_reasons = reasons.copy()
        
        # OPTIMIZATION 1: Volume-Price Divergence Check
        # Ensure volume supports the price move
        volume_ratio = indicators.get('volume_ratio', 1.0)
        momentum = indicators.get('momentum', 0)
        
        if signal == 'BUY' and momentum > 0.01:
            # Bullish price move should have good volume
            if volume_ratio < 1.0:
                # Price up but volume declining = potential false breakout
                optimized_confidence *= 0.85
                enhanced_reasons['volume_divergence'] = 'bearish (price up, volume down)'
                self.logger.debug(f"Volume divergence detected on BUY signal: {volume_ratio:.2f}")
        
        elif signal == 'SELL' and momentum < -0.01:
            # Bearish price move should have good volume
            if volume_ratio < 1.0:
                # Price down but volume declining = potential false breakdown
                optimized_confidence *= 0.85
                enhanced_reasons['volume_divergence'] = 'bullish (price down, volume down)'
                self.logger.debug(f"Volume divergence detected on SELL signal: {volume_ratio:.2f}")
        
        # OPTIMIZATION 2: Multi-Timeframe Momentum Alignment
        # Check if short-term momentum aligns with signal
        roc = indicators.get('roc', 0)
        macd_diff = indicators.get('macd_diff', 0)
        
        momentum_alignment_score = 0
        if signal == 'BUY':
            if momentum > 0:
                momentum_alignment_score += 1
            if roc > 0:
                momentum_alignment_score += 1
            if macd_diff > 0:
                momentum_alignment_score += 1
        elif signal == 'SELL':
            if momentum < 0:
                momentum_alignment_score += 1
            if roc < 0:
                momentum_alignment_score += 1
            if macd_diff < 0:
                momentum_alignment_score += 1
        
        # All 3 momentum indicators should align
        if momentum_alignment_score == 3:
            optimized_confidence *= 1.05  # Small boost for perfect alignment
            enhanced_reasons['momentum_alignment'] = 'perfect'
        elif momentum_alignment_score < 2:
            optimized_confidence *= 0.90  # Penalty for poor alignment
            enhanced_reasons['momentum_alignment'] = 'weak'
        
        # OPTIMIZATION 3: Volatility Regime Check
        # Adjust based on current volatility environment
        bb_width = indicators.get('bb_width', 0)
        atr = indicators.get('atr', 0)
        
        # Calculate volatility percentile (simplified)
        if bb_width < 0.015:
            volatility_regime = 'low'
        elif bb_width < 0.04:
            volatility_regime = 'normal'
        elif bb_width < 0.07:
            volatility_regime = 'high'
        else:
            volatility_regime = 'extreme'
        
        enhanced_reasons['volatility_regime'] = volatility_regime
        
        # Adjust confidence based on volatility
        if volatility_regime == 'extreme':
            # Extreme volatility = higher risk
            optimized_confidence *= 0.85
            enhanced_reasons['volatility_adjustment'] = 'reduced (extreme vol)'
        elif volatility_regime == 'low':
            # Low volatility may lead to false breakouts
            if signal in ['BUY', 'SELL']:
                optimized_confidence *= 0.92
                enhanced_reasons['volatility_adjustment'] = 'reduced (low vol)'
        
        # OPTIMIZATION 4: Support/Resistance Confluence
        # Check proximity to key levels
        close = indicators.get('close', 0)
        bb_low = indicators.get('bb_low', 0)
        bb_high = indicators.get('bb_high', 0)
        bb_mid = indicators.get('bb_mid', 0)
        
        if signal == 'BUY':
            # Better entries near support
            distance_to_support = (close - bb_low) / close if close > 0 else 1
            if distance_to_support < 0.01:  # Within 1% of support
                optimized_confidence *= 1.08
                enhanced_reasons['entry_level'] = 'excellent (at support)'
            elif distance_to_support < 0.02:  # Within 2%
                optimized_confidence *= 1.03
                enhanced_reasons['entry_level'] = 'good (near support)'
            elif distance_to_support > 0.05:  # Far from support
                optimized_confidence *= 0.93
                enhanced_reasons['entry_level'] = 'poor (far from support)'
        
        elif signal == 'SELL':
            # Better entries near resistance
            distance_to_resistance = (bb_high - close) / close if close > 0 else 1
            if distance_to_resistance < 0.01:  # Within 1% of resistance
                optimized_confidence *= 1.08
                enhanced_reasons['entry_level'] = 'excellent (at resistance)'
            elif distance_to_resistance < 0.02:  # Within 2%
                optimized_confidence *= 1.03
                enhanced_reasons['entry_level'] = 'good (near resistance)'
            elif distance_to_resistance > 0.05:  # Far from resistance
                optimized_confidence *= 0.93
                enhanced_reasons['entry_level'] = 'poor (far from resistance)'
        
        # OPTIMIZATION 5: RSI Divergence Enhancement
        # Look for hidden divergences
        rsi = indicators.get('rsi', 50)
        
        if signal == 'BUY':
            # RSI should not be overbought on BUY
            if rsi > 65:
                optimized_confidence *= 0.88
                enhanced_reasons['rsi_warning'] = f'elevated RSI ({rsi:.1f})'
            # Bonus for very oversold
            elif rsi < 25:
                optimized_confidence *= 1.10
                enhanced_reasons['rsi_bonus'] = f'extreme oversold ({rsi:.1f})'
        
        elif signal == 'SELL':
            # RSI should not be oversold on SELL
            if rsi < 35:
                optimized_confidence *= 0.88
                enhanced_reasons['rsi_warning'] = f'low RSI ({rsi:.1f})'
            # Bonus for very overbought
            elif rsi > 75:
                optimized_confidence *= 1.10
                enhanced_reasons['rsi_bonus'] = f'extreme overbought ({rsi:.1f})'
        
        # Cap confidence at 0.99
        optimized_confidence = min(0.99, optimized_confidence)
        
        # Final threshold check with adaptive threshold
        if optimized_confidence < self.current_confidence_threshold:
            optimized_signal = 'HOLD'
            enhanced_reasons['optimization_result'] = f'confidence too low ({optimized_confidence:.2f} < {self.current_confidence_threshold:.2f})'
        
        return optimized_signal, optimized_confidence, enhanced_reasons
    
    def optimize_position_size(self, base_size: float, signal: str,
                               confidence: float, indicators: Dict,
                               account_balance: float) -> float:
        """
        Optimize position size based on multiple factors
        
        Args:
            base_size: Base position size from risk manager
            signal: BUY or SELL
            confidence: Signal confidence
            indicators: Technical indicators
            account_balance: Current account balance
            
        Returns:
            Optimized position size
        """
        optimized_size = base_size
        
        # Factor 1: Confidence-based scaling
        # Higher confidence = larger position (up to 25% increase)
        if confidence > 0.80:
            confidence_multiplier = 1.25
        elif confidence > 0.70:
            confidence_multiplier = 1.15
        elif confidence > 0.65:
            confidence_multiplier = 1.05
        else:
            confidence_multiplier = 0.90  # Reduce for lower confidence
        
        optimized_size *= confidence_multiplier
        
        # Factor 2: Volatility-based scaling
        # Lower volatility = can use larger size
        bb_width = indicators.get('bb_width', 0.03)
        atr = indicators.get('atr', 0)
        
        if bb_width < 0.02:  # Low volatility
            volatility_multiplier = 1.15
        elif bb_width < 0.04:  # Normal volatility
            volatility_multiplier = 1.0
        elif bb_width < 0.06:  # High volatility
            volatility_multiplier = 0.85
        else:  # Extreme volatility
            volatility_multiplier = 0.70
        
        optimized_size *= volatility_multiplier
        
        # Factor 3: Volume-based scaling
        # Higher volume = more liquid = can use larger size
        volume_ratio = indicators.get('volume_ratio', 1.0)
        
        if volume_ratio > 2.0:
            volume_multiplier = 1.10
        elif volume_ratio > 1.5:
            volume_multiplier = 1.05
        elif volume_ratio < 0.8:
            volume_multiplier = 0.85
        else:
            volume_multiplier = 1.0
        
        optimized_size *= volume_multiplier
        
        # Factor 4: Recent performance scaling
        # Reduce size during losing streaks
        if len(self.recent_trades) >= 5:
            recent_pnl = [t.get('pnl', 0) for t in self.recent_trades[-5:]]
            losing_trades = sum(1 for pnl in recent_pnl if pnl < 0)
            
            if losing_trades >= 3:  # 3+ losses in last 5
                performance_multiplier = 0.75
            elif losing_trades >= 2:
                performance_multiplier = 0.90
            else:
                performance_multiplier = 1.0
            
            optimized_size *= performance_multiplier
        
        # Cap at maximum reasonable size (50% of base for safety)
        max_size = base_size * 1.5
        min_size = base_size * 0.5
        
        optimized_size = max(min_size, min(optimized_size, max_size))
        
        self.logger.debug(
            f"Position size optimized: {base_size:.4f} → {optimized_size:.4f} "
            f"(conf: {confidence_multiplier:.2f}, vol: {volatility_multiplier:.2f}, "
            f"volume: {volume_multiplier:.2f})"
        )
        
        return optimized_size
    
    def adjust_dynamic_threshold(self):
        """
        Dynamically adjust confidence threshold based on recent performance
        """
        if len(self.recent_trades) < 20:
            return  # Need more data
        
        # Calculate recent win rate
        recent_20 = self.recent_trades[-20:]
        wins = sum(1 for t in recent_20 if t.get('pnl', 0) > 0)
        win_rate = wins / 20
        
        # Adjust threshold to reach target win rate
        if win_rate < self.win_rate_target - 0.05:
            # Win rate too low, increase threshold
            self.current_confidence_threshold = min(
                0.75, 
                self.current_confidence_threshold + 0.02
            )
            self.logger.info(
                f"📈 Increasing confidence threshold to {self.current_confidence_threshold:.2f} "
                f"(win rate: {win_rate:.1%})"
            )
        elif win_rate > self.win_rate_target + 0.05:
            # Win rate high, can lower threshold for more trades
            self.current_confidence_threshold = max(
                0.55,
                self.current_confidence_threshold - 0.01
            )
            self.logger.info(
                f"📉 Decreasing confidence threshold to {self.current_confidence_threshold:.2f} "
                f"(win rate: {win_rate:.1%})"
            )
    
    def record_trade_outcome(self, trade_data: Dict):
        """
        Record trade outcome for optimization learning
        
        Args:
            trade_data: Dict with trade details and outcome
        """
        self.recent_trades.append({
            'timestamp': datetime.now(),
            'signal': trade_data.get('signal'),
            'confidence': trade_data.get('confidence'),
            'pnl': trade_data.get('pnl', 0),
            'hold_time': trade_data.get('hold_time', 0)
        })
        
        # Keep only recent history
        if len(self.recent_trades) > self.max_history:
            self.recent_trades = self.recent_trades[-self.max_history:]
        
        # Adjust threshold periodically
        if len(self.recent_trades) % 20 == 0:
            self.adjust_dynamic_threshold()
    
    def get_optimization_stats(self) -> Dict:
        """
        Get current optimization statistics
        
        Returns:
            Dict with optimization metrics
        """
        if not self.recent_trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'current_threshold': self.current_confidence_threshold
            }
        
        total = len(self.recent_trades)
        wins = sum(1 for t in self.recent_trades if t.get('pnl', 0) > 0)
        losses = sum(1 for t in self.recent_trades if t.get('pnl', 0) < 0)
        
        total_pnl = sum(t.get('pnl', 0) for t in self.recent_trades)
        avg_pnl = total_pnl / total if total > 0 else 0
        
        return {
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'win_rate': wins / total if total > 0 else 0,
            'avg_pnl': avg_pnl,
            'current_threshold': self.current_confidence_threshold,
            'base_threshold': self.base_confidence_threshold,
            'threshold_adjustment': self.current_confidence_threshold - self.base_confidence_threshold
        }
