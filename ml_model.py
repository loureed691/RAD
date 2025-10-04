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
        
        # Prediction cache to avoid redundant predictions (optimization)
        self._prediction_cache = {}
        self._cache_max_age = 300  # 5 minutes
        
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
        """Prepare enhanced feature vector from indicators with derived features (optimized)"""
        # Extract base indicators with defaults (vectorized access)
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
        close = indicators.get('close', 0)
        bb_high = indicators.get('bb_high', close)
        bb_low = indicators.get('bb_low', close)
        ema_12 = indicators.get('ema_12', close)
        ema_26 = indicators.get('ema_26', close)
        
        # Pre-compute commonly used values to avoid redundant calculations
        rsi_centered = rsi - 50
        abs_rsi_centered = abs(rsi_centered)
        abs_macd_diff = abs(macd_diff)
        abs_momentum = abs(momentum)
        stoch_diff = stoch_k - stoch_d
        bb_range = bb_high - bb_low
        
        # Vectorized feature computation for performance
        # Use numpy operations where possible to leverage CPU vectorization
        features = np.array([
            # Base indicators (11 features)
            rsi, macd, macd_signal, macd_diff, stoch_k, stoch_d,
            bb_width, volume_ratio, momentum, roc, atr,
            # Derived features (15 features) - optimized calculations
            abs_rsi_centered / 50,  # Normalized RSI strength
            abs_macd_diff,  # MACD momentum strength
            abs(stoch_diff) / 100 if stoch_diff else 0,  # Stochastic momentum
            max(0, volume_ratio - 1),  # Volume surge
            min(bb_width * 10, 1),  # Normalized volatility
            float(rsi < 30 or rsi > 70),  # RSI extreme zones (binary)
            float(macd > macd_signal),  # MACD bullish (binary)
            float(abs_momentum > 0.02),  # Strong momentum (binary)
            (close - bb_low) / bb_range if bb_range > 0 else 0.5,  # BB position
            (close - ema_12) / ema_12 if ema_12 > 0 else 0,  # Distance to EMA12
            (close - ema_26) / ema_26 if ema_26 > 0 else 0,  # Distance to EMA26
            (ema_12 - ema_26) / ema_26 if ema_26 > 0 else 0,  # EMA separation
            indicators.get('rsi_prev', rsi) - rsi,  # RSI momentum
            np.sign(volume_ratio - 1) if abs(volume_ratio - 1) > 0.2 else 0,  # Volume trend
            np.sign(bb_width - 0.035) if abs(bb_width - 0.035) > 0.015 else 0,  # Volatility regime
        ], dtype=np.float32)  # Use float32 for memory efficiency
        
        return features.reshape(1, -1)
    
    def predict(self, indicators: Dict) -> Tuple[str, float]:
        """
        Predict trading signal using ML model with caching for performance
        
        Returns:
            Tuple of (signal, confidence)
            signal: 'BUY', 'SELL', or 'HOLD'
            confidence: probability of the prediction
        """
        if self.model is None:
            return 'HOLD', 0.0
        
        try:
            # Create cache key from critical indicators
            cache_key = (
                round(indicators.get('rsi', 50), 1),
                round(indicators.get('macd', 0), 4),
                round(indicators.get('momentum', 0), 4),
                round(indicators.get('volume_ratio', 1), 2)
            )
            
            # Check cache first for performance boost
            if cache_key in self._prediction_cache:
                cached_result, timestamp = self._prediction_cache[cache_key]
                age = (datetime.now() - timestamp).total_seconds()
                if age < self._cache_max_age:
                    return cached_result
            
            features = self.prepare_features(indicators)
            features_scaled = self.scaler.transform(features)
            
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            confidence = max(probabilities)
            
            signal_map = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
            signal = signal_map.get(prediction, 'HOLD')
            
            result = (signal, confidence)
            
            # Cache the result
            self._prediction_cache[cache_key] = (result, datetime.now())
            
            # Limit cache size to prevent memory bloat
            if len(self._prediction_cache) > 1000:
                # Remove oldest 20% of entries
                sorted_items = sorted(self._prediction_cache.items(), 
                                    key=lambda x: x[1][1])
                for key, _ in sorted_items[:200]:
                    del self._prediction_cache[key]
            
            return result
            
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
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
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
            
            # Clear prediction cache after retraining
            self.clear_cache()
            
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
    
    def clear_cache(self):
        """Clear prediction cache (call after model retraining)"""
        self._prediction_cache.clear()
        self.logger.debug("Prediction cache cleared")

