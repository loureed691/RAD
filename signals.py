"""
Trading signal generation based on technical indicators
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from indicators import Indicators
from logger import Logger

class SignalGenerator:
    """Generate trading signals based on multiple indicators"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.market_regime = 'neutral'  # 'trending', 'ranging', 'neutral'
        self.adaptive_threshold = 0.55
    
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
    
    def generate_signal(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        """
        Generate trading signal based on technical indicators with adaptive weighting
        
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
        
        # Detect market regime for adaptive strategy
        self.market_regime = self.detect_market_regime(df)
        
        buy_signals = 0.0
        sell_signals = 0.0
        reasons = {}
        reasons['market_regime'] = self.market_regime
        
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
        if indicators['stoch_k'] < 20 and indicators['stoch_k'] > indicators['stoch_d']:
            buy_signals += oscillator_weight
            reasons['stochastic'] = 'bullish crossover'
        elif indicators['stoch_k'] > 80 and indicators['stoch_k'] < indicators['stoch_d']:
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
            signal = 'HOLD'
            confidence = 0.5
        
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
        elif bb_width > 0.05:
            score += 5
        elif bb_width > 0.10:
            score -= 5  # Too volatile
        
        # Bonus for extreme RSI (mean reversion opportunity)
        rsi = indicators.get('rsi', 50)
        if rsi < 25 or rsi > 75:
            score += 10
        elif rsi < 30 or rsi > 70:
            score += 5
        
        # Bonus for trending markets
        if self.market_regime == 'trending':
            score += 10
        
        return score
