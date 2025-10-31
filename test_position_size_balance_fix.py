"""
Test to verify position sizing respects balance limits with leverage.
This test specifically addresses the bug where positions were calculated
far larger than the balance allowed.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_position_size_respects_balance():
    """Test that position size calculation respects balance with leverage"""
    print("\n" + "="*80)
    print("TESTING POSITION SIZE RESPECTS BALANCE WITH LEVERAGE")
    print("="*80)
    
    try:
        from risk_manager import RiskManager
        
        # Test Case 1: Small balance ($100) with high leverage (10x)
        print("\n  Test 1: $100 balance with 10x leverage...")
        manager = RiskManager(
            max_position_size=500,  # This is intentionally high
            risk_per_trade=0.02,    # 2% risk per trade
            max_open_positions=3
        )
        
        balance = 100.0
        entry_price = 50000.0  # BTC at $50k
        stop_loss_price = 49000.0  # 2% stop loss
        leverage = 10
        
        position_size = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage
        )
        
        position_value = position_size * entry_price
        required_margin = position_value / leverage
        
        print(f"  Balance: ${balance:.2f}")
        print(f"  Leverage: {leverage}x")
        print(f"  Position size: {position_size:.6f} contracts")
        print(f"  Position value (notional): ${position_value:.2f}")
        print(f"  Required margin: ${required_margin:.2f}")
        
        # Critical assertion: required margin should not exceed balance
        assert required_margin <= balance, (
            f"FAILED: Required margin ${required_margin:.2f} exceeds balance ${balance:.2f}! "
            f"This is the bug we're fixing."
        )
        print(f"  ✓ Required margin ${required_margin:.2f} fits within balance ${balance:.2f}")
        
        # Test Case 2: Very small balance ($10) with moderate leverage (5x)
        print("\n  Test 2: $10 balance with 5x leverage...")
        manager.max_position_size = 50
        balance = 10.0
        leverage = 5
        
        position_size = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage
        )
        
        position_value = position_size * entry_price
        required_margin = position_value / leverage
        
        print(f"  Balance: ${balance:.2f}")
        print(f"  Leverage: {leverage}x")
        print(f"  Position size: {position_size:.6f} contracts")
        print(f"  Position value (notional): ${position_value:.2f}")
        print(f"  Required margin: ${required_margin:.2f}")
        
        assert required_margin <= balance, (
            f"FAILED: Required margin ${required_margin:.2f} exceeds balance ${balance:.2f}"
        )
        print(f"  ✓ Required margin ${required_margin:.2f} fits within balance ${balance:.2f}")
        
        # Test Case 3: Larger balance ($1000) with lower leverage (3x)
        print("\n  Test 3: $1000 balance with 3x leverage...")
        manager.max_position_size = 3000
        balance = 1000.0
        leverage = 3
        
        position_size = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage
        )
        
        position_value = position_size * entry_price
        required_margin = position_value / leverage
        
        print(f"  Balance: ${balance:.2f}")
        print(f"  Leverage: {leverage}x")
        print(f"  Position size: {position_size:.6f} contracts")
        print(f"  Position value (notional): ${position_value:.2f}")
        print(f"  Required margin: ${required_margin:.2f}")
        
        assert required_margin <= balance, (
            f"FAILED: Required margin ${required_margin:.2f} exceeds balance ${balance:.2f}"
        )
        print(f"  ✓ Required margin ${required_margin:.2f} fits within balance ${balance:.2f}")
        
        # Test Case 4: Edge case - tight stop loss that would create huge position
        print("\n  Test 4: Tight stop loss (0.5%) with $100 balance and 10x leverage...")
        balance = 100.0
        entry_price = 50000.0
        stop_loss_price = 49750.0  # Only 0.5% stop loss
        leverage = 10
        
        position_size = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage
        )
        
        position_value = position_size * entry_price
        required_margin = position_value / leverage
        
        print(f"  Balance: ${balance:.2f}")
        print(f"  Stop loss: 0.5% (very tight)")
        print(f"  Leverage: {leverage}x")
        print(f"  Position size: {position_size:.6f} contracts")
        print(f"  Position value (notional): ${position_value:.2f}")
        print(f"  Required margin: ${required_margin:.2f}")
        
        # This is the most critical test - tight stops can create huge positions
        assert required_margin <= balance, (
            f"FAILED: Tight stop loss created position requiring ${required_margin:.2f} "
            f"margin which exceeds balance ${balance:.2f}"
        )
        print(f"  ✓ Even with tight stop, required margin ${required_margin:.2f} fits within balance ${balance:.2f}")
        
        # Test Case 5: Very high leverage (20x) with $100 balance
        print("\n  Test 5: Very high leverage (20x) with $100 balance...")
        balance = 100.0
        entry_price = 50000.0
        stop_loss_price = 49000.0  # 2% stop loss
        leverage = 20
        
        position_size = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage
        )
        
        position_value = position_size * entry_price
        required_margin = position_value / leverage
        
        print(f"  Balance: ${balance:.2f}")
        print(f"  Leverage: {leverage}x")
        print(f"  Position size: {position_size:.6f} contracts")
        print(f"  Position value (notional): ${position_value:.2f}")
        print(f"  Required margin: ${required_margin:.2f}")
        
        assert required_margin <= balance, (
            f"FAILED: High leverage created position requiring ${required_margin:.2f} "
            f"margin which exceeds balance ${balance:.2f}"
        )
        print(f"  ✓ High leverage position fits: required margin ${required_margin:.2f} <= balance ${balance:.2f}")
        
        print("\n✓ ALL TESTS PASSED: Position sizing correctly respects balance limits!")
        return True
        
    except AssertionError as e:
        print(f"\n✗ ASSERTION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_max_position_size_interaction():
    """Test interaction between max_position_size and balance limits"""
    print("\n" + "="*80)
    print("TESTING MAX_POSITION_SIZE INTERACTION WITH BALANCE")
    print("="*80)
    
    try:
        from risk_manager import RiskManager
        
        # Scenario: max_position_size is set higher than balance allows
        print("\n  Test: max_position_size ($500) > balance ($100) with 10x leverage...")
        manager = RiskManager(
            max_position_size=500,  # Higher than balance
            risk_per_trade=0.02,
            max_open_positions=3
        )
        
        balance = 100.0
        entry_price = 50000.0
        stop_loss_price = 49000.0
        leverage = 10
        
        position_size = manager.calculate_position_size(
            balance, entry_price, stop_loss_price, leverage
        )
        
        position_value = position_size * entry_price
        required_margin = position_value / leverage
        
        print(f"  Config max_position_size: ${manager.max_position_size:.2f}")
        print(f"  Balance: ${balance:.2f}")
        print(f"  Calculated position value: ${position_value:.2f}")
        print(f"  Required margin: ${required_margin:.2f}")
        
        # The fix should prevent position from exceeding balance capacity
        assert required_margin <= balance, (
            f"Position sizing failed to respect balance: "
            f"required margin ${required_margin:.2f} > balance ${balance:.2f}"
        )
        
        # Position value should also be limited by what balance can afford
        max_affordable_position = balance * leverage * 0.95  # 95% safety factor
        assert position_value <= max_affordable_position, (
            f"Position value ${position_value:.2f} exceeds affordable "
            f"${max_affordable_position:.2f} (balance * leverage * 0.95)"
        )
        
        print(f"  ✓ Position correctly limited by balance despite high max_position_size setting")
        print(f"  ✓ Required margin ${required_margin:.2f} fits within balance ${balance:.2f}")
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ ASSERTION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all balance limit tests"""
    print("="*80)
    print("POSITION SIZE BALANCE FIX VERIFICATION")
    print("Testing that positions respect balance limits with leverage")
    print("="*80)
    
    tests = [
        test_position_size_respects_balance,
        test_max_position_size_interaction,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "="*80)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*80)
    
    if all(results):
        print("\n✅ All balance limit tests passed!")
        print("The position sizing bug has been fixed.")
        return 0
    else:
        print("\n⚠️  Some tests failed - position sizing may still have issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
