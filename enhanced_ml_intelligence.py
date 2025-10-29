"""
Enhanced Machine Learning Intelligence - Advanced AI for Smarter Trading
Implements deep learning, reinforcement learning, and advanced signal processing
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import deque
import joblib
import os

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, optimizers
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    
from logger import Logger


class DeepLearningSignalPredictor:
    """
    Deep neural network for signal prediction with LSTM for temporal patterns.
    Significantly more sophisticated than basic ensemble methods.
    """
    
    def __init__(self, n_features: int = 31, sequence_length: int = 10):
        self.logger = Logger.get_logger()
        self.n_features = n_features
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = None
        self.feature_buffer = deque(maxlen=sequence_length)
        self.model_path = 'models/deep_signal_model.h5'
        
        if not TENSORFLOW_AVAILABLE:
            self.logger.warning("TensorFlow not available, DeepLearningSignalPredictor disabled")
            return
            
        # Create models directory
        os.makedirs('models', exist_ok=True)
        
        # Try to load existing model
        if os.path.exists(self.model_path):
            try:
                self.model = keras.models.load_model(self.model_path)
                self.logger.info("Loaded existing deep learning model")
            except Exception as e:
                self.logger.warning(f"Could not load existing model: {e}")
                self._build_model()
        else:
            self._build_model()
    
    def _build_model(self):
        """Build advanced LSTM + Dense neural network"""
        if not TENSORFLOW_AVAILABLE:
            return
            
        try:
            # Input: sequence of features over time
            inputs = layers.Input(shape=(self.sequence_length, self.n_features))
            
            # LSTM layers for temporal pattern recognition
            x = layers.LSTM(128, return_sequences=True, dropout=0.2)(inputs)
            x = layers.LSTM(64, return_sequences=False, dropout=0.2)(x)
            
            # Dense layers for decision making
            x = layers.Dense(64, activation='relu')(x)
            x = layers.Dropout(0.3)(x)
            x = layers.Dense(32, activation='relu')(x)
            x = layers.Dropout(0.2)(x)
            
            # Output: 3 classes (HOLD, BUY, SELL)
            outputs = layers.Dense(3, activation='softmax')(x)
            
            self.model = models.Model(inputs=inputs, outputs=outputs)
            
            # Compile with optimizer
            self.model.compile(
                optimizer=optimizers.Adam(learning_rate=0.001),
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )
            
            self.logger.info("Built deep learning signal prediction model")
            
        except Exception as e:
            self.logger.error(f"Error building deep learning model: {e}")
    
    def predict(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Predict signal using deep learning model
        
        Args:
            features: Current feature vector (1D array)
            
        Returns:
            (signal, confidence) tuple
        """
        if not TENSORFLOW_AVAILABLE or self.model is None:
            return 'HOLD', 0.5
        
        try:
            # Add to buffer
            self.feature_buffer.append(features)
            
            # Need full sequence to predict
            if len(self.feature_buffer) < self.sequence_length:
                return 'HOLD', 0.3  # Low confidence until we have enough history
            
            # Prepare sequence
            sequence = np.array(list(self.feature_buffer))
            sequence = sequence.reshape(1, self.sequence_length, self.n_features)
            
            # Predict
            probabilities = self.model.predict(sequence, verbose=0)[0]
            prediction = np.argmax(probabilities)
            confidence = probabilities[prediction]
            
            signal_map = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
            signal = signal_map[prediction]
            
            return signal, float(confidence)
            
        except Exception as e:
            self.logger.error(f"Error in deep learning prediction: {e}")
            return 'HOLD', 0.5
    
    def update(self, features: np.ndarray, label: int, weight: float = 1.0):
        """
        Online learning update (not implemented for production to avoid overfitting)
        In production, should collect data and retrain periodically
        """
        # For production, we'd store training examples and retrain periodically
        # rather than online updates which can cause model drift
        pass
    
    def save(self):
        """Save model to disk"""
        if TENSORFLOW_AVAILABLE and self.model is not None:
            try:
                self.model.save(self.model_path)
                self.logger.info("Saved deep learning model")
            except Exception as e:
                self.logger.error(f"Error saving model: {e}")


class MultiTimeframeSignalFusion:
    """
    Sophisticated multi-timeframe signal fusion using weighted voting
    and temporal consistency checks
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        
        # Timeframe weights (longer timeframes have more weight for trend)
        self.timeframe_weights = {
            '1h': 0.25,
            '4h': 0.35,
            '1d': 0.40
        }
        
        # Signal history for consistency tracking
        self.signal_history = {
            '1h': deque(maxlen=5),
            '4h': deque(maxlen=3),
            '1d': deque(maxlen=2)
        }
    
    def fuse_signals(self, 
                    signals_1h: Tuple[str, float],
                    signals_4h: Tuple[str, float],
                    signals_1d: Tuple[str, float]) -> Tuple[str, float, Dict]:
        """
        Fuse multi-timeframe signals with sophisticated voting mechanism
        
        Args:
            signals_1h: (signal, confidence) for 1h timeframe
            signals_4h: (signal, confidence) for 4h timeframe
            signals_1d: (signal, confidence) for 1d timeframe
            
        Returns:
            (fused_signal, fused_confidence, details_dict)
        """
        try:
            # Map signals to numeric values
            signal_map = {'HOLD': 0, 'BUY': 1, 'SELL': -1}
            reverse_map = {0: 'HOLD', 1: 'BUY', -1: 'SELL'}
            
            # Extract signals and confidences
            sig_1h, conf_1h = signals_1h
            sig_4h, conf_4h = signals_4h
            sig_1d, conf_1d = signals_1d
            
            # Convert to numeric
            val_1h = signal_map.get(sig_1h, 0)
            val_4h = signal_map.get(sig_4h, 0)
            val_1d = signal_map.get(sig_1d, 0)
            
            # Add to history
            self.signal_history['1h'].append((val_1h, conf_1h))
            self.signal_history['4h'].append((val_4h, conf_4h))
            self.signal_history['1d'].append((val_1d, conf_1d))
            
            # Calculate weighted vote
            weighted_sum = (
                val_1h * conf_1h * self.timeframe_weights['1h'] +
                val_4h * conf_4h * self.timeframe_weights['4h'] +
                val_1d * conf_1d * self.timeframe_weights['1d']
            )
            
            total_weight = (
                conf_1h * self.timeframe_weights['1h'] +
                conf_4h * self.timeframe_weights['4h'] +
                conf_1d * self.timeframe_weights['1d']
            )
            
            if total_weight > 0:
                weighted_avg = weighted_sum / total_weight
            else:
                weighted_avg = 0
            
            # Determine fused signal
            if weighted_avg > 0.3:
                fused_signal = 'BUY'
            elif weighted_avg < -0.3:
                fused_signal = 'SELL'
            else:
                fused_signal = 'HOLD'
            
            # Calculate confidence based on agreement and consistency
            agreement_score = self._calculate_agreement(val_1h, val_4h, val_1d)
            consistency_score = self._calculate_consistency()
            
            # Fused confidence is combination of weighted average and agreement
            base_confidence = abs(weighted_avg)
            fused_confidence = (base_confidence * 0.6 + 
                              agreement_score * 0.25 + 
                              consistency_score * 0.15)
            
            # Cap confidence
            fused_confidence = min(max(fused_confidence, 0.0), 1.0)
            
            details = {
                'weighted_avg': weighted_avg,
                'agreement_score': agreement_score,
                'consistency_score': consistency_score,
                'individual_signals': {
                    '1h': (sig_1h, conf_1h),
                    '4h': (sig_4h, conf_4h),
                    '1d': (sig_1d, conf_1d)
                }
            }
            
            return fused_signal, fused_confidence, details
            
        except Exception as e:
            self.logger.error(f"Error fusing signals: {e}")
            return 'HOLD', 0.3, {}
    
    def _calculate_agreement(self, val_1h: int, val_4h: int, val_1d: int) -> float:
        """Calculate agreement score between timeframes"""
        # All agree
        if val_1h == val_4h == val_1d:
            return 1.0
        
        # Two agree
        if val_1h == val_4h or val_1h == val_1d or val_4h == val_1d:
            return 0.6
        
        # All different or mixed
        return 0.3
    
    def _calculate_consistency(self) -> float:
        """Calculate temporal consistency score"""
        try:
            consistency_sum = 0
            count = 0
            
            for timeframe, history in self.signal_history.items():
                if len(history) < 2:
                    continue
                
                # Check if recent signals are consistent
                recent_signals = [s[0] for s in list(history)[-2:]]
                if recent_signals[0] == recent_signals[1]:
                    consistency_sum += 1
                count += 1
            
            if count == 0:
                return 0.5
            
            return consistency_sum / count
            
        except Exception as e:
            self.logger.debug(f"Error calculating consistency: {e}")
            return 0.5


class AdaptiveExitStrategy:
    """
    Advanced exit strategy that adapts to market conditions and position performance
    """
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.position_states = {}  # Track state per symbol
    
    def calculate_optimal_exit(self,
                              symbol: str,
                              entry_price: float,
                              current_price: float,
                              side: str,
                              volatility: float,
                              volume_ratio: float,
                              momentum: float,
                              time_in_position: float,  # minutes
                              unrealized_pnl_pct: float) -> Dict:
        """
        Calculate optimal exit point with multiple dynamic targets
        
        Returns:
            Dict with exit recommendations and reasoning
        """
        try:
            # Initialize position state if new
            if symbol not in self.position_states:
                self.position_states[symbol] = {
                    'highest_pnl': unrealized_pnl_pct,
                    'lowest_pnl': unrealized_pnl_pct,
                    'profit_peaks': []
                }
            
            state = self.position_states[symbol]
            
            # Update tracking
            state['highest_pnl'] = max(state['highest_pnl'], unrealized_pnl_pct)
            state['lowest_pnl'] = min(state['lowest_pnl'], unrealized_pnl_pct)
            
            # Dynamic profit targets based on volatility
            # High volatility = wider targets
            base_target_1 = 0.02  # 2%
            base_target_2 = 0.04  # 4%
            base_target_3 = 0.06  # 6%
            
            vol_multiplier = 1 + (volatility - 0.03) * 5  # Scale with volatility
            vol_multiplier = max(0.5, min(vol_multiplier, 2.0))
            
            target_1 = base_target_1 * vol_multiplier
            target_2 = base_target_2 * vol_multiplier
            target_3 = base_target_3 * vol_multiplier
            
            # Dynamic trailing stop based on profit level
            if unrealized_pnl_pct > target_3:
                # Very profitable - tight trailing stop
                trailing_pct = 0.015  # 1.5%
                scale_out_pct = 0.5  # Scale out 50%
            elif unrealized_pnl_pct > target_2:
                # Good profit - moderate trailing stop
                trailing_pct = 0.02  # 2%
                scale_out_pct = 0.33  # Scale out 33%
            elif unrealized_pnl_pct > target_1:
                # Small profit - normal trailing stop
                trailing_pct = 0.025  # 2.5%
                scale_out_pct = 0.25  # Scale out 25%
            else:
                # Not yet profitable - wider stop
                trailing_pct = 0.03  # 3%
                scale_out_pct = 0.0  # No scaling yet
            
            # Calculate trailing stop from highest profit
            trailing_stop_pnl = state['highest_pnl'] - trailing_pct
            
            # Exit signals
            should_exit = False
            exit_reason = None
            exit_confidence = 0.0
            scale_out_recommendation = 0.0
            
            # Signal 1: Trailing stop hit (only if we've had some profit)
            if unrealized_pnl_pct < trailing_stop_pnl and state['highest_pnl'] > 0.01:
                should_exit = True
                exit_reason = 'trailing_stop'
                exit_confidence = 0.9
            
            # Signal 2: Momentum reversal at profit
            if unrealized_pnl_pct > target_1:
                if (side == 'long' and momentum < -0.015) or (side == 'short' and momentum > 0.015):
                    should_exit = True
                    exit_reason = 'momentum_reversal_at_profit'
                    exit_confidence = 0.85
            
            # Signal 3: Time-based exit for stagnant positions
            if time_in_position > 480:  # 8 hours
                pnl_change = abs(unrealized_pnl_pct - state['lowest_pnl'])
                if pnl_change < 0.01:  # Less than 1% movement
                    should_exit = True
                    exit_reason = 'stagnant_position'
                    exit_confidence = 0.7
            
            # Signal 4: Volume drying up at profit
            if unrealized_pnl_pct > target_1 and volume_ratio < 0.5:
                should_exit = True
                exit_reason = 'low_volume_at_profit'
                exit_confidence = 0.75
            
            # Signal 5: Exceptional profit - take some off the table
            if unrealized_pnl_pct > target_2:
                scale_out_recommendation = scale_out_pct
            
            # Signal 6: Stop loss - significant unrealized loss
            max_loss = -0.03  # -3% max loss
            if unrealized_pnl_pct < max_loss:
                should_exit = True
                exit_reason = 'stop_loss'
                exit_confidence = 1.0
            
            return {
                'should_exit': should_exit,
                'exit_reason': exit_reason,
                'exit_confidence': exit_confidence,
                'scale_out_recommendation': scale_out_recommendation,
                'dynamic_targets': {
                    'target_1': target_1,
                    'target_2': target_2,
                    'target_3': target_3
                },
                'trailing_stop_pnl': trailing_stop_pnl,
                'current_pnl': unrealized_pnl_pct,
                'highest_pnl': state['highest_pnl']
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating optimal exit: {e}")
            return {
                'should_exit': False,
                'exit_confidence': 0.0,
                'scale_out_recommendation': 0.0
            }
    
    def cleanup_position_state(self, symbol: str):
        """Clean up state after position closes"""
        if symbol in self.position_states:
            del self.position_states[symbol]


class ReinforcementLearningStrategy:
    """
    Simple Q-learning based strategy selector
    Learns which strategies work best in different market conditions
    """
    
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.95):
        self.logger = Logger.get_logger()
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        
        # Q-table: state -> action -> Q-value
        # States: market regime (5 types) + volatility level (3 levels) = 15 states
        # Actions: 4 strategies
        self.q_table = {}
        
        # Initialize Q-table
        regimes = ['bull', 'bear', 'neutral', 'high_vol', 'low_vol']
        vol_levels = ['low', 'medium', 'high']
        strategies = ['trend_following', 'mean_reversion', 'breakout', 'momentum']
        
        for regime in regimes:
            for vol in vol_levels:
                state = f"{regime}_{vol}"
                self.q_table[state] = {strategy: 0.0 for strategy in strategies}
        
        # Exploration rate
        self.epsilon = 0.2  # 20% random exploration
        self.epsilon_decay = 0.995
        self.min_epsilon = 0.05
    
    def get_state(self, market_regime: str, volatility: float) -> str:
        """Convert market conditions to state string"""
        if volatility > 0.06:
            vol_level = 'high'
        elif volatility > 0.03:
            vol_level = 'medium'
        else:
            vol_level = 'low'
        
        return f"{market_regime}_{vol_level}"
    
    def select_strategy(self, market_regime: str, volatility: float) -> str:
        """
        Select best strategy using Q-learning
        
        Args:
            market_regime: Current market regime
            volatility: Current volatility level
            
        Returns:
            Selected strategy name
        """
        state = self.get_state(market_regime, volatility)
        
        # Epsilon-greedy strategy selection
        if np.random.random() < self.epsilon:
            # Explore: random strategy
            strategies = list(self.q_table[state].keys())
            strategy = np.random.choice(strategies)
            self.logger.debug(f"Exploring: selected {strategy}")
        else:
            # Exploit: best strategy
            q_values = self.q_table[state]
            strategy = max(q_values, key=q_values.get)
            self.logger.debug(f"Exploiting: selected {strategy} (Q={q_values[strategy]:.2f})")
        
        return strategy
    
    def update_q_value(self, 
                      market_regime: str, 
                      volatility: float, 
                      strategy: str, 
                      reward: float,
                      next_market_regime: Optional[str] = None,
                      next_volatility: Optional[float] = None):
        """
        Update Q-value based on trade outcome using proper Q-learning formula
        
        Args:
            market_regime: Market regime when trade was taken
            volatility: Volatility when trade was taken
            strategy: Strategy used
            reward: Reward (profit/loss)
            next_market_regime: Market regime after action (optional)
            next_volatility: Volatility after action (optional)
        """
        state = self.get_state(market_regime, volatility)
        
        # Q-learning update
        current_q = self.q_table[state][strategy]
        
        # Proper Q-learning: use max Q-value from NEXT state
        if next_market_regime is not None and next_volatility is not None:
            next_state = self.get_state(next_market_regime, next_volatility)
            max_future_q = max(self.q_table[next_state].values())
        else:
            # If next state not available, assume terminal state (max_future_q = 0)
            # This simplifies to immediate reward-based learning
            max_future_q = 0.0
        
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_future_q - current_q
        )
        
        self.q_table[state][strategy] = new_q
        
        # Decay exploration rate
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        self.logger.debug(
            f"Updated Q-value: {state} -> {strategy}: "
            f"{current_q:.3f} -> {new_q:.3f} (reward: {reward:.3f}, max_future: {max_future_q:.3f})"
        )
    
    def save_q_table(self, path: str = 'models/q_table.pkl'):
        """Save Q-table to disk"""
        try:
            os.makedirs('models', exist_ok=True)
            joblib.dump({
                'q_table': self.q_table,
                'epsilon': self.epsilon
            }, path)
            self.logger.info("Saved Q-table")
        except Exception as e:
            self.logger.error(f"Error saving Q-table: {e}")
    
    def load_q_table(self, path: str = 'models/q_table.pkl'):
        """Load Q-table from disk"""
        try:
            if os.path.exists(path):
                data = joblib.load(path)
                self.q_table = data['q_table']
                self.epsilon = data.get('epsilon', self.epsilon)
                self.logger.info(f"Loaded Q-table (epsilon: {self.epsilon:.3f})")
        except Exception as e:
            self.logger.error(f"Error loading Q-table: {e}")
