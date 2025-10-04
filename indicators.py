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
