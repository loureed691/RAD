#!/usr/bin/env python3
"""
Test script to verify enhanced logging system
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logger_setup():
    """Test that loggers are set up correctly"""
    print("\n" + "="*60)
    print("Testing Enhanced Logging System")
    print("="*60)
    
    try:
        from logger import Logger
        from config import Config
        
        # Test main logger
        print("\n1. Testing main logger setup...")
        main_logger = Logger.setup(Config.LOG_LEVEL, Config.LOG_FILE)
        print(f"   ✓ Main logger created: {Config.LOG_FILE}")
        
        # Test position logger
        print("\n2. Testing position logger setup...")
        position_logger = Logger.setup_specialized_logger(
            'PositionLogger',
            Config.POSITION_LOG_FILE,
            Config.DETAILED_LOG_LEVEL
        )
        print(f"   ✓ Position logger created: {Config.POSITION_LOG_FILE}")
        
        # Test scanning logger
        print("\n3. Testing scanning logger setup...")
        scanning_logger = Logger.setup_specialized_logger(
            'ScanningLogger',
            Config.SCANNING_LOG_FILE,
            Config.DETAILED_LOG_LEVEL
        )
        print(f"   ✓ Scanning logger created: {Config.SCANNING_LOG_FILE}")
        
        # Test writing to each logger
        print("\n4. Testing log writing...")
        
        main_logger.info("Test message to main log")
        print("   ✓ Main log: INFO message written")
        
        position_logger.info("Test position opening")
        position_logger.debug("Test position details")
        print("   ✓ Position log: INFO and DEBUG messages written")
        
        scanning_logger.info("Test market scan")
        scanning_logger.debug("Test pair analysis")
        print("   ✓ Scanning log: INFO and DEBUG messages written")
        
        # Verify files were created
        print("\n5. Verifying log files...")
        log_files = [
            Config.LOG_FILE,
            Config.POSITION_LOG_FILE,
            Config.SCANNING_LOG_FILE
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                size = os.path.getsize(log_file)
                print(f"   ✓ {log_file} exists ({size} bytes)")
            else:
                print(f"   ✗ {log_file} does not exist")
                return False
        
        # Read and display sample content
        print("\n6. Sample log content:")
        
        print(f"\n   Main Log ({Config.LOG_FILE}):")
        with open(Config.LOG_FILE, 'r') as f:
            lines = f.readlines()[-3:]
            for line in lines:
                print(f"      {line.rstrip()}")
        
        print(f"\n   Position Log ({Config.POSITION_LOG_FILE}):")
        with open(Config.POSITION_LOG_FILE, 'r') as f:
            lines = f.readlines()[-3:]
            for line in lines:
                print(f"      {line.rstrip()}")
        
        print(f"\n   Scanning Log ({Config.SCANNING_LOG_FILE}):")
        with open(Config.SCANNING_LOG_FILE, 'r') as f:
            lines = f.readlines()[-3:]
            for line in lines:
                print(f"      {line.rstrip()}")
        
        print("\n" + "="*60)
        print("✓ All logging tests passed!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_position_manager_logging():
    """Test position manager logging without actual API calls"""
    print("\n" + "="*60)
    print("Testing Position Manager Logging")
    print("="*60)
    
    try:
        from logger import Logger
        from config import Config
        
        # Setup loggers
        Logger.setup(Config.LOG_LEVEL, Config.LOG_FILE)
        Logger.setup_specialized_logger(
            'PositionLogger',
            Config.POSITION_LOG_FILE,
            Config.DETAILED_LOG_LEVEL
        )
        
        position_logger = Logger.get_position_logger()
        
        # Simulate position opening log
        print("\n1. Simulating position opening log...")
        position_logger.info("="*80)
        position_logger.info("OPENING POSITION: BTCUSDT")
        position_logger.info("  Signal: BUY (LONG)")
        position_logger.info("  Amount: 0.1000 contracts")
        position_logger.info("  Leverage: 10x")
        position_logger.info("  Current Price: 45000.00")
        position_logger.info("  Stop Loss: 44550.00 (-1.00%)")
        position_logger.info("  Take Profit: 45900.00 (+2.00%)")
        position_logger.info(f"✓ Position opened successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        position_logger.info("="*80)
        print("   ✓ Position opening logged")
        
        # Simulate position update log
        print("\n2. Simulating position update log...")
        position_logger.info("\n"+"="*80)
        position_logger.info("UPDATING 1 OPEN POSITION(S) - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        position_logger.info("="*80)
        position_logger.info("\n--- Position: BTCUSDT (LONG) ---")
        position_logger.info("  Current Price: 45200.00")
        position_logger.info("  Current P/L: +4.44% ($200.00)")
        position_logger.debug("  Market Indicators:")
        position_logger.debug("    Volatility: 0.0350")
        position_logger.debug("    Momentum: +0.0150")
        position_logger.debug("    RSI: 62.50")
        position_logger.info("  🔄 Trailing stop updated: 44550.00 -> 44650.00")
        position_logger.info("  ✓ Position still open and healthy")
        position_logger.info("="*80 + "\n")
        print("   ✓ Position update logged")
        
        # Simulate position closing log
        print("\n3. Simulating position closing log...")
        position_logger.info("\n"+"="*80)
        position_logger.info("CLOSING POSITION: BTCUSDT")
        position_logger.info("  Reason: take_profit")
        position_logger.info("  Side: LONG")
        position_logger.info("  Entry Price: 45000.00")
        position_logger.info("  Exit Price: 45900.00")
        position_logger.info("  P/L: +20.00% ($900.00)")
        position_logger.info("  Duration: 45.5 minutes")
        position_logger.info(f"✓ Position closed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        position_logger.info("="*80 + "\n")
        print("   ✓ Position closing logged")
        
        print("\n" + "="*60)
        print("✓ Position manager logging tests passed!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_market_scanner_logging():
    """Test market scanner logging without actual API calls"""
    print("\n" + "="*60)
    print("Testing Market Scanner Logging")
    print("="*60)
    
    try:
        from logger import Logger
        from config import Config
        
        # Setup loggers
        Logger.setup(Config.LOG_LEVEL, Config.LOG_FILE)
        Logger.setup_specialized_logger(
            'ScanningLogger',
            Config.SCANNING_LOG_FILE,
            Config.DETAILED_LOG_LEVEL
        )
        
        scanning_logger = Logger.get_scanning_logger()
        
        # Simulate market scan start
        print("\n1. Simulating market scan start...")
        scanning_logger.info("\n"+"="*80)
        scanning_logger.info("FULL MARKET SCAN - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        scanning_logger.info("="*80)
        scanning_logger.info("Total futures contracts: 150")
        scanning_logger.info("Filtered to 50 high-priority pairs")
        scanning_logger.info("Max workers: 10")
        scanning_logger.info("\nScanning pairs in parallel...")
        print("   ✓ Scan start logged")
        
        # Simulate individual pair scans
        print("\n2. Simulating pair scan logs...")
        pairs = [
            ("BTCUSDT", "BUY", 8.5, 0.75),
            ("ETHUSDT", "SELL", 7.2, 0.68),
            ("BNBUSDT", "HOLD", 3.5, 0.42),
        ]
        
        for symbol, signal, score, confidence in pairs:
            scanning_logger.debug(f"--- Scanning {symbol} ---")
            scanning_logger.debug("  Fetching OHLCV data...")
            scanning_logger.debug("  1h data: 100 candles")
            scanning_logger.debug("  4h data: 50 candles")
            scanning_logger.debug("  Calculating indicators...")
            scanning_logger.debug("  Generating trading signal...")
            scanning_logger.info(f"  Result: Signal={signal}, Score={score:.2f}, Confidence={confidence:.2%}")
            
            if signal != "HOLD":
                scanning_logger.info(f"✓ Found opportunity: {symbol} - {signal} (score: {score:.2f}, confidence: {confidence:.2%})")
        
        print("   ✓ Pair scans logged")
        
        # Simulate scan summary
        print("\n3. Simulating scan summary...")
        scanning_logger.info("\n"+"="*40)
        scanning_logger.info("SCAN SUMMARY")
        scanning_logger.info("="*40)
        scanning_logger.info("Pairs scanned: 50")
        scanning_logger.info("Opportunities found: 2")
        scanning_logger.info("\nTop opportunities:")
        scanning_logger.info("  1. BTCUSDT: BUY (score: 8.50, conf: 75.00%)")
        scanning_logger.info("  2. ETHUSDT: SELL (score: 7.20, conf: 68.00%)")
        scanning_logger.info("="*80 + "\n")
        print("   ✓ Scan summary logged")
        
        print("\n" + "="*60)
        print("✓ Market scanner logging tests passed!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# Enhanced Logging System Test Suite")
    print("#"*60)
    
    tests = [
        ("Logger Setup", test_logger_setup),
        ("Position Manager Logging", test_position_manager_logging),
        ("Market Scanner Logging", test_market_scanner_logging),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            results.append((name, False))
    
    # Print summary
    print("\n\n" + "#"*60)
    print("# TEST SUMMARY")
    print("#"*60)
    
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        return 0
    else:
        print(f"\n✗✗✗ {total - passed} TEST(S) FAILED ✗✗✗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
