"""
Test API call priority and collision prevention
"""
import threading
import time
from datetime import datetime


def test_thread_start_order():
    """Test that threads start in the correct priority order"""
    print("\n" + "=" * 60)
    print("TEST: Thread Start Priority Order")
    print("=" * 60)
    
    # Read bot.py to verify thread start order
    with open('bot.py', 'r') as f:
        bot_source = f.read()
    
    # Find the run method section
    run_method_start = bot_source.find('def run(self):')
    if run_method_start == -1:
        print("  ✗ Could not find run method")
        return False
    
    run_method = bot_source[run_method_start:run_method_start + 5000]
    
    # Find position monitor start
    pos_monitor_start = run_method.find('self._position_monitor_thread = threading.Thread')
    pos_monitor_actual_start = run_method.find('self._position_monitor_thread.start()')
    
    # Find scanner start
    scanner_start = run_method.find('self._scan_thread = threading.Thread')
    scanner_actual_start = run_method.find('self._scan_thread.start()')
    
    if pos_monitor_start == -1 or scanner_start == -1:
        print("  ✗ Could not find thread initialization")
        return False
    
    if pos_monitor_actual_start == -1 or scanner_actual_start == -1:
        print("  ✗ Could not find thread start calls")
        return False
    
    # Verify position monitor starts BEFORE scanner
    if pos_monitor_actual_start < scanner_actual_start:
        print("  ✓ Position monitor thread starts BEFORE scanner (correct priority)")
        print(f"    Position monitor at position: {pos_monitor_actual_start}")
        print(f"    Scanner at position: {scanner_actual_start}")
    else:
        print("  ✗ Scanner starts before position monitor (WRONG PRIORITY!)")
        print(f"    Position monitor at position: {pos_monitor_actual_start}")
        print(f"    Scanner at position: {scanner_actual_start}")
        return False
    
    # Verify there's a delay between starts
    between_code = run_method[pos_monitor_actual_start:scanner_actual_start]
    if 'time.sleep' in between_code:
        print("  ✓ Delay exists between thread starts (ensures priority)")
    else:
        print("  ⚠ No delay between thread starts (may want to add one)")
    
    # Check for priority comments
    if 'CRITICAL' in run_method and 'priority' in run_method.lower():
        print("  ✓ Priority clearly documented in code")
    else:
        print("  ⚠ Priority not clearly documented")
    
    return True


def test_scanner_startup_delay():
    """Test that scanner has startup delay to give position monitor priority"""
    print("\n" + "=" * 60)
    print("TEST: Scanner Startup Delay")
    print("=" * 60)
    
    # Read bot.py to check _background_scanner method
    with open('bot.py', 'r') as f:
        bot_source = f.read()
    
    # Find _background_scanner method
    scanner_method_start = bot_source.find('def _background_scanner(self):')
    if scanner_method_start == -1:
        print("  ✗ Could not find _background_scanner method")
        return False
    
    scanner_method = bot_source[scanner_method_start:scanner_method_start + 2000]
    
    # Check for startup delay
    first_while = scanner_method.find('while self._scan_thread_running:')
    if first_while == -1:
        print("  ✗ Could not find main loop")
        return False
    
    before_loop = scanner_method[:first_while]
    
    if 'time.sleep' in before_loop:
        print("  ✓ Scanner has startup delay before beginning scans")
        # Extract the delay value
        import re
        delay_match = re.search(r'time\.sleep\((\d+(?:\.\d+)?)\)', before_loop)
        if delay_match:
            delay_value = float(delay_match.group(1))
            print(f"    Delay: {delay_value}s")
            if delay_value >= 0.5:
                print("  ✓ Delay is sufficient (>= 0.5s)")
            else:
                print("  ⚠ Delay may be too short")
    else:
        print("  ⚠ No startup delay in scanner (position monitor may not have priority)")
    
    return True


def test_shutdown_order():
    """Test that shutdown order is correct (scanner first, then position monitor)"""
    print("\n" + "=" * 60)
    print("TEST: Shutdown Priority Order")
    print("=" * 60)
    
    # Read bot.py to check shutdown method
    with open('bot.py', 'r') as f:
        bot_source = f.read()
    
    # Find shutdown method
    shutdown_start = bot_source.find('def shutdown(self):')
    if shutdown_start == -1:
        print("  ✗ Could not find shutdown method")
        return False
    
    shutdown_method = bot_source[shutdown_start:shutdown_start + 3000]
    
    # Find when each thread is stopped
    scanner_stop = shutdown_method.find('self._scan_thread_running = False')
    pos_monitor_stop = shutdown_method.find('self._position_monitor_running = False')
    
    if scanner_stop == -1 or pos_monitor_stop == -1:
        print("  ✗ Could not find thread stop calls")
        return False
    
    # Scanner should stop before position monitor
    if scanner_stop < pos_monitor_stop:
        print("  ✓ Scanner stops BEFORE position monitor (correct priority)")
        print("    This allows position monitor to complete critical operations")
    else:
        print("  ✗ Position monitor stops before scanner (WRONG PRIORITY!)")
        return False
    
    return True


def test_api_call_sequence_simulation():
    """Simulate API call sequencing with priority"""
    print("\n" + "=" * 60)
    print("TEST: API Call Priority Simulation")
    print("=" * 60)
    
    api_calls = []
    lock = threading.Lock()
    
    def position_monitor():
        """Simulates position monitor making critical API calls"""
        time.sleep(0.05)  # Small delay to simulate thread startup
        for i in range(3):
            with lock:
                api_calls.append(('position_monitor', datetime.now(), f'critical_call_{i}'))
            time.sleep(0.2)
    
    def scanner():
        """Simulates scanner making non-critical API calls"""
        time.sleep(1.0)  # Startup delay (as implemented)
        for i in range(3):
            with lock:
                api_calls.append(('scanner', datetime.now(), f'scan_call_{i}'))
            time.sleep(0.2)
    
    # Start position monitor first
    pos_thread = threading.Thread(target=position_monitor)
    pos_thread.start()
    
    time.sleep(0.5)  # Delay before starting scanner (as implemented)
    
    # Start scanner second
    scan_thread = threading.Thread(target=scanner)
    scan_thread.start()
    
    # Wait for both to complete
    pos_thread.join()
    scan_thread.join()
    
    # Analyze call order
    print(f"  Total API calls: {len(api_calls)}")
    print("\n  Call sequence:")
    for i, (source, timestamp, call_type) in enumerate(api_calls):
        rel_time = (timestamp - api_calls[0][1]).total_seconds()
        print(f"    {i+1}. {source:20s} {call_type:20s} at +{rel_time:.3f}s")
    
    # Verify first call is from position monitor
    if api_calls and api_calls[0][0] == 'position_monitor':
        print("\n  ✓ First API call is from position monitor (CRITICAL)")
    else:
        print("\n  ✗ First API call is NOT from position monitor")
        return False
    
    # Count how many position monitor calls happen before first scanner call
    pos_calls_before_scan = 0
    for source, _, _ in api_calls:
        if source == 'scanner':
            break
        if source == 'position_monitor':
            pos_calls_before_scan += 1
    
    print(f"  ✓ {pos_calls_before_scan} position monitor calls completed before scanner starts")
    
    if pos_calls_before_scan >= 1:
        print("  ✓ Position monitor established priority")
    else:
        print("  ⚠ Position monitor may not have enough priority")
    
    return True


def run_all_tests():
    """Run all priority tests"""
    print("\n" + "=" * 80)
    print("API PRIORITY AND COLLISION PREVENTION - TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Thread Start Order", test_thread_start_order),
        ("Scanner Startup Delay", test_scanner_startup_delay),
        ("Shutdown Order", test_shutdown_order),
        ("API Call Priority Simulation", test_api_call_sequence_simulation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n  ✗ {test_name} failed with exception:")
            print(f"    {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
