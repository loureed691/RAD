#!/usr/bin/env python3
"""
Tests for logger bugs and functionality issues
"""
import os
import sys
import tempfile
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_log_propagation():
    """Test that logger doesn't propagate to root logger (causing duplicates)"""
    print("\nTesting log propagation bug...")
    try:
        from logger import Logger
        
        # Setup root logger (simulating another library)
        root_handler = logging.StreamHandler(sys.stdout)
        root_handler.setFormatter(logging.Formatter('ROOT_DUPLICATE: %(message)s'))
        logging.root.addHandler(root_handler)
        logging.root.setLevel(logging.INFO)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_log = f.name
        
        try:
            logger = Logger.setup('INFO', temp_log)
            
            # Check propagation setting
            if logger.propagate:
                print("  ⚠️  BUG FOUND: logger.propagate is True")
                print("  This causes duplicate log messages when root logger is configured")
                return False
            else:
                print("  ✓ logger.propagate is False (correct)")
                return True
                
        finally:
            # Cleanup
            logging.root.removeHandler(root_handler)
            if os.path.exists(temp_log):
                os.remove(temp_log)
                
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_setup_calls():
    """Test that multiple setup calls don't cause issues"""
    print("\nTesting multiple setup calls...")
    try:
        from logger import Logger
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_log = f.name
        
        try:
            # Setup multiple times
            for i in range(3):
                logger = Logger.setup('INFO', temp_log)
                logger.info(f"Setup {i+1}")
            
            # Should always have exactly 2 handlers
            if len(logger.handlers) != 2:
                print(f"  ⚠️  BUG: Expected 2 handlers, got {len(logger.handlers)}")
                return False
            
            # Check file for correct number of messages
            with open(temp_log, 'r', encoding='utf-8') as f:
                lines = [l for l in f.read().strip().split('\n') if l]
                if len(lines) != 3:
                    print(f"  ⚠️  BUG: Expected 3 log lines, got {len(lines)}")
                    return False
            
            print("  ✓ Multiple setup calls handled correctly")
            return True
            
        finally:
            if os.path.exists(temp_log):
                os.remove(temp_log)
                
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_message_with_separators():
    """Test that messages with ' - ' separators are formatted correctly"""
    print("\nTesting messages with separators...")
    try:
        from logger import Logger
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_log = f.name
        
        try:
            logger = Logger.setup('INFO', temp_log)
            
            # Test various messages with ' - ' separators
            test_messages = [
                "Win Rate: 75.50% - Avg P/L: 2.50% - Total Trades: 100",
                "Symbol: BTC/USDT - Signal: BUY - Confidence: 0.85",
                "Entry: 50000 - Exit: 52000 - P/L: 4.00%",
            ]
            
            for msg in test_messages:
                logger.info(msg)
            
            # Verify all messages were logged correctly
            with open(temp_log, 'r', encoding='utf-8') as f:
                content = f.read()
                for msg in test_messages:
                    if msg not in content:
                        print(f"  ⚠️  BUG: Message not found in log: {msg}")
                        return False
            
            print("  ✓ Messages with separators handled correctly")
            return True
            
        finally:
            if os.path.exists(temp_log):
                os.remove(temp_log)
                
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_empty_log_dir():
    """Test that logger creates log directory if it doesn't exist"""
    print("\nTesting log directory creation...")
    try:
        from logger import Logger
        
        # Use a temp directory that doesn't exist yet
        temp_dir = tempfile.mkdtemp()
        log_path = os.path.join(temp_dir, 'subdir', 'test.log')
        
        try:
            logger = Logger.setup('INFO', log_path)
            logger.info("Test message")
            
            # Check that directory was created
            if not os.path.exists(os.path.dirname(log_path)):
                print("  ⚠️  BUG: Log directory was not created")
                return False
            
            # Check that file was created
            if not os.path.exists(log_path):
                print("  ⚠️  BUG: Log file was not created")
                return False
            
            print("  ✓ Log directory creation handled correctly")
            return True
            
        finally:
            # Cleanup
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        print(f"✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all logger bug tests"""
    print("=" * 60)
    print("Logger Bug Tests")
    print("=" * 60)
    
    tests = [
        test_log_propagation,
        test_multiple_setup_calls,
        test_message_with_separators,
        test_empty_log_dir,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✅ All logger bug tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} bug(s) found!")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
