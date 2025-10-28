#!/usr/bin/env python3
"""
Manual verification script for position cleanup fix.

This script simulates scenarios where positions become orphaned
in local tracking but don't exist on the exchange.
"""
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

print("=" * 70)
print("Position Manager Cleanup Verification")
print("=" * 70)
print()

# Mock the logger before importing modules
with patch('logger.Logger.get_logger'), \
     patch('logger.Logger.get_position_logger'), \
     patch('logger.Logger.get_orders_logger'):
    from position_manager import PositionManager, Position

def scenario_1():
    """Scenario 1: Position exists locally but was closed externally"""
    print("Scenario 1: Position closed externally")
    print("-" * 70)
    
    # Setup
    mock_client = Mock()
    pm = PositionManager(client=mock_client, trailing_stop_percentage=0.02)
    
    # Add position to local tracking
    symbol = 'BTC/USDT:USDT'
    position = Position(
        symbol=symbol,
        side='long',
        entry_price=50000.0,
        amount=0.01,
        leverage=10,
        stop_loss=49000.0,
        take_profit=52000.0
    )
    pm.positions[symbol] = position
    
    print(f"✓ Local tracking has 1 position: {symbol}")
    print(f"  Position count before update: {len(pm.positions)}")
    
    # Mock: Position doesn't exist on exchange (closed externally)
    mock_client.get_open_positions = Mock(return_value=[])
    print(f"✓ Exchange returns: No open positions (closed externally)")
    
    # Update positions (should clean up the orphaned position)
    list(pm.update_positions())
    
    print(f"  Position count after update: {len(pm.positions)}")
    
    if len(pm.positions) == 0:
        print("✅ SUCCESS: Orphaned position was removed from tracking")
        return True
    else:
        print("❌ FAILURE: Position still in tracking")
        return False

def scenario_2():
    """Scenario 2: Multiple positions, some closed externally"""
    print("\nScenario 2: Multiple positions, some closed externally")
    print("-" * 70)
    
    # Setup
    mock_client = Mock()
    pm = PositionManager(client=mock_client, trailing_stop_percentage=0.02)
    
    # Add 3 positions to local tracking
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
    for symbol in symbols:
        position = Position(
            symbol=symbol,
            side='long',
            entry_price=50000.0,
            amount=0.01,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        pm.positions[symbol] = position
    
    print(f"✓ Local tracking has {len(pm.positions)} positions: {', '.join(symbols)}")
    print(f"  Position count before update: {len(pm.positions)}")
    
    # Mock: Only BTC position exists on exchange
    mock_client.get_open_positions = Mock(return_value=[{
        'symbol': 'BTC/USDT:USDT',
        'side': 'long',
        'contracts': 0.01,
        'leverage': 10
    }])
    mock_client.get_ticker = Mock(return_value={'last': 51000.0})
    mock_client.get_ohlcv = Mock(return_value=[])
    
    print(f"✓ Exchange returns: 1 open position (BTC/USDT:USDT)")
    
    # Update positions
    list(pm.update_positions())
    
    print(f"  Position count after update: {len(pm.positions)}")
    print(f"  Remaining positions: {list(pm.positions.keys())}")
    
    if len(pm.positions) == 1 and 'BTC/USDT:USDT' in pm.positions:
        print("✅ SUCCESS: Only BTC position remains, others were cleaned up")
        return True
    else:
        print("❌ FAILURE: Incorrect positions remain")
        return False

def scenario_3():
    """Scenario 3: All positions exist on exchange"""
    print("\nScenario 3: All positions exist on exchange")
    print("-" * 70)
    
    # Setup
    mock_client = Mock()
    pm = PositionManager(client=mock_client, trailing_stop_percentage=0.02)
    
    # Add 2 positions
    symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT']
    for symbol in symbols:
        position = Position(
            symbol=symbol,
            side='long',
            entry_price=50000.0,
            amount=0.01,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        pm.positions[symbol] = position
    
    print(f"✓ Local tracking has {len(pm.positions)} positions: {', '.join(symbols)}")
    
    # Mock: Both positions exist on exchange
    mock_client.get_open_positions = Mock(return_value=[
        {'symbol': 'BTC/USDT:USDT', 'side': 'long', 'contracts': 0.01, 'leverage': 10},
        {'symbol': 'ETH/USDT:USDT', 'side': 'long', 'contracts': 0.01, 'leverage': 10}
    ])
    mock_client.get_ticker = Mock(return_value={'last': 51000.0})
    mock_client.get_ohlcv = Mock(return_value=[])
    
    print(f"✓ Exchange returns: {len(mock_client.get_open_positions())} open positions")
    
    # Update positions
    list(pm.update_positions())
    
    print(f"  Position count after update: {len(pm.positions)}")
    
    if len(pm.positions) == 2:
        print("✅ SUCCESS: Both positions remain (no cleanup needed)")
        return True
    else:
        print("❌ FAILURE: Positions were incorrectly removed")
        return False

# Run scenarios
results = []
results.append(scenario_1())
results.append(scenario_2())
results.append(scenario_3())

# Summary
print("\n" + "=" * 70)
print("Summary")
print("=" * 70)
passed = sum(results)
total = len(results)

if passed == total:
    print(f"✅ All {total} scenarios passed!")
    print("The position manager cleanup fix is working correctly.")
else:
    print(f"❌ {total - passed} scenario(s) failed out of {total}")
    print("The fix needs adjustment.")

print("=" * 70)
