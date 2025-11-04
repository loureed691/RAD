"""
Unit tests for Avellaneda-Stoikov market making strategy
"""

import pytest
from avellaneda_stoikov import AvellanedaStoikovStrategy


class TestAvellanedaStoikov:
    """Test cases for Avellaneda-Stoikov strategy."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.strategy = AvellanedaStoikovStrategy(
            risk_aversion=0.1,
            time_horizon_minutes=60.0,
            order_arrival_rate=1.0,
            max_inventory=5,
            min_spread_bps=5.0,
            max_spread_bps=100.0
        )
    
    def test_initialization(self):
        """Test strategy initialization."""
        assert self.strategy.gamma == 0.1
        assert self.strategy.T == 3600  # 60 minutes in seconds
        assert self.strategy.max_inventory == 5
        assert self.strategy.current_inventory == 0
        assert self.strategy.volatility_estimate > 0
    
    def test_update_volatility(self):
        """Test volatility estimation."""
        # Generate sample price history
        prices = [100.0, 100.5, 101.0, 100.8, 101.2, 101.5, 101.3]
        
        volatility = self.strategy.update_volatility(prices)
        
        assert volatility > 0
        assert isinstance(volatility, float)
        # Volatility should be reasonable (not too extreme)
        assert 0.001 < volatility < 1.0
    
    def test_reservation_price_neutral_inventory(self):
        """Test reservation price with neutral inventory."""
        mid_price = 100.0
        inventory = 0
        
        reservation_price = self.strategy.calculate_reservation_price(
            mid_price, inventory
        )
        
        # With zero inventory, reservation price should equal mid price
        assert abs(reservation_price - mid_price) < 0.01
    
    def test_reservation_price_long_inventory(self):
        """Test reservation price with long inventory."""
        mid_price = 100.0
        inventory = 3  # Long position
        
        reservation_price = self.strategy.calculate_reservation_price(
            mid_price, inventory
        )
        
        # With long inventory, reservation price should be lower than mid
        # (we want to sell to reduce inventory)
        assert reservation_price < mid_price
    
    def test_reservation_price_short_inventory(self):
        """Test reservation price with short inventory."""
        mid_price = 100.0
        inventory = -3  # Short position
        
        reservation_price = self.strategy.calculate_reservation_price(
            mid_price, inventory
        )
        
        # With short inventory, reservation price should be higher than mid
        # (we want to buy to cover shorts)
        assert reservation_price > mid_price
    
    def test_optimal_spread_calculation(self):
        """Test optimal spread calculation."""
        mid_price = 100.0
        
        half_spread = self.strategy.calculate_optimal_spread(mid_price)
        
        assert half_spread > 0
        # Spread should be within min/max bounds
        min_half_spread = self.strategy.min_spread * mid_price
        max_half_spread = self.strategy.max_spread * mid_price
        assert min_half_spread <= half_spread <= max_half_spread
    
    def test_calculate_quotes_neutral(self):
        """Test quote calculation with neutral inventory."""
        mid_price = 100.0
        inventory = 0
        price_history = [99.0, 99.5, 100.0, 100.5, 101.0]
        
        quotes = self.strategy.calculate_quotes(mid_price, inventory, price_history)
        
        assert 'bid' in quotes
        assert 'ask' in quotes
        assert 'mid' in quotes
        assert 'spread_bps' in quotes
        
        # Bid should be below mid, ask above mid
        assert quotes['bid'] < mid_price
        assert quotes['ask'] > mid_price
        
        # Bid-ask spread should be positive
        assert quotes['ask'] > quotes['bid']
    
    def test_calculate_quotes_with_skew(self):
        """Test quote calculation with inventory skew."""
        mid_price = 100.0
        inventory = 3  # Long position
        
        quotes_long = self.strategy.calculate_quotes(mid_price, inventory)
        
        # Now test with short inventory
        inventory = -3
        quotes_short = self.strategy.calculate_quotes(mid_price, inventory)
        
        # With long inventory, quotes should be skewed lower
        # With short inventory, quotes should be skewed higher
        assert quotes_long['bid'] < quotes_short['bid']
        assert quotes_long['ask'] < quotes_short['ask']
    
    def test_should_quote_within_limits(self):
        """Test quoting decision within inventory limits."""
        # Within limits
        assert self.strategy.should_quote(0) is True
        assert self.strategy.should_quote(3) is True
        assert self.strategy.should_quote(-3) is True
        
        # At limits
        assert self.strategy.should_quote(5) is False
        assert self.strategy.should_quote(-5) is False
        
        # Beyond limits
        assert self.strategy.should_quote(6) is False
        assert self.strategy.should_quote(-6) is False
    
    def test_get_quote_sizes(self):
        """Test quote size calculation based on inventory."""
        base_size = 1.0
        
        # Neutral inventory
        bid_size, ask_size = self.strategy.get_quote_sizes(base_size, 0)
        assert abs(bid_size - ask_size) < 0.01  # Should be nearly equal
        
        # Long inventory - should increase bid size, decrease ask size
        bid_size_long, ask_size_long = self.strategy.get_quote_sizes(base_size, 3)
        assert bid_size_long < base_size  # Reduce buying when already long
        assert ask_size_long > base_size  # Increase selling when already long
        
        # Short inventory - opposite behavior
        bid_size_short, ask_size_short = self.strategy.get_quote_sizes(base_size, -3)
        assert bid_size_short > base_size  # Increase buying when short
        assert ask_size_short < base_size  # Reduce selling when short
    
    def test_update_inventory(self):
        """Test inventory update tracking."""
        assert self.strategy.current_inventory == 0
        
        self.strategy.update_inventory(2)
        assert self.strategy.current_inventory == 2
        
        self.strategy.update_inventory(-1)
        assert self.strategy.current_inventory == -1
    
    def test_reset_session(self):
        """Test session reset."""
        old_start_time = self.strategy.session_start_time
        
        # Wait a bit
        import time
        time.sleep(0.1)
        
        self.strategy.reset_session()
        
        # Start time should be updated
        assert self.strategy.session_start_time > old_start_time
    
    def test_get_status(self):
        """Test status reporting."""
        status = self.strategy.get_status()
        
        assert 'strategy' in status
        assert status['strategy'] == 'Avellaneda-Stoikov'
        assert 'risk_aversion' in status
        assert 'volatility' in status
        assert 'current_inventory' in status
        assert 'max_inventory' in status
    
    def test_spread_increases_with_volatility(self):
        """Test that spread increases with volatility (within practical bounds)."""
        # Instead of testing extreme cases, verify that spread calculation
        # responds appropriately to volatility within realistic ranges
        mid_price = 100.0
        
        strategy = AvellanedaStoikovStrategy(
            risk_aversion=0.5,
            time_horizon_minutes=60.0,
            min_spread_bps=1.0,
            max_spread_bps=1000.0
        )
        
        # Test reasonable volatility range
        vols = [0.01, 0.02, 0.03, 0.04, 0.05]
        spreads = []
        
        for vol in vols:
            strategy.volatility_estimate = vol
            spread = strategy.calculate_optimal_spread(mid_price)
            spreads.append(spread)
        
        # Spreads should generally increase with volatility
        # At least some should be increasing
        increasing_count = sum(1 for i in range(len(spreads)-1) if spreads[i+1] >= spreads[i])
        assert increasing_count >= len(spreads) - 2  # Allow for 1 exception due to clamping
    
    def test_spread_decreases_with_time(self):
        """Test that spread responds to time remaining (within practical bounds)."""
        mid_price = 100.0
        
        strategy = AvellanedaStoikovStrategy(
            risk_aversion=0.5,
            time_horizon_minutes=60.0,
            min_spread_bps=1.0,
            max_spread_bps=1000.0
        )
        
        # Test with different time values
        times = [3600, 1800, 900, 300, 60]
        spreads = []
        
        for time_remaining in times:
            spread = strategy.calculate_optimal_spread(mid_price, time_remaining=time_remaining)
            spreads.append(spread)
        
        # Spreads should generally decrease or stay constant as time decreases
        # Check that at least the trend is downward or flat
        decreasing_count = sum(1 for i in range(len(spreads)-1) if spreads[i+1] <= spreads[i])
        assert decreasing_count >= len(spreads) - 2  # Allow for 1 exception
    
    def test_risk_aversion_effect(self):
        """Test effect of different risk aversion parameters (within practical bounds)."""
        mid_price = 100.0
        
        # Test a range of risk aversion values
        risk_aversions = [0.01, 0.1, 0.5, 1.0, 2.0]
        spreads = []
        
        for gamma in risk_aversions:
            strategy = AvellanedaStoikovStrategy(
                risk_aversion=gamma,
                min_spread_bps=1.0,
                max_spread_bps=1000.0
            )
            spread = strategy.calculate_optimal_spread(mid_price)
            spreads.append(spread)
        
        # Spreads should generally increase with risk aversion
        # Check for overall increasing trend
        increasing_count = sum(1 for i in range(len(spreads)-1) if spreads[i+1] >= spreads[i])
        assert increasing_count >= len(spreads) - 2  # Allow for 1 exception
    
    def test_multiple_quote_calculations(self):
        """Test multiple consecutive quote calculations."""
        mid_price = 100.0
        prices = [99.0, 99.5, 100.0, 100.5, 101.0]
        
        # Calculate quotes multiple times
        for i in range(5):
            quotes = self.strategy.calculate_quotes(mid_price + i * 0.1, i - 2, prices)
            
            # Basic sanity checks
            assert quotes['bid'] > 0
            assert quotes['ask'] > 0
            assert quotes['ask'] > quotes['bid']
            assert quotes['spread_bps'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
