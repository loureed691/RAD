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
        self.ensemble_models = []  # For ensemble learning
        self.scaler = StandardScaler()
        self.logger = Logger.get_logger()
        self.training_data = []
        self.feature_importance = {}
        self.mistake_log = []  # Track mistakes for adaptive learning
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
                self.ensemble_models = saved_data.get('ensemble_models', [])
                self.scaler = saved_data['scaler']
                self.training_data = saved_data.get('training_data', [])
                self.feature_importance = saved_data.get('feature_importance', {})
                self.mistake_log = saved_data.get('mistake_log', [])
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
                'ensemble_models': self.ensemble_models,
                'scaler': self.scaler,
                'training_data': self.training_data[-10000:],  # Keep last 10k records
                'feature_importance': self.feature_importance,
                'mistake_log': self.mistake_log[-1000:],  # Keep last 1k mistakes
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
        Predict trading signal using ensemble ML models for better accuracy
        
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
            
            # Use ensemble if available
            if self.ensemble_models:
                # Get predictions from all models
                predictions = []
                confidences = []
                
                for model in [self.model] + self.ensemble_models:
                    pred = model.predict(features_scaled)[0]
                    proba = model.predict_proba(features_scaled)[0]
                    predictions.append(pred)
                    confidences.append(max(proba))
                
                # Majority voting for prediction
                prediction = max(set(predictions), key=predictions.count)
                # Average confidence across models
                confidence = sum(confidences) / len(confidences)
            else:
                # Single model prediction
                prediction = self.model.predict(features_scaled)[0]
                probabilities = self.model.predict_proba(features_scaled)[0]
                confidence = max(probabilities)
            
            # Check for similar past mistakes to adjust confidence
            mistake_penalty = self._check_mistake_log(features.flatten())
            confidence = confidence * (1.0 - mistake_penalty)
            
            # Convert to signal
            if prediction == 1:
                signal = 'BUY'
            elif prediction == 2:
                signal = 'SELL'
            else:
                signal = 'HOLD'
            
            return signal, confidence
            
        except Exception as e:
            self.logger.error(f"Error predicting: {e}")
            return 'HOLD', 0.0
    
    def record_outcome(self, indicators: Dict, signal: str, profit_loss: float):
        """
        Record trade outcome for model improvement with mistake tracking
        
        Args:
            indicators: Technical indicators at time of trade
            signal: 'BUY' or 'SELL'
            profit_loss: Profit/loss as percentage (0.05 = 5%)
        """
        # Determine label based on outcome with refined thresholds
        if profit_loss > 0.005:  # Profitable trade (>0.5%)
            label = 1 if signal == 'BUY' else 2
        elif profit_loss < -0.005:  # Losing trade (<-0.5%)
            label = 2 if signal == 'BUY' else 1
            # Log mistake for adaptive learning
            self._log_mistake(indicators, signal, profit_loss)
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
    
    def _log_mistake(self, indicators: Dict, signal: str, profit_loss: float):
        """Log a trading mistake for adaptive learning with time decay"""
        features = self.prepare_features(indicators).flatten().tolist()
        self.mistake_log.append({
            'features': features,
            'signal': signal,
            'profit_loss': profit_loss,
            'timestamp': datetime.now().isoformat()
        })
        self.logger.debug(f"Logged mistake: {signal} with loss {profit_loss:.4f}")
    
    def _check_mistake_log(self, current_features: np.array, similarity_threshold: float = 0.95) -> float:
        """
        Check if current features are similar to past mistakes
        Returns a confidence penalty (0.0 to 0.5) based on similarity and recency
        """
        if not self.mistake_log:
            return 0.0
        
        try:
            from datetime import timedelta
            
            max_penalty = 0.0
            current_time = datetime.now()
            
            for mistake in self.mistake_log[-100:]:  # Check last 100 mistakes
                # Calculate feature similarity (cosine similarity)
                mistake_features = np.array(mistake['features'])
                
                # Normalize vectors
                norm_current = np.linalg.norm(current_features)
                norm_mistake = np.linalg.norm(mistake_features)
                
                if norm_current == 0 or norm_mistake == 0:
                    continue
                
                similarity = np.dot(current_features, mistake_features) / (norm_current * norm_mistake)
                
                if similarity > similarity_threshold:
                    # Calculate time decay (mistakes older than 30 days have reduced impact)
                    mistake_time = datetime.fromisoformat(mistake['timestamp'])
                    days_ago = (current_time - mistake_time).days
                    time_decay = max(0.0, 1.0 - (days_ago / 30.0))
                    
                    # Penalty based on similarity and loss magnitude
                    loss_magnitude = min(abs(mistake['profit_loss']), 0.1) / 0.1
                    penalty = (similarity - similarity_threshold) / (1.0 - similarity_threshold) * 0.5 * loss_magnitude * time_decay
                    max_penalty = max(max_penalty, penalty)
            
            return min(max_penalty, 0.5)  # Cap at 50% confidence penalty
            
        except Exception as e:
            self.logger.error(f"Error checking mistake log: {e}")
            return 0.0
    
    def train(self, min_samples: int = 100):
        """Train or retrain the model with ensemble learning for better accuracy"""
        if len(self.training_data) < min_samples:
            self.logger.info(f"Not enough training data ({len(self.training_data)}/{min_samples})")
            return False
        
        try:
            self.logger.info(f"Training ensemble model with {len(self.training_data)} samples...")
            
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
            
            # Train primary model with optimized hyperparameters
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
            
            # Train ensemble models for better predictions
            self.ensemble_models = []
            
            # Add Random Forest for diversity
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
            rf_model.fit(X_train_scaled, y_train)
            self.ensemble_models.append(rf_model)
            
            # Add another Gradient Boosting with different params
            gb2_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                min_samples_split=10,
                subsample=0.9,
                random_state=43
            )
            gb2_model.fit(X_train_scaled, y_train)
            self.ensemble_models.append(gb2_model)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            # Evaluate ensemble
            ensemble_test_score = self._evaluate_ensemble(X_test_scaled, y_test)
            
            self.logger.info(f"Model trained - Primary test: {test_score:.3f}, Ensemble test: {ensemble_test_score:.3f}")
            
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
            
            # Save model
            self.save_model()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return False
    
    def _evaluate_ensemble(self, X_test: np.array, y_test: np.array) -> float:
        """Evaluate ensemble model performance"""
        try:
            predictions = []
            for model in [self.model] + self.ensemble_models:
                pred = model.predict(X_test)
                predictions.append(pred)
            
            # Majority voting
            ensemble_pred = []
            for i in range(len(y_test)):
                votes = [pred[i] for pred in predictions]
                ensemble_pred.append(max(set(votes), key=votes.count))
            
            # Calculate accuracy
            correct = sum(1 for i in range(len(y_test)) if ensemble_pred[i] == y_test[i])
            return correct / len(y_test)
        except:
            return 0.0
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def get_adaptive_confidence_threshold(self) -> float:
        """
        Calculate adaptive confidence threshold based on model performance and recent trends
        
        Returns:
            Adjusted confidence threshold (0.5-0.75)
        """
        base_threshold = 0.6
        
        # Adjust based on win rate
        win_rate = self.performance_metrics.get('win_rate', 0.5)
        total_trades = self.performance_metrics.get('total_trades', 0)
        
        # More sophisticated adaptive logic
        if total_trades >= 50:
            # Check recent performance trend (last 20 trades)
            recent_data = self.training_data[-20:] if len(self.training_data) >= 20 else self.training_data
            recent_wins = sum(1 for d in recent_data if d.get('profit_loss', 0) > 0.005)
            recent_win_rate = recent_wins / len(recent_data) if recent_data else 0.5
            
            # Combine overall and recent performance
            combined_rate = (win_rate * 0.6) + (recent_win_rate * 0.4)
            
            if combined_rate > 0.65:
                # Strong performance, can be more aggressive
                return max(0.52, base_threshold - 0.08)
            elif combined_rate > 0.6:
                # Good performance, slightly more aggressive
                return max(0.55, base_threshold - 0.05)
            elif combined_rate < 0.45:
                # Poor performance, be conservative
                return min(0.72, base_threshold + 0.12)
            elif combined_rate < 0.5:
                # Below average, be more cautious
                return min(0.70, base_threshold + 0.10)
        else:
            # Not enough trades, use simple logic
            if win_rate > 0.6:
                return max(0.55, base_threshold - 0.05)
            elif win_rate < 0.4:
                return min(0.75, base_threshold + 0.1)
        
        return base_threshold

