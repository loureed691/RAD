"""
Technical indicators for trading signals
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from functools import lru_cache
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange

class Indicators:
    """Calculate technical indicators for trading"""
    
    # Class-level cache for indicator calculations
    _indicator_cache = {}
    _cache_max_size = 100
    
    @staticmethod
    def calculate_all(ohlcv_data: List) -> pd.DataFrame:
        """
        Calculate all technical indicators from OHLCV data
        
        Args:
            ohlcv_data: List of [timestamp, open, high, low, close, volume] or DataFrame
        
        Returns:
            DataFrame with all indicators
        """
        # Handle empty data
        if ohlcv_data is None:
            return pd.DataFrame()
        
        # If it's a DataFrame, use it directly
        if isinstance(ohlcv_data, pd.DataFrame):
            df = ohlcv_data.copy()
            # Ensure timestamp column exists and is datetime
            if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce')
        else:
            # Handle list input
            if len(ohlcv_data) == 0:
                return pd.DataFrame()
            
            if len(ohlcv_data) < 50:
                # Return empty DataFrame - caller should check for this
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Check minimum data requirement
        if len(df) < 50:
            return pd.DataFrame()
        
        try:
            # OPTIMIZATION: Vectorized calculations where possible
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            volume = df['volume'].values
            
            # Moving Averages (optimized with pandas ewm/rolling)
            df['sma_20'] = df['close'].rolling(window=20, min_periods=20).mean()
            df['sma_50'] = df['close'].rolling(window=50, min_periods=50).mean()
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            
            # MACD (optimized)
            ema_fast = df['close'].ewm(span=12, adjust=False).mean()
            ema_slow = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema_fast - ema_slow
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_diff'] = df['macd'] - df['macd_signal']
            
            # RSI (optimized vectorized calculation)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss.replace(0, np.nan)
            df['rsi'] = 100 - (100 / (1 + rs))
            df['rsi'] = df['rsi'].fillna(50)  # Neutral when no data
            
            # Stochastic Oscillator
            stoch = StochasticOscillator(df['high'], df['low'], df['close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # Handle NaN values (occurs when high == low for all periods in window)
            # Default to neutral 50 when stochastic can't be calculated
            df['stoch_k'] = df['stoch_k'].fillna(50.0)
            df['stoch_d'] = df['stoch_d'].fillna(50.0)
            
            # Bollinger Bands (optimized)
            bb_mid = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_high'] = bb_mid + (bb_std * 2)
            df['bb_mid'] = bb_mid
            df['bb_low'] = bb_mid - (bb_std * 2)
            df['bb_width'] = (df['bb_high'] - df['bb_low']) / df['bb_mid'].replace(0, np.nan)
            df['bb_width'] = df['bb_width'].replace([np.inf, -np.inf], np.nan).fillna(0.03)
            
            # ATR (Average True Range)
            df['atr'] = AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            
            # Volume indicators (optimized)
            df['volume_sma'] = df['volume'].rolling(window=20, min_periods=1).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma'].replace(0, np.nan)
            df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
            
            # Price momentum (optimized)
            df['momentum'] = df['close'].pct_change(periods=10)
            df['roc'] = df['momentum'] * 100  # Same calculation, optimized
            
            # Volume-weighted indicators (VWAP optimized)
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            tp_volume = typical_price * df['volume']
            df['vwap'] = tp_volume.rolling(window=50, min_periods=1).sum() / df['volume'].rolling(window=50, min_periods=1).sum()
            
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
            # OPTIMIZATION: Fully vectorized calculation replacing O(n*m) nested loops with O(n) vectorized ops
            volume_profile = np.zeros(num_bins - 1)
            
            # Extract arrays for vectorized operations
            candle_lows = recent_df['low'].values
            candle_highs = recent_df['high'].values
            candle_volumes = recent_df['volume'].values
            
            # Vectorized bin assignment for each candle
            for i in range(num_bins - 1):
                bin_low = bins[i]
                bin_high = bins[i + 1]
                
                # Vectorized overlap calculation
                # Check which candles intersect with this bin
                intersects = (candle_highs >= bin_low) & (candle_lows <= bin_high)
                
                # Calculate overlap for intersecting candles
                overlap_lows = np.maximum(candle_lows, bin_low)
                overlap_highs = np.minimum(candle_highs, bin_high)
                candle_ranges = np.maximum(candle_highs - candle_lows, 1e-10)  # Avoid division by zero
                overlap_ratios = (overlap_highs - overlap_lows) / candle_ranges
                
                # Sum volumes with overlap ratios, only for intersecting candles
                volume_profile[i] = np.sum(candle_volumes * overlap_ratios * intersects)
            
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
