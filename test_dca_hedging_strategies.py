"""
Comprehensive tests for DCA and Hedging strategies
"""
import unittest
from datetime import datetime, timedelta
from dca_strategy import DCAStrategy
from hedging_strategy import HedgingStrategy


class TestDCAStrategy(unittest.TestCase):
    """Test DCA Strategy implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dca = DCAStrategy()
    
    def test_initialization(self):
        """Test DCA strategy initializes correctly"""
        self.assertTrue(self.dca.entry_dca_enabled)
        self.assertTrue(self.dca.accumulation_dca_enabled)
        self.assertTrue(self.dca.range_dca_enabled)
        self.assertEqual(self.dca.entry_dca_num_entries, 3)
        print("✓ DCA strategy initialization test passed")
    
    def test_entry_dca_plan_creation(self):
        """Test entry DCA plan creation"""
        symbol = 'BTC-USDT'
        signal = 'BUY'
        total_amount = 1.0
        entry_price = 50000
        confidence = 0.65
        
        plan = self.dca.initialize_entry_dca(
            symbol, signal, total_amount, entry_price, confidence
        )
        
        self.assertEqual(plan['symbol'], symbol)
        self.assertEqual(plan['signal'], signal)
        self.assertEqual(plan['total_amount'], total_amount)
        self.assertEqual(plan['num_entries'], 3)  # For 0.65 confidence
        self.assertTrue(plan['active'])
        self.assertEqual(plan['completed_entries'], 0)
        
        # Check entry prices are decreasing for BUY (buying lower)
        self.assertGreater(plan['entry_prices'][0], plan['entry_prices'][1])
        self.assertGreater(plan['entry_prices'][1], plan['entry_prices'][2])
        
        print(f"✓ Entry DCA plan created: {plan['num_entries']} entries")
        print(f"  Entry prices: {[f'${p:.2f}' for p in plan['entry_prices']]}")
    
    def test_entry_dca_high_confidence(self):
        """Test DCA with high confidence creates fewer entries"""
        plan = self.dca.initialize_entry_dca(
            'ETH-USDT', 'BUY', 1.0, 3000, confidence=0.80
        )
        
        self.assertEqual(plan['num_entries'], 2)  # High confidence = 2 entries
        print("✓ High confidence DCA creates 2 entries")
    
    def test_entry_dca_low_confidence(self):
        """Test DCA with low confidence creates more entries"""
        plan = self.dca.initialize_entry_dca(
            'SOL-USDT', 'BUY', 1.0, 100, confidence=0.55
        )
        
        self.assertEqual(plan['num_entries'], 4)  # Low confidence = 4 entries
        print("✓ Low confidence DCA creates 4 entries")
    
    def test_get_next_entry(self):
        """Test getting next DCA entry"""
        symbol = 'BTC-USDT'
        plan = self.dca.initialize_entry_dca(
            symbol, 'BUY', 1.0, 50000, 0.65
        )
        
        # Price at first entry level
        current_price = plan['entry_prices'][0]
        result = self.dca.get_next_entry(symbol, current_price)
        
        self.assertIsNotNone(result)
        amount, price = result
        self.assertGreater(amount, 0)
        self.assertAlmostEqual(price, current_price, delta=100)
        
        print(f"✓ Next entry triggered at ${price:.2f}, amount: {amount:.4f}")
    
    def test_record_entry(self):
        """Test recording completed DCA entry"""
        symbol = 'BTC-USDT'
        plan = self.dca.initialize_entry_dca(
            symbol, 'BUY', 1.0, 50000, 0.65
        )
        
        # Record first entry
        success = self.dca.record_entry(symbol, 0.4, 50000)
        
        self.assertTrue(success)
        updated_plan = self.dca.get_dca_plan(symbol)
        self.assertEqual(updated_plan['completed_entries'], 1)
        self.assertAlmostEqual(updated_plan['total_filled'], 0.4, places=6)
        self.assertAlmostEqual(updated_plan['average_entry_price'], 50000, places=2)
        
        print(f"✓ Entry recorded: {updated_plan['completed_entries']}/{updated_plan['num_entries']}")
        print(f"  Average entry: ${updated_plan['average_entry_price']:.2f}")
    
    def test_dca_completion(self):
        """Test DCA plan completes after all entries"""
        symbol = 'BTC-USDT'
        plan = self.dca.initialize_entry_dca(
            symbol, 'BUY', 1.0, 50000, 0.80  # 2 entries
        )
        
        # Complete all entries
        self.dca.record_entry(symbol, 0.6, 50000)
        self.dca.record_entry(symbol, 0.4, 49500)
        
        updated_plan = self.dca.get_dca_plan(symbol)
        self.assertFalse(updated_plan['active'])
        self.assertEqual(updated_plan['completed_entries'], 2)
        
        # Check average price calculation
        expected_avg = (0.6 * 50000 + 0.4 * 49500) / 1.0
        self.assertAlmostEqual(updated_plan['average_entry_price'], expected_avg, places=2)
        
        print(f"✓ DCA completed: {updated_plan['completed_entries']} entries")
        print(f"  Final average: ${updated_plan['average_entry_price']:.2f}")
    
    def test_accumulation_dca(self):
        """Test accumulation DCA logic"""
        symbol = 'BTC-USDT'
        entry_price = 50000
        current_price = 51000
        current_pnl = 0.025  # 2.5% profit
        
        should_accumulate = self.dca.should_accumulate(
            symbol, current_price, entry_price, current_pnl, existing_adds=0
        )
        
        self.assertTrue(should_accumulate)
        
        # Test accumulation amount
        amount = self.dca.get_accumulation_amount(1.0, add_number=1)
        self.assertAlmostEqual(amount, 0.5, places=2)  # 50% of original
        
        print(f"✓ Accumulation triggered at {current_pnl*100:.1f}% profit")
        print(f"  Add amount: {amount:.2f} (50% of original)")
    
    def test_accumulation_max_adds(self):
        """Test accumulation respects max adds limit"""
        symbol = 'BTC-USDT'
        
        # Already have max adds
        should_accumulate = self.dca.should_accumulate(
            symbol, 51000, 50000, 0.03, existing_adds=2
        )
        
        self.assertFalse(should_accumulate)
        print("✓ Accumulation respects max adds limit")
    
    def test_range_dca_plan(self):
        """Test range DCA plan creation"""
        symbol = 'BTC-USDT'
        signal = 'BUY'
        total_amount = 1.0
        support = 48000
        resistance = 52000
        
        plan = self.dca.initialize_range_dca(
            symbol, signal, total_amount, support, resistance
        )
        
        self.assertEqual(plan['symbol'], symbol)
        self.assertEqual(plan['strategy_type'], 'range_dca')
        self.assertEqual(plan['num_entries'], 4)
        
        # Check prices are in range
        for price in plan['entry_prices']:
            self.assertGreaterEqual(price, support)
            self.assertLessEqual(price, resistance)
        
        print(f"✓ Range DCA plan created")
        print(f"  Range: ${support:.2f} - ${resistance:.2f}")
        print(f"  {plan['num_entries']} entries")
    
    def test_cancel_dca_plan(self):
        """Test canceling DCA plan"""
        symbol = 'BTC-USDT'
        self.dca.initialize_entry_dca(symbol, 'BUY', 1.0, 50000, 0.65)
        
        success = self.dca.cancel_dca_plan(symbol)
        
        self.assertTrue(success)
        plan = self.dca.get_dca_plan(symbol)
        self.assertFalse(plan['active'])
        
        print("✓ DCA plan cancelled successfully")
    
    def test_cleanup_old_plans(self):
        """Test cleanup of old DCA plans"""
        # Create an old inactive plan
        symbol = 'BTC-USDT'
        self.dca.initialize_entry_dca(symbol, 'BUY', 1.0, 50000, 0.65)
        plan = self.dca.get_dca_plan(symbol)
        plan['active'] = False
        plan['created_at'] = datetime.now() - timedelta(hours=48)
        
        self.dca.cleanup_old_plans(max_age_hours=24)
        
        self.assertNotIn(symbol, self.dca.dca_positions)
        print("✓ Old DCA plans cleaned up")


class TestHedgingStrategy(unittest.TestCase):
    """Test Hedging Strategy implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.hedging = HedgingStrategy()
    
    def test_initialization(self):
        """Test hedging strategy initializes correctly"""
        self.assertTrue(self.hedging.hedging_enabled)
        self.assertEqual(self.hedging.hedge_instrument, 'BTC-USDT')
        self.assertEqual(self.hedging.drawdown_hedge_threshold, 0.10)
        print("✓ Hedging strategy initialization test passed")
    
    def test_drawdown_hedge_trigger(self):
        """Test drawdown hedge triggers correctly"""
        current_drawdown = 0.12  # 12% drawdown
        portfolio_value = 10000
        
        recommendation = self.hedging.should_hedge_drawdown(
            current_drawdown, portfolio_value
        )
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation['reason'], 'drawdown_protection')
        self.assertAlmostEqual(
            recommendation['hedge_size'],
            portfolio_value * self.hedging.drawdown_hedge_ratio,
            places=2
        )
        self.assertEqual(recommendation['urgency'], 'medium')
        
        print(f"✓ Drawdown hedge triggered at {current_drawdown*100:.0f}%")
        print(f"  Hedge size: ${recommendation['hedge_size']:.2f}")
    
    def test_drawdown_hedge_no_trigger(self):
        """Test drawdown hedge doesn't trigger below threshold"""
        recommendation = self.hedging.should_hedge_drawdown(0.05, 10000)
        
        self.assertIsNone(recommendation)
        print("✓ Drawdown hedge correctly not triggered below threshold")
    
    def test_volatility_hedge_trigger(self):
        """Test volatility hedge triggers correctly"""
        current_volatility = 0.10  # 10% volatility
        portfolio_value = 10000
        portfolio_beta = 1.2
        
        recommendation = self.hedging.should_hedge_volatility(
            current_volatility, portfolio_value, portfolio_beta
        )
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation['reason'], 'volatility_protection')
        
        # Check beta adjustment
        expected_hedge = portfolio_value * self.hedging.volatility_hedge_ratio * portfolio_beta
        self.assertAlmostEqual(recommendation['hedge_size'], expected_hedge, places=2)
        
        print(f"✓ Volatility hedge triggered at {current_volatility*100:.0f}%")
        print(f"  Hedge size: ${recommendation['hedge_size']:.2f} (beta adjusted)")
    
    def test_correlation_hedge_trigger(self):
        """Test correlation hedge triggers when portfolio too concentrated"""
        # Create heavily long-biased portfolio
        open_positions = {
            'BTC-USDT': {'side': 'long', 'notional_value': 5000},
            'ETH-USDT': {'side': 'long', 'notional_value': 3000},
            'SOL-USDT': {'side': 'short', 'notional_value': 1000}
        }
        portfolio_value = 10000
        
        recommendation = self.hedging.should_hedge_correlation(
            open_positions, portfolio_value
        )
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation['reason'], 'correlation_protection')
        self.assertEqual(recommendation['hedge_side'], 'short')
        self.assertEqual(recommendation['concentrated_side'], 'long')
        
        print(f"✓ Correlation hedge triggered")
        print(f"  Long: ${recommendation['long_exposure']:.2f}, Short: ${recommendation['short_exposure']:.2f}")
        print(f"  Hedge: {recommendation['hedge_side']} ${recommendation['hedge_size']:.2f}")
    
    def test_correlation_hedge_balanced_portfolio(self):
        """Test no hedge for balanced portfolio"""
        # Balanced portfolio
        open_positions = {
            'BTC-USDT': {'side': 'long', 'notional_value': 4000},
            'ETH-USDT': {'side': 'short', 'notional_value': 3500}
        }
        
        recommendation = self.hedging.should_hedge_correlation(
            open_positions, 10000
        )
        
        self.assertIsNone(recommendation)
        print("✓ No correlation hedge for balanced portfolio")
    
    def test_create_hedge(self):
        """Test hedge creation"""
        recommendation = {
            'reason': 'drawdown_protection',
            'trigger_value': 0.12,
            'threshold': 0.10,
            'hedge_size': 5000,
            'instrument': 'BTC-USDT',
            'urgency': 'high'
        }
        
        hedge_id = self.hedging.create_hedge(recommendation)
        
        self.assertIsNotNone(hedge_id)
        self.assertIn(hedge_id, self.hedging.active_hedges)
        
        hedge = self.hedging.active_hedges[hedge_id]
        self.assertEqual(hedge['reason'], 'drawdown_protection')
        self.assertEqual(hedge['status'], 'active')
        self.assertEqual(hedge['hedge_size'], 5000)
        
        print(f"✓ Hedge created: {hedge_id}")
        print(f"  Reason: {hedge['reason']}, Size: ${hedge['hedge_size']:.2f}")
    
    def test_close_hedge_drawdown_recovery(self):
        """Test hedge closes when drawdown recovers"""
        # Create drawdown hedge
        recommendation = {
            'reason': 'drawdown_protection',
            'trigger_value': 0.12,
            'threshold': 0.10,
            'hedge_size': 5000,
            'instrument': 'BTC-USDT',
            'urgency': 'high'
        }
        hedge_id = self.hedging.create_hedge(recommendation)
        
        # Check if should close when drawdown recovers
        current_conditions = {'drawdown': 0.05}  # Recovered to 5%
        should_close = self.hedging.should_close_hedge(hedge_id, current_conditions)
        
        self.assertTrue(should_close)
        print("✓ Hedge closes when drawdown recovers")
    
    def test_close_hedge_volatility_normalized(self):
        """Test hedge closes when volatility normalizes"""
        # Create volatility hedge
        recommendation = {
            'reason': 'volatility_protection',
            'trigger_value': 0.10,
            'threshold': 0.08,
            'hedge_size': 3000,
            'instrument': 'BTC-USDT',
            'urgency': 'medium'
        }
        hedge_id = self.hedging.create_hedge(recommendation)
        
        # Check if should close when volatility normalizes
        current_conditions = {'volatility': 0.05}  # Back to 5%
        should_close = self.hedging.should_close_hedge(hedge_id, current_conditions)
        
        self.assertTrue(should_close)
        print("✓ Hedge closes when volatility normalizes")
    
    def test_hedge_stop_loss(self):
        """Test hedge closes if losing too much"""
        recommendation = {
            'reason': 'drawdown_protection',
            'trigger_value': 0.12,
            'threshold': 0.10,
            'hedge_size': 5000,
            'instrument': 'BTC-USDT',
            'urgency': 'high'
        }
        hedge_id = self.hedging.create_hedge(recommendation)
        
        # Update with large loss
        self.hedging.update_hedge_pnl(hedge_id, -0.06)  # -6% loss
        
        current_conditions = {'drawdown': 0.12}  # Still in drawdown
        should_close = self.hedging.should_close_hedge(hedge_id, current_conditions)
        
        self.assertTrue(should_close)
        print("✓ Hedge closes on stop loss")
    
    def test_hedge_cooldown(self):
        """Test hedge cooldown prevents too frequent hedging"""
        # Create first hedge
        recommendation = {
            'reason': 'drawdown_protection',
            'trigger_value': 0.12,
            'threshold': 0.10,
            'hedge_size': 5000,
            'instrument': 'BTC-USDT',
            'urgency': 'high'
        }
        self.hedging.create_hedge(recommendation)
        
        # Try to create another immediately
        recommendation2 = self.hedging.should_hedge_drawdown(0.12, 10000)
        
        self.assertIsNone(recommendation2)
        print("✓ Hedge cooldown prevents frequent hedging")
    
    def test_event_hedge_scheduling(self):
        """Test scheduling hedge for known event"""
        event_name = "Fed Announcement"
        start_time = datetime.now() + timedelta(hours=2)
        portfolio_value = 10000
        
        recommendation = self.hedging.schedule_event_hedge(
            event_name, start_time, portfolio_value, hedge_ratio=0.5
        )
        
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation['reason'], 'event_protection')
        self.assertEqual(recommendation['event_name'], event_name)
        self.assertAlmostEqual(recommendation['hedge_size'], 5000, places=2)
        
        print(f"✓ Event hedge scheduled for {event_name}")
        print(f"  Time until event: {recommendation['trigger_value']:.1f} hours")
    
    def test_total_hedge_exposure(self):
        """Test calculation of total hedge exposure"""
        # Create multiple hedges
        rec1 = {
            'reason': 'drawdown_protection',
            'trigger_value': 0.12,
            'threshold': 0.10,
            'hedge_size': 5000,
            'instrument': 'BTC-USDT',
            'urgency': 'high'
        }
        rec2 = {
            'reason': 'volatility_protection',
            'trigger_value': 0.10,
            'threshold': 0.08,
            'hedge_size': 3000,
            'instrument': 'BTC-USDT',
            'urgency': 'medium'
        }
        
        # Reset last_hedge_time to allow multiple hedges
        self.hedging.last_hedge_time = None
        self.hedging.create_hedge(rec1)
        self.hedging.last_hedge_time = None
        self.hedging.create_hedge(rec2)
        
        total_exposure = self.hedging.get_total_hedge_exposure()
        
        self.assertAlmostEqual(total_exposure, 8000, places=2)
        print(f"✓ Total hedge exposure calculated: ${total_exposure:.2f}")
    
    def test_cleanup_old_hedges(self):
        """Test cleanup of old closed hedges"""
        # Create and close a hedge
        recommendation = {
            'reason': 'drawdown_protection',
            'trigger_value': 0.12,
            'threshold': 0.10,
            'hedge_size': 5000,
            'instrument': 'BTC-USDT',
            'urgency': 'high'
        }
        hedge_id = self.hedging.create_hedge(recommendation)
        self.hedging.close_hedge(hedge_id, final_pnl=0.02)
        
        # Make it old
        self.hedging.active_hedges[hedge_id]['closed_at'] = datetime.now() - timedelta(hours=72)
        
        self.hedging.cleanup_old_hedges(max_age_hours=48)
        
        self.assertNotIn(hedge_id, self.hedging.active_hedges)
        print("✓ Old hedges cleaned up")


def run_all_tests():
    """Run all DCA and Hedging tests"""
    print("=" * 60)
    print("Running DCA Strategy Tests")
    print("=" * 60)
    
    dca_suite = unittest.TestLoader().loadTestsFromTestCase(TestDCAStrategy)
    dca_result = unittest.TextTestRunner(verbosity=0).run(dca_suite)
    
    print("\n" + "=" * 60)
    print("Running Hedging Strategy Tests")
    print("=" * 60)
    
    hedging_suite = unittest.TestLoader().loadTestsFromTestCase(TestHedgingStrategy)
    hedging_result = unittest.TextTestRunner(verbosity=0).run(hedging_suite)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"DCA Tests: {dca_result.testsRun} run, "
          f"{len(dca_result.failures)} failures, "
          f"{len(dca_result.errors)} errors")
    print(f"Hedging Tests: {hedging_result.testsRun} run, "
          f"{len(hedging_result.failures)} failures, "
          f"{len(hedging_result.errors)} errors")
    
    total_tests = dca_result.testsRun + hedging_result.testsRun
    total_failures = len(dca_result.failures) + len(hedging_result.failures)
    total_errors = len(dca_result.errors) + len(hedging_result.errors)
    
    if total_failures == 0 and total_errors == 0:
        print(f"\n✅ ALL {total_tests} TESTS PASSED!")
        return True
    else:
        print(f"\n❌ SOME TESTS FAILED")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
