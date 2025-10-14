"""
Tests for 2025 AI Enhancement Modules
"""
import unittest
import numpy as np
from enhanced_order_book_2025 import EnhancedOrderBookAnalyzer
from bayesian_kelly_2025 import BayesianAdaptiveKelly
from attention_features_2025 import AttentionFeatureSelector


class TestEnhancedOrderBook(unittest.TestCase):
    """Test enhanced order book analysis"""
    
    def setUp(self):
        self.analyzer = EnhancedOrderBookAnalyzer()
        self.sample_order_book = {
            'bids': [
                [50000.0, 1.5],
                [49950.0, 2.0],
                [49900.0, 1.8],
                [49850.0, 2.2],
                [49800.0, 1.9]
            ],
            'asks': [
                [50050.0, 1.2],
                [50100.0, 1.8],
                [50150.0, 1.5],
                [50200.0, 2.0],
                [50250.0, 1.7]
            ]
        }
    
    def test_calculate_vamp(self):
        """Test VAMP calculation"""
        vamp = self.analyzer.calculate_vamp(self.sample_order_book)
        self.assertIsNotNone(vamp)
        self.assertGreater(vamp, 49900)
        self.assertLess(vamp, 50100)
        print(f"✓ VAMP calculated: {vamp:.2f}")
    
    def test_calculate_wdop(self):
        """Test WDOP calculation"""
        wdop_bid, wdop_ask = self.analyzer.calculate_wdop(self.sample_order_book)
        self.assertIsNotNone(wdop_bid)
        self.assertIsNotNone(wdop_ask)
        self.assertLess(wdop_bid, wdop_ask)
        print(f"✓ WDOP calculated: Bid={wdop_bid:.2f}, Ask={wdop_ask:.2f}")
    
    def test_calculate_enhanced_obi(self):
        """Test enhanced OBI calculation"""
        obi_metrics = self.analyzer.calculate_enhanced_obi(self.sample_order_book)
        self.assertIn('obi', obi_metrics)
        self.assertIn('obi_strength', obi_metrics)
        self.assertIn('obi_trend', obi_metrics)
        self.assertGreaterEqual(obi_metrics['obi'], -1.0)
        self.assertLessEqual(obi_metrics['obi'], 1.0)
        print(f"✓ OBI calculated: {obi_metrics['obi']:.3f} ({obi_metrics['obi_strength']})")
    
    def test_predict_slippage(self):
        """Test slippage prediction"""
        slippage = self.analyzer.predict_slippage(self.sample_order_book, 100000, 'buy')
        self.assertIn('predicted_slippage_pct', slippage)
        self.assertIn('can_fill', slippage)
        self.assertGreaterEqual(slippage['predicted_slippage_pct'], 0)
        print(f"✓ Slippage predicted: {slippage['predicted_slippage_pct']:.2f}%")
    
    def test_get_execution_score(self):
        """Test execution score calculation"""
        score = self.analyzer.get_execution_score(self.sample_order_book, 50000, 'buy')
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        print(f"✓ Execution score: {score:.2f}")
    
    def test_should_execute_now(self):
        """Test execution decision"""
        should_exec, reason = self.analyzer.should_execute_now(
            self.sample_order_book, 50000, 'buy', min_score=0.5
        )
        self.assertIsInstance(should_exec, bool)
        self.assertIsInstance(reason, str)
        print(f"✓ Execution decision: {should_exec} - {reason}")


class TestBayesianKelly(unittest.TestCase):
    """Test Bayesian Adaptive Kelly Criterion"""
    
    def setUp(self):
        self.kelly = BayesianAdaptiveKelly(base_kelly_fraction=0.25)
        
        # Add some sample trade history
        for i in range(30):
            # 60% win rate
            win = i % 5 != 0  # 4 out of 5 trades win
            profit_loss = 0.02 if win else -0.01
            self.kelly.update_trade_outcome(win, profit_loss)
    
    def test_calculate_bayesian_win_rate(self):
        """Test Bayesian win rate calculation"""
        win_stats = self.kelly.calculate_bayesian_win_rate()
        self.assertIn('mean', win_stats)
        self.assertIn('std', win_stats)
        self.assertIn('n_trades', win_stats)
        self.assertGreaterEqual(win_stats['mean'], 0.0)
        self.assertLessEqual(win_stats['mean'], 1.0)
        print(f"✓ Bayesian win rate: {win_stats['mean']:.3f} ± {win_stats['std']:.3f}")
    
    def test_calculate_dynamic_kelly_fraction(self):
        """Test dynamic Kelly fraction"""
        fraction = self.kelly.calculate_dynamic_kelly_fraction(
            uncertainty=0.1, market_volatility=0.03
        )
        self.assertGreater(fraction, 0.0)
        self.assertLess(fraction, 0.5)
        print(f"✓ Dynamic Kelly fraction: {fraction:.3f}")
    
    def test_calculate_optimal_position_size(self):
        """Test optimal position sizing"""
        result = self.kelly.calculate_optimal_position_size(
            balance=10000, confidence=0.7, market_volatility=0.03
        )
        self.assertIn('position_size', result)
        self.assertIn('recommendation', result)
        self.assertGreater(result['position_size'], 0)
        self.assertLess(result['position_size'], 10000)
        print(f"✓ Optimal position: ${result['position_size']:.2f} ({result['recommendation']})")
    
    def test_get_risk_recommendation(self):
        """Test comprehensive risk recommendation"""
        rec = self.kelly.get_risk_recommendation(
            balance=10000, confidence=0.7, market_regime='neutral'
        )
        self.assertIn('position_size', rec)
        self.assertIn('max_recommended_leverage', rec)
        print(f"✓ Risk recommendation: ${rec['position_size']:.2f}, "
              f"max leverage: {rec['max_recommended_leverage']}x")
    
    def test_conservative_with_limited_data(self):
        """Test that system is conservative with limited data"""
        kelly_new = BayesianAdaptiveKelly()
        result = kelly_new.calculate_optimal_position_size(
            balance=10000, confidence=0.7
        )
        # Should use very conservative sizing with no history
        self.assertLess(result['position_size'], 200)  # Less than 2%
        print(f"✓ Conservative sizing with no data: ${result['position_size']:.2f}")


class TestAttentionFeatures(unittest.TestCase):
    """Test attention-based feature selection"""
    
    def setUp(self):
        self.attention = AttentionFeatureSelector(n_features=31)
        self.sample_features = np.random.randn(31) * 10
    
    def test_calculate_attention_scores(self):
        """Test attention score calculation"""
        scores = self.attention.calculate_attention_scores(self.sample_features)
        self.assertEqual(len(scores), 31)
        self.assertAlmostEqual(np.sum(scores), 1.0, places=5)  # Should sum to 1
        self.assertTrue(np.all(scores >= 0))  # All non-negative
        print(f"✓ Attention scores sum: {np.sum(scores):.6f}")
    
    def test_apply_attention(self):
        """Test attention application to features"""
        weighted = self.attention.apply_attention(self.sample_features)
        self.assertEqual(len(weighted), 31)
        # Weighted features should be different from original
        self.assertFalse(np.array_equal(weighted, self.sample_features))
        print(f"✓ Attention applied, mean weight: {np.mean(weighted/self.sample_features):.2f}")
    
    def test_update_attention_weights(self):
        """Test attention weight updates"""
        initial_weights = self.attention.attention_weights.copy()
        
        # Simulate multiple trades
        for i in range(20):
            features = np.random.randn(31) * 10
            outcome = i % 3 != 0  # ~66% win rate
            profit = 0.02 if outcome else -0.01
            self.attention.update_attention_weights(features, outcome, profit)
        
        # Weights should have changed
        self.assertFalse(np.array_equal(
            initial_weights, self.attention.attention_weights
        ))
        print(f"✓ Weights updated after learning")
    
    def test_get_feature_importance(self):
        """Test feature importance retrieval"""
        importance = self.attention.get_feature_importance()
        self.assertEqual(len(importance), 31)
        self.assertTrue(all(isinstance(v, float) for v in importance.values()))
        print(f"✓ Feature importance calculated: {len(importance)} features")
    
    def test_get_top_features(self):
        """Test getting top N features"""
        top = self.attention.get_top_features(n=5)
        self.assertEqual(len(top), 5)
        # Should be sorted by importance
        importances = [t[1] for t in top]
        self.assertEqual(importances, sorted(importances, reverse=True))
        print(f"✓ Top 5 features: {[t[0] for t in top]}")
    
    def test_boost_regime_features(self):
        """Test regime-specific feature boosting"""
        boosted = self.attention.boost_regime_features(
            self.sample_features, 'trending', boost_factor=1.5
        )
        self.assertEqual(len(boosted), 31)
        # Some features should be boosted
        self.assertGreater(np.sum(np.abs(boosted)), np.sum(np.abs(self.sample_features)))
        print(f"✓ Regime features boosted")


class TestIntegration(unittest.TestCase):
    """Test integration between modules"""
    
    def test_full_pipeline(self):
        """Test complete enhancement pipeline"""
        # Initialize all modules
        order_book = EnhancedOrderBookAnalyzer()
        kelly = BayesianAdaptiveKelly()
        attention = AttentionFeatureSelector()
        
        # Sample data
        sample_order_book = {
            'bids': [[50000.0, 1.5], [49950.0, 2.0]],
            'asks': [[50050.0, 1.2], [50100.0, 1.8]]
        }
        
        # 1. Analyze order book
        exec_score = order_book.get_execution_score(sample_order_book, 50000, 'buy')
        self.assertIsNotNone(exec_score)
        print(f"✓ Step 1: Order book score = {exec_score:.2f}")
        
        # 2. Add some trade history to Kelly
        for i in range(20):
            kelly.update_trade_outcome(i % 3 != 0, 0.02 if i % 3 != 0 else -0.01)
        
        # 3. Calculate position size
        position_rec = kelly.calculate_optimal_position_size(
            balance=10000, confidence=exec_score
        )
        self.assertGreater(position_rec['position_size'], 0)
        print(f"✓ Step 2: Position size = ${position_rec['position_size']:.2f}")
        
        # 4. Apply attention to sample features
        features = np.random.randn(31) * 10
        weighted_features = attention.apply_attention(features)
        self.assertEqual(len(weighted_features), 31)
        print(f"✓ Step 3: Features weighted with attention")
        
        print("✓ Full pipeline integration test passed!")


def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("Testing 2025 AI Enhancement Modules")
    print("="*60 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedOrderBook))
    suite.addTests(loader.loadTestsFromTestCase(TestBayesianKelly))
    suite.addTests(loader.loadTestsFromTestCase(TestAttentionFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*60 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
