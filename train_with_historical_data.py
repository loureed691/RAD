"""
Script to train the ML model with historical data from CSV files
"""
import sys
import os
import glob
from config import Config
from logger import Logger
from ml_model import MLModel

def train_model_with_historical_csv(csv_path: str, model_path: str = None):
    """
    Train ML model with historical data from a CSV file
    
    Args:
        csv_path: Path to CSV file with historical data
        model_path: Optional custom path for the model file
    """
    logger = Logger.setup('INFO', 'logs/train_model.log')
    
    try:
        logger.info("="*60)
        logger.info("Training ML Model with Historical Data")
        logger.info("="*60)
        logger.info(f"CSV file: {csv_path}")
        
        # Initialize ML model
        if model_path:
            model = MLModel(model_path)
        else:
            model = MLModel()
        
        logger.info(f"Model path: {model.model_path}")
        
        # Check current model state
        if model.model is not None:
            logger.info(f"Existing model loaded with {len(model.training_data)} training samples")
            logger.info(f"Current performance: Win rate {model.performance_metrics.get('win_rate', 0):.2%}, "
                       f"Trades: {model.performance_metrics.get('total_trades', 0)}")
        
        # Load historical data from CSV
        historical_data = model.load_historical_data_from_csv(csv_path)
        
        if historical_data.empty:
            logger.error("Failed to load historical data from CSV")
            return False
        
        # Train with historical data
        logger.info("Starting training with historical data...")
        success = model.train_with_historical_data(historical_data, min_samples=100)
        
        if success:
            logger.info("✓ Model training completed successfully!")
            logger.info(f"  Training samples: {len(model.training_data)}")
            logger.info(f"  Model saved to: {model.model_path}")
            
            if model.feature_importance:
                logger.info("\nTop 10 important features:")
                top_features = sorted(
                    model.feature_importance.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
                for i, (feature, importance) in enumerate(top_features, 1):
                    logger.info(f"  {i}. {feature}: {importance:.4f}")
            
            return True
        else:
            logger.error("✗ Model training failed")
            return False
            
    except Exception as e:
        logger.error(f"Error training model: {e}")
        import traceback
        traceback.print_exc()
        return False

def train_from_multiple_files(directory: str = 'historical_data', pattern: str = '*.csv'):
    """
    Train model with multiple historical data files
    
    Args:
        directory: Directory containing CSV files
        pattern: File pattern to match (default: '*.csv')
    """
    logger = Logger.setup('INFO', 'logs/train_model.log')
    
    try:
        logger.info("="*60)
        logger.info("Training ML Model with Multiple Historical Files")
        logger.info("="*60)
        
        # Find all CSV files matching pattern
        search_path = os.path.join(directory, pattern)
        csv_files = glob.glob(search_path)
        
        if not csv_files:
            logger.error(f"No CSV files found in {directory} matching {pattern}")
            return False
        
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        # Initialize ML model
        model = MLModel()
        
        # Process each file
        for i, csv_path in enumerate(csv_files, 1):
            logger.info(f"\nProcessing file {i}/{len(csv_files)}: {csv_path}")
            
            # Load historical data
            historical_data = model.load_historical_data_from_csv(csv_path)
            
            if historical_data.empty:
                logger.warning(f"Skipping {csv_path} - failed to load")
                continue
            
            # Train with this data (will accumulate training samples)
            model.train_with_historical_data(historical_data, min_samples=50)
        
        # Final training with all accumulated data
        logger.info("\nPerforming final training with all accumulated data...")
        success = model.train(min_samples=100)
        
        if success:
            logger.info("✓ Multi-file training completed successfully!")
            logger.info(f"  Total training samples: {len(model.training_data)}")
            logger.info(f"  Model saved to: {model.model_path}")
            return True
        else:
            logger.error("✗ Final training failed")
            return False
            
    except Exception as e:
        logger.error(f"Error in multi-file training: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("ML Model Training with Historical Data")
    print("="*60)
    
    if len(sys.argv) > 1:
        # Command line mode
        csv_path = sys.argv[1]
        model_path = sys.argv[2] if len(sys.argv) > 2 else None
        
        if not os.path.exists(csv_path):
            print(f"\n✗ Error: CSV file not found: {csv_path}")
            sys.exit(1)
        
        success = train_model_with_historical_csv(csv_path, model_path)
    else:
        # Interactive mode
        print("\nOptions:")
        print("  1. Train with a single CSV file")
        print("  2. Train with all CSV files in historical_data/")
        
        choice = input("\nSelect option [1 or 2]: ").strip()
        
        if choice == "2":
            # Multiple files
            directory = input("Enter directory path [default: historical_data]: ").strip()
            if not directory:
                directory = "historical_data"
            
            if not os.path.exists(directory):
                print(f"\n✗ Error: Directory not found: {directory}")
                sys.exit(1)
            
            success = train_from_multiple_files(directory)
        else:
            # Single file
            csv_files = glob.glob("historical_data/*.csv")
            
            if csv_files:
                print("\nAvailable CSV files:")
                for i, filepath in enumerate(csv_files, 1):
                    print(f"  {i}. {filepath}")
                
                file_choice = input(f"\nSelect file number [1-{len(csv_files)}] or enter path: ").strip()
                
                try:
                    idx = int(file_choice) - 1
                    if 0 <= idx < len(csv_files):
                        csv_path = csv_files[idx]
                    else:
                        csv_path = file_choice
                except ValueError:
                    csv_path = file_choice
            else:
                csv_path = input("\nEnter CSV file path: ").strip()
            
            if not os.path.exists(csv_path):
                print(f"\n✗ Error: CSV file not found: {csv_path}")
                sys.exit(1)
            
            success = train_model_with_historical_csv(csv_path)
    
    if success:
        print("\n" + "="*60)
        print("✓ Training Complete!")
        print("="*60)
        print("\nYour ML model is now trained with historical data.")
        print("You can start the bot and it will use this trained model.")
        print("\nTo start the bot: python start.py")
    else:
        print("\n✗ Training failed - check logs/train_model.log for details")
        sys.exit(1)

if __name__ == "__main__":
    main()
