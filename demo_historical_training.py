"""
Demo: Train ML Model with Historical Data

This script demonstrates the new historical data training capability.
It creates sample data, trains the model, and shows the results.
"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml_model import MLModel
from logger import Logger

def create_sample_historical_data(num_candles=300, base_price=50000):
    """Create sample OHLCV data for demonstration"""
    print(f"\n📊 Creating {num_candles} candles of sample historical data...")
    
    start_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
    
    data = []
    for i in range(num_candles):
        timestamp = start_time + i * 3600000  # 1 hour intervals
        
        # Simulate realistic price movement
        trend = i * 5 + np.random.normal(0, 50)
        noise = np.random.normal(0, 100)
        close = base_price + trend + noise
        
        high = close + abs(np.random.normal(0, 50))
        low = close - abs(np.random.normal(0, 50))
        open_price = close + np.random.normal(0, 30)
        volume = np.random.uniform(1000, 2000)
        
        data.append([timestamp, open_price, high, low, close, volume])
    
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    print(f"   ✓ Created data from {pd.to_datetime(df['timestamp'].iloc[0], unit='ms')} "
          f"to {pd.to_datetime(df['timestamp'].iloc[-1], unit='ms')}")
    
    return df

def demo_csv_training():
    """Demonstrate training with CSV file"""
    print("\n" + "="*70)
    print(" Demo 1: Training with CSV File ".center(70, "="))
    print("="*70)
    
    # Create sample data
    df = create_sample_historical_data(300)
    
    # Save to CSV
    os.makedirs('demo_data', exist_ok=True)
    csv_path = 'demo_data/sample_btc_1h.csv'
    df.to_csv(csv_path, index=False)
    print(f"\n💾 Saved sample data to: {csv_path}")
    
    # Initialize model
    model = MLModel('demo_data/demo_model.pkl')
    print(f"\n🤖 Initialized ML model at: {model.model_path}")
    
    # Load and train with CSV
    print("\n📖 Loading historical data from CSV...")
    historical_data = model.load_historical_data_from_csv(csv_path)
    print(f"   ✓ Loaded {len(historical_data)} candles")
    
    print("\n🎓 Training model with historical data...")
    success = model.train_with_historical_data(historical_data, min_samples=50)
    
    if success:
        print("\n✅ Training completed successfully!")
        print(f"   📈 Training samples: {len(model.training_data)}")
        print(f"   💾 Model saved to: {model.model_path}")
        
        # Show top features
        if model.feature_importance:
            print("\n   🎯 Top 5 most important features:")
            top_features = sorted(
                model.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            for i, (feature, importance) in enumerate(top_features, 1):
                print(f"      {i}. {feature}: {importance:.4f}")
    else:
        print("\n❌ Training failed")
    
    return success

def demo_direct_training():
    """Demonstrate training with direct data (list format)"""
    print("\n" + "="*70)
    print(" Demo 2: Training with Direct OHLCV Data ".center(70, "="))
    print("="*70)
    
    # Create sample data as list (like exchange API returns)
    print("\n📊 Creating sample OHLCV data (like from exchange)...")
    
    num_candles = 250
    start_time = int((datetime.now() - timedelta(days=25)).timestamp() * 1000)
    base_price = 45000
    
    ohlcv_list = []
    for i in range(num_candles):
        timestamp = start_time + i * 3600000
        close = base_price + i * 8 + np.random.normal(0, 80)
        high = close + abs(np.random.normal(0, 40))
        low = close - abs(np.random.normal(0, 40))
        open_price = close + np.random.normal(0, 25)
        volume = np.random.uniform(900, 1900)
        
        ohlcv_list.append([timestamp, open_price, high, low, close, volume])
    
    print(f"   ✓ Created {len(ohlcv_list)} candles")
    
    # Initialize model
    model = MLModel('demo_data/demo_model2.pkl')
    print(f"\n🤖 Initialized ML model at: {model.model_path}")
    
    # Train directly with list
    print("\n🎓 Training model with OHLCV list data...")
    success = model.train_with_historical_data(ohlcv_list, min_samples=50)
    
    if success:
        print("\n✅ Training completed successfully!")
        print(f"   📈 Training samples: {len(model.training_data)}")
        
        # Test prediction
        print("\n🔮 Testing model predictions...")
        sample_indicators = {
            'rsi': 55,
            'macd': 0.5,
            'macd_signal': 0.3,
            'macd_diff': 0.2,
            'stoch_k': 60,
            'stoch_d': 55,
            'bb_width': 0.04,
            'volume_ratio': 1.3,
            'momentum': 0.015,
            'roc': 1.5,
            'atr': 2.0,
            'close': 51000,
            'bb_high': 51200,
            'bb_low': 50800,
            'bb_mid': 51000,
            'ema_12': 50900,
            'ema_26': 50800
        }
        
        signal, confidence = model.predict(sample_indicators)
        print(f"   🎯 Prediction: {signal}")
        print(f"   📊 Confidence: {confidence:.2%}")
    else:
        print("\n❌ Training failed")
    
    return success

def demo_performance_metrics():
    """Demonstrate performance metrics"""
    print("\n" + "="*70)
    print(" Demo 3: Model Performance Metrics ".center(70, "="))
    print("="*70)
    
    # Load a trained model
    if not os.path.exists('demo_data/demo_model.pkl'):
        print("\n⚠️  No trained model found, training first...")
        demo_csv_training()
    
    model = MLModel('demo_data/demo_model.pkl')
    
    print("\n📊 Model Performance Metrics:")
    metrics = model.get_performance_metrics()
    
    print(f"   Total trades: {metrics.get('total_trades', 0)}")
    print(f"   Win rate: {metrics.get('win_rate', 0):.2%}")
    print(f"   Wins: {metrics.get('wins', 0)}")
    print(f"   Losses: {metrics.get('losses', 0)}")
    print(f"   Average profit: {metrics.get('avg_profit', 0):.2%}")
    print(f"   Average loss: {metrics.get('avg_loss', 0):.2%}")
    
    print("\n🎯 Adaptive Confidence Threshold:")
    threshold = model.get_adaptive_confidence_threshold()
    print(f"   Current threshold: {threshold:.2f}")
    print(f"   (Adjusts based on win rate)")
    
    return True

def main():
    """Run all demos"""
    print("\n" + "="*70)
    print(" Historical Data Training - Complete Demo ".center(70, "="))
    print("="*70)
    print("\nThis demo shows how to train the ML model with historical data.")
    print("It demonstrates three different approaches:")
    print("  1. Training with CSV files")
    print("  2. Training with direct OHLCV data")
    print("  3. Viewing performance metrics")
    
    input("\nPress Enter to start the demos...")
    
    # Run demos
    results = []
    
    try:
        results.append(demo_csv_training())
        input("\nPress Enter to continue to Demo 2...")
        
        results.append(demo_direct_training())
        input("\nPress Enter to continue to Demo 3...")
        
        results.append(demo_performance_metrics())
        
        # Summary
        print("\n" + "="*70)
        print(" Demo Summary ".center(70, "="))
        print("="*70)
        
        if all(results):
            print("\n✅ All demos completed successfully!")
            print("\n📚 Next Steps:")
            print("   1. Read HISTORICAL_DATA_TRAINING.md for full documentation")
            print("   2. Use fetch_historical_data.py to get real exchange data")
            print("   3. Use train_with_historical_data.py to train your model")
            print("   4. Start the bot with python start.py")
            
            print("\n📁 Demo files created:")
            print("   - demo_data/sample_btc_1h.csv (sample data)")
            print("   - demo_data/demo_model.pkl (trained model 1)")
            print("   - demo_data/demo_model2.pkl (trained model 2)")
            
            print("\n🗑️  To clean up demo files: rm -rf demo_data/")
        else:
            print("\n⚠️  Some demos failed - check the output above")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
