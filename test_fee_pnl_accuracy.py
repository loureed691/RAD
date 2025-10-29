#!/usr/bin/env python3
"""
Deep testing for fee calculations and position PnL accuracy.
Tests to ensure fees are calculated correctly and PnL matches real trading results.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from position_manager import Position


class TestFeeCalculationAccuracy(unittest.TestCase):
    """Test fee calculation accuracy and PnL correctness"""
    
    def test_fee_calculation_with_leverage(self):
        """Test that fees are calculated correctly with leverage"""
        # KuCoin futures fees: 0.06% taker fee
        # Entry: 0.06% on notional value
        # Exit: 0.06% on notional value  
        # Total: 0.12% on notional value
        
        # Example: $10,000 balance, 10x leverage
        # Position size: $10,000
        # Notional value: $10,000 * 10 = $100,000
        # Entry fee: $100,000 * 0.0006 = $60
        # Exit fee: $100,000 * 0.0006 = $60
        # Total fees: $120
        
        # Fees as % of balance: $120 / $10,000 = 1.2%
        
        entry_price = 50000
        amount = 0.2  # $10,000 / $50,000 = 0.2 BTC
        leverage = 10
        
        position = Position(
            symbol='BTCUSDT',
            side='long',
            entry_price=entry_price,
            amount=amount,
            leverage=leverage,
            stop_loss=49000
        )
        
        # Test 1: Breakeven trade (price doesn't change)
        # PnL should be negative due to fees
        pnl_with_fees = position.get_leveraged_pnl(entry_price, include_fees=True)
        
        # The fees should be 0.12% * leverage = 1.2% of position value
        # Wait, actually the current implementation applies fees before leverage
        # Let's calculate what we expect:
        # Base PnL = 0% (no price change)
        # After fees = 0% - 0.12% = -0.12%
        # After leverage = -0.12% * 10 = -1.2%
        
        expected_fee_impact = -0.0012 * leverage
        self.assertAlmostEqual(pnl_with_fees, expected_fee_impact, places=4,
                              msg=f"Breakeven trade should show {expected_fee_impact:.2%} loss due to fees")
    
    def test_small_profit_eaten_by_fees(self):
        """Test that small profits can be eaten by fees"""
        entry_price = 50000
        amount = 0.2
        leverage = 10
        
        position = Position(
            symbol='BTCUSDT',
            side='long',
            entry_price=entry_price,
            amount=amount,
            leverage=leverage,
            stop_loss=49000
        )
        
        # Small price increase: 0.1%
        exit_price = entry_price * 1.001
        
        # Without fees: 0.1% * 10x = 1.0% profit
        pnl_no_fees = position.get_leveraged_pnl(exit_price, include_fees=False)
        self.assertAlmostEqual(pnl_no_fees, 0.01, places=3)
        
        # With fees: 0.1% - 0.12% = -0.02%, then * 10x = -0.2% (net loss!)
        pnl_with_fees = position.get_leveraged_pnl(exit_price, include_fees=True)
        
        # The trade should result in a small loss after fees
        self.assertLess(pnl_with_fees, 0, 
                       "Small 0.1% price move should result in loss after 0.12% fees")
    
    def test_minimum_profitable_trade(self):
        """Test minimum price move needed for profitable trade"""
        entry_price = 50000
        amount = 0.2
        leverage = 10
        
        position = Position(
            symbol='BTCUSDT',
            side='long',
            entry_price=entry_price,
            amount=amount,
            leverage=leverage,
            stop_loss=49000
        )
        
        # Need at least 0.12% + desired profit to be profitable
        # For 0.5% profit: need 0.12% + 0.5% = 0.62% price move
        min_profitable_move = 0.0062
        exit_price = entry_price * (1 + min_profitable_move)
        
        pnl_with_fees = position.get_leveraged_pnl(exit_price, include_fees=True)
        
        # After fees, should have approximately 0.5% * 10x = 5% profit
        expected_profit = (min_profitable_move - 0.0012) * leverage
        self.assertAlmostEqual(pnl_with_fees, expected_profit, places=3)
        
        # Profit should be positive
        self.assertGreater(pnl_with_fees, 0)
    
    def test_fee_impact_with_different_leverage(self):
        """Test how fees scale with different leverage levels"""
        entry_price = 50000
        amount = 0.2
        
        # Test with different leverage levels
        for leverage in [1, 5, 10, 20, 50]:
            position = Position(
                symbol='BTCUSDT',
                side='long',
                entry_price=entry_price,
                amount=amount,
                leverage=leverage,
                stop_loss=entry_price * 0.98
            )
            
            # 1% price move
            exit_price = entry_price * 1.01
            
            pnl_no_fees = position.get_leveraged_pnl(exit_price, include_fees=False)
            pnl_with_fees = position.get_leveraged_pnl(exit_price, include_fees=True)
            
            # Fee impact should be 0.12% * leverage
            expected_fee_impact = 0.0012 * leverage
            actual_fee_impact = pnl_no_fees - pnl_with_fees
            
            self.assertAlmostEqual(actual_fee_impact, expected_fee_impact, places=3,
                                 msg=f"Fee impact at {leverage}x leverage should be {expected_fee_impact:.2%}")
    
    def test_short_position_fees(self):
        """Test fee calculation for short positions"""
        entry_price = 50000
        amount = 0.2
        leverage = 10
        
        position = Position(
            symbol='BTCUSDT',
            side='short',
            entry_price=entry_price,
            amount=amount,
            leverage=leverage,
            stop_loss=51000
        )
        
        # Price drops 1% (profit for short)
        exit_price = entry_price * 0.99
        
        pnl_no_fees = position.get_leveraged_pnl(exit_price, include_fees=False)
        pnl_with_fees = position.get_leveraged_pnl(exit_price, include_fees=True)
        
        # Should have 1% * 10x = 10% profit before fees
        self.assertAlmostEqual(pnl_no_fees, 0.10, places=3)
        
        # After fees: (1% - 0.12%) * 10x = 8.8% profit
        expected_profit_with_fees = (0.01 - 0.0012) * leverage
        self.assertAlmostEqual(pnl_with_fees, expected_profit_with_fees, places=3)


class TestPositionPnLCornerCases(unittest.TestCase):
    """Test corner cases in PnL calculation"""
    
    def test_zero_price_handling(self):
        """Test handling of zero or negative prices"""
        position = Position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            amount=0.1,
            leverage=10,
            stop_loss=49000
        )
        
        # Zero price should return 0 PnL (not crash)
        pnl = position.get_pnl(0)
        self.assertEqual(pnl, 0.0)
        
        # Negative price should return 0 PnL (not crash)
        pnl = position.get_pnl(-100)
        self.assertEqual(pnl, 0.0)
    
    def test_extreme_price_movements(self):
        """Test PnL calculation with extreme price movements"""
        position = Position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000,
            amount=0.1,
            leverage=10,
            stop_loss=49000
        )
        
        # 50% price crash
        crash_price = 25000
        pnl = position.get_leveraged_pnl(crash_price)
        
        # -50% * 10x = -500% (would be liquidated in real trading)
        self.assertAlmostEqual(pnl, -5.0, places=1)
        
        # 100% price increase
        moon_price = 100000
        pnl = position.get_leveraged_pnl(moon_price)
        
        # +100% * 10x = +1000%
        self.assertAlmostEqual(pnl, 10.0, places=1)
    
    def test_floating_point_precision(self):
        """Test PnL calculation with floating point precision"""
        position = Position(
            symbol='BTCUSDT',
            side='long',
            entry_price=50000.12345678,
            amount=0.1,
            leverage=10,
            stop_loss=49000
        )
        
        # Very small price change
        exit_price = 50000.12345679
        pnl = position.get_pnl(exit_price)
        
        # Should handle tiny changes without errors
        self.assertIsNotNone(pnl)
        self.assertFalse(pnl != pnl)  # Check for NaN


class TestLiquidationRisk(unittest.TestCase):
    """Test liquidation risk calculations"""
    
    def test_liquidation_threshold_estimation(self):
        """Test estimation of liquidation price"""
        # With 10x leverage, liquidation happens around -10% price move
        # (actually a bit less due to fees, typically -9% to -9.5%)
        
        entry_price = 50000
        leverage = 10
        
        position = Position(
            symbol='BTCUSDT',
            side='long',
            entry_price=entry_price,
            amount=0.1,
            leverage=leverage,
            stop_loss=49000
        )
        
        # Estimate liquidation price (rough approximation)
        # For long: liquidation at entry_price * (1 - 1/leverage)
        estimated_liq_price = entry_price * (1 - 0.9 / leverage)
        
        # At liquidation price, should have approximately -100% ROI
        pnl_at_liq = position.get_leveraged_pnl(estimated_liq_price)
        
        # Should be close to -100% (may not be exact due to fees)
        self.assertLess(pnl_at_liq, -0.85, "Should be near liquidation")
        self.assertGreater(pnl_at_liq, -1.1, "Should not exceed -110% ROI")
    
    def test_high_leverage_liquidation_risk(self):
        """Test liquidation risk with very high leverage"""
        entry_price = 50000
        leverage = 100  # Very high leverage
        
        position = Position(
            symbol='BTCUSDT',
            side='long',
            entry_price=entry_price,
            amount=0.1,
            leverage=leverage,
            stop_loss=49500
        )
        
        # With 100x leverage, a 1% price drop = -100% ROI (liquidation)
        price_drop_1pct = entry_price * 0.99
        pnl = position.get_leveraged_pnl(price_drop_1pct)
        
        # Should be approximately -100% ROI
        self.assertAlmostEqual(pnl, -1.0, delta=0.1)


def run_tests():
    """Run all fee and PnL tests"""
    print("=" * 70)
    print("💰 DEEP FEE CALCULATION & PnL ACCURACY TESTING")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestFeeCalculationAccuracy))
    suite.addTests(loader.loadTestsFromTestCase(TestPositionPnLCornerCases))
    suite.addTests(loader.loadTestsFromTestCase(TestLiquidationRisk))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("📊 FEE & PnL TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
