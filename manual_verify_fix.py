"""
Manual verification test - simulates real-world scenario where bot tries to close already-closed position
"""
from unittest.mock import Mock, patch
from datetime import datetime

print("=" * 70)
print("MANUAL VERIFICATION: Already-Closed Position Handling")
print("=" * 70)

# Mock the logger before importing modules
with patch('logger.Logger.get_logger'), \
     patch('logger.Logger.get_position_logger'), \
     patch('logger.Logger.get_orders_logger'):
    from position_manager import PositionManager, Position

# Create a mock KuCoin client
mock_client = Mock()

# Create position manager
pm = PositionManager(client=mock_client, trailing_stop_percentage=0.02)

# Scenario 1: Position exists locally but not on exchange (already closed externally)
print("\n" + "="*70)
print("SCENARIO 1: Position closed externally (manual close/liquidation)")
print("="*70)

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

# Add to local tracking
pm.positions[symbol] = position
print(f"✓ Position added to local tracking: {symbol}")
print(f"  Entry: $50,000, Amount: 0.01, Leverage: 10x")

# Simulate: Position already closed on exchange
mock_client.get_open_positions = Mock(return_value=[])
print(f"✓ Exchange returns: No open positions (already closed)")

# Try to close the position
print(f"\nAttempting to close position...")
result = pm.close_position(symbol, 'test_scenario')

if result is None:
    print(f"✅ SUCCESS: close_position returned None (position already closed)")
else:
    print(f"❌ FAIL: close_position should return None but returned: {result}")

if symbol not in pm.positions:
    print(f"✅ SUCCESS: Position removed from local tracking")
else:
    print(f"❌ FAIL: Position still in local tracking")

if not mock_client.close_position.called:
    print(f"✅ SUCCESS: client.close_position NOT called (avoided unnecessary API call)")
else:
    print(f"❌ FAIL: client.close_position was called unnecessarily")

# Scenario 2: Try to close the same position again (double close)
print("\n" + "="*70)
print("SCENARIO 2: Attempt to close already-closed position again")
print("="*70)

result2 = pm.close_position(symbol, 'test_scenario_2')

if result2 is None:
    print(f"✅ SUCCESS: Second close attempt returned None (position not in tracking)")
else:
    print(f"❌ FAIL: Second close should return None but returned: {result2}")

# Scenario 3: Normal close (position exists on both sides)
print("\n" + "="*70)
print("SCENARIO 3: Normal position close (position exists on exchange)")
print("="*70)

symbol2 = 'ETH/USDT:USDT'
position2 = Position(
    symbol=symbol2,
    side='long',
    entry_price=3000.0,
    amount=0.1,
    leverage=5,
    stop_loss=2900.0,
    take_profit=3200.0
)

pm.positions[symbol2] = position2
print(f"✓ Position added: {symbol2}")

# Simulate: Position exists on exchange
mock_client.get_open_positions = Mock(return_value=[{
    'symbol': symbol2,
    'side': 'long',
    'contracts': 0.1,
    'leverage': 5
}])
print(f"✓ Exchange returns: Position exists")

# Mock ticker and close operation
mock_client.get_ticker = Mock(return_value={'last': 3100.0})
mock_client.close_position = Mock(return_value=True)
print(f"✓ Current price: $3,100 (profitable)")

# Try to close
print(f"\nAttempting to close position...")
result3 = pm.close_position(symbol2, 'normal_close')

if result3 is not None:
    print(f"✅ SUCCESS: close_position returned P/L value: {result3:.4f}")
else:
    print(f"❌ FAIL: Normal close should return P/L but returned None")

if symbol2 not in pm.positions:
    print(f"✅ SUCCESS: Position removed from local tracking")
else:
    print(f"❌ FAIL: Position still in local tracking after close")

if mock_client.close_position.called:
    print(f"✅ SUCCESS: client.close_position WAS called (correct for normal close)")
else:
    print(f"❌ FAIL: client.close_position should be called for normal close")

print("\n" + "="*70)
print("VERIFICATION COMPLETE")
print("="*70)
print("\nSummary:")
print("  - Bot correctly detects already-closed positions")
print("  - Avoids unnecessary API calls when position doesn't exist")
print("  - Handles double-close attempts gracefully")
print("  - Normal close operations still work correctly")
print("="*70)
