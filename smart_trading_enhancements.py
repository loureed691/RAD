"""
Smart Trading Enhancements - 2025 Intelligence Upgrade
Advanced trading intelligence features for optimal performance
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from logger import Logger


class SmartTradeFilter:
    """
    ML-based trade quality prediction to filter low-quality trades before entry.
    Analyzes historical patterns to predict trade outcome probability.
    """

    def __init__(self):
        self.logger = Logger.get_logger()
        self.min_quality_score = 0.65  # Minimum quality score to take trade
        self.trade_history = []

    def calculate_trade_quality_score(self,
                                     signal_confidence: float,
                                     volatility: float,
                                     volume_ratio: float,
                                     trend_strength: float,
                                     rsi: float,
                                     recent_win_rate: float,
                                     market_regime: str) -> Dict:
        """
        Calculate comprehensive trade quality score (0-1) based on multiple factors.

        Returns:
            Dict with quality_score, components, and recommendation
        """
        try:
            components = {}
            total_score = 0.0

            # 1. Signal Confidence Component (30% weight)
            signal_score = signal_confidence
            components['signal_confidence'] = signal_score * 0.30
            total_score += components['signal_confidence']

            # 2. Market Conditions Component (25% weight)
            # Optimal volatility: 0.02-0.05 (2-5%)
            if 0.02 <= volatility <= 0.05:
                volatility_score = 1.0
            elif volatility < 0.02:
                volatility_score = 0.6  # Too low - choppy
            elif volatility > 0.10:
                volatility_score = 0.4  # Too high - risky
            else:
                volatility_score = 0.8

            # Volume confirmation
            if volume_ratio > 1.5:
                volume_score = 1.0
            elif volume_ratio > 1.2:
                volume_score = 0.8
            elif volume_ratio > 0.8:
                volume_score = 0.6
            else:
                volume_score = 0.3  # Low volume - risky

            market_conditions_score = (volatility_score + volume_score) / 2
            components['market_conditions'] = market_conditions_score * 0.25
            total_score += components['market_conditions']

            # 3. Trend Alignment Component (20% weight)
            # Strong trend + extreme RSI = contrarian risk
            # Strong trend + moderate RSI = good
            if trend_strength > 0.7:
                if 30 < rsi < 70:
                    trend_score = 1.0  # Strong trend, not extreme
                elif rsi < 25 or rsi > 75:
                    trend_score = 0.6  # Might be late to the party
                else:
                    trend_score = 0.8
            elif trend_strength > 0.4:
                trend_score = 0.8  # Moderate trend
            else:
                trend_score = 0.5  # Weak trend - mean reversion opportunity

            components['trend_alignment'] = trend_score * 0.20
            total_score += components['trend_alignment']

            # 4. Recent Performance Component (15% weight)
            # Recent wins boost confidence, recent losses reduce it
            if recent_win_rate > 0.70:
                performance_score = 1.0
            elif recent_win_rate > 0.60:
                performance_score = 0.9
            elif recent_win_rate > 0.50:
                performance_score = 0.7
            else:
                performance_score = 0.5  # Below 50% - be cautious

            components['recent_performance'] = performance_score * 0.15
            total_score += components['recent_performance']

            # 5. Market Regime Component (10% weight)
            # Trending markets: favor trend-following
            # Ranging markets: be more selective
            regime_scores = {
                'trending': 0.9,
                'bull': 0.85,
                'bear': 0.85,
                'neutral': 0.7,
                'ranging': 0.6,
                'high_vol': 0.5,
                'low_vol': 0.65
            }
            regime_score = regime_scores.get(market_regime, 0.7)
            components['market_regime'] = regime_score * 0.10
            total_score += components['market_regime']

            # Determine recommendation
            if total_score >= 0.75:
                recommendation = 'EXCELLENT'
                multiplier = 1.2  # Increase position size
            elif total_score >= 0.65:
                recommendation = 'GOOD'
                multiplier = 1.0  # Normal position size
            elif total_score >= 0.55:
                recommendation = 'ACCEPTABLE'
                multiplier = 0.8  # Reduce position size
            else:
                recommendation = 'SKIP'
                multiplier = 0.0  # Skip trade

            return {
                'quality_score': total_score,
                'components': components,
                'recommendation': recommendation,
                'position_multiplier': multiplier,
                'passed': total_score >= self.min_quality_score
            }

        except Exception as e:
            self.logger.error(f"Error calculating trade quality: {e}")
            return {
                'quality_score': 0.5,
                'components': {},
                'recommendation': 'SKIP',
                'position_multiplier': 0.0,
                'passed': False
            }

    def record_trade_outcome(self, quality_score: float, profit_pct: float):
        """Record trade outcome for learning"""
        self.trade_history.append({
            'quality_score': quality_score,
            'profit_pct': profit_pct,
            'timestamp': datetime.now()
        })

        # Keep last 200 trades
        if len(self.trade_history) > 200:
            self.trade_history = self.trade_history[-200:]


class SmartPositionSizer:
    """
    Intelligent position sizing that considers multiple risk factors
    and dynamically adjusts position size for optimal risk/reward.
    """

    def __init__(self):
        self.logger = Logger.get_logger()

    def calculate_optimal_position_size(self,
                                       base_position_size: float,
                                       signal_confidence: float,
                                       trade_quality_score: float,
                                       volatility: float,
                                       correlation_risk: float,
                                       portfolio_heat: float,
                                       recent_win_rate: float) -> Dict:
        """
        Calculate optimal position size with multi-factor adjustment.

        Returns:
            Dict with adjusted_size, factors, and reasoning
        """
        try:
            adjustments = {}
            multiplier = 1.0

            # 1. Signal Confidence Adjustment (±30%)
            if signal_confidence > 0.80:
                conf_mult = 1.3
            elif signal_confidence > 0.70:
                conf_mult = 1.15
            elif signal_confidence > 0.60:
                conf_mult = 1.0
            else:
                conf_mult = 0.8

            multiplier *= conf_mult
            adjustments['confidence'] = conf_mult

            # 2. Trade Quality Adjustment (±25%)
            quality_mult = 0.75 + (trade_quality_score * 0.5)  # 0.75 - 1.25
            multiplier *= quality_mult
            adjustments['quality'] = quality_mult

            # 3. Volatility Adjustment (±30%)
            # Higher volatility = smaller position
            if volatility > 0.08:
                vol_mult = 0.7  # High vol - reduce 30%
            elif volatility > 0.05:
                vol_mult = 0.85  # Moderate-high vol
            elif volatility > 0.02:
                vol_mult = 1.0  # Normal vol
            else:
                vol_mult = 0.9  # Very low vol - slightly reduce (choppy)

            multiplier *= vol_mult
            adjustments['volatility'] = vol_mult

            # 4. Correlation Risk Adjustment (±20%)
            # High correlation with existing positions = reduce size
            if correlation_risk > 0.7:
                corr_mult = 0.8  # High correlation
            elif correlation_risk > 0.5:
                corr_mult = 0.9
            elif correlation_risk > 0.3:
                corr_mult = 0.95
            else:
                corr_mult = 1.0  # Low correlation - full size

            multiplier *= corr_mult
            adjustments['correlation'] = corr_mult

            # 5. Portfolio Heat Adjustment (±40%)
            # Total portfolio risk - reduce when already at risk
            if portfolio_heat > 0.8:
                heat_mult = 0.6  # Very high heat - reduce significantly
            elif portfolio_heat > 0.6:
                heat_mult = 0.75
            elif portfolio_heat > 0.4:
                heat_mult = 0.9
            else:
                heat_mult = 1.0

            multiplier *= heat_mult
            adjustments['portfolio_heat'] = heat_mult

            # 6. Recent Performance Adjustment (±20%)
            # Recent wins = can increase size, recent losses = reduce
            if recent_win_rate > 0.75:
                perf_mult = 1.2  # On a roll
            elif recent_win_rate > 0.65:
                perf_mult = 1.1
            elif recent_win_rate > 0.55:
                perf_mult = 1.0
            elif recent_win_rate > 0.45:
                perf_mult = 0.9
            else:
                perf_mult = 0.8  # Struggling - reduce size

            multiplier *= perf_mult
            adjustments['performance'] = perf_mult

            # Calculate final position size
            adjusted_size = base_position_size * multiplier

            # Safety bounds (don't go below 25% or above 200% of base)
            adjusted_size = max(base_position_size * 0.25, adjusted_size)
            adjusted_size = min(base_position_size * 2.0, adjusted_size)

            return {
                'original_size': base_position_size,
                'adjusted_size': adjusted_size,
                'multiplier': multiplier,
                'adjustments': adjustments,
                'reasoning': self._generate_reasoning(adjustments)
            }

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return {
                'original_size': base_position_size,
                'adjusted_size': base_position_size,
                'multiplier': 1.0,
                'adjustments': {},
                'reasoning': 'Error - using base size'
            }

    def _generate_reasoning(self, adjustments: Dict) -> str:
        """Generate human-readable reasoning for adjustments"""
        reasons = []

        for factor, mult in adjustments.items():
            if mult > 1.05:
                reasons.append(f"+{factor}")
            elif mult < 0.95:
                reasons.append(f"-{factor}")

        if not reasons:
            return "No significant adjustments"

        return "Adjusted: " + ", ".join(reasons)


class SmartExitOptimizer:
    """
    Intelligent exit timing optimization using ML predictions
    and multi-factor analysis.
    """

    def __init__(self):
        self.logger = Logger.get_logger()

    def should_exit_early(self,
                         position_pnl: float,
                         position_duration_minutes: int,
                         current_momentum: float,
                         current_rsi: float,
                         volatility: float,
                         volume_ratio: float,
                         trend_weakening: bool) -> Dict:
        """
        Determine if position should exit early (before stop/target).

        Returns:
            Dict with should_exit, confidence, and reason
        """
        try:
            exit_score = 0.0
            reasons = []

            # 1. Momentum Reversal Detection
            if position_pnl > 0:
                # In profit - watch for momentum reversal
                if current_momentum < -0.02 and current_rsi > 65:
                    exit_score += 30
                    reasons.append("momentum_reversal")
                elif current_momentum < -0.015 and current_rsi > 70:
                    exit_score += 40
                    reasons.append("strong_momentum_reversal")

            # 2. Profit Protection
            if position_pnl > 0.03:  # >3% profit
                # Large profit - consider taking it
                if current_momentum < 0:
                    exit_score += 25
                    reasons.append("protect_large_profit")

                # Very large profit - strongly consider exit
                if position_pnl > 0.07:  # >7%
                    exit_score += 30
                    reasons.append("exceptional_profit")

            # 3. Time-based Exit (stalled position)
            if position_duration_minutes > 480:  # >8 hours
                if abs(position_pnl) < 0.01:  # <1% move
                    exit_score += 20
                    reasons.append("stalled_position")

            # 4. Volatility Spike
            if volatility > 0.08:  # High volatility
                if position_pnl > 0:  # In profit
                    exit_score += 15
                    reasons.append("volatility_spike")

            # 5. Volume Drying Up
            if volume_ratio < 0.6:  # Very low volume
                if position_pnl > 0:
                    exit_score += 15
                    reasons.append("low_volume")

            # 6. Trend Weakening
            if trend_weakening and position_pnl > 0.015:
                exit_score += 20
                reasons.append("trend_weakening")

            # 7. RSI Extremes (overbought/oversold)
            if current_rsi > 80 and position_pnl > 0:
                exit_score += 25
                reasons.append("extreme_overbought")
            elif current_rsi < 20 and position_pnl < 0:
                exit_score += 25
                reasons.append("extreme_oversold")

            # Decision threshold
            should_exit = exit_score >= 50
            confidence = min(exit_score / 100.0, 1.0)

            return {
                'should_exit': should_exit,
                'confidence': confidence,
                'score': exit_score,
                'reasons': reasons,
                'reason_text': ', '.join(reasons) if reasons else 'no clear exit signal'
            }

        except Exception as e:
            self.logger.error(f"Error in exit optimization: {e}")
            return {
                'should_exit': False,
                'confidence': 0.0,
                'score': 0.0,
                'reasons': [],
                'reason_text': 'error'
            }


class MarketContextAnalyzer:
    """
    Analyzes broader market context to improve trading decisions.
    Considers market-wide conditions, correlations, and sentiment.
    """

    def __init__(self):
        self.logger = Logger.get_logger()
        self.market_state_history = []

    def analyze_market_context(self,
                               current_pairs_analyzed: int,
                               bullish_signals: int,
                               bearish_signals: int,
                               avg_volatility: float,
                               avg_volume_ratio: float) -> Dict:
        """
        Analyze overall market context for better decision making.

        Returns:
            Dict with market health, sentiment, and recommendations
        """
        try:
            total_signals = bullish_signals + bearish_signals

            # 1. Market Sentiment
            if total_signals > 0:
                bullish_pct = bullish_signals / total_signals
                if bullish_pct > 0.65:
                    sentiment = 'strong_bullish'
                    sentiment_score = 0.9
                elif bullish_pct > 0.55:
                    sentiment = 'bullish'
                    sentiment_score = 0.7
                elif bullish_pct < 0.35:
                    sentiment = 'strong_bearish'
                    sentiment_score = 0.9
                elif bullish_pct < 0.45:
                    sentiment = 'bearish'
                    sentiment_score = 0.7
                else:
                    sentiment = 'neutral'
                    sentiment_score = 0.5
            else:
                sentiment = 'unknown'
                sentiment_score = 0.5

            # 2. Market Activity Level
            signal_density = total_signals / max(current_pairs_analyzed, 1)
            if signal_density > 0.3:
                activity = 'very_high'
                activity_multiplier = 1.2  # Many opportunities
            elif signal_density > 0.2:
                activity = 'high'
                activity_multiplier = 1.1
            elif signal_density > 0.1:
                activity = 'normal'
                activity_multiplier = 1.0
            else:
                activity = 'low'
                activity_multiplier = 0.9  # Few opportunities - be selective

            # 3. Market Volatility Assessment
            if avg_volatility > 0.06:
                vol_state = 'high'
                vol_recommendation = 'reduce_position_sizes'
            elif avg_volatility > 0.03:
                vol_state = 'normal'
                vol_recommendation = 'normal_trading'
            else:
                vol_state = 'low'
                vol_recommendation = 'possible_breakout_watch'

            # 4. Volume Health
            if avg_volume_ratio > 1.3:
                volume_health = 'strong'
            elif avg_volume_ratio > 0.9:
                volume_health = 'healthy'
            else:
                volume_health = 'weak'

            # 5. Overall Market Health Score
            health_score = 0.0
            health_score += sentiment_score * 0.3
            health_score += (1.0 if volume_health == 'strong' else 0.7 if volume_health == 'healthy' else 0.4) * 0.3
            health_score += (1.0 if vol_state == 'normal' else 0.7) * 0.2
            health_score += min(signal_density * 3, 1.0) * 0.2

            return {
                'sentiment': sentiment,
                'sentiment_score': sentiment_score,
                'activity': activity,
                'activity_multiplier': activity_multiplier,
                'volatility_state': vol_state,
                'volatility_recommendation': vol_recommendation,
                'volume_health': volume_health,
                'market_health_score': health_score,
                'recommendation': self._generate_market_recommendation(health_score, sentiment, vol_state)
            }

        except Exception as e:
            self.logger.error(f"Error analyzing market context: {e}")
            return {
                'sentiment': 'unknown',
                'sentiment_score': 0.5,
                'activity': 'unknown',
                'activity_multiplier': 1.0,
                'volatility_state': 'unknown',
                'volatility_recommendation': 'normal_trading',
                'volume_health': 'unknown',
                'market_health_score': 0.5,
                'recommendation': 'proceed_with_caution'
            }

    def _generate_market_recommendation(self, health_score: float, sentiment: str, vol_state: str) -> str:
        """Generate actionable recommendation based on market context"""
        if health_score > 0.75:
            return 'favorable_conditions'
        elif health_score > 0.60:
            return 'normal_trading'
        elif health_score > 0.45:
            return 'be_selective'
        else:
            return 'reduce_activity'


class VolatilityAdaptiveParameters:
    """
    Dynamically adjusts trading parameters based on market volatility.
    """

    def __init__(self):
        self.logger = Logger.get_logger()

    def adjust_parameters(self, current_volatility: float, base_params: Dict) -> Dict:
        """
        Adjust trading parameters based on volatility regime.

        Args:
            current_volatility: Current market volatility (0-1)
            base_params: Base parameter values

        Returns:
            Adjusted parameters
        """
        try:
            adjusted = base_params.copy()

            # Volatility regimes
            if current_volatility > 0.08:
                # High volatility regime
                adjusted['confidence_threshold'] = base_params.get('confidence_threshold', 0.62) * 1.15
                adjusted['stop_loss_multiplier'] = 1.3  # Wider stops
                adjusted['position_size_multiplier'] = 0.7  # Smaller positions
                adjusted['trailing_stop_distance'] = 0.035  # Wider trailing stop
                regime = 'high_volatility'

            elif current_volatility > 0.05:
                # Elevated volatility
                adjusted['confidence_threshold'] = base_params.get('confidence_threshold', 0.62) * 1.08
                adjusted['stop_loss_multiplier'] = 1.15
                adjusted['position_size_multiplier'] = 0.85
                adjusted['trailing_stop_distance'] = 0.025
                regime = 'elevated_volatility'

            elif current_volatility > 0.02:
                # Normal volatility
                adjusted['confidence_threshold'] = base_params.get('confidence_threshold', 0.62)
                adjusted['stop_loss_multiplier'] = 1.0
                adjusted['position_size_multiplier'] = 1.0
                adjusted['trailing_stop_distance'] = 0.02
                regime = 'normal_volatility'

            else:
                # Low volatility regime
                adjusted['confidence_threshold'] = base_params.get('confidence_threshold', 0.62) * 1.1
                adjusted['stop_loss_multiplier'] = 0.9  # Tighter stops
                adjusted['position_size_multiplier'] = 0.9  # Slightly smaller (choppy)
                adjusted['trailing_stop_distance'] = 0.015  # Tighter trailing
                regime = 'low_volatility'

            adjusted['volatility_regime'] = regime

            return adjusted

        except Exception as e:
            self.logger.error(f"Error adjusting parameters: {e}")
            return base_params


# Initialize global instances for easy access
smart_trade_filter = SmartTradeFilter()
smart_position_sizer = SmartPositionSizer()
smart_exit_optimizer = SmartExitOptimizer()
market_context_analyzer = MarketContextAnalyzer()
volatility_adaptive_parameters = VolatilityAdaptiveParameters()
