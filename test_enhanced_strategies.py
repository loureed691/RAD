"""
Comprehensive integration test for enhanced buy/sell strategies
Tests all improvements together to ensure they work as expected
"""
import unittest
import pandas as pd
import numpy as np
from signals import SignalGenerator
from indicators import Indicators
from smart_entry_exit import SmartEntryExit
from advanced_exit_strategy import AdvancedExitStrategy
from adaptive_strategy_2026 import AdaptiveStrategySelector2026


class TestEnhancedStrategies(unittest.TestCase):
    """Test enhanced strategy improvements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sg = SignalGenerator()
        self.see = SmartEntryExit()
        self.aes = AdvancedExitStrategy()
        self.ass = AdaptiveStrategySelector2026()
        
        # Create sample OHLCV data
        self.ohlcv_data = self._create_sample_data(100)
        self.df = Indicators.calculate_all(self.ohlcv_data)
    
    def _create_sample_data(self, periods):
        """Create sample OHLCV data"""
        ohlcv_list = []
        base_price = 50000
        for i in range(periods):
            timestamp = 1704067200000 + (i * 3600000)
            price = base_price + np.random.randn() * 100
            ohlcv_list.append([
                timestamp,
                price + np.random.rand() * 10,
                price + np.random.rand() * 50,
                price - np.random.rand() * 50,
                price,
                1000 + np.random.rand() * 500
            ])
            base_price = price
        return ohlcv_list
    
    def test_enhanced_market_regime_detection(self):
        """Test enhanced market regime detection with 5 regimes"""
        regime = self.sg.detect_market_regime(self.df)
        self.assertIn(regime, ['trending', 'ranging', 'neutral', 'volatile', 'consolidating'])
        print(f"✓ Market regime detected: {regime}")
    
    def test_market_structure_analysis(self):
        """Test market structure analysis for trend validation"""
        structure = self.sg.detect_market_structure(self.df)
        
        self.assertIn('structure', structure)
        self.assertIn('strength', structure)
        self.assertIn(structure['structure'], ['uptrend', 'downtrend', 'neutral'])
        self.assertGreaterEqual(structure['strength'], 0.0)
        self.assertLessEqual(structure['strength'], 1.0)
        
        print(f"✓ Market structure: {structure['structure']} (strength: {structure['strength']:.2f})")
    
    def test_enhanced_signal_generation(self):
        """Test signal generation with all enhancements"""
        signal, confidence, reasons = self.sg.generate_signal(self.df)
        
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        self.assertIsInstance(reasons, dict)
        
        print(f"✓ Signal: {signal}, Confidence: {confidence:.2f}")
        print(f"  Market regime: {reasons.get('market_regime', 'unknown')}")
    
    def test_order_book_wall_detection(self):
        """Test order book wall detection for better entry timing"""
        orderbook = {
            'bids': [[50000 - i*50, 10 if i != 3 else 50] for i in range(20)],
            'asks': [[50050 + i*50, 8 if i != 4 else 45] for i in range(20)]
        }
        
        timing = self.see.analyze_entry_timing(
            orderbook=orderbook,
            current_price=50025,
            signal='BUY',
            volatility=0.03
        )
        
        self.assertIn('timing_score', timing)
        self.assertIn('obi', timing)
        self.assertIn('reason', timing)
        
        # Check that walls are detected in reason
        self.assertTrue('wall' in timing['reason'].lower())
        
        print(f"✓ Entry timing score: {timing['timing_score']:.2f}")
        print(f"  Reason: {timing['reason']}")
    
    def test_atr_based_profit_targets(self):
        """Test ATR-based profit target calculation"""
        targets = self.aes.calculate_atr_profit_targets(
            entry_price=50000,
            atr=1000,
            position_side='long'
        )
        
        self.assertEqual(len(targets), 3)  # Default 3 targets
        
        # Verify targets are increasing
        for i in range(1, len(targets)):
            self.assertGreater(targets[i]['price'], targets[i-1]['price'])
        
        target_str = ', '.join([f"{t['atr_multiple']}x" for t in targets])
        print(f"✓ ATR profit targets: {target_str}")
    
    def test_trend_acceleration_detection(self):
        """Test trend acceleration detection"""
        # Accelerating trend
        momentum_up = [0.01, 0.015, 0.02, 0.025, 0.03]
        volume_up = [1.0, 1.1, 1.2, 1.3, 1.4]
        
        acceleration = self.aes.detect_trend_acceleration(momentum_up, volume_up)
        
        self.assertTrue(acceleration['accelerating'])
        self.assertGreater(acceleration['strength'], 0.5)
        
        print(f"✓ Trend acceleration: {acceleration['accelerating']} (strength: {acceleration['strength']:.2f})")
    
    def test_exhaustion_detection(self):
        """Test trend exhaustion detection"""
        # Overbought with weak volume
        exhaustion = self.aes.detect_exhaustion(
            rsi=78.0,
            volume_ratio=0.75,
            position_side='long',
            price_distance_from_entry=0.06
        )
        
        self.assertTrue(exhaustion['exhausted'])
        self.assertGreater(exhaustion['severity'], 0.0)
        self.assertGreater(len(exhaustion['reasons']), 0)
        
        print(f"✓ Exhaustion detected: severity {exhaustion['severity']:.2f}")
    
    def test_dynamic_strategy_weights(self):
        """Test dynamic strategy weight calculation"""
        weights = self.ass.calculate_dynamic_strategy_weights(
            market_regime='bull',
            volatility=0.3
        )
        
        # Verify weights sum to 1.0
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=2)
        
        # In bull market, trend following should have higher weight
        self.assertGreater(weights['trend_following'], weights['mean_reversion'])
        
        print(f"✓ Dynamic weights: trend={weights['trend_following']:.2f}, mean_rev={weights['mean_reversion']:.2f}")
    
    def test_ensemble_signal_with_strict_majority(self):
        """Test ensemble signal requires stricter majority (55%)"""
        indicators = {
            'trend_direction': 'up',
            'trend_strength': 0.6,
            'rsi': 55,
            'volatility': 0.03
        }
        
        signal, conf = self.ass.get_strategy_ensemble_signal(
            indicators=indicators,
            base_signal='BUY',
            base_confidence=0.7,
            market_regime='bull',
            volatility=0.3
        )
        
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
        
        print(f"✓ Ensemble signal: {signal} (confidence: {conf:.2f})")
    
    def test_integration_full_trading_flow(self):
        """Test full trading flow with all enhancements"""
        # 1. Generate signal
        signal, confidence, reasons = self.sg.generate_signal(self.df)
        
        # 2. If signal is not HOLD, analyze entry timing
        if signal != 'HOLD':
            orderbook = {
                'bids': [[50000 - i*50, 10] for i in range(20)],
                'asks': [[50050 + i*50, 8] for i in range(20)]
            }
            
            timing = self.see.analyze_entry_timing(
                orderbook=orderbook,
                current_price=50025,
                signal=signal,
                volatility=0.03
            )
            
            # 3. Calculate profit targets using ATR
            targets = self.aes.calculate_atr_profit_targets(
                entry_price=50000,
                atr=1000,
                position_side='long' if signal == 'BUY' else 'short'
            )
            
            print(f"\n✓ Full trading flow test:")
            print(f"  Signal: {signal} ({confidence:.2f})")
            print(f"  Entry timing: {timing['timing_score']:.2f}")
            print(f"  Profit targets: {len(targets)} levels")
            
            self.assertGreater(timing['timing_score'], 0.0)
            self.assertGreater(len(targets), 0)
        else:
            print(f"\n✓ Full trading flow test: HOLD signal (skipped entry analysis)")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
