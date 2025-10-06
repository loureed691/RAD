#!/usr/bin/env python3
"""
Test script to verify orders logging functionality
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_orders_logger_setup():
    """Test that orders logger is set up correctly"""
    print("\n" + "="*60)
    print("Testing Orders Logging System")
    print("="*60)
    
    try:
        from logger import Logger
        from config import Config
        
        # Test orders logger setup
        print("\n1. Testing orders logger setup...")
        orders_logger = Logger.setup_specialized_logger(
            'OrdersLogger',
            Config.ORDERS_LOG_FILE,
            Config.DETAILED_LOG_LEVEL
        )
        print(f"   ✓ Orders logger created: {Config.ORDERS_LOG_FILE}")
        
        # Test writing to orders logger
        print("\n2. Testing log writing...")
        
        orders_logger.info("=" * 80)
        orders_logger.info("BUY ORDER EXECUTED: BTC/USDT:USDT")
        orders_logger.info("-" * 80)
        orders_logger.info("  Order ID: test_order_12345")
        orders_logger.info("  Type: MARKET")
        orders_logger.info("  Side: BUY")
        orders_logger.info("  Symbol: BTC/USDT:USDT")
        orders_logger.info("  Amount: 0.001 contracts")
        orders_logger.info("  Leverage: 10x")
        orders_logger.info("  Reference Price: 50000.00")
        orders_logger.info("  Average Fill Price: 50050.00")
        orders_logger.info("  Filled Amount: 0.001")
        orders_logger.info("  Total Cost: 50.05")
        orders_logger.info("  Status: closed")
        orders_logger.info("  Timestamp: 1234567890")
        orders_logger.info("  Slippage: 0.1000%")
        orders_logger.info("=" * 80)
        orders_logger.info("")
        
        orders_logger.info("=" * 80)
        orders_logger.info("SELL ORDER CREATED: ETH/USDT:USDT")
        orders_logger.info("-" * 80)
        orders_logger.info("  Order ID: test_order_67890")
        orders_logger.info("  Type: LIMIT")
        orders_logger.info("  Side: SELL")
        orders_logger.info("  Symbol: ETH/USDT:USDT")
        orders_logger.info("  Amount: 0.1 contracts")
        orders_logger.info("  Limit Price: 3000.00")
        orders_logger.info("  Leverage: 5x")
        orders_logger.info("  Post Only: True")
        orders_logger.info("  Reduce Only: False")
        orders_logger.info("  Status: open")
        orders_logger.info("  Timestamp: 1234567890")
        orders_logger.info("=" * 80)
        orders_logger.info("")
        
        orders_logger.info("=" * 80)
        orders_logger.info("BUY ORDER CREATED: BTC/USDT:USDT")
        orders_logger.info("-" * 80)
        orders_logger.info("  Order ID: test_order_99999")
        orders_logger.info("  Type: STOP-LIMIT")
        orders_logger.info("  Side: BUY")
        orders_logger.info("  Symbol: BTC/USDT:USDT")
        orders_logger.info("  Amount: 0.01 contracts")
        orders_logger.info("  Stop Price: 49000.00")
        orders_logger.info("  Limit Price: 49500.00")
        orders_logger.info("  Leverage: 10x")
        orders_logger.info("  Reduce Only: False")
        orders_logger.info("  Status: open")
        orders_logger.info("  Timestamp: 1234567890")
        orders_logger.info("=" * 80)
        orders_logger.info("")
        
        orders_logger.info("=" * 80)
        orders_logger.info("ORDER CANCELLED: BTC/USDT:USDT")
        orders_logger.info("-" * 80)
        orders_logger.info("  Order ID: test_order_99999")
        orders_logger.info("  Symbol: BTC/USDT:USDT")
        orders_logger.info("=" * 80)
        orders_logger.info("")
        
        print("   ✓ Orders log: Test orders written (market, limit, stop-limit, cancel)")
        
        # Verify file was created
        print("\n3. Verifying log file...")
        
        if os.path.exists(Config.ORDERS_LOG_FILE):
            size = os.path.getsize(Config.ORDERS_LOG_FILE)
            print(f"   ✓ {Config.ORDERS_LOG_FILE} exists ({size} bytes)")
        else:
            print(f"   ✗ {Config.ORDERS_LOG_FILE} does not exist")
            return False
        
        # Read and display sample content
        print("\n4. Sample log content:")
        
        print(f"\n   Orders Log ({Config.ORDERS_LOG_FILE}):")
        with open(Config.ORDERS_LOG_FILE, 'r') as f:
            lines = f.readlines()[-20:]  # Last 20 lines
            for line in lines:
                print(f"      {line.rstrip()}")
        
        print("\n" + "="*60)
        print("✓ Orders logging test passed!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logger_methods():
    """Test that logger methods are available"""
    print("\n" + "="*60)
    print("Testing Logger Methods")
    print("="*60)
    
    try:
        from logger import Logger
        
        # Test that get_orders_logger method exists
        print("\n1. Testing get_orders_logger method...")
        orders_logger = Logger.get_orders_logger()
        print(f"   ✓ get_orders_logger() returns: {orders_logger}")
        
        # Verify it's a logger instance
        import logging
        if isinstance(orders_logger, logging.Logger):
            print(f"   ✓ Returned object is a Logger instance")
        else:
            print(f"   ✗ Returned object is not a Logger instance")
            return False
        
        print("\n" + "="*60)
        print("✓ Logger methods test passed!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test that config has ORDERS_LOG_FILE"""
    print("\n" + "="*60)
    print("Testing Config")
    print("="*60)
    
    try:
        from config import Config
        
        # Test that ORDERS_LOG_FILE exists in config
        print("\n1. Testing ORDERS_LOG_FILE attribute...")
        if hasattr(Config, 'ORDERS_LOG_FILE'):
            print(f"   ✓ Config.ORDERS_LOG_FILE exists: {Config.ORDERS_LOG_FILE}")
        else:
            print(f"   ✗ Config.ORDERS_LOG_FILE does not exist")
            return False
        
        print("\n" + "="*60)
        print("✓ Config test passed!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    all_passed = True
    
    all_passed = test_config() and all_passed
    all_passed = test_logger_methods() and all_passed
    all_passed = test_orders_logger_setup() and all_passed
    
    if all_passed:
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ SOME TESTS FAILED")
        print("="*60)
        sys.exit(1)
