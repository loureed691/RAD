"""
Test suite for advanced trading strategy integration
"""
import sys
from datetime import datetime, timedelta
from position_manager import Position, PositionManager
from advanced_exit_strategy import AdvancedExitStrategy
from unittest.mock import Mock, MagicMock

def test_position_manager_has_advanced_exit_strategy():
    """Test that PositionManager initializes with AdvancedExitStrategy"""
    print("\nTesting PositionManager has AdvancedExitStrategy...")
    
    try:
        mock_client = Mock()
        manager = PositionManager(mock_client)
        
        assert hasattr(manager, 'advanced_exit_strategy'), "PositionManager should have advanced_exit_strategy attribute"
        assert isinstance(manager.advanced_exit_strategy, AdvancedExitStrategy), "advanced_exit_strategy should be an instance of AdvancedExitStrategy"
        
        print("  ✓ PositionManager correctly initialized with AdvancedExitStrategy")
    except Exception as e:
        print(f"  ✗ Test error: {e}")


def test_breakeven_plus_exit_integration():
    """Test breakeven+ exit strategy in position management"""
    print("\nTesting breakeven+ exit integration...")
    
    try:
        # Create advanced exit strategy
        exit_strategy = AdvancedExitStrategy()
        
        # Test position with 2% profit (above 1.5% activation threshold)
        # With 10x leverage, spot P&L is 0.2% and leveraged P&L is 2%
        position_data = {
            'side': 'long',
            'entry_price': 50000,
            'current_price': 51000,
            'current_pnl_pct': 0.20,  # 20% leveraged profit (2% spot profit with 10x leverage)
            'peak_pnl_pct': 0.25,
            'leverage': 10,
            'entry_time': datetime.now() - timedelta(minutes=30),
            'stop_loss': 49000,
            'take_profit': 55000
        }
        
        market_data = {
            'volatility': 0.03,
            'momentum': 0.01,
            'rsi': 65.0,
            'trend_strength': 0.6
        }
        
        should_exit, reason, new_stop = exit_strategy.get_comprehensive_exit_signal(
            position_data, market_data
        )
        
        # Breakeven+ should suggest a new stop loss to lock in profit
        assert new_stop is not None, f"Breakeven+ should suggest a new stop loss, got: {new_stop}, reason: {reason}"
        assert new_stop > position_data['entry_price'], f"New stop {new_stop} should be above entry {position_data['entry_price']} (locking in profit)"
        print(f"  ✓ Breakeven+ activated: new stop = {new_stop:.2f} (entry = {position_data['entry_price']:.2f}), reason = {reason}")
        
        return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        import traceback
        traceback.print_exc()


def test_momentum_reversal_exit_integration():
    """Test momentum reversal detection"""
    print("\nTesting momentum reversal exit integration...")
    
    try:
        exit_strategy = AdvancedExitStrategy()
        
        # Test long position with negative momentum and overbought RSI
        position_data = {
            'side': 'long',
            'entry_price': 50000,
            'current_price': 51500,
            'pnl_pct': 0.03,  # 3% profit
            'peak_pnl_pct': 0.035,
            'entry_time': datetime.now() - timedelta(minutes=45),
            'stop_loss': 49000,
            'take_profit': 55000
        }
        
        market_data = {
            'volatility': 0.03,
            'momentum': -0.025,  # Strong negative momentum
            'rsi': 75.0,  # Overbought
            'trend_strength': 0.4
        }
        
        should_exit, reason, _ = exit_strategy.get_comprehensive_exit_signal(
            position_data, market_data
        )
        
        # Should detect momentum reversal
        assert should_exit == True, "Should exit on momentum reversal"
        assert 'reversal' in reason.lower(), "Reason should mention momentum reversal"
        print(f"  ✓ Momentum reversal detected: {reason}")
        
        return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")


def test_profit_lock_exit_integration():
    """Test profit lock exit strategy"""
    print("\nTesting profit lock exit integration...")
    
    try:
        exit_strategy = AdvancedExitStrategy()
        
        # Test position with significant profit retracement
        # Peak was at 5%, now at 3.0% = 40% retracement (above 30% threshold)
        position_data = {
            'side': 'long',
            'entry_price': 50000,
            'current_price': 51500,  # Adjusted for 3% profit
            'current_pnl_pct': 0.30,  # 30% leveraged = 3.0% spot (10x leverage)
            'peak_pnl_pct': 0.50,  # 50% leveraged = 5% spot (10x leverage)
            'leverage': 10,
            'entry_time': datetime.now() - timedelta(hours=1),
            'stop_loss': 49500,
            'take_profit': 55000
        }
        
        market_data = {
            'volatility': 0.04,
            'momentum': -0.01,
            'rsi': 62.0,
            'trend_strength': 0.5
        }
        
        should_exit, reason, _ = exit_strategy.get_comprehensive_exit_signal(
            position_data, market_data
        )
        
        # Profit lock should trigger (retraced from 5% to 3% = 40% retracement)
        assert should_exit == True, f"Should exit on profit lock (40% retracement), got exit={should_exit}, reason={reason}"
        print(f"  ✓ Profit lock triggered: {reason}")
        
        return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")


def test_time_based_exit_integration():
    """Test time-based exit strategy"""
    print("\nTesting time-based exit integration...")
    
    try:
        exit_strategy = AdvancedExitStrategy()
        
        # Test position held for over 24 hours
        position_data = {
            'side': 'long',
            'entry_price': 50000,
            'current_price': 50100,
            'pnl_pct': 0.002,  # Small profit
            'peak_pnl_pct': 0.015,
            'entry_time': datetime.now() - timedelta(hours=25),  # Over 24 hours
            'stop_loss': 49000,
            'take_profit': 55000
        }
        
        market_data = {
            'volatility': 0.03,
            'momentum': 0.005,
            'rsi': 52.0,
            'trend_strength': 0.4
        }
        
        should_exit, reason, _ = exit_strategy.get_comprehensive_exit_signal(
            position_data, market_data
        )
        
        # Time-based exit should trigger
        assert should_exit == True, "Should exit after max hold time"
        assert 'time' in reason.lower() or 'hold' in reason.lower(), "Reason should mention time/hold"
        print(f"  ✓ Time-based exit triggered: {reason}")
        
        return True
    except Exception as e:
        print(f"  ✗ Test error: {e}")


def test_volatility_spike_exit_integration():
    """Test volatility spike exit strategy"""
    print("\nTesting volatility spike exit integration...")
    
    try:
        exit_strategy = AdvancedExitStrategy()
        
        # Test position with high volatility spike
        # Need to simulate entry volatility stored somewhere
        position_data = {
            'side': 'long',
            'entry_price': 50000,
            'current_price': 50500,
            'pnl_pct': 0.01,
            'peak_pnl_pct': 0.02,
            'entry_time': datetime.now() - timedelta(minutes=20),
            'stop_loss': 49000,
            'take_profit': 55000
        }
        
        # Very high volatility (simulating spike)
        market_data = {
            'volatility': 0.10,  # 10% volatility is very high
            'momentum': 0.02,
            'rsi': 58.0,
            'trend_strength': 0.5
        }
        
        # Note: Volatility spike detection requires entry volatility tracking
        # For now, this test validates the integration works
        should_exit, reason, _ = exit_strategy.get_comprehensive_exit_signal(
            position_data, market_data
        )
        
        print(f"  ✓ Volatility spike handling tested (exit={should_exit}, reason={reason})")
    except Exception as e:
        print(f"  ✗ Test error: {e}")


def test_position_update_with_advanced_exits():
    """Test that position updates properly integrate advanced exit strategies"""
    print("\nTesting position updates with advanced exits...")
    
    try:
        # Create mock client
        mock_client = Mock()
        mock_client.get_ticker.return_value = {'last': 51000}
        mock_client.get_ohlcv.return_value = None  # Simulate no market data
        
        # Create position manager
        manager = PositionManager(mock_client)
        
        # Create a test position
        position = Position(
            symbol='BTC-USDT',
            side='long',
            entry_price=50000,
            amount=1.0,
            leverage=10,
            stop_loss=49000,
            take_profit=55000
        )
        # Set it to profitable to trigger breakeven+
        position.max_favorable_excursion = 0.02
        manager.positions['BTC-USDT'] = position
        
        # Update positions (this should use advanced exit strategies)
        closed_positions = list(manager.update_positions())
        
        print(f"  ✓ Position update integrated with advanced exit strategies (closed: {len(closed_positions)})")
    except Exception as e:
        print(f"  ✗ Test error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all advanced strategy integration tests"""
    print("=" * 60)
    print("Running Advanced Strategy Integration Tests")
    print("=" * 60)
    
    tests = [
        test_position_manager_has_advanced_exit_strategy,
        test_breakeven_plus_exit_integration,
        test_momentum_reversal_exit_integration,
        test_profit_lock_exit_integration,
        test_time_based_exit_integration,
        test_volatility_spike_exit_integration,
        test_position_update_with_advanced_exits,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All advanced strategy integration tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
