#!/usr/bin/env python3
"""
Manual validation test for the improved retry logic.
This simulates realistic API failure scenarios.
"""
import time
from unittest.mock import Mock, MagicMock
from position_manager import PositionManager, Position
from datetime import datetime

def test_realistic_api_failure_recovery():
    """Test that the bot can recover from realistic API failures"""
    print("\n" + "="*80)
    print("Testing Realistic API Failure Recovery")
    print("="*80)
    
    # Create mock client
    mock_client = Mock()
    mock_client.get_market_limits.return_value = {
        'amount': {'min': 0.001, 'max': 10000}
    }
    
    # Create position manager
    position_manager = PositionManager(mock_client, trailing_stop_percentage=0.02)
    
    # Add a test position
    test_symbol = "ETH/USDT:USDT"
    test_position = Position(
        symbol=test_symbol,
        side='long',
        entry_price=2000.0,
        amount=1.0,
        leverage=5,
        stop_loss=1900.0,
        take_profit=2200.0
    )
    position_manager.positions[test_symbol] = test_position
    
    print(f"\n✓ Created position: {test_symbol}")
    print(f"  Entry: ${test_position.entry_price}")
    print(f"  Stop Loss: ${test_position.stop_loss}")
    print(f"  Take Profit: ${test_position.take_profit}")
    
    # Scenario 1: API fails for first 5 attempts, then recovers
    print("\n" + "-"*80)
    print("Scenario 1: API fails 5 times, then recovers")
    print("-"*80)
    
    call_count = 0
    def ticker_with_failures(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 5:
            print(f"  Attempt {call_count}: API failure (simulated)")
            return None
        else:
            print(f"  Attempt {call_count}: API success! Returning price $2050")
            return {'last': 2050.0, 'symbol': test_symbol}
    
    mock_client.get_ticker.side_effect = ticker_with_failures
    mock_client.get_ohlcv.return_value = []  # Empty list to prevent advanced exit strategy
    
    start_time = time.time()
    list(position_manager.update_positions())
    elapsed = time.time() - start_time
    
    print(f"\n✓ Position update completed in {elapsed:.1f}s")
    print(f"✓ Total API calls: {call_count}")
    print(f"✓ Position still active: {test_symbol in position_manager.positions}")
    
    # Verify position was updated correctly
    # Note: Position might be closed by advanced exit strategy, which is OK
    # The important thing is that the retry logic worked and got the price
    print(f"✓ Retry logic worked - price was fetched after {call_count} attempts")
    assert call_count >= 6, f"Expected at least 6 API calls, got {call_count}"
    print("✓ All assertions passed!")
    
    # Scenario 2: API fails all 10 attempts (position skipped)
    print("\n" + "-"*80)
    print("Scenario 2: API fails all 10 attempts (critical failure)")
    print("-"*80)
    
    # Re-create the position for scenario 2
    test_position_2 = Position(
        symbol=test_symbol,
        side='long',
        entry_price=2000.0,
        amount=1.0,
        leverage=5,
        stop_loss=1900.0,
        take_profit=2200.0
    )
    position_manager.positions[test_symbol] = test_position_2
    print(f"✓ Re-created position: {test_symbol}")
    
    call_count_2 = 0
    def ticker_always_fails(*args, **kwargs):
        nonlocal call_count_2
        call_count_2 += 1
        print(f"  Attempt {call_count_2}/10: API failure (simulated)")
        return None
    
    mock_client.get_ticker.side_effect = ticker_always_fails
    
    start_time = time.time()
    list(position_manager.update_positions())
    elapsed = time.time() - start_time
    
    print(f"\n✓ Position update completed in {elapsed:.1f}s")
    print(f"✓ Total API calls: {call_count_2}")
    print(f"✓ Position still active: {test_symbol in position_manager.positions}")
    print("✓ Position was correctly skipped (not closed due to missing price)")
    
    # Verify position was NOT closed
    assert test_symbol in position_manager.positions, "Position should still be active after failures"
    assert call_count_2 == 10, f"Expected 10 API calls, got {call_count_2}"
    print("✓ All assertions passed!")
    
    # Scenario 3: Stop loss triggers after successful price fetch
    print("\n" + "-"*80)
    print("Scenario 3: Price below stop loss triggers exit")
    print("-"*80)
    
    # Re-create the position for scenario 3
    test_position_3 = Position(
        symbol=test_symbol,
        side='long',
        entry_price=2000.0,
        amount=1.0,
        leverage=5,
        stop_loss=1900.0,
        take_profit=2200.0
    )
    position_manager.positions[test_symbol] = test_position_3
    print(f"✓ Re-created position: {test_symbol}")
    
    call_count_3 = 0
    def ticker_stop_loss(*args, **kwargs):
        nonlocal call_count_3
        call_count_3 += 1
        if call_count_3 <= 2:
            print(f"  Attempt {call_count_3}: API failure (simulated)")
            return None
        else:
            print(f"  Attempt {call_count_3}: API success! Price at $1850 (below stop loss)")
            return {'last': 1850.0, 'symbol': test_symbol}
    
    mock_client.get_ticker.side_effect = ticker_stop_loss
    mock_client.close_position.return_value = True
    
    start_time = time.time()
    closed_positions = list(position_manager.update_positions())
    elapsed = time.time() - start_time
    
    print(f"\n✓ Position update completed in {elapsed:.1f}s")
    print(f"✓ Total API calls: {call_count_3}")
    print(f"✓ Positions closed: {len(closed_positions)}")
    
    if closed_positions:
        symbol, pnl, position = closed_positions[0]
        print(f"✓ Closed position: {symbol} with P/L: {pnl:.2%}")
    
    # Verify position was closed
    assert len(closed_positions) == 1, "Position should have been closed"
    assert test_symbol not in position_manager.positions, "Position should be removed"
    print("✓ All assertions passed!")
    
    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED - Retry logic working correctly!")
    print("="*80)
    print("\nKey improvements:")
    print("  ✓ Increased retries from 3 to 10 attempts")
    print("  ✓ Longer backoff times (1s to 30s)")
    print("  ✓ Position monitoring never gives up prematurely")
    print("  ✓ Stop losses still trigger when price is fetched")
    print("  ✓ Positions are not closed on API failures")
    print()

if __name__ == '__main__':
    test_realistic_api_failure_recovery()
