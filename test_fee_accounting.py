"""
Test suite for trading fee accounting
Validates that fees are correctly deducted from P/L calculations
"""
import unittest
from position_manager import Position


class TestFeeAccounting(unittest.TestCase):
    """Test cases for fee accounting in P/L calculations"""
    
    def test_pnl_without_fees(self):
        """Test P/L calculation without fees (backward compatibility)"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000,
            amount=0.1,
            leverage=5,
            stop_loss=49000,
            take_profit=51000
        )
        
        # 2% price gain
        exit_price = 51000
        pnl = position.get_pnl(exit_price, include_fees=False)
        leveraged_pnl = position.get_leveraged_pnl(exit_price, include_fees=False)
        
        # Without fees: 2% price move * 5x leverage = 10% ROI
        self.assertAlmostEqual(pnl, 0.02, places=4, msg="Base P/L should be 2%")
        self.assertAlmostEqual(leveraged_pnl, 0.10, places=4, msg="Leveraged P/L should be 10%")
    
    def test_pnl_with_fees(self):
        """Test P/L calculation with fees included"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000,
            amount=0.1,
            leverage=5,
            stop_loss=49000,
            take_profit=51000
        )
        
        # 2% price gain
        exit_price = 51000
        pnl = position.get_pnl(exit_price, include_fees=True)
        leveraged_pnl = position.get_leveraged_pnl(exit_price, include_fees=True)
        
        # With fees: (2% - 0.12%) * 5x = 9.4% ROI
        expected_base_pnl = 0.02 - 0.0012  # 1.88%
        expected_leveraged_pnl = expected_base_pnl * 5  # 9.4%
        
        self.assertAlmostEqual(pnl, expected_base_pnl, places=4, 
                              msg="Base P/L with fees should be 1.88%")
        self.assertAlmostEqual(leveraged_pnl, expected_leveraged_pnl, places=4, 
                              msg="Leveraged P/L with fees should be 9.4%")
    
    def test_small_profit_becomes_loss_with_fees(self):
        """Test that small profits can become losses when fees are accounted for"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000,
            amount=0.1,
            leverage=5,
            stop_loss=49000,
            take_profit=51000
        )
        
        # Very small profit: 0.1% price gain
        exit_price = 50050
        pnl_no_fees = position.get_leveraged_pnl(exit_price, include_fees=False)
        pnl_with_fees = position.get_leveraged_pnl(exit_price, include_fees=True)
        
        # Without fees: 0.1% * 5x = 0.5% ROI
        # With fees: (0.1% - 0.12%) * 5x = -0.1% ROI (loss!)
        self.assertGreater(pnl_no_fees, 0, "P/L without fees should be positive")
        self.assertLess(pnl_with_fees, 0, "P/L with fees should be negative (loss)")
    
    def test_short_position_with_fees(self):
        """Test fee accounting for short positions"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='short',
            entry_price=50000,
            amount=0.1,
            leverage=5,
            stop_loss=51000,
            take_profit=49000
        )
        
        # 2% price drop (profitable for short)
        exit_price = 49000
        pnl = position.get_pnl(exit_price, include_fees=True)
        leveraged_pnl = position.get_leveraged_pnl(exit_price, include_fees=True)
        
        # With fees: (2% - 0.12%) * 5x = 9.4% ROI
        expected_base_pnl = 0.02 - 0.0012  # 1.88%
        expected_leveraged_pnl = expected_base_pnl * 5  # 9.4%
        
        self.assertAlmostEqual(pnl, expected_base_pnl, places=4, 
                              msg="Base P/L with fees should be 1.88%")
        self.assertAlmostEqual(leveraged_pnl, expected_leveraged_pnl, places=4, 
                              msg="Leveraged P/L with fees should be 9.4%")
    
    def test_breakeven_calculation(self):
        """Test the minimum price move needed to break even after fees"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000,
            amount=0.1,
            leverage=5,
            stop_loss=49000,
            take_profit=51000
        )
        
        # To break even with 0.12% fees, need 0.12% price gain
        breakeven_price = 50000 * 1.0012  # 50060
        pnl_with_fees = position.get_leveraged_pnl(breakeven_price, include_fees=True)
        
        # Should be very close to 0%
        self.assertAlmostEqual(pnl_with_fees, 0.0, places=3, 
                              msg="P/L should be ~0% at breakeven price")
    
    def test_fee_impact_varies_with_leverage(self):
        """Test that fee impact scales correctly with different leverage"""
        scenarios = [
            (2, 0.02, 0.0024),   # 2x leverage: fees = 0.24% ROI impact (0.12% * 2)
            (5, 0.02, 0.006),    # 5x leverage: fees = 0.6% ROI impact (0.12% * 5)
            (10, 0.02, 0.012),   # 10x leverage: fees = 1.2% ROI impact (0.12% * 10)
        ]
        
        for leverage, price_move, expected_fee_impact in scenarios:
            position = Position(
                symbol='BTC/USDT:USDT',
                side='long',
                entry_price=50000,
                amount=0.1,
                leverage=leverage,
                stop_loss=49000,
                take_profit=51000
            )
            
            exit_price = 50000 * (1 + price_move)  # 2% price gain
            pnl_no_fees = position.get_leveraged_pnl(exit_price, include_fees=False)
            pnl_with_fees = position.get_leveraged_pnl(exit_price, include_fees=True)
            
            fee_impact = pnl_no_fees - pnl_with_fees
            
            self.assertAlmostEqual(fee_impact, expected_fee_impact, places=4,
                                  msg=f"Fee impact at {leverage}x leverage should be {expected_fee_impact*100:.2f}%")


if __name__ == '__main__':
    unittest.main()
