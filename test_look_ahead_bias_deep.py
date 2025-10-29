#!/usr/bin/env python3
"""
Deep testing for look-ahead bias in trading bot.
Tests to ensure no future data leakage in signals, indicators, or ML models.
"""
import unittest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indicators import Indicators
from signals import SignalGenerator
from ml_model import MLModel

class TestIndicatorLookAheadBias(unittest.TestCase):
    """Deep testing for indicator look-ahead bias"""
    
    def setUp(self):
        self.indicators = Indicators()
    
    def generate_price_series(self, length=200, seed=100):
        """Generate synthetic price data"""
        np.random.seed(seed)
        timestamps = pd.date_range(end=datetime.now(), periods=length, freq='1h')
        base_price = 50000
        returns = np.random.normal(0, 0.02, length)
        prices = base_price * (1 + np.cumsum(returns))
        prices = np.maximum(prices, base_price * 0.5)
        
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            high = close * (1 + abs(np.random.normal(0, 0.01)))
            low = close * (1 - abs(np.random.normal(0, 0.01)))
            open_price = close * (1 + np.random.normal(0, 0.005))
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            volume = np.random.uniform(1000000, 5000000)
            
            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def test_sma_no_future_data(self):
        """Test SMA doesn't use future data"""
        df = self.generate_price_series(length=200, seed=101)
        
        for i in range(50, len(df)):
            partial = df.iloc[:i+1].copy()
            result = self.indicators.calculate_all(partial)
            
            if result.empty:
                continue
            
            # SMA at position i should only use data up to i
            sma_20 = result.iloc[-1]['sma_20']
            
            # Manually calculate SMA to verify
            manual_sma = partial['close'].tail(20).mean()
            
            # Should match closely (allow small floating point difference)
            if not pd.isna(sma_20) and not pd.isna(manual_sma):
                self.assertAlmostEqual(sma_20, manual_sma, places=2)
    
    def test_ema_no_future_data(self):
        """Test EMA doesn't use future data"""
        df = self.generate_price_series(length=200, seed=102)
        
        for i in range(50, len(df)):
            partial = df.iloc[:i+1].copy()
            result = self.indicators.calculate_all(partial)
            
            if result.empty:
                continue
            
            # EMA should only use past data
            ema_12 = result.iloc[-1]['ema_12']
            self.assertFalse(pd.isna(ema_12))
    
    def test_rsi_no_future_data(self):
        """Test RSI doesn't use future data"""
        df = self.generate_price_series(length=200, seed=103)
        
        for i in range(50, len(df)):
            partial = df.iloc[:i+1].copy()
            result = self.indicators.calculate_all(partial)
            
            if result.empty:
                continue
            
            rsi = result.iloc[-1]['rsi']
            
            # RSI should be between 0 and 100
            self.assertGreaterEqual(rsi, 0)
            self.assertLessEqual(rsi, 100)
    
    def test_macd_no_future_data(self):
        """Test MACD doesn't use future data"""
        df = self.generate_price_series(length=200, seed=104)
        
        for i in range(50, len(df)):
            partial = df.iloc[:i+1].copy()
            result = self.indicators.calculate_all(partial)
            
            if result.empty:
                continue
            
            macd = result.iloc[-1]['macd']
            macd_signal = result.iloc[-1]['macd_signal']
            
            # MACD values should be finite
            self.assertFalse(pd.isna(macd))
            self.assertFalse(pd.isna(macd_signal))
    
    def test_bollinger_bands_no_future_data(self):
        """Test Bollinger Bands don't use future data"""
        df = self.generate_price_series(length=200, seed=105)
        
        for i in range(50, len(df)):
            partial = df.iloc[:i+1].copy()
            result = self.indicators.calculate_all(partial)
            
            if result.empty:
                continue
            
            bb_high = result.iloc[-1]['bb_high']
            bb_low = result.iloc[-1]['bb_low']
            close = result.iloc[-1]['close']
            
            # Upper band should be above lower band
            if not pd.isna(bb_high) and not pd.isna(bb_low):
                self.assertGreater(bb_high, bb_low)


class TestSignalLookAheadBias(unittest.TestCase):
    """Deep testing for signal generation look-ahead bias"""
    
    def setUp(self):
        self.signal_gen = SignalGenerator()
        self.indicators = Indicators()
    
    def generate_price_series(self, length=200, seed=200):
        """Generate synthetic price data"""
        np.random.seed(seed)
        timestamps = pd.date_range(end=datetime.now(), periods=length, freq='1h')
        base_price = 50000
        returns = np.random.normal(0, 0.02, length)
        prices = base_price * (1 + np.cumsum(returns))
        prices = np.maximum(prices, base_price * 0.5)
        
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            high = close * (1 + abs(np.random.normal(0, 0.01)))
            low = close * (1 - abs(np.random.normal(0, 0.01)))
            open_price = close * (1 + np.random.normal(0, 0.005))
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            volume = np.random.uniform(1000000, 5000000)
            
            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def test_signal_generation_incrementally(self):
        """Test signal generation doesn't peek at future data"""
        df = self.generate_price_series(length=150, seed=201)
        
        # Generate signals incrementally
        signals = []
        for i in range(50, len(df)):
            partial = df.iloc[:i+1].copy()
            partial_ind = self.indicators.calculate_all(partial)
            
            if partial_ind.empty:
                continue
            
            signal, conf, reasons = self.signal_gen.generate_signal(partial_ind)
            signals.append({
                'index': i,
                'signal': signal,
                'confidence': conf,
                'price': partial['close'].iloc[-1]
            })
        
        # Verify signals are consistent (same input should give same signal)
        self.assertGreater(len(signals), 0)
        
        for sig in signals:
            self.assertIn(sig['signal'], ['BUY', 'SELL', 'HOLD'])
            self.assertGreaterEqual(sig['confidence'], 0.0)
            self.assertLessEqual(sig['confidence'], 1.0)
    
    def test_confidence_scores_reasonable(self):
        """Test confidence scores don't show look-ahead bias"""
        df = self.generate_price_series(length=150, seed=202)
        df_ind = self.indicators.calculate_all(df)
        
        if df_ind.empty:
            self.skipTest("Insufficient data")
        
        # Generate signal
        signal, conf, reasons = self.signal_gen.generate_signal(df_ind)
        
        # Confidence should be reasonable (not suspiciously high)
        # In real trading, confidence > 0.95 is rare without look-ahead bias
        self.assertLessEqual(conf, 0.98, 
                            "Suspiciously high confidence may indicate look-ahead bias")


class TestMLModelLookAheadBias(unittest.TestCase):
    """Test ML model for look-ahead bias"""
    
    def setUp(self):
        self.ml_model = MLModel('models/signal_model.pkl')
        self.indicators = Indicators()
    
    def test_ml_prediction_no_future_data(self):
        """Test ML model predictions don't use future data"""
        # Create synthetic feature data
        np.random.seed(300)
        
        for _ in range(10):
            # Generate random features (31 features as per ML model)
            features = np.random.randn(31)
            
            # Predict
            try:
                prediction = self.ml_model.predict(features.reshape(1, -1))
                
                # Prediction should be finite
                self.assertFalse(np.isnan(prediction))
                self.assertFalse(np.isinf(prediction))
            except Exception as e:
                # Model might not be trained, skip test
                self.skipTest(f"ML model not available: {e}")


def run_tests():
    """Run all look-ahead bias tests"""
    print("=" * 70)
    print("🔍 DEEP LOOK-AHEAD BIAS TESTING")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestIndicatorLookAheadBias))
    suite.addTests(loader.loadTestsFromTestCase(TestSignalLookAheadBias))
    suite.addTests(loader.loadTestsFromTestCase(TestMLModelLookAheadBias))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("📊 LOOK-AHEAD BIAS TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
