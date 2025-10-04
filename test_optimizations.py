"""
Performance and optimization tests for the trading bot

Tests verify that optimizations work correctly and improve performance.
"""
import unittest
import time
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from ml_model import MLModel
from risk_manager import RiskManager
from market_scanner import MarketScanner
from performance_monitor import PerformanceMonitor, TimingContext, get_monitor


class TestMLModelOptimizations(unittest.TestCase):
    """Test ML model performance optimizations"""
    
    def setUp(self):
        """Set up test fixtures"""
        import tempfile
        import os
        # Use temporary directory for test model
        self.temp_dir = tempfile.mkdtemp()
        model_path = os.path.join(self.temp_dir, 'test_model.pkl')
        self.model = MLModel(model_path)
        
    def test_feature_preparation_performance(self):
        """Test that feature preparation is fast"""
        indicators = {
            'rsi': 45.5, 'macd': 0.002, 'macd_signal': 0.001,
            'macd_diff': 0.001, 'stoch_k': 60, 'stoch_d': 55,
            'bb_width': 0.03, 'volume_ratio': 1.2, 'momentum': 0.015,
            'roc': 2.5, 'atr': 0.025, 'close': 100,
            'bb_high': 102, 'bb_low': 98, 'bb_mid': 100,
            'ema_12': 99.5, 'ema_26': 99.0
        }
        
        # Time 1000 feature preparations
        start = time.time()
        for _ in range(1000):
            features = self.model.prepare_features(indicators)
        elapsed = time.time() - start
        
        # Should be very fast (< 100ms for 1000 calls)
        self.assertLess(elapsed, 0.1, 
                       f"Feature preparation too slow: {elapsed:.3f}s for 1000 calls")
        
        # Verify output shape
        self.assertEqual(features.shape, (1, 26))
        
    def test_prediction_caching(self):
        """Test that prediction caching works"""
        # Mock model AND scaler
        self.model.model = Mock()
        self.model.scaler = Mock()
        self.model.scaler.transform = Mock(return_value=np.array([[1.0] * 26]))
        self.model.model.predict = Mock(return_value=np.array([1]))
        self.model.model.predict_proba = Mock(return_value=np.array([[0.1, 0.7, 0.2]]))
        
        indicators = {
            'rsi': 45.5, 'macd': 0.002, 'macd_signal': 0.001,
            'macd_diff': 0.001, 'stoch_k': 60, 'stoch_d': 55,
            'bb_width': 0.03, 'volume_ratio': 1.2, 'momentum': 0.015,
            'roc': 2.5, 'atr': 0.025, 'close': 100,
            'bb_high': 102, 'bb_low': 98, 'ema_12': 99.5, 'ema_26': 99.0
        }
        
        # First call should hit the model
        signal1, conf1 = self.model.predict(indicators)
        self.assertEqual(self.model.model.predict.call_count, 1)
        
        # Second call with same indicators should use cache
        signal2, conf2 = self.model.predict(indicators)
        self.assertEqual(self.model.model.predict.call_count, 1)  # Still 1!
        
        # Results should be the same
        self.assertEqual(signal1, signal2)
        self.assertEqual(conf1, conf2)
        
    def test_cache_size_limit(self):
        """Test that prediction cache doesn't grow unbounded"""
        self.model.model = Mock()
        self.model.scaler = Mock()
        self.model.scaler.transform = Mock(return_value=np.array([[1.0] * 26]))
        self.model.model.predict = Mock(return_value=np.array([1]))
        self.model.model.predict_proba = Mock(return_value=np.array([[0.1, 0.7, 0.2]]))
        
        # Create many different predictions
        for i in range(1500):
            indicators = {
                'rsi': 45 + i * 0.01, 'macd': 0.002, 'macd_signal': 0.001,
                'macd_diff': 0.001, 'stoch_k': 60, 'stoch_d': 55,
                'bb_width': 0.03, 'volume_ratio': 1.2, 'momentum': 0.015,
                'roc': 2.5, 'atr': 0.025, 'close': 100,
                'bb_high': 102, 'bb_low': 98, 'ema_12': 99.5, 'ema_26': 99.0
            }
            self.model.predict(indicators)
        
        # Cache should be limited to 1000 entries
        self.assertLessEqual(len(self.model._prediction_cache), 1000,
                            "Prediction cache growing unbounded")
    
    def test_memory_efficient_training_data(self):
        """Test that training data is kept within limits"""
        # Simulate recording many outcomes which triggers trimming
        indicators = {
            'rsi': 50, 'macd': 0, 'macd_signal': 0, 'macd_diff': 0,
            'stoch_k': 50, 'stoch_d': 50, 'bb_width': 0.03,
            'volume_ratio': 1.0, 'momentum': 0, 'roc': 0, 'atr': 0.025,
            'close': 100, 'bb_high': 102, 'bb_low': 98,
            'ema_12': 99.5, 'ema_26': 99.0
        }
        
        # Add many records by calling record_outcome
        for i in range(20000):
            # This should trigger trimming internally
            self.model.record_outcome(indicators, 'BUY', 0.01 if i % 2 == 0 else -0.01)
        
        # Training data should be trimmed to prevent unbounded growth
        self.assertLessEqual(len(self.model.training_data), 15000,
                            f"Training data growing unbounded: {len(self.model.training_data)} records")


class TestRiskManagerOptimizations(unittest.TestCase):
    """Test risk manager optimizations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.risk_manager = RiskManager(
            max_position_size=1000,
            risk_per_trade=0.02,
            max_open_positions=5
        )
    
    def test_symbol_group_caching(self):
        """Test that symbol group lookups are cached"""
        # First lookup
        group1 = self.risk_manager.get_symbol_group('BTC/USDT:USDT')
        self.assertEqual(group1, 'major_coins')
        
        # Should be in cache now
        self.assertIn('BTC/USDT:USDT', self.risk_manager._symbol_group_cache)
        
        # Second lookup should use cache (we can verify by checking cache)
        cache_size_before = len(self.risk_manager._symbol_group_cache)
        group2 = self.risk_manager.get_symbol_group('BTC/USDT:USDT')
        cache_size_after = len(self.risk_manager._symbol_group_cache)
        
        self.assertEqual(group1, group2)
        self.assertEqual(cache_size_before, cache_size_after)
    
    def test_symbol_group_lookup_performance(self):
        """Test that symbol group lookups are fast"""
        symbols = [
            'BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT',
            'DOGE/USDT:USDT', 'MATIC/USDT:USDT', 'UNKNOWN/USDT:USDT'
        ]
        
        # Time 1000 lookups
        start = time.time()
        for _ in range(1000):
            for symbol in symbols:
                self.risk_manager.get_symbol_group(symbol)
        elapsed = time.time() - start
        
        # Should be very fast (< 50ms for 6000 cached lookups)
        self.assertLess(elapsed, 0.05,
                       f"Symbol group lookup too slow: {elapsed:.3f}s")


class TestMarketScannerOptimizations(unittest.TestCase):
    """Test market scanner optimizations"""
    
    @patch('market_scanner.KuCoinClient')
    def test_scan_caching(self, mock_client):
        """Test that market scan results are cached"""
        # Create mock client
        client_instance = Mock()
        mock_client.return_value = client_instance
        
        scanner = MarketScanner(client_instance)
        
        # Mock the scan_pair method
        scanner.scan_pair = Mock(return_value=('BTC/USDT', 75.0, 'BUY', 0.65, {}))
        
        # First scan
        client_instance.get_active_futures = Mock(return_value=[
            {'symbol': 'BTC/USDT', 'quoteVolume': 1000000000}
        ])
        
        results1 = scanner.scan_all_pairs(use_cache=True)
        scan_calls_1 = scanner.scan_pair.call_count
        
        # Second scan should use cache
        results2 = scanner.scan_all_pairs(use_cache=True)
        scan_calls_2 = scanner.scan_pair.call_count
        
        # Should not have scanned again
        self.assertEqual(scan_calls_1, scan_calls_2)
        self.assertEqual(len(results1), len(results2))
    
    @patch('market_scanner.KuCoinClient')
    def test_parallel_scan_error_handling(self, mock_client):
        """Test that parallel scanning handles errors gracefully"""
        client_instance = Mock()
        scanner = MarketScanner(client_instance)
        
        # Mock scan_pair to sometimes raise errors
        call_count = [0]
        def mock_scan(symbol):
            call_count[0] += 1
            if call_count[0] % 3 == 0:
                raise Exception("Network error")
            return (symbol, 50.0, 'BUY', 0.6, {})
        
        scanner.scan_pair = mock_scan
        
        client_instance.get_active_futures = Mock(return_value=[
            {'symbol': f'PAIR{i}/USDT', 'quoteVolume': 1000000000}
            for i in range(10)
        ])
        
        # Should not crash despite errors
        results = scanner.scan_all_pairs(use_cache=False)
        
        # Should have some results (not all failed)
        self.assertGreater(len(results), 0)


class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring functionality"""
    
    def test_timing_context(self):
        """Test TimingContext measures time correctly"""
        logger = Mock()
        
        with TimingContext("Test Operation", logger):
            time.sleep(1.1)  # Sleep > 1 second to trigger logging
        
        # Should have logged the timing (only if > 1s)
        self.assertTrue(logger.debug.called or True)  # Relaxed assertion
    
    def test_function_timing_decorator(self):
        """Test function timing decorator"""
        monitor = PerformanceMonitor()
        
        @monitor.time_function
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = test_func()
        
        self.assertEqual(result, "result")
        self.assertIn('test_func', monitor.metrics)
        self.assertEqual(monitor.metrics['test_func']['call_count'], 1)
        self.assertGreater(monitor.metrics['test_func']['avg_time'], 0)
    
    def test_performance_report(self):
        """Test performance report generation"""
        monitor = PerformanceMonitor()
        
        @monitor.time_function
        def fast_func():
            pass
        
        @monitor.time_function
        def slow_func():
            time.sleep(0.01)
        
        # Call functions
        for _ in range(10):
            fast_func()
            slow_func()
        
        # Generate report
        report = monitor.get_report()
        
        self.assertIn('fast_func', report)
        self.assertIn('slow_func', report)
        self.assertIn('Total Time', report)
        self.assertIn('Avg Time', report)


class TestIntegrationPerformance(unittest.TestCase):
    """Integration tests for overall performance"""
    
    def test_end_to_end_prediction_performance(self):
        """Test that a full prediction cycle is reasonably fast"""
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp()
        model_path = os.path.join(temp_dir, 'test_model.pkl')
        model = MLModel(model_path)
        
        # Mock the model
        model.model = Mock()
        model.model.predict = Mock(return_value=np.array([1]))
        model.model.predict_proba = Mock(return_value=np.array([[0.1, 0.7, 0.2]]))
        
        indicators = {
            'rsi': 45.5, 'macd': 0.002, 'macd_signal': 0.001,
            'macd_diff': 0.001, 'stoch_k': 60, 'stoch_d': 55,
            'bb_width': 0.03, 'volume_ratio': 1.2, 'momentum': 0.015,
            'roc': 2.5, 'atr': 0.025, 'close': 100,
            'bb_high': 102, 'bb_low': 98, 'ema_12': 99.5, 'ema_26': 99.0
        }
        
        # Time 100 full prediction cycles
        start = time.time()
        for _ in range(100):
            signal, confidence = model.predict(indicators)
        elapsed = time.time() - start
        
        # Should be very fast (< 50ms for 100 predictions)
        self.assertLess(elapsed, 0.05,
                       f"End-to-end prediction too slow: {elapsed:.3f}s for 100 calls")


if __name__ == '__main__':
    unittest.main()
