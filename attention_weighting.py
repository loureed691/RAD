"""
Attention-Based Feature Weighting
Dynamic feature importance for indicators based on market conditions
"""
import numpy as np
from typing import Dict, List
from logger import Logger


class AttentionFeatureWeighting:
    """
    Intelligent feature weighting using attention mechanism:
    - Dynamic indicator importance based on market regime
    - Historical performance tracking for each indicator
    - Attention weights that adapt to market conditions
    - Regime-specific feature boosting
    - Feature importance visualization
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        
        # Feature groups with base weights
        self.feature_groups = {
            'trend': {
                'features': ['ema_12', 'ema_26', 'sma_20', 'sma_50', 'macd', 'macd_signal'],
                'base_weight': 1.0,
                'best_regimes': ['trending', 'bull', 'bear']
            },
            'momentum': {
                'features': ['rsi', 'stoch_k', 'stoch_d', 'momentum', 'roc'],
                'base_weight': 1.0,
                'best_regimes': ['trending', 'bull', 'bear', 'high_vol']
            },
            'volatility': {
                'features': ['bb_width', 'bb_upper', 'bb_lower', 'atr'],
                'base_weight': 1.0,
                'best_regimes': ['high_vol', 'low_vol', 'ranging']
            },
            'volume': {
                'features': ['volume', 'volume_ratio', 'volume_sma'],
                'base_weight': 0.8,
                'best_regimes': ['breakout', 'trending']
            }
        }
        
        # Performance tracking for features
        self.feature_performance = {}  # feature -> {'wins': 0, 'losses': 0, 'accuracy': 0.5}
        
        # Attention weights (learned over time)
        self.attention_weights = {}  # feature -> weight
        self._initialize_attention_weights()
        
        # Learning rate for attention updates
        self.learning_rate = 0.05
        
        self.logger.info("🎯 Attention-Based Feature Weighting initialized")
    
    def _initialize_attention_weights(self):
        """Initialize attention weights to base values"""
        for group_name, group_info in self.feature_groups.items():
            for feature in group_info['features']:
                self.attention_weights[feature] = 1.0
                self.feature_performance[feature] = {
                    'wins': 0,
                    'losses': 0,
                    'accuracy': 0.5
                }
    
    def calculate_attention_weights(self, 
                                   market_regime: str,
                                   volatility: float,
                                   recent_performance: Dict = None) -> Dict[str, float]:
        """
        Calculate attention weights for features based on context
        
        Args:
            market_regime: Current market regime
            volatility: Market volatility
            recent_performance: Recent performance metrics
            
        Returns:
            Dict of feature -> attention weight
        """
        try:
            weights = {}
            
            for group_name, group_info in self.feature_groups.items():
                # Start with base weight
                group_weight = group_info['base_weight']
                
                # Boost if regime matches
                if market_regime in group_info.get('best_regimes', []):
                    group_weight *= 1.5
                
                # Apply to all features in group
                for feature in group_info['features']:
                    # Base weight from group
                    feature_weight = group_weight
                    
                    # Apply learned attention weight
                    feature_weight *= self.attention_weights.get(feature, 1.0)
                    
                    # Apply performance-based adjustment
                    if feature in self.feature_performance:
                        perf = self.feature_performance[feature]
                        accuracy = perf.get('accuracy', 0.5)
                        
                        # Boost high-performing features
                        if accuracy > 0.65:
                            feature_weight *= 1.2
                        elif accuracy < 0.45:
                            feature_weight *= 0.8
                    
                    # Volatility-specific adjustments
                    if group_name == 'volatility' and volatility > 0.05:
                        feature_weight *= 1.3
                    elif group_name == 'trend' and volatility < 0.02:
                        feature_weight *= 1.2
                    
                    weights[feature] = feature_weight
            
            # Normalize weights
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {k: v / total_weight * len(weights) for k, v in weights.items()}
            
            return weights
            
        except Exception as e:
            self.logger.error(f"Error calculating attention weights: {e}")
            # Return uniform weights
            return {f: 1.0 for group in self.feature_groups.values() 
                    for f in group['features']}
    
    def apply_attention_to_indicators(self,
                                     indicators: Dict,
                                     market_regime: str,
                                     volatility: float) -> Dict:
        """
        Apply attention weights to indicators
        
        Args:
            indicators: Raw indicator values
            market_regime: Current market regime
            volatility: Market volatility
            
        Returns:
            Weighted indicators
        """
        try:
            # Calculate attention weights
            attention = self.calculate_attention_weights(
                market_regime, volatility
            )
            
            # Apply weights to indicators
            weighted_indicators = indicators.copy()
            
            for feature, weight in attention.items():
                if feature in weighted_indicators:
                    # Store original value for reference
                    if f'{feature}_raw' not in weighted_indicators:
                        weighted_indicators[f'{feature}_raw'] = weighted_indicators[feature]
                    
                    # Apply attention weight (for normalized features)
                    # Don't modify absolute price values
                    if feature not in ['close', 'open', 'high', 'low']:
                        weighted_indicators[f'{feature}_attention'] = weight
            
            return weighted_indicators
            
        except Exception as e:
            self.logger.error(f"Error applying attention weights: {e}")
            return indicators
    
    def update_feature_performance(self,
                                   indicators: Dict,
                                   signal: str,
                                   outcome_pnl: float):
        """
        Update feature performance based on trade outcome
        
        Args:
            indicators: Indicators used for the trade
            signal: Signal generated ('BUY' or 'SELL')
            outcome_pnl: Trade outcome (positive = win, negative = loss)
        """
        try:
            is_win = outcome_pnl > 0.005  # >0.5% is a win
            
            # Determine which features contributed to the signal
            contributing_features = self._identify_contributing_features(
                indicators, signal
            )
            
            # Update performance for contributing features
            for feature in contributing_features:
                if feature in self.feature_performance:
                    perf = self.feature_performance[feature]
                    
                    if is_win:
                        perf['wins'] += 1
                    else:
                        perf['losses'] += 1
                    
                    total = perf['wins'] + perf['losses']
                    if total > 0:
                        perf['accuracy'] = perf['wins'] / total
                    
                    # Update attention weight using gradient-like update
                    if is_win:
                        # Increase weight for winning feature
                        self.attention_weights[feature] = min(
                            2.0,
                            self.attention_weights[feature] * (1 + self.learning_rate)
                        )
                    else:
                        # Decrease weight for losing feature
                        self.attention_weights[feature] = max(
                            0.5,
                            self.attention_weights[feature] * (1 - self.learning_rate)
                        )
            
        except Exception as e:
            self.logger.debug(f"Error updating feature performance: {e}")
    
    def _identify_contributing_features(self,
                                       indicators: Dict,
                                       signal: str) -> List[str]:
        """
        Identify which features likely contributed to the signal
        
        Args:
            indicators: Indicator values
            signal: Generated signal
            
        Returns:
            List of contributing feature names
        """
        try:
            contributing = []
            
            # Trend features
            if signal == 'BUY':
                if indicators.get('ema_12', 0) > indicators.get('ema_26', 0):
                    contributing.extend(['ema_12', 'ema_26'])
                if indicators.get('macd', 0) > indicators.get('macd_signal', 0):
                    contributing.extend(['macd', 'macd_signal'])
            elif signal == 'SELL':
                if indicators.get('ema_12', 0) < indicators.get('ema_26', 0):
                    contributing.extend(['ema_12', 'ema_26'])
                if indicators.get('macd', 0) < indicators.get('macd_signal', 0):
                    contributing.extend(['macd', 'macd_signal'])
            
            # Momentum features
            rsi = indicators.get('rsi', 50)
            if signal == 'BUY' and rsi < 40:
                contributing.append('rsi')
            elif signal == 'SELL' and rsi > 60:
                contributing.append('rsi')
            
            # Stochastic
            stoch_k = indicators.get('stoch_k', 50)
            if signal == 'BUY' and stoch_k < 30:
                contributing.append('stoch_k')
            elif signal == 'SELL' and stoch_k > 70:
                contributing.append('stoch_k')
            
            # Volume
            volume_ratio = indicators.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                contributing.append('volume_ratio')
            
            return list(set(contributing))  # Remove duplicates
            
        except Exception as e:
            self.logger.debug(f"Error identifying contributing features: {e}")
            return []
    
    def get_feature_importance_summary(self) -> Dict:
        """
        Get summary of feature importance
        
        Returns:
            Dict with feature importance statistics
        """
        try:
            summary = {
                'top_features': [],
                'bottom_features': [],
                'feature_stats': {}
            }
            
            # Collect feature stats
            feature_scores = []
            for feature, perf in self.feature_performance.items():
                if perf['wins'] + perf['losses'] >= 5:  # Minimum trades
                    score = {
                        'feature': feature,
                        'accuracy': perf['accuracy'],
                        'attention_weight': self.attention_weights.get(feature, 1.0),
                        'trades': perf['wins'] + perf['losses']
                    }
                    feature_scores.append(score)
            
            # Sort by accuracy
            feature_scores.sort(key=lambda x: x['accuracy'], reverse=True)
            
            # Top and bottom features
            summary['top_features'] = feature_scores[:5]
            summary['bottom_features'] = feature_scores[-5:]
            
            # All features
            summary['feature_stats'] = {
                f['feature']: {
                    'accuracy': f['accuracy'],
                    'weight': f['attention_weight'],
                    'trades': f['trades']
                }
                for f in feature_scores
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating feature importance summary: {e}")
            return {'top_features': [], 'bottom_features': [], 'feature_stats': {}}
    
    def log_feature_importance(self):
        """Log current feature importance"""
        try:
            summary = self.get_feature_importance_summary()
            
            if not summary['top_features']:
                self.logger.debug("Not enough trade history for feature importance")
                return
            
            self.logger.info("=" * 60)
            self.logger.info("🎯 FEATURE IMPORTANCE SUMMARY")
            self.logger.info("=" * 60)
            
            self.logger.info("Top Performing Features:")
            for i, feat in enumerate(summary['top_features'], 1):
                self.logger.info(
                    f"  {i}. {feat['feature']}: "
                    f"Accuracy={feat['accuracy']:.1%}, "
                    f"Weight={feat['attention_weight']:.2f}, "
                    f"Trades={feat['trades']}"
                )
            
            if summary['bottom_features']:
                self.logger.info("\nBottom Performing Features:")
                for i, feat in enumerate(summary['bottom_features'], 1):
                    self.logger.info(
                        f"  {i}. {feat['feature']}: "
                        f"Accuracy={feat['accuracy']:.1%}, "
                        f"Weight={feat['attention_weight']:.2f}, "
                        f"Trades={feat['trades']}"
                    )
            
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Error logging feature importance: {e}")
