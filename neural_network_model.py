"""
Neural Network Model for Trading Signal Enhancement
Provides deep learning capabilities alongside traditional ML models
"""
import os
import numpy as np
from typing import Dict, Tuple, Optional
from logger import Logger

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    Logger.get_logger().warning("TensorFlow not available. Neural network features disabled.")

class NeuralNetworkModel:
    """Deep learning model for trading signal prediction"""
    
    def __init__(self, model_path: str = 'models/neural_network_model.h5'):
        self.model_path = model_path
        self.model = None
        self.logger = Logger.get_logger()
        self.input_dim = 31  # Number of features from ml_model.py
        
        if not TENSORFLOW_AVAILABLE:
            self.logger.warning("Neural network features disabled (TensorFlow not installed)")
            return
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Load existing model if available
        self.load_model()
    
    def create_model(self) -> Optional[keras.Model]:
        """Create a neural network architecture optimized for trading signals"""
        if not TENSORFLOW_AVAILABLE:
            return None
        
        try:
            model = models.Sequential([
                # Input layer with batch normalization
                layers.Dense(128, activation='relu', input_shape=(self.input_dim,)),
                layers.BatchNormalization(),
                layers.Dropout(0.3),
                
                # Hidden layers with decreasing units
                layers.Dense(64, activation='relu'),
                layers.BatchNormalization(),
                layers.Dropout(0.25),
                
                layers.Dense(32, activation='relu'),
                layers.BatchNormalization(),
                layers.Dropout(0.2),
                
                # Output layer (3 classes: HOLD, BUY, SELL)
                layers.Dense(3, activation='softmax')
            ])
            
            # Compile with Adam optimizer and categorical crossentropy
            model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=0.001),
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )
            
            self.logger.info("Created neural network model with architecture:")
            self.logger.info(f"  Input: {self.input_dim} features")
            self.logger.info("  Hidden: [128, 64, 32] with dropout and batch normalization")
            self.logger.info("  Output: 3 classes (HOLD, BUY, SELL)")
            
            return model
        except Exception as e:
            self.logger.error(f"Error creating neural network model: {e}")
            return None
    
    def load_model(self):
        """Load trained model from disk"""
        if not TENSORFLOW_AVAILABLE:
            return
        
        try:
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                self.logger.info(f"Loaded neural network model from {self.model_path}")
            else:
                self.logger.info("No existing neural network model found")
                self.model = None
        except Exception as e:
            self.logger.error(f"Error loading neural network model: {e}")
            self.model = None
    
    def save_model(self):
        """Save trained model to disk"""
        if not TENSORFLOW_AVAILABLE or self.model is None:
            return
        
        try:
            self.model.save(self.model_path)
            self.logger.info(f"Saved neural network model to {self.model_path}")
        except Exception as e:
            self.logger.error(f"Error saving neural network model: {e}")
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 50, 
              batch_size: int = 32, validation_split: float = 0.2) -> bool:
        """
        Train the neural network model
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target labels (n_samples,)
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Fraction of data to use for validation
        
        Returns:
            True if training succeeded, False otherwise
        """
        if not TENSORFLOW_AVAILABLE:
            return False
        
        try:
            # Create model if it doesn't exist
            if self.model is None:
                self.model = self.create_model()
                if self.model is None:
                    return False
            
            # Prepare callbacks
            early_stopping = callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=0
            )
            
            reduce_lr = callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=0.00001,
                verbose=0
            )
            
            # Train the model
            history = self.model.fit(
                X, y,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                callbacks=[early_stopping, reduce_lr],
                verbose=0
            )
            
            # Get final metrics
            final_loss = history.history['loss'][-1]
            final_acc = history.history['accuracy'][-1]
            final_val_loss = history.history['val_loss'][-1]
            final_val_acc = history.history['val_accuracy'][-1]
            
            self.logger.info(
                f"Neural network training complete: "
                f"loss={final_loss:.4f}, acc={final_acc:.4f}, "
                f"val_loss={final_val_loss:.4f}, val_acc={final_val_acc:.4f}"
            )
            
            # Save the trained model
            self.save_model()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training neural network: {e}")
            return False
    
    def predict(self, features: np.ndarray) -> Tuple[str, float]:
        """
        Predict trading signal using neural network
        
        Args:
            features: Feature vector (should match input_dim)
        
        Returns:
            Tuple of (signal, confidence)
            signal: 'BUY', 'SELL', or 'HOLD'
            confidence: probability of the prediction
        """
        if not TENSORFLOW_AVAILABLE or self.model is None:
            return 'HOLD', 0.0
        
        try:
            # Ensure features is 2D array
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # Get prediction probabilities
            probabilities = self.model.predict(features, verbose=0)[0]
            
            # Get predicted class and confidence
            predicted_class = int(np.argmax(probabilities))
            confidence = float(probabilities[predicted_class])
            
            # Map class to signal
            signal_map = {0: 'HOLD', 1: 'BUY', 2: 'SELL'}
            signal = signal_map.get(predicted_class, 'HOLD')
            
            return signal, confidence
            
        except Exception as e:
            self.logger.error(f"Error making neural network prediction: {e}")
            return 'HOLD', 0.0
    
    def incremental_train(self, X: np.ndarray, y: np.ndarray, 
                         epochs: int = 5, batch_size: int = 32) -> bool:
        """
        Perform incremental/online learning on new data
        
        Args:
            X: New feature matrix
            y: New target labels
            epochs: Number of epochs for incremental training
            batch_size: Batch size
        
        Returns:
            True if successful, False otherwise
        """
        if not TENSORFLOW_AVAILABLE or self.model is None:
            return False
        
        try:
            # Train on new data with fewer epochs
            self.model.fit(
                X, y,
                epochs=epochs,
                batch_size=batch_size,
                verbose=0
            )
            
            self.logger.info(f"Incremental training completed on {len(X)} new samples")
            
            # Save updated model
            self.save_model()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in incremental training: {e}")
            return False
