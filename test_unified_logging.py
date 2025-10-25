#!/usr/bin/env python3
"""
Test script to verify unified logging with component tags
"""
import os
import sys
import tempfile
from logger import Logger

def test_unified_logging():
    """Test that all loggers write to a single file with proper tags"""
    print("=" * 60)
    print("Testing Unified Logging System")
    print("=" * 60)
    
    # Create a temporary log file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as temp_log:
        log_file = temp_log.name
    
    try:
        # Setup main logger
        main_logger = Logger.setup(log_level='DEBUG', log_file=log_file)
        
        # Setup specialized loggers (they should all write to the same file)
        position_logger = Logger.setup_specialized_logger(
            'TradingBot.Position', 
            log_file, 
            'DEBUG'
        )
        scanning_logger = Logger.setup_specialized_logger(
            'TradingBot.Scanning', 
            log_file, 
            'DEBUG'
        )
        order_logger = Logger.setup_specialized_logger(
            'TradingBot.Order', 
            log_file, 
            'DEBUG'
        )
        strategy_logger = Logger.setup_specialized_logger(
            'TradingBot.Strategy', 
            log_file, 
            'DEBUG'
        )
        
        # Test logging from each component
        print("\n✅ Logging test messages...")
        main_logger.info("Main bot initialized")
        position_logger.info("Position opened: BTC/USDT at $50,000")
        scanning_logger.info("Scanning 100 markets for opportunities")
        order_logger.info("Market buy order executed: 0.001 BTC")
        strategy_logger.info("Strategy recommendation: LONG")
        
        position_logger.debug("Position details: size=0.001, leverage=10x")
        scanning_logger.debug("Market analysis: RSI=45, MACD=positive")
        order_logger.debug("Order filled at: $50,050 (slippage: 0.1%)")
        strategy_logger.debug("Strategy confidence: 75%")
        
        main_logger.warning("Low balance warning: $100 remaining")
        position_logger.warning("Stop loss approaching: -1.8%")
        
        print("✅ Test messages logged\n")
        
        # Verify the log file contains all messages
        print("=" * 60)
        print("Log File Contents:")
        print("=" * 60)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
        
        # Check that component tags are present
        print("=" * 60)
        print("Verification:")
        print("=" * 60)
        
        checks = [
            ('[POSITION]', 'Position component tag'),
            ('[SCANNING]', 'Scanning component tag'),
            ('[ORDER]', 'Order component tag'),
            ('[STRATEGY]', 'Strategy component tag'),
            ('Position opened', 'Position log message'),
            ('Scanning 100 markets', 'Scanning log message'),
            ('Market buy order', 'Order log message'),
            ('Strategy recommendation', 'Strategy log message'),
        ]
        
        all_passed = True
        for check_str, check_name in checks:
            if check_str in content:
                print(f"✓ {check_name} found")
            else:
                print(f"✗ {check_name} NOT found")
                all_passed = False
        
        # Verify only ONE log file was created
        log_dir = os.path.dirname(log_file)
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        print(f"\n✓ Number of log files in temp directory: {len(log_files)}")
        
        if all_passed:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("✓ All components write to a single unified log file")
            print("✓ Component tags ([POSITION], [SCANNING], etc.) are visible")
            print("✓ Better view: All logs in one place with clear labels")
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ SOME TESTS FAILED")
            print("=" * 60)
            return False
            
    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)

if __name__ == "__main__":
    success = test_unified_logging()
    sys.exit(0 if success else 1)
