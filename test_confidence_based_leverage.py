#!/usr/bin/env python3
"""
Test confidence-based leverage calculation (2-25x range)
This test verifies that leverage is determined primarily by position confidence
"""
import os
import sys
import unittest

# Ensure we're testing the local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set required environment variables
os.environ['KUCOIN_API_KEY'] = 'test_key'
os.environ['KUCOIN_API_SECRET'] = 'test_secret'
os.environ['KUCOIN_API_PASSPHRASE'] = 'test_passphrase'


class TestConfidenceBasedLeverage(unittest.TestCase):
    """Test that leverage is based on confidence (2-25x)"""
    
    def setUp(self):
        """Set up test environment"""
        from risk_manager import RiskManager
        self.risk_manager = RiskManager(
            max_position_size=1000,
            risk_per_trade=0.02,
            max_open_positions=3
        )
    
    def test_minimum_leverage_low_confidence(self):
        """Test that very low confidence results in minimum 2x leverage"""
        # Very low confidence (< 0.40)
        leverage = self.risk_manager.get_max_leverage(
            volatility=0.02,  # Normal volatility
            confidence=0.30   # Very low confidence
        )
        self.assertEqual(leverage, 2, "Very low confidence should result in 2x leverage")
    
    def test_low_confidence_range(self):
        """Test leverage in low confidence range (2-6x)"""
        # Test various points in low confidence range
        test_cases = [
            (0.40, 2, 6),   # At lower bound
            (0.45, 2, 6),   # Middle
            (0.49, 2, 6),   # Near upper bound
        ]
        
        for confidence, min_lev, max_lev in test_cases:
            leverage = self.risk_manager.get_max_leverage(
                volatility=0.02,
                confidence=confidence
            )
            self.assertGreaterEqual(leverage, min_lev, 
                f"Confidence {confidence:.2f} should result in leverage >= {min_lev}x")
            self.assertLessEqual(leverage, max_lev,
                f"Confidence {confidence:.2f} should result in leverage <= {max_lev}x")
    
    def test_moderate_confidence_range(self):
        """Test leverage in moderate confidence range (6-12x)"""
        test_cases = [
            (0.50, 6, 12),   # At lower bound
            (0.57, 6, 12),   # Middle
            (0.64, 6, 12),   # Near upper bound
        ]
        
        for confidence, min_lev, max_lev in test_cases:
            leverage = self.risk_manager.get_max_leverage(
                volatility=0.02,
                confidence=confidence
            )
            self.assertGreaterEqual(leverage, min_lev,
                f"Confidence {confidence:.2f} should result in leverage >= {min_lev}x")
            self.assertLessEqual(leverage, max_lev,
                f"Confidence {confidence:.2f} should result in leverage <= {max_lev}x")
    
    def test_good_confidence_range(self):
        """Test leverage in good confidence range (12-17x)"""
        test_cases = [
            (0.65, 12, 17),  # At lower bound
            (0.70, 12, 17),  # Middle
            (0.74, 12, 17),  # Near upper bound
        ]
        
        for confidence, min_lev, max_lev in test_cases:
            leverage = self.risk_manager.get_max_leverage(
                volatility=0.02,
                confidence=confidence
            )
            self.assertGreaterEqual(leverage, min_lev,
                f"Confidence {confidence:.2f} should result in leverage >= {min_lev}x")
            self.assertLessEqual(leverage, max_lev,
                f"Confidence {confidence:.2f} should result in leverage <= {max_lev}x")
    
    def test_high_confidence_range(self):
        """Test leverage in high confidence range (17-21x)"""
        test_cases = [
            (0.75, 17, 21),  # At lower bound
            (0.80, 17, 21),  # Middle
            (0.84, 17, 21),  # Near upper bound
        ]
        
        for confidence, min_lev, max_lev in test_cases:
            leverage = self.risk_manager.get_max_leverage(
                volatility=0.02,
                confidence=confidence
            )
            self.assertGreaterEqual(leverage, min_lev,
                f"Confidence {confidence:.2f} should result in leverage >= {min_lev}x")
            self.assertLessEqual(leverage, max_lev,
                f"Confidence {confidence:.2f} should result in leverage <= {max_lev}x")
    
    def test_very_high_confidence_range(self):
        """Test leverage in very high confidence range (21-25x)"""
        test_cases = [
            (0.85, 21, 25),  # At lower bound
            (0.90, 21, 25),  # Middle
            (0.94, 21, 25),  # Near upper bound
        ]
        
        for confidence, min_lev, max_lev in test_cases:
            leverage = self.risk_manager.get_max_leverage(
                volatility=0.02,
                confidence=confidence
            )
            self.assertGreaterEqual(leverage, min_lev,
                f"Confidence {confidence:.2f} should result in leverage >= {min_lev}x")
            self.assertLessEqual(leverage, max_lev,
                f"Confidence {confidence:.2f} should result in leverage <= {max_lev}x")
    
    def test_maximum_leverage_exceptional_confidence(self):
        """Test that exceptional confidence (>= 0.95) results in maximum 25x leverage"""
        leverage = self.risk_manager.get_max_leverage(
            volatility=0.02,
            confidence=0.95
        )
        self.assertEqual(leverage, 25, "Exceptional confidence (>= 0.95) should result in 25x leverage")
        
        # Test even higher confidence
        leverage = self.risk_manager.get_max_leverage(
            volatility=0.02,
            confidence=0.99
        )
        self.assertEqual(leverage, 25, "Confidence 0.99 should result in 25x leverage")
    
    def test_volatility_safety_cap(self):
        """Test that high volatility caps leverage regardless of confidence"""
        # High confidence but extreme volatility
        leverage = self.risk_manager.get_max_leverage(
            volatility=0.12,  # Extreme volatility
            confidence=0.90   # Very high confidence
        )
        self.assertLessEqual(leverage, 5, "Extreme volatility should cap leverage at 5x")
        
        # High confidence but very high volatility
        leverage = self.risk_manager.get_max_leverage(
            volatility=0.09,  # Very high volatility
            confidence=0.90   # Very high confidence
        )
        self.assertLessEqual(leverage, 8, "Very high volatility should cap leverage at 8x")
        
        # High confidence but high volatility
        leverage = self.risk_manager.get_max_leverage(
            volatility=0.06,  # High volatility
            confidence=0.90   # Very high confidence
        )
        self.assertLessEqual(leverage, 12, "High volatility should cap leverage at 12x")
    
    def test_drawdown_reduces_leverage(self):
        """Test that drawdown reduces leverage as a safety feature"""
        # Set a drawdown
        self.risk_manager.current_drawdown = 0.12  # 12% drawdown
        
        leverage = self.risk_manager.get_max_leverage(
            volatility=0.02,
            confidence=0.80  # High confidence
        )
        
        # With 12% drawdown, leverage should be reduced by 5x
        # High confidence (0.80) would normally give ~19x, but with drawdown it should be reduced
        self.assertLessEqual(leverage, 15, "Moderate drawdown should reduce leverage")
        
        # Test severe drawdown
        self.risk_manager.current_drawdown = 0.20  # 20% drawdown
        leverage = self.risk_manager.get_max_leverage(
            volatility=0.02,
            confidence=0.80
        )
        
        # Severe drawdown should reduce leverage significantly
        self.assertLessEqual(leverage, 10, "Severe drawdown should significantly reduce leverage")
    
    def test_leverage_increases_with_confidence(self):
        """Test that leverage increases monotonically with confidence"""
        confidences = [0.40, 0.50, 0.60, 0.70, 0.80, 0.90]
        previous_leverage = 0
        
        for confidence in confidences:
            leverage = self.risk_manager.get_max_leverage(
                volatility=0.02,  # Normal volatility
                confidence=confidence
            )
            self.assertGreaterEqual(leverage, previous_leverage,
                f"Leverage should increase with confidence: {confidence:.2f} -> {leverage}x (was {previous_leverage}x)")
            previous_leverage = leverage
    
    def test_momentum_and_trend_not_affecting_leverage(self):
        """Test that momentum and trend strength don't affect leverage (backward compatibility)"""
        # These parameters are kept for backward compatibility but shouldn't affect leverage
        base_leverage = self.risk_manager.get_max_leverage(
            volatility=0.02,
            confidence=0.70,
            momentum=0.0,
            trend_strength=0.5,
            market_regime='neutral'
        )
        
        # Try different momentum values
        leverage_strong_momentum = self.risk_manager.get_max_leverage(
            volatility=0.02,
            confidence=0.70,
            momentum=0.05,  # Strong momentum
            trend_strength=0.5,
            market_regime='neutral'
        )
        
        # Leverage should be the same (only confidence and volatility matter)
        self.assertEqual(base_leverage, leverage_strong_momentum,
            "Momentum should not affect leverage in new confidence-based system")


if __name__ == '__main__':
    print("Testing confidence-based leverage calculation (2-25x range)...")
    print("=" * 70)
    unittest.main(verbosity=2)
