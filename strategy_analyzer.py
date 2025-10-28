"""
Strategy Analyzer - Comprehensive analysis and optimization of buy/sell strategies

This module provides detailed analysis of trading strategies including:
- Signal quality analysis
- Entry/exit timing optimization
- Risk/reward ratio analysis
- Strategy performance comparison
- Parameter sensitivity analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from logger import Logger
from indicators import Indicators
from signals import SignalGenerator


class StrategyAnalyzer:
    """
    Analyzes and optimizes trading strategies for better performance
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.signal_generator = SignalGenerator()
        
        # Analysis metrics
        self.signal_quality_scores = []
        self.entry_timing_scores = []
        self.exit_timing_scores = []
        
        self.logger.info("📊 Strategy Analyzer initialized")
    
    def analyze_signal_quality(self, df: pd.DataFrame, signal: str, 
                               confidence: float, reasons: Dict) -> Dict:
        """
        Analyze the quality of a trading signal
        
        Returns comprehensive quality metrics:
        - Signal strength score
        - Risk/reward potential
        - Market condition alignment
        - Timing quality
        """
        if df.empty or len(df) < 50:
            return {'score': 0.0, 'quality': 'insufficient_data'}
        
        try:
            indicators = Indicators.get_latest_indicators(df)
            if not indicators:
                return {'score': 0.0, 'quality': 'no_indicators'}
            
            quality_score = 0.0
            quality_factors = {}
            
            # 1. Trend Alignment Score (0-25 points)
            ema_12 = indicators.get('ema_12', 0)
            ema_26 = indicators.get('ema_26', 0)
            sma_20 = indicators.get('sma_20', 0)
            sma_50 = indicators.get('sma_50', 0)
            
            trend_alignment = 0
            if signal == 'BUY':
                if ema_12 > ema_26:
                    trend_alignment += 10
                if sma_20 > sma_50:
                    trend_alignment += 10
                if indicators.get('momentum', 0) > 0:
                    trend_alignment += 5
            elif signal == 'SELL':
                if ema_12 < ema_26:
                    trend_alignment += 10
                if sma_20 < sma_50:
                    trend_alignment += 10
                if indicators.get('momentum', 0) < 0:
                    trend_alignment += 5
            
            quality_score += trend_alignment
            quality_factors['trend_alignment'] = trend_alignment
            
            # 2. Momentum Strength Score (0-20 points)
            momentum = abs(indicators.get('momentum', 0))
            roc = abs(indicators.get('roc', 0))
            
            momentum_score = 0
            if momentum > 0.03:  # Strong momentum
                momentum_score += 12
            elif momentum > 0.015:  # Moderate momentum
                momentum_score += 8
            elif momentum > 0.005:  # Weak momentum
                momentum_score += 4
            
            if roc > 3.0:  # Strong ROC
                momentum_score += 8
            elif roc > 1.5:  # Moderate ROC
                momentum_score += 4
            
            quality_score += momentum_score
            quality_factors['momentum_strength'] = momentum_score
            
            # 3. Volume Confirmation Score (0-15 points)
            volume_ratio = indicators.get('volume_ratio', 1.0)
            volume_score = 0
            
            if volume_ratio > 2.0:  # Very high volume
                volume_score = 15
            elif volume_ratio > 1.5:  # High volume
                volume_score = 12
            elif volume_ratio > 1.2:  # Above average
                volume_score = 8
            elif volume_ratio > 0.8:  # Average
                volume_score = 5
            else:  # Low volume - penalty
                volume_score = 0
            
            quality_score += volume_score
            quality_factors['volume_confirmation'] = volume_score
            
            # 4. Volatility Appropriateness (0-15 points)
            bb_width = indicators.get('bb_width', 0)
            atr = indicators.get('atr', 0)
            
            volatility_score = 0
            # Optimal volatility range: 2-5%
            if 0.02 <= bb_width <= 0.05:
                volatility_score = 15
            elif 0.015 <= bb_width <= 0.06:
                volatility_score = 10
            elif 0.01 <= bb_width <= 0.08:
                volatility_score = 5
            else:
                volatility_score = 0  # Too low or too high
            
            quality_score += volatility_score
            quality_factors['volatility_appropriateness'] = volatility_score
            
            # 5. Oscillator Confirmation (0-15 points)
            rsi = indicators.get('rsi', 50)
            stoch_k = indicators.get('stoch_k', 50)
            
            oscillator_score = 0
            if signal == 'BUY':
                if rsi < 30:  # Oversold
                    oscillator_score += 10
                elif rsi < 40:
                    oscillator_score += 5
                if stoch_k < 20:  # Oversold
                    oscillator_score += 5
            elif signal == 'SELL':
                if rsi > 70:  # Overbought
                    oscillator_score += 10
                elif rsi > 60:
                    oscillator_score += 5
                if stoch_k > 80:  # Overbought
                    oscillator_score += 5
            
            quality_score += oscillator_score
            quality_factors['oscillator_confirmation'] = oscillator_score
            
            # 6. Risk/Reward Potential (0-10 points)
            # Calculate based on support/resistance distance
            close = indicators.get('close', 0)
            atr_value = indicators.get('atr', close * 0.02)
            
            # Estimate potential risk/reward
            if signal == 'BUY':
                estimated_stop = close - (1.5 * atr_value)
                estimated_target = close + (3 * atr_value)
            else:
                estimated_stop = close + (1.5 * atr_value)
                estimated_target = close - (3 * atr_value)
            
            risk = abs(close - estimated_stop)
            reward = abs(estimated_target - close)
            
            if risk > 0:
                rr_ratio = reward / risk
                if rr_ratio >= 2.5:
                    rr_score = 10
                elif rr_ratio >= 2.0:
                    rr_score = 8
                elif rr_ratio >= 1.5:
                    rr_score = 5
                else:
                    rr_score = 0
            else:
                rr_score = 0
            
            quality_score += rr_score
            quality_factors['risk_reward_ratio'] = rr_score
            
            # Calculate overall quality rating
            max_score = 100
            quality_percentage = (quality_score / max_score) * 100
            
            if quality_percentage >= 80:
                quality_rating = 'excellent'
            elif quality_percentage >= 65:
                quality_rating = 'good'
            elif quality_percentage >= 50:
                quality_rating = 'fair'
            else:
                quality_rating = 'poor'
            
            return {
                'score': quality_score,
                'max_score': max_score,
                'percentage': quality_percentage,
                'quality': quality_rating,
                'factors': quality_factors,
                'confidence': confidence,
                'signal': signal
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing signal quality: {e}")
            return {'score': 0.0, 'quality': 'error', 'error': str(e)}
    
    def analyze_entry_timing(self, df: pd.DataFrame, signal: str) -> Dict:
        """
        Analyze optimal entry timing for a signal
        
        Returns:
        - Timing score (0-100)
        - Optimal entry recommendation
        - Wait time suggestion
        """
        if df.empty or len(df) < 20:
            return {'timing_score': 0, 'recommendation': 'insufficient_data'}
        
        try:
            indicators = Indicators.get_latest_indicators(df)
            if not indicators:
                return {'timing_score': 0, 'recommendation': 'no_indicators'}
            
            timing_score = 50  # Neutral starting point
            recommendation = 'enter_now'
            
            rsi = indicators.get('rsi', 50)
            close = indicators.get('close', 0)
            bb_low = indicators.get('bb_low', 0)
            bb_high = indicators.get('bb_high', 0)
            bb_mid = indicators.get('bb_mid', 0)
            
            if signal == 'BUY':
                # Better timing at support levels
                if close <= bb_low * 1.01:  # Near lower band
                    timing_score += 25
                    recommendation = 'excellent_entry'
                elif close <= bb_mid:  # Below midpoint
                    timing_score += 10
                    recommendation = 'good_entry'
                
                # RSI timing
                if rsi < 25:  # Extreme oversold
                    timing_score += 20
                elif rsi < 30:  # Oversold
                    timing_score += 15
                elif rsi > 50:  # Not oversold
                    timing_score -= 15
                    recommendation = 'wait_for_pullback'
                
            elif signal == 'SELL':
                # Better timing at resistance levels
                if close >= bb_high * 0.99:  # Near upper band
                    timing_score += 25
                    recommendation = 'excellent_entry'
                elif close >= bb_mid:  # Above midpoint
                    timing_score += 10
                    recommendation = 'good_entry'
                
                # RSI timing
                if rsi > 75:  # Extreme overbought
                    timing_score += 20
                elif rsi > 70:  # Overbought
                    timing_score += 15
                elif rsi < 50:  # Not overbought
                    timing_score -= 15
                    recommendation = 'wait_for_rally'
            
            # Cap timing score
            timing_score = max(0, min(100, timing_score))
            
            return {
                'timing_score': timing_score,
                'recommendation': recommendation,
                'rsi': rsi,
                'price_vs_bb': 'near_support' if close < bb_mid else 'near_resistance'
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing entry timing: {e}")
            return {'timing_score': 0, 'recommendation': 'error', 'error': str(e)}
    
    def optimize_signal_threshold(self, historical_signals: List[Dict],
                                  target_win_rate: float = 0.70) -> float:
        """
        Optimize signal confidence threshold based on historical performance
        
        Args:
            historical_signals: List of past signals with outcomes
            target_win_rate: Desired win rate (default 70%)
            
        Returns:
            Optimal confidence threshold
        """
        if not historical_signals or len(historical_signals) < 20:
            return 0.62  # Default threshold
        
        # Analyze performance at different confidence levels
        thresholds = np.arange(0.50, 0.85, 0.02)
        best_threshold = 0.62
        best_score = 0
        
        for threshold in thresholds:
            filtered_signals = [s for s in historical_signals 
                              if s.get('confidence', 0) >= threshold]
            
            if len(filtered_signals) < 10:
                continue
            
            wins = sum(1 for s in filtered_signals if s.get('outcome', 0) > 0)
            total = len(filtered_signals)
            win_rate = wins / total if total > 0 else 0
            
            # Score: balance win rate and trade frequency
            # Higher win rate is good, but we also want enough trades
            trade_frequency_penalty = max(0, 1 - (total / len(historical_signals)))
            score = win_rate * (1 - trade_frequency_penalty * 0.3)
            
            if score > best_score and win_rate >= target_win_rate * 0.9:
                best_score = score
                best_threshold = threshold
        
        self.logger.info(
            f"📊 Optimized confidence threshold: {best_threshold:.2f} "
            f"(score: {best_score:.2f})"
        )
        
        return best_threshold
    
    def generate_strategy_report(self, symbol: str, df: pd.DataFrame,
                                df_4h: pd.DataFrame = None,
                                df_1d: pd.DataFrame = None) -> Dict:
        """
        Generate comprehensive strategy analysis report
        
        Returns:
            Complete analysis with recommendations
        """
        self.logger.info(f"📊 Generating strategy report for {symbol}")
        
        # Generate signal
        signal, confidence, reasons = self.signal_generator.generate_signal(
            df, df_4h, df_1d
        )
        
        report = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'confidence': confidence,
            'reasons': reasons
        }
        
        if signal != 'HOLD':
            # Analyze signal quality
            quality_analysis = self.analyze_signal_quality(
                df, signal, confidence, reasons
            )
            report['quality_analysis'] = quality_analysis
            
            # Analyze entry timing
            timing_analysis = self.analyze_entry_timing(df, signal)
            report['timing_analysis'] = timing_analysis
            
            # Overall recommendation
            if quality_analysis['percentage'] >= 70 and timing_analysis['timing_score'] >= 70:
                report['recommendation'] = 'strong_trade'
            elif quality_analysis['percentage'] >= 60 and timing_analysis['timing_score'] >= 60:
                report['recommendation'] = 'moderate_trade'
            elif quality_analysis['percentage'] >= 50:
                report['recommendation'] = 'weak_trade'
            else:
                report['recommendation'] = 'avoid'
        else:
            report['recommendation'] = 'hold'
        
        return report
    
    def compare_strategies(self, df: pd.DataFrame, strategies: List[str]) -> Dict:
        """
        Compare performance of different strategy configurations
        
        Args:
            df: Historical price data
            strategies: List of strategy names to compare
            
        Returns:
            Performance comparison metrics
        """
        results = {}
        
        for strategy in strategies:
            # This would run backtests with different strategy configs
            # For now, placeholder
            results[strategy] = {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0
            }
        
        return results
