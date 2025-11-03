"""
Trading signal generation based on technical indicators
Enhanced with ML Strategy Coordinator 2025 for cutting-edge ML/AI integration
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from indicators import Indicators
from logger import Logger
from pattern_recognition import PatternRecognition
from volume_profile import VolumeProfile

# Import ML Strategy Coordinator 2025
try:
    from ml_strategy_coordinator_2025 import MLStrategyCoordinator2025
    ML_COORDINATOR_AVAILABLE = True
except ImportError:
    ML_COORDINATOR_AVAILABLE = False

class SignalGenerator:
    """Generate trading signals based on multiple indicators"""
    
    # Loss prevention thresholds - adjustable for fine-tuning
    MIN_CONFLUENCE_THRESHOLD = 0.55  # Minimum confluence score for penalty
    VERY_WEAK_CONFLUENCE_THRESHOLD = 0.40  # Below this, reject signal entirely
    
    # Volatility filter thresholds
    EXTREME_HIGH_VOLATILITY_BB = 0.12  # Max Bollinger Band width (12%)
    EXTREME_HIGH_VOLATILITY_ATR = 0.08  # Max ATR as % of price (8%)
    EXTREME_LOW_VOLATILITY_BB = 0.008  # Min Bollinger Band width (0.8%)
    EXTREME_LOW_VOLATILITY_ATR = 0.005  # Min ATR as % of price (0.5%)
    
    # Choppy market detection thresholds
    CHOPPY_MARKET_EMA_DIFF = 0.01  # Max EMA difference for choppy market (1%)
    CHOPPY_MARKET_ROC = 1.5  # Max ROC for choppy market
    
    # Risk-reward requirements
    MIN_RISK_REWARD_RATIO = 2.0  # Minimum R:R ratio required
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.strategy_logger = Logger.get_strategy_logger()
        self.market_regime = 'neutral'  # 'trending', 'ranging', 'neutral'
        self.adaptive_threshold = 0.72  # FURTHER INCREASED from 0.68 to prevent money loss - ultra-selective
        self.pattern_recognizer = PatternRecognition()
        self.volume_profile_analyzer = VolumeProfile()
        
        # Initialize ML Strategy Coordinator 2025 (cutting-edge ML/AI)
        if ML_COORDINATOR_AVAILABLE:
            try:
                self.ml_coordinator = MLStrategyCoordinator2025()
                self.ml_coordinator_enabled = True
                self.logger.info("✅ ML Strategy Coordinator 2025 enabled - Using cutting-edge ML/AI strategies")
            except Exception as e:
                self.logger.warning(f"⚠️  ML Strategy Coordinator unavailable: {e}")
                self.ml_coordinator = None
                self.ml_coordinator_enabled = False
        else:
            self.ml_coordinator = None
            self.ml_coordinator_enabled = False
            self.logger.info("ℹ️  ML Strategy Coordinator 2025 not available - Using standard technical analysis")
    
    def detect_support_resistance(self, df: pd.DataFrame, current_price: float) -> Dict:
        """
        Detect key support and resistance levels with enhanced algorithm
        
        Returns:
            Dict with support/resistance info including strength scores
        """
        if df.empty or len(df) < 20:
            return {'support': None, 'resistance': None, 'distance_to_support': 0, 'distance_to_resistance': 0}
        
        try:
            # Use recent price action (last 50 periods)
            recent_df = df.tail(50)
            
            # Find local highs and lows
            highs = recent_df['high'].values
            lows = recent_df['low'].values
            closes = recent_df['close'].values
            
            # Resistance: recent highest high
            resistance = np.max(highs)
            
            # Support: recent lowest low
            support = np.min(lows)
            
            # Calculate strength scores based on touch count
            support_touches = np.sum(np.abs(lows - support) / support < 0.01)
            resistance_touches = np.sum(np.abs(highs - resistance) / resistance < 0.01)
            
            # Calculate distances (as percentage)
            distance_to_resistance = (resistance - current_price) / current_price if current_price > 0 else 0
            distance_to_support = (current_price - support) / current_price if current_price > 0 else 0
            
            # Enhanced proximity detection with strength consideration
            near_support = distance_to_support < 0.02 or (distance_to_support < 0.03 and support_touches >= 2)
            near_resistance = distance_to_resistance < 0.02 or (distance_to_resistance < 0.03 and resistance_touches >= 2)
            
            return {
                'support': support,
                'resistance': resistance,
                'distance_to_support': distance_to_support,
                'distance_to_resistance': distance_to_resistance,
                'near_support': near_support,
                'near_resistance': near_resistance,
                'support_strength': min(support_touches / 5.0, 1.0),  # Normalize to 0-1
                'resistance_strength': min(resistance_touches / 5.0, 1.0)
            }
        except Exception as e:
            self.logger.debug(f"Error detecting support/resistance: {e}")
            return {'support': None, 'resistance': None, 'distance_to_support': 0, 'distance_to_resistance': 0}
    
    def detect_divergence(self, df: pd.DataFrame) -> Dict:
        """
        Detect bullish/bearish divergences between price and indicators
        
        Returns:
            Dict with divergence signals
        """
        if df.empty or len(df) < 20:
            return {'rsi_divergence': None, 'macd_divergence': None, 'strength': 0.0}
        
        try:
            # Look at last 20 periods
            recent_df = df.tail(20)
            
            # Get price and indicator trends
            price_trend = recent_df['close'].iloc[-1] - recent_df['close'].iloc[0]
            rsi_trend = recent_df['rsi'].iloc[-1] - recent_df['rsi'].iloc[0]
            macd_trend = recent_df['macd'].iloc[-1] - recent_df['macd'].iloc[0]
            
            divergence = {
                'rsi_divergence': None,
                'macd_divergence': None,
                'strength': 0.0
            }
            
            # Bullish divergence: price down, indicator up
            if price_trend < 0 and rsi_trend > 5:
                divergence['rsi_divergence'] = 'bullish'
                divergence['strength'] += 0.5
            # Bearish divergence: price up, indicator down
            elif price_trend > 0 and rsi_trend < -5:
                divergence['rsi_divergence'] = 'bearish'
                divergence['strength'] += 0.5
            
            # MACD divergence
            if price_trend < 0 and macd_trend > 0:
                divergence['macd_divergence'] = 'bullish'
                divergence['strength'] += 0.5
            elif price_trend > 0 and macd_trend < 0:
                divergence['macd_divergence'] = 'bearish'
                divergence['strength'] += 0.5
            
            return divergence
            
        except Exception as e:
            self.logger.debug(f"Error detecting divergence: {e}")
            return {'rsi_divergence': None, 'macd_divergence': None, 'strength': 0.0}
    
    def calculate_confluence_score(self, indicators: Dict, signal: str) -> float:
        """
        Calculate confluence score - how many signals align
        
        Returns:
            Score from 0.0 to 1.0 indicating signal strength
        """
        if signal not in ['BUY', 'SELL']:
            return 0.0
        
        aligned_signals = 0
        total_signals = 0
        
        # Check trend alignment
        total_signals += 1
        if signal == 'BUY' and indicators.get('ema_12', 0) > indicators.get('ema_26', 0):
            aligned_signals += 1
        elif signal == 'SELL' and indicators.get('ema_12', 0) < indicators.get('ema_26', 0):
            aligned_signals += 1
        
        # Check momentum
        total_signals += 1
        momentum = indicators.get('momentum', 0)
        if (signal == 'BUY' and momentum > 0) or (signal == 'SELL' and momentum < 0):
            aligned_signals += 1
        
        # Check RSI
        total_signals += 1
        rsi = indicators.get('rsi', 50)
        if (signal == 'BUY' and rsi < 50) or (signal == 'SELL' and rsi > 50):
            aligned_signals += 1
        
        # Check MACD
        total_signals += 1
        if signal == 'BUY' and indicators.get('macd', 0) > indicators.get('macd_signal', 0):
            aligned_signals += 1
        elif signal == 'SELL' and indicators.get('macd', 0) < indicators.get('macd_signal', 0):
            aligned_signals += 1
        
        # Check volume confirmation
        total_signals += 1
        if indicators.get('volume_ratio', 0) > 1.2:
            aligned_signals += 1
        
        return aligned_signals / total_signals if total_signals > 0 else 0.0
    
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
        
        # Detect divergences for additional signal strength
        divergence = self.detect_divergence(df)
        
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
        # PROFITABILITY FIX: Be more selective with RSI - avoid false reversals
        if rsi < 25:
            # Extreme oversold - strong buy signal
            buy_signals += (oscillator_weight * 2.0)  # INCREASED from 1.5
            reasons['rsi'] = f'extreme oversold ({rsi:.1f})'
        elif rsi < 30:
            buy_signals += (oscillator_weight * 1.5)
            reasons['rsi'] = f'oversold ({rsi:.1f})'
        elif rsi > 75:
            # Extreme overbought - strong sell signal
            sell_signals += (oscillator_weight * 2.0)  # INCREASED from 1.5
            reasons['rsi'] = f'extreme overbought ({rsi:.1f})'
        elif rsi > 70:
            sell_signals += (oscillator_weight * 1.5)
            reasons['rsi'] = f'overbought ({rsi:.1f})'
        elif 45 < rsi < 55:
            # PROFITABILITY FIX: Neutral zone - slightly penalize signals (choppy market)
            reasons['rsi'] = f'neutral ({rsi:.1f})'
            # Reduce signal strength in neutral RSI
            buy_signals *= 0.95
            sell_signals *= 0.95
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
        # LOSS PREVENTION: Require strong volume to avoid low-liquidity traps
        volume_ratio = indicators.get('volume_ratio', 0)
        if volume_ratio < 1.0:
            # Below-average volume - signal is unreliable (FURTHER INCREASED from 0.9)
            buy_signals *= 0.5  # Penalize even more heavily (INCREASED from 0.6)
            sell_signals *= 0.5
            reasons['volume'] = 'low volume - weak signal'
        elif volume_ratio > 1.5:
            reasons['volume'] = 'high volume confirmation'
            # Amplify existing signals with high volume
            if buy_signals > sell_signals:
                buy_signals += 1.0
            elif sell_signals > buy_signals:
                sell_signals += 1.0
        elif volume_ratio > 1.2:
            # Good volume - slight boost
            if buy_signals > sell_signals:
                buy_signals += 0.5
            elif sell_signals > buy_signals:
                sell_signals += 0.5
        
        # 7. Enhanced Momentum Analysis (weighted by regime)
        momentum_threshold = 0.015 if self.market_regime == 'ranging' else 0.02
        momentum = indicators['momentum']
        roc = indicators.get('roc', 0)
        
        # Combine momentum and ROC for stronger signal
        momentum_strength = (abs(momentum) + abs(roc) / 100) / 2
        
        if momentum > momentum_threshold:
            # Scale signal strength by momentum magnitude
            momentum_signal_strength = min(momentum_strength / momentum_threshold, 2.0) * trend_weight
            buy_signals += momentum_signal_strength
            reasons['momentum'] = f'strong positive ({momentum:.2%})'
        elif momentum < -momentum_threshold:
            momentum_signal_strength = min(momentum_strength / momentum_threshold, 2.0) * trend_weight
            sell_signals += momentum_signal_strength
            reasons['momentum'] = f'strong negative ({momentum:.2%})'
        elif momentum > 0.005:
            # Weak positive momentum
            buy_signals += trend_weight * 0.3
            reasons['momentum'] = f'weak positive ({momentum:.2%})'
        elif momentum < -0.005:
            # Weak negative momentum
            sell_signals += trend_weight * 0.3
            reasons['momentum'] = f'weak negative ({momentum:.2%})'
        
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
        
        # 9. Support/Resistance Analysis (ENHANCED)
        close = indicators['close']
        sr_levels = self.detect_support_resistance(df, close)
        if sr_levels.get('near_support', False):
            # Near support is a potential buy opportunity - weight by strength
            support_weight = 1.5 * (1 + sr_levels.get('support_strength', 0))
            buy_signals += support_weight
            reasons['support_resistance'] = f'near support ({sr_levels["distance_to_support"]:.1%}, strength: {sr_levels.get("support_strength", 0):.1f})'
        elif sr_levels.get('near_resistance', False):
            # Near resistance is a potential sell opportunity - weight by strength
            resistance_weight = 1.5 * (1 + sr_levels.get('resistance_strength', 0))
            sell_signals += resistance_weight
            reasons['support_resistance'] = f'near resistance ({sr_levels["distance_to_resistance"]:.1%}, strength: {sr_levels.get("resistance_strength", 0):.1f})'
        
        # 10. Divergence Detection (NEW)
        if divergence['strength'] > 0:
            divergence_weight = divergence['strength'] * 2.0
            if divergence.get('rsi_divergence') == 'bullish' or divergence.get('macd_divergence') == 'bullish':
                buy_signals += divergence_weight
                reasons['divergence'] = 'bullish divergence detected'
                self.logger.info(f"🔍 Bullish divergence detected (strength: {divergence['strength']:.1f})")
            elif divergence.get('rsi_divergence') == 'bearish' or divergence.get('macd_divergence') == 'bearish':
                sell_signals += divergence_weight
                reasons['divergence'] = 'bearish divergence detected'
                self.logger.info(f"🔍 Bearish divergence detected (strength: {divergence['strength']:.1f})")
        
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
        
        # Adaptive threshold based on market regime - ULTRA-SELECTIVE to prevent losses
        if self.market_regime == 'trending':
            min_confidence = 0.70  # FURTHER INCREASED from 0.65 - only strongest trending signals
        elif self.market_regime == 'ranging':
            min_confidence = 0.76  # FURTHER INCREASED from 0.72 - ranging markets are dangerous
        else:
            min_confidence = self.adaptive_threshold
        
        # Require minimum confidence threshold
        if confidence < min_confidence:
            signal = 'HOLD'
            reasons['confidence'] = f'too low ({confidence:.2f} < {min_confidence:.2f})'
        
        # LOSS PREVENTION: Require even stronger signal strength ratio
        # This prevents weak trades where buy/sell signals are too close
        if signal != 'HOLD':
            weaker_signal = min(buy_signals, sell_signals)
            stronger_signal = max(buy_signals, sell_signals)
            if stronger_signal > 0:
                signal_ratio = stronger_signal / (weaker_signal + 1)  # Add 1 to avoid div by 0
                # Require at least 3.0:1 ratio - FURTHER INCREASED from 2.5:1 to prevent losses
                if signal_ratio < 3.0:
                    signal = 'HOLD'
                    confidence = 0.0
                    reasons['weak_signal_ratio'] = f'insufficient signal strength ({signal_ratio:.2f}:1, need 3.0:1)'
        
        # PROFITABILITY FIX: Require trend and momentum alignment for non-extreme conditions
        # STRENGTHENED: Require BOTH trend AND momentum alignment (not just OR) for stronger signals
        if signal != 'HOLD' and rsi > 25 and rsi < 75:  # Not in extreme oversold/overbought (wider range)
            # Check if trend and momentum agree with the signal
            ema_12 = indicators.get('ema_12', 0)
            ema_26 = indicators.get('ema_26', 0)
            momentum = indicators.get('momentum', 0)
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            
            if signal == 'BUY':
                # For BUY, require BOTH bullish trend AND bullish momentum (STRENGTHENED from OR)
                trend_bullish = ema_12 > ema_26
                momentum_bullish = momentum > 0 and macd > macd_signal
                if not (trend_bullish and momentum_bullish):
                    signal = 'HOLD'
                    confidence = 0.0
                    reasons['trend_momentum_mismatch'] = 'both trend AND momentum must align with BUY'
            elif signal == 'SELL':
                # For SELL, require BOTH bearish trend AND bearish momentum (STRENGTHENED from OR)
                trend_bearish = ema_12 < ema_26
                momentum_bearish = momentum < 0 and macd < macd_signal
                if not (trend_bearish and momentum_bearish):
                    signal = 'HOLD'
                    confidence = 0.0
                    reasons['trend_momentum_mismatch'] = 'both trend AND momentum must align with SELL'
        
        # Apply confluence scoring boost (NEW)
        if signal != 'HOLD':
            confluence_score = self.calculate_confluence_score(indicators, signal)
            if confluence_score > 0.7:
                # Strong confluence - boost confidence
                confidence *= (1.0 + (confluence_score - 0.7) * 0.5)  # Up to 15% boost
                confidence = min(confidence, 0.99)
                reasons['confluence'] = f'strong ({confluence_score:.1%})'
            elif confluence_score < self.MIN_CONFLUENCE_THRESHOLD:  # Use class constant
                # Weak confluence - reduce confidence more aggressively
                confidence *= 0.75  # FURTHER INCREASED penalty from 0.80
                reasons['confluence'] = f'weak ({confluence_score:.1%})'
                # If confluence is too weak, reject the signal entirely
                if confluence_score < self.VERY_WEAK_CONFLUENCE_THRESHOLD:  # Use class constant
                    signal = 'HOLD'
                    confidence = 0.0
                    reasons['very_weak_confluence'] = f'extremely weak signal alignment ({confluence_score:.1%})'
        
        # Apply multi-timeframe confidence boost
        if signal != 'HOLD' and mtf_analysis['trend_alignment'] != 'neutral':
            # Boost confidence if MTF aligns with signal
            if (signal == 'BUY' and mtf_analysis['trend_alignment'] == 'bullish') or \
               (signal == 'SELL' and mtf_analysis['trend_alignment'] == 'bearish'):
                confidence *= mtf_analysis['confidence_multiplier']
                confidence = min(confidence, 0.99)  # Cap at 99%
                reasons['mtf_boost'] = f"+{(mtf_analysis['confidence_multiplier']-1)*100:.0f}%"
            # MTF conflict handling: When higher timeframes disagree, be VERY conservative
            elif (signal == 'BUY' and mtf_analysis['trend_alignment'] == 'bearish') or \
                 (signal == 'SELL' and mtf_analysis['trend_alignment'] == 'bullish'):
                confidence *= 0.5  # Even stronger penalty for conflicting signals (INCREASED from 0.6)
                # Keep original threshold - don't make it easier to pass when there's conflict
                reasons['mtf_conflict'] = 'warning'
                if confidence < min_confidence:
                    signal = 'HOLD'
                    reasons['confidence'] = f'too low after MTF adjustment ({confidence:.2f} < {min_confidence:.2f})'
        
        # ADDITIONAL FILTER: Reject signals with no multi-timeframe support in neutral regime
        if signal != 'HOLD' and self.market_regime == 'neutral' and mtf_analysis.get('trend_alignment') == 'neutral':
            # In uncertain conditions, require either strong confidence or MTF confirmation
            if confidence < 0.75:  # Very high threshold for neutral/neutral combination
                signal = 'HOLD'
                confidence = 0.0
                reasons['neutral_regime_no_mtf'] = 'neutral market + no MTF support requires >75% confidence'
        
        # LOSS PREVENTION: Reject signals in extremely volatile conditions (whipsaw risk)
        bb_width = indicators.get('bb_width', 0)
        atr_normalized = indicators.get('atr', 0) / indicators.get('close', 1) if indicators.get('close', 0) > 0 else 0
        if signal != 'HOLD':
            # Avoid extreme volatility that leads to stop-loss hunting
            if bb_width > self.EXTREME_HIGH_VOLATILITY_BB or atr_normalized > self.EXTREME_HIGH_VOLATILITY_ATR:
                signal = 'HOLD'
                confidence = 0.0
                reasons['extreme_volatility'] = f'dangerous volatility (bb_width: {bb_width:.3f}, atr: {atr_normalized:.3f})'
            # Also avoid very low volatility (low profit potential, high slippage risk)
            elif bb_width < self.EXTREME_LOW_VOLATILITY_BB or atr_normalized < self.EXTREME_LOW_VOLATILITY_ATR:
                signal = 'HOLD'
                confidence = 0.0
                reasons['insufficient_volatility'] = f'too low volatility for profitable trade (bb_width: {bb_width:.3f})'
        
        # LOSS PREVENTION: Check for choppy market conditions using ADX-like logic
        if signal != 'HOLD':
            # Calculate trend strength
            ema_12 = indicators.get('ema_12', 0)
            ema_26 = indicators.get('ema_26', 0)
            ema_diff = abs(ema_12 - ema_26) / ema_26 if ema_26 > 0 else 0
            roc = abs(indicators.get('roc', 0))
            
            # Choppy market: weak trend + conflicting signals
            is_choppy = (ema_diff < self.CHOPPY_MARKET_EMA_DIFF and roc < self.CHOPPY_MARKET_ROC)
            if is_choppy:
                signal = 'HOLD'
                confidence = 0.0
                reasons['choppy_market'] = f'no clear trend (ema_diff: {ema_diff:.3%}, roc: {roc:.2f})'
        
        # LOSS PREVENTION: Require strong risk-reward ratio
        if signal != 'HOLD':
            # Calculate potential risk-reward based on volatility
            close = indicators.get('close', 0)
            if close > 0 and bb_width > 0:
                # Estimate stop loss distance (1.5x ATR or BB width)
                estimated_stop_distance = max(atr_normalized * 1.5, bb_width / 2)
                # Estimate take profit potential (2x ATR or 1.5x BB width)
                estimated_tp_potential = max(atr_normalized * 2.5, bb_width * 1.5)
                
                # Require minimum risk-reward ratio
                if estimated_stop_distance > 0:
                    risk_reward = estimated_tp_potential / estimated_stop_distance
                    if risk_reward < self.MIN_RISK_REWARD_RATIO:  # Use class constant
                        signal = 'HOLD'
                        confidence = 0.0
                        reasons['poor_risk_reward'] = f'insufficient R:R ratio ({risk_reward:.2f}:1, need {self.MIN_RISK_REWARD_RATIO}:1)'
        
        self.logger.debug(f"Signal: {signal}, Confidence: {confidence:.2f}, Regime: {self.market_regime}, Buy: {buy_signals:.1f}/{total_signals:.1f}, Sell: {sell_signals:.1f}/{total_signals:.1f}")
        
        # === ML STRATEGY COORDINATOR 2025 INTEGRATION ===
        # Apply cutting-edge ML/AI enhancements using unified ML framework
        if self.ml_coordinator_enabled and signal != 'HOLD':
            try:
                # Get volatility for ML coordinator
                volatility = indicators.get('bb_width', 0.03)
                
                # Generate unified ML-enhanced signal
                ml_signal, ml_confidence, ml_reasons = self.ml_coordinator.generate_unified_signal(
                    technical_signal=signal,
                    technical_confidence=confidence,
                    technical_reasons=reasons,
                    df_1h=df,
                    df_4h=df_4h,
                    df_1d=df_1d,
                    indicators=indicators,
                    market_regime=self.market_regime,
                    volatility=volatility
                )
                
                # Use ML-enhanced signal and confidence
                signal = ml_signal
                confidence = ml_confidence
                reasons.update(ml_reasons)
                
                self.logger.info(f"🤖 ML Strategy Coordinator enhanced signal: {signal} (conf: {confidence:.2%})")
                
            except Exception as e:
                self.logger.warning(f"ML Strategy Coordinator error (falling back to technical): {e}")
                # Continue with technical signal on error
        
        # Log strategy details to strategy logger if signal is not HOLD
        if signal != 'HOLD':
            self.strategy_logger.info("=" * 80)
            self.strategy_logger.info(f"TRADING STRATEGY ANALYSIS")
            self.strategy_logger.info("-" * 80)
            self.strategy_logger.info(f"  Signal: {signal}")
            self.strategy_logger.info(f"  Confidence: {confidence:.2%}")
            self.strategy_logger.info(f"  Market Regime: {self.market_regime}")
            self.strategy_logger.info(f"  Buy Signals: {buy_signals:.2f} / {total_signals:.2f}")
            self.strategy_logger.info(f"  Sell Signals: {sell_signals:.2f} / {total_signals:.2f}")
            self.strategy_logger.info(f"  Multi-Timeframe Alignment: {mtf_analysis['trend_alignment']}")
            if self.ml_coordinator_enabled:
                self.strategy_logger.info(f"  ML Coordinator: ACTIVE ✅")
            self.strategy_logger.info("")
            self.strategy_logger.info("  Strategy Components:")
            for key, value in reasons.items():
                if key not in ['no_signals', 'equal_signals', 'confidence']:
                    self.strategy_logger.info(f"    - {key}: {value}")
            self.strategy_logger.info("=" * 80)
            self.strategy_logger.info("")
        
        return signal, confidence, reasons
    
    def set_adaptive_threshold(self, threshold: float):
        """Set adaptive confidence threshold"""
        self.adaptive_threshold = max(0.5, min(0.75, threshold))
    
    def calculate_score(self, df: pd.DataFrame) -> float:
        """
        Calculate a numerical score for ranking trading pairs with volume profile analysis
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
            score += 25  # Increased from 20
        elif momentum > 0.03:
            score += 18  # Increased from 15
        elif momentum > 0.02:
            score += 12  # Increased from 10
        elif momentum > 0.01:
            score += 5  # Added gradation
        
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
            score += 12  # Sweet spot - increased from 10
        elif bb_width > 0.10:
            score -= 8  # Too volatile - increased penalty from -5
        elif bb_width > 0.05:
            score += 6  # Increased from 5
        elif bb_width < 0.01:
            score -= 3  # Too low volatility - new penalty
        
        # Bonus for extreme RSI (mean reversion opportunity)
        rsi = indicators.get('rsi', 50)
        if rsi < 25 or rsi > 75:
            score += 12  # Increased from 10
        elif rsi < 30 or rsi > 70:
            score += 6  # Increased from 5
        
        # Bonus for trending markets
        if self.market_regime == 'trending':
            score += 12  # Increased from 10
        elif self.market_regime == 'ranging':
            score += 5  # Small bonus for range trading opportunities
        
        # Risk-adjusted scoring: penalize high volatility relative to momentum
        if momentum > 0:
            risk_reward_ratio = momentum / max(bb_width, 0.01)
            if risk_reward_ratio > 1.5:
                score += 15  # Excellent risk/reward - increased from 10
            elif risk_reward_ratio > 1.0:
                score += 8  # Good risk/reward - increased from 10
            elif risk_reward_ratio < 0.5:
                score -= 8  # Poor risk/reward - increased penalty from -5
        else:
            # Negative or zero momentum - penalize low risk/reward
            score -= 5
        
        # ENHANCED: Volume Profile Analysis (NEW)
        close = indicators.get('close', 0)
        if close > 0:
            # Calculate volume profile
            volume_profile = self.volume_profile_analyzer.calculate_volume_profile(df)
            
            if volume_profile.get('poc'):
                # Check if near high-volume node
                is_near_node, node_type = self.volume_profile_analyzer.is_near_high_volume_node(
                    close, volume_profile, threshold=0.015
                )
                
                # Get volume-based support/resistance
                vol_sr = self.volume_profile_analyzer.get_support_resistance_from_volume(
                    close, volume_profile
                )
                
                # Bonus for being in value area (institutional interest)
                if vol_sr.get('in_value_area', False):
                    score += 8  # Trading in high-volume area
                
                # Strong bonus for bouncing off volume-based support (BUY)
                if signal == 'BUY' and vol_sr.get('support'):
                    distance_to_support = (close - vol_sr['support']) / close
                    if distance_to_support < 0.02:  # Within 2% of support
                        strength = vol_sr.get('support_strength', 0)
                        score += 15 * strength  # Weighted by support strength
                        if node_type == 'POC':
                            score += 5  # Extra bonus for POC (strongest level)
                
                # Strong bonus for rejecting at volume-based resistance (SELL)
                if signal == 'SELL' and vol_sr.get('resistance'):
                    distance_to_resistance = (vol_sr['resistance'] - close) / close
                    if distance_to_resistance < 0.02:  # Within 2% of resistance
                        strength = vol_sr.get('resistance_strength', 0)
                        score += 15 * strength  # Weighted by resistance strength
                        if node_type == 'POC':
                            score += 5  # Extra bonus for POC (strongest level)
        
        # Existing support/resistance bonus (keep for compatibility)
        sr_levels = self.detect_support_resistance(df, close)
        if sr_levels.get('near_support', False) and signal == 'BUY':
            score += 10  # Bouncing off support
        elif sr_levels.get('near_resistance', False) and signal == 'SELL':
            score += 10  # Rejecting at resistance
        
        # Bonus for multi-timeframe alignment (if available in reasons)
        if reasons.get('mtf_boost'):
            score += 8  # Multi-timeframe confirmation
        
        # Penalty for conflicting signals
        if reasons.get('mtf_conflict'):
            score -= 5  # Multi-timeframe conflict
        
        return score
