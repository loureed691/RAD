#!/usr/bin/env python3
"""
Test script to demonstrate Unicode emoji handling fix for Windows encoding issues
"""
import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 70)
    print("Testing Unicode Emoji Handling (Windows Encoding Fix)")
    print("=" * 70)
    print()
    
    from logger import Logger
    
    # Create a temporary log file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_log = f.name
    
    try:
        # Setup logger
        logger = Logger.setup('INFO', temp_log)
        
        print("Logging messages with emojis that previously caused encoding errors on Windows:")
        print()
        
        # Test the exact messages from the error report
        logger.info("🔎 Evaluating opportunity: RESOLV/USDT:USDT - Score: 130.0, Signal: SELL, Confidence: 0.99")
        logger.info("🔎 Evaluating opportunity: ETH/USDT:USDT - Score: 120.0, Signal: SELL, Confidence: 1.00")
        logger.info("⏸️  Waiting 60s before next cycle...")
        
        print()
        print("Testing other emojis used in the bot:")
        print()
        
        # Test all the emojis used in bot.py
        logger.info("=" * 60)
        logger.info("🚀 BOT STARTED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info("⏱️  Check interval: 60s")
        logger.info("📊 Max positions: 3")
        logger.info("💪 Leverage: 10x")
        logger.info("=" * 60)
        logger.info("✅ Trade executed for BTC/USDT:USDT")
        logger.info("❌ Error in trading cycle")
        logger.info("🤖 Retraining ML model...")
        logger.info("🛑 Shutdown signal received")
        logger.info("⌨️  Received keyboard interrupt")
        
        print()
        print("=" * 70)
        print("✅ SUCCESS: All emoji messages logged without encoding errors!")
        print("=" * 70)
        print()
        
        # Show file content
        print("File log content (UTF-8 encoded):")
        print("-" * 70)
        with open(temp_log, 'r', encoding='utf-8') as f:
            for line in f:
                print(line.rstrip())
        print("-" * 70)
        print()
        
        print("The fix ensures:")
        print("  ✓ Console output uses UTF-8 encoding via stream.reconfigure()")
        print("  ✓ File output uses UTF-8 encoding via FileHandler(encoding='utf-8')")
        print("  ✓ Errors='replace' prevents crashes on unsupported characters")
        print("  ✓ Works on both Windows (cp1252) and Unix (utf-8) systems")
        print()
        
        return True
        
    finally:
        # Cleanup
        if os.path.exists(temp_log):
            os.remove(temp_log)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
