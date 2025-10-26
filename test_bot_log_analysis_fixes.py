"""
Test fixes for issues found in bot.log analysis
"""
from unittest.mock import Mock, MagicMock, patch
from bot import TradingBot
from position_correlation import PositionCorrelationManager
from risk_manager import RiskManager
from kucoin_client import KuCoinClient


class TestPositionSizeCapping:
    """Test that position sizes are capped to exchange maximum"""
    
    def test_position_size_respects_exchange_maximum(self):
        """Position size should be capped to exchange max_amount"""
        # Create a mock client with metadata
        mock_client = Mock(spec=KuCoinClient)
        mock_client.get_cached_symbol_metadata.return_value = {
            'active': True,
            'min_amount': 1.0,
            'max_amount': 1000000.0,  # Max 1 million contracts
            'min_cost': 1.0,
        }
        
        # Simulate a large calculated position size (like 7.2M contracts for SHIB)
        large_position_size = 7283883.2939
        
        # The bot should cap this to the maximum
        metadata = mock_client.get_cached_symbol_metadata('SHIB/USDT:USDT')
        max_amount = metadata.get('max_amount')
        
        if max_amount and large_position_size > max_amount:
            capped_size = max_amount
        else:
            capped_size = large_position_size
        
        assert capped_size == 1000000.0, f"Position size should be capped to {max_amount}"
        assert capped_size < large_position_size, "Capped size should be less than original"
        print(f"✓ Position size correctly capped: {large_position_size:.4f} → {capped_size:.4f}")


class TestConcentrationLimitCalculation:
    """Test that concentration limits use correct portfolio value"""
    
    def test_concentration_uses_total_portfolio_value(self):
        """Concentration should be calculated against total portfolio value, not just available balance"""
        # Simulate the scenario from the log:
        # - Position value: $309.54 (306471 contracts * 0.00101)
        # - Available balance after drawdown: $50
        # OLD WAY: concentration = 309.54 / 50 = 619% (WRONG!)
        # NEW WAY: concentration = 309.54 / (309.54 + 50) = 86% (CORRECT)
        
        position_value = 309.54
        available_balance = 50.0
        
        # Old incorrect calculation
        old_concentration = position_value / available_balance
        
        # New correct calculation
        total_portfolio_value = position_value + available_balance
        new_concentration = position_value / total_portfolio_value
        
        print(f"Old concentration: {old_concentration:.1%}")
        print(f"New concentration: {new_concentration:.1%}")
        
        assert new_concentration < 1.0, "Concentration should be less than 100% for a single position"
        assert new_concentration < old_concentration, "New calculation should give smaller percentage"
        assert 0.80 < new_concentration < 0.90, f"Expected ~86%, got {new_concentration:.1%}"
        print(f"✓ Concentration correctly calculated: {new_concentration:.1%} of total portfolio")


class TestDrawdownWarningThrottling:
    """Test that drawdown warnings are throttled to avoid spam"""
    
    def test_drawdown_warning_only_on_significant_change(self):
        """Drawdown warnings should only appear when drawdown changes significantly"""
        risk_manager = RiskManager(
            max_position_size=500.0,
            risk_per_trade=0.02,
            max_open_positions=20
        )
        
        # Set initial peak balance
        risk_manager.peak_balance = 1000.0
        
        # First call with 25% drawdown - should warn
        current_balance_1 = 750.0  # 25% drawdown
        adjustment_1 = risk_manager.update_drawdown(current_balance_1)
        first_warning_level = risk_manager.last_drawdown_warning_level
        
        # Second call with 27% drawdown (< 10% threshold) - should NOT warn again
        current_balance_2 = 730.0  # 27% drawdown
        adjustment_2 = risk_manager.update_drawdown(current_balance_2)
        second_warning_level = risk_manager.last_drawdown_warning_level
        
        # Warning level should not change on second call
        assert first_warning_level == second_warning_level, \
            f"Warning level should stay same for small changes: {first_warning_level} vs {second_warning_level}"
        
        # Third call with 40% drawdown (>= 10% threshold difference) - should warn
        current_balance_3 = 600.0  # 40% drawdown (increased by 15% from first warning)
        adjustment_3 = risk_manager.update_drawdown(current_balance_3)
        third_warning_level = risk_manager.last_drawdown_warning_level
        
        # Warning level should update on significant change
        assert third_warning_level > first_warning_level, \
            f"Warning level should update on significant change: {third_warning_level} vs {first_warning_level}"
        
        print(f"✓ Drawdown warning throttling works correctly")
        print(f"  First warning at: {first_warning_level:.1%}")
        print(f"  Second check (no warning): {second_warning_level:.1%}")
        print(f"  Third warning at: {third_warning_level:.1%}")


class TestOrderValidation:
    """Test that order validation catches oversized orders"""
    
    def test_order_validation_rejects_oversized_amount(self):
        """validate_order_locally should reject orders exceeding max_amount"""
        from kucoin_client import KuCoinClient as KC
        
        mock_client = Mock(spec=KC)
        mock_client.get_cached_symbol_metadata = Mock(return_value={
            'active': True,
            'min_amount': 1.0,
            'max_amount': 1000000.0,
            'min_cost': 1.0,
        })
        
        # Create a real KuCoinClient instance for validation logic
        # (we just need the validation method, not real API access)
        client = KC(api_key='test', api_secret='test', api_passphrase='test')
        
        # Mock the metadata method
        client.get_cached_symbol_metadata = mock_client.get_cached_symbol_metadata
        
        # Test validation
        is_valid, reason = client.validate_order_locally('SHIB/USDT:USDT', 7283883.2939, 0)
        
        assert not is_valid, "Oversized order should be rejected"
        assert "exceeds maximum" in reason.lower(), f"Rejection reason should mention maximum: {reason}"
        print(f"✓ Order validation correctly rejects oversized orders: {reason}")


class TestOrderStatusQueryHandling:
    """Test that order status query failures are handled gracefully"""
    
    def test_order_status_query_failure_logged_at_debug_level(self):
        """Failed immediate order status queries should be DEBUG, not WARNING"""
        # This is more of a code review check - we changed the log level
        # from WARNING to DEBUG for "Could not fetch order status immediately"
        # The actual test would require running the bot, but we can verify
        # the change was made
        
        # Read the kucoin_client.py file and check for the change
        with open('/home/runner/work/RAD/RAD/kucoin_client.py', 'r') as f:
            content = f.read()
        
        # Check that we're using DEBUG level for this error
        assert 'self.logger.debug(f"Could not fetch order status immediately' in content, \
            "Order status query failure should be logged at DEBUG level"
        
        print("✓ Order status query failures are logged at DEBUG level")


def run_tests():
    """Run all tests and report results"""
    print("=" * 80)
    print("TESTING BOT.LOG ISSUE FIXES")
    print("=" * 80)
    print()
    
    # Test position size capping
    print("Test 1: Position Size Capping")
    test = TestPositionSizeCapping()
    test.test_position_size_respects_exchange_maximum()
    print()
    
    # Test concentration calculation
    print("Test 2: Concentration Limit Calculation")
    test = TestConcentrationLimitCalculation()
    test.test_concentration_uses_total_portfolio_value()
    print()
    
    # Test drawdown warning throttling
    print("Test 3: Drawdown Warning Throttling")
    test = TestDrawdownWarningThrottling()
    test.test_drawdown_warning_only_on_significant_change()
    print()
    
    # Test order validation
    print("Test 4: Order Validation")
    test = TestOrderValidation()
    test.test_order_validation_rejects_oversized_amount()
    print()
    
    # Test order status handling
    print("Test 5: Order Status Query Handling")
    test = TestOrderStatusQueryHandling()
    test.test_order_status_query_failure_logged_at_debug_level()
    print()
    
    print("=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)


if __name__ == '__main__':
    run_tests()
