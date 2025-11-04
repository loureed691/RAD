"""
Tests for performance improvements and bug fixes
"""
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_nested_loop_optimization():
    """Test that nested loop optimization in risk_manager works correctly"""
    print("\n" + "=" * 80)
    print("TEST: Nested Loop Optimization in RiskManager")
    print("=" * 80)

    from risk_manager import RiskManager
    from position_manager import Position

    # Create risk manager
    rm = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=5)

    # Create mock positions in the same correlation group
    class MockPosition:
        def __init__(self, symbol):
            self.symbol = symbol

    # Test with positions in same group (defi)
    positions = [
        MockPosition('UNI/USDT:USDT'),
        MockPosition('AAVE/USDT:USDT'),
    ]

    # Should reject - already 2 in group
    is_safe, reason = rm.check_correlation_risk('SUSHI/USDT:USDT', positions)
    assert not is_safe, "Should reject third position in same group"
    assert 'too_many_in_defi_group' in reason, f"Wrong reason: {reason}"

    # Should allow - different group
    is_safe, reason = rm.check_correlation_risk('BTC/USDT:USDT', positions)
    assert is_safe, "Should allow position from different group"

    print("✓ Nested loop optimization works correctly")
    print("✓ Correlation risk check passes")

    # Performance test
    print("\nPerformance comparison:")

    # Create many positions for performance test
    large_positions = [MockPosition(f'TEST{i}/USDT:USDT') for i in range(100)]

    start = time.time()
    for _ in range(100):
        rm.check_correlation_risk('BTC/USDT:USDT', large_positions)
    duration = time.time() - start

    print(f"  100 checks with 100 positions: {duration*1000:.2f}ms")
    print(f"  Average per check: {duration*10:.2f}ms")

    if duration < 0.1:  # Should be fast with O(n) optimization
        print("  ✓ Performance excellent (< 100ms for 100 iterations)")
    else:
        print("  ⚠ Performance could be better")

    return True


def test_config_validation():
    """Test configuration validation with safety bounds"""
    print("\n" + "=" * 80)
    print("TEST: Configuration Validation")
    print("=" * 80)

    from config import Config

    # Save original API keys
    original_key = Config.API_KEY
    original_secret = Config.API_SECRET
    original_pass = Config.API_PASSPHRASE

    # Set dummy API keys for testing
    Config.API_KEY = "test_key"
    Config.API_SECRET = "test_secret"
    Config.API_PASSPHRASE = "test_pass"

    try:
        # Test leverage validation
        print("\nTesting leverage bounds:")
        original_leverage = Config.LEVERAGE

        try:
            Config.LEVERAGE = 0
            try:
                Config.validate()
                print("  ✗ Should reject leverage = 0")
                return False
            except ValueError as e:
                print(f"  ✓ Correctly rejected leverage = 0: {e}")

            Config.LEVERAGE = 25
            try:
                Config.validate()
                print("  ✗ Should reject leverage = 25")
                return False
            except ValueError as e:
                print(f"  ✓ Correctly rejected leverage = 25: {e}")

            Config.LEVERAGE = 10
            Config.validate()
            print("  ✓ Accepts valid leverage = 10")

        finally:
            Config.LEVERAGE = original_leverage

        # Test position size validation
        print("\nTesting position size bounds:")
        original_size = Config.MAX_POSITION_SIZE

        try:
            Config.MAX_POSITION_SIZE = -100
            try:
                Config.validate()
                print("  ✗ Should reject negative position size")
                return False
            except ValueError as e:
                print(f"  ✓ Correctly rejected negative size: {e}")

            Config.MAX_POSITION_SIZE = 2000000  # $2M
            try:
                Config.validate()
                print("  ✗ Should reject unreasonably large position size")
                return False
            except ValueError as e:
                print(f"  ✓ Correctly rejected large size: {e}")

            Config.MAX_POSITION_SIZE = 5000
            Config.validate()
            print("  ✓ Accepts valid position size = 5000")

        finally:
            Config.MAX_POSITION_SIZE = original_size

        print("\n✓ Configuration validation works correctly")
        return True

    finally:
        # Restore original API keys
        Config.API_KEY = original_key
        Config.API_SECRET = original_secret
        Config.API_PASSPHRASE = original_pass


def test_performance_monitor():
    """Test performance monitoring functionality"""
    print("\n" + "=" * 80)
    print("TEST: Performance Monitor")
    print("=" * 80)

    from performance_monitor import get_monitor

    monitor = get_monitor()

    # Record some test metrics
    print("\nRecording test metrics...")

    for i in range(10):
        monitor.record_scan_time(0.5 + i * 0.1)
        monitor.record_api_call(0.05 + i * 0.01, success=True)

    # Record some errors
    monitor.record_api_call(1.0, success=False)
    monitor.record_api_call(0.8, success=True, retried=True)

    # Get stats
    stats = monitor.get_stats()

    print(f"\nStats collected:")
    print(f"  Scan samples: {stats['scan']['samples']}")
    print(f"  Avg scan time: {stats['scan']['avg_time']:.2f}s")
    print(f"  API calls: {stats['api']['total_calls']}")
    print(f"  API avg time: {stats['api']['avg_time']:.3f}s")
    print(f"  API error rate: {stats['api']['error_rate']:.1%}")
    print(f"  API retry rate: {stats['api']['retry_rate']:.1%}")

    assert stats['scan']['samples'] == 10, "Should have 10 scan samples"
    assert stats['api']['total_calls'] == 12, "Should have 12 API calls"
    assert stats['api']['errors'] == 1, "Should have 1 error"
    assert stats['api']['retries'] == 1, "Should have 1 retry"

    print("\n✓ Performance monitor working correctly")

    # Test health check
    is_healthy, reason = monitor.check_health()
    print(f"\nHealth check: {is_healthy} - {reason}")

    return True


def test_reproducibility():
    """Test that random seed is set for reproducibility"""
    print("\n" + "=" * 80)
    print("TEST: Reproducibility (Random Seed)")
    print("=" * 80)

    import random
    import numpy as np

    # Generate some random numbers
    rand_nums_1 = [random.random() for _ in range(5)]
    np_nums_1 = np.random.rand(5)

    print(f"\nFirst run random numbers: {rand_nums_1[:3]}")
    print(f"First run numpy numbers: {np_nums_1[:3]}")

    # Reset seeds
    random.seed(42)
    np.random.seed(42)

    # Generate again
    rand_nums_2 = [random.random() for _ in range(5)]
    np_nums_2 = np.random.rand(5)

    print(f"Second run random numbers: {rand_nums_2[:3]}")
    print(f"Second run numpy numbers: {np_nums_2[:3]}")

    # Should be identical
    assert rand_nums_1 == rand_nums_2, "Random numbers should be reproducible"
    assert np.array_equal(np_nums_1, np_nums_2), "Numpy arrays should be reproducible"

    print("\n✓ Reproducibility confirmed - random seed working")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("PERFORMANCE IMPROVEMENTS AND BUG FIXES TEST SUITE")
    print("=" * 80)

    tests = [
        ("Nested Loop Optimization", test_nested_loop_optimization),
        ("Configuration Validation", test_config_validation),
        ("Performance Monitor", test_performance_monitor),
        ("Reproducibility", test_reproducibility),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name}: FAILED with exception")
            print(f"   Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
