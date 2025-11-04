"""
Machine Learning model for signal optimization
"""
import os
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None
try:
    from lightgbm import LGBMClassifier
except ImportError:
    LGBMClassifier = None
try:
    from catboost import CatBoostClassifier
except ImportError:
    CatBoostClassifier = None
from logger import Logger

class MLModel:
    """Self-learning ML model for optimizing trading signals with modern gradient boosting ensemble (XGBoost/LightGBM/CatBoost)"""

    # Feature names for ML model - used for training and prediction
    FEATURE_NAMES = [
        'rsi', 'macd', 'macd_signal', 'macd_diff', 'stoch_k', 'stoch_d',
        'bb_width', 'volume_ratio', 'momentum', 'roc', 'atr',
        'rsi_strength', 'macd_strength', 'stoch_momentum', 'volume_surge',
        'volatility_norm', 'rsi_zone', 'macd_bullish', 'momentum_flag',
        'bb_position', 'price_to_ema12', 'price_to_ema26', 'ema_separation',
        'rsi_momentum', 'volume_trend', 'volatility_regime', 'sentiment_score',
        'momentum_accel', 'mtf_trend', 'breakout_potential', 'mean_reversion'
    ]

    def __init__(self, model_path: str = 'models/signal_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()

        # Initialize logger first (needed for logging in _configure_scaler_output)
        self.logger = Logger.get_logger()

        # Configure scaler to output pandas DataFrames (sklearn 1.5+)
        # This preserves feature names and eliminates sklearn warnings
        self._configure_scaler_output()

        self.training_data = []
        self.feature_importance = {}
        self.performance_metrics = {
            'win_rate': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'recent_trades': []  # Track last 20 trades for momentum
        }

        # 2025 AI Enhancement: Attention-based feature selection
        self.attention_selector = None  # Will be set by bot if available

        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Load existing model if available
        self.load_model()

    def _configure_scaler_output(self):
        """
        Configure StandardScaler to output pandas DataFrames (sklearn 1.5+)
        This preserves feature names and eliminates sklearn warnings about
        "X has feature names, but StandardScaler was fitted without feature names"
        """
        if hasattr(self.scaler, 'set_output'):
            try:
                self.scaler.set_output(transform='pandas')
                self.logger.debug("Configured StandardScaler to preserve feature names")
            except Exception as e:
                self.logger.debug(f"Could not configure scaler output: {e}")

    def load_model(self):
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                saved_data = joblib.load(self.model_path)
                self.model = saved_data['model']
                self.scaler = saved_data['scaler']

                # CRITICAL: Configure loaded scaler to output pandas DataFrames (sklearn 1.5+)
                # This must be done after loading to ensure feature names are preserved
                # and to eliminate sklearn warnings about feature names mismatch
                self._configure_scaler_output()

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
        """Prepare enhanced feature vector from indicators with advanced derived features"""
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

        # Calculate trend acceleration (change in momentum)
        prev_momentum = indicators.get('momentum_prev', None)
        momentum_acceleration = momentum - prev_momentum if prev_momentum is not None else 0

        # Calculate sentiment score from price action
        # Positive sentiment: price above MA, rising volume, strong momentum
        sentiment_score = 0
        if close > ema_12:
            sentiment_score += 0.3
        if close > ema_26:
            sentiment_score += 0.2
        if volume_ratio > 1.2:
            sentiment_score += 0.2
        if momentum > 0.01:
            sentiment_score += 0.3
        # Negative sentiment
        if close < ema_12:
            sentiment_score -= 0.3
        if close < ema_26:
            sentiment_score -= 0.2
        if volume_ratio < 0.8:
            sentiment_score -= 0.2
        if momentum < -0.01:
            sentiment_score -= 0.3

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
            # Price position in BB (0-1, 0.5 = middle)
            (close - bb_low) / (bb_high - bb_low) if (bb_high - bb_low) > 0 else 0.5,
            # Distance from EMA (trend strength)
            (close - ema_12) / ema_12 if ema_12 > 0 else 0,
            (close - ema_26) / ema_26 if ema_26 > 0 else 0,
            # EMA separation (trend divergence)
            (ema_12 - ema_26) / ema_26 if ema_26 > 0 else 0,
            # RSI momentum (rate of change)
            indicators.get('rsi_prev', rsi) - rsi if 'rsi_prev' in indicators else 0,
            # Volume trend
            1 if volume_ratio > 1.2 else (-1 if volume_ratio < 0.8 else 0),
            # Volatility regime
            1 if bb_width > 0.05 else (-1 if bb_width < 0.02 else 0),
            # NEW: Sentiment score (price action based)
            sentiment_score,
            # NEW: Momentum acceleration (trend strength change)
            momentum_acceleration,
            # NEW: Multi-timeframe trend alignment indicator
            1 if (close > sma_20 and sma_20 > sma_50) else (-1 if (close < sma_20 and sma_20 < sma_50) else 0),
            # NEW: Breakout potential (price near BB bands with low volatility)
            1 if (close > 0 and abs(close - bb_high) / close < 0.01 and bb_width < 0.03) else 0,
            # NEW: Mean reversion signal (price far from MA with high volatility)
            1 if (close > 0 and abs(close - bb_mid) / close > 0.03 and bb_width > 0.05) else 0,
        ]
        return np.array(features).reshape(1, -1)

    def predict(self, indicators: Dict) -> Tuple[str, float]:
        """
        Predict trading signal using ML model with 2025 attention-based feature weighting

        Returns:
            Tuple of (signal, confidence)
            signal: 'BUY', 'SELL', or 'HOLD'
            confidence: probability of the prediction
        """
        if self.model is None:
            return 'HOLD', 0.0

        try:
            features = self.prepare_features(indicators)

            # Ensure features are 2D for DataFrame creation
            if features.ndim == 1:
                features = features.reshape(1, -1)

            # Validate feature length matches expected
            if features.shape[1] != len(self.FEATURE_NAMES):
                self.logger.warning(f"Feature length mismatch: expected {len(self.FEATURE_NAMES)}, got {features.shape[1]}")
                return 'HOLD', 0.0

            # Convert features to DataFrame with feature names BEFORE attention weighting
            # This ensures feature names are preserved throughout the pipeline
            features_df = pd.DataFrame(features, columns=self.FEATURE_NAMES)

            # 2025 AI ENHANCEMENT: Apply attention-based feature weighting if available
            if self.attention_selector is not None:
                try:
                    # Apply attention weighting to features while preserving DataFrame structure
                    # Extract values, apply attention, then recreate DataFrame with same columns
                    features_array = features_df.values.flatten()
                    weighted_features = self.attention_selector.apply_attention(features_array)
                    features_df = pd.DataFrame(weighted_features.reshape(1, -1), columns=self.FEATURE_NAMES)

                    self.logger.debug("Applied attention-based feature weighting")
                except Exception as e:
                    self.logger.debug(f"Attention feature weighting error: {e}, using standard features")

            # Scale features - scaler configured with set_output('pandas') returns DataFrame
            # This maintains feature names and eliminates sklearn warnings
            features_scaled = self.scaler.transform(features_df)

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

        # Track recent trades for momentum-based threshold adjustment (last 20 trades)
        recent_trades = self.performance_metrics.get('recent_trades', [])
        recent_trades.append(profit_loss)
        if len(recent_trades) > 20:
            recent_trades = recent_trades[-20:]
        self.performance_metrics['recent_trades'] = recent_trades

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
        """Train or retrain the model with modern gradient boosting ensemble (XGBoost/LightGBM/CatBoost) for improved accuracy and speed"""
        if len(self.training_data) < min_samples:
            self.logger.info(f"Not enough training data ({len(self.training_data)}/{min_samples})")
            return False

        try:
            self.logger.info(f"Training modern gradient boosting ensemble with {len(self.training_data)} samples...")

            # Validate feature consistency
            expected_features = len(self.FEATURE_NAMES)
            if self.training_data:
                actual_features = len(self.training_data[0]['features'])
                if actual_features != expected_features:
                    self.logger.error(f"Feature length mismatch: expected {expected_features}, got {actual_features}")
                    return False

            # Prepare data as DataFrame with feature names
            X = pd.DataFrame([d['features'] for d in self.training_data], columns=self.FEATURE_NAMES)
            y = np.array([d['label'] for d in self.training_data])

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
            )

            # Scale features - scaler configured with set_output('pandas') returns DataFrames
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Create ensemble model with modern gradient boosting algorithms
            # XGBoost: Fastest and most accurate gradient boosting with GPU support
            xgb_model = XGBClassifier(
                n_estimators=100,  # Reduced from 150 for faster training
                max_depth=5,  # Reduced from 6 for regularization
                learning_rate=0.15,  # Increased from 0.1 for faster convergence
                subsample=0.8,
                colsample_bytree=0.8,
                tree_method='hist',  # Faster histogram-based algorithm
                enable_categorical=False,
                random_state=42,
                n_jobs=-1,  # Use all CPU cores
                verbosity=0  # Suppress warnings
            )

            # LightGBM: Fast gradient boosting with leaf-wise growth
            lgb_model = LGBMClassifier(
                n_estimators=100,  # Reduced from 150 for faster training
                max_depth=5,
                learning_rate=0.15,
                subsample=0.8,
                colsample_bytree=0.8,
                num_leaves=31,  # LightGBM-specific parameter
                random_state=42,
                n_jobs=-1,
                verbosity=-1  # Suppress warnings
            )

            # CatBoost: Handles categorical features natively, robust to overfitting
            cat_model = CatBoostClassifier(
                iterations=100,  # Reduced from 150 for faster training
                depth=5,
                learning_rate=0.15,
                random_state=42,
                thread_count=-1,  # Use all CPU cores
                verbose=False  # Suppress output
            )

            # Use VotingClassifier for ensemble approach (soft voting for probabilities)
            # Combine all three modern gradient boosting methods for maximum accuracy
            ensemble = VotingClassifier(
                estimators=[
                    ('xgb', xgb_model),
                    ('lgb', lgb_model),
                    ('cat', cat_model)
                ],
                voting='soft',  # Use probability averaging
                weights=[3, 2, 2]  # Give more weight to XGBoost (fastest and most reliable)
            )

            # Calibrate the ensemble for better probability estimates
            self.model = CalibratedClassifierCV(ensemble, cv=3, method='sigmoid')
            self.model.fit(X_train_scaled, y_train)

            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)

            # Get feature importance from the base XGBoost model
            try:
                # Access the base estimator through CalibratedClassifierCV
                base_estimator = self.model.calibrated_classifiers_[0].estimator.estimators_[0]  # Get fitted XGBoost from VotingClassifier inside CalibratedClassifierCV
                if hasattr(base_estimator, 'feature_importances_'):
                    importances = base_estimator.feature_importances_
                    self.feature_importance = {name: float(imp) for name, imp in zip(self.FEATURE_NAMES, importances)}

                    # Log top 5 features
                    top_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
                    self.logger.info(f"Top features: {', '.join([f'{k}:{v:.3f}' for k, v in top_features])}")
            except Exception as e:
                self.logger.debug(f"Could not extract feature importance: {e}")

            self.logger.info(f"Modern gradient boosting ensemble trained - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")

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
        Calculate adaptive confidence threshold based on model performance and recent momentum

        Returns:
            Adjusted confidence threshold (0.55-0.80) - MORE CONSERVATIVE FOR PROFITABILITY
        """
        base_threshold = 0.65  # INCREASED from 0.6 for better quality

        # Adjust based on overall win rate
        win_rate = self.performance_metrics.get('win_rate', 0.5)
        total_trades = self.performance_metrics.get('total_trades', 0)

        # Need minimum trades for reliable adjustment (INCREASED from 10 to 20)
        if total_trades < 20:
            return 0.70  # Very conservative when learning

        # Calculate recent momentum (last 20 trades)
        recent_trades = self.performance_metrics.get('recent_trades', [])
        if len(recent_trades) >= 10:
            recent_wins = sum(1 for pnl in recent_trades if pnl > 0.005)
            recent_win_rate = recent_wins / len(recent_trades)

            # Recent momentum is strong - can be more aggressive
            if recent_win_rate > 0.70:  # INCREASED from 0.65
                momentum_adjustment = -0.08  # Lower threshold when hot
            # Recent momentum is weak - be more conservative
            elif recent_win_rate < 0.40:  # INCREASED from 0.35
                momentum_adjustment = 0.15  # INCREASED from 0.12 - Higher threshold when cold
            # Recent momentum is neutral
            else:
                momentum_adjustment = 0.0
        else:
            momentum_adjustment = 0.0

        # Adjust based on overall win rate (longer term trend)
        if win_rate > 0.65:  # INCREASED from 0.6
            # If winning more overall, can be slightly more aggressive
            win_rate_adjustment = -0.03
        elif win_rate < 0.45:  # INCREASED from 0.4
            # If losing more overall, be more conservative
            win_rate_adjustment = 0.12  # INCREASED from 0.08
        else:
            win_rate_adjustment = 0.0

        # Combine adjustments with recent momentum weighted more heavily
        threshold = base_threshold + (momentum_adjustment * 0.6) + (win_rate_adjustment * 0.4)

        # Ensure threshold stays within bounds - MORE CONSERVATIVE RANGE
        threshold = max(0.55, min(threshold, 0.80))  # Changed from 0.52-0.75 to 0.55-0.80

        return threshold
