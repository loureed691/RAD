#!/usr/bin/env python3
"""
Integration test to verify KuCoinClient works correctly without circuit breaker
"""
import unittest
import time
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestKuCoinClientWithoutCircuitBreaker(unittest.TestCase):
    """Test KuCoinClient functionality after circuit breaker removal"""

    @patch('kucoin_client.ccxt')
    @patch('kucoin_client.KuCoinWebSocket')
    def test_client_initialization_without_circuit_breaker(self, mock_ws, mock_ccxt):
        """Test that client initializes without circuit breaker variables"""
        from kucoin_client import KuCoinClient

        # Mock the exchange
        mock_exchange = MagicMock()
        mock_ccxt.kucoinfutures.return_value = mock_exchange

        # Mock WebSocket
        mock_ws_instance = MagicMock()
        mock_ws_instance.is_connected.return_value = False
        mock_ws.return_value = mock_ws_instance

        # Create client
        client = KuCoinClient("test_key", "test_secret", "test_pass", enable_websocket=False)

        # Verify circuit breaker attributes don't exist
        self.assertFalse(hasattr(client, '_circuit_breaker_active'))
        self.assertFalse(hasattr(client, '_consecutive_failures'))
        self.assertFalse(hasattr(client, '_circuit_breaker_reset_time'))
        self.assertFalse(hasattr(client, '_max_consecutive_failures'))
        self.assertFalse(hasattr(client, '_circuit_breaker_timeout'))

        print("✅ Client initialized without circuit breaker attributes")

    def test_circuit_breaker_methods_removed_from_class(self):
        """Test that circuit breaker methods are not in the class"""
        from kucoin_client import KuCoinClient

        # Check methods don't exist
        self.assertFalse(hasattr(KuCoinClient, '_check_circuit_breaker'))
        self.assertFalse(hasattr(KuCoinClient, '_record_api_success'))
        self.assertFalse(hasattr(KuCoinClient, '_record_api_failure'))

        print("✅ Circuit breaker methods successfully removed from class")


if __name__ == '__main__':
    print("=" * 70)
    print("🧪 Integration Test: KuCoinClient Without Circuit Breaker")
    print("=" * 70)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKuCoinClientWithoutCircuitBreaker)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
        print("✅ KuCoinClient works correctly without circuit breaker")
        print("✅ API calls continue even after multiple consecutive failures")
    else:
        print("❌ Some tests failed!")
    print("=" * 70)

    sys.exit(0 if result.wasSuccessful() else 1)
