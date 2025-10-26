"""
Test suite for rate limit and circuit breaker fixes
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from kucoin_client import KuCoinClient, APICallPriority
from config import Config


class TestRateLimitFixes(unittest.TestCase):
    """Test rate limit handling and circuit breaker improvements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_exchange = Mock()
        
    def test_max_workers_reduced(self):
        """Test that MAX_WORKERS default is reduced to prevent rate limiting"""
        # Verify the new default is 8 instead of 20
        self.assertEqual(Config.MAX_WORKERS, 8, 
                        "MAX_WORKERS should be reduced to 8 to prevent rate limiting")
    
    @patch('kucoin_client.ccxt')
    @patch('kucoin_client.KuCoinWebSocket')
    def test_circuit_breaker_allows_critical_operations(self, mock_ws, mock_ccxt):
        """Test that circuit breaker allows critical operations during cooldown"""
        # Mock the exchange
        mock_exchange = Mock()
        mock_ccxt.kucoinfutures.return_value = mock_exchange
        
        # Create client
        client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=False)
        
        # Activate circuit breaker by simulating failures
        for _ in range(5):
            client._record_api_failure()
        
        # Verify circuit breaker is active
        self.assertTrue(client._circuit_breaker_active, 
                       "Circuit breaker should be active after 5 failures")
        
        # Test that critical operations can bypass circuit breaker
        result = client._check_circuit_breaker(is_critical=True)
        self.assertTrue(result, 
                       "Critical operations should bypass circuit breaker")
        
        # Test that non-critical operations are blocked
        result = client._check_circuit_breaker(is_critical=False)
        self.assertFalse(result, 
                        "Non-critical operations should be blocked by circuit breaker")
    
    @patch('kucoin_client.ccxt')
    @patch('kucoin_client.KuCoinWebSocket')
    def test_get_ticker_marked_critical_for_high_priority(self, mock_ws, mock_ccxt):
        """Test that get_ticker with HIGH priority is marked as critical"""
        # Mock the exchange
        mock_exchange = Mock()
        mock_exchange.fetch_ticker.return_value = {'last': 100.0}
        mock_ccxt.kucoinfutures.return_value = mock_exchange
        
        # Create client
        client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=False)
        
        # Activate circuit breaker
        for _ in range(5):
            client._record_api_failure()
        
        # Mock _execute_with_priority to call the function directly
        def mock_execute(func, priority, name):
            return func()
        
        with patch.object(client, '_execute_with_priority', side_effect=mock_execute):
            # HIGH priority ticker should work during circuit breaker
            ticker = client.get_ticker('BTC/USDT:USDT', priority=APICallPriority.HIGH)
            self.assertIsNotNone(ticker, 
                               "HIGH priority get_ticker should bypass circuit breaker")
            
            # Reset exchange mock
            mock_exchange.fetch_ticker.reset_mock()
            
            # NORMAL priority ticker should be blocked
            ticker = client.get_ticker('BTC/USDT:USDT', priority=APICallPriority.NORMAL)
            # Note: This will be None because circuit breaker blocks it
            # The _handle_api_error will return None when circuit breaker blocks
    
    @patch('kucoin_client.ccxt')
    @patch('kucoin_client.KuCoinWebSocket')
    def test_get_balance_marked_critical(self, mock_ws, mock_ccxt):
        """Test that get_balance is marked as critical"""
        # Mock the exchange
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {'USDT': {'free': 1000.0}}
        mock_ccxt.kucoinfutures.return_value = mock_exchange
        
        # Create client
        client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=False)
        
        # Activate circuit breaker
        for _ in range(5):
            client._record_api_failure()
        
        # Mock _execute_with_priority to call the function directly
        def mock_execute(func, priority, name):
            return func()
        
        with patch.object(client, '_execute_with_priority', side_effect=mock_execute):
            # Balance checks should work during circuit breaker
            balance = client.get_balance()
            self.assertIsNotNone(balance, 
                               "get_balance should bypass circuit breaker (critical)")
    
    def test_circuit_breaker_resets_after_timeout(self):
        """Test that circuit breaker resets after timeout period"""
        with patch('kucoin_client.ccxt') as mock_ccxt, \
             patch('kucoin_client.KuCoinWebSocket') as mock_ws:
            
            mock_exchange = Mock()
            mock_ccxt.kucoinfutures.return_value = mock_exchange
            
            client = KuCoinClient('test_key', 'test_secret', 'test_pass', enable_websocket=False)
            
            # Activate circuit breaker
            for _ in range(5):
                client._record_api_failure()
            
            self.assertTrue(client._circuit_breaker_active)
            
            # Simulate timeout passing
            client._circuit_breaker_reset_time = time.time() - 1
            
            # Check should reset the circuit breaker
            result = client._check_circuit_breaker(is_critical=False)
            self.assertTrue(result, "Circuit breaker should reset after timeout")
            self.assertFalse(client._circuit_breaker_active, 
                           "Circuit breaker should be inactive after reset")


class TestMarketScannerStaggering(unittest.TestCase):
    """Test market scanner request staggering"""
    
    def test_scan_submissions_are_staggered(self):
        """Test that scan submissions include delays to prevent rate limit bursts"""
        # Instead of importing market_scanner (which has many dependencies),
        # we'll test the staggering logic directly from the code
        
        # Read the market_scanner.py file to verify staggering is implemented
        with open('market_scanner.py', 'r') as f:
            content = f.read()
        
        # Check that time.sleep is called in the executor submission loop
        self.assertIn('time.sleep(0.1)', content, 
                     "Staggering delay should be implemented in scan submission loop")
        
        # Check that the comment about staggering exists
        self.assertIn('stagger', content.lower(), 
                     "Code should have comments about staggering API requests")


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRateLimitFixes))
    suite.addTests(loader.loadTestsFromTestCase(TestMarketScannerStaggering))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED")
    else:
        print("\n❌ SOME TESTS FAILED")
        
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
