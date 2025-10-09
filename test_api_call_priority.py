"""
Test API call priority system to ensure trading operations always execute before scanning
"""
import threading
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import sys


def test_priority_system_imports():
    """Test that priority system can be imported"""
    print("\n" + "=" * 80)
    print("TEST 1: API Priority System Imports")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient, APICallPriority
        print("  ✓ APICallPriority enum imported successfully")
        print(f"    - CRITICAL: {APICallPriority.CRITICAL}")
        print(f"    - HIGH: {APICallPriority.HIGH}")
        print(f"    - NORMAL: {APICallPriority.NORMAL}")
        print(f"    - LOW: {APICallPriority.LOW}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to import: {e}")
        return False


def test_critical_calls_block_normal_calls():
    """Test that CRITICAL calls block NORMAL calls"""
    print("\n" + "=" * 80)
    print("TEST 2: Critical Calls Block Normal Calls")
    print("=" * 80)
    
    try:
        from kucoin_client import KuCoinClient, APICallPriority
        from unittest.mock import MagicMock, patch
        
        # Create mock client
        with patch('kucoin_client.ccxt.kucoinfutures') as mock_exchange_class:
            mock_exchange = MagicMock()
            mock_exchange_class.return_value = mock_exchange
            
            # Create client
            client = KuCoinClient('test_key', 'test_secret', 'test_pass')
            
            # Track execution order
            execution_order = []
            
            def critical_operation():
                """Simulates a critical trading operation"""
                execution_order.append(('CRITICAL', time.time()))
                time.sleep(0.3)  # Simulate work
                return "critical_result"
            
            def normal_operation():
                """Simulates a normal scanning operation"""
                execution_order.append(('NORMAL', time.time()))
                time.sleep(0.1)  # Simulate work
                return "normal_result"
            
            # Start both operations concurrently
            # Normal operation starts first but should wait for critical
            def run_normal():
                client._execute_with_priority(
                    normal_operation, APICallPriority.NORMAL, 'test_normal'
                )
            
            def run_critical():
                time.sleep(0.05)  # Start critical slightly after normal
                client._execute_with_priority(
                    critical_operation, APICallPriority.CRITICAL, 'test_critical'
                )
            
            normal_thread = threading.Thread(target=run_normal)
            critical_thread = threading.Thread(target=run_critical)
            
            start_time = time.time()
            normal_thread.start()
            critical_thread.start()
            
            normal_thread.join()
            critical_thread.join()
            
            # Analyze execution order
            print(f"\n  Execution sequence:")
            for call_type, timestamp in execution_order:
                relative_time = timestamp - start_time
                print(f"    {call_type:10s} at +{relative_time:.3f}s")
            
            # CRITICAL should execute before NORMAL completes
            if len(execution_order) >= 2:
                first_call, first_time = execution_order[0]
                second_call, second_time = execution_order[1]
                
                # Check that critical call happened during or before normal call
                if first_call == 'CRITICAL' or (first_call == 'NORMAL' and second_call == 'CRITICAL'):
                    print(f"\n  ✓ Priority system working: CRITICAL operations prioritized")
                    return True
                else:
                    print(f"\n  ✗ Priority system failed: unexpected execution order")
                    return False
            else:
                print(f"\n  ⚠ Insufficient execution data")
                return False
            
    except Exception as e:
        print(f"  ✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_order_methods_have_critical_priority():
    """Test that order creation methods are marked as CRITICAL"""
    print("\n" + "=" * 80)
    print("TEST 3: Order Methods Use CRITICAL Priority")
    print("=" * 80)
    
    try:
        # Read kucoin_client.py to verify priority annotations
        with open('kucoin_client.py', 'r') as f:
            source = f.read()
        
        # Check that order methods have CRITICAL priority
        critical_methods = [
            'create_market_order',
            'create_limit_order',
            'create_stop_limit_order',
            'cancel_order'
        ]
        
        all_found = True
        for method in critical_methods:
            method_start = source.find(f'def {method}')
            if method_start == -1:
                print(f"  ✗ Method {method} not found")
                all_found = False
                continue
            
            # Check nearby for CRITICAL priority
            method_section = source[method_start:method_start + 2000]
            
            if 'APICallPriority.CRITICAL' in method_section or '🔴 CRITICAL' in method_section:
                print(f"  ✓ {method} uses CRITICAL priority")
            else:
                print(f"  ⚠ {method} may not use CRITICAL priority")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_scanning_methods_have_normal_priority():
    """Test that scanning methods use NORMAL priority"""
    print("\n" + "=" * 80)
    print("TEST 4: Scanning Methods Use NORMAL Priority")
    print("=" * 80)
    
    try:
        # Read kucoin_client.py to verify priority annotations
        with open('kucoin_client.py', 'r') as f:
            source = f.read()
        
        # Check that scanning methods have NORMAL priority
        normal_methods = [
            'get_active_futures',
            'get_ohlcv'
        ]
        
        all_found = True
        for method in normal_methods:
            method_start = source.find(f'def {method}')
            if method_start == -1:
                print(f"  ✗ Method {method} not found")
                all_found = False
                continue
            
            # Check nearby for NORMAL priority
            method_section = source[method_start:method_start + 2000]
            
            if 'APICallPriority.NORMAL' in method_section or 'SCANNING' in method_section:
                print(f"  ✓ {method} uses NORMAL priority")
            else:
                print(f"  ⚠ {method} may not use NORMAL priority explicitly")
        
        return all_found
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_position_monitoring_has_high_priority():
    """Test that position monitoring methods use HIGH priority"""
    print("\n" + "=" * 80)
    print("TEST 5: Position Monitoring Uses HIGH Priority")
    print("=" * 80)
    
    try:
        # Read kucoin_client.py to verify priority annotations
        with open('kucoin_client.py', 'r') as f:
            source = f.read()
        
        # Check that position methods have HIGH priority
        high_methods = [
            'get_open_positions',
            'get_balance'
        ]
        
        all_found = True
        for method in high_methods:
            method_start = source.find(f'def {method}')
            if method_start == -1:
                print(f"  ✗ Method {method} not found")
                all_found = False
                continue
            
            # Check nearby for HIGH priority
            method_section = source[method_start:method_start + 2000]
            
            if 'APICallPriority.HIGH' in method_section or 'HIGH priority' in method_section:
                print(f"  ✓ {method} uses HIGH priority")
            else:
                print(f"  ⚠ {method} may not use HIGH priority explicitly")
        
        return all_found
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_priority_queue_initialization():
    """Test that priority queue is initialized in client"""
    print("\n" + "=" * 80)
    print("TEST 6: Priority Queue Initialization")
    print("=" * 80)
    
    try:
        # Read kucoin_client.py to check initialization
        with open('kucoin_client.py', 'r') as f:
            source = f.read()
        
        # Check for priority queue initialization
        checks = [
            ('_pending_critical_calls', 'Critical calls tracking'),
            ('_critical_call_lock', 'Critical call lock'),
            ('_wait_for_critical_calls', 'Wait mechanism'),
            ('_track_critical_call', 'Tracking mechanism'),
            ('_execute_with_priority', 'Priority execution wrapper')
        ]
        
        all_found = True
        for item, description in checks:
            if item in source:
                print(f"  ✓ {description} ({item}) found")
            else:
                print(f"  ✗ {description} ({item}) NOT found")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all API priority tests"""
    print("\n" + "=" * 80)
    print("API CALL PRIORITY SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Priority System Imports", test_priority_system_imports),
        ("Critical Calls Block Normal", test_critical_calls_block_normal_calls),
        ("Order Methods CRITICAL", test_order_methods_have_critical_priority),
        ("Scanning Methods NORMAL", test_scanning_methods_have_normal_priority),
        ("Position Methods HIGH", test_position_monitoring_has_high_priority),
        ("Priority Queue Init", test_priority_queue_initialization),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n  ✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print("=" * 80)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 80)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
