"""
Test suite for bot enhancements - Phase 1
Tests new risk management, signal generation, and indicator enhancements
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime
from risk_manager import RiskManager
from signals import SignalGenerator
from indicators import Indicators


class TestRiskManagerEnhancements(unittest.TestCase):
    """Test enhanced risk management features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.risk_manager = RiskManager(
            max_position_size=1000.0,
            risk_per_trade=0.02,
            max_open_positions=3
        )
    
    def test_time_of_day_risk_adjustment(self):
        """Test that risk is adjusted based on time of day"""
        base_risk = 0.02
        
        # Test with time-of-day adjustment
        adjusted_risk = self.risk_manager.adjust_risk_for_conditions(
            base_risk=base_risk,
            market_volatility=0.03,
            win_rate=0.5,
            time_of_day_adj=True
        )
        
        # Should return a value between 0.005 and 0.04
        self.assertGreaterEqual(adjusted_risk, 0.005)
        self.assertLessEqual(adjusted_risk, 0.04)
        
        # Test without time-of-day adjustment
        adjusted_risk_no_tod = self.risk_manager.adjust_risk_for_conditions(
            base_risk=base_risk,
            market_volatility=0.03,
            win_rate=0.5,
            time_of_day_adj=False
        )
        
        # Both should be valid but may differ
        self.assertGreaterEqual(adjusted_risk_no_tod, 0.005)
        self.assertLessEqual(adjusted_risk_no_tod, 0.04)
    
    def test_high_volatility_risk_reduction(self):
        """Test that high volatility reduces risk"""
        base_risk = 0.02
        
        # Low volatility
        low_vol_risk = self.risk_manager.adjust_risk_for_conditions(
            base_risk=base_risk,
            market_volatility=0.01,
            win_rate=0.5,
            time_of_day_adj=False
        )
        
        # High volatility
        high_vol_risk = self.risk_manager.adjust_risk_for_conditions(
            base_risk=base_risk,
            market_volatility=0.08,
            win_rate=0.5,
            time_of_day_adj=False
        )
        
        # High volatility should result in lower risk
        self.assertLess(high_vol_risk, low_vol_risk)
    
    def test_slippage_estimation_basic(self):
        """Test basic slippage estimation"""
        # Small position, normal volatility
        slippage = self.risk_manager.estimate_slippage(
            position_value=100.0,
            orderbook=None,
            volatility=0.03,
            volume_24h=1000000.0
        )
        
        # Should be a small positive value
        self.assertGreater(slippage, 0)
        self.assertLess(slippage, 0.02)  # Less than 2%
    
    def test_slippage_estimation_large_position(self):
        """Test that large positions have higher slippage"""
        volume_24h = 100000.0  # $100k daily volume
        
        # Small position (0.1% of daily volume)
        small_slippage = self.risk_manager.estimate_slippage(
            position_value=100.0,
            orderbook=None,
            volatility=0.03,
            volume_24h=volume_24h
        )
        
        # Large position (5% of daily volume)
        large_slippage = self.risk_manager.estimate_slippage(
            position_value=5000.0,
            orderbook=None,
            volatility=0.03,
            volume_24h=volume_24h
        )
        
        # Large position should have more slippage
        self.assertGreater(large_slippage, small_slippage)
    
    def test_slippage_estimation_high_volatility(self):
        """Test that high volatility increases slippage"""
        position_value = 1000.0
        
        # Low volatility
        low_vol_slippage = self.risk_manager.estimate_slippage(
            position_value=position_value,
            orderbook=None,
            volatility=0.02,
            volume_24h=1000000.0
        )
        
        # High volatility
        high_vol_slippage = self.risk_manager.estimate_slippage(
            position_value=position_value,
            orderbook=None,
            volatility=0.08,
            volume_24h=1000000.0
        )
        
        # High volatility should result in higher slippage
        self.assertGreater(high_vol_slippage, low_vol_slippage)


class TestSignalGeneratorEnhancements(unittest.TestCase):
    """Test enhanced signal generation features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.signal_gen = SignalGenerator()
    
    def test_adaptive_confidence_threshold_volatility(self):
        """Test that confidence threshold adjusts for volatility"""
        # Low volatility
        low_vol_threshold = self.signal_gen.get_adaptive_confidence_threshold(
            volatility=0.02,
            volume_ratio=1.0
        )
        
        # High volatility
        high_vol_threshold = self.signal_gen.get_adaptive_confidence_threshold(
            volatility=0.08,
            volume_ratio=1.0
        )
        
        # High volatility should have higher threshold
        self.assertGreater(high_vol_threshold, low_vol_threshold)
        
        # Both should be within valid range
        self.assertGreaterEqual(low_vol_threshold, 0.50)
        self.assertLessEqual(high_vol_threshold, 0.75)
    
    def test_adaptive_confidence_threshold_volume(self):
        """Test that confidence threshold adjusts for volume"""
        # Normal volume
        normal_vol_threshold = self.signal_gen.get_adaptive_confidence_threshold(
            volatility=0.03,
            volume_ratio=1.0
        )
        
        # Low volume
        low_volume_threshold = self.signal_gen.get_adaptive_confidence_threshold(
            volatility=0.03,
            volume_ratio=0.5
        )
        
        # Low volume should have higher threshold (more selective)
        self.assertGreater(low_volume_threshold, normal_vol_threshold)
    
    def test_signal_outcome_tracking(self):
        """Test signal outcome recording"""
        # Record profitable trades
        self.signal_gen.record_signal_outcome(profitable=True, pnl=0.05)
        self.signal_gen.record_signal_outcome(profitable=True, pnl=0.03)
        self.signal_gen.record_signal_outcome(profitable=False, pnl=-0.02)
        
        # Should have 3 recent signals
        self.assertEqual(len(self.signal_gen.recent_signals), 3)
        
        # Win rate should be ~66%
        win_count = sum(1 for s in self.signal_gen.recent_signals if s['profitable'])
        self.assertEqual(win_count, 2)
    
    def test_signal_outcome_window_limit(self):
        """Test that signal tracking respects window limit"""
        # Add more than max signals
        for i in range(25):
            self.signal_gen.record_signal_outcome(profitable=(i % 2 == 0), pnl=0.01)
        
        # Should only keep last 20
        self.assertEqual(len(self.signal_gen.recent_signals), 
                        self.signal_gen.max_recent_signals)


class TestIndicatorEnhancements(unittest.TestCase):
    """Test enhanced indicator calculations"""
    
    def setUp(self):
        """Set up test data"""
        # Create sample OHLCV data
        np.random.seed(42)
        n_candles = 100
        
        base_price = 50000
        data = []
        for i in range(n_candles):
            price_change = np.random.randn() * 100
            close = base_price + price_change
            high = close + abs(np.random.randn() * 50)
            low = close - abs(np.random.randn() * 50)
            open_price = close + np.random.randn() * 20
            volume = abs(np.random.randn() * 1000000)
            
            data.append([
                int(time.time() * 1000) + i * 3600000,  # timestamp
                open_price, high, low, close, volume
            ])
        
        self.df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Calculate indicators
        self.df = Indicators.calculate_all(self.df)
    
    def test_momentum_strength_calculation(self):
        """Test momentum strength calculation"""
        momentum = Indicators.calculate_momentum_strength(self.df, lookback=14)
        
        # Should return dict with required keys
        self.assertIn('strength', momentum)
        self.assertIn('direction', momentum)
        self.assertIn('acceleration', momentum)
        
        # Strength should be non-negative
        self.assertGreaterEqual(momentum['strength'], 0)
        
        # Direction should be one of the expected values
        self.assertIn(momentum['direction'], ['bullish', 'bearish', 'neutral'])
    
    def test_momentum_strength_with_trend(self):
        """Test momentum detection with trending data"""
        # Create strongly trending data
        trending_data = []
        base_price = 50000
        for i in range(100):
            close = base_price + i * 100  # Strong uptrend
            high = close + 50
            low = close - 30
            open_price = close - 20
            volume = 1000000
            
            trending_data.append([
                int(time.time() * 1000) + i * 3600000,
                open_price, high, low, close, volume
            ])
        
        df_trend = pd.DataFrame(trending_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_trend = Indicators.calculate_all(df_trend)
        
        momentum = Indicators.calculate_momentum_strength(df_trend, lookback=14)
        
        # Should detect bullish direction or at least not bearish with strong uptrend
        self.assertIn(momentum['direction'], ['bullish', 'neutral'])
        
        # Should have measurable strength (not zero)
        self.assertGreater(momentum['strength'], 0.0)
    
    def test_momentum_strength_insufficient_data(self):
        """Test momentum calculation with insufficient data"""
        # Create very small dataset
        small_data = self.df.head(5)
        
        momentum = Indicators.calculate_momentum_strength(small_data, lookback=14)
        
        # Should return default values
        self.assertEqual(momentum['strength'], 0.0)
        self.assertEqual(momentum['direction'], 'neutral')


def run_tests():
    """Run all tests and return results"""
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    import time
    print("=" * 70)
    print("ENHANCEMENT TESTS - PHASE 1")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    success = run_tests()
    
    print("=" * 70)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 70)
    
    exit(0 if success else 1)
