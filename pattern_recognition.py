"""
Advanced chart pattern recognition for trading
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from logger import Logger
from scipy.signal import argrelextrema
from scipy.stats import linregress

class PatternRecognition:
    """Identify advanced chart patterns for improved signal quality"""

    def __init__(self):
        self.logger = Logger.get_logger()

    def find_peaks_and_troughs(self, df: pd.DataFrame, order: int = 5) -> Tuple[List, List]:
        """
        Find local peaks and troughs in price data

        Args:
            df: DataFrame with OHLCV data
            order: How many points on each side to use for comparison

        Returns:
            Tuple of (peaks, troughs) indices
        """
        if len(df) < order * 2 + 1:
            return [], []

        # Find local maxima and minima
        high_prices = df['high'].values
        low_prices = df['low'].values

        peaks = argrelextrema(high_prices, np.greater, order=order)[0]
        troughs = argrelextrema(low_prices, np.less, order=order)[0]

        return list(peaks), list(troughs)

    def detect_head_and_shoulders(self, df: pd.DataFrame) -> Dict:
        """
        Detect head and shoulders pattern (bearish reversal)

        Returns:
            Dict with pattern info or None if not detected
        """
        if len(df) < 50:
            return None

        peaks, troughs = self.find_peaks_and_troughs(df, order=3)

        if len(peaks) < 3 or len(troughs) < 2:
            return None

        # Get recent peaks and troughs
        recent_peaks = peaks[-3:]
        recent_troughs = troughs[-2:]

        if len(recent_peaks) != 3:
            return None

        # Check if middle peak (head) is higher than shoulders
        left_shoulder_idx = recent_peaks[0]
        head_idx = recent_peaks[1]
        right_shoulder_idx = recent_peaks[2]

        left_shoulder = df['high'].iloc[left_shoulder_idx]
        head = df['high'].iloc[head_idx]
        right_shoulder = df['high'].iloc[right_shoulder_idx]

        # Head should be highest, shoulders roughly equal
        if head > left_shoulder and head > right_shoulder:
            shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
            if shoulder_diff < 0.03:  # Shoulders within 3% of each other
                # Calculate neckline (support connecting troughs)
                if len(recent_troughs) >= 2:
                    neckline_price = (df['low'].iloc[recent_troughs[-2]] +
                                     df['low'].iloc[recent_troughs[-1]]) / 2

                    current_price = df['close'].iloc[-1]

                    # Pattern is complete if price breaks below neckline
                    if current_price < neckline_price:
                        return {
                            'pattern': 'head_and_shoulders',
                            'type': 'bearish',
                            'confidence': 0.8,
                            'target': neckline_price - (head - neckline_price),
                            'neckline': neckline_price
                        }

        return None

    def detect_inverse_head_and_shoulders(self, df: pd.DataFrame) -> Dict:
        """
        Detect inverse head and shoulders pattern (bullish reversal)

        Returns:
            Dict with pattern info or None if not detected
        """
        if len(df) < 50:
            return None

        peaks, troughs = self.find_peaks_and_troughs(df, order=3)

        if len(troughs) < 3 or len(peaks) < 2:
            return None

        # Get recent troughs and peaks
        recent_troughs = troughs[-3:]
        recent_peaks = peaks[-2:]

        if len(recent_troughs) != 3:
            return None

        # Check if middle trough (head) is lower than shoulders
        left_shoulder_idx = recent_troughs[0]
        head_idx = recent_troughs[1]
        right_shoulder_idx = recent_troughs[2]

        left_shoulder = df['low'].iloc[left_shoulder_idx]
        head = df['low'].iloc[head_idx]
        right_shoulder = df['low'].iloc[right_shoulder_idx]

        # Head should be lowest, shoulders roughly equal
        if head < left_shoulder and head < right_shoulder:
            shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
            if shoulder_diff < 0.03:  # Shoulders within 3% of each other
                # Calculate neckline (resistance connecting peaks)
                if len(recent_peaks) >= 2:
                    neckline_price = (df['high'].iloc[recent_peaks[-2]] +
                                     df['high'].iloc[recent_peaks[-1]]) / 2

                    current_price = df['close'].iloc[-1]

                    # Pattern is complete if price breaks above neckline
                    if current_price > neckline_price:
                        return {
                            'pattern': 'inverse_head_and_shoulders',
                            'type': 'bullish',
                            'confidence': 0.8,
                            'target': neckline_price + (neckline_price - head),
                            'neckline': neckline_price
                        }

        return None

    def detect_double_top(self, df: pd.DataFrame) -> Dict:
        """
        Detect double top pattern (bearish reversal)

        Returns:
            Dict with pattern info or None if not detected
        """
        if len(df) < 30:
            return None

        peaks, troughs = self.find_peaks_and_troughs(df, order=3)

        if len(peaks) < 2:
            return None

        # Get last two peaks
        peak1_idx = peaks[-2]
        peak2_idx = peaks[-1]

        peak1 = df['high'].iloc[peak1_idx]
        peak2 = df['high'].iloc[peak2_idx]

        # Peaks should be roughly equal (within 2%)
        peak_diff = abs(peak1 - peak2) / peak1
        if peak_diff < 0.02:
            # Find the trough between peaks
            troughs_between = [t for t in troughs if peak1_idx < t < peak2_idx]
            if troughs_between:
                support_price = df['low'].iloc[troughs_between[0]]
                current_price = df['close'].iloc[-1]

                # Pattern confirms on break below support
                if current_price < support_price:
                    return {
                        'pattern': 'double_top',
                        'type': 'bearish',
                        'confidence': 0.75,
                        'target': support_price - (peak1 - support_price),
                        'support': support_price
                    }

        return None

    def detect_double_bottom(self, df: pd.DataFrame) -> Dict:
        """
        Detect double bottom pattern (bullish reversal)

        Returns:
            Dict with pattern info or None if not detected
        """
        if len(df) < 30:
            return None

        peaks, troughs = self.find_peaks_and_troughs(df, order=3)

        if len(troughs) < 2:
            return None

        # Get last two troughs
        trough1_idx = troughs[-2]
        trough2_idx = troughs[-1]

        trough1 = df['low'].iloc[trough1_idx]
        trough2 = df['low'].iloc[trough2_idx]

        # Troughs should be roughly equal (within 2%)
        trough_diff = abs(trough1 - trough2) / trough1
        if trough_diff < 0.02:
            # Find the peak between troughs
            peaks_between = [p for p in peaks if trough1_idx < p < trough2_idx]
            if peaks_between:
                resistance_price = df['high'].iloc[peaks_between[0]]
                current_price = df['close'].iloc[-1]

                # Pattern confirms on break above resistance
                if current_price > resistance_price:
                    return {
                        'pattern': 'double_bottom',
                        'type': 'bullish',
                        'confidence': 0.75,
                        'target': resistance_price + (resistance_price - trough1),
                        'resistance': resistance_price
                    }

        return None

    def detect_triangle(self, df: pd.DataFrame) -> Dict:
        """
        Detect triangle patterns (ascending, descending, symmetrical)

        Returns:
            Dict with pattern info or None if not detected
        """
        if len(df) < 40:
            return None

        peaks, troughs = self.find_peaks_and_troughs(df, order=3)

        if len(peaks) < 2 or len(troughs) < 2:
            return None

        # Get recent peaks and troughs
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks[-2:]
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs[-2:]

        # Calculate trendlines
        peak_prices = [df['high'].iloc[i] for i in recent_peaks]
        trough_prices = [df['low'].iloc[i] for i in recent_troughs]

        # Linear regression for trendlines
        if len(peak_prices) >= 2:
            peak_slope, _, _, _, _ = linregress(recent_peaks, peak_prices)
        else:
            return None

        if len(trough_prices) >= 2:
            trough_slope, _, _, _, _ = linregress(recent_troughs, trough_prices)
        else:
            return None

        current_price = df['close'].iloc[-1]

        # Ascending triangle: flat resistance, rising support
        if abs(peak_slope) < 0.001 and trough_slope > 0.001:
            resistance = np.mean(peak_prices)
            if current_price > resistance:
                return {
                    'pattern': 'ascending_triangle',
                    'type': 'bullish',
                    'confidence': 0.7,
                    'breakout': 'upward',
                    'target': resistance + (resistance - min(trough_prices))
                }

        # Descending triangle: flat support, falling resistance
        elif abs(trough_slope) < 0.001 and peak_slope < -0.001:
            support = np.mean(trough_prices)
            if current_price < support:
                return {
                    'pattern': 'descending_triangle',
                    'type': 'bearish',
                    'confidence': 0.7,
                    'breakout': 'downward',
                    'target': support - (max(peak_prices) - support)
                }

        # Symmetrical triangle: converging trendlines
        elif peak_slope < -0.001 and trough_slope > 0.001:
            return {
                'pattern': 'symmetrical_triangle',
                'type': 'neutral',
                'confidence': 0.6,
                'breakout': 'pending',
                'message': 'Awaiting breakout direction'
            }

        return None

    def detect_wedge(self, df: pd.DataFrame) -> Dict:
        """
        Detect wedge patterns (rising/falling wedge)

        Returns:
            Dict with pattern info or None if not detected
        """
        if len(df) < 40:
            return None

        peaks, troughs = self.find_peaks_and_troughs(df, order=3)

        if len(peaks) < 3 or len(troughs) < 3:
            return None

        # Get recent peaks and troughs
        recent_peaks = peaks[-3:]
        recent_troughs = troughs[-3:]

        peak_prices = [df['high'].iloc[i] for i in recent_peaks]
        trough_prices = [df['low'].iloc[i] for i in recent_troughs]

        # Calculate slopes
        peak_slope, _, _, _, _ = linregress(recent_peaks, peak_prices)
        trough_slope, _, _, _, _ = linregress(recent_troughs, trough_prices)

        current_price = df['close'].iloc[-1]

        # Rising wedge: both lines rising, but converging (bearish)
        if peak_slope > 0 and trough_slope > 0 and peak_slope < trough_slope:
            return {
                'pattern': 'rising_wedge',
                'type': 'bearish',
                'confidence': 0.65,
                'message': 'Bearish reversal pattern'
            }

        # Falling wedge: both lines falling, but converging (bullish)
        elif peak_slope < 0 and trough_slope < 0 and peak_slope > trough_slope:
            return {
                'pattern': 'falling_wedge',
                'type': 'bullish',
                'confidence': 0.65,
                'message': 'Bullish reversal pattern'
            }

        return None

    def detect_all_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect all chart patterns

        Returns:
            List of detected patterns with their details
        """
        patterns = []

        # Try each pattern detection
        pattern_detectors = [
            self.detect_head_and_shoulders,
            self.detect_inverse_head_and_shoulders,
            self.detect_double_top,
            self.detect_double_bottom,
            self.detect_triangle,
            self.detect_wedge
        ]

        for detector in pattern_detectors:
            try:
                pattern = detector(df)
                if pattern:
                    patterns.append(pattern)
            except Exception as e:
                self.logger.debug(f"Error in pattern detection: {e}")

        return patterns

    def get_pattern_signal(self, df: pd.DataFrame) -> Tuple[str, float, str]:
        """
        Get trading signal from detected patterns

        Returns:
            Tuple of (signal, confidence, pattern_name)
            signal: 'BUY', 'SELL', or 'HOLD'
        """
        patterns = self.detect_all_patterns(df)

        if not patterns:
            return 'HOLD', 0.0, 'none'

        # Use the highest confidence pattern
        best_pattern = max(patterns, key=lambda p: p.get('confidence', 0))

        signal = 'HOLD'
        if best_pattern['type'] == 'bullish':
            signal = 'BUY'
        elif best_pattern['type'] == 'bearish':
            signal = 'SELL'

        confidence = best_pattern.get('confidence', 0.5)
        pattern_name = best_pattern.get('pattern', 'unknown')

        self.logger.debug(f"Pattern detected: {pattern_name} ({best_pattern['type']}) - confidence: {confidence:.2f}")

        return signal, confidence, pattern_name
