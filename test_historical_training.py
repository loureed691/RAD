"""
Test historical training functionality
"""
import sys
import os
from datetime import datetime
from config import Config
from logger import Logger
from ml_model import MLModel
from historical_trainer import HistoricalTrainer


class MockKuCoinClient:
    """Mock KuCoin client for testing"""
    
    def __init__(self):
        self.logger = Logger.get_logger()
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100):
        """Return mock OHLCV data for testing"""
        self.logger.info(f"Mock: Fetching {limit} candles for {symbol}")
        
        # Generate synthetic OHLCV data
        import random
        base_price = 50000 if 'BTC' in symbol else 3000
        ohlcv = []
        
        for i in range(limit):
            # Simulate price movement with trend and noise
            trend = i * 0.01 * base_price / limit
            noise = random.uniform(-0.02, 0.02) * base_price
            close = base_price + trend + noise
            high = close + random.uniform(0, 0.01) * base_price
            low = close - random.uniform(0, 0.01) * base_price
            open_price = close + random.uniform(-0.005, 0.005) * base_price
            volume = random.uniform(900, 1100)
            timestamp = (datetime.now().timestamp() - (limit - i) * 3600) * 1000
            
            ohlcv.append([timestamp, open_price, high, low, close, volume])
        
        return ohlcv


def test_historical_trainer():
    """Test the historical trainer"""
    print("\n" + "=" * 60)
    print("Testing Historical Trainer")
    print("=" * 60)
    
    # Setup logger
    logger = Logger.setup('INFO', 'logs/test_historical_training.log')
    
    # Create mock client
    client = MockKuCoinClient()
    
    # Create ML model
    ml_model = MLModel('models/test_historical_model.pkl')
    
    # Create trainer
    trainer = HistoricalTrainer(client, ml_model)
    
    # Test fetching historical data
    print("\n1. Testing historical data fetch...")
    ohlcv = trainer.fetch_historical_data('BTC/USDT:USDT', '1h', 7)
    
    if ohlcv and len(ohlcv) > 0:
        print(f"✓ Fetched {len(ohlcv)} candles")
    else:
        print("✗ Failed to fetch historical data")
        return False
    
    # Test generating training samples
    print("\n2. Testing training sample generation...")
    samples = trainer.generate_training_samples(ohlcv, 'BTC/USDT:USDT')
    
    if samples > 0:
        print(f"✓ Generated {samples} training samples")
    else:
        print("✗ Failed to generate training samples")
        return False
    
    # Test full training
    print("\n3. Testing full historical training...")
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT']
    success = trainer.train_from_history(
        symbols=symbols,
        timeframe='1h',
        days=7,
        min_samples=10
    )
    
    if success:
        print("✓ Historical training completed successfully")
    else:
        print("✗ Historical training failed")
        return False
    
    # Check model state
    print("\n4. Checking ML model state...")
    metrics = ml_model.get_performance_metrics()
    print(f"   Training data: {len(ml_model.training_data)} samples")
    print(f"   Model trained: {'Yes' if ml_model.model is not None else 'No'}")
    
    if ml_model.model is not None:
        print("✓ ML model successfully trained with historical data")
    else:
        print("✗ ML model not trained")
        return False
    
    # Test predictions
    print("\n5. Testing predictions with trained model...")
    if ohlcv and len(ohlcv) > 50:
        from indicators import Indicators
        df = Indicators.calculate_all(ohlcv)
        if not df.empty:
            indicators = Indicators.get_latest_indicators(df)
            signal, confidence = ml_model.predict(indicators)
            print(f"   Prediction: {signal} (confidence: {confidence:.2%})")
            print("✓ Model can make predictions")
        else:
            print("⚠️  Could not calculate indicators for prediction test")
    else:
        print("⚠️  Insufficient data for prediction test")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    
    # Cleanup test model
    try:
        if os.path.exists('models/test_historical_model.pkl'):
            os.remove('models/test_historical_model.pkl')
            print("\n✓ Test model file cleaned up")
    except Exception as e:
        print(f"\n⚠️  Could not clean up test model: {e}")
    
    return True


def test_configuration():
    """Test configuration options"""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    
    print(f"ENABLE_HISTORICAL_TRAINING: {Config.ENABLE_HISTORICAL_TRAINING}")
    print(f"HISTORICAL_TRAINING_SYMBOLS: {Config.HISTORICAL_TRAINING_SYMBOLS}")
    print(f"HISTORICAL_TRAINING_TIMEFRAME: {Config.HISTORICAL_TRAINING_TIMEFRAME}")
    print(f"HISTORICAL_TRAINING_DAYS: {Config.HISTORICAL_TRAINING_DAYS}")
    print(f"HISTORICAL_TRAINING_MIN_SAMPLES: {Config.HISTORICAL_TRAINING_MIN_SAMPLES}")
    
    print("\n✓ Configuration loaded successfully")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Historical Training Test Suite")
    print("=" * 60)
    
    try:
        # Test configuration
        if not test_configuration():
            print("\n✗ Configuration test failed")
            sys.exit(1)
        
        # Test historical trainer
        if not test_historical_trainer():
            print("\n✗ Historical trainer test failed")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nHistorical training is working correctly!")
        print("The bot will automatically train on startup using KuCoin data.")
        
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
