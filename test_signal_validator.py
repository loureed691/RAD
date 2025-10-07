"""
Test suite for signal validator
"""
import unittest
from signal_validator import SignalValidator, TradingOpportunityRanker


class TestSignalValidator(unittest.TestCase):
    """Test signal validation functionality"""
    
    def setUp(self):
        self.validator = SignalValidator()
    
    def test_valid_buy_signal(self):
        """Test validation of valid BUY signal"""
        indicators = {
            'rsi': 35,
            'close': 50000,
            'volume_ratio': 1.5,
            'bb_position': 0.3,
            'momentum': 0.02
        }
        reasons = {}
        
        is_valid, reason = self.validator.validate_signal_quality(
            'BUY', 0.75, indicators, reasons
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(reason, "Signal validated")
    
    def test_rejects_low_confidence(self):
        """Test rejection of low confidence signals"""
        indicators = {
            'rsi': 50,
            'close': 50000,
            'volume_ratio': 1.0
        }
        reasons = {}
        
        is_valid, reason = self.validator.validate_signal_quality(
            'BUY', 0.4, indicators, reasons
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Confidence too low", reason)
    
    def test_rejects_mtf_conflict(self):
        """Test rejection of multi-timeframe conflicts"""
        indicators = {
            'rsi': 50,
            'close': 50000,
            'volume_ratio': 1.0
        }
        reasons = {'mtf_conflict': True}
        
        is_valid, reason = self.validator.validate_signal_quality(
            'BUY', 0.75, indicators, reasons
        )
        
        self.assertFalse(is_valid)
        self.assertIn("conflict", reason.lower())
    
    def test_rejects_low_volume(self):
        """Test rejection of low volume signals"""
        indicators = {
            'rsi': 50,
            'close': 50000,
            'volume_ratio': 0.3
        }
        reasons = {}
        
        is_valid, reason = self.validator.validate_signal_quality(
            'BUY', 0.75, indicators, reasons
        )
        
        self.assertFalse(is_valid)
        self.assertIn("Volume too low", reason)
    
    def test_signal_strength_calculation(self):
        """Test signal strength score calculation"""
        indicators = {
            'rsi': 32,
            'close': 50000,
            'volume_ratio': 2.0,
            'momentum': 0.03
        }
        reasons = {
            'mtf_alignment': 'bullish',
            'trend_strength': 0.8
        }
        
        strength = self.validator.calculate_signal_strength(
            0.8, indicators, reasons
        )
        
        # Should be high due to good conditions
        self.assertGreater(strength, 70)
        self.assertLessEqual(strength, 100)
    
    def test_market_condition_filtering(self):
        """Test market condition filtering"""
        indicators = {
            'close': 50000,
            'sma_20': 51000,
            'sma_50': 49000,
            'confidence': 0.75
        }
        
        # Should reject SELL in uptrend
        should_trade, reason = self.validator.filter_by_market_conditions(
            'SELL', indicators, 'trending'
        )
        
        self.assertFalse(should_trade)
        self.assertIn("uptrend", reason.lower())
    
    def test_adjustments_for_high_volatility(self):
        """Test adjustments for high volatility"""
        indicators = {
            'bb_width': 0.06,  # High volatility
            'volume_ratio': 1.0,
            'momentum': 0.01
        }
        reasons = {}
        
        adjustments = self.validator.suggest_adjustments(
            'BUY', 0.7, indicators, reasons
        )
        
        # Should reduce leverage and widen stop loss
        self.assertLess(adjustments['leverage'], 1.0)
        self.assertGreater(adjustments['stop_loss'], 1.0)


class TestTradingOpportunityRanker(unittest.TestCase):
    """Test opportunity ranking functionality"""
    
    def setUp(self):
        self.ranker = TradingOpportunityRanker()
    
    def test_ranks_by_quality(self):
        """Test opportunities are ranked by quality"""
        opportunities = [
            {
                'symbol': 'BTC/USDT:USDT',
                'score': 50,
                'confidence': 0.6,
                'reasons': {}
            },
            {
                'symbol': 'ETH/USDT:USDT',
                'score': 70,
                'confidence': 0.8,
                'reasons': {'mtf_alignment': 'bullish'}
            },
            {
                'symbol': 'SOL/USDT:USDT',
                'score': 60,
                'confidence': 0.7,
                'reasons': {}
            }
        ]
        
        ranked = self.ranker.rank_opportunities(opportunities)
        
        # ETH should be ranked first (higher score and confidence)
        self.assertEqual(ranked[0]['symbol'], 'ETH/USDT:USDT')
    
    def test_penalizes_duplicate_exposure(self):
        """Test ranking penalizes duplicate exposure"""
        opportunities = [
            {
                'symbol': 'BTC/USDT:USDT',
                'score': 70,
                'confidence': 0.8,
                'reasons': {}
            }
        ]
        current_positions = ['BTC/USDT:USDT']
        
        ranked = self.ranker.rank_opportunities(opportunities, current_positions)
        
        # Score should be reduced due to existing exposure
        self.assertLess(ranked[0]['final_score'], 70 * 0.8)
    
    def test_filters_correlated_opportunities(self):
        """Test filtering of correlated opportunities"""
        opportunities = [
            {'symbol': 'BTC/USDT:USDT', 'score': 70, 'confidence': 0.8, 'reasons': {}},
            {'symbol': 'ETH/USDT:USDT', 'score': 65, 'confidence': 0.75, 'reasons': {}},
            {'symbol': 'SOL/USDT:USDT', 'score': 60, 'confidence': 0.7, 'reasons': {}},
            {'symbol': 'AVAX/USDT:USDT', 'score': 58, 'confidence': 0.7, 'reasons': {}},
            {'symbol': 'NEAR/USDT:USDT', 'score': 55, 'confidence': 0.68, 'reasons': {}}
        ]
        
        # Should limit layer1 positions (SOL, AVAX, NEAR are all layer1)
        filtered = self.ranker.filter_correlated_opportunities(
            opportunities, max_similar=2
        )
        
        # Should have BTC, ETH, and at most 2 layer1
        layer1_count = sum(
            1 for opp in filtered 
            if any(asset in opp['symbol'] for asset in ['SOL', 'AVAX', 'NEAR'])
        )
        self.assertLessEqual(layer1_count, 2)


def run_tests():
    """Run all tests"""
    print("=" * 70)
    print("SIGNAL VALIDATOR TEST SUITE")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSignalValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestTradingOpportunityRanker))
    
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
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
