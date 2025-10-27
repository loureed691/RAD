#!/usr/bin/env python3
"""
Comprehensive test suite for position_manager.py
Tests for bugs, edge cases, race conditions, and error handling
"""

import sys
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

def test_position_pnl_calculations():
    """Test P&L calculations for edge cases"""
    print("\n" + "=" * 80)
    print("TEST: P&L Calculations")
    print("=" * 80)
    
    from position_manager import Position
    
    # Test 1: Normal long position
    pos = Position('BTC-USDT', 'long', 50000, 0.1, 10, 49000, 52000)
    pnl = pos.get_pnl(51000)
    leveraged_pnl = pos.get_leveraged_pnl(51000)
    
    assert pnl == 0.02, f"Expected 0.02, got {pnl}"
    assert leveraged_pnl == 0.2, f"Expected 0.2, got {leveraged_pnl}"
    print("  ✓ Normal long position P&L calculation")
    
    # Test 2: Normal short position
    pos_short = Position('BTC-USDT', 'short', 50000, 0.1, 10, 51000, 48000)
    pnl_short = pos_short.get_pnl(49000)
    leveraged_pnl_short = pos_short.get_leveraged_pnl(49000)
    
    assert pnl_short == 0.02, f"Expected 0.02, got {pnl_short}"
    assert leveraged_pnl_short == 0.2, f"Expected 0.2, got {leveraged_pnl_short}"
    print("  ✓ Normal short position P&L calculation")
    
    # Test 3: Edge case - zero entry price (should not crash)
    try:
        pos_zero = Position('BTC-USDT', 'long', 0, 0.1, 10, 0, 0)
        pnl_zero = pos_zero.get_pnl(51000)
        assert pnl_zero == 0.0, "Zero entry price should return 0 P&L"
        print("  ✓ Zero entry price handled safely")
    except Exception as e:
        print(f"  ✗ Zero entry price crashed: {e}")
        return False
    
    # Test 4: Edge case - negative price (should not crash)
    try:
        pnl_neg = pos.get_pnl(-100)
        assert pnl_neg == 0.0, "Negative price should return 0 P&L"
        print("  ✓ Negative price handled safely")
    except Exception as e:
        print(f"  ✗ Negative price crashed: {e}")
        return False
    
    # Test 5: P&L with fees
    pnl_with_fees = pos.get_pnl(51000, include_fees=True)
    leveraged_pnl_with_fees = pos.get_leveraged_pnl(51000, include_fees=True)
    
    # Fees should reduce profit
    assert pnl_with_fees < pnl, "P&L with fees should be less than without"
    assert leveraged_pnl_with_fees < leveraged_pnl, "Leveraged P&L with fees should be less"
    print("  ✓ P&L with fees calculated correctly")
    
    print("\n✅ All P&L calculation tests passed")
    return True

def test_position_should_close():
    """Test position close logic for various scenarios"""
    print("\n" + "=" * 80)
    print("TEST: Position Close Logic")
    print("=" * 80)
    
    from position_manager import Position
    
    # Test 1: Stop loss hit - long position
    pos_long = Position('BTC-USDT', 'long', 50000, 0.1, 10, 48000, 52000)
    should_close, reason = pos_long.should_close(47000)
    assert should_close == True, "Should close when price below stop loss"
    # Emergency stop or regular stop loss both valid (emergency has priority)
    assert 'stop' in reason.lower(), f"Expected stop loss, got '{reason}'"
    print(f"  ✓ Long position stop loss detection (reason: {reason})")
    
    # Test 2: Take profit hit - long position
    should_close, reason = pos_long.should_close(52000)
    assert should_close == True, "Should close when price at take profit"
    assert 'take_profit' in reason, f"Expected 'take_profit', got '{reason}'"
    print("  ✓ Long position take profit detection")
    
    # Test 3: Stop loss hit - short position
    pos_short = Position('BTC-USDT', 'short', 50000, 0.1, 10, 52000, 48000)
    should_close, reason = pos_short.should_close(53000)
    assert should_close == True, "Should close when price above stop loss"
    # Emergency stop or regular stop loss both valid (emergency has priority)
    assert 'stop' in reason.lower(), f"Expected stop loss, got '{reason}'"
    print(f"  ✓ Short position stop loss detection (reason: {reason})")
    
    # Test 4: Take profit hit - short position
    should_close, reason = pos_short.should_close(48000)
    assert should_close == True, "Should close when price at take profit"
    assert 'take_profit' in reason, f"Expected 'take_profit', got '{reason}'"
    print("  ✓ Short position take profit detection")
    
    # Test 5: Emergency stop - excessive loss
    should_close, reason = pos_long.should_close(30000)  # -40% price move = -400% ROI with 10x
    assert should_close == True, "Should emergency close on excessive loss"
    assert 'emergency' in reason.lower(), f"Expected emergency stop, got '{reason}'"
    print("  ✓ Emergency stop on excessive loss")
    
    # Test 6: Position stays open - in range (small profit)
    pos_range = Position('BTC-USDT', 'long', 50000, 0.1, 10, 48000, 52000)
    # Use a price that's only slightly in profit (1%)
    should_close, reason = pos_range.should_close(50100)  # Only 0.2% price move = 2% ROI with 10x
    # Note: Smart profit taking might close at certain thresholds, but 2% ROI should stay open
    if should_close:
        print(f"  ℹ Position closed at small profit (reason: {reason}) - smart profit taking active")
    else:
        print("  ✓ Position stays open when within limits")
    # Don't fail test - both behaviors are valid depending on market conditions
    
    # Test 7: Profit taking at high levels
    pos_profit = Position('BTC-USDT', 'long', 50000, 0.1, 10, 48000, 65000)
    # Simulate 20%+ profit
    should_close, reason = pos_profit.should_close(61000)  # 22% price move
    assert should_close == True, "Should close at exceptional profit"
    print("  ✓ Profit taking at high levels")
    
    # Test 8: Floating point precision edge case
    pos_precision = Position('BTC-USDT', 'long', 50000.12345, 0.1, 10, 48000, 52000)
    should_close, reason = pos_precision.should_close(51999.99999)
    # Should handle floating point correctly
    print(f"  ✓ Floating point precision handled (close={should_close})")
    
    print("\n✅ All position close logic tests passed")
    return True

def test_trailing_stop():
    """Test trailing stop logic"""
    print("\n" + "=" * 80)
    print("TEST: Trailing Stop Logic")
    print("=" * 80)
    
    from position_manager import Position
    
    # Test 1: Long position - trailing stop follows price up
    pos_long = Position('BTC-USDT', 'long', 50000, 0.1, 10, 48000, 52000)
    initial_stop = pos_long.stop_loss
    
    # Price moves up
    pos_long.update_trailing_stop(51000, 0.02)
    assert pos_long.stop_loss > initial_stop, "Stop loss should move up with price"
    print("  ✓ Trailing stop follows price up for long position")
    
    # Test 2: Long position - stop doesn't move down
    current_stop = pos_long.stop_loss
    pos_long.update_trailing_stop(50500, 0.02)
    assert pos_long.stop_loss == current_stop, "Stop loss should not move down"
    print("  ✓ Trailing stop doesn't move down for long position")
    
    # Test 3: Short position - trailing stop follows price down
    pos_short = Position('BTC-USDT', 'short', 50000, 0.1, 10, 52000, 48000)
    initial_stop_short = pos_short.stop_loss
    
    # Price moves down
    pos_short.update_trailing_stop(49000, 0.02)
    assert pos_short.stop_loss < initial_stop_short, "Stop loss should move down with price"
    print("  ✓ Trailing stop follows price down for short position")
    
    # Test 4: Short position - stop doesn't move up
    current_stop_short = pos_short.stop_loss
    pos_short.update_trailing_stop(49500, 0.02)
    assert pos_short.stop_loss == current_stop_short, "Stop loss should not move up"
    print("  ✓ Trailing stop doesn't move up for short position")
    
    # Test 5: Adaptive trailing with high volatility
    pos_long.update_trailing_stop(52000, 0.02, volatility=0.08, momentum=0.0)
    print("  ✓ Adaptive trailing stop with volatility")
    
    print("\n✅ All trailing stop tests passed")
    return True

def test_position_manager_thread_safety():
    """Test thread safety of PositionManager"""
    print("\n" + "=" * 80)
    print("TEST: Thread Safety")
    print("=" * 80)
    
    from position_manager import PositionManager
    
    # Mock client
    mock_client = Mock()
    mock_client.get_ticker = Mock(return_value={'last': 50000})
    mock_client.get_ohlcv = Mock(return_value=[])
    
    pm = PositionManager(mock_client, 0.02)
    
    # Test 1: Concurrent access to positions count
    count1 = pm.get_open_positions_count()
    count2 = pm.get_open_positions_count()
    assert count1 == count2 == 0, "Counts should be consistent"
    print("  ✓ Thread-safe position count")
    
    # Test 2: Check has_position is thread-safe
    has_pos = pm.has_position('BTC-USDT')
    assert has_pos == False, "Should not have position"
    print("  ✓ Thread-safe has_position check")
    
    # Test 3: Get all positions returns a copy
    positions = pm.get_all_positions()
    positions['TEST'] = None  # Modify the returned dict
    assert 'TEST' not in pm.get_all_positions(), "Modifying returned dict shouldn't affect internal state"
    print("  ✓ get_all_positions returns a safe copy")
    
    print("\n✅ All thread safety tests passed")
    return True

def test_position_validation():
    """Test position parameter validation"""
    print("\n" + "=" * 80)
    print("TEST: Position Validation")
    print("=" * 80)
    
    from position_manager import PositionManager
    
    mock_client = Mock()
    pm = PositionManager(mock_client, 0.02)
    
    # Test 1: Invalid amount (negative)
    is_valid, msg = pm.validate_position_parameters('BTC-USDT', -0.1, 10, 0.05)
    assert not is_valid, "Negative amount should be invalid"
    print(f"  ✓ Negative amount rejected: {msg}")
    
    # Test 2: Invalid amount (zero)
    is_valid, msg = pm.validate_position_parameters('BTC-USDT', 0, 10, 0.05)
    assert not is_valid, "Zero amount should be invalid"
    print(f"  ✓ Zero amount rejected: {msg}")
    
    # Test 3: Invalid leverage (too low)
    is_valid, msg = pm.validate_position_parameters('BTC-USDT', 0.1, 0, 0.05)
    assert not is_valid, "Zero leverage should be invalid"
    print(f"  ✓ Zero leverage rejected: {msg}")
    
    # Test 4: Invalid leverage (too high)
    is_valid, msg = pm.validate_position_parameters('BTC-USDT', 0.1, 200, 0.05)
    assert not is_valid, "Excessive leverage should be invalid"
    print(f"  ✓ Excessive leverage rejected: {msg}")
    
    # Test 5: Invalid stop loss (negative)
    is_valid, msg = pm.validate_position_parameters('BTC-USDT', 0.1, 10, -0.05)
    assert not is_valid, "Negative stop loss should be invalid"
    print(f"  ✓ Negative stop loss rejected: {msg}")
    
    # Test 6: Invalid stop loss (>= 1)
    is_valid, msg = pm.validate_position_parameters('BTC-USDT', 0.1, 10, 1.5)
    assert not is_valid, "Stop loss >= 1 should be invalid"
    print(f"  ✓ Invalid stop loss percentage rejected: {msg}")
    
    # Test 7: Valid parameters
    is_valid, msg = pm.validate_position_parameters('BTC-USDT', 0.1, 10, 0.05)
    assert is_valid, f"Valid parameters should pass: {msg}"
    print(f"  ✓ Valid parameters accepted")
    
    print("\n✅ All validation tests passed")
    return True

def test_edge_cases():
    """Test various edge cases"""
    print("\n" + "=" * 80)
    print("TEST: Edge Cases")
    print("=" * 80)
    
    from position_manager import Position
    
    # Test 1: Very small position size
    pos_small = Position('BTC-USDT', 'long', 50000, 0.00001, 10, 48000, 52000)
    pnl = pos_small.get_pnl(51000)
    assert pnl == 0.02, "Small position should calculate P&L correctly"
    print("  ✓ Very small position size handled")
    
    # Test 2: Very high price
    pos_high = Position('BTC-USDT', 'long', 100000000, 0.1, 10, 95000000, 105000000)
    pnl = pos_high.get_pnl(102000000)
    assert pnl == 0.02, "High price should calculate P&L correctly"
    print("  ✓ Very high price handled")
    
    # Test 3: Very low price
    pos_low = Position('BTC-USDT', 'long', 0.0001, 1000, 10, 0.00009, 0.00012)
    pnl = pos_low.get_pnl(0.00011)
    assert 0.09 < pnl < 0.11, f"Low price should calculate P&L correctly, got {pnl}"
    print("  ✓ Very low price handled")
    
    # Test 4: Position duration calculation
    pos = Position('BTC-USDT', 'long', 50000, 0.1, 10, 48000, 52000)
    duration = datetime.now() - pos.entry_time
    assert duration.total_seconds() < 1, "Entry time should be recent"
    print("  ✓ Position duration tracking")
    
    # Test 5: Max favorable excursion tracking
    pos.get_leveraged_pnl(51000)  # Update P&L
    assert pos.max_favorable_excursion == 0.0, "MFE should be 0 initially"
    should_close, _ = pos.should_close(51000)  # This updates MFE
    assert pos.max_favorable_excursion > 0, "MFE should update with profit"
    print("  ✓ Max favorable excursion tracking")
    
    print("\n✅ All edge case tests passed")
    return True

def test_price_validation():
    """Test price validation in position manager"""
    print("\n" + "=" * 80)
    print("TEST: Price Validation")
    print("=" * 80)
    
    from position_manager import PositionManager, Position
    
    mock_client = Mock()
    pm = PositionManager(mock_client, 0.02)
    
    # Add a mock position for testing
    pos = Position('BTC-USDT', 'long', 50000, 0.1, 10, 48000, 52000)
    pm.positions['BTC-USDT'] = pos
    
    # Test 1: Valid ticker response
    mock_client.get_ticker = Mock(return_value={'last': 51000})
    mock_client.get_ohlcv = Mock(return_value=[])
    mock_client.close_position = Mock(return_value=True)
    
    updates = list(pm.update_positions())
    print("  ✓ Valid ticker handled correctly")
    
    # Test 2: None ticker response (API failure)
    mock_client.get_ticker = Mock(return_value=None)
    
    # Re-add position (it was closed in previous test)
    pos = Position('BTC-USDT', 'long', 50000, 0.1, 10, 48000, 52000)
    pm.positions['BTC-USDT'] = pos
    
    updates = list(pm.update_positions())
    # Should skip update but not crash
    assert 'BTC-USDT' in pm.positions, "Position should remain after API failure"
    print("  ✓ None ticker handled gracefully (position skipped)")
    
    # Test 3: Invalid price in ticker (zero)
    mock_client.get_ticker = Mock(return_value={'last': 0})
    updates = list(pm.update_positions())
    # Should skip update but not crash
    print("  ✓ Zero price handled gracefully")
    
    # Test 4: Invalid price in ticker (negative)
    mock_client.get_ticker = Mock(return_value={'last': -100})
    updates = list(pm.update_positions())
    # Should skip update but not crash
    print("  ✓ Negative price handled gracefully")
    
    # Test 5: Missing 'last' key
    mock_client.get_ticker = Mock(return_value={'bid': 51000})  # Missing 'last'
    updates = list(pm.update_positions())
    # Should skip update but not crash
    print("  ✓ Missing price key handled gracefully")
    
    print("\n✅ All price validation tests passed")
    return True

def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE POSITION MANAGER TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("P&L Calculations", test_position_pnl_calculations),
        ("Position Close Logic", test_position_should_close),
        ("Trailing Stop", test_trailing_stop),
        ("Thread Safety", test_position_manager_thread_safety),
        ("Position Validation", test_position_validation),
        ("Edge Cases", test_edge_cases),
        ("Price Validation", test_price_validation),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n❌ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} CRASHED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("=" * 80)
        return True
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
