"""
Incremental/Online Machine Learning model using River library
Supports real-time learning from streaming data without full retraining
"""
import os
import pickle
import numpy as np
from datetime import datetime
from typing import Dict, Tuple
from river import tree, ensemble, linear_model, preprocessing, compose, metrics
from logger import Logger


class IncrementalMLModel:
    """Online/Incremental learning ML model using River for real-time adaptation"""
    
    def __init__(self, model_path: str = 'models/incremental_model.pkl'):
        self.model_path = model_path
        self.logger = Logger.get_logger()
        
        # Initialize River pipeline with preprocessing and ensemble model
        # Use ADWIN Bagging with Hoeffding Tree for adaptive online learning
        self.model = compose.Pipeline(
            preprocessing.StandardScaler(),
            ensemble.ADWINBaggingClassifier(
                model=tree.HoeffdingTreeClassifier(
                    grace_period=50,
                    delta=1e-5,
                    max_depth=10
                ),
                n_models=10,
                seed=42
            )
        )
        
        # Performance tracking metrics
        self.accuracy_metric = metrics.Accuracy()
        self.f1_metric = metrics.F1()
        self.precision_metric = metrics.Precision()
        self.recall_metric = metrics.Recall()
        
        # Performance metrics storage
        self.performance_metrics = {
            'total_trades': 0,
            'win_rate': 0.0,
            'accuracy': 0.0,
            'f1_score': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'wins': 0,
            'losses': 0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'recent_trades': []
        }
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Load existing model if available
        self.load_model()
    
    def load_model(self):
        """Load trained incremental model from disk"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    saved_data = pickle.load(f)
                    self.model = saved_data.get('model', self.model)
                    self.performance_metrics = saved_data.get('performance_metrics', self.performance_metrics)
                    self.accuracy_metric = saved_data.get('accuracy_metric', self.accuracy_metric)
                    self.f1_metric = saved_data.get('f1_metric', self.f1_metric)
                    
                self.logger.info(f"Loaded incremental model - Win rate: {self.performance_metrics.get('win_rate', 0):.2%}, "
                               f"Accuracy: {self.performance_metrics.get('accuracy', 0):.2%}, "
                               f"Trades: {self.performance_metrics.get('total_trades', 0)}")
            else:
                self.logger.info("No existing incremental model found, starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading incremental model: {e}")
            # Reset to default model if loading fails
            self.model = compose.Pipeline(
                preprocessing.StandardScaler(),
                ensemble.ADWINBaggingClassifier(
                    model=tree.HoeffdingTreeClassifier(
                        grace_period=50,
                        delta=1e-5,
                        max_depth=10
                    ),
                    n_models=10,
                    seed=42
                )
            )
    
    def save_model(self):
        """Save incremental model to disk"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'performance_metrics': self.performance_metrics,
                    'accuracy_metric': self.accuracy_metric,
                    'f1_metric': self.f1_metric
                }, f)
            self.logger.info(f"Saved incremental model - Win rate: {self.performance_metrics.get('win_rate', 0):.2%}, "
                           f"Accuracy: {self.performance_metrics.get('accuracy', 0):.2%}")
        except Exception as e:
            self.logger.error(f"Error saving incremental model: {e}")
    
    def prepare_features(self, indicators: Dict) -> Dict:
        """
        Prepare feature dictionary from indicators for River (uses dict format)
        
        Args:
            indicators: Dictionary of technical indicators
            
        Returns:
            Dictionary of features for River model
        """
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
        sma_20 = indicators.get('sma_20', close)
        sma_50 = indicators.get('sma_50', close)
        
        # Calculate derived features
        prev_momentum = indicators.get('momentum_prev', momentum)
        momentum_acceleration = momentum - prev_momentum
        
        # Sentiment score from price action
        sentiment_score = 0
        if close > ema_12:
            sentiment_score += 0.3
        if close > ema_26:
            sentiment_score += 0.2
        if volume_ratio > 1.2:
            sentiment_score += 0.2
        if momentum > 0.01:
            sentiment_score += 0.3
        if close < ema_12:
            sentiment_score -= 0.3
        if close < ema_26:
            sentiment_score -= 0.2
        if volume_ratio < 0.8:
            sentiment_score -= 0.2
        if momentum < -0.01:
            sentiment_score -= 0.3
        
        # River uses dictionaries for features
        features = {
            'rsi': float(rsi),
            'macd': float(macd),
            'macd_signal': float(macd_signal),
            'macd_diff': float(macd_diff),
            'stoch_k': float(stoch_k),
            'stoch_d': float(stoch_d),
            'bb_width': float(bb_width),
            'volume_ratio': float(volume_ratio),
            'momentum': float(momentum),
            'roc': float(roc),
            'atr': float(atr),
            'rsi_strength': float(abs(rsi - 50) / 50),
            'macd_strength': float(abs(macd_diff) if macd_diff else 0),
            'stoch_momentum': float(abs(stoch_k - stoch_d) / 100 if stoch_k and stoch_d else 0),
            'volume_surge': float(max(0, volume_ratio - 1)),
            'volatility_norm': float(min(bb_width * 10, 1) if bb_width else 0),
            'rsi_zone': float(1 if rsi < 30 else (1 if rsi > 70 else 0)),
            'macd_bullish': float(1 if macd > macd_signal else 0),
            'momentum_flag': float(1 if abs(momentum) > 0.02 else 0),
            'bb_position': float((close - bb_low) / (bb_high - bb_low) if (bb_high - bb_low) > 0 else 0.5),
            'price_to_ema12': float((close - ema_12) / ema_12 if ema_12 > 0 else 0),
            'price_to_ema26': float((close - ema_26) / ema_26 if ema_26 > 0 else 0),
            'ema_separation': float((ema_12 - ema_26) / ema_26 if ema_26 > 0 else 0),
            'rsi_momentum': float(indicators.get('rsi_prev', rsi) - rsi if 'rsi_prev' in indicators else 0),
            'volume_trend': float(1 if volume_ratio > 1.2 else (-1 if volume_ratio < 0.8 else 0)),
            'volatility_regime': float(1 if bb_width > 0.05 else (-1 if bb_width < 0.02 else 0)),
            'sentiment_score': float(sentiment_score),
            'momentum_accel': float(momentum_acceleration),
            'mtf_trend': float(1 if (close > sma_20 and sma_20 > sma_50) else (-1 if (close < sma_20 and sma_20 < sma_50) else 0)),
            'breakout_potential': float(1 if (close > 0 and abs(close - bb_high) / close < 0.01 and bb_width < 0.03) else 0),
            'mean_reversion': float(1 if (close > 0 and abs(close - bb_mid) / close > 0.03 and bb_width > 0.05) else 0),
        }
        
        return features
    
    def predict(self, indicators: Dict) -> Tuple[str, float]:
        """
        Predict trading signal using incremental model
        
        Args:
            indicators: Dictionary of technical indicators
            
        Returns:
            Tuple of (signal, confidence)
            signal: 'BUY', 'SELL', or 'HOLD'
            confidence: probability of the prediction
        """
        try:
            features = self.prepare_features(indicators)
            
            # Get prediction probabilities from River model
            proba = self.model.predict_proba_one(features)
            
            if not proba:
                return 'HOLD', 0.0
            
            # Get the predicted class and its probability
            predicted_class = max(proba, key=proba.get)
            confidence = proba[predicted_class]
            
            # Map class to signal
            signal_map = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
            signal = signal_map.get(predicted_class, 'HOLD')
            
            return signal, confidence
            
        except Exception as e:
            self.logger.error(f"Error making incremental prediction: {e}")
            return 'HOLD', 0.0
    
    def learn_one(self, indicators: Dict, signal: str, profit_loss: float):
        """
        Incrementally learn from a single trade outcome
        This is the core of online learning - updating model in real-time
        
        Args:
            indicators: Dictionary of technical indicators
            signal: The signal that was generated ('BUY' or 'SELL')
            profit_loss: The profit or loss from the trade (percentage)
        """
        try:
            # Determine label based on outcome
            if profit_loss > 0.005:  # Profitable trade (>0.5%)
                label = 1 if signal == 'BUY' else 2
            elif profit_loss < -0.005:  # Losing trade (<-0.5%)
                label = 2 if signal == 'BUY' else 1
            else:  # Neutral (close to breakeven)
                label = 0
            
            # Prepare features
            features = self.prepare_features(indicators)
            
            # Update the model with this single observation
            # This is the key difference from batch learning - we learn incrementally
            self.model.learn_one(features, label)
            
            # Update metrics
            y_pred = self.model.predict_one(features)
            if y_pred is not None:
                self.accuracy_metric.update(label, y_pred)
                self.f1_metric.update(label, y_pred)
                self.precision_metric.update(label, y_pred)
                self.recall_metric.update(label, y_pred)
            
            # Update performance metrics
            self.performance_metrics['total_trades'] = self.performance_metrics.get('total_trades', 0) + 1
            total = self.performance_metrics['total_trades']
            
            # Track recent trades
            recent_trades = self.performance_metrics.get('recent_trades', [])
            recent_trades.append(profit_loss)
            if len(recent_trades) > 20:
                recent_trades = recent_trades[-20:]
            self.performance_metrics['recent_trades'] = recent_trades
            
            # Track wins and losses
            if profit_loss > 0.005:
                wins = self.performance_metrics.get('wins', 0) + 1
                self.performance_metrics['wins'] = wins
                self.performance_metrics['win_rate'] = wins / total
                
                # Update average profit
                avg_profit = self.performance_metrics.get('avg_profit', 0)
                self.performance_metrics['avg_profit'] = ((avg_profit * (wins - 1)) + profit_loss) / wins
                
            elif profit_loss < -0.005:
                losses = self.performance_metrics.get('losses', 0) + 1
                self.performance_metrics['losses'] = losses
                
                # Update average loss
                avg_loss = self.performance_metrics.get('avg_loss', 0)
                self.performance_metrics['avg_loss'] = ((avg_loss * (losses - 1)) + abs(profit_loss)) / losses
            
            # Update stored metrics
            self.performance_metrics['accuracy'] = self.accuracy_metric.get()
            self.performance_metrics['f1_score'] = self.f1_metric.get()
            self.performance_metrics['precision'] = self.precision_metric.get()
            self.performance_metrics['recall'] = self.recall_metric.get()
            
            self.logger.debug(f"Incremental learning: signal={signal}, P/L={profit_loss:.4f}, label={label}, "
                            f"Accuracy: {self.performance_metrics['accuracy']:.2%}, "
                            f"Win rate: {self.performance_metrics.get('win_rate', 0):.2%}")
            
        except Exception as e:
            self.logger.error(f"Error in incremental learning: {e}")
    
    def record_outcome(self, indicators: Dict, signal: str, profit_loss: float):
        """
        Record trading outcome and learn from it incrementally
        This method maintains API compatibility with the batch model
        
        Args:
            indicators: Dictionary of technical indicators
            signal: The signal that was generated ('BUY' or 'SELL')
            profit_loss: The profit or loss from the trade (percentage)
        """
        self.learn_one(indicators, signal, profit_loss)
    
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
        
        win_rate = self.performance_metrics.get('win_rate', 0.5)
        total_trades = self.performance_metrics.get('total_trades', 0)
        
        # Need minimum trades for reliable adjustment
        if total_trades < 10:
            return base_threshold
        
        # Calculate recent momentum
        recent_trades = self.performance_metrics.get('recent_trades', [])
        if len(recent_trades) >= 10:
            recent_wins = sum(1 for pnl in recent_trades if pnl > 0.005)
            recent_win_rate = recent_wins / len(recent_trades)
            
            # Adjust threshold based on recent performance
            if recent_win_rate > 0.65:
                momentum_adjustment = -0.08
            elif recent_win_rate < 0.35:
                momentum_adjustment = 0.12
            else:
                momentum_adjustment = 0.0
        else:
            momentum_adjustment = 0.0
        
        # Adjust based on overall win rate
        if win_rate > 0.6:
            win_rate_adjustment = -0.03
        elif win_rate < 0.4:
            win_rate_adjustment = 0.08
        else:
            win_rate_adjustment = 0.0
        
        # Combine adjustments
        threshold = base_threshold + (momentum_adjustment * 0.6) + (win_rate_adjustment * 0.4)
        
        # Ensure threshold stays within bounds
        threshold = max(0.52, min(threshold, 0.75))
        
        return threshold
    
    def get_kelly_fraction(self) -> float:
        """
        Calculate Kelly Criterion fraction for optimal position sizing
        
        Returns:
            Kelly fraction (0.0-1.0)
        """
        total_trades = self.performance_metrics.get('total_trades', 0)
        
        if total_trades < 20:
            return 0.0
        
        win_rate = self.performance_metrics.get('win_rate', 0.0)
        avg_profit = self.performance_metrics.get('avg_profit', 0.0)
        avg_loss = self.performance_metrics.get('avg_loss', 0.0)
        
        if avg_loss <= 0 or win_rate <= 0:
            return 0.0
        
        b = avg_profit / avg_loss
        p = win_rate
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Use half-Kelly for safety
        safe_kelly = kelly_fraction * 0.5
        safe_kelly = max(0.0, min(safe_kelly, 0.25))
        
        return safe_kelly
