"""
Test position sync functionality
"""
import sys
from unittest.mock import Mock, MagicMock

# Add parent directory to path

from position_manager import PositionManager, Position
from logger import Logger

def test_sync_existing_positions():
    """Test syncing existing positions from exchange"""
    print("Testing position sync from exchange...")
    
    try:
        # Setup logger
        Logger.setup('INFO', 'logs/test.log')
        
        # Create mock client
        mock_client = Mock()
        
        # Mock exchange positions
        mock_positions = [
            {
                'symbol': 'BTC/USDT:USDT',
                'contracts': 0.5,
                'side': 'long',
                'entryPrice': 50000.0,
                'leverage': 10
            },
            {
                'symbol': 'ETH/USDT:USDT',
                'contracts': -2.0,  # negative means short
                'side': 'short',
                'entryPrice': 3000.0,
                'leverage': 8
            }
        ]
        
        mock_client.get_open_positions.return_value = mock_positions
        
        # Mock ticker data for current prices
        def mock_get_ticker(symbol):
            if symbol == 'BTC/USDT:USDT':
                return {'last': 51000.0}  # BTC is up (profitable long)
            elif symbol == 'ETH/USDT:USDT':
                return {'last': 2950.0}  # ETH is down (profitable short)
            return None
        
        mock_client.get_ticker.side_effect = mock_get_ticker
        
        # Create position manager
        manager = PositionManager(mock_client, trailing_stop_percentage=0.02)
        
        # Sync positions
        synced_count = manager.sync_existing_positions()
        
        # Verify results
        assert synced_count == 2, f"Expected to sync 2 positions, got {synced_count}"
        assert len(manager.positions) == 2, f"Expected 2 positions tracked, got {len(manager.positions)}"
        
        # Check BTC position
        assert 'BTC/USDT:USDT' in manager.positions
        btc_pos = manager.positions['BTC/USDT:USDT']
        assert btc_pos.side == 'long'
        assert btc_pos.entry_price == 50000.0
        assert btc_pos.amount == 0.5
        assert btc_pos.leverage == 10
        assert btc_pos.highest_price == 51000.0, "Highest price should be set to current price for profitable position"
        
        # Calculate P/L
        btc_pnl = btc_pos.get_pnl(51000.0)
        assert btc_pnl > 0, "BTC position should be profitable"
        
        # Check ETH position
        assert 'ETH/USDT:USDT' in manager.positions
        eth_pos = manager.positions['ETH/USDT:USDT']
        assert eth_pos.side == 'short'
        assert eth_pos.entry_price == 3000.0
        assert eth_pos.amount == 2.0  # Should be absolute value
        assert eth_pos.leverage == 8
        assert eth_pos.lowest_price == 2950.0, "Lowest price should be set to current price for profitable position"
        
        # Calculate P/L
        eth_pnl = eth_pos.get_pnl(2950.0)
        assert eth_pnl > 0, "ETH position should be profitable"
        
        print(f"  ✓ Successfully synced {synced_count} positions")
        print(f"  ✓ BTC position: {btc_pos.side} @ {btc_pos.entry_price}, P/L: {btc_pnl:.2%}")
        print(f"  ✓ ETH position: {eth_pos.side} @ {eth_pos.entry_price}, P/L: {eth_pnl:.2%}")
        print("✓ Position sync working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Position sync test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sync_no_duplicate():
    """Test that sync doesn't duplicate already tracked positions"""
    print("\nTesting sync doesn't create duplicates...")
    
    try:
        # Create mock client
        mock_client = Mock()
        
        # Mock exchange positions
        mock_positions = [
            {
                'symbol': 'BTC/USDT:USDT',
                'contracts': 0.5,
                'side': 'long',
                'entryPrice': 50000.0,
                'leverage': 10
            }
        ]
        
        mock_client.get_open_positions.return_value = mock_positions
        mock_client.get_ticker.return_value = {'last': 51000.0}
        
        # Create position manager
        manager = PositionManager(mock_client, trailing_stop_percentage=0.02)
        
        # Manually add a position (simulating bot-opened position)
        manager.positions['BTC/USDT:USDT'] = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.5,
            leverage=10,
            stop_loss=47500.0,
            take_profit=55000.0
        )
        
        # Try to sync - should not duplicate
        synced_count = manager.sync_existing_positions()
        
        # Verify results
        assert synced_count == 0, f"Should not sync already tracked position, but synced {synced_count}"
        assert len(manager.positions) == 1, f"Should still have 1 position, got {len(manager.positions)}"
        
        print("  ✓ Sync correctly skips already tracked positions")
        print("✓ No duplicate positions created")
        return True
        
    except Exception as e:
        print(f"✗ Duplicate test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sync_empty_positions():
    """Test sync with no existing positions"""
    print("\nTesting sync with no existing positions...")
    
    try:
        # Create mock client
        mock_client = Mock()
        mock_client.get_open_positions.return_value = []
        
        # Create position manager
        manager = PositionManager(mock_client, trailing_stop_percentage=0.02)
        
        # Sync positions
        synced_count = manager.sync_existing_positions()
        
        # Verify results
        assert synced_count == 0, f"Expected 0 synced positions, got {synced_count}"
        assert len(manager.positions) == 0, f"Should have no positions, got {len(manager.positions)}"
        
        print("  ✓ Correctly handles empty position list")
        print("✓ No positions synced")
        return True
        
    except Exception as e:
        print(f"✗ Empty positions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all position sync tests"""
    print("="*60)
    print("Testing Position Sync Functionality")
    print("="*60)
    
    tests = [
        test_sync_existing_positions,
        test_sync_no_duplicate,
        test_sync_empty_positions
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*60)
    
    if all(results):
        print("\n✓ All position sync tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
