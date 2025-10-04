#!/usr/bin/env python3
"""
Tests for enhanced logger with colors and icons
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logger_import():
    """Test that logger module can be imported"""
    print("Testing logger import...")
    try:
        from logger import Logger, ColoredFormatter
        print("✓ Logger and ColoredFormatter imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_logger_setup():
    """Test logger setup"""
    print("\nTesting logger setup...")
    try:
        from logger import Logger
        
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_log = f.name
        
        try:
            logger = Logger.setup('INFO', temp_log)
            
            # Test that logger was created
            assert logger is not None
            assert logger.name == 'TradingBot'
            
            # Test that it has handlers
            assert len(logger.handlers) == 2  # File and console
            
            print("✓ Logger setup successful")
            return True
        finally:
            # Cleanup
            if os.path.exists(temp_log):
                os.remove(temp_log)
    except Exception as e:
        print(f"✗ Logger setup error: {e}")
        return False

def test_logger_messages():
    """Test different log levels"""
    print("\nTesting logger messages...")
    try:
        from logger import Logger
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_log = f.name
        
        try:
            logger = Logger.setup('DEBUG', temp_log)
            
            # Test different log levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Verify messages were written to file
            with open(temp_log, 'r') as f:
                content = f.read()
                assert 'Debug message' in content
                assert 'Info message' in content
                assert 'Warning message' in content
                assert 'Error message' in content
            
            print("✓ All log levels working correctly")
            return True
        finally:
            if os.path.exists(temp_log):
                os.remove(temp_log)
    except Exception as e:
        print(f"✗ Logger messages error: {e}")
        return False

def test_file_logging_plain_text():
    """Test that file logging remains plain text without ANSI codes"""
    print("\nTesting file logging format...")
    try:
        from logger import Logger
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_log = f.name
        
        try:
            logger = Logger.setup('INFO', temp_log)
            
            logger.info("Test message with emoji 🤖")
            logger.warning("Warning message ⚠️")
            logger.error("Error message ✗")
            
            # Read file and check for ANSI codes
            with open(temp_log, 'r') as f:
                content = f.read()
                
                # Should NOT contain ANSI escape codes
                assert '\033[' not in content, "File log should not contain ANSI codes"
                
                # Should contain the actual messages
                assert 'Test message' in content
                assert 'Warning message' in content
                assert 'Error message' in content
                
                # Should contain proper timestamp format
                assert ' - TradingBot - ' in content
            
            print("✓ File logging is plain text (no ANSI codes)")
            return True
        finally:
            if os.path.exists(temp_log):
                os.remove(temp_log)
    except Exception as e:
        print(f"✗ File logging test error: {e}")
        return False

def test_colored_formatter():
    """Test ColoredFormatter class"""
    print("\nTesting ColoredFormatter...")
    try:
        from logger import ColoredFormatter
        import logging
        
        # Create formatter
        formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S',
            use_colors=True
        )
        
        # Test that it has the required attributes
        assert hasattr(formatter, 'COLORS')
        assert hasattr(formatter, 'ICONS')
        assert 'INFO' in formatter.COLORS
        assert 'WARNING' in formatter.COLORS
        assert 'ERROR' in formatter.COLORS
        assert 'INFO' in formatter.ICONS
        assert 'WARNING' in formatter.ICONS
        assert 'ERROR' in formatter.ICONS
        
        print("✓ ColoredFormatter structure is correct")
        return True
    except Exception as e:
        print(f"✗ ColoredFormatter test error: {e}")
        return False

def test_logger_get():
    """Test getting existing logger"""
    print("\nTesting Logger.get_logger()...")
    try:
        from logger import Logger
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_log = f.name
        
        try:
            # Setup logger
            logger1 = Logger.setup('INFO', temp_log)
            
            # Get logger
            logger2 = Logger.get_logger()
            
            # Should be the same logger
            assert logger1 is logger2
            assert logger1.name == logger2.name == 'TradingBot'
            
            print("✓ Logger.get_logger() working correctly")
            return True
        finally:
            if os.path.exists(temp_log):
                os.remove(temp_log)
    except Exception as e:
        print(f"✗ get_logger test error: {e}")
        return False

def test_unicode_emoji_handling():
    """Test that Unicode emojis are handled correctly in logs"""
    print("\nTesting Unicode emoji handling...")
    try:
        from logger import Logger
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_log = f.name
        
        try:
            logger = Logger.setup('INFO', temp_log)
            
            # Test various emojis that were causing issues
            logger.info("🔎 Evaluating opportunity")
            logger.info("⏸️  Waiting for next cycle")
            logger.info("🚀 BOT STARTED SUCCESSFULLY!")
            logger.info("⏱️  Check interval")
            logger.info("📊 Max positions")
            logger.info("💪 Leverage")
            logger.info("✅ Trade executed")
            logger.info("❌ Error in trading")
            logger.info("🤖 Retraining ML model")
            
            # Verify messages were written to file correctly
            with open(temp_log, 'r', encoding='utf-8') as f:
                content = f.read()
                assert '🔎 Evaluating opportunity' in content
                assert '⏸️  Waiting for next cycle' in content
                assert '🚀 BOT STARTED SUCCESSFULLY!' in content
                assert '✅ Trade executed' in content
            
            print("✓ Unicode emojis handled correctly in file logs")
            print("✓ Console output completed without encoding errors")
            return True
        finally:
            if os.path.exists(temp_log):
                os.remove(temp_log)
    except Exception as e:
        print(f"✗ Unicode emoji handling test error: {e}")
        return False

def run_all_tests():
    """Run all logger tests"""
    print("=" * 60)
    print("Testing Enhanced Logger")
    print("=" * 60)
    
    tests = [
        test_logger_import,
        test_logger_setup,
        test_logger_messages,
        test_file_logging_plain_text,
        test_colored_formatter,
        test_logger_get,
        test_unicode_emoji_handling,
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
        print("\n✅ All logger tests passed!")
        return True
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
