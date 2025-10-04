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
        if not ohlcv_data or len(ohlcv_data) < 50:
            return pd.DataFrame()
        
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
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Price momentum
        df['momentum'] = df['close'].pct_change(periods=10)
        df['roc'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
        
        return df
    
    @staticmethod
    def get_latest_indicators(df: pd.DataFrame) -> Dict:
        """Get the latest indicator values"""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
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
            'stoch_k': latest['stoch_k'],
            'stoch_d': latest['stoch_d'],
            'bb_high': latest['bb_high'],
            'bb_mid': latest['bb_mid'],
            'bb_low': latest['bb_low'],
            'bb_width': latest['bb_width'],
            'atr': latest['atr'],
            'volume_ratio': latest['volume_ratio'],
            'momentum': latest['momentum'],
            'roc': latest['roc']
        }
