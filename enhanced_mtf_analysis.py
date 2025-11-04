"""
Enhanced Multi-Timeframe Analysis
Advanced timeframe confluence and adaptive weighting
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from logger import Logger
from indicators import Indicators


class EnhancedMultiTimeframeAnalysis:
    """
    Intelligent multi-timeframe analysis:
    - Adaptive timeframe weighting based on market conditions
    - Timeframe confluence scoring for signal validation
    - Dynamic timeframe selection based on asset volatility
    - Trend strength analysis across timeframes
    - Divergence detection between timeframes
    """

    def __init__(self):
        self.logger = Logger.get_logger()
        self.logger.info("📊 Enhanced Multi-Timeframe Analysis initialized")

    def calculate_timeframe_weight(self, timeframe: str,
                                   volatility: float,
                                   market_regime: str) -> float:
        """
        Calculate adaptive weight for each timeframe

        Args:
            timeframe: '1h', '4h', '1d'
            volatility: Market volatility
            market_regime: Current market regime

        Returns:
            Weight for this timeframe (0.0 to 1.0)
        """
        try:
            # Base weights
            base_weights = {
                '1h': 0.3,
                '4h': 0.4,
                '1d': 0.3
            }

            weight = base_weights.get(timeframe, 0.3)

            # Adjust based on volatility
            if volatility > 0.05:  # High volatility
                # Favor shorter timeframes for faster reaction
                if timeframe == '1h':
                    weight *= 1.3
                elif timeframe == '1d':
                    weight *= 0.8
            elif volatility < 0.02:  # Low volatility
                # Favor longer timeframes for stability
                if timeframe == '1d':
                    weight *= 1.3
                elif timeframe == '1h':
                    weight *= 0.8

            # Adjust based on market regime
            if market_regime == 'trending':
                # Favor longer timeframes in trends
                if timeframe == '1d':
                    weight *= 1.2
                elif timeframe == '4h':
                    weight *= 1.1
            elif market_regime == 'ranging':
                # Favor shorter timeframes in ranging markets
                if timeframe == '1h':
                    weight *= 1.2
                elif timeframe == '1d':
                    weight *= 0.9

            return weight

        except Exception as e:
            self.logger.debug(f"Error calculating timeframe weight: {e}")
            return 0.3

    def analyze_timeframe_confluence(self,
                                    df_1h: pd.DataFrame,
                                    df_4h: Optional[pd.DataFrame] = None,
                                    df_1d: Optional[pd.DataFrame] = None,
                                    signal_1h: str = 'HOLD',
                                    volatility: float = 0.03) -> Dict:
        """
        Analyze confluence across multiple timeframes

        Args:
            df_1h: 1-hour OHLCV data
            df_4h: 4-hour OHLCV data (optional)
            df_1d: 1-day OHLCV data (optional)
            signal_1h: Primary signal from 1h timeframe
            volatility: Current market volatility

        Returns:
            Dict with confluence analysis
        """
        try:
            if df_1h is None or len(df_1h) < 50:
                return {
                    'confluence_score': 0.0,
                    'alignment': 'none',
                    'confidence_multiplier': 1.0,
                    'reason': 'Insufficient 1h data'
                }

            # Get indicators for each timeframe
            ind_1h = Indicators.get_latest_indicators(df_1h)
            if not ind_1h:
                return {
                    'confluence_score': 0.0,
                    'alignment': 'none',
                    'confidence_multiplier': 1.0,
                    'reason': 'No indicators available'
                }

            # Detect market regime from 1h
            market_regime = self._detect_regime_from_indicators(ind_1h)

            # Calculate weights
            weight_1h = self.calculate_timeframe_weight('1h', volatility, market_regime)
            weight_4h = self.calculate_timeframe_weight('4h', volatility, market_regime)
            weight_1d = self.calculate_timeframe_weight('1d', volatility, market_regime)

            # Analyze each timeframe
            bullish_score = 0.0
            bearish_score = 0.0
            total_weight = weight_1h

            # 1-hour timeframe analysis
            if ind_1h['ema_12'] > ind_1h['ema_26']:
                bullish_score += weight_1h
            else:
                bearish_score += weight_1h

            if ind_1h['macd'] > ind_1h['macd_signal']:
                bullish_score += weight_1h * 0.5
            else:
                bearish_score += weight_1h * 0.5

            # 4-hour timeframe analysis
            if df_4h is not None and len(df_4h) >= 50:
                ind_4h = Indicators.get_latest_indicators(df_4h)
                if ind_4h:
                    total_weight += weight_4h

                    if ind_4h['ema_12'] > ind_4h['ema_26']:
                        bullish_score += weight_4h
                    else:
                        bearish_score += weight_4h

                    if ind_4h['macd'] > ind_4h['macd_signal']:
                        bullish_score += weight_4h * 0.5
                    else:
                        bearish_score += weight_4h * 0.5

                    # Check RSI alignment
                    rsi_4h = ind_4h.get('rsi', 50)
                    if rsi_4h > 55:
                        bullish_score += weight_4h * 0.3
                    elif rsi_4h < 45:
                        bearish_score += weight_4h * 0.3

            # 1-day timeframe analysis (stronger weight)
            if df_1d is not None and len(df_1d) >= 50:
                ind_1d = Indicators.get_latest_indicators(df_1d)
                if ind_1d:
                    total_weight += weight_1d

                    if ind_1d['ema_12'] > ind_1d['ema_26']:
                        bullish_score += weight_1d * 1.5  # Daily trend is more important
                    else:
                        bearish_score += weight_1d * 1.5

                    if ind_1d['macd'] > ind_1d['macd_signal']:
                        bullish_score += weight_1d * 0.8
                    else:
                        bearish_score += weight_1d * 0.8

            # Normalize scores
            if total_weight > 0:
                bullish_score = bullish_score / total_weight
                bearish_score = bearish_score / total_weight

            # Calculate confluence
            max_score = max(bullish_score, bearish_score)
            confluence_score = max_score

            # Determine alignment
            if bullish_score > bearish_score * 1.3:  # 30% stronger
                alignment = 'bullish'
                confidence_multiplier = 1.0 + (confluence_score * 0.25)  # Up to 25% boost
            elif bearish_score > bullish_score * 1.3:
                alignment = 'bearish'
                confidence_multiplier = 1.0 + (confluence_score * 0.25)
            else:
                alignment = 'mixed'
                confidence_multiplier = 0.9  # Slight penalty for conflicting signals

            # Check if alignment matches primary signal
            signal_alignment = False
            if signal_1h == 'BUY' and alignment == 'bullish':
                signal_alignment = True
            elif signal_1h == 'SELL' and alignment == 'bearish':
                signal_alignment = True

            # Adjust confidence if misaligned
            if not signal_alignment and alignment != 'mixed':
                confidence_multiplier *= 0.8  # 20% penalty for misalignment

            return {
                'confluence_score': confluence_score,
                'alignment': alignment,
                'confidence_multiplier': confidence_multiplier,
                'bullish_score': bullish_score,
                'bearish_score': bearish_score,
                'signal_alignment': signal_alignment,
                'reason': f'{alignment} confluence across timeframes'
            }

        except Exception as e:
            self.logger.error(f"Error analyzing timeframe confluence: {e}")
            return {
                'confluence_score': 0.0,
                'alignment': 'none',
                'confidence_multiplier': 1.0,
                'reason': f'Error: {str(e)}'
            }

    def detect_timeframe_divergence(self,
                                   df_1h: pd.DataFrame,
                                   df_4h: Optional[pd.DataFrame] = None) -> Dict:
        """
        Detect divergences between timeframes

        Args:
            df_1h: 1-hour OHLCV data
            df_4h: 4-hour OHLCV data

        Returns:
            Dict with divergence information
        """
        try:
            if df_1h is None or len(df_1h) < 50:
                return {'divergence': False, 'type': None, 'strength': 0.0}

            if df_4h is None or len(df_4h) < 50:
                return {'divergence': False, 'type': None, 'strength': 0.0}

            # Get indicators
            ind_1h = Indicators.get_latest_indicators(df_1h)
            ind_4h = Indicators.get_latest_indicators(df_4h)

            if not ind_1h or not ind_4h:
                return {'divergence': False, 'type': None, 'strength': 0.0}

            # Check trend direction on each timeframe
            trend_1h = 'bullish' if ind_1h['ema_12'] > ind_1h['ema_26'] else 'bearish'
            trend_4h = 'bullish' if ind_4h['ema_12'] > ind_4h['ema_26'] else 'bearish'

            # Check momentum direction
            momentum_1h = ind_1h.get('momentum', 0)
            momentum_4h = ind_4h.get('momentum', 0)

            # Detect divergence
            divergence = False
            div_type = None
            strength = 0.0

            # Trend divergence
            if trend_1h != trend_4h:
                divergence = True
                div_type = 'trend'
                strength = 0.5

                # Stronger if momentum also diverges
                if (momentum_1h > 0) != (momentum_4h > 0):
                    strength = 0.8

            # Momentum divergence without trend divergence
            elif abs(momentum_1h - momentum_4h) > 0.03:  # 3% difference
                divergence = True
                div_type = 'momentum'
                strength = min(abs(momentum_1h - momentum_4h) / 0.05, 1.0)

            return {
                'divergence': divergence,
                'type': div_type,
                'strength': strength,
                'trend_1h': trend_1h,
                'trend_4h': trend_4h
            }

        except Exception as e:
            self.logger.debug(f"Error detecting timeframe divergence: {e}")
            return {'divergence': False, 'type': None, 'strength': 0.0}

    def _detect_regime_from_indicators(self, indicators: Dict) -> str:
        """
        Helper to detect market regime from indicators

        Args:
            indicators: Technical indicators

        Returns:
            Market regime: 'trending', 'ranging', or 'neutral'
        """
        try:
            volatility = indicators.get('bb_width', 0.03)
            momentum = abs(indicators.get('momentum', 0))

            if momentum > 0.03:
                return 'trending'
            elif volatility < 0.02 and momentum < 0.01:
                return 'ranging'
            else:
                return 'neutral'
        except Exception:
            return 'neutral'

    def get_optimal_timeframe_for_entry(self,
                                       df_1h: pd.DataFrame,
                                       df_4h: Optional[pd.DataFrame] = None,
                                       df_1d: Optional[pd.DataFrame] = None,
                                       asset_volatility: float = 0.03) -> str:
        """
        Determine optimal timeframe for entry signal

        Args:
            df_1h: 1-hour data
            df_4h: 4-hour data
            df_1d: 1-day data
            asset_volatility: Asset-specific volatility

        Returns:
            Optimal timeframe: '1h', '4h', or '1d'
        """
        try:
            # High volatility assets -> use shorter timeframe
            if asset_volatility > 0.08:
                return '1h'

            # Low volatility assets -> use longer timeframe
            elif asset_volatility < 0.02:
                return '4h' if df_4h is not None and len(df_4h) >= 50 else '1h'

            # Medium volatility -> use balanced approach (4h)
            else:
                return '4h' if df_4h is not None and len(df_4h) >= 50 else '1h'

        except Exception as e:
            self.logger.debug(f"Error determining optimal timeframe: {e}")
            return '1h'
