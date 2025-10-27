"""
Comprehensive tests for institutional-grade stop loss and take profit strategies

Tests ATR Chandelier Exit, ATR-based partial profit taking, and time-based stops.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from position_manager import Position, PositionManager


class TestATRChandelierExit:
    """Test ATR Chandelier Exit stop loss strategy"""
    
    def test_long_position_atr_stop_basic(self):
        """Test basic ATR Chandelier stop for long position"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        # Price moves up, establishing new high
        position.highest_price = 52000.0
        atr = 800.0  # 1.6% of price
        
        # Update trailing stop with ATR (normal volatility, 2.0x multiplier)
        position.update_trailing_stop(
            current_price=52000.0,
            trailing_percentage=0.02,
            volatility=0.03,  # Normal volatility
            momentum=0.01,
            atr=atr
        )
        
        # Expected: 52000 - (800 × 2.0) = 50400
        assert position.stop_loss == 50400.0
        assert position.stop_loss > position.entry_price  # Locked in profit
        assert position.trailing_stop_activated == True
    
    def test_short_position_atr_stop_basic(self):
        """Test basic ATR Chandelier stop for short position"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='short',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=51500.0,
            take_profit=47000.0
        )
        
        # Price moves down, establishing new low
        position.lowest_price = 48000.0
        atr = 800.0
        
        # Update trailing stop
        position.update_trailing_stop(
            current_price=48000.0,
            trailing_percentage=0.02,
            volatility=0.03,
            momentum=-0.01,
            atr=atr
        )
        
        # Expected: 48000 + (800 × 2.0) = 49600
        assert position.stop_loss == 49600.0
        assert position.stop_loss < position.entry_price  # Locked in profit
    
    def test_atr_stop_high_volatility(self):
        """Test ATR stop uses wider multiplier in high volatility"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        position.highest_price = 52000.0
        atr = 800.0
        
        # High volatility = 3.0x multiplier
        position.update_trailing_stop(
            current_price=52000.0,
            trailing_percentage=0.02,
            volatility=0.07,  # High volatility
            momentum=0.01,
            atr=atr
        )
        
        # Expected: 52000 - (800 × 3.0) = 49600
        assert position.stop_loss == 49600.0
    
    def test_atr_stop_low_volatility(self):
        """Test ATR stop uses tighter multiplier in low volatility"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        position.highest_price = 52000.0
        atr = 800.0
        
        # Low volatility = 1.5x multiplier
        position.update_trailing_stop(
            current_price=52000.0,
            trailing_percentage=0.02,
            volatility=0.015,  # Low volatility
            momentum=0.01,
            atr=atr
        )
        
        # Expected: 52000 - (800 × 1.5) = 50800
        assert position.stop_loss == 50800.0
    
    def test_atr_stop_tightens_with_profit(self):
        """Test ATR stop tightens as profit increases"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        # Significant profit (>10%)
        position.highest_price = 55500.0  # 11% profit
        atr = 800.0
        
        # With >10% profit, multiplier × 0.6
        position.update_trailing_stop(
            current_price=55500.0,
            trailing_percentage=0.02,
            volatility=0.03,
            momentum=0.01,
            atr=atr
        )
        
        # Expected: 55500 - (800 × 2.0 × 0.6) = 54540
        assert position.stop_loss == 54540.0
    
    def test_atr_stop_fallback_to_percentage(self):
        """Test fallback to percentage-based stop if ATR unavailable"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        position.highest_price = 52000.0
        
        # Update without ATR (should use percentage-based)
        position.update_trailing_stop(
            current_price=52000.0,
            trailing_percentage=0.02,
            volatility=0.03,
            momentum=0.01,
            atr=None  # No ATR
        )
        
        # Expected: percentage-based = 52000 × (1 - 0.02) = 50960
        # (with some adjustments from volatility/momentum)
        assert position.stop_loss > 50000.0  # Above entry
        assert position.trailing_stop_activated == True


class TestATRPartialProfitTaking:
    """Test ATR-based partial profit taking strategy"""
    
    def test_calculate_atr_profit_targets_long(self):
        """Test calculation of ATR profit targets for long position"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        atr = 800.0
        targets = position.calculate_atr_profit_targets(atr)
        
        # Check target structure
        assert '1x_atr' in targets
        assert '2x_atr' in targets
        assert '3x_atr' in targets
        
        # Check prices
        assert targets['1x_atr']['price'] == 50800.0  # 50000 + 800
        assert targets['2x_atr']['price'] == 51600.0  # 50000 + 1600
        assert targets['3x_atr']['price'] == 52400.0  # 50000 + 2400
        
        # Check scale out percentages
        assert targets['1x_atr']['scale_out_pct'] == 0.25
        assert targets['2x_atr']['scale_out_pct'] == 0.25
        assert targets['3x_atr']['scale_out_pct'] == 0.50
    
    def test_calculate_atr_profit_targets_short(self):
        """Test calculation of ATR profit targets for short position"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='short',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=51500.0,
            take_profit=47000.0
        )
        
        atr = 800.0
        targets = position.calculate_atr_profit_targets(atr)
        
        # Check prices (should be below entry for short)
        assert targets['1x_atr']['price'] == 49200.0  # 50000 - 800
        assert targets['2x_atr']['price'] == 48400.0  # 50000 - 1600
        assert targets['3x_atr']['price'] == 47600.0  # 50000 - 2400
    
    def test_check_first_atr_target_hit(self):
        """Test detection of first ATR profit target hit"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        atr = 800.0
        targets_hit = set()
        
        # Price at 1×ATR target
        should_scale, target_name, scale_pct = position.check_atr_profit_targets(
            current_price=50800.0,
            atr=atr,
            targets_hit=targets_hit
        )
        
        assert should_scale == True
        assert target_name == '1x_atr'
        assert scale_pct == 0.25
    
    def test_check_second_atr_target_hit(self):
        """Test detection of second ATR profit target hit"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        atr = 800.0
        targets_hit = {'1x_atr'}  # First target already hit
        
        # Price at 2×ATR target
        should_scale, target_name, scale_pct = position.check_atr_profit_targets(
            current_price=51600.0,
            atr=atr,
            targets_hit=targets_hit
        )
        
        assert should_scale == True
        assert target_name == '2x_atr'
        assert scale_pct == 0.25
    
    def test_no_duplicate_partial_exits(self):
        """Test that targets aren't triggered multiple times"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        atr = 800.0
        targets_hit = {'1x_atr'}  # Already hit first target
        
        # Price still at 1×ATR level
        should_scale, target_name, scale_pct = position.check_atr_profit_targets(
            current_price=50800.0,
            atr=atr,
            targets_hit=targets_hit
        )
        
        # Should not trigger again
        assert should_scale == False
        assert target_name == ''
        assert scale_pct == 0.0
    
    def test_atr_targets_tracking_in_position(self):
        """Test that Position class tracks ATR targets hit"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        # Check initial state
        assert len(position.atr_targets_hit) == 0
        
        # Simulate hitting first target
        position.atr_targets_hit.add('1x_atr')
        assert '1x_atr' in position.atr_targets_hit
        assert len(position.atr_targets_hit) == 1


class TestTimeBasedStopLoss:
    """Test time-based stop loss strategy"""
    
    def test_time_based_exit_stagnant_position(self):
        """Test closing stagnant position after max hold time"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        # Simulate 48 hours passing
        position.entry_time = datetime.now() - timedelta(hours=48)
        
        # Near breakeven (<2% movement)
        should_close, reason = position.should_close(
            current_price=50500.0,  # +1%
            max_hold_hours=48.0
        )
        
        assert should_close == True
        assert 'time_based_exit_stagnant' in reason
        assert '48' in reason  # Should mention 48 hours
    
    def test_time_based_exit_losing_position(self):
        """Test closing losing position after half max hold time"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        # Simulate 24 hours passing (half of 48)
        position.entry_time = datetime.now() - timedelta(hours=24)
        
        # In losing range (-3% to -10%)
        # With 5x leverage: -2% price = -10% ROI
        should_close, reason = position.should_close(
            current_price=49000.0,  # -2% price, -10% ROI
            max_hold_hours=48.0
        )
        
        assert should_close == True
        assert 'time_based_exit_losing' in reason
    
    def test_no_time_exit_for_profitable_position(self):
        """Test that profitable positions don't get time-exited early"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        # Simulate 48 hours passing
        position.entry_time = datetime.now() - timedelta(hours=48)
        
        # Profitable position (>2%)
        # With 5x leverage: +5% price = +25% ROI
        should_close, reason = position.should_close(
            current_price=52500.0,  # +5% price
            max_hold_hours=48.0
        )
        
        # Should not close due to time if profitable
        assert should_close == False or 'time_based' not in reason
    
    def test_no_time_exit_before_max_hours(self):
        """Test that positions aren't closed before max hold time"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        # Simulate 20 hours passing (less than 48)
        position.entry_time = datetime.now() - timedelta(hours=20)
        
        # Near breakeven
        should_close, reason = position.should_close(
            current_price=50500.0,
            max_hold_hours=48.0
        )
        
        # Should not close due to time yet
        if should_close:
            assert 'time_based' not in reason


class TestIntegratedStrategies:
    """Test integration of all strategies together"""
    
    def test_strategies_work_together(self):
        """Test that ATR stops, partial exits, and time stops coexist"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        # Update with ATR
        position.highest_price = 52000.0
        atr = 800.0
        position.update_trailing_stop(
            current_price=52000.0,
            trailing_percentage=0.02,
            volatility=0.03,
            momentum=0.01,
            atr=atr
        )
        
        # Check ATR target
        should_scale, target_name, scale_pct = position.check_atr_profit_targets(
            current_price=51600.0,
            atr=atr,
            targets_hit=set()
        )
        
        # Check time-based exit
        position.entry_time = datetime.now() - timedelta(hours=50)
        should_close, reason = position.should_close(
            current_price=50200.0,  # Near entry
            max_hold_hours=48.0
        )
        
        # All strategies should work
        assert position.stop_loss > 50000.0  # ATR stop in profit
        assert should_scale == True  # Partial exit available
        assert should_close == True  # Time-based exit triggered
    
    def test_emergency_stops_override_all(self):
        """Test that emergency stops override all other strategies"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        # Severe loss scenario
        # -10% price × 5x leverage = -50% ROI (but capped at -40%)
        should_close, reason = position.should_close(
            current_price=45000.0,  # -10% price
            max_hold_hours=48.0
        )
        
        assert should_close == True
        assert 'emergency_stop' in reason
    
    def test_priority_order_emergency_then_time(self):
        """Test that emergency stops are checked before time-based"""
        position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=5,
            stop_loss=48500.0,
            take_profit=53000.0
        )
        
        # Both conditions met: severe loss + time
        position.entry_time = datetime.now() - timedelta(hours=50)
        
        should_close, reason = position.should_close(
            current_price=45000.0,  # Severe loss
            max_hold_hours=48.0  # Time exceeded
        )
        
        # Emergency stop should take priority
        assert should_close == True
        assert 'emergency_stop' in reason
        assert 'time_based' not in reason


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
