"""
Machine Learning model for signal optimization
"""
import os
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestClassifier
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
                self.logger.info("Loaded existing ML model")
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
                'training_data': self.training_data[-10000:]  # Keep last 10k records
            }, self.model_path)
            self.logger.info("Saved ML model")
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
    
    def prepare_features(self, indicators: Dict) -> np.array:
        """Prepare feature vector from indicators"""
        features = [
            indicators.get('rsi', 50),
            indicators.get('macd', 0),
            indicators.get('macd_signal', 0),
            indicators.get('macd_diff', 0),
            indicators.get('stoch_k', 50),
            indicators.get('stoch_d', 50),
            indicators.get('bb_width', 0),
            indicators.get('volume_ratio', 1),
            indicators.get('momentum', 0),
            indicators.get('roc', 0),
            indicators.get('atr', 0),
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
        # Determine label based on outcome
        if profit_loss > 0.01:  # Profitable trade
            label = 1 if signal == 'BUY' else 2
        elif profit_loss < -0.01:  # Losing trade
            label = 2 if signal == 'BUY' else 1
        else:  # Neutral
            label = 0
        
        features = self.prepare_features(indicators).flatten().tolist()
        
        self.training_data.append({
            'features': features,
            'label': label,
            'timestamp': datetime.now().isoformat()
        })
        
        self.logger.debug(f"Recorded outcome: signal={signal}, P/L={profit_loss:.4f}, label={label}")
    
    def train(self, min_samples: int = 100):
        """Train or retrain the model with collected data"""
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
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            self.logger.info(f"Model trained - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
            
            # Save model
            self.save_model()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training model: {e}")
            return False
