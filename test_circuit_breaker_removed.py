#!/usr/bin/env python3
"""
Test to verify circuit breaker has been successfully removed
"""
import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kucoin_client import KuCoinClient, APICallPriority


class TestCircuitBreakerRemoved(unittest.TestCase):
    """Test suite to verify circuit breaker functionality has been removed"""

    def test_circuit_breaker_methods_removed(self):
        """Verify that circuit breaker methods no longer exist"""
        # Check that the circuit breaker methods are not present
        self.assertFalse(
            hasattr(KuCoinClient, '_check_circuit_breaker'),
            "Circuit breaker check method should be removed"
        )
        self.assertFalse(
            hasattr(KuCoinClient, '_record_api_success'),
            "API success recording method should be removed"
        )
        self.assertFalse(
            hasattr(KuCoinClient, '_record_api_failure'),
            "API failure recording method should be removed"
        )

    def test_kucoin_client_instantiation(self):
        """Test that KuCoinClient can still be imported and defined"""
        # This just verifies the class exists and can be referenced
        self.assertTrue(KuCoinClient is not None)
        self.assertTrue(callable(KuCoinClient))

    def test_api_call_priority_enum_exists(self):
        """Test that APICallPriority enum still exists"""
        self.assertTrue(APICallPriority is not None)
        self.assertTrue(hasattr(APICallPriority, 'CRITICAL'))
        self.assertTrue(hasattr(APICallPriority, 'HIGH'))
        self.assertTrue(hasattr(APICallPriority, 'NORMAL'))
        self.assertTrue(hasattr(APICallPriority, 'LOW'))


if __name__ == '__main__':
    print("=" * 70)
    print("🧪 Testing Circuit Breaker Removal")
    print("=" * 70)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCircuitBreakerRemoved)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ All tests passed! Circuit breaker successfully removed.")
    else:
        print("❌ Some tests failed!")
    print("=" * 70)

    sys.exit(0 if result.wasSuccessful() else 1)
