"""
Attention-Based Feature Selection - 2025 Enhancement
Dynamic feature weighting using attention mechanism
"""
import numpy as np
import os
from typing import Dict, List, Tuple
from logger import Logger
from sklearn.preprocessing import StandardScaler


class AttentionFeatureSelector:
    """
    Attention mechanism for dynamic feature importance weighting
    
    Learns which features are most important in current market conditions
    and adjusts their contributions to predictions accordingly.
    """
    
    def __init__(self, n_features: int = 31, learning_rate: float = 0.01):
        """
        Initialize attention mechanism
        
        Args:
            n_features: Number of features in model
            learning_rate: Learning rate for attention weight updates
        """
        self.logger = Logger.get_logger()
        self.n_features = n_features
        self.learning_rate = learning_rate
        
        # Initialize attention weights uniformly
        self.attention_weights = np.ones(n_features) / n_features
        
        # Track feature importance history for learning
        self.feature_outcomes = [[] for _ in range(n_features)]
        
        # Feature names for interpretability
        self.feature_names = self._get_default_feature_names()
        
        # Load existing weights if available
        self.load_weights()
        
    def _get_default_feature_names(self) -> List[str]:
        """Get default feature names matching ml_model.py"""
        return [
            'rsi', 'macd', 'macd_signal', 'macd_diff',
            'stoch_k', 'stoch_d', 'bb_width', 'volume_ratio',
            'momentum', 'roc', 'cci', 'willr',
            'adx', 'atr', 'obv_norm', 'mfi',
            'ema_20', 'ema_50', 'ema_200', 'trend_strength',
            'bb_position', 'price_vs_vwap', 'volume_strength',
            'rsi_momentum', 'macd_strength', 'price_momentum',
            'volatility_regime', 'trend_regime', 'volume_regime',
            'momentum_regime', 'multi_timeframe_signal'
        ]
    
    def calculate_attention_scores(self, features: np.ndarray) -> np.ndarray:
        """
        Calculate attention scores for current features
        
        Uses simple scaled dot-product attention:
        attention(Q,K,V) = softmax(Q·K^T / sqrt(d)) · V
        
        For simplicity, we use feature values as queries and 
        learned weights as keys/values.
        
        Args:
            features: Feature vector (shape: n_features)
            
        Returns:
            Attention scores (shape: n_features)
        """
        try:
            # Normalize features for attention calculation
            feature_norm = np.linalg.norm(features)
            if feature_norm > 0:
                normalized_features = features / feature_norm
            else:
                normalized_features = features
            
            # Calculate attention scores using dot product with learned weights
            raw_scores = normalized_features * self.attention_weights
            
            # Apply softmax for probability distribution
            exp_scores = np.exp(raw_scores - np.max(raw_scores))  # Numerical stability
            attention_scores = exp_scores / np.sum(exp_scores)
            
            return attention_scores
            
        except Exception as e:
            self.logger.error(f"Error calculating attention scores: {e}")
            return np.ones(self.n_features) / self.n_features
    
    def apply_attention(self, features: np.ndarray) -> np.ndarray:
        """
        Apply attention weighting to features
        
        Args:
            features: Original feature vector
            
        Returns:
            Attention-weighted features
        """
        try:
            attention_scores = self.calculate_attention_scores(features)
            
            # Weight features by attention scores
            weighted_features = features * attention_scores * self.n_features
            
            # Log top features if debug enabled
            if self.logger.isEnabledFor(10):  # DEBUG level
                top_indices = np.argsort(attention_scores)[-5:][::-1]
                top_features = [(self.feature_names[i], attention_scores[i]) 
                              for i in top_indices]
                self.logger.debug(f"Top attention features: {top_features}")
            
            return weighted_features
            
        except Exception as e:
            self.logger.error(f"Error applying attention: {e}")
            return features
    
    def update_attention_weights(self, features: np.ndarray, 
                                outcome: bool, 
                                profit_loss_pct: float = 0.0):
        """
        Update attention weights based on trade outcome
        
        Uses gradient descent to learn which features contribute 
        to successful predictions.
        
        Args:
            features: Feature vector used for prediction
            outcome: True if trade was successful
            profit_loss_pct: Magnitude of profit/loss
        """
        try:
            # Record outcome for each feature
            for i in range(self.n_features):
                self.feature_outcomes[i].append({
                    'value': features[i],
                    'outcome': outcome,
                    'profit_loss': profit_loss_pct
                })
                
                # Keep limited history
                if len(self.feature_outcomes[i]) > 100:
                    self.feature_outcomes[i].pop(0)
            
            # Update weights if we have enough data
            if len(self.feature_outcomes[0]) >= 10:
                self._gradient_update(features, outcome, profit_loss_pct)
            
        except Exception as e:
            self.logger.error(f"Error updating attention weights: {e}")
    
    def _gradient_update(self, features: np.ndarray, 
                        outcome: bool, 
                        profit_loss_pct: float):
        """
        Perform gradient descent update on attention weights
        
        Args:
            features: Current features
            outcome: Trade outcome
            profit_loss_pct: Profit/loss percentage
        """
        try:
            # Calculate gradients based on recent performance
            gradients = np.zeros(self.n_features)
            
            for i in range(self.n_features):
                recent = self.feature_outcomes[i][-20:]  # Last 20 trades
                
                # Calculate correlation between feature value and positive outcomes
                feature_values = [d['value'] for d in recent]
                outcomes = [1.0 if d['outcome'] else -1.0 for d in recent]
                
                if len(feature_values) > 1:
                    # Simple correlation
                    corr = np.corrcoef(feature_values, outcomes)[0, 1]
                    if not np.isnan(corr):
                        gradients[i] = corr
            
            # Update weights with gradient ascent (we want to maximize performance)
            reward = 1.0 if outcome else -1.0
            reward *= abs(profit_loss_pct) * 10  # Scale by magnitude
            
            self.attention_weights += self.learning_rate * gradients * reward
            
            # Ensure weights stay positive and normalized
            self.attention_weights = np.abs(self.attention_weights)
            weight_sum = np.sum(self.attention_weights)
            if weight_sum > 0:
                self.attention_weights /= weight_sum
            else:
                self.attention_weights = np.ones(self.n_features) / self.n_features
            
        except Exception as e:
            self.logger.error(f"Error in gradient update: {e}")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get current feature importance rankings
        
        Returns:
            Dictionary of feature_name: importance_score
        """
        try:
            importance = {}
            for i, name in enumerate(self.feature_names):
                importance[name] = float(self.attention_weights[i])
            
            # Sort by importance
            sorted_importance = dict(sorted(
                importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            ))
            
            return sorted_importance
            
        except Exception as e:
            self.logger.error(f"Error getting feature importance: {e}")
            return {}
    
    def get_top_features(self, n: int = 10) -> List[Tuple[str, float]]:
        """
        Get top N most important features
        
        Args:
            n: Number of top features to return
            
        Returns:
            List of (feature_name, importance) tuples
        """
        try:
            importance = self.get_feature_importance()
            top_n = list(importance.items())[:n]
            return top_n
            
        except Exception as e:
            self.logger.error(f"Error getting top features: {e}")
            return []
    
    def get_regime_specific_features(self, market_regime: str) -> List[str]:
        """
        Get most important features for specific market regime
        
        Different features matter in different market conditions.
        
        Args:
            market_regime: Current market regime
            
        Returns:
            List of important feature names for this regime
        """
        # Define regime-specific important features based on trading theory
        regime_features = {
            'trending': ['trend_strength', 'macd', 'ema_20', 'ema_50', 
                        'momentum', 'adx', 'price_momentum'],
            'ranging': ['rsi', 'stoch_k', 'bb_position', 'mfi', 
                       'willr', 'cci'],
            'high_volatility': ['atr', 'bb_width', 'volatility_regime',
                              'volume_ratio', 'volume_strength'],
            'low_volatility': ['trend_strength', 'macd', 'rsi',
                             'price_vs_vwap'],
            'bull': ['momentum', 'rsi', 'macd', 'volume_ratio',
                    'ema_20', 'trend_strength'],
            'bear': ['rsi', 'stoch_k', 'bb_position', 'willr',
                    'volume_strength'],
            'neutral': ['rsi', 'macd', 'bb_position', 'volume_ratio',
                       'trend_strength']
        }
        
        return regime_features.get(market_regime, regime_features['neutral'])
    
    def boost_regime_features(self, features: np.ndarray, 
                             market_regime: str,
                             boost_factor: float = 1.3) -> np.ndarray:
        """
        Boost importance of regime-specific features
        
        Args:
            features: Feature vector
            market_regime: Current market regime
            boost_factor: Multiplier for regime-specific features
            
        Returns:
            Adjusted feature vector
        """
        try:
            adjusted_features = features.copy()
            regime_features = self.get_regime_specific_features(market_regime)
            
            for feature_name in regime_features:
                if feature_name in self.feature_names:
                    idx = self.feature_names.index(feature_name)
                    adjusted_features[idx] *= boost_factor
            
            self.logger.debug(f"Boosted {len(regime_features)} features for {market_regime} regime")
            return adjusted_features
            
        except Exception as e:
            self.logger.error(f"Error boosting regime features: {e}")
            return features
    
    def save_weights(self, filepath: str = 'models/attention_weights.npy'):
        """Save attention weights to disk"""
        try:
            np.save(filepath, self.attention_weights)
            self.logger.info(f"Saved attention weights to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving attention weights: {e}")
    
    def load_weights(self, filepath: str = 'models/attention_weights.npy'):
        """Load attention weights from disk"""
        try:
            if os.path.exists(filepath):
                self.attention_weights = np.load(filepath)
                self.logger.info(f"Loaded attention weights from {filepath}")
            else:
                self.logger.info("No saved attention weights found, using defaults")
        except Exception as e:
            self.logger.error(f"Error loading attention weights: {e}")
