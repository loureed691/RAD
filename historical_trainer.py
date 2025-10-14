"""
Historical Data Trainer for ML Model
Fetches historical data from KuCoin and generates training samples
"""
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from logger import Logger
from indicators import Indicators


class HistoricalTrainer:
    """Train ML model with historical data from KuCoin"""
    
    def __init__(self, client, ml_model):
        """
        Initialize historical trainer
        
        Args:
            client: KuCoinClient instance
            ml_model: MLModel instance to train
        """
        self.client = client
        self.ml_model = ml_model
        self.logger = Logger.get_logger()
    
    def fetch_historical_data(self, symbol: str, timeframe: str = '1h', 
                             days: int = 30) -> Optional[List]:
        """
        Fetch historical OHLCV data for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT:USDT')
            timeframe: Candle timeframe (e.g., '1h', '4h', '1d')
            days: Number of days to fetch
            
        Returns:
            List of OHLCV candles or None if error
        """
        try:
            # Calculate limit based on timeframe and days
            timeframe_minutes = {
                '1m': 1, '5m': 5, '15m': 15, '30m': 30,
                '1h': 60, '4h': 240, '1d': 1440
            }
            minutes = timeframe_minutes.get(timeframe, 60)
            limit = min((days * 24 * 60) // minutes, 1500)  # KuCoin max is typically 1500
            
            self.logger.info(f"Fetching {limit} candles of {symbol} ({timeframe}) for training...")
            
            ohlcv = self.client.get_ohlcv(symbol, timeframe, limit)
            
            if not ohlcv or len(ohlcv) < 50:
                self.logger.warning(f"Insufficient data for {symbol}: got {len(ohlcv) if ohlcv else 0} candles")
                return None
            
            self.logger.info(f"✓ Fetched {len(ohlcv)} candles for {symbol}")
            return ohlcv
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def generate_training_samples(self, ohlcv_data: List, symbol: str) -> int:
        """
        Generate training samples from historical OHLCV data
        
        Strategy:
        - Calculate indicators for each candle
        - Look ahead to see if price went up or down significantly
        - Label as BUY if price increased, SELL if decreased, HOLD if neutral
        - Record synthetic outcomes for model training
        
        Args:
            ohlcv_data: List of OHLCV candles
            symbol: Trading pair symbol
            
        Returns:
            Number of training samples generated
        """
        try:
            # Calculate indicators
            df = Indicators.calculate_all(ohlcv_data)
            
            if df.empty or len(df) < 50:
                self.logger.warning(f"Insufficient indicator data for {symbol}")
                return 0
            
            samples_generated = 0
            lookforward = 5  # Look 5 candles ahead to determine outcome
            
            # Iterate through data, leaving room for look-forward
            for i in range(len(df) - lookforward - 1):
                try:
                    current_row = df.iloc[i]
                    future_row = df.iloc[i + lookforward]
                    
                    # Skip if any critical data is missing
                    if pd.isna(current_row['close']) or pd.isna(future_row['close']):
                        continue
                    
                    current_price = float(current_row['close'])
                    future_price = float(future_row['close'])
                    
                    if current_price == 0:
                        continue
                    
                    # Calculate price change
                    price_change = (future_price - current_price) / current_price
                    
                    # Extract indicators for this candle
                    indicators = Indicators.get_latest_indicators(df.iloc[i:i+1])
                    
                    if not indicators or 'close' not in indicators:
                        continue
                    
                    # Determine signal based on which direction would have been profitable
                    # If price went up, a BUY signal would have been correct
                    # If price went down, a SELL signal would have been correct
                    if price_change > 0.01:  # Price increased > 1%
                        signal = 'BUY'
                        profit_loss = price_change
                    elif price_change < -0.01:  # Price decreased > 1%
                        signal = 'SELL'
                        profit_loss = abs(price_change)
                    else:
                        # Neutral movement - skip or record as neutral
                        signal = 'HOLD'
                        profit_loss = 0.0
                    
                    # Only record non-HOLD signals for training
                    if signal != 'HOLD':
                        self.ml_model.record_outcome(indicators, signal, profit_loss)
                        samples_generated += 1
                    
                except Exception as e:
                    # Skip individual candles with errors
                    continue
            
            return samples_generated
            
        except Exception as e:
            self.logger.error(f"Error generating training samples for {symbol}: {e}")
            return 0
    
    def train_from_history(self, symbols: List[str], timeframe: str = '1h', 
                          days: int = 30, min_samples: int = 100) -> bool:
        """
        Train ML model using historical data from multiple symbols
        
        Args:
            symbols: List of trading pairs
            timeframe: Candle timeframe
            days: Number of days of history
            min_samples: Minimum samples before training
            
        Returns:
            True if training successful, False otherwise
        """
        self.logger.info("=" * 60)
        self.logger.info("🎓 STARTING HISTORICAL TRAINING")
        self.logger.info("=" * 60)
        self.logger.info(f"Symbols: {len(symbols)}")
        self.logger.info(f"Timeframe: {timeframe}")
        self.logger.info(f"History: {days} days")
        self.logger.info(f"Min samples: {min_samples}")
        self.logger.info("=" * 60)
        
        total_samples = 0
        
        for symbol in symbols:
            try:
                self.logger.info(f"Processing {symbol}...")
                
                # Fetch historical data
                ohlcv = self.fetch_historical_data(symbol, timeframe, days)
                
                if not ohlcv:
                    self.logger.warning(f"Skipping {symbol} - no data available")
                    continue
                
                # Generate training samples
                samples = self.generate_training_samples(ohlcv, symbol)
                total_samples += samples
                
                self.logger.info(f"✓ Generated {samples} training samples from {symbol}")
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error processing {symbol}: {e}")
                continue
        
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Total training samples generated: {total_samples}")
        self.logger.info("=" * 60)
        
        # Train the model if we have enough samples
        if total_samples >= min_samples:
            self.logger.info("🤖 Training ML model with historical data...")
            success = self.ml_model.train(min_samples=min_samples)
            
            if success:
                self.logger.info("✅ Historical training completed successfully!")
                self.ml_model.save_model()
                self.logger.info("💾 Model saved to disk")
                return True
            else:
                self.logger.warning("⚠️  Model training did not complete")
                return False
        else:
            self.logger.warning(
                f"⚠️  Not enough samples for training "
                f"(got {total_samples}, need {min_samples})"
            )
            return False
