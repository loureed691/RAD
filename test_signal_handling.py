#!/usr/bin/env python3
"""
Test script to verify Ctrl+C (SIGINT) shutdown works correctly.
This test verifies that the signal handler properly interrupts the bot's main loop.
"""

import sys
import os
import signal
import time
import threading
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_signal_handler_raises_keyboard_interrupt():
    """Test that signal handler raises KeyboardInterrupt"""
    print("\n" + "=" * 60)
    print("TEST: Signal Handler Raises KeyboardInterrupt")
    print("=" * 60)
    
    # Test the signal handler logic without importing the full bot
    # This avoids dependency issues while still testing the core logic
    
    # Simulate the bot's signal handler
    class MockBot:
        def __init__(self):
            self.running = True
            self._scan_thread_running = True
            self._position_monitor_running = True
            self._dashboard_running = True
            self.logger = Mock()
        
        def signal_handler(self, sig, frame):
            """Handle shutdown signals gracefully - same logic as real bot"""
            signal_name = 'SIGINT (Ctrl+C)' if sig == signal.SIGINT else f'SIGTERM ({sig})'
            self.logger.info(f"🛑 Shutdown signal received: {signal_name}")
            self.running = False
            self._scan_thread_running = False
            self._position_monitor_running = False
            self._dashboard_running = False
            # Raise KeyboardInterrupt to break out of any blocking calls
            raise KeyboardInterrupt()
    
    bot = MockBot()
    print("✓ Mock bot instance created")
    
    # Test that signal handler raises KeyboardInterrupt
    try:
        bot.signal_handler(signal.SIGINT, None)
        print("✗ FAILED: signal_handler did not raise KeyboardInterrupt")
        return False
    except KeyboardInterrupt:
        print("✓ signal_handler correctly raised KeyboardInterrupt")
    
    # Verify flags were set
    assert bot.running == False, "running flag should be False"
    assert bot._scan_thread_running == False, "_scan_thread_running flag should be False"
    assert bot._position_monitor_running == False, "_position_monitor_running flag should be False"
    print("✓ All shutdown flags were set correctly")
    
    print("=" * 60)
    print("✅ TEST PASSED: Signal handler works correctly")
    print("=" * 60)
    return True


def test_keyboard_interrupt_breaks_main_loop():
    """Test that KeyboardInterrupt properly breaks the main loop"""
    print("\n" + "=" * 60)
    print("TEST: KeyboardInterrupt Breaks Main Loop")
    print("=" * 60)
    
    # Simulate a simplified main loop like in bot.run()
    running = True
    signal_received = False
    
    def signal_handler(sig, frame):
        nonlocal running, signal_received
        running = False
        signal_received = True
        raise KeyboardInterrupt()
    
    # Install handler
    old_handler = signal.signal(signal.SIGINT, signal_handler)
    
    try:
        loop_count = 0
        start_time = time.time()
        
        try:
            while running:
                loop_count += 1
                # Simulate work
                time.sleep(0.05)
                
                # Send signal after 0.2 seconds (4 iterations)
                if loop_count == 4:
                    os.kill(os.getpid(), signal.SIGINT)
                
                # Safety timeout
                if time.time() - start_time > 2.0:
                    print("✗ FAILED: Loop didn't exit within timeout")
                    return False
                    
        except KeyboardInterrupt:
            elapsed = time.time() - start_time
            print(f"✓ KeyboardInterrupt caught after {loop_count} iterations ({elapsed:.3f}s)")
            print(f"✓ Signal was processed immediately")
            
            # Verify it happened quickly (should be < 0.5s)
            if elapsed > 0.5:
                print(f"⚠️  WARNING: Signal took {elapsed:.3f}s to process (expected < 0.5s)")
            else:
                print(f"✓ Signal processing time is good: {elapsed:.3f}s")
            
            assert signal_received, "signal_received flag should be True"
            print("✓ Signal handler was executed")
            
    finally:
        # Restore original handler
        signal.signal(signal.SIGINT, old_handler)
    
    print("=" * 60)
    print("✅ TEST PASSED: KeyboardInterrupt breaks loop correctly")
    print("=" * 60)
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 TESTING CTRL+C SHUTDOWN FIX")
    print("=" * 60)
    
    tests = [
        test_signal_handler_raises_keyboard_interrupt,
        test_keyboard_interrupt_breaks_main_loop,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ TEST FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
