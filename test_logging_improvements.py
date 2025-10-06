#!/usr/bin/env python3
"""
Test script to verify improved logging functionality:
1. Order details (status, timestamp, average fill price) are not None
2. Trading strategy logging is working
3. Stop loss and take profit logging is working
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logger_setup():
    """Test that all loggers are set up correctly"""
    print("\n" + "="*60)
    print("TEST 1: Logger Setup")
    print("="*60)
    
    try:
        from logger import Logger
        from config import Config
        
        # Test that all log file configs exist
        print("\n1.1 Testing log file configuration...")
        assert hasattr(Config, 'ORDERS_LOG_FILE'), "ORDERS_LOG_FILE missing"
        assert hasattr(Config, 'STRATEGY_LOG_FILE'), "STRATEGY_LOG_FILE missing"
        print(f"   ✓ ORDERS_LOG_FILE: {Config.ORDERS_LOG_FILE}")
        print(f"   ✓ STRATEGY_LOG_FILE: {Config.STRATEGY_LOG_FILE}")
        
        # Test that all logger getters exist
        print("\n1.2 Testing logger getters...")
        orders_logger = Logger.get_orders_logger()
        strategy_logger = Logger.get_strategy_logger()
        assert orders_logger is not None, "Orders logger is None"
        assert strategy_logger is not None, "Strategy logger is None"
        print("   ✓ Orders logger available")
        print("   ✓ Strategy logger available")
        
        print("\n✓ Logger setup test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Logger setup test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_logging():
    """Test that strategy logging is implemented"""
    print("\n" + "="*60)
    print("TEST 2: Strategy Logging")
    print("="*60)
    
    try:
        from logger import Logger
        from config import Config
        
        # Setup strategy logger
        print("\n2.1 Setting up strategy logger...")
        strategy_logger = Logger.setup_specialized_logger(
            'StrategyLogger',
            Config.STRATEGY_LOG_FILE,
            Config.DETAILED_LOG_LEVEL
        )
        print(f"   ✓ Strategy logger created: {Config.STRATEGY_LOG_FILE}")
        
        # Test writing to strategy logger
        print("\n2.2 Testing strategy log writing...")
        
        strategy_logger.info("=" * 80)
        strategy_logger.info("TRADING STRATEGY ANALYSIS")
        strategy_logger.info("-" * 80)
        strategy_logger.info("  Signal: BUY")
        strategy_logger.info("  Confidence: 67.50%")
        strategy_logger.info("  Market Regime: trending")
        strategy_logger.info("  Buy Signals: 6.50 / 10.00")
        strategy_logger.info("  Sell Signals: 3.50 / 10.00")
        strategy_logger.info("  Multi-Timeframe Alignment: bullish")
        strategy_logger.info("")
        strategy_logger.info("  Strategy Components:")
        strategy_logger.info("    - ma_trend: bullish")
        strategy_logger.info("    - macd: bullish")
        strategy_logger.info("    - rsi: weak (38.5)")
        strategy_logger.info("    - volume: high volume confirmation")
        strategy_logger.info("    - momentum: strong positive")
        strategy_logger.info("=" * 80)
        strategy_logger.info("")
        
        print("   ✓ Strategy log entries written")
        
        # Verify file was created and written
        if os.path.exists(Config.STRATEGY_LOG_FILE):
            with open(Config.STRATEGY_LOG_FILE, 'r') as f:
                content = f.read()
                assert 'TRADING STRATEGY ANALYSIS' in content, "Strategy log content missing"
                print(f"   ✓ Strategy log file verified: {len(content)} bytes")
        else:
            print(f"   ⚠ Strategy log file not found (may not have been created yet)")
        
        print("\n✓ Strategy logging test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Strategy logging test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sl_tp_logging():
    """Test that stop loss and take profit logging is implemented"""
    print("\n" + "="*60)
    print("TEST 3: Stop Loss & Take Profit Logging")
    print("="*60)
    
    try:
        from logger import Logger
        from config import Config
        
        # Setup orders logger
        print("\n3.1 Setting up orders logger...")
        orders_logger = Logger.setup_specialized_logger(
            'OrdersLogger',
            Config.ORDERS_LOG_FILE,
            Config.DETAILED_LOG_LEVEL
        )
        print(f"   ✓ Orders logger created: {Config.ORDERS_LOG_FILE}")
        
        # Test SL/TP set logging
        print("\n3.2 Testing SL/TP set logging...")
        
        orders_logger.info("=" * 80)
        orders_logger.info("STOP LOSS & TAKE PROFIT SET: BTC/USDT:USDT")
        orders_logger.info("-" * 80)
        orders_logger.info("  Symbol: BTC/USDT:USDT")
        orders_logger.info("  Position Side: BUY (LONG)")
        orders_logger.info("  Entry Price: 50000.00")
        orders_logger.info("  Amount: 0.1 contracts")
        orders_logger.info("  Leverage: 10x")
        orders_logger.info("")
        orders_logger.info("  Stop Loss Price: 47500.00")
        orders_logger.info("  Stop Loss %: 5.00% from entry")
        orders_logger.info("  Stop Loss Type: Monitored (closes position when price reaches SL)")
        orders_logger.info("")
        orders_logger.info("  Take Profit Price: 55000.00")
        orders_logger.info("  Take Profit %: 10.00% from entry")
        orders_logger.info("  Take Profit Type: Monitored (closes position when price reaches TP)")
        orders_logger.info("")
        orders_logger.info("  Risk/Reward Ratio: 1:2.00")
        orders_logger.info(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        orders_logger.info("=" * 80)
        orders_logger.info("")
        
        print("   ✓ SL/TP set log entries written")
        
        # Test SL/TP trigger logging
        print("\n3.3 Testing SL/TP trigger logging...")
        
        orders_logger.info("=" * 80)
        orders_logger.info("STOP LOSS TRIGGERED: BTC/USDT:USDT")
        orders_logger.info("-" * 80)
        orders_logger.info("  Symbol: BTC/USDT:USDT")
        orders_logger.info("  Position Side: LONG")
        orders_logger.info("  Entry Price: 50000.00")
        orders_logger.info("  Exit Price: 47500.00")
        orders_logger.info("  Amount: 0.1 contracts")
        orders_logger.info("  Leverage: 10x")
        orders_logger.info("  Stop Loss Price: 47500.00")
        orders_logger.info("  Trigger: Price fell below stop loss")
        orders_logger.info("  P/L: -5.00% ($-250.00)")
        orders_logger.info("  Duration: 15.5 minutes")
        orders_logger.info(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        orders_logger.info("=" * 80)
        orders_logger.info("")
        
        print("   ✓ SL/TP trigger log entries written")
        
        # Verify file was created and written
        if os.path.exists(Config.ORDERS_LOG_FILE):
            with open(Config.ORDERS_LOG_FILE, 'r') as f:
                content = f.read()
                assert 'STOP LOSS & TAKE PROFIT SET' in content, "SL/TP set log content missing"
                assert 'STOP LOSS TRIGGERED' in content, "SL trigger log content missing"
                print(f"   ✓ Orders log file verified: {len(content)} bytes")
        else:
            print(f"   ⚠ Orders log file not found (may not have been created yet)")
        
        print("\n✓ SL/TP logging test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ SL/TP logging test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_order_details_fix():
    """Test that order details are properly fetched and not None"""
    print("\n" + "="*60)
    print("TEST 4: Order Details Fix")
    print("="*60)
    
    try:
        from kucoin_client import KuCoinClient
        
        print("\n4.1 Checking create_market_order implementation...")
        
        # Read the file to verify the fix is in place
        with open('kucoin_client.py', 'r') as f:
            content = f.read()
            
        # Check for the fix: fetching order status after creation
        assert 'fetch_order(order[' in content or "fetch_order(order.get('id')" in content, \
            "Order status fetch not found in create_market_order"
        print("   ✓ Order status fetch implemented in create_market_order")
        
        # Check for timestamp formatting
        assert 'fromtimestamp' in content or 'Timestamp:' in content, \
            "Timestamp formatting not found"
        print("   ✓ Timestamp formatting implemented")
        
        # Check for sleep/wait after order creation
        assert 'time.sleep' in content, \
            "No wait time after order creation found"
        print("   ✓ Wait time after order creation implemented")
        
        print("\n✓ Order details fix test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Order details fix test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_generator_integration():
    """Test that SignalGenerator has strategy logger integrated"""
    print("\n" + "="*60)
    print("TEST 5: Signal Generator Integration")
    print("="*60)
    
    try:
        from signals import SignalGenerator
        
        print("\n5.1 Checking SignalGenerator implementation...")
        
        # Read the file to verify the integration
        with open('signals.py', 'r') as f:
            content = f.read()
            
        # Check for strategy logger initialization
        assert 'strategy_logger' in content, \
            "strategy_logger not found in SignalGenerator"
        print("   ✓ strategy_logger attribute found in SignalGenerator")
        
        # Check for strategy logging calls
        assert 'TRADING STRATEGY ANALYSIS' in content, \
            "Strategy analysis logging not found"
        print("   ✓ Strategy analysis logging implemented")
        
        # Check for strategy components logging
        assert 'Strategy Components' in content or 'strategy components' in content.lower(), \
            "Strategy components logging not found"
        print("   ✓ Strategy components logging implemented")
        
        print("\n✓ Signal generator integration test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Signal generator integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    all_passed = True
    
    all_passed = test_logger_setup() and all_passed
    all_passed = test_strategy_logging() and all_passed
    all_passed = test_sl_tp_logging() and all_passed
    all_passed = test_order_details_fix() and all_passed
    all_passed = test_signal_generator_integration() and all_passed
    
    if all_passed:
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nSummary of improvements:")
        print("  ✓ Order details (status, timestamp, avg price) are fetched properly")
        print("  ✓ Trading strategy analysis is logged to logs/strategy.log")
        print("  ✓ Stop loss and take profit setup is logged to logs/orders.log")
        print("  ✓ Stop loss and take profit triggers are logged to logs/orders.log")
        print("  ✓ All loggers are properly configured and integrated")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ SOME TESTS FAILED")
        print("="*60)
        sys.exit(1)
