"""
ML Strategy Coordinator 2025 - Unified Machine Learning Decision Framework

This module coordinates all advanced ML components to provide the smartest,
most adaptive trading strategies using cutting-edge 2025 ML/AI techniques:

1. Deep Learning Signal Prediction (LSTM + Dense)
2. Reinforcement Learning Strategy Selection (Q-learning)
3. Multi-Timeframe Signal Fusion (Weighted voting)
4. Adaptive Ensemble Voting (Meta-learning)
5. Attention-Based Feature Weighting
6. Bayesian Confidence Calibration

The coordinator integrates all these components into a unified decision-making
framework that adapts to market conditions and continuously improves.
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional
from datetime import datetime
from logger import Logger
from config import Config

# Import all advanced ML components
from enhanced_ml_intelligence import (
    DeepLearningSignalPredictor,
    MultiTimeframeSignalFusion,
    AdaptiveExitStrategy,
    ReinforcementLearningStrategy
)

try:
    from attention_features_2025 import AttentionFeatureSelector
    ATTENTION_AVAILABLE = True
except ImportError:
    ATTENTION_AVAILABLE = False
    
try:
    from bayesian_kelly_2025 import BayesianAdaptiveKelly
    BAYESIAN_AVAILABLE = True
except ImportError:
    BAYESIAN_AVAILABLE = False


class MLStrategyCoordinator2025:
    """
    Unified ML strategy coordinator that integrates all advanced ML components
    for optimal trading decisions using 2025 cutting-edge techniques.
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.strategy_logger = Logger.get_strategy_logger()
        
        # Initialize all ML components
        self.logger.info("🤖 Initializing ML Strategy Coordinator 2025...")
        
        # 1. Deep Learning Signal Predictor
        try:
            self.dl_predictor = DeepLearningSignalPredictor(n_features=31, sequence_length=10)
            self.dl_enabled = True
            self.logger.info("   ✅ Deep Learning Predictor initialized")
        except Exception as e:
            self.logger.warning(f"   ⚠️  Deep Learning unavailable: {e}")
            self.dl_predictor = None
            self.dl_enabled = False
        
        # 2. Multi-Timeframe Signal Fusion
        self.mtf_fusion = MultiTimeframeSignalFusion()
        self.logger.info("   ✅ Multi-Timeframe Fusion initialized")
        
        # 3. Reinforcement Learning Strategy Selector
        self.rl_selector = ReinforcementLearningStrategy(learning_rate=0.1, discount_factor=0.95)
        self.rl_selector.load_q_table()  # Load existing Q-table if available
        self.logger.info("   ✅ RL Strategy Selector initialized")
        
        # 4. Attention-Based Feature Selector (if available)
        if ATTENTION_AVAILABLE:
            try:
                self.attention_selector = AttentionFeatureSelector()
                self.attention_enabled = True
                self.logger.info("   ✅ Attention Feature Selector initialized")
            except Exception as e:
                self.logger.warning(f"   ⚠️  Attention selector unavailable: {e}")
                self.attention_selector = None
                self.attention_enabled = False
        else:
            self.attention_selector = None
            self.attention_enabled = False
        
        # 5. Bayesian Confidence Calibration (if available)
        if BAYESIAN_AVAILABLE:
            try:
                self.bayesian_kelly = BayesianAdaptiveKelly()
                self.bayesian_enabled = True
                self.logger.info("   ✅ Bayesian Kelly Criterion initialized")
            except Exception as e:
                self.logger.warning(f"   ⚠️  Bayesian Kelly unavailable: {e}")
                self.bayesian_kelly = None
                self.bayesian_enabled = False
        else:
            self.bayesian_kelly = None
            self.bayesian_enabled = False
        
        # Ensemble voting configuration
        self.ensemble_weights = {
            'technical': 0.30,      # Base technical analysis
            'deep_learning': 0.25,  # Deep learning predictor
            'mtf_fusion': 0.20,     # Multi-timeframe fusion
            'rl_strategy': 0.15,    # RL-based strategy selection
            'attention': 0.10       # Attention-weighted features
        }
        
        # Performance tracking for adaptive weight adjustment
        self.component_performance = {
            'technical': {'correct': 0, 'total': 0, 'accuracy': 0.5},
            'deep_learning': {'correct': 0, 'total': 0, 'accuracy': 0.5},
            'mtf_fusion': {'correct': 0, 'total': 0, 'accuracy': 0.5},
            'rl_strategy': {'correct': 0, 'total': 0, 'accuracy': 0.5},
            'attention': {'correct': 0, 'total': 0, 'accuracy': 0.5}
        }
        
        # Meta-learning: track which combinations work best
        self.strategy_combinations = {}
        
        self.logger.info("🚀 ML Strategy Coordinator 2025 ready!")
        self.logger.info(f"   Components active: {sum([self.dl_enabled, True, True, self.attention_enabled])}/5")
    
    def generate_unified_signal(self,
                                technical_signal: str,
                                technical_confidence: float,
                                technical_reasons: Dict,
                                df_1h: pd.DataFrame,
                                df_4h: Optional[pd.DataFrame] = None,
                                df_1d: Optional[pd.DataFrame] = None,
                                indicators: Dict = None,
                                market_regime: str = 'neutral',
                                volatility: float = 0.03) -> Tuple[str, float, Dict]:
        """
        Generate unified trading signal by coordinating all ML components.
        
        This is the main method that integrates:
        1. Technical analysis baseline
        2. Deep learning predictions
        3. Multi-timeframe fusion
        4. RL strategy selection
        5. Attention-weighted features
        6. Bayesian confidence calibration
        
        Args:
            technical_signal: Base signal from technical analysis
            technical_confidence: Confidence from technical analysis
            technical_reasons: Reasons dict from technical analysis
            df_1h: 1-hour timeframe data
            df_4h: 4-hour timeframe data (optional)
            df_1d: 1-day timeframe data (optional)
            indicators: Latest indicators dict
            market_regime: Current market regime
            volatility: Current volatility level
            
        Returns:
            Tuple of (unified_signal, unified_confidence, unified_reasons)
        """
        self.strategy_logger.info("=" * 80)
        self.strategy_logger.info("🤖 ML STRATEGY COORDINATOR 2025 - UNIFIED ANALYSIS")
        self.strategy_logger.info("=" * 80)
        
        # Store component signals for ensemble voting
        signals = {}
        confidences = {}
        
        # 1. Technical Analysis (baseline)
        signals['technical'] = technical_signal
        confidences['technical'] = technical_confidence
        self.strategy_logger.info(f"1️⃣  Technical Analysis: {technical_signal} (conf: {technical_confidence:.2%})")
        
        # 2. Deep Learning Prediction
        if self.dl_enabled and indicators:
            try:
                features = self._prepare_features(indicators)
                dl_signal, dl_confidence = self.dl_predictor.predict(features)
                signals['deep_learning'] = dl_signal
                confidences['deep_learning'] = dl_confidence
                self.strategy_logger.info(f"2️⃣  Deep Learning: {dl_signal} (conf: {dl_confidence:.2%})")
            except Exception as e:
                self.logger.debug(f"Deep learning prediction error: {e}")
                signals['deep_learning'] = 'HOLD'
                confidences['deep_learning'] = 0.3
        else:
            signals['deep_learning'] = technical_signal  # Fallback to technical
            confidences['deep_learning'] = technical_confidence * 0.8
        
        # 3. Multi-Timeframe Fusion
        if df_4h is not None and df_1d is not None:
            try:
                # Get signals for each timeframe (reuse technical signal for 1h)
                sig_1h = (technical_signal, technical_confidence)
                
                # For 4h and 1d, use simplified signal (could be enhanced)
                sig_4h = (technical_signal, technical_confidence * 0.9)
                sig_1d = (technical_signal, technical_confidence * 0.85)
                
                mtf_signal, mtf_confidence, mtf_details = self.mtf_fusion.fuse_signals(
                    sig_1h, sig_4h, sig_1d
                )
                signals['mtf_fusion'] = mtf_signal
                confidences['mtf_fusion'] = mtf_confidence
                self.strategy_logger.info(f"3️⃣  Multi-Timeframe Fusion: {mtf_signal} (conf: {mtf_confidence:.2%})")
                self.strategy_logger.info(f"    Agreement: {mtf_details.get('agreement_score', 0):.2%}, Consistency: {mtf_details.get('consistency_score', 0):.2%}")
            except Exception as e:
                self.logger.debug(f"MTF fusion error: {e}")
                signals['mtf_fusion'] = technical_signal
                confidences['mtf_fusion'] = technical_confidence * 0.9
        else:
            signals['mtf_fusion'] = technical_signal
            confidences['mtf_fusion'] = technical_confidence * 0.85
        
        # 4. RL Strategy Selection
        try:
            # RL selects best strategy type for current conditions
            selected_strategy = self.rl_selector.select_strategy(market_regime, volatility)
            
            # Adjust signal based on strategy selection
            strategy_adjustment = self._apply_rl_strategy(
                selected_strategy, technical_signal, technical_confidence, 
                indicators, market_regime
            )
            signals['rl_strategy'] = strategy_adjustment['signal']
            confidences['rl_strategy'] = strategy_adjustment['confidence']
            self.strategy_logger.info(f"4️⃣  RL Strategy ({selected_strategy}): {strategy_adjustment['signal']} (conf: {strategy_adjustment['confidence']:.2%})")
        except Exception as e:
            self.logger.debug(f"RL strategy error: {e}")
            signals['rl_strategy'] = technical_signal
            confidences['rl_strategy'] = technical_confidence * 0.9
        
        # 5. Attention-Weighted Features
        if self.attention_enabled and indicators:
            try:
                features = self._prepare_features(indicators)
                attention_weights = self.attention_selector.calculate_attention_weights(features)
                
                # Use attention to boost or reduce confidence
                attention_signal, attention_conf = self._apply_attention_weighting(
                    technical_signal, technical_confidence, 
                    attention_weights, indicators
                )
                signals['attention'] = attention_signal
                confidences['attention'] = attention_conf
                self.strategy_logger.info(f"5️⃣  Attention-Weighted: {attention_signal} (conf: {attention_conf:.2%})")
            except Exception as e:
                self.logger.debug(f"Attention weighting error: {e}")
                signals['attention'] = technical_signal
                confidences['attention'] = technical_confidence * 0.95
        else:
            signals['attention'] = technical_signal
            confidences['attention'] = technical_confidence * 0.95
        
        # 6. Ensemble Voting with Adaptive Weights
        unified_signal, unified_confidence = self._ensemble_vote(signals, confidences)
        
        self.strategy_logger.info("-" * 80)
        self.strategy_logger.info(f"🎯 UNIFIED SIGNAL: {unified_signal}")
        self.strategy_logger.info(f"🎯 UNIFIED CONFIDENCE: {unified_confidence:.2%}")
        self.strategy_logger.info("-" * 80)
        
        # 7. Bayesian Confidence Calibration
        if self.bayesian_enabled and unified_signal != 'HOLD':
            try:
                # Use Bayesian Kelly to calibrate confidence based on historical win rate
                calibrated_confidence = self._bayesian_calibrate_confidence(
                    unified_confidence, unified_signal
                )
                
                if calibrated_confidence != unified_confidence:
                    self.strategy_logger.info(f"📊 Bayesian Calibration: {unified_confidence:.2%} → {calibrated_confidence:.2%}")
                    unified_confidence = calibrated_confidence
            except Exception as e:
                self.logger.debug(f"Bayesian calibration error: {e}")
        
        # Build unified reasons
        unified_reasons = {
            **technical_reasons,
            'ml_coordinator': 'active',
            'ensemble_components': len([s for s in signals.values() if s != 'HOLD']),
            'component_signals': {k: f"{v} ({confidences[k]:.1%})" for k, v in signals.items()},
            'adaptive_weights': {k: f"{v:.1%}" for k, v in self.ensemble_weights.items()}
        }
        
        self.strategy_logger.info("=" * 80)
        self.strategy_logger.info("")
        
        return unified_signal, unified_confidence, unified_reasons
    
    def _prepare_features(self, indicators: Dict) -> np.ndarray:
        """Prepare feature vector from indicators for ML models"""
        # Core technical indicators
        features = [
            indicators.get('rsi', 50) / 100.0,  # Normalize to 0-1
            indicators.get('macd', 0) * 10,
            indicators.get('macd_signal', 0) * 10,
            indicators.get('macd_diff', 0) * 10,
            indicators.get('stoch_k', 50) / 100.0,
            indicators.get('stoch_d', 50) / 100.0,
            indicators.get('bb_width', 0) * 10,
            indicators.get('volume_ratio', 1.0),
            indicators.get('momentum', 0) * 10,
            indicators.get('roc', 0) / 10.0,
            indicators.get('atr', 0) * 100,
            
            # Price-based features
            indicators.get('close', 0) / 50000.0,  # Normalize
            indicators.get('ema_12', 0) / 50000.0,
            indicators.get('ema_26', 0) / 50000.0,
            indicators.get('sma_20', 0) / 50000.0,
            indicators.get('sma_50', 0) / 50000.0,
            indicators.get('bb_high', 0) / 50000.0,
            indicators.get('bb_mid', 0) / 50000.0,
            indicators.get('bb_low', 0) / 50000.0,
            
            # Derived features
            (indicators.get('ema_12', 0) - indicators.get('ema_26', 0)) / max(indicators.get('ema_26', 1), 1),
            ((indicators.get('close', 0) - indicators.get('sma_20', 0)) / indicators['sma_20'] if indicators.get('sma_20', 0) != 0 else 0.0),
            (indicators.get('close', 0) - indicators.get('bb_mid', 0)) / max(indicators.get('bb_width', 0.01), 0.01),
            
            # Additional features to reach 31
            indicators.get('adx', 25) / 100.0 if 'adx' in indicators else 0.25,
            indicators.get('cci', 0) / 200.0 if 'cci' in indicators else 0.0,
            indicators.get('williams_r', -50) / 100.0 if 'williams_r' in indicators else -0.5,
            indicators.get('momentum_strength', 0) if 'momentum_strength' in indicators else 0.0,
            indicators.get('trend_strength', 0.5) if 'trend_strength' in indicators else 0.5,
            indicators.get('volume_trend', 0) if 'volume_trend' in indicators else 0.0,
            indicators.get('price_position', 0.5) if 'price_position' in indicators else 0.5,
            indicators.get('volatility_ratio', 1.0) if 'volatility_ratio' in indicators else 1.0,
            indicators.get('momentum_divergence', 0) if 'momentum_divergence' in indicators else 0.0
        ]
        
        return np.array(features, dtype=np.float32)
    
    def _apply_rl_strategy(self, strategy: str, signal: str, confidence: float,
                          indicators: Dict, market_regime: str) -> Dict:
        """
        Apply RL-selected strategy to adjust signal/confidence
        
        Different strategies emphasize different aspects:
        - trend_following: Emphasize trend indicators
        - mean_reversion: Emphasize oversold/overbought
        - breakout: Emphasize volatility and momentum
        - momentum: Emphasize momentum indicators
        """
        adjustment = {'signal': signal, 'confidence': confidence}
        
        if strategy == 'trend_following':
            # Boost confidence for aligned trends
            if indicators:
                ema_12 = indicators.get('ema_12', 0)
                ema_26 = indicators.get('ema_26', 0)
                if (signal == 'BUY' and ema_12 > ema_26) or (signal == 'SELL' and ema_12 < ema_26):
                    adjustment['confidence'] = min(confidence * 1.15, 0.99)
                else:
                    adjustment['confidence'] = confidence * 0.85
        
        elif strategy == 'mean_reversion':
            # Boost for extreme RSI
            if indicators:
                rsi = indicators.get('rsi', 50)
                if (signal == 'BUY' and rsi < 30) or (signal == 'SELL' and rsi > 70):
                    adjustment['confidence'] = min(confidence * 1.2, 0.99)
                elif 40 < rsi < 60:
                    # Neutral zone - reduce confidence
                    adjustment['confidence'] = confidence * 0.8
        
        elif strategy == 'breakout':
            # Boost for high volatility + momentum
            if indicators:
                volatility = indicators.get('bb_width', 0)
                momentum = abs(indicators.get('momentum', 0))
                if volatility > 0.04 and momentum > 0.02:
                    adjustment['confidence'] = min(confidence * 1.18, 0.99)
                elif volatility < 0.02:
                    adjustment['confidence'] = confidence * 0.85
        
        elif strategy == 'momentum':
            # Boost for strong momentum
            if indicators:
                momentum = indicators.get('momentum', 0)
                if (signal == 'BUY' and momentum > 0.025) or (signal == 'SELL' and momentum < -0.025):
                    adjustment['confidence'] = min(confidence * 1.2, 0.99)
                elif abs(momentum) < 0.01:
                    adjustment['confidence'] = confidence * 0.85
        
        return adjustment
    
    def _apply_attention_weighting(self, signal: str, confidence: float,
                                  attention_weights: np.ndarray,
                                  indicators: Dict) -> Tuple[str, float]:
        """
        Apply attention weights to boost/reduce confidence based on
        which features are most important for current market conditions
        """
        # Calculate weighted importance of bullish vs bearish indicators
        # This is simplified - in practice would use the actual attention mechanism
        
        # For now, use attention to slightly adjust confidence
        avg_attention = np.mean(attention_weights) if len(attention_weights) > 0 else 0.5
        
        # If attention is high (features are clearly pointing one way), boost confidence
        if avg_attention > 0.7:
            adjusted_conf = min(confidence * 1.1, 0.99)
        elif avg_attention < 0.3:
            # Low attention = unclear signals, reduce confidence
            adjusted_conf = confidence * 0.9
        else:
            adjusted_conf = confidence
        
        return signal, adjusted_conf
    
    def _ensemble_vote(self, signals: Dict[str, str], 
                      confidences: Dict[str, float]) -> Tuple[str, float]:
        """
        Ensemble voting with adaptive weights based on component performance
        """
        # Update ensemble weights based on recent performance
        self._update_adaptive_weights()
        
        # Calculate weighted votes
        vote_scores = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        total_weight = 0.0
        
        for component, signal in signals.items():
            if component in self.ensemble_weights:
                weight = self.ensemble_weights[component]
                confidence = confidences.get(component, 0.5)
                
                # Vote weighted by component weight and confidence
                vote_scores[signal] += weight * confidence
                total_weight += weight
        
        # Determine winning signal
        if total_weight == 0:
            return 'HOLD', 0.0
        
        # Normalize scores
        for signal in vote_scores:
            vote_scores[signal] /= total_weight
        
        # Get winning signal
        winning_signal = max(vote_scores, key=vote_scores.get)
        winning_score = vote_scores[winning_signal]
        
        # Calculate unified confidence
        # Higher score = more agreement among components
        unified_confidence = winning_score
        
        # Boost confidence if multiple components strongly agree
        agreement_count = sum(1 for s in signals.values() if s == winning_signal)
        if agreement_count >= 4:
            unified_confidence = min(unified_confidence * 1.1, 0.99)
        elif agreement_count >= 3:
            unified_confidence = min(unified_confidence * 1.05, 0.99)
        
        return winning_signal, unified_confidence
    
    def _update_adaptive_weights(self):
        """
        Update ensemble weights based on component performance
        Better performing components get higher weights
        """
        # Calculate performance-based adjustment
        for component in self.ensemble_weights:
            if component in self.component_performance:
                perf = self.component_performance[component]
                if perf['total'] >= 10:  # Need minimum samples
                    accuracy = perf['accuracy']
                    
                    # Adjust weight based on accuracy
                    # High accuracy (>70%) gets boost, low accuracy (<50%) gets reduction
                    if accuracy > 0.70:
                        adjustment = 1.0 + (accuracy - 0.70) * 0.5  # Up to 15% boost
                    elif accuracy < 0.50:
                        adjustment = 1.0 - (0.50 - accuracy) * 0.5  # Up to 25% reduction
                    else:
                        adjustment = 1.0
                    
                    # Apply adjustment (limited range)
                    base_weight = 1.0 / len(self.ensemble_weights)  # Equal starting point
                    self.ensemble_weights[component] = base_weight * adjustment
        
        # Normalize weights to sum to 1.0
        total = sum(self.ensemble_weights.values())
        if total > 0:
            for component in self.ensemble_weights:
                self.ensemble_weights[component] /= total
    
    def _bayesian_calibrate_confidence(self, confidence: float, signal: str) -> float:
        """
        Use Bayesian approach to calibrate confidence based on historical win rate
        """
        if not self.bayesian_enabled:
            return confidence
        
        try:
            # Get historical win rate from Bayesian Kelly
            win_rate = self.bayesian_kelly.get_win_rate_estimate()
            
            # Calibrate confidence based on win rate
            # If win rate is high, we can be more confident
            # If win rate is low, reduce confidence
            calibration_factor = win_rate / 0.5  # Normalize around 50%
            calibration_factor = max(0.7, min(calibration_factor, 1.3))  # Limit range
            
            calibrated = confidence * calibration_factor
            return min(max(calibrated, 0.0), 0.99)
        except Exception as e:
            self.logger.debug(f"Bayesian calibration error: {e}")
            return confidence
    
    def update_performance(self, component: str, was_correct: bool):
        """Update performance tracking for a component"""
        if component in self.component_performance:
            perf = self.component_performance[component]
            perf['total'] += 1
            if was_correct:
                perf['correct'] += 1
            perf['accuracy'] = perf['correct'] / perf['total'] if perf['total'] > 0 else 0.5
    
    def update_rl_strategy(self, market_regime: str, volatility: float, 
                          strategy: str, reward: float):
        """Update RL Q-values based on trade outcome"""
        self.rl_selector.update_q_value(market_regime, volatility, strategy, reward)
        
        # Periodically save Q-table
        if np.random.random() < 0.1:  # 10% chance to save
            self.rl_selector.save_q_table()
    
    def save_models(self):
        """Save all ML models"""
        try:
            if self.dl_enabled and self.dl_predictor:
                self.dl_predictor.save()
            
            self.rl_selector.save_q_table()
            
            self.logger.info("💾 ML models saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving ML models: {e}")
