"""
Machine Learning model for signal optimization
"""
import os
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from logger import Logger

class MLModel:
    """Self-learning ML model for optimizing trading signals"""
    
    def __init__(self, model_path: str = 'models/signal_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.logger = Logger.get_logger()
        self.training_data = []
        self.feature_importance = {}
        self.performance_metrics = {
            'win_rate': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'total_trades': 0,
            'wins': 0,
            'losses': 0
        }
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Load existing model if available
        self.load_model()
    
    def load_model(self):
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                saved_data = joblib.load(self.model_path)
                self.model = saved_data['model']
                self.scaler = saved_data['scaler']
                self.training_data = saved_data.get('training_data', [])
                self.feature_importance = saved_data.get('feature_importance', {})
                self.performance_metrics = saved_data.get('performance_metrics', {
                    'win_rate': 0.0,
                    'avg_profit': 0.0,
                    'total_trades': 0
                })
                self.logger.info(f"Loaded existing ML model - Win rate: {self.performance_metrics.get('win_rate', 0):.2%}, Trades: {self.performance_metrics.get('total_trades', 0)}")
            else:
                self.logger.info("No existing model found, will train new model")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
    
    def save_model(self):
        """Save trained model to disk"""
        try:
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'training_data': self.training_data[-10000:],  # Keep last 10k records
                'feature_importance': self.feature_importance,
                'performance_metrics': self.performance_metrics
            }, self.model_path)
            self.logger.info(f"Saved ML model - Win rate: {self.performance_metrics.get('win_rate', 0):.2%}")
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
    
    def prepare_features(self, indicators: Dict) -> np.array:
        """Prepare enhanced feature vector from indicators with derived features"""
        # Base technical indicators
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_diff = indicators.get('macd_diff', 0)
        stoch_k = indicators.get('stoch_k', 50)
        stoch_d = indicators.get('stoch_d', 50)
        bb_width = indicators.get('bb_width', 0)
        volume_ratio = indicators.get('volume_ratio', 1)
        momentum = indicators.get('momentum', 0)
        roc = indicators.get('roc', 0)
        atr = indicators.get('atr', 0)
        
        # Additional advanced indicators
        close = indicators.get('close', 0)
        bb_high = indicators.get('bb_high', close)
        bb_low = indicators.get('bb_low', close)
        bb_mid = indicators.get('bb_mid', close)
        ema_12 = indicators.get('ema_12', close)
        ema_26 = indicators.get('ema_26', close)
        
        # Derived features for better signal quality
        features = [
            rsi,
            macd,
            macd_signal,
            macd_diff,
            stoch_k,
            stoch_d,
            bb_width,
            volume_ratio,
            momentum,
            roc,
            atr,
            # Normalized RSI strength (0-1 scale)
            abs(rsi - 50) / 50,
            # MACD momentum strength
            abs(macd_diff) if macd_diff else 0,
            # Stochastic momentum
            abs(stoch_k - stoch_d) / 100 if stoch_k and stoch_d else 0,
            # Volume surge indicator
            max(0, volume_ratio - 1),
            # Volatility normalized
            min(bb_width * 10, 1) if bb_width else 0,
            # RSI oversold/overbought zones
            1 if rsi < 30 else (1 if rsi > 70 else 0),
            # MACD bullish/bearish
            1 if macd > macd_signal else 0,
            # Strong momentum flag
            1 if abs(momentum) > 0.02 else 0,
            # NEW: Price position in BB (0-1, 0.5 = middle)
            (close - bb_low) / (bb_high - bb_low) if (bb_high - bb_low) > 0 else 0.5,
            # NEW: Distance from EMA (trend strength)
            (close - ema_12) / ema_12 if ema_12 > 0 else 0,
            (close - ema_26) / ema_26 if ema_26 > 0 else 0,
            # NEW: EMA separation (trend divergence)
            (ema_12 - ema_26) / ema_26 if ema_26 > 0 else 0,
            # NEW: RSI momentum (rate of change)
            indicators.get('rsi_prev', rsi) - rsi if 'rsi_prev' in indicators else 0,
            # NEW: Volume trend
            1 if volume_ratio > 1.2 else (-1 if volume_ratio < 0.8 else 0),
            # NEW: Volatility regime
            1 if bb_width > 0.05 else (-1 if bb_width < 0.02 else 0),
        ]
        return np.array(features).reshape(1, -1)
    
    def predict(self, indicators: Dict) -> Tuple[str, float]:
        """
        Predict trading signal using ML model
        
        Returns:
            Tuple of (signal, confidence)
            signal: 'BUY', 'SELL', or 'HOLD'
            confidence: probability of the prediction
        """
        if self.model is None:
            return 'HOLD', 0.0
        
        try:
            features = self.prepare_features(indicators)
            features_scaled = self.scaler.transform(features)
            
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            confidence = max(probabilities)
            
            signal_map = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
            signal = signal_map.get(prediction, 'HOLD')
            
            return signal, confidence
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {e}")
            return 'HOLD', 0.0
    
    def record_outcome(self, indicators: Dict, signal: str, profit_loss: float):
        """
        Record trading outcome for future training
        
        Args:
            indicators: Dict of technical indicators
            signal: The signal that was generated ('BUY' or 'SELL')
            profit_loss: The profit or loss from the trade (percentage)
        """
        # Determine label based on outcome with refined thresholds
        if profit_loss > 0.005:  # Profitable trade (>0.5%)
            label = 1 if signal == 'BUY' else 2
        elif profit_loss < -0.005:  # Losing trade (<-0.5%)
            label = 2 if signal == 'BUY' else 1
        else:  # Neutral (close to breakeven)
            label = 0
        
        features = self.prepare_features(indicators).flatten().tolist()
        
        self.training_data.append({
            'features': features,
            'label': label,
            'timestamp': datetime.now().isoformat(),
            'profit_loss': profit_loss
        })
        
        # Limit training data to prevent memory leak - keep only last 10,000 records
        if len(self.training_data) > 10000:
            self.training_data = self.training_data[-10000:]
        
        # Update performance metrics
        self.performance_metrics['total_trades'] = self.performance_metrics.get('total_trades', 0) + 1
        total = self.performance_metrics['total_trades']
        
        # Track wins and losses separately for better Kelly Criterion
        if profit_loss > 0.005:  # Profitable trade (>0.5%)
            wins = self.performance_metrics.get('wins', 0) + 1
            self.performance_metrics['wins'] = wins
            self.performance_metrics['win_rate'] = wins / total
            
            # Update average profit (only winning trades)
            avg_profit = self.performance_metrics.get('avg_profit', 0)
            self.performance_metrics['avg_profit'] = ((avg_profit * (wins - 1)) + profit_loss) / wins
            
        elif profit_loss < -0.005:  # Losing trade (<-0.5%)
            losses = self.performance_metrics.get('losses', 0) + 1
            self.performance_metrics['losses'] = losses
            
            # Update average loss (only losing trades, as positive number)
            avg_loss = self.performance_metrics.get('avg_loss', 0)
            self.performance_metrics['avg_loss'] = ((avg_loss * (losses - 1)) + abs(profit_loss)) / losses
        
        self.logger.debug(f"Recorded outcome: signal={signal}, P/L={profit_loss:.4f}, label={label}, Win rate: {self.performance_metrics.get('win_rate', 0):.2%}")
    
    def train(self, min_samples: int = 100):
        """Train or retrain the model with collected data using optimized hyperparameters"""
        if len(self.training_data) < min_samples:
            self.logger.info(f"Not enough training data ({len(self.training_data)}/{min_samples})")
            return False
        
        try:
            self.logger.info(f"Training model with {len(self.training_data)} samples...")
            
            # Prepare data
            X = np.array([d['features'] for d in self.training_data])
            y = np.array([d['label'] for d in self.training_data])
            
            # Split data
            # Only use stratification if we have enough samples of each class
            unique_classes, class_counts = np.unique(y, return_counts=True)
            use_stratify = len(unique_classes) > 1 and all(count >= 2 for count in class_counts)
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if use_stratify else None
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model with optimized hyperparameters
            # Use GradientBoosting for better performance on imbalanced data
            self.model = GradientBoostingClassifier(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                min_samples_split=5,
                min_samples_leaf=2,
                subsample=0.8,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            # Get feature importance
            if hasattr(self.model, 'feature_importances_'):
                feature_names = [
                    'rsi', 'macd', 'macd_signal', 'macd_diff', 'stoch_k', 'stoch_d',
                    'bb_width', 'volume_ratio', 'momentum', 'roc', 'atr',
                    'rsi_strength', 'macd_strength', 'stoch_momentum', 'volume_surge',
                    'volatility_norm', 'rsi_zone', 'macd_bullish', 'momentum_flag',
                    'bb_position', 'price_to_ema12', 'price_to_ema26', 'ema_separation',
                    'rsi_momentum', 'volume_trend', 'volatility_regime'
                ]
                importances = self.model.feature_importances_
                self.feature_importance = {name: float(imp) for name, imp in zip(feature_names, importances)}
                
                # Log top 5 features
                top_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
                self.logger.info(f"Top features: {', '.join([f'{k}:{v:.3f}' for k, v in top_features])}")
            
            self.logger.info(f"Model trained - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
            
            # Save model
            self.save_model()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return False
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def get_adaptive_confidence_threshold(self) -> float:
        """
        Calculate adaptive confidence threshold based on model performance
        
        Returns:
            Adjusted confidence threshold (0.5-0.75)
        """
        base_threshold = 0.6
        
        # Adjust based on win rate
        win_rate = self.performance_metrics.get('win_rate', 0.5)
        if win_rate > 0.6:
            # If winning more, can be slightly more aggressive
            return max(0.55, base_threshold - 0.05)
        elif win_rate < 0.4:
            # If losing more, be more conservative
            return min(0.75, base_threshold + 0.1)
        
        return base_threshold
    
    def train_with_historical_data(self, historical_data: pd.DataFrame, signal_generator=None, min_samples: int = 100):
        """
        Train the model with historical OHLCV data
        
        Args:
            historical_data: DataFrame with OHLCV data (columns: timestamp, open, high, low, close, volume)
            signal_generator: Optional SignalGenerator instance to generate labels. If None, uses simple price-based labels
            min_samples: Minimum number of samples required for training
            
        Returns:
            bool: True if training was successful, False otherwise
        """
        try:
            from indicators import Indicators
            
            self.logger.info(f"Processing {len(historical_data)} candles of historical data for training...")
            
            # Ensure we have enough data
            if len(historical_data) < 100:
                self.logger.warning(f"Not enough historical data ({len(historical_data)} candles), need at least 100")
                return False
            
            # Convert to proper format if needed
            if isinstance(historical_data, list):
                historical_data = pd.DataFrame(
                    historical_data,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
            
            # Calculate all indicators for the historical data
            df = Indicators.calculate_all(historical_data)
            if df.empty or len(df) < 50:
                self.logger.error("Failed to calculate indicators from historical data")
                return False
            
            self.logger.info(f"Calculated indicators for {len(df)} candles")
            
            # Generate training samples from historical data
            training_samples = []
            
            # Use a rolling window approach to create samples
            for i in range(50, len(df) - 1):  # Start at 50 to have enough history, leave 1 for future
                current_row = df.iloc[i]
                future_row = df.iloc[i + 1]
                
                # Prepare indicators for this point in time
                indicators = {
                    'rsi': current_row.get('rsi', 50),
                    'macd': current_row.get('macd', 0),
                    'macd_signal': current_row.get('macd_signal', 0),
                    'macd_diff': current_row.get('macd_diff', 0),
                    'stoch_k': current_row.get('stoch_k', 50),
                    'stoch_d': current_row.get('stoch_d', 50),
                    'bb_width': current_row.get('bb_width', 0),
                    'volume_ratio': current_row.get('volume_ratio', 1),
                    'momentum': current_row.get('momentum', 0),
                    'roc': current_row.get('roc', 0),
                    'atr': current_row.get('atr', 0),
                    'close': current_row.get('close', 0),
                    'bb_high': current_row.get('bb_high', current_row.get('close', 0)),
                    'bb_low': current_row.get('bb_low', current_row.get('close', 0)),
                    'bb_mid': current_row.get('bb_mid', current_row.get('close', 0)),
                    'ema_12': current_row.get('ema_12', current_row.get('close', 0)),
                    'ema_26': current_row.get('ema_26', current_row.get('close', 0)),
                }
                
                # Calculate profit/loss based on next candle
                current_price = current_row.get('close', 0)
                future_price = future_row.get('close', 0)
                
                if current_price <= 0 or future_price <= 0:
                    continue
                
                price_change = (future_price - current_price) / current_price
                
                # Determine label based on price movement
                # Label 1 = BUY (price went up), Label 2 = SELL (price went down), Label 0 = HOLD (neutral)
                if price_change > 0.005:  # Price increased >0.5%
                    label = 1  # BUY would have been profitable
                elif price_change < -0.005:  # Price decreased >0.5%
                    label = 2  # SELL would have been profitable
                else:
                    label = 0  # HOLD (neutral movement)
                
                # Prepare features
                features = self.prepare_features(indicators).flatten().tolist()
                
                training_samples.append({
                    'features': features,
                    'label': label,
                    'timestamp': current_row.get('timestamp', ''),
                    'profit_loss': price_change
                })
            
            self.logger.info(f"Generated {len(training_samples)} training samples from historical data")
            
            if len(training_samples) < min_samples:
                self.logger.warning(f"Not enough training samples generated ({len(training_samples)}/{min_samples})")
                return False
            
            # Add to training data (respecting the 10k limit)
            self.training_data.extend(training_samples)
            if len(self.training_data) > 10000:
                self.training_data = self.training_data[-10000:]
            
            self.logger.info(f"Total training data now: {len(self.training_data)} samples")
            
            # Train the model with the accumulated data
            return self.train(min_samples=min_samples)
            
        except Exception as e:
            self.logger.error(f"Error training with historical data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_historical_data_from_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load historical OHLCV data from a CSV file
        
        Args:
            csv_path: Path to the CSV file containing historical data
            
        Returns:
            DataFrame with historical data or empty DataFrame on error
        """
        try:
            self.logger.info(f"Loading historical data from {csv_path}...")
            
            # Try to read the CSV
            df = pd.read_csv(csv_path)
            
            # Verify required columns exist
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            # Check if columns exist (case-insensitive)
            df.columns = [col.lower() for col in df.columns]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"CSV missing required columns: {missing_columns}")
                return pd.DataFrame()
            
            self.logger.info(f"Loaded {len(df)} candles from CSV")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading historical data from CSV: {e}")
            return pd.DataFrame()
