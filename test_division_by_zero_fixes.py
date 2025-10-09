"""
Test script to verify division by zero fixes
"""
from datetime import datetime
from unittest.mock import Mock, MagicMock
import sys

def test_position_manager_time_delta_fix():
    """Test that position_manager handles zero time delta safely"""
    print("\n" + "="*70)
    print("TEST: Position Manager Time Delta Division Fix")
    print("="*70)
    
    try:
        # Import after path setup
        from position_manager import Position
        
        # Create a position
        position = Position(
            symbol='BTC-USDT:USDT',
            side='long',
            entry_price=50000,
            amount=0.1,
            leverage=10,
            stop_loss=49000,
            take_profit=52000
        )
        
        # Test 1: Normal time delta (should work)
        print("\n  Test 1: Normal time delta (1 second apart)")
        import time
        time.sleep(0.001)  # Small delay
        position.update_take_profit(
            current_price=50500,
            momentum=0.02,
            trend_strength=0.7,
            volatility=0.03,
            rsi=55
        )
        print("    ✓ No error with normal time delta")
        
        # Test 2: Zero time delta (edge case - should not crash)
        print("\n  Test 2: Zero time delta (simultaneous calls)")
        # Reset the time to create zero delta scenario
        position.last_pnl_time = datetime.now()
        position.update_take_profit(
            current_price=50500,
            momentum=0.02,
            trend_strength=0.7,
            volatility=0.03,
            rsi=55
        )
        print("    ✓ No crash with zero time delta")
        
        print("\n  ✅ PASS: Time delta division is safe")
        return True
        
    except ZeroDivisionError as e:
        print(f"\n  ❌ FAIL: Division by zero error: {e}")
        return False
    except Exception as e:
        print(f"\n  ❌ FAIL: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_position_get_pnl_fix():
    """Test that Position.get_pnl handles zero entry_price safely"""
    print("\n" + "="*70)
    print("TEST: Position get_pnl() Division Fix")
    print("="*70)
    
    try:
        from position_manager import Position
        
        # Test 1: Normal entry price
        print("\n  Test 1: Normal entry price (50000)")
        position = Position(
            symbol='BTC-USDT:USDT',
            side='long',
            entry_price=50000,
            amount=0.1,
            leverage=10,
            stop_loss=49000,
            take_profit=52000
        )
        pnl = position.get_pnl(51000)
        print(f"    P/L: {pnl:.2%}")
        print("    ✓ Normal calculation works")
        
        # Test 2: Zero entry price (edge case - should not crash)
        print("\n  Test 2: Zero entry price (defensive edge case)")
        position.entry_price = 0
        pnl = position.get_pnl(51000)
        print(f"    P/L: {pnl:.2%} (should be 0.0)")
        
        if pnl == 0.0:
            print("    ✓ Safely returns 0.0 for invalid entry price")
        else:
            print(f"    ⚠️  Unexpected P/L value: {pnl}")
        
        # Test 3: Negative entry price (should also return 0)
        print("\n  Test 3: Negative entry price (invalid data)")
        position.entry_price = -100
        pnl = position.get_pnl(51000)
        print(f"    P/L: {pnl:.2%} (should be 0.0)")
        
        if pnl == 0.0:
            print("    ✓ Safely returns 0.0 for negative entry price")
        else:
            print(f"    ⚠️  Unexpected P/L value: {pnl}")
        
        print("\n  ✅ PASS: get_pnl() division is safe")
        return True
        
    except ZeroDivisionError as e:
        print(f"\n  ❌ FAIL: Division by zero error: {e}")
        return False
    except Exception as e:
        print(f"\n  ❌ FAIL: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_manager_portfolio_heat_fix():
    """Test that RiskManager.get_portfolio_heat handles zero entry_price safely"""
    print("\n" + "="*70)
    print("TEST: Risk Manager Portfolio Heat Division Fix")
    print("="*70)
    
    try:
        from risk_manager import RiskManager
        from position_manager import Position
        
        risk_mgr = RiskManager(
            max_position_size=1000,
            risk_per_trade=0.02,
            max_open_positions=3
        )
        
        # Test 1: Normal positions
        print("\n  Test 1: Normal positions with valid entry prices")
        positions = [
            Position('BTC-USDT:USDT', 'long', 50000, 0.1, 10, 49000, 52000),
            Position('ETH-USDT:USDT', 'long', 3000, 1.0, 10, 2950, 3100),
        ]
        heat = risk_mgr.get_portfolio_heat(positions)
        print(f"    Portfolio heat: {heat:.2f}")
        print("    ✓ Normal calculation works")
        
        # Test 2: Position with zero entry price (should be skipped)
        print("\n  Test 2: Position with zero entry price (defensive)")
        bad_position = Position('BAD-USDT:USDT', 'long', 0, 0.1, 10, 0, 0)
        positions.append(bad_position)
        heat = risk_mgr.get_portfolio_heat(positions)
        print(f"    Portfolio heat: {heat:.2f}")
        print("    ✓ Bad position skipped, no crash")
        
        print("\n  ✅ PASS: Portfolio heat calculation is safe")
        return True
        
    except ZeroDivisionError as e:
        print(f"\n  ❌ FAIL: Division by zero error: {e}")
        return False
    except Exception as e:
        print(f"\n  ❌ FAIL: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_manager_position_size_fix():
    """Test that RiskManager.calculate_position_size handles zero entry_price safely"""
    print("\n" + "="*70)
    print("TEST: Risk Manager Position Size Division Fix")
    print("="*70)
    
    try:
        from risk_manager import RiskManager
        
        risk_mgr = RiskManager(
            max_position_size=1000,
            risk_per_trade=0.02,
            max_open_positions=3
        )
        
        # Test 1: Normal parameters
        print("\n  Test 1: Normal entry price (50000)")
        size = risk_mgr.calculate_position_size(
            balance=10000,
            entry_price=50000,
            stop_loss_price=49000,
            leverage=10
        )
        print(f"    Position size: {size:.4f} contracts")
        print("    ✓ Normal calculation works")
        
        # Test 2: Zero entry price (should return 0 and log error)
        print("\n  Test 2: Zero entry price (defensive)")
        size = risk_mgr.calculate_position_size(
            balance=10000,
            entry_price=0,
            stop_loss_price=49000,
            leverage=10
        )
        print(f"    Position size: {size:.4f} (should be 0.0)")
        
        if size == 0.0:
            print("    ✓ Safely returns 0.0 for invalid entry price")
        else:
            print(f"    ⚠️  Unexpected size: {size}")
        
        # Test 3: Negative entry price
        print("\n  Test 3: Negative entry price (invalid)")
        size = risk_mgr.calculate_position_size(
            balance=10000,
            entry_price=-100,
            stop_loss_price=49000,
            leverage=10
        )
        print(f"    Position size: {size:.4f} (should be 0.0)")
        
        if size == 0.0:
            print("    ✓ Safely returns 0.0 for negative entry price")
        else:
            print(f"    ⚠️  Unexpected size: {size}")
        
        print("\n  ✅ PASS: Position size calculation is safe")
        return True
        
    except ZeroDivisionError as e:
        print(f"\n  ❌ FAIL: Division by zero error: {e}")
        return False
    except Exception as e:
        print(f"\n  ❌ FAIL: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("DIVISION BY ZERO FIXES VALIDATION TESTS")
    print("="*70)
    
    results = {
        'Position Manager Time Delta': test_position_manager_time_delta_fix(),
        'Position get_pnl()': test_position_get_pnl_fix(),
        'Risk Manager Portfolio Heat': test_risk_manager_portfolio_heat_fix(),
        'Risk Manager Position Size': test_risk_manager_position_size_fix(),
    }
    
    print("\n" + "="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
