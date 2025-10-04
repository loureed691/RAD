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
    
    def generate_signal(self, df: pd.DataFrame) -> Tuple[str, float, Dict]:
        """
        Generate trading signal based on technical indicators
        
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
        
        buy_signals = 0
        sell_signals = 0
        reasons = {}
        
        # 1. Trend Following - Moving Average Crossover
        if indicators['ema_12'] > indicators['ema_26']:
            buy_signals += 2
            reasons['ma_trend'] = 'bullish'
        elif indicators['ema_12'] < indicators['ema_26']:
            sell_signals += 2
            reasons['ma_trend'] = 'bearish'
        
        # 2. MACD
        if indicators['macd'] > indicators['macd_signal'] and indicators['macd_diff'] > 0:
            buy_signals += 2
            reasons['macd'] = 'bullish'
        elif indicators['macd'] < indicators['macd_signal'] and indicators['macd_diff'] < 0:
            sell_signals += 2
            reasons['macd'] = 'bearish'
        
        # 3. RSI
        rsi = indicators['rsi']
        if rsi < 30:
            buy_signals += 1.5
            reasons['rsi'] = f'oversold ({rsi:.1f})'
        elif rsi > 70:
            sell_signals += 1.5
            reasons['rsi'] = f'overbought ({rsi:.1f})'
        elif 40 < rsi < 60:
            reasons['rsi'] = f'neutral ({rsi:.1f})'
        
        # 4. Stochastic Oscillator
        if indicators['stoch_k'] < 20 and indicators['stoch_k'] > indicators['stoch_d']:
            buy_signals += 1
            reasons['stochastic'] = 'bullish crossover'
        elif indicators['stoch_k'] > 80 and indicators['stoch_k'] < indicators['stoch_d']:
            sell_signals += 1
            reasons['stochastic'] = 'bearish crossover'
        
        # 5. Bollinger Bands
        close = indicators['close']
        if close < indicators['bb_low']:
            buy_signals += 1
            reasons['bollinger'] = 'below lower band'
        elif close > indicators['bb_high']:
            sell_signals += 1
            reasons['bollinger'] = 'above upper band'
        
        # 6. Volume
        if indicators['volume_ratio'] > 1.5:
            reasons['volume'] = 'high volume confirmation'
            # Amplify existing signals with high volume
            if buy_signals > sell_signals:
                buy_signals += 0.5
            elif sell_signals > buy_signals:
                sell_signals += 0.5
        
        # 7. Momentum
        if indicators['momentum'] > 0.02:
            buy_signals += 1
            reasons['momentum'] = 'strong positive'
        elif indicators['momentum'] < -0.02:
            sell_signals += 1
            reasons['momentum'] = 'strong negative'
        
        total_signals = buy_signals + sell_signals
        
        # Calculate confidence
        if total_signals == 0:
            # No signals fired, remain neutral
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
        
        # Require minimum confidence threshold (lowered to 0.55 for more opportunities)
        if confidence < 0.55:
            signal = 'HOLD'
            reasons['confidence'] = f'too low ({confidence:.2f})'
        
        self.logger.info(f"Signal: {signal}, Confidence: {confidence:.2f}, Buy: {buy_signals}/{total_signals}, Sell: {sell_signals}/{total_signals}, Reasons: {reasons}")
        
        return signal, confidence, reasons
    
    def calculate_score(self, df: pd.DataFrame) -> float:
        """
        Calculate a numerical score for ranking trading pairs
        Higher score = better trading opportunity
        """
        signal, confidence, _ = self.generate_signal(df)
        
        if signal == 'HOLD':
            return 0.0
        
        indicators = Indicators.get_latest_indicators(df)
        
        # Base score from confidence
        score = confidence * 100
        
        # Bonus for strong trends
        if abs(indicators.get('momentum', 0)) > 0.03:
            score += 10
        
        # Bonus for high volume
        if indicators.get('volume_ratio', 0) > 2.0:
            score += 10
        
        # Bonus for volatility (ATR)
        if indicators.get('bb_width', 0) > 0.05:
            score += 5
        
        return score
