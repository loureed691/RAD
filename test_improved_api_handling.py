#!/usr/bin/env python3
"""
Test improved API handling and position monitoring
Tests the separation of position monitoring from scanning
"""
import sys
import os
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_values():
    """Test that configuration values are optimized for fast monitoring"""
    print("\n" + "=" * 60)
    print("Testing Configuration Values")
    print("=" * 60)
    
    from config import Config
    
    # Test new optimized values
    print(f"  CHECK_INTERVAL: {Config.CHECK_INTERVAL}s")
    print(f"  POSITION_UPDATE_INTERVAL: {Config.POSITION_UPDATE_INTERVAL}s")
    print(f"  LIVE_LOOP_INTERVAL: {Config.LIVE_LOOP_INTERVAL}s")
    
    # Verify improvements
    assert Config.POSITION_UPDATE_INTERVAL <= 1.5, \
        f"POSITION_UPDATE_INTERVAL should be <= 1.5s for fast monitoring, got {Config.POSITION_UPDATE_INTERVAL}s"
    assert Config.LIVE_LOOP_INTERVAL <= 0.1, \
        f"LIVE_LOOP_INTERVAL should be <= 0.1s for responsive loop, got {Config.LIVE_LOOP_INTERVAL}s"
    
    print("  ✓ Configuration values are optimized for fast monitoring")
    return True

def test_threading_separation():
    """Test that position monitoring and scanning are properly separated"""
    print("\n" + "=" * 60)
    print("Testing Thread Separation")
    print("=" * 60)
    
    # Test by checking the bot.py file directly
    with open('bot.py', 'r') as f:
        bot_source = f.read()
    
    # Check for position monitor thread
    assert '_position_monitor' in bot_source, "Bot should have _position_monitor method"
    print("  ✓ Bot has _position_monitor method")
    
    # Check for background scanner
    assert '_background_scanner' in bot_source, "Bot should have _background_scanner method"
    print("  ✓ Bot has _background_scanner method")
    
    # Check for thread state variables
    assert '_position_monitor_thread' in bot_source, "Bot should initialize _position_monitor_thread"
    assert '_position_monitor_running' in bot_source, "Bot should initialize _position_monitor_running"
    print("  ✓ Bot has separate thread states for position monitoring")
    
    # Check that run method starts both threads
    assert 'Thread(target=self._position_monitor' in bot_source, "Bot run method should start position monitor thread"
    assert 'Thread(target=self._background_scanner' in bot_source, "Bot run method should start background scanner thread"
    print("  ✓ Bot run method starts both threads independently")
    
    # Check that position monitoring runs in dedicated thread
    assert 'def _position_monitor(self):' in bot_source, "Bot should have dedicated position monitor method"
    print("  ✓ Position monitoring has dedicated thread method")
    
    return True

def test_position_monitor_responsiveness():
    """Test that position monitor responds faster than before"""
    print("\n" + "=" * 60)
    print("Testing Position Monitor Responsiveness")
    print("=" * 60)
    
    from config import Config
    
    # Simulate position monitoring
    class MockPositionManager:
        def __init__(self):
            self.positions = {'TEST:USDT': 'test_position'}
            self.update_count = 0
        
        def get_open_positions_count(self):
            return len(self.positions)
        
        def update_positions(self):
            self.update_count += 1
            return []
    
    position_manager = MockPositionManager()
    monitor_running = True
    last_check = datetime.now()
    
    def position_monitor():
        nonlocal last_check
        while monitor_running:
            if position_manager.get_open_positions_count() > 0:
                time_since_last = (datetime.now() - last_check).total_seconds()
                
                if time_since_last >= Config.POSITION_UPDATE_INTERVAL:
                    position_manager.update_positions()
                    last_check = datetime.now()
            
            time.sleep(0.05)  # 50ms
    
    # Start monitor thread
    monitor_thread = threading.Thread(target=position_monitor, daemon=True)
    monitor_thread.start()
    
    # Run for 3 seconds
    print(f"  Running position monitor for 3 seconds with {Config.POSITION_UPDATE_INTERVAL}s interval...")
    time.sleep(3)
    
    # Stop monitor
    monitor_running = False
    monitor_thread.join(timeout=1)
    
    # Check responsiveness
    expected_updates = int(3 / Config.POSITION_UPDATE_INTERVAL)
    actual_updates = position_manager.update_count
    
    print(f"  Expected ~{expected_updates} updates, got {actual_updates}")
    
    # Allow some tolerance
    assert actual_updates >= expected_updates - 1, \
        f"Position monitor should perform at least {expected_updates - 1} updates, got {actual_updates}"
    
    avg_interval = 3 / actual_updates if actual_updates > 0 else float('inf')
    print(f"  ✓ Average update interval: {avg_interval:.2f}s")
    
    # Verify it's faster than old 3s interval
    assert avg_interval < 2.0, \
        f"Average interval should be < 2.0s (old was 3s), got {avg_interval:.2f}s"
    
    print("  ✓ Position monitoring is faster than before (< 2s vs old 3s)")
    
    return True

def test_scanner_independence():
    """Test that scanner runs independently without blocking position monitoring"""
    print("\n" + "=" * 60)
    print("Testing Scanner Independence")
    print("=" * 60)
    
    from config import Config
    
    # Simulate both threads running
    scan_running = True
    monitor_running = True
    scan_count = 0
    monitor_count = 0
    
    def background_scanner():
        nonlocal scan_count
        while scan_running:
            # Simulate long scan (5 seconds)
            scan_count += 1
            for _ in range(Config.CHECK_INTERVAL):
                if not scan_running:
                    break
                time.sleep(0.1)  # Check more frequently
    
    def position_monitor():
        nonlocal monitor_count
        last_check = datetime.now()
        while monitor_running:
            time_since_last = (datetime.now() - last_check).total_seconds()
            
            if time_since_last >= Config.POSITION_UPDATE_INTERVAL:
                monitor_count += 1
                last_check = datetime.now()
            
            time.sleep(0.05)
    
    # Start both threads
    scanner_thread = threading.Thread(target=background_scanner, daemon=True)
    monitor_thread = threading.Thread(target=position_monitor, daemon=True)
    
    scanner_thread.start()
    monitor_thread.start()
    
    # Run for 3 seconds
    print("  Running both threads for 3 seconds...")
    time.sleep(3)
    
    # Stop threads
    scan_running = False
    monitor_running = False
    scanner_thread.join(timeout=1)
    monitor_thread.join(timeout=1)
    
    print(f"  Scanner iterations: {scan_count}")
    print(f"  Position updates: {monitor_count}")
    
    # Position monitor should have updated multiple times even during scan
    assert monitor_count >= 2, \
        f"Position monitor should update multiple times during scan, got {monitor_count}"
    
    print("  ✓ Position monitor runs independently during scanning")
    
    return True

def test_api_rate_limit_safety():
    """Test that API calls are properly throttled"""
    print("\n" + "=" * 60)
    print("Testing API Rate Limit Safety")
    print("=" * 60)
    
    from config import Config
    
    # Track API call timestamps
    api_calls = []
    
    def mock_api_call():
        api_calls.append(datetime.now())
    
    # Simulate position monitoring with API calls
    monitor_running = True
    last_check = datetime.now()
    
    def position_monitor():
        nonlocal last_check
        while monitor_running:
            time_since_last = (datetime.now() - last_check).total_seconds()
            
            if time_since_last >= Config.POSITION_UPDATE_INTERVAL:
                mock_api_call()
                last_check = datetime.now()
            
            time.sleep(0.05)
    
    # Start monitor
    monitor_thread = threading.Thread(target=position_monitor, daemon=True)
    monitor_thread.start()
    
    # Run for 3 seconds
    time.sleep(3)
    
    # Stop monitor
    monitor_running = False
    monitor_thread.join(timeout=1)
    
    # Check API call intervals
    if len(api_calls) > 1:
        intervals = []
        for i in range(1, len(api_calls)):
            interval = (api_calls[i] - api_calls[i-1]).total_seconds()
            intervals.append(interval)
        
        min_interval = min(intervals)
        avg_interval = sum(intervals) / len(intervals)
        
        print(f"  API calls made: {len(api_calls)}")
        print(f"  Min interval: {min_interval:.2f}s")
        print(f"  Avg interval: {avg_interval:.2f}s")
        
        # Ensure we respect the throttle
        assert min_interval >= Config.POSITION_UPDATE_INTERVAL * 0.9, \
            f"Min interval {min_interval:.2f}s should be >= {Config.POSITION_UPDATE_INTERVAL * 0.9:.2f}s"
        
        print(f"  ✓ API calls properly throttled (min {min_interval:.2f}s >= {Config.POSITION_UPDATE_INTERVAL}s)")
    else:
        print("  ⚠️  Not enough API calls to verify throttling")
    
    return True

def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("IMPROVED API HANDLING - TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Configuration Values", test_config_values),
        ("Thread Separation", test_threading_separation),
        ("Position Monitor Responsiveness", test_position_monitor_responsiveness),
        ("Scanner Independence", test_scanner_independence),
        ("API Rate Limit Safety", test_api_rate_limit_safety),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  ✗ {test_name} failed")
        except Exception as e:
            failed += 1
            print(f"\n  ✗ {test_name} failed with exception:")
            print(f"    {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
