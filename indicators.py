"""
Technical indicators for trading signals
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange

class Indicators:
    """Calculate technical indicators for trading"""
    
    @staticmethod
    def detect_candlestick_patterns(df: pd.DataFrame) -> Dict:
        """
        Detect advanced candlestick patterns for sentiment analysis
        
        Returns:
            Dict with detected patterns and their sentiment scores
        """
        if df.empty or len(df) < 3:
            return {'patterns': [], 'bullish_score': 0, 'bearish_score': 0}
        
        try:
            last_3 = df.tail(3)
            current = last_3.iloc[-1]
            prev = last_3.iloc[-2]
            prev2 = last_3.iloc[-3] if len(last_3) >= 3 else None
            
            patterns = []
            bullish_score = 0
            bearish_score = 0
            
            # Calculate candle body and wicks
            body = abs(current['close'] - current['open'])
            body_pct = body / current['open'] if current['open'] > 0 else 0
            upper_wick = current['high'] - max(current['close'], current['open'])
            lower_wick = min(current['close'], current['open']) - current['low']
            
            # Hammer (bullish reversal)
            if (lower_wick > 2 * body and upper_wick < body * 0.3 and 
                current['close'] > current['open']):
                patterns.append('hammer')
                bullish_score += 2
            
            # Shooting Star (bearish reversal)
            if (upper_wick > 2 * body and lower_wick < body * 0.3 and 
                current['close'] < current['open']):
                patterns.append('shooting_star')
                bearish_score += 2
            
            # Doji (indecision)
            if body_pct < 0.001:
                patterns.append('doji')
            
            # Engulfing patterns
            if prev is not None:
                prev_body = abs(prev['close'] - prev['open'])
                
                # Bullish Engulfing
                if (prev['close'] < prev['open'] and  # prev bearish
                    current['close'] > current['open'] and  # current bullish
                    current['open'] < prev['close'] and
                    current['close'] > prev['open']):
                    patterns.append('bullish_engulfing')
                    bullish_score += 3
                
                # Bearish Engulfing
                if (prev['close'] > prev['open'] and  # prev bullish
                    current['close'] < current['open'] and  # current bearish
                    current['open'] > prev['close'] and
                    current['close'] < prev['open']):
                    patterns.append('bearish_engulfing')
                    bearish_score += 3
            
            # Morning/Evening Star (3-candle patterns)
            if prev is not None and prev2 is not None:
                # Morning Star (bullish)
                if (prev2['close'] < prev2['open'] and  # first bearish
                    abs(prev['close'] - prev['open']) < body * 0.3 and  # middle doji-like
                    current['close'] > current['open'] and  # third bullish
                    current['close'] > (prev2['open'] + prev2['close']) / 2):
                    patterns.append('morning_star')
                    bullish_score += 4
                
                # Evening Star (bearish)
                if (prev2['close'] > prev2['open'] and  # first bullish
                    abs(prev['close'] - prev['open']) < body * 0.3 and  # middle doji-like
                    current['close'] < current['open'] and  # third bearish
                    current['close'] < (prev2['open'] + prev2['close']) / 2):
                    patterns.append('evening_star')
                    bearish_score += 4
            
            return {
                'patterns': patterns,
                'bullish_score': bullish_score,
                'bearish_score': bearish_score,
                'net_sentiment': bullish_score - bearish_score
            }
        except Exception as e:
            return {'patterns': [], 'bullish_score': 0, 'bearish_score': 0}
    
    @staticmethod
    def calculate_all(ohlcv_data: List) -> pd.DataFrame:
        """
        Calculate all technical indicators from OHLCV data
        
        Args:
            ohlcv_data: List of [timestamp, open, high, low, close, volume]
        
        Returns:
            DataFrame with all indicators
        """
        if not ohlcv_data:
            return pd.DataFrame()
            
        if len(ohlcv_data) < 50:
            # Return empty DataFrame with a note - caller should check for this
            return pd.DataFrame()
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Moving Averages
            df['sma_20'] = SMAIndicator(df['close'], window=20).sma_indicator()
            df['sma_50'] = SMAIndicator(df['close'], window=50).sma_indicator()
            df['ema_12'] = EMAIndicator(df['close'], window=12).ema_indicator()
            df['ema_26'] = EMAIndicator(df['close'], window=26).ema_indicator()
            
            # MACD
            macd = MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            # RSI
            df['rsi'] = RSIIndicator(df['close'], window=14).rsi()
            
            # Stochastic Oscillator
            stoch = StochasticOscillator(df['high'], df['low'], df['close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # Bollinger Bands
            bb = BollingerBands(df['close'])
            df['bb_high'] = bb.bollinger_hband()
            df['bb_mid'] = bb.bollinger_mavg()
            df['bb_low'] = bb.bollinger_lband()
            df['bb_width'] = (df['bb_high'] - df['bb_low']) / df['bb_mid']
            
            # ATR (Average True Range)
            df['atr'] = AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            # Handle potential division by zero or NaN in volume_sma
            df['volume_ratio'] = df['volume'] / df['volume_sma'].replace(0, np.nan)
            df['volume_ratio'] = df['volume_ratio'].fillna(1.0)  # Default to 1.0 if NaN
            
            # Price momentum
            df['momentum'] = df['close'].pct_change(periods=10)
            df['roc'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
            
            # Volume-weighted indicators (VWAP with rolling window to avoid indefinite growth)
            # Use a 50-period rolling window for VWAP calculation
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            df['vwap'] = (typical_price * df['volume']).rolling(window=50, min_periods=1).sum() / df['volume'].rolling(window=50, min_periods=1).sum()
            
            return df
        except Exception as e:
            # If any error occurs during indicator calculation, return empty DataFrame
            return pd.DataFrame()
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, lookback: int = 50) -> Dict:
        """
        Calculate key support and resistance levels using volume profile
        
        Returns:
            Dict with support/resistance levels and strength
        """
        if df.empty or len(df) < lookback:
            return {'support': [], 'resistance': [], 'poc': None}
        
        try:
            # Use last N candles
            recent_df = df.tail(lookback).copy()
            
            # Calculate price levels and volume at each level
            price_min = recent_df['low'].min()
            price_max = recent_df['high'].max()
            price_range = price_max - price_min
            
            # Create price bins
            num_bins = 20
            bins = np.linspace(price_min, price_max, num_bins)
            
            # Volume profile: accumulate volume at each price level
            volume_profile = np.zeros(num_bins - 1)
            
            for idx, row in recent_df.iterrows():
                # Find which bin this candle's range covers
                candle_low = row['low']
                candle_high = row['high']
                candle_volume = row['volume']
                
                # Distribute volume across price levels
                for i in range(len(bins) - 1):
                    bin_low = bins[i]
                    bin_high = bins[i + 1]
                    
                    # Check if candle intersects with this bin
                    if candle_high >= bin_low and candle_low <= bin_high:
                        # Calculate overlap
                        overlap_low = max(candle_low, bin_low)
                        overlap_high = min(candle_high, bin_high)
                        overlap_ratio = (overlap_high - overlap_low) / (candle_high - candle_low) if candle_high > candle_low else 1.0
                        volume_profile[i] += candle_volume * overlap_ratio
            
            # Find POC (Point of Control - highest volume level)
            poc_idx = np.argmax(volume_profile)
            poc_price = (bins[poc_idx] + bins[poc_idx + 1]) / 2
            
            # Find support levels (high volume below current price)
            current_price = df['close'].iloc[-1]
            support_levels = []
            resistance_levels = []
            
            # Find local maxima in volume profile
            for i in range(1, len(volume_profile) - 1):
                if volume_profile[i] > volume_profile[i-1] and volume_profile[i] > volume_profile[i+1]:
                    level_price = (bins[i] + bins[i + 1]) / 2
                    level_strength = volume_profile[i] / volume_profile.sum()
                    
                    if level_price < current_price:
                        support_levels.append({'price': level_price, 'strength': level_strength})
                    else:
                        resistance_levels.append({'price': level_price, 'strength': level_strength})
            
            # Sort by strength
            support_levels.sort(key=lambda x: x['strength'], reverse=True)
            resistance_levels.sort(key=lambda x: x['strength'], reverse=True)
            
            return {
                'support': support_levels[:3],  # Top 3 support levels
                'resistance': resistance_levels[:3],  # Top 3 resistance levels
                'poc': poc_price
            }
            
        except Exception as e:
            return {'support': [], 'resistance': [], 'poc': None}
    
    @staticmethod
    def analyze_volatility_clustering(df: pd.DataFrame, window: int = 20) -> Dict:
        """
        Analyze volatility clustering for adaptive position sizing
        Uses GARCH-like approach to detect high/low volatility regimes
        
        Returns:
            Dict with volatility metrics and regime classification
        """
        if df.empty or len(df) < window:
            return {
                'current_volatility': 0.0,
                'avg_volatility': 0.0,
                'volatility_regime': 'normal',
                'volatility_percentile': 0.5,
                'clustering_detected': False
            }
        
        try:
            # Calculate returns
            returns = df['close'].pct_change().dropna()
            
            if len(returns) < window:
                return {
                    'current_volatility': 0.0,
                    'avg_volatility': 0.0,
                    'volatility_regime': 'normal',
                    'volatility_percentile': 0.5,
                    'clustering_detected': False
                }
            
            # Rolling standard deviation (volatility)
            rolling_vol = returns.rolling(window=window).std()
            
            # Current volatility
            current_vol = rolling_vol.iloc[-1] if not pd.isna(rolling_vol.iloc[-1]) else 0.0
            
            # Average volatility over period
            avg_vol = rolling_vol.mean()
            
            # Volatility percentile (where current vol ranks)
            volatility_percentile = (rolling_vol < current_vol).sum() / len(rolling_vol)
            
            # Detect volatility clustering (autocorrelation in squared returns)
            squared_returns = returns ** 2
            recent_squared = squared_returns.tail(window)
            if len(recent_squared) >= 2:
                clustering_detected = recent_squared.autocorr(lag=1) > 0.3
            else:
                clustering_detected = False
            
            # Classify regime
            if current_vol > avg_vol * 1.5:
                regime = 'high'
            elif current_vol < avg_vol * 0.7:
                regime = 'low'
            else:
                regime = 'normal'
            
            return {
                'current_volatility': float(current_vol),
                'avg_volatility': float(avg_vol),
                'volatility_regime': regime,
                'volatility_percentile': float(volatility_percentile),
                'clustering_detected': clustering_detected,
                'volatility_ratio': float(current_vol / avg_vol) if avg_vol > 0 else 1.0
            }
            
        except Exception as e:
            return {
                'current_volatility': 0.0,
                'avg_volatility': 0.0,
                'volatility_regime': 'normal',
                'volatility_percentile': 0.5,
                'clustering_detected': False
            }
    
    @staticmethod
    def get_latest_indicators(df: pd.DataFrame) -> Dict:
        """Get the latest indicator values"""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        return {
            'close': latest['close'],
            'sma_20': latest['sma_20'],
            'sma_50': latest['sma_50'],
            'ema_12': latest['ema_12'],
            'ema_26': latest['ema_26'],
            'macd': latest['macd'],
            'macd_signal': latest['macd_signal'],
            'macd_diff': latest['macd_diff'],
            'rsi': latest['rsi'],
            'rsi_prev': prev['rsi'],  # For RSI momentum calculation
            'stoch_k': latest['stoch_k'],
            'stoch_d': latest['stoch_d'],
            'bb_high': latest['bb_high'],
            'bb_mid': latest['bb_mid'],
            'bb_low': latest['bb_low'],
            'bb_width': latest['bb_width'],
            'atr': latest['atr'],
            'volume_ratio': latest['volume_ratio'],
            'momentum': latest['momentum'],
            'roc': latest['roc'],
            'vwap': latest['vwap'] if 'vwap' in latest else latest['close']
        }
