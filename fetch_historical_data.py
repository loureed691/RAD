"""
Utility script to fetch historical data from KuCoin and save it as CSV
This data can then be used to train the ML model
"""
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from config import Config
from logger import Logger
from kucoin_client import KuCoinClient

def fetch_and_save_historical_data(
    symbol: str,
    timeframe: str = '1h',
    days_back: int = 30,
    output_dir: str = 'historical_data'
):
    """
    Fetch historical OHLCV data from KuCoin and save to CSV
    
    Args:
        symbol: Trading symbol (e.g., 'BTC/USDT:USDT')
        timeframe: Candle timeframe ('1h', '4h', '1d', etc.)
        days_back: Number of days of historical data to fetch
        output_dir: Directory to save the CSV file
    """
    logger = Logger.setup('INFO', 'logs/fetch_data.log')
    
    try:
        logger.info("="*60)
        logger.info("Fetching Historical Data")
        logger.info("="*60)
        logger.info(f"Symbol: {symbol}")
        logger.info(f"Timeframe: {timeframe}")
        logger.info(f"Days back: {days_back}")
        
        # Initialize KuCoin client
        client = KuCoinClient(
            Config.API_KEY,
            Config.API_SECRET,
            Config.API_PASSPHRASE
        )
        
        # Calculate how many candles we need
        timeframe_minutes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '2h': 120,
            '4h': 240,
            '6h': 360,
            '12h': 720,
            '1d': 1440
        }
        
        minutes = timeframe_minutes.get(timeframe, 60)
        candles_per_day = 1440 / minutes
        total_candles = int(days_back * candles_per_day)
        
        # KuCoin typically limits to 200-1500 candles per request depending on timeframe
        # We'll fetch in chunks if needed
        max_candles_per_request = 1500
        all_data = []
        
        logger.info(f"Need to fetch approximately {total_candles} candles")
        
        # Fetch data in chunks
        fetched = 0
        while fetched < total_candles:
            batch_size = min(max_candles_per_request, total_candles - fetched)
            
            logger.info(f"Fetching batch: {fetched}/{total_candles} candles...")
            
            try:
                data = client.get_ohlcv(symbol, timeframe, limit=batch_size)
                
                if not data:
                    logger.warning("No data returned, stopping fetch")
                    break
                
                all_data.extend(data)
                fetched += len(data)
                
                # If we got less than requested, we've reached the end
                if len(data) < batch_size:
                    logger.info("Reached end of available historical data")
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching batch: {e}")
                break
        
        if not all_data:
            logger.error("No historical data fetched")
            return False
        
        logger.info(f"Successfully fetched {len(all_data)} candles")
        
        # Convert to DataFrame
        df = pd.DataFrame(
            all_data,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        
        # Convert timestamp to readable datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        safe_symbol = symbol.replace('/', '_').replace(':', '_')
        filename = f"{safe_symbol}_{timeframe}_{days_back}days.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        
        logger.info(f"✓ Historical data saved to: {filepath}")
        logger.info(f"  Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        logger.info(f"  Total candles: {len(df)}")
        
        print(f"\n✓ Successfully fetched and saved historical data")
        print(f"  File: {filepath}")
        print(f"  Candles: {len(df)}")
        print(f"  Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("KuCoin Historical Data Fetcher")
    print("="*60)
    
    # Check if we have command line arguments
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        timeframe = sys.argv[2] if len(sys.argv) > 2 else '1h'
        days_back = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    else:
        # Interactive mode
        print("\nFetch historical data to train the ML model")
        print("\nExamples:")
        print("  BTC/USDT:USDT")
        print("  ETH/USDT:USDT")
        
        symbol = input("\nEnter symbol (or press Enter for BTC/USDT:USDT): ").strip()
        if not symbol:
            symbol = "BTC/USDT:USDT"
        
        timeframe = input("Enter timeframe (1h, 4h, 1d) [default: 1h]: ").strip()
        if not timeframe:
            timeframe = "1h"
        
        days_input = input("Enter number of days back [default: 30]: ").strip()
        days_back = int(days_input) if days_input else 30
    
    print(f"\nFetching {days_back} days of {timeframe} data for {symbol}...")
    
    success = fetch_and_save_historical_data(symbol, timeframe, days_back)
    
    if success:
        print("\n✓ Data fetch complete!")
        print("\nNext steps:")
        print("  1. Use train_with_historical_data.py to train your model")
        print("  2. Or use the data in your own scripts")
    else:
        print("\n✗ Data fetch failed - check logs/fetch_data.log for details")
        sys.exit(1)

if __name__ == "__main__":
    main()
