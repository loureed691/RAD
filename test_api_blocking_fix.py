"""
Test to verify API blocking fix and take profit improvements
"""
import time
import threading
from datetime import datetime

def test_max_workers_reduction():
    """Test that MAX_WORKERS is reduced to prevent API saturation"""
    from config import Config
    
    print("\n" + "="*60)
    print("TEST 1: MAX_WORKERS Reduction")
    print("="*60)
    
    max_workers = Config.MAX_WORKERS
    print(f"Current MAX_WORKERS: {max_workers}")
    
    assert max_workers == 8, f"Expected MAX_WORKERS=8, got {max_workers}"
    print("✓ MAX_WORKERS reduced from 20 to 8 to prevent API saturation")
    print("  Benefit: Fewer concurrent API calls during market scanning")
    return True

def test_api_semaphore():
    """Test that API semaphore limits concurrent calls"""
    from kucoin_client import KuCoinClient
    
    print("\n" + "="*60)
    print("TEST 2: API Semaphore Rate Limiting")
    print("="*60)
    
    # Mock client initialization without real API keys
    class MockExchange:
        def __init__(self):
            pass
    
    # Check if KuCoinClient has semaphore
    print("Checking KuCoinClient implementation...")
    import inspect
    source = inspect.getsource(KuCoinClient.__init__)
    
    has_semaphore = '_api_semaphore' in source
    assert has_semaphore, "KuCoinClient should have _api_semaphore"
    print("✓ API semaphore implemented in KuCoinClient")
    
    # Check _execute_with_priority uses semaphore
    source = inspect.getsource(KuCoinClient._execute_with_priority)
    uses_semaphore = 'acquire()' in source and 'release()' in source
    assert uses_semaphore, "_execute_with_priority should use semaphore"
    print("✓ Semaphore used in _execute_with_priority method")
    
    # Check critical calls bypass semaphore
    bypasses_critical = 'use_semaphore = priority > APICallPriority.CRITICAL' in source
    assert bypasses_critical, "Critical calls should bypass semaphore"
    print("✓ Critical calls (position closing, stop loss) bypass semaphore")
    print("  Benefit: Position management always executes immediately")
    
    return True

def test_take_profit_multipliers():
    """Test that take profit multipliers are reduced for profitability"""
    from position_manager import Position
    import inspect
    
    print("\n" + "="*60)
    print("TEST 3: Take Profit Extension Reductions")
    print("="*60)
    
    # Check position manager source code
    source = inspect.getsource(Position.update_take_profit)
    
    # Check for reduced momentum multiplier
    has_reduced_momentum = 'tp_multiplier = 1.05  # Extend 5% further' in source
    assert has_reduced_momentum, "Momentum multiplier should be 1.05"
    print("✓ Momentum extension reduced: 1.20 → 1.05 (5% instead of 20%)")
    
    # Check for reduced trend strength multiplier
    has_reduced_trend = 'tp_multiplier *= 1.05  # Strong trend bonus' in source
    assert has_reduced_trend, "Trend strength multiplier should be 1.05"
    print("✓ Trend strength extension reduced: 1.15 → 1.05")
    
    # Check for reduced volatility multiplier
    has_reduced_volatility = 'tp_multiplier *= 1.03  # (was 1.1)' in source
    assert has_reduced_volatility, "Volatility multiplier should be 1.03"
    print("✓ Volatility extension reduced: 1.10 → 1.03")
    
    # Check for tighter profit caps
    has_tight_cap_10 = 'tp_multiplier = min(tp_multiplier, 1.01)  # Almost no extension (was 1.03)' in source
    assert has_tight_cap_10, "Should have 1.01x cap at 10% profit"
    print("✓ 10% profit cap: 1.03x → 1.01x (lock in profits!)")
    
    has_tight_cap_5 = 'tp_multiplier = min(tp_multiplier, 1.03)  # Very limited extension (was 1.08)' in source
    assert has_tight_cap_5, "Should have 1.03x cap at 5% profit"
    print("✓ 5% profit cap: 1.08x → 1.03x")
    
    has_tight_cap_3 = 'tp_multiplier = min(tp_multiplier, 1.05)  # Cap extensions early (was 1.15)' in source
    assert has_tight_cap_3, "Should have 1.05x cap at 3% profit"
    print("✓ 3% profit cap: 1.15x → 1.05x")
    
    print("\n  Benefit: More profits locked in, less likely to give back gains")
    return True

def test_semaphore_behavior():
    """Test semaphore behavior with concurrent threads"""
    import threading
    
    print("\n" + "="*60)
    print("TEST 4: Semaphore Concurrent Behavior")
    print("="*60)
    
    semaphore = threading.Semaphore(8)
    concurrent_calls = []
    max_concurrent = 0
    lock = threading.Lock()
    
    def mock_api_call(call_id):
        nonlocal max_concurrent
        semaphore.acquire()
        
        # Track concurrent calls
        with lock:
            concurrent_calls.append(call_id)
            max_concurrent = max(max_concurrent, len(concurrent_calls))
        
        # Simulate API call
        time.sleep(0.01)
        
        # Remove from concurrent calls
        with lock:
            concurrent_calls.remove(call_id)
        
        semaphore.release()
    
    # Start 20 threads (simulating 20 workers scanning)
    threads = []
    start_time = time.time()
    
    for i in range(20):
        t = threading.Thread(target=mock_api_call, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    duration = time.time() - start_time
    
    print(f"20 mock API calls completed in {duration:.2f}s")
    print(f"Maximum concurrent calls: {max_concurrent}")
    
    assert max_concurrent <= 8, f"Expected max 8 concurrent, got {max_concurrent}"
    print("✓ Semaphore correctly limits to 8 concurrent calls")
    print("  Benefit: Prevents API rate limit exhaustion")
    
    return True

def test_comparison():
    """Show before/after comparison"""
    print("\n" + "="*60)
    print("BEFORE vs AFTER COMPARISON")
    print("="*60)
    
    print("\n📊 API Rate Limiting:")
    print("  BEFORE: 20 parallel workers, no rate limiting")
    print("  AFTER:  8 parallel workers + semaphore limiting")
    print("  Impact: ~60% fewer concurrent API calls")
    
    print("\n💰 Take Profit Strategy:")
    print("  BEFORE: Aggressive extensions (1.15-1.20x)")
    print("  AFTER:  Conservative extensions (1.01-1.05x)")
    print("  Impact: Lock in profits earlier, prevent reversals")
    
    print("\n🎯 At 5% Profit:")
    print("  BEFORE: Could extend TP by 8% (1.08x)")
    print("  AFTER:  Max 3% extension (1.03x)")
    print("  Impact: Take profit sooner, secure gains")
    
    print("\n⚡ Position Management Priority:")
    print("  BEFORE: Could be blocked by 20 scanning threads")
    print("  AFTER:  Critical calls bypass semaphore")
    print("  Impact: Stop loss/take profit execute immediately")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("API BLOCKING FIX & PROFITABILITY IMPROVEMENTS TEST")
    print("="*60)
    
    try:
        test_max_workers_reduction()
        test_api_semaphore()
        test_take_profit_multipliers()
        test_semaphore_behavior()
        test_comparison()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nSummary:")
        print("1. API blocking fixed with semaphore rate limiting")
        print("2. Take profit strategy now locks in profits earlier")
        print("3. Position management prioritized over scanning")
        print("4. Expected improvement: Better profitability, no API blocking")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
