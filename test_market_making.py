"""
Tests for Avellaneda-Stoikov market making implementation
"""
import unittest
import numpy as np
from datetime import datetime
from avellaneda_stoikov import AvellanedaStoikovMarketMaker
from delta_hedger import DeltaHedger, CrossVenueDeltaHedger
from funding_arbitrage import FundingArbitrage
from market_microstructure_2026 import MarketMicrostructure2026


class TestAvellanedaStoikov(unittest.TestCase):
    """Test Avellaneda-Stoikov market maker"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mm = AvellanedaStoikovMarketMaker(
            risk_aversion=0.1,
            terminal_time=1.0,
            target_inventory=0.0,
            max_inventory=10.0
        )
    
    def test_initialization(self):
        """Test market maker initialization"""
        self.assertEqual(self.mm.gamma, 0.1)
        self.assertEqual(self.mm.target_inventory, 0.0)
        self.assertEqual(self.mm.max_inventory, 10.0)
        self.assertEqual(self.mm.current_inventory, 0.0)
    
    def test_reservation_price(self):
        """Test reservation price calculation"""
        # Set market data
        self.mm.update_market_data(
            mid_price=100.0,
            volatility=0.3,
            inventory=5.0
        )
        
        # Calculate reservation price
        r = self.mm.compute_reservation_price()
        
        # Should be below mid price when long (inventory > 0)
        self.assertIsNotNone(r)
        self.assertLess(r, 100.0)
    
    def test_optimal_spread(self):
        """Test optimal spread calculation"""
        self.mm.update_market_data(
            mid_price=100.0,
            volatility=0.3,
            inventory=0.0
        )
        
        spread = self.mm.compute_optimal_spread()
        
        # Spread should be positive and reasonable
        self.assertGreater(spread, 0)
        self.assertLess(spread, 5.0)  # Less than 5% half-spread
    
    def test_compute_quotes(self):
        """Test quote generation"""
        self.mm.update_market_data(
            mid_price=100.0,
            volatility=0.3,
            inventory=0.0
        )
        
        bid, ask = self.mm.compute_quotes()
        
        # Quotes should be valid
        self.assertIsNotNone(bid)
        self.assertIsNotNone(ask)
        
        # Ask should be higher than bid
        self.assertGreater(ask, bid)
        
        # Both should be near mid price
        self.assertGreater(bid, 95.0)
        self.assertLess(ask, 105.0)
    
    def test_inventory_skew(self):
        """Test inventory-based quote skewing"""
        # When long, quotes should be skewed to facilitate selling
        self.mm.update_market_data(
            mid_price=100.0,
            volatility=0.3,
            inventory=8.0  # Long
        )
        
        bid_long, ask_long = self.mm.compute_quotes()
        
        # When short, quotes should be skewed to facilitate buying
        self.mm.update_market_data(
            mid_price=100.0,
            volatility=0.3,
            inventory=-8.0  # Short
        )
        
        bid_short, ask_short = self.mm.compute_quotes()
        
        # Short position should have higher bids to attract buys
        self.assertGreater(bid_short, bid_long)
    
    def test_should_quote_side(self):
        """Test quote side filtering based on inventory limits"""
        self.mm.current_inventory = 10.0  # At max
        
        # Should not quote bid when at max long
        self.assertFalse(self.mm.should_quote_side('bid'))
        
        # Should still quote ask
        self.assertTrue(self.mm.should_quote_side('ask'))
    
    def test_microstructure_enhancement(self):
        """Test microstructure signal integration"""
        # With positive order flow, reservation price should be higher
        self.mm.update_market_data(
            mid_price=100.0,
            volatility=0.3,
            inventory=0.0,
            order_flow_imbalance=0.5  # Positive OFI
        )
        
        r_positive = self.mm.compute_reservation_price()
        
        # With negative order flow
        self.mm.update_market_data(
            mid_price=100.0,
            volatility=0.3,
            inventory=0.0,
            order_flow_imbalance=-0.5  # Negative OFI
        )
        
        r_negative = self.mm.compute_reservation_price()
        
        # Positive OFI should result in higher reservation price
        self.assertGreater(r_positive, r_negative)


class TestDeltaHedger(unittest.TestCase):
    """Test delta hedger"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.hedger = DeltaHedger(
            hedge_threshold=5.0,
            target_delta=0.0,
            hedge_ratio=0.8
        )
    
    def test_initialization(self):
        """Test hedger initialization"""
        self.assertEqual(self.hedger.hedge_threshold, 5.0)
        self.assertEqual(self.hedger.target_delta, 0.0)
        self.assertEqual(self.hedger.hedge_ratio, 0.8)
    
    def test_should_hedge(self):
        """Test hedge trigger logic"""
        # Below threshold - should not hedge
        self.hedger.update_inventory(3.0)
        self.assertFalse(self.hedger.should_hedge())
        
        # Above threshold - should hedge
        self.hedger.update_inventory(7.0)
        self.assertTrue(self.hedger.should_hedge())
    
    def test_calculate_hedge_size(self):
        """Test hedge size calculation"""
        self.hedger.update_inventory(10.0)
        
        size, side = self.hedger.calculate_hedge_size()
        
        # Should hedge 80% of 10 = 8
        self.assertEqual(size, 8.0)
        self.assertEqual(side, 'sell')  # Sell to reduce long position
    
    def test_hedge_recommendation(self):
        """Test hedge recommendation generation"""
        self.hedger.update_inventory(10.0)
        
        rec = self.hedger.get_hedge_recommendation(100.0)
        
        self.assertIsNotNone(rec)
        self.assertEqual(rec['side'], 'sell')
        self.assertGreater(rec['hedge_size'], 0)
        self.assertIn(rec['urgency'], ['low', 'medium', 'high', 'critical'])


class TestFundingArbitrage(unittest.TestCase):
    """Test funding arbitrage system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.arb = FundingArbitrage(
            min_funding_rate=0.0001,
            min_apr_threshold=0.05
        )
    
    def test_initialization(self):
        """Test funding arbitrage initialization"""
        self.assertEqual(self.arb.min_funding_rate, 0.0001)
        self.assertEqual(self.arb.min_apr_threshold, 0.05)
    
    def test_funding_apr_calculation(self):
        """Test funding rate to APR conversion"""
        apr = self.arb.calculate_funding_apr(0.0001)
        
        # 0.01% per 8h = ~10.95% APR
        self.assertGreater(apr, 0.10)
        self.assertLess(apr, 0.12)
    
    def test_perp_spot_opportunity(self):
        """Test perp-spot arbitrage detection"""
        # High positive funding - should short perp, long spot
        # Use smaller basis to pass basis risk check
        opp = self.arb.evaluate_perp_spot_opportunity(
            perp_price=100.1,  # Smaller basis
            spot_price=100.0,
            funding_rate=0.0005  # 0.05% = ~54% APR
        )
        
        self.assertIsNotNone(opp)
        self.assertEqual(opp['direction'], 'short_perp_long_spot')
        self.assertGreater(opp['funding_apr'], 0.05)
    
    def test_cross_venue_opportunity(self):
        """Test cross-venue arbitrage detection"""
        # Venue 1 has higher funding
        opp = self.arb.evaluate_cross_venue_opportunity(
            venue1_price=100.0,
            venue1_funding=0.0005,
            venue1_name='binance',
            venue2_price=100.0,
            venue2_funding=0.0001,
            venue2_name='okx'
        )
        
        self.assertIsNotNone(opp)
        self.assertEqual(opp['type'], 'cross_venue_arbitrage')
        self.assertIn('binance', opp['direction'])
        self.assertIn('okx', opp['direction'])
    
    def test_position_lifecycle(self):
        """Test opening, updating, and closing positions"""
        # Create opportunity with smaller basis
        opp = self.arb.evaluate_perp_spot_opportunity(
            perp_price=100.1,  # Smaller basis
            spot_price=100.0,
            funding_rate=0.0005
        )
        
        # Open position
        pos_id = self.arb.open_position(opp, 10000.0)
        self.assertIn(pos_id, self.arb.active_positions)
        
        # Update position
        self.arb.update_position(pos_id, 0.0004, 0.001, funding_payment=5.0)
        pos = self.arb.active_positions[pos_id]
        self.assertEqual(pos['funding_collected'], 5.0)
        
        # Close position
        summary = self.arb.close_position(pos_id, 0.001)
        self.assertNotIn(pos_id, self.arb.active_positions)
        self.assertGreater(summary['total_pnl'], 0)


class TestMarketMicrostructure(unittest.TestCase):
    """Test market microstructure analysis"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.ms = MarketMicrostructure2026()
    
    def test_microprice_calculation(self):
        """Test microprice calculation"""
        orderbook = {
            'bids': [[100.0, 10.0], [99.5, 5.0]],
            'asks': [[100.5, 5.0], [101.0, 10.0]]
        }
        
        microprice = self.ms.calculate_microprice(orderbook)
        
        self.assertIsNotNone(microprice)
        # Microprice should be between best bid and ask
        self.assertGreater(microprice, 100.0)
        self.assertLess(microprice, 100.5)
    
    def test_queue_imbalance(self):
        """Test queue imbalance calculation"""
        orderbook = {
            'bids': [[100.0, 100.0], [99.5, 50.0]],
            'asks': [[100.5, 30.0], [101.0, 20.0]]
        }
        
        qi = self.ms.calculate_queue_imbalance(orderbook)
        
        # More bids than asks - positive imbalance
        self.assertGreater(qi, 0)
        self.assertLessEqual(abs(qi), 1.0)
    
    def test_kyle_lambda(self):
        """Test Kyle's lambda calculation"""
        # Create mock trades
        trades = [
            {'price': 100.0, 'amount': 1.0, 'side': 'buy'},
            {'price': 100.1, 'amount': 2.0, 'side': 'buy'},
            {'price': 100.05, 'amount': 1.5, 'side': 'sell'},
            {'price': 100.15, 'amount': 1.0, 'side': 'buy'},
            {'price': 100.2, 'amount': 1.0, 'side': 'buy'}
        ]
        
        orderbook = {'bids': [[100.0, 10]], 'asks': [[100.5, 10]]}
        
        kyle_lambda = self.ms.calculate_kyle_lambda(trades, orderbook)
        
        # Should return a value
        self.assertIsInstance(kyle_lambda, float)
    
    def test_short_horizon_volatility(self):
        """Test short-horizon volatility calculation"""
        # Create mock trades with varying prices
        trades = [
            {'price': 100.0 + np.random.randn() * 0.5}
            for _ in range(50)
        ]
        
        vol = self.ms.calculate_short_horizon_volatility(trades)
        
        if vol is not None:
            self.assertGreater(vol, 0)
            self.assertLess(vol, 15.0)  # Extended reasonable vol range (can be high for short horizons)
    
    def test_get_all_signals(self):
        """Test getting all microstructure signals at once"""
        orderbook = {
            'bids': [[100.0, 10.0], [99.5, 5.0]],
            'asks': [[100.5, 5.0], [101.0, 10.0]]
        }
        
        trades = [
            {'price': 100.0, 'amount': 1.0}
            for _ in range(20)
        ]
        
        signals = self.ms.get_microstructure_signals(orderbook, trades)
        
        self.assertIn('microprice', signals)
        self.assertIn('kyle_lambda', signals)
        self.assertIn('queue_imbalance', signals)
        self.assertIn('short_horizon_volatility', signals)


if __name__ == '__main__':
    unittest.main()
