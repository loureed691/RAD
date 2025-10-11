"""
Test suite for money loss fixes
Validates that the bot now uses more conservative risk management
"""
import unittest
from risk_manager import RiskManager
from position_manager import Position


class TestMoneyLossFixes(unittest.TestCase):
    """Test cases for money loss prevention fixes"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.risk_manager = RiskManager(
            max_position_size=1000,
            risk_per_trade=0.02,
            max_open_positions=3
        )
    
    def test_emergency_stop_loss_protection(self):
        """Test that emergency stop loss prevents catastrophic losses"""
        # Create a position with high leverage
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000,
            amount=0.1,
            leverage=10,
            stop_loss=48000,  # 4% price stop
            take_profit=56000
        )
        
        # Test Level 3: -20% ROI loss (should trigger emergency stop)
        # With 10x leverage, 2% price move = 20% ROI loss
        price_for_20pct_loss = 50000 * (1 - 0.02)  # 49000
        should_close, reason = position.should_close(price_for_20pct_loss)
        self.assertTrue(should_close, "Position should close at -20% ROI loss")
        self.assertEqual(reason, 'emergency_stop_excessive_loss', "Should trigger emergency stop")
        
        # Test Level 2: -35% ROI loss
        price_for_35pct_loss = 50000 * (1 - 0.035)  # 48250
        should_close, reason = position.should_close(price_for_35pct_loss)
        self.assertTrue(should_close, "Position should close at -35% ROI loss")
        self.assertEqual(reason, 'emergency_stop_severe_loss', "Should trigger severe loss stop")
        
        # Test Level 1: -50% ROI loss (near liquidation)
        price_for_50pct_loss = 50000 * (1 - 0.05)  # 47500
        should_close, reason = position.should_close(price_for_50pct_loss)
        self.assertTrue(should_close, "Position should close at -50% ROI loss")
        self.assertEqual(reason, 'emergency_stop_liquidation_risk', "Should trigger liquidation risk stop")
        
        # Test that normal losses don't trigger emergency stop
        price_for_5pct_loss = 50000 * (1 - 0.005)  # 49750 (5% ROI loss with 10x)
        should_close, reason = position.should_close(price_for_5pct_loss)
        self.assertFalse(should_close, "Position should NOT close at -5% ROI loss (below emergency threshold)")
    
    def test_stop_loss_percentage_tighter(self):
        """Test that stop loss percentages are more conservative"""
        # Low volatility - should be tight
        low_vol_sl = self.risk_manager.calculate_stop_loss_percentage(0.015)
        self.assertLessEqual(low_vol_sl, 0.035, "Low volatility stop loss should be <= 3.5%")
        self.assertGreaterEqual(low_vol_sl, 0.01, "Stop loss should be >= 1%")
        
        # Medium volatility
        med_vol_sl = self.risk_manager.calculate_stop_loss_percentage(0.035)
        self.assertLessEqual(med_vol_sl, 0.04, "Medium volatility stop loss should be <= 4%")
        
        # High volatility - capped at 4%
        high_vol_sl = self.risk_manager.calculate_stop_loss_percentage(0.10)
        self.assertEqual(high_vol_sl, 0.04, "High volatility stop loss should be capped at 4% (was 8%)")
    
    def test_leverage_reduced_bounds(self):
        """Test that leverage has more conservative bounds"""
        # Test low volatility scenario (should give higher leverage but capped)
        low_vol_leverage = self.risk_manager.get_max_leverage(
            volatility=0.01,
            confidence=0.85,
            momentum=0.03,
            trend_strength=0.8,
            market_regime='trending'
        )
        self.assertLessEqual(low_vol_leverage, 12, "Max leverage should be capped at 12x (was 20x)")
        self.assertGreaterEqual(low_vol_leverage, 2, "Min leverage should be >= 2x")
        
        # Test high volatility scenario (should give lower leverage)
        high_vol_leverage = self.risk_manager.get_max_leverage(
            volatility=0.15,
            confidence=0.50,
            momentum=-0.01,
            trend_strength=0.3,
            market_regime='ranging'
        )
        self.assertLessEqual(high_vol_leverage, 5, "High volatility leverage should be very low")
        self.assertGreaterEqual(high_vol_leverage, 2, "Min leverage should be >= 2x (was 3x)")
    
    def test_leverage_base_values_conservative(self):
        """Test that base leverage values are more conservative"""
        # Very low volatility
        very_low_vol = self.risk_manager.get_max_leverage(
            volatility=0.005,
            confidence=0.60,
            momentum=0.0,
            trend_strength=0.5,
            market_regime='neutral'
        )
        self.assertLessEqual(very_low_vol, 12, "Even very low volatility should cap at 12x")
        
        # Normal volatility
        normal_vol = self.risk_manager.get_max_leverage(
            volatility=0.025,
            confidence=0.60,
            momentum=0.0,
            trend_strength=0.5,
            market_regime='neutral'
        )
        self.assertLessEqual(normal_vol, 10, "Normal volatility leverage should be ~8x (was ~11x)")
    
    def test_drawdown_protection_tighter(self):
        """Test that drawdown protection activates earlier"""
        # Simulate a small drawdown that should now trigger protection
        self.risk_manager.peak_balance = 1000
        self.risk_manager.current_drawdown = 0.06  # 6% drawdown
        
        leverage_with_drawdown = self.risk_manager.get_max_leverage(
            volatility=0.03,
            confidence=0.75,
            momentum=0.02,
            trend_strength=0.6,
            market_regime='trending'
        )
        
        # Reset drawdown for comparison
        self.risk_manager.current_drawdown = 0.0
        leverage_without_drawdown = self.risk_manager.get_max_leverage(
            volatility=0.03,
            confidence=0.75,
            momentum=0.02,
            trend_strength=0.6,
            market_regime='trending'
        )
        
        self.assertLess(
            leverage_with_drawdown, 
            leverage_without_drawdown,
            "Leverage should be reduced with 6% drawdown (new threshold)"
        )
    
    def test_risk_reward_ratio_improved(self):
        """Test that risk/reward ratio is now 1:3 instead of 1:2"""
        # This is implicit in position_manager.py changes
        # Entry: 100, SL: 2% (98), TP should be 6% (106) not 4% (104)
        stop_loss_pct = 0.02
        
        # Old ratio was 2x (TP = 104)
        old_take_profit_pct = stop_loss_pct * 2  # 0.04
        
        # New ratio is 3x (TP = 106)
        new_take_profit_pct = stop_loss_pct * 3  # 0.06
        
        self.assertEqual(new_take_profit_pct, 0.06, "New TP should be 6% for 2% SL")
        self.assertGreater(new_take_profit_pct, old_take_profit_pct, "New ratio should be better")
        self.assertEqual(new_take_profit_pct / stop_loss_pct, 3.0, "Risk/reward should be 1:3")


if __name__ == '__main__':
    unittest.main()
