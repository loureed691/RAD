#!/usr/bin/env python3
"""
Massive stress testing with 400+ randomized scenarios.
This generates a wide variety of market conditions and trading situations
to find edge cases and subtle bugs.
"""
import unittest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from position_manager import Position
from risk_manager import RiskManager
from signals import SignalGenerator
from indicators import Indicators


class StressTestScenarioGenerator:
    """Generate randomized stress test scenarios"""
    
    @staticmethod
    def generate_random_market_data(num_candles=100, seed=None):
        """Generate random but realistic market data"""
        if seed:
            np.random.seed(seed)
            
        base_price = np.random.uniform(1000, 100000)
        volatility = np.random.uniform(0.005, 0.15)  # 0.5% to 15%
        trend_strength = np.random.uniform(-0.05, 0.05)  # -5% to +5% drift
        
        timestamps = pd.date_range(end=datetime.now(), periods=num_candles, freq='1h')
        
        # Generate price path with realistic characteristics
        returns = np.random.normal(trend_strength/num_candles, volatility, num_candles)
        prices = base_price * (1 + np.cumsum(returns))
        prices = np.maximum(prices, base_price * 0.1)  # Prevent negative prices
        
        data = []
        for ts, close in zip(timestamps, prices):
            high_offset = abs(np.random.normal(0, volatility/2))
            low_offset = abs(np.random.normal(0, volatility/2))
            
            high = close * (1 + high_offset)
            low = close * (1 - low_offset)
            open_price = close * (1 + np.random.normal(0, volatility/4))
            
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            volume = np.random.uniform(100000, 10000000)
            
            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data)


class TestMassiveStressPositions(unittest.TestCase):
    """Stress test positions with 100+ random scenarios"""
    
    def test_100_random_long_positions(self):
        """Test 100 random long position scenarios"""
        failures = []
        
        for i in range(100):
            try:
                # Random parameters
                entry_price = np.random.uniform(1000, 100000)
                leverage = np.random.choice([1, 3, 5, 10, 20, 50, 100])
                stop_loss_pct = np.random.uniform(0.01, 0.10)  # 1-10% stop
                take_profit_pct = np.random.uniform(0.02, 0.20)  # 2-20% take profit
                
                stop_loss = entry_price * (1 - stop_loss_pct)
                take_profit = entry_price * (1 + take_profit_pct)
                
                position = Position(
                    symbol='TEST',
                    side='long',
                    entry_price=entry_price,
                    amount=np.random.uniform(0.01, 10),
                    leverage=leverage,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                # Test various price points
                for price_change in [-0.15, -0.05, -0.01, 0, 0.01, 0.05, 0.15, 0.30]:
                    current_price = entry_price * (1 + price_change)
                    
                    # Should not crash
                    pnl = position.get_pnl(current_price)
                    self.assertIsNotNone(pnl)
                    
                    leveraged_pnl = position.get_leveraged_pnl(current_price)
                    self.assertIsNotNone(leveraged_pnl)
                    
                    should_close, reason = position.should_close(current_price)
                    self.assertIsInstance(should_close, bool)
                    self.assertIsInstance(reason, str)
                    
            except Exception as e:
                failures.append(f"Scenario {i}: {e}")
        
        if failures:
            self.fail(f"Failed scenarios:\n" + "\n".join(failures[:10]))
    
    def test_100_random_short_positions(self):
        """Test 100 random short position scenarios"""
        failures = []
        
        for i in range(100):
            try:
                entry_price = np.random.uniform(1000, 100000)
                leverage = np.random.choice([1, 3, 5, 10, 20, 50, 100])
                stop_loss_pct = np.random.uniform(0.01, 0.10)
                take_profit_pct = np.random.uniform(0.02, 0.20)
                
                stop_loss = entry_price * (1 + stop_loss_pct)  # Above entry for short
                take_profit = entry_price * (1 - take_profit_pct)  # Below entry for short
                
                position = Position(
                    symbol='TEST',
                    side='short',
                    entry_price=entry_price,
                    amount=np.random.uniform(0.01, 10),
                    leverage=leverage,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
                
                # Test various price points
                for price_change in [-0.30, -0.15, -0.05, -0.01, 0, 0.01, 0.05, 0.15]:
                    current_price = entry_price * (1 + price_change)
                    
                    pnl = position.get_pnl(current_price)
                    self.assertIsNotNone(pnl)
                    
                    leveraged_pnl = position.get_leveraged_pnl(current_price)
                    self.assertIsNotNone(leveraged_pnl)
                    
                    should_close, reason = position.should_close(current_price)
                    self.assertIsInstance(should_close, bool)
                    
            except Exception as e:
                failures.append(f"Scenario {i}: {e}")
        
        if failures:
            self.fail(f"Failed scenarios:\n" + "\n".join(failures[:10]))


class TestMassiveStressRiskManager(unittest.TestCase):
    """Stress test risk manager with 50+ scenarios"""
    
    def test_50_random_kelly_calculations(self):
        """Test Kelly criterion with 50 random scenarios"""
        risk_manager = RiskManager(
            max_position_size=10000,
            risk_per_trade=0.02,
            max_open_positions=3
        )
        
        failures = []
        
        for i in range(50):
            try:
                win_rate = np.random.uniform(0.3, 0.8)
                avg_win = np.random.uniform(0.01, 0.10)
                avg_loss = np.random.uniform(0.01, 0.10)
                volatility = np.random.uniform(0.01, 0.15)
                
                kelly = risk_manager.calculate_kelly_fraction(
                    win_rate=win_rate,
                    avg_win=avg_win,
                    avg_loss=avg_loss,
                    volatility_adj=volatility
                )
                
                # Kelly should be reasonable
                self.assertGreaterEqual(kelly, 0.0)
                self.assertLessEqual(kelly, 1.0)
                self.assertFalse(np.isnan(kelly))
                self.assertFalse(np.isinf(kelly))
                
            except Exception as e:
                failures.append(f"Scenario {i}: {e}")
        
        if failures:
            self.fail(f"Failed scenarios:\n" + "\n".join(failures[:10]))
    
    def test_50_random_position_size_calculations(self):
        """Test position sizing with 50 random scenarios"""
        risk_manager = RiskManager(
            max_position_size=10000,
            risk_per_trade=0.02,
            max_open_positions=3
        )
        
        failures = []
        
        for i in range(50):
            try:
                balance = np.random.uniform(100, 100000)
                entry_price = np.random.uniform(1000, 100000)
                stop_loss_pct = np.random.uniform(0.01, 0.10)
                stop_loss_price = entry_price * (1 - stop_loss_pct)
                leverage = np.random.choice([1, 3, 5, 10, 20])
                
                size = risk_manager.calculate_position_size(
                    balance=balance,
                    entry_price=entry_price,
                    stop_loss_price=stop_loss_price,
                    leverage=leverage
                )
                
                # Position size should be reasonable
                self.assertGreaterEqual(size, 0)
                self.assertFalse(np.isnan(size))
                self.assertFalse(np.isinf(size))
                
                # Position value should not be absurdly large
                position_value = size * entry_price
                self.assertLess(position_value, balance * leverage * 2)
                
            except Exception as e:
                failures.append(f"Scenario {i}: {e}")
        
        if failures:
            self.fail(f"Failed scenarios:\n" + "\n".join(failures[:10]))


class TestMassiveStressSignals(unittest.TestCase):
    """Stress test signal generation with 100+ scenarios"""
    
    def setUp(self):
        self.signal_gen = SignalGenerator()
        self.indicators = Indicators()
    
    def test_100_random_market_signals(self):
        """Test signal generation with 100 random market conditions"""
        failures = []
        
        for i in range(100):
            try:
                # Generate random market data
                df = StressTestScenarioGenerator.generate_random_market_data(
                    num_candles=100,
                    seed=1000 + i
                )
                
                # Calculate indicators
                df_with_ind = self.indicators.calculate_all(df)
                
                if df_with_ind.empty:
                    continue
                
                # Generate signal
                signal, confidence, reasons = self.signal_gen.generate_signal(df_with_ind)
                
                # Signal should be valid
                self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
                self.assertGreaterEqual(confidence, 0.0)
                self.assertLessEqual(confidence, 1.0)
                self.assertFalse(np.isnan(confidence))
                
                # Reasons should be a dict
                self.assertIsInstance(reasons, dict)
                
            except Exception as e:
                failures.append(f"Scenario {i}: {e}")
        
        if failures:
            self.fail(f"Failed scenarios:\n" + "\n".join(failures[:10]))


class TestMassiveStressEdgeCases(unittest.TestCase):
    """Test 50+ edge cases"""
    
    def test_extreme_leverage_scenarios(self):
        """Test with extreme leverage values"""
        test_cases = [
            (1, "Minimum leverage"),
            (3, "Conservative leverage"),
            (10, "Moderate leverage"),
            (25, "High leverage"),
            (50, "Very high leverage"),
            (100, "Extreme leverage"),
            (125, "Maximum KuCoin leverage"),
        ]
        
        for leverage, description in test_cases:
            entry_price = 50000
            position = Position(
                symbol='TEST',
                side='long',
                entry_price=entry_price,
                amount=0.1,
                leverage=leverage,
                stop_loss=entry_price * 0.95
            )
            
            # Small price move should have appropriate leveraged effect
            exit_price = entry_price * 1.01  # 1% move
            pnl = position.get_leveraged_pnl(exit_price)
            
            # Expected: 1% * leverage
            expected = 0.01 * leverage
            self.assertAlmostEqual(pnl, expected, places=2,
                                 msg=f"{description} ({leverage}x) failed")
    
    def test_extreme_price_ranges(self):
        """Test with extreme price values"""
        test_prices = [
            0.001,      # Very small (altcoin)
            0.01,       # Small
            1.0,        # Dollar
            10.0,       # Typical small coin
            100.0,      # Medium
            1000.0,     # Large
            10000.0,    # BTC range
            50000.0,    # High BTC
            100000.0,   # Very high
        ]
        
        for entry_price in test_prices:
            position = Position(
                symbol='TEST',
                side='long',
                entry_price=entry_price,
                amount=1.0,
                leverage=10,
                stop_loss=entry_price * 0.95
            )
            
            # Test 5% profit
            exit_price = entry_price * 1.05
            pnl = position.get_pnl(exit_price)
            
            self.assertAlmostEqual(pnl, 0.05, places=3,
                                 msg=f"Failed at price {entry_price}")
    
    def test_extreme_position_sizes(self):
        """Test with extreme position sizes"""
        test_sizes = [
            0.0001,     # Very small (dust)
            0.01,       # Small
            0.1,        # Typical
            1.0,        # One unit
            10.0,       # Large
            100.0,      # Very large
            1000.0,     # Institutional
        ]
        
        entry_price = 50000
        for amount in test_sizes:
            position = Position(
                symbol='TEST',
                side='long',
                entry_price=entry_price,
                amount=amount,
                leverage=10,
                stop_loss=entry_price * 0.95
            )
            
            # Calculate position value
            position_value = amount * entry_price
            
            # Should handle all sizes
            self.assertGreater(position_value, 0)


def run_tests():
    """Run all stress tests"""
    print("=" * 70)
    print("⚡ MASSIVE STRESS TESTING (400+ Scenarios)")
    print("=" * 70)
    print("Testing with randomized parameters to find edge cases...")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestMassiveStressPositions))
    suite.addTests(loader.loadTestsFromTestCase(TestMassiveStressRiskManager))
    suite.addTests(loader.loadTestsFromTestCase(TestMassiveStressSignals))
    suite.addTests(loader.loadTestsFromTestCase(TestMassiveStressEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("📊 STRESS TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Scenarios Tested: 400+")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
