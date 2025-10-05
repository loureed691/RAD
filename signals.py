"""
Trading signal generation based on technical indicators
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from indicators import Indicators
from logger import Logger
from pattern_recognition import PatternRecognition

class SignalGenerator:
    """Generate trading signals based on multiple indicators"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.market_regime = 'neutral'  # 'trending', 'ranging', 'neutral'
        self.adaptive_threshold = 0.55
        self.pattern_recognizer = PatternRecognition()
    
    def detect_market_regime(self, df: pd.DataFrame) -> str:
        """
        Detect market regime to adapt strategy
        
        Returns:
            'trending', 'ranging', or 'neutral'
        """
        if df.empty or len(df) < 20:
            return 'neutral'
        
        indicators = Indicators.get_latest_indicators(df)
        
        # Use ADX-like logic with ATR and momentum
        volatility = indicators.get('bb_width', 0)
        momentum = abs(indicators.get('momentum', 0))
        roc = abs(indicators.get('roc', 0))
        
        # Strong trend indicators
        if momentum > 0.03 or roc > 3.0:
            return 'trending'
        # Low volatility and momentum = ranging
        elif volatility < 0.02 and momentum < 0.01:
            return 'ranging'
        
        return 'neutral'
    
    def analyze_multi_timeframe(self, df_1h: pd.DataFrame, df_4h: pd.DataFrame = None, 
                               df_1d: pd.DataFrame = None) -> Dict:
        """
        Analyze multiple timeframes for trend alignment
        
        Returns:
            Dict with multi-timeframe analysis results
        """
        mtf_analysis = {
            'trend_alignment': 'neutral',
            'strength': 0.0,
            'confidence_multiplier': 1.0
        }
        
        if df_4h is None or len(df_4h) < 20:
            return mtf_analysis
        
        # Get indicators for higher timeframe
        indicators_4h = Indicators.get_latest_indicators(df_4h)
        if not indicators_4h:
            return mtf_analysis
        
        # Check trend alignment
        bullish_alignment = 0
        bearish_alignment = 0
        
        # Check EMA trend on 4h
        if indicators_4h['ema_12'] > indicators_4h['ema_26']:
            bullish_alignment += 1
        else:
            bearish_alignment += 1
        
        # Check MACD on 4h
        if indicators_4h['macd'] > indicators_4h['macd_signal']:
            bullish_alignment += 1
        else:
            bearish_alignment += 1
        
        # Check RSI trend on 4h
        rsi_4h = indicators_4h['rsi']
        if rsi_4h > 50:
            bullish_alignment += 0.5
        elif rsi_4h < 50:
            bearish_alignment += 0.5
        
        # Daily timeframe if available
        if df_1d is not None and len(df_1d) >= 20:
            indicators_1d = Indicators.get_latest_indicators(df_1d)
            if indicators_1d:
                if indicators_1d['ema_12'] > indicators_1d['ema_26']:
                    bullish_alignment += 1.5  # Daily trend is stronger
                else:
                    bearish_alignment += 1.5
        
        # Determine trend alignment
        total = bullish_alignment + bearish_alignment
        if total > 0:
            strength = max(bullish_alignment, bearish_alignment) / total
            
            if bullish_alignment > bearish_alignment * 1.5:
                mtf_analysis['trend_alignment'] = 'bullish'
                mtf_analysis['strength'] = strength
                mtf_analysis['confidence_multiplier'] = 1.0 + (strength * 0.2)  # Up to 20% boost
            elif bearish_alignment > bullish_alignment * 1.5:
                mtf_analysis['trend_alignment'] = 'bearish'
                mtf_analysis['strength'] = strength
                mtf_analysis['confidence_multiplier'] = 1.0 + (strength * 0.2)
        
        return mtf_analysis

    def generate_signal(self, df: pd.DataFrame, df_4h: pd.DataFrame = None, 
                       df_1d: pd.DataFrame = None) -> Tuple[str, float, Dict]:
        """
        Generate trading signal based on technical indicators with adaptive weighting
        and multi-timeframe analysis
        
        Returns:
            Tuple of (signal, confidence, reasons)
            signal: 'BUY', 'SELL', or 'HOLD'
            confidence: float between 0 and 1
            reasons: dict with reasons for the signal
        """
        if df.empty or len(df) < 50:
            return 'HOLD', 0.0, {'reason': 'Insufficient data'}
        
        indicators = Indicators.get_latest_indicators(df)
        if not indicators:
            return 'HOLD', 0.0, {'reason': 'No indicators available'}
        
        # Multi-timeframe analysis
        mtf_analysis = self.analyze_multi_timeframe(df, df_4h, df_1d)
        
        # Detect market regime for adaptive strategy
        self.market_regime = self.detect_market_regime(df)
        
        buy_signals = 0.0
        sell_signals = 0.0
        reasons = {}
        reasons['market_regime'] = self.market_regime
        reasons['mtf_alignment'] = mtf_analysis['trend_alignment']
        
        # Adaptive weights based on market regime
        trend_weight = 2.5 if self.market_regime == 'trending' else 1.5
        oscillator_weight = 2.0 if self.market_regime == 'ranging' else 1.0
        
        # 1. Trend Following - Moving Average Crossover (weighted by regime)
        if indicators['ema_12'] > indicators['ema_26']:
            buy_signals += trend_weight
            reasons['ma_trend'] = 'bullish'
        elif indicators['ema_12'] < indicators['ema_26']:
            sell_signals += trend_weight
            reasons['ma_trend'] = 'bearish'
        
        # 2. MACD (weighted by regime)
        if indicators['macd'] > indicators['macd_signal'] and indicators['macd_diff'] > 0:
            buy_signals += trend_weight
            reasons['macd'] = 'bullish'
        elif indicators['macd'] < indicators['macd_signal'] and indicators['macd_diff'] < 0:
            sell_signals += trend_weight
            reasons['macd'] = 'bearish'
        
        # 3. RSI (weighted for ranging markets)
        rsi = indicators['rsi']
        if rsi < 30:
            buy_signals += (oscillator_weight * 1.5)
            reasons['rsi'] = f'oversold ({rsi:.1f})'
        elif rsi > 70:
            sell_signals += (oscillator_weight * 1.5)
            reasons['rsi'] = f'overbought ({rsi:.1f})'
        elif 40 < rsi < 60:
            reasons['rsi'] = f'neutral ({rsi:.1f})'
        elif rsi < 40:
            buy_signals += oscillator_weight * 0.5
            reasons['rsi'] = f'weak ({rsi:.1f})'
        elif rsi > 60:
            sell_signals += oscillator_weight * 0.5
            reasons['rsi'] = f'strong ({rsi:.1f})'
        
        # 4. Stochastic Oscillator (weighted for ranging)
        # FIX BUG 6: Check for NaN values before using stochastic indicators
        stoch_k = indicators.get('stoch_k', 50.0)
        stoch_d = indicators.get('stoch_d', 50.0)
        if not pd.isna(stoch_k) and not pd.isna(stoch_d):
            if stoch_k < 20 and stoch_k > stoch_d:
                buy_signals += oscillator_weight
                reasons['stochastic'] = 'bullish crossover'
            elif stoch_k > 80 and stoch_k < stoch_d:
                sell_signals += oscillator_weight
                reasons['stochastic'] = 'bearish crossover'
        
        # 5. Bollinger Bands
        close = indicators['close']
        if close < indicators['bb_low']:
            buy_signals += 1.5
            reasons['bollinger'] = 'below lower band'
        elif close > indicators['bb_high']:
            sell_signals += 1.5
            reasons['bollinger'] = 'above upper band'
        
        # 6. Volume (confirmation signal - amplifies existing signals)
        if indicators['volume_ratio'] > 1.5:
            reasons['volume'] = 'high volume confirmation'
            # Amplify existing signals with high volume
            if buy_signals > sell_signals:
                buy_signals += 1.0
            elif sell_signals > buy_signals:
                sell_signals += 1.0
        
        # 7. Momentum (weighted by regime)
        momentum_threshold = 0.015 if self.market_regime == 'ranging' else 0.02
        if indicators['momentum'] > momentum_threshold:
            buy_signals += trend_weight
            reasons['momentum'] = 'strong positive'
        elif indicators['momentum'] < -momentum_threshold:
            sell_signals += trend_weight
            reasons['momentum'] = 'strong negative'
        
        # 8. Advanced Pattern Recognition (NEW)
        pattern_signal, pattern_confidence, pattern_name = self.pattern_recognizer.get_pattern_signal(df)
        if pattern_signal != 'HOLD':
            pattern_weight = pattern_confidence * 3.0  # Patterns are strong signals
            if pattern_signal == 'BUY':
                buy_signals += pattern_weight
                reasons['pattern'] = f'{pattern_name} (bullish)'
                self.logger.info(f"🔍 Bullish pattern detected: {pattern_name} (confidence: {pattern_confidence:.2f})")
            elif pattern_signal == 'SELL':
                sell_signals += pattern_weight
                reasons['pattern'] = f'{pattern_name} (bearish)'
                self.logger.info(f"🔍 Bearish pattern detected: {pattern_name} (confidence: {pattern_confidence:.2f})")
        
        total_signals = buy_signals + sell_signals
        
        # Calculate confidence
        if total_signals == 0:
            signal = 'HOLD'
            confidence = 0.0
            reasons['no_signals'] = 'no clear signal detected'
        elif buy_signals > sell_signals:
            signal = 'BUY'
            confidence = buy_signals / total_signals
        elif sell_signals > buy_signals:
            signal = 'SELL'
            confidence = sell_signals / total_signals
        else:
            # FIX BUG 1: Equal signals should result in HOLD with 0 confidence
            # to properly fail threshold checks, not 0.5 which may pass
            signal = 'HOLD'
            confidence = 0.0
            reasons['equal_signals'] = 'buy and sell signals balanced'
        
        # Adaptive threshold based on market regime
        if self.market_regime == 'trending':
            min_confidence = 0.52  # Lower threshold in trending markets
        elif self.market_regime == 'ranging':
            min_confidence = 0.58  # Higher threshold in ranging markets
        else:
            min_confidence = self.adaptive_threshold
        
        # Require minimum confidence threshold
        if confidence < min_confidence:
            signal = 'HOLD'
            reasons['confidence'] = f'too low ({confidence:.2f} < {min_confidence:.2f})'
        
        # Apply multi-timeframe confidence boost
        if signal != 'HOLD' and mtf_analysis['trend_alignment'] != 'neutral':
            # Boost confidence if MTF aligns with signal
            if (signal == 'BUY' and mtf_analysis['trend_alignment'] == 'bullish') or \
               (signal == 'SELL' and mtf_analysis['trend_alignment'] == 'bearish'):
                confidence *= mtf_analysis['confidence_multiplier']
                confidence = min(confidence, 0.99)  # Cap at 99%
                reasons['mtf_boost'] = f"+{(mtf_analysis['confidence_multiplier']-1)*100:.0f}%"
            # FIX BUG 3: Adjust min_confidence proportionally when reducing confidence for MTF conflict
            elif (signal == 'BUY' and mtf_analysis['trend_alignment'] == 'bearish') or \
                 (signal == 'SELL' and mtf_analysis['trend_alignment'] == 'bullish'):
                confidence *= 0.7  # Penalize conflicting signals
                adjusted_min_confidence = min_confidence * 0.7  # Also reduce threshold proportionally
                reasons['mtf_conflict'] = 'warning'
                if confidence < adjusted_min_confidence:
                    signal = 'HOLD'
                    reasons['confidence'] = f'too low after MTF adjustment ({confidence:.2f} < {adjusted_min_confidence:.2f})'
        
        self.logger.debug(f"Signal: {signal}, Confidence: {confidence:.2f}, Regime: {self.market_regime}, Buy: {buy_signals:.1f}/{total_signals:.1f}, Sell: {sell_signals:.1f}/{total_signals:.1f}")
        
        return signal, confidence, reasons
    
    def set_adaptive_threshold(self, threshold: float):
        """Set adaptive confidence threshold"""
        self.adaptive_threshold = max(0.5, min(0.75, threshold))
    
    def calculate_score(self, df: pd.DataFrame) -> float:
        """
        Calculate a numerical score for ranking trading pairs
        Higher score = better trading opportunity
        """
        signal, confidence, reasons = self.generate_signal(df)
        
        if signal == 'HOLD':
            return 0.0
        
        indicators = Indicators.get_latest_indicators(df)
        
        # Base score from confidence (weighted higher)
        score = confidence * 120
        
        # Bonus for strong trends (higher weight)
        momentum = abs(indicators.get('momentum', 0))
        if momentum > 0.04:
            score += 20
        elif momentum > 0.03:
            score += 15
        elif momentum > 0.02:
            score += 10
        
        # Bonus for high volume (confirmation)
        volume_ratio = indicators.get('volume_ratio', 0)
        if volume_ratio > 3.0:
            score += 15
        elif volume_ratio > 2.0:
            score += 10
        elif volume_ratio > 1.5:
            score += 5
        
        # Bonus for volatility (opportunity) but penalize extreme volatility
        bb_width = indicators.get('bb_width', 0)
        if 0.03 < bb_width < 0.08:
            score += 10  # Sweet spot
        elif bb_width > 0.10:
            score -= 5  # Too volatile
        elif bb_width > 0.05:
            score += 5
        
        # Bonus for extreme RSI (mean reversion opportunity)
        rsi = indicators.get('rsi', 50)
        if rsi < 25 or rsi > 75:
            score += 10
        elif rsi < 30 or rsi > 70:
            score += 5
        
        # Bonus for trending markets
        if self.market_regime == 'trending':
            score += 10
        
        # Risk-adjusted scoring: penalize high volatility relative to momentum
        if momentum > 0:
            risk_reward_ratio = momentum / max(bb_width, 0.01)
            if risk_reward_ratio > 1.0:
                score += 10  # Good risk/reward
            elif risk_reward_ratio < 0.5:
                score -= 5  # Poor risk/reward
        
        return score
