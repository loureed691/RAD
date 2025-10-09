"""
AutoML Module for Hyperparameter Optimization
Uses Optuna to automatically find the best model parameters
"""
import numpy as np
from typing import Dict, Any, Optional
from logger import Logger

try:
    import optuna
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    Logger.get_logger().warning("Optuna not available. AutoML features disabled.")

try:
    from xgboost import XGBClassifier
    from lightgbm import LGBMClassifier
    from catboost import CatBoostClassifier
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

class AutoML:
    """Automatic hyperparameter optimization for trading models"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
        self.best_params = None
        self.best_score = 0.0
        self.study = None
    
    def optimize_xgboost(self, X: np.ndarray, y: np.ndarray, 
                        n_trials: int = 50) -> Dict[str, Any]:
        """
        Optimize XGBoost hyperparameters using Optuna
        
        Args:
            X: Feature matrix
            y: Target labels
            n_trials: Number of optimization trials
        
        Returns:
            Dictionary with best parameters
        """
        if not OPTUNA_AVAILABLE or not ML_AVAILABLE:
            self.logger.warning("AutoML not available")
            return {}
        
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'gamma': trial.suggest_float('gamma', 0.0, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
                'random_state': 42,
                'n_jobs': -1,
                'verbosity': 0
            }
            
            model = XGBClassifier(**params)
            
            # Use 3-fold cross-validation
            scores = cross_val_score(model, X, y, cv=3, scoring='accuracy', n_jobs=-1)
            
            return scores.mean()
        
        try:
            # Create study with TPE sampler
            self.study = optuna.create_study(
                direction='maximize',
                sampler=TPESampler(seed=42)
            )
            
            # Suppress Optuna logs
            optuna.logging.set_verbosity(optuna.logging.WARNING)
            
            # Optimize
            self.logger.info(f"Starting XGBoost hyperparameter optimization ({n_trials} trials)...")
            self.study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
            
            self.best_params = self.study.best_params
            self.best_score = self.study.best_value
            
            self.logger.info(
                f"XGBoost optimization complete: "
                f"best_score={self.best_score:.4f}, "
                f"best_params={self.best_params}"
            )
            
            return self.best_params
            
        except Exception as e:
            self.logger.error(f"Error in XGBoost optimization: {e}")
            return {}
    
    def optimize_lightgbm(self, X: np.ndarray, y: np.ndarray, 
                         n_trials: int = 50) -> Dict[str, Any]:
        """
        Optimize LightGBM hyperparameters using Optuna
        
        Args:
            X: Feature matrix
            y: Target labels
            n_trials: Number of optimization trials
        
        Returns:
            Dictionary with best parameters
        """
        if not OPTUNA_AVAILABLE or not ML_AVAILABLE:
            self.logger.warning("AutoML not available")
            return {}
        
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'num_leaves': trial.suggest_int('num_leaves', 20, 100),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
                'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
                'random_state': 42,
                'n_jobs': -1,
                'verbosity': -1
            }
            
            model = LGBMClassifier(**params)
            
            # Use 3-fold cross-validation
            scores = cross_val_score(model, X, y, cv=3, scoring='accuracy', n_jobs=-1)
            
            return scores.mean()
        
        try:
            # Create study with TPE sampler
            self.study = optuna.create_study(
                direction='maximize',
                sampler=TPESampler(seed=42)
            )
            
            # Suppress Optuna logs
            optuna.logging.set_verbosity(optuna.logging.WARNING)
            
            # Optimize
            self.logger.info(f"Starting LightGBM hyperparameter optimization ({n_trials} trials)...")
            self.study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
            
            self.best_params = self.study.best_params
            self.best_score = self.study.best_value
            
            self.logger.info(
                f"LightGBM optimization complete: "
                f"best_score={self.best_score:.4f}, "
                f"best_params={self.best_params}"
            )
            
            return self.best_params
            
        except Exception as e:
            self.logger.error(f"Error in LightGBM optimization: {e}")
            return {}
    
    def optimize_ensemble(self, X: np.ndarray, y: np.ndarray,
                         n_trials: int = 30) -> Dict[str, Dict[str, Any]]:
        """
        Optimize all models in ensemble
        
        Args:
            X: Feature matrix
            y: Target labels
            n_trials: Number of trials per model
        
        Returns:
            Dictionary with best parameters for each model
        """
        if not OPTUNA_AVAILABLE or not ML_AVAILABLE:
            self.logger.warning("AutoML not available")
            return {}
        
        try:
            results = {}
            
            # Optimize XGBoost
            self.logger.info("Optimizing XGBoost...")
            results['xgboost'] = self.optimize_xgboost(X, y, n_trials)
            
            # Optimize LightGBM
            self.logger.info("Optimizing LightGBM...")
            results['lightgbm'] = self.optimize_lightgbm(X, y, n_trials)
            
            self.logger.info("Ensemble optimization complete")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in ensemble optimization: {e}")
            return {}
    
    def get_optimization_history(self) -> Optional[Dict]:
        """Get optimization history for analysis"""
        if self.study is None:
            return None
        
        try:
            trials = self.study.trials
            history = {
                'values': [trial.value for trial in trials],
                'params': [trial.params for trial in trials],
                'best_value': self.study.best_value,
                'best_params': self.study.best_params,
                'n_trials': len(trials)
            }
            return history
        except Exception as e:
            self.logger.error(f"Error getting optimization history: {e}")
            return None
