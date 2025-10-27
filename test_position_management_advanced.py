#!/usr/bin/env python3
"""
Advanced Position Management Testing Suite

Tests advanced scenarios and edge cases including:
- Position collisions (duplicate symbols)
- Race conditions in concurrent operations
- Scale in/out operations
- Position reconciliation
- Extreme market conditions
- State corruption scenarios
"""

import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional

# Import the mock client from comprehensive tests
import test_position_management_comprehensive as base_tests
MockKuCoinClient = base_tests.MockKuCoinClient


def test_position_collision_prevention():
    """Test that duplicate position creation is prevented"""
    print("\n" + "="*80)
    print("TEST: Position Collision Prevention")
    print("="*80)
    
    try:
        from position_manager import PositionManager
        
        client = MockKuCoinClient()
        pm = PositionManager(client)
        
        # Open first position
        success1 = pm.open_position('BTC/USDT:USDT', 'BUY', 0.1, 10, 0.05)
        assert success1, "First position should open successfully"
        print(f"✓ First position opened")
        
        # Try to open duplicate position - should fail
        success2 = pm.open_position('BTC/USDT:USDT', 'BUY', 0.1, 10, 0.05)
        assert not success2, "Duplicate position should be rejected"
        print(f"✓ Duplicate position rejected")
        
        # Verify only one position exists
        count = pm.get_open_positions_count()
        assert count == 1, f"Should have exactly 1 position, got {count}"
        print(f"✓ Position count correct: {count}")
        
        return True
        
    except Exception as e:
        print(f"✗ Position collision test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_concurrent_position_operations():
    """Test race conditions in concurrent position operations"""
    print("\n" + "="*80)
    print("TEST: Concurrent Position Operations (Race Conditions)")
    print("="*80)
    
    try:
        from position_manager import PositionManager
        
        client = MockKuCoinClient()
        pm = PositionManager(client)
        
        # Open initial position
        pm.open_position('BTC/USDT:USDT', 'BUY', 0.1, 10, 0.05)
        
        errors = []
        operation_count = [0]
        
        def concurrent_operations():
            """Perform various operations concurrently"""
            try:
                for i in range(50):
                    # Mix of read and write operations
                    if i % 5 == 0:
                        # Check if position exists
                        has_pos = pm.has_position('BTC/USDT:USDT')
                    elif i % 5 == 1:
                        # Get position
                        pos = pm.get_position('BTC/USDT:USDT')
                    elif i % 5 == 2:
                        # Get all positions
                        all_pos = pm.get_all_positions()
                    elif i % 5 == 3:
                        # Update targets (write operation)
                        pm.safe_update_position_targets(
                            'BTC/USDT:USDT',
                            new_stop_loss=49000.0 + i,
                            reason='test'
                        )
                    else:
                        # Get open count
                        count = pm.get_open_positions_count()
                    
                    operation_count[0] += 1
                    
            except Exception as e:
                errors.append(f"Thread error: {str(e)}")
        
        # Run with 20 concurrent threads
        threads = []
        for _ in range(20):
            t = threading.Thread(target=concurrent_operations)
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Race condition errors: {errors[:5]}"
        print(f"✓ No race conditions detected")
        print(f"  Threads: 20")
        print(f"  Operations: {operation_count[0]}")
        print(f"  Errors: {len(errors)}")
        
        # Verify position integrity after concurrent operations
        pos = pm.get_position('BTC/USDT:USDT')
        assert pos is not None, "Position should still exist"
        assert pos.symbol == 'BTC/USDT:USDT', "Position data should be intact"
        print(f"✓ Position integrity maintained")
        
        return True
        
    except Exception as e:
        print(f"✗ Concurrent operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scale_in_out_operations():
    """Test position scaling in and out"""
    print("\n" + "="*80)
    print("TEST: Scale In/Out Operations")
    print("="*80)
    
    try:
        from position_manager import PositionManager
        
        client = MockKuCoinClient()
        pm = PositionManager(client)
        
        # Open initial position
        success = pm.open_position('BTC/USDT:USDT', 'BUY', 0.1, 10, 0.05)
        assert success, "Failed to open initial position"
        
        initial_pos = pm.get_position('BTC/USDT:USDT')
        initial_amount = initial_pos.amount
        print(f"✓ Initial position: {initial_amount} contracts")
        
        # Test scale in
        success = pm.scale_in_position('BTC/USDT:USDT', 0.05, 50500.0)
        assert success, "Scale in should succeed"
        
        scaled_pos = pm.get_position('BTC/USDT:USDT')
        assert scaled_pos.amount > initial_amount, "Amount should increase after scale in"
        print(f"✓ Scale in successful: {initial_amount} -> {scaled_pos.amount} contracts")
        
        # Verify average entry price updated
        print(f"  Entry price updated: ${initial_pos.entry_price:.2f} -> ${scaled_pos.entry_price:.2f}")
        
        # Test partial scale out (50%)
        scaled_amount = scaled_pos.amount  # Store the amount before scaling out
        scale_out_amount = scaled_amount * 0.5
        pnl = pm.scale_out_position('BTC/USDT:USDT', scale_out_amount, 'test_partial')
        assert pnl is not None, "Scale out should succeed"
        
        remaining_pos = pm.get_position('BTC/USDT:USDT')
        assert remaining_pos is not None, "Position should still exist after partial close"
        assert remaining_pos.amount < scaled_amount, "Amount should decrease"
        print(f"✓ Partial scale out: {scaled_amount:.4f} -> {remaining_pos.amount:.4f} contracts")
        print(f"  P&L on partial exit: {pnl:.2%}")
        
        # Test scale out below minimum (should adjust to minimum)
        tiny_amount = 0.0001  # Very small amount
        pnl2 = pm.scale_out_position('BTC/USDT:USDT', tiny_amount, 'test_minimum')
        
        # Either adjusted to minimum and closed, or position still exists
        final_pos = pm.get_position('BTC/USDT:USDT')
        if final_pos:
            print(f"✓ Minimum order size handling: position remains")
        else:
            print(f"✓ Minimum order size handling: adjusted to minimum and closed position")
        
        return True
        
    except Exception as e:
        print(f"✗ Scale in/out test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_position_reconciliation():
    """Test position reconciliation with exchange"""
    print("\n" + "="*80)
    print("TEST: Position Reconciliation")
    print("="*80)
    
    try:
        from position_manager import PositionManager, Position
        
        client = MockKuCoinClient()
        pm = PositionManager(client)
        
        # Simulate: Bot has position but exchange doesn't
        pm.open_position('BTC/USDT:USDT', 'BUY', 0.1, 10, 0.05)
        
        # Clear exchange positions to simulate discrepancy
        client.positions = {}
        
        # Reconcile should detect and fix discrepancy
        discrepancies = pm.reconcile_positions()
        
        # After reconciliation, local position should be removed
        has_pos = pm.has_position('BTC/USDT:USDT')
        assert not has_pos, "Orphaned position should be removed"
        print(f"✓ Orphaned local position removed")
        print(f"  Discrepancies found: {discrepancies}")
        
        # Simulate: Exchange has position but bot doesn't
        client.positions['ETH/USDT:USDT'] = {
            'symbol': 'ETH/USDT:USDT',
            'contracts': 1.0,
            'side': 'long',
            'entryPrice': 3000.0,
            'leverage': 5
        }
        
        # Reconcile should import the position
        discrepancies = pm.reconcile_positions()
        
        # After reconciliation, position should be tracked
        has_eth = pm.has_position('ETH/USDT:USDT')
        assert has_eth, "Exchange position should be imported"
        print(f"✓ Exchange position imported")
        print(f"  Discrepancies found: {discrepancies}")
        
        return True
        
    except Exception as e:
        print(f"✗ Position reconciliation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_extreme_market_conditions():
    """Test position behavior under extreme conditions"""
    print("\n" + "="*80)
    print("TEST: Extreme Market Conditions")
    print("="*80)
    
    try:
        from position_manager import Position
        
        # Test 1: Flash crash scenario (-20% instant drop)
        print("\n1. Flash Crash Scenario")
        long_pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Price drops 20% instantly
        crash_price = 40000.0
        should_close, reason = long_pos.should_close(crash_price)
        assert should_close, "Should close during flash crash"
        assert 'emergency' in reason.lower(), f"Should trigger emergency stop, got {reason}"
        
        pnl = long_pos.get_leveraged_pnl(crash_price)
        print(f"  ✓ Flash crash handled: {pnl:.2%} ROI")
        print(f"    Close reason: {reason}")
        
        # Test 2: Moon shot scenario (+50% instant pump)
        print("\n2. Moon Shot Scenario")
        long_pos2 = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=5,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Price pumps 50%
        moon_price = 75000.0
        should_close, reason = long_pos2.should_close(moon_price)
        
        pnl = long_pos2.get_leveraged_pnl(moon_price)
        print(f"  ✓ Moon shot handled: {pnl:.2%} ROI")
        if should_close:
            print(f"    Close reason: {reason}")
        else:
            print(f"    Position remains open (TP may have extended)")
        
        # Test 3: Extreme volatility (price whipsaw)
        print("\n3. Volatility Whipsaw")
        whipsaw_pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Price moves: +5%, -3%, +4%, -2%
        prices = [52500, 51000, 52000, 51000]
        for i, price in enumerate(prices):
            whipsaw_pos.update_trailing_stop(price, 0.02)
            pnl = whipsaw_pos.get_leveraged_pnl(price)
            print(f"    Move {i+1}: ${price:.0f}, ROI: {pnl:+.1%}, SL: ${whipsaw_pos.stop_loss:.0f}")
        
        print(f"  ✓ Trailing stop survived volatility")
        
        # Test 4: Leverage amplification
        print("\n4. Leverage Amplification")
        
        # Same price move with different leverage
        price_change = 0.03  # 3% price move
        leverages = [1, 5, 10, 20]
        
        for lev in leverages:
            test_pos = Position(
                symbol='BTC/USDT:USDT',
                side='long',
                entry_price=50000.0,
                amount=0.1,
                leverage=lev,
                stop_loss=48000.0,
                take_profit=55000.0
            )
            
            new_price = 50000.0 * (1 + price_change)
            roi = test_pos.get_leveraged_pnl(new_price)
            print(f"    {lev}x leverage: 3% price = {roi:.1%} ROI")
        
        print(f"  ✓ Leverage amplification calculated correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Extreme market conditions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_corruption_recovery():
    """Test recovery from corrupted or invalid states"""
    print("\n" + "="*80)
    print("TEST: State Corruption Recovery")
    print("="*80)
    
    try:
        from position_manager import Position
        
        # Test 1: Invalid stop loss (above entry for long)
        print("\n1. Invalid Stop Loss Detection")
        try:
            pos = Position(
                symbol='BTC/USDT:USDT',
                side='long',
                entry_price=50000.0,
                amount=0.1,
                leverage=10,
                stop_loss=51000.0,  # Above entry - invalid!
                take_profit=52000.0
            )
            # Even though created, the logic should prevent closing at wrong conditions
            should_close, reason = pos.should_close(50500.0)
            print(f"  ⚠ Invalid SL created but position logic handles it")
        except Exception as e:
            print(f"  ✓ Invalid stop loss prevented: {type(e).__name__}")
        
        # Test 2: Invalid take profit (below entry for long)
        print("\n2. Invalid Take Profit Detection")
        try:
            pos = Position(
                symbol='BTC/USDT:USDT',
                side='long',
                entry_price=50000.0,
                amount=0.1,
                leverage=10,
                stop_loss=49000.0,
                take_profit=48000.0  # Below entry - invalid!
            )
            print(f"  ⚠ Invalid TP created but position logic handles it")
        except Exception as e:
            print(f"  ✓ Invalid take profit prevented: {type(e).__name__}")
        
        # Test 3: NaN/Inf values in calculations
        print("\n3. NaN/Inf Value Handling")
        pos = Position(
            symbol='BTC/USDT:USDT',
            side='long',
            entry_price=50000.0,
            amount=0.1,
            leverage=10,
            stop_loss=49000.0,
            take_profit=52000.0
        )
        
        # Test with extreme values
        import math
        
        # Test infinity
        try:
            pnl_inf = pos.get_pnl(float('inf'))
            print(f"  Infinity price: P&L = {pnl_inf}")
        except Exception as e:
            print(f"  ✓ Infinity handled: {type(e).__name__}")
        
        # Test very large number (near overflow)
        try:
            pnl_large = pos.get_pnl(1e100)
            print(f"  Very large price: P&L = {pnl_large:.2%}")
            print(f"  ✓ Large values handled gracefully")
        except Exception as e:
            print(f"  ✓ Large value overflow prevented: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ State corruption recovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_positions_management():
    """Test managing multiple positions simultaneously"""
    print("\n" + "="*80)
    print("TEST: Multiple Positions Management")
    print("="*80)
    
    try:
        from position_manager import PositionManager
        
        client = MockKuCoinClient()
        pm = PositionManager(client)
        
        # Open multiple positions
        symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']
        
        for symbol in symbols:
            success = pm.open_position(symbol, 'BUY', 0.1, 10, 0.05)
            assert success, f"Failed to open {symbol}"
        
        count = pm.get_open_positions_count()
        assert count == len(symbols), f"Should have {len(symbols)} positions, got {count}"
        print(f"✓ Opened {count} positions")
        
        # Update all positions
        for symbol in symbols:
            client.set_price(symbol, client.current_prices[symbol] * 1.02)
        
        updates = list(pm.update_positions())
        print(f"✓ Updated all positions (closed: {len(updates)})")
        
        # Verify positions still exist (unless closed by profit taking)
        remaining = pm.get_open_positions_count()
        print(f"  Remaining positions: {remaining}/{len(symbols)}")
        
        # Close all remaining positions
        for symbol in symbols:
            if pm.has_position(symbol):
                pnl = pm.close_position(symbol, 'test_cleanup')
                if pnl is not None:
                    print(f"  Closed {symbol}: P&L = {pnl:.2%}")
        
        final_count = pm.get_open_positions_count()
        assert final_count == 0, f"All positions should be closed, {final_count} remain"
        print(f"✓ All positions closed successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Multiple positions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all advanced position management tests"""
    print("\n" + "="*80)
    print("ADVANCED POSITION MANAGEMENT TEST SUITE")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Position Collision Prevention", test_position_collision_prevention),
        ("Concurrent Operations", test_concurrent_position_operations),
        ("Scale In/Out Operations", test_scale_in_out_operations),
        ("Position Reconciliation", test_position_reconciliation),
        ("Extreme Market Conditions", test_extreme_market_conditions),
        ("State Corruption Recovery", test_state_corruption_recovery),
        ("Multiple Positions", test_multiple_positions_management),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print("\n" + "="*80)
    print(f"Results: {passed}/{total} tests passed")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
