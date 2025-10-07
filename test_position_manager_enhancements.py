#!/usr/bin/env python3
"""
Unit tests for position manager enhancements (thread safety and validation)
"""
import sys
import time
import threading
from unittest.mock import Mock, MagicMock, patch

def test_thread_safe_operations():
    """Test thread-safe operations on position manager"""
    print("\nTesting thread-safe operations...")
    
    try:
        from position_manager import PositionManager, Position
        
        # Create mock client
        mock_client = Mock()
        pm = PositionManager(mock_client)
        
        # Test 1: Thread-safe get_open_positions_count
        print("  Test 1: Thread-safe get_open_positions_count...")
        count = pm.get_open_positions_count()
        assert count == 0, f"Expected 0, got {count}"
        print(f"    ✓ Count is {count}")
        
        # Test 2: Thread-safe has_position
        print("  Test 2: Thread-safe has_position...")
        has_pos = pm.has_position('BTC/USDT:USDT')
        assert has_pos == False, f"Expected False, got {has_pos}"
        print(f"    ✓ has_position returns {has_pos}")
        
        # Test 3: Thread-safe get_position
        print("  Test 3: Thread-safe get_position...")
        pos = pm.get_position('BTC/USDT:USDT')
        assert pos is None, f"Expected None, got {pos}"
        print(f"    ✓ get_position returns None for non-existent position")
        
        # Test 4: Thread-safe get_all_positions
        print("  Test 4: Thread-safe get_all_positions...")
        all_pos = pm.get_all_positions()
        assert isinstance(all_pos, dict), f"Expected dict, got {type(all_pos)}"
        assert len(all_pos) == 0, f"Expected 0 positions, got {len(all_pos)}"
        print(f"    ✓ get_all_positions returns empty dict")
        
        # Test 5: Add a position and verify thread-safe access
        print("  Test 5: Add position and verify thread-safe access...")
        test_position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=10,
            stop_loss=47500.0,
            take_profit=55000.0
        )
        
        # Directly add to positions (simulating position opening)
        with pm._positions_lock:
            pm.positions['BTC/USDT:USDT'] = test_position
        
        # Verify count
        count = pm.get_open_positions_count()
        assert count == 1, f"Expected 1, got {count}"
        print(f"    ✓ Count after adding position: {count}")
        
        # Verify has_position
        has_pos = pm.has_position('BTC/USDT:USDT')
        assert has_pos == True, f"Expected True, got {has_pos}"
        print(f"    ✓ has_position returns True after adding")
        
        # Verify get_position
        pos = pm.get_position('BTC/USDT:USDT')
        assert pos is not None, "Expected position, got None"
        assert pos.symbol == 'BTC/USDT:USDT', f"Expected BTC/USDT:USDT, got {pos.symbol}"
        print(f"    ✓ get_position returns correct position")
        
        # Verify get_all_positions
        all_pos = pm.get_all_positions()
        assert len(all_pos) == 1, f"Expected 1 position, got {len(all_pos)}"
        assert 'BTC/USDT:USDT' in all_pos, "Expected BTC/USDT:USDT in positions"
        print(f"    ✓ get_all_positions returns correct snapshot")
        
        print("✓ All thread-safe operation tests passed")
        return True
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_position_validation():
    """Test position parameter validation"""
    print("\nTesting position parameter validation...")
    
    try:
        from position_manager import PositionManager
        
        # Create mock client
        mock_client = Mock()
        pm = PositionManager(mock_client)
        
        # Test 1: Valid parameters
        print("  Test 1: Valid parameters...")
        valid, msg = pm.validate_position_parameters('BTC/USDT:USDT', 1.0, 10, 0.05)
        assert valid == True, f"Expected valid, got {valid}"
        assert msg == "Valid parameters", f"Expected 'Valid parameters', got '{msg}'"
        print(f"    ✓ Valid parameters accepted: {msg}")
        
        # Test 2: Invalid amount (zero)
        print("  Test 2: Invalid amount (zero)...")
        valid, msg = pm.validate_position_parameters('BTC/USDT:USDT', 0.0, 10, 0.05)
        assert valid == False, f"Expected invalid, got {valid}"
        assert "Invalid amount" in msg, f"Expected 'Invalid amount' in message, got '{msg}'"
        print(f"    ✓ Zero amount rejected: {msg}")
        
        # Test 3: Invalid amount (negative)
        print("  Test 3: Invalid amount (negative)...")
        valid, msg = pm.validate_position_parameters('BTC/USDT:USDT', -1.0, 10, 0.05)
        assert valid == False, f"Expected invalid, got {valid}"
        assert "Invalid amount" in msg, f"Expected 'Invalid amount' in message, got '{msg}'"
        print(f"    ✓ Negative amount rejected: {msg}")
        
        # Test 4: Invalid leverage (too low)
        print("  Test 4: Invalid leverage (too low)...")
        valid, msg = pm.validate_position_parameters('BTC/USDT:USDT', 1.0, 0, 0.05)
        assert valid == False, f"Expected invalid, got {valid}"
        assert "Invalid leverage" in msg, f"Expected 'Invalid leverage' in message, got '{msg}'"
        print(f"    ✓ Zero leverage rejected: {msg}")
        
        # Test 5: Invalid leverage (too high)
        print("  Test 5: Invalid leverage (too high)...")
        valid, msg = pm.validate_position_parameters('BTC/USDT:USDT', 1.0, 200, 0.05)
        assert valid == False, f"Expected invalid, got {valid}"
        assert "Invalid leverage" in msg, f"Expected 'Invalid leverage' in message, got '{msg}'"
        print(f"    ✓ Excessive leverage rejected: {msg}")
        
        # Test 6: Invalid stop loss percentage (zero)
        print("  Test 6: Invalid stop loss percentage (zero)...")
        valid, msg = pm.validate_position_parameters('BTC/USDT:USDT', 1.0, 10, 0.0)
        assert valid == False, f"Expected invalid, got {valid}"
        assert "Invalid stop loss" in msg, f"Expected 'Invalid stop loss' in message, got '{msg}'"
        print(f"    ✓ Zero stop loss rejected: {msg}")
        
        # Test 7: Invalid stop loss percentage (>= 1)
        print("  Test 7: Invalid stop loss percentage (>= 1)...")
        valid, msg = pm.validate_position_parameters('BTC/USDT:USDT', 1.0, 10, 1.0)
        assert valid == False, f"Expected invalid, got {valid}"
        assert "Invalid stop loss" in msg, f"Expected 'Invalid stop loss' in message, got '{msg}'"
        print(f"    ✓ Stop loss >= 1 rejected: {msg}")
        
        # Test 8: Position already exists
        print("  Test 8: Position already exists...")
        from position_manager import Position
        test_position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=10,
            stop_loss=47500.0,
            take_profit=55000.0
        )
        with pm._positions_lock:
            pm.positions['BTC/USDT:USDT'] = test_position
        
        valid, msg = pm.validate_position_parameters('BTC/USDT:USDT', 1.0, 10, 0.05)
        assert valid == False, f"Expected invalid, got {valid}"
        assert "already exists" in msg, f"Expected 'already exists' in message, got '{msg}'"
        print(f"    ✓ Duplicate position rejected: {msg}")
        
        print("✓ All position validation tests passed")
        return True
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_concurrent_access():
    """Test concurrent access to position manager"""
    print("\nTesting concurrent access...")
    
    try:
        from position_manager import PositionManager, Position
        
        # Create mock client
        mock_client = Mock()
        pm = PositionManager(mock_client)
        
        # Add some test positions
        for i in range(3):
            test_position = Position(
                symbol=f'TEST{i}/USDT:USDT',
                side='long',
                entry_price=100.0 + i,
                amount=1.0,
                leverage=10,
                stop_loss=95.0 + i,
                take_profit=110.0 + i
            )
            with pm._positions_lock:
                pm.positions[f'TEST{i}/USDT:USDT'] = test_position
        
        print("  Test 1: Concurrent reads...")
        results = []
        errors = []
        
        def read_positions():
            try:
                for _ in range(100):
                    count = pm.get_open_positions_count()
                    has_pos = pm.has_position('TEST0/USDT:USDT')
                    pos = pm.get_position('TEST1/USDT:USDT')
                    all_pos = pm.get_all_positions()
                    results.append((count, has_pos, pos, all_pos))
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads for concurrent reads
        threads = []
        for _ in range(5):
            t = threading.Thread(target=read_positions)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors occurred during concurrent reads: {errors}"
        assert len(results) == 500, f"Expected 500 results, got {len(results)}"
        
        # Verify all results are consistent
        for count, has_pos, pos, all_pos in results:
            assert count == 3, f"Expected count 3, got {count}"
            assert has_pos == True, f"Expected has_pos True, got {has_pos}"
            assert pos is not None, "Expected position object, got None"
            assert len(all_pos) == 3, f"Expected 3 positions, got {len(all_pos)}"
        
        print(f"    ✓ {len(results)} concurrent reads completed successfully")
        
        print("✓ All concurrent access tests passed")
        return True
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_position_reconciliation():
    """Test position reconciliation with exchange"""
    print("\nTesting position reconciliation...")
    
    try:
        from position_manager import PositionManager, Position
        
        # Create mock client
        mock_client = Mock()
        pm = PositionManager(mock_client)
        
        # Test 1: No discrepancies
        print("  Test 1: No discrepancies (empty exchange)...")
        mock_client.get_open_positions = Mock(return_value=[])
        discrepancies = pm.reconcile_positions()
        assert discrepancies == 0, f"Expected 0 discrepancies, got {discrepancies}"
        print(f"    ✓ No discrepancies found: {discrepancies}")
        
        # Test 2: Position on exchange but not tracked locally
        print("  Test 2: Position on exchange but not tracked locally...")
        mock_exchange_position = {
            'symbol': 'BTC/USDT:USDT',
            'contracts': 1.0,
            'side': 'long',
            'entryPrice': 50000.0,
            'leverage': 10
        }
        mock_client.get_open_positions = Mock(return_value=[mock_exchange_position])
        mock_client.get_ticker = Mock(return_value={'last': 51000.0})
        
        discrepancies = pm.reconcile_positions()
        assert discrepancies == 1, f"Expected 1 discrepancy, got {discrepancies}"
        
        # Verify position was added
        has_pos = pm.has_position('BTC/USDT:USDT')
        assert has_pos == True, "Expected position to be added"
        print(f"    ✓ Position reconciled and added: {discrepancies}")
        
        # Test 3: Position tracked locally but not on exchange
        print("  Test 3: Position tracked locally but not on exchange...")
        # Add a local position that doesn't exist on exchange
        orphan_position = Position(
            symbol='ETH/USDT:USDT',
            side='long',
            entry_price=3000.0,
            amount=1.0,
            leverage=10,
            stop_loss=2850.0,
            take_profit=3300.0
        )
        with pm._positions_lock:
            pm.positions['ETH/USDT:USDT'] = orphan_position
        
        # Exchange only has BTC position
        mock_client.get_open_positions = Mock(return_value=[mock_exchange_position])
        
        discrepancies = pm.reconcile_positions()
        assert discrepancies == 1, f"Expected 1 discrepancy, got {discrepancies}"
        
        # Verify orphaned position was removed
        has_pos = pm.has_position('ETH/USDT:USDT')
        assert has_pos == False, "Expected orphaned position to be removed"
        print(f"    ✓ Orphaned position removed: {discrepancies}")
        
        print("✓ All position reconciliation tests passed")
        return True
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_safe_update_targets():
    """Test safe position target updates with validation"""
    print("\nTesting safe position target updates...")
    
    try:
        from position_manager import PositionManager, Position
        
        # Create mock client
        mock_client = Mock()
        pm = PositionManager(mock_client)
        
        # Add a long position
        print("  Test 1: Long position target validation...")
        long_position = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=1.0,
            leverage=10,
            stop_loss=47500.0,
            take_profit=55000.0
        )
        with pm._positions_lock:
            pm.positions['BTC/USDT:USDT'] = long_position
        
        # Valid stop loss update (below entry)
        result = pm.safe_update_position_targets('BTC/USDT:USDT', new_stop_loss=48000.0)
        assert result == True, "Expected valid stop loss update to succeed"
        assert pm.positions['BTC/USDT:USDT'].stop_loss == 48000.0, "Stop loss not updated"
        print(f"    ✓ Valid stop loss update accepted")
        
        # Invalid stop loss update (above entry for long)
        result = pm.safe_update_position_targets('BTC/USDT:USDT', new_stop_loss=51000.0)
        assert result == False, "Expected invalid stop loss update to fail"
        assert pm.positions['BTC/USDT:USDT'].stop_loss == 48000.0, "Stop loss changed unexpectedly"
        print(f"    ✓ Invalid stop loss (above entry) rejected")
        
        # Valid take profit update (above entry)
        result = pm.safe_update_position_targets('BTC/USDT:USDT', new_take_profit=56000.0)
        assert result == True, "Expected valid take profit update to succeed"
        assert pm.positions['BTC/USDT:USDT'].take_profit == 56000.0, "Take profit not updated"
        print(f"    ✓ Valid take profit update accepted")
        
        # Invalid take profit update (below entry for long)
        result = pm.safe_update_position_targets('BTC/USDT:USDT', new_take_profit=49000.0)
        assert result == False, "Expected invalid take profit update to fail"
        assert pm.positions['BTC/USDT:USDT'].take_profit == 56000.0, "Take profit changed unexpectedly"
        print(f"    ✓ Invalid take profit (below entry) rejected")
        
        # Add a short position
        print("  Test 2: Short position target validation...")
        short_position = Position(
            symbol='ETH/USDT:USDT',
            side='short',
            entry_price=3000.0,
            amount=1.0,
            leverage=10,
            stop_loss=3150.0,
            take_profit=2700.0
        )
        with pm._positions_lock:
            pm.positions['ETH/USDT:USDT'] = short_position
        
        # Valid stop loss update (above entry for short)
        result = pm.safe_update_position_targets('ETH/USDT:USDT', new_stop_loss=3100.0)
        assert result == True, "Expected valid stop loss update to succeed"
        print(f"    ✓ Valid stop loss update for short accepted")
        
        # Invalid stop loss update (below entry for short)
        result = pm.safe_update_position_targets('ETH/USDT:USDT', new_stop_loss=2900.0)
        assert result == False, "Expected invalid stop loss update to fail"
        print(f"    ✓ Invalid stop loss (below entry) rejected for short")
        
        # Valid take profit update (below entry for short)
        result = pm.safe_update_position_targets('ETH/USDT:USDT', new_take_profit=2600.0)
        assert result == True, "Expected valid take profit update to succeed"
        print(f"    ✓ Valid take profit update for short accepted")
        
        # Invalid take profit update (above entry for short)
        result = pm.safe_update_position_targets('ETH/USDT:USDT', new_take_profit=3100.0)
        assert result == False, "Expected invalid take profit update to fail"
        print(f"    ✓ Invalid take profit (above entry) rejected for short")
        
        print("✓ All safe update target tests passed")
        return True
        
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all unit tests"""
    print("="*70)
    print("Unit Tests for Position Manager Enhancements")
    print("="*70)
    
    results = {
        'thread_safe_operations': test_thread_safe_operations(),
        'position_validation': test_position_validation(),
        'concurrent_access': test_concurrent_access(),
        'position_reconciliation': test_position_reconciliation(),
        'safe_update_targets': test_safe_update_targets(),
    }
    
    print("\n" + "="*70)
    print("Unit Test Results")
    print("="*70)
    
    for test, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test:.<50} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("✓✓✓ All unit tests passed! ✓✓✓")
    else:
        print("✗✗✗ Some unit tests failed. ✗✗✗")
    print("="*70)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    exit(main())
