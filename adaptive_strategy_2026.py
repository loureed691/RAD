"""
Adaptive Strategy Selector for 2026
Dynamically selects and applies the best trading strategy based on market conditions
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from logger import Logger


class AdaptiveStrategySelector2026:
    """
    Intelligent strategy selection engine:
    - Multiple trading strategies (trend following, mean reversion, breakout, etc.)
    - Real-time strategy performance tracking
    - Automatic strategy switching based on market regime
    - Strategy ensemble for robustness
    - A/B testing of new strategies
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        
        # Available strategies with their characteristics
        self.strategies = {
            'trend_following': {
                'name': 'Trend Following',
                'best_regimes': ['bull', 'bear'],
                'performance': {'win_rate': 0.0, 'trades': 0, 'profit': 0.0},
                'active': True,
                'weight': 0.3
            },
            'mean_reversion': {
                'name': 'Mean Reversion',
                'best_regimes': ['neutral', 'low_vol'],
                'performance': {'win_rate': 0.0, 'trades': 0, 'profit': 0.0},
                'active': True,
                'weight': 0.25
            },
            'breakout': {
                'name': 'Breakout Trading',
                'best_regimes': ['low_vol', 'neutral'],
                'performance': {'win_rate': 0.0, 'trades': 0, 'profit': 0.0},
                'active': True,
                'weight': 0.25
            },
            'momentum': {
                'name': 'Momentum Trading',
                'best_regimes': ['bull', 'bear'],
                'performance': {'win_rate': 0.0, 'trades': 0, 'profit': 0.0},
                'active': True,
                'weight': 0.2
            }
        }
        
        self.current_strategy = 'trend_following'
        self.strategy_history = []
        
        # Strategy switch tracking
        self.last_switch_time = datetime.now()
        self.min_switch_interval = timedelta(hours=6)  # Don't switch too frequently
        
        self.logger.info("🎯 Adaptive Strategy Selector 2026 initialized")
    
    def select_strategy(self, market_regime: str,
                       volatility: float,
                       trend_strength: float,
                       confidence_scores: Dict[str, float]) -> str:
        """
        Select optimal strategy based on market conditions
        
        Args:
            market_regime: Current market regime
            volatility: Market volatility measure
            trend_strength: Strength of current trend
            confidence_scores: Confidence scores for each strategy
            
        Returns:
            Selected strategy name
        """
        try:
            # Calculate strategy scores
            strategy_scores = {}
            
            for strategy_name, strategy_info in self.strategies.items():
                if not strategy_info['active']:
                    continue
                
                score = 0.0
                
                # Base score from strategy weight
                score += strategy_info['weight'] * 100
                
                # Bonus if regime matches strategy's best regimes
                if market_regime in strategy_info['best_regimes']:
                    score += 30
                
                # Performance bonus (recent win rate)
                perf = strategy_info['performance']
                if perf['trades'] > 10:  # Only consider if enough history
                    score += perf['win_rate'] * 40
                
                # Confidence bonus
                if strategy_name in confidence_scores:
                    score += confidence_scores[strategy_name] * 30
                
                # Strategy-specific adjustments
                if strategy_name == 'trend_following':
                    # Better in strong trends
                    score += abs(trend_strength) * 50
                elif strategy_name == 'mean_reversion':
                    # Better in range-bound markets (weak trends)
                    score += (1 - abs(trend_strength)) * 40
                elif strategy_name == 'breakout':
                    # Better in low volatility (pending breakout)
                    if volatility < 0.3:
                        score += 30
                elif strategy_name == 'momentum':
                    # Better with strong trends and moderate volatility
                    if abs(trend_strength) > 0.3 and 0.3 < volatility < 0.6:
                        score += 35
                
                strategy_scores[strategy_name] = score
            
            # Select strategy with highest score
            best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
            selected_strategy = best_strategy[0]
            
            # Check if we should switch
            time_since_switch = datetime.now() - self.last_switch_time
            
            if selected_strategy != self.current_strategy:
                if time_since_switch > self.min_switch_interval:
                    # Switch allowed
                    self.logger.info(
                        f"📊 Strategy switch: {self.current_strategy} → {selected_strategy} "
                        f"(score: {best_strategy[1]:.1f}, regime: {market_regime})"
                    )
                    self.current_strategy = selected_strategy
                    self.last_switch_time = datetime.now()
                    
                    self.strategy_history.append({
                        'timestamp': datetime.now(),
                        'strategy': selected_strategy,
                        'regime': market_regime,
                        'score': best_strategy[1]
                    })
                else:
                    # Too soon to switch
                    self.logger.debug(
                        f"Strategy switch deferred (last switch: "
                        f"{time_since_switch.total_seconds()/3600:.1f}h ago)"
                    )
            
            return self.current_strategy
            
        except Exception as e:
            self.logger.error(f"Error selecting strategy: {e}")
            return 'trend_following'  # Safe default
    
    def apply_trend_following_filters(self, indicators: Dict,
                                     signal: str,
                                     confidence: float) -> Tuple[str, float]:
        """
        Apply trend following strategy filters
        
        Args:
            indicators: Technical indicators
            signal: Raw signal ('BUY', 'SELL', 'HOLD')
            confidence: Raw confidence score
            
        Returns:
            Tuple of (filtered_signal, adjusted_confidence)
        """
        # Trend following only trades WITH the trend
        trend_direction = indicators.get('trend_direction', 'neutral')
        
        if signal == 'BUY' and trend_direction == 'down':
            return 'HOLD', 0.0  # Don't buy in downtrend
        elif signal == 'SELL' and trend_direction == 'up':
            return 'HOLD', 0.0  # Don't sell in uptrend
        
        # Boost confidence if signal aligns with strong trend
        trend_strength = indicators.get('trend_strength', 0.0)
        if abs(trend_strength) > 0.5:
            confidence *= 1.2  # 20% boost
        
        return signal, min(confidence, 1.0)
    
    def apply_mean_reversion_filters(self, indicators: Dict,
                                    signal: str,
                                    confidence: float) -> Tuple[str, float]:
        """
        Apply mean reversion strategy filters
        
        Args:
            indicators: Technical indicators
            signal: Raw signal
            confidence: Raw confidence score
            
        Returns:
            Tuple of (filtered_signal, adjusted_confidence)
        """
        rsi = indicators.get('rsi', 50)
        bb_position = indicators.get('bb_position', 0.5)
        
        # Mean reversion trades oversold/overbought conditions
        if signal == 'BUY':
            # Only buy if oversold
            if rsi > 35 or bb_position > 0.3:
                return 'HOLD', 0.0
            # Boost confidence for extreme oversold
            if rsi < 25:
                confidence *= 1.3
        elif signal == 'SELL':
            # Only sell if overbought
            if rsi < 65 or bb_position < 0.7:
                return 'HOLD', 0.0
            # Boost confidence for extreme overbought
            if rsi > 75:
                confidence *= 1.3
        
        return signal, min(confidence, 1.0)
    
    def apply_breakout_filters(self, indicators: Dict,
                              signal: str,
                              confidence: float) -> Tuple[str, float]:
        """
        Apply breakout trading strategy filters
        
        Args:
            indicators: Technical indicators
            signal: Raw signal
            confidence: Raw confidence score
            
        Returns:
            Tuple of (filtered_signal, adjusted_confidence)
        """
        bb_width = indicators.get('bb_width', 0.0)
        volume_ratio = indicators.get('volume_ratio', 1.0)
        
        # Breakouts need:
        # 1. Tight consolidation (narrow BB)
        # 2. Volume surge on breakout
        
        if bb_width > 0.03:  # Too wide, not a breakout setup
            return 'HOLD', 0.0
        
        if volume_ratio < 1.5:  # Need volume confirmation
            confidence *= 0.7  # Reduce confidence
        else:
            confidence *= 1.2  # Boost confidence for volume
        
        return signal, min(confidence, 1.0)
    
    def apply_momentum_filters(self, indicators: Dict,
                              signal: str,
                              confidence: float) -> Tuple[str, float]:
        """
        Apply momentum trading strategy filters
        
        Args:
            indicators: Technical indicators
            signal: Raw signal
            confidence: Raw confidence score
            
        Returns:
            Tuple of (filtered_signal, adjusted_confidence)
        """
        momentum = indicators.get('momentum', 0.0)
        roc = indicators.get('roc', 0.0)
        
        # Momentum trading needs accelerating price movement
        if signal == 'BUY':
            if momentum < 0 or roc < 0:
                return 'HOLD', 0.0
            # Strong momentum = higher confidence
            if momentum > 0.02:
                confidence *= 1.25
        elif signal == 'SELL':
            if momentum > 0 or roc > 0:
                return 'HOLD', 0.0
            # Strong negative momentum = higher confidence
            if momentum < -0.02:
                confidence *= 1.25
        
        return signal, min(confidence, 1.0)
    
    def apply_strategy_filters(self, strategy: str,
                              indicators: Dict,
                              signal: str,
                              confidence: float) -> Tuple[str, float]:
        """
        Apply filters based on selected strategy
        
        Args:
            strategy: Strategy name
            indicators: Technical indicators
            signal: Raw signal
            confidence: Raw confidence score
            
        Returns:
            Tuple of (filtered_signal, adjusted_confidence)
        """
        if strategy == 'trend_following':
            return self.apply_trend_following_filters(indicators, signal, confidence)
        elif strategy == 'mean_reversion':
            return self.apply_mean_reversion_filters(indicators, signal, confidence)
        elif strategy == 'breakout':
            return self.apply_breakout_filters(indicators, signal, confidence)
        elif strategy == 'momentum':
            return self.apply_momentum_filters(indicators, signal, confidence)
        else:
            return signal, confidence
    
    def record_strategy_outcome(self, strategy: str, pnl: float):
        """
        Record outcome for strategy performance tracking
        
        Args:
            strategy: Strategy that was used
            pnl: Trade P&L (profit/loss as decimal)
        """
        if strategy not in self.strategies:
            return
        
        perf = self.strategies[strategy]['performance']
        perf['trades'] += 1
        perf['profit'] += pnl
        
        # Update win rate
        if pnl > 0:
            wins = perf.get('wins', 0) + 1
            perf['wins'] = wins
        
        if perf['trades'] > 0:
            perf['win_rate'] = perf.get('wins', 0) / perf['trades']
        
        self.logger.debug(
            f"Strategy {strategy} outcome recorded: "
            f"trades={perf['trades']}, win_rate={perf['win_rate']:.2%}"
        )
    
    def get_strategy_ensemble_signal(self, indicators: Dict,
                                    base_signal: str,
                                    base_confidence: float) -> Tuple[str, float]:
        """
        Get ensemble signal from multiple strategies
        
        Args:
            indicators: Technical indicators
            base_signal: Base signal from primary analysis
            base_confidence: Base confidence score
            
        Returns:
            Tuple of (ensemble_signal, ensemble_confidence)
        """
        strategy_votes = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        confidence_sum = 0.0
        vote_count = 0
        
        # Get vote from each active strategy
        for strategy_name, strategy_info in self.strategies.items():
            if not strategy_info['active']:
                continue
            
            signal, conf = self.apply_strategy_filters(
                strategy_name, indicators, base_signal, base_confidence
            )
            
            # Weight vote by strategy weight
            weight = strategy_info['weight']
            strategy_votes[signal] += weight
            confidence_sum += conf * weight
            vote_count += weight
        
        # Determine ensemble signal
        ensemble_signal = max(strategy_votes.items(), key=lambda x: x[1])[0]
        
        # Calculate ensemble confidence
        ensemble_confidence = confidence_sum / vote_count if vote_count > 0 else 0.0
        
        # Require majority agreement (>50% of weight)
        winning_weight = strategy_votes[ensemble_signal]
        if winning_weight < 0.5:
            return 'HOLD', 0.0
        
        return ensemble_signal, ensemble_confidence
    
    def get_strategy_statistics(self) -> Dict:
        """
        Get statistics about strategy performance
        
        Returns:
            Dictionary with strategy statistics
        """
        stats = {
            'current_strategy': self.current_strategy,
            'last_switch': self.last_switch_time.isoformat(),
            'strategies': {}
        }
        
        for name, info in self.strategies.items():
            perf = info['performance']
            stats['strategies'][name] = {
                'name': info['name'],
                'active': info['active'],
                'weight': info['weight'],
                'trades': perf['trades'],
                'win_rate': perf['win_rate'],
                'total_profit': perf['profit']
            }
        
        return stats
