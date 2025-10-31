"""
Test to verify position size calculation accounts for leverage and margin constraints
"""
from risk_manager import RiskManager

# Constants
FEE_BUFFER = 1.05  # 5% buffer for fees and safety margin


def test_position_size_respects_margin_with_leverage():
    """Test that position sizing accounts for leverage to prevent margin check failures"""
    print("\n" + "="*70)
    print("Testing Position Size Calculation with Leverage Constraints")
    print("="*70)
    
    # Initialize risk manager
    manager = RiskManager(
        max_position_size=100,  # $100 max position
        risk_per_trade=0.02,    # 2% risk per trade
        max_open_positions=3
    )
    
    # Test Case 1: Reproduce the issue from the problem statement
    print("\n📊 Test Case 1: Small balance ($16.65) with 12x leverage")
    print("="*70)
    balance = 16.65
    # Using realistic price and tight stop loss that would cause large positions
    entry_price = 8.71
    stop_loss_price = entry_price * 0.988  # Stop loss distance: 1.2% below entry
    leverage = 12
    
    size = manager.calculate_position_size(balance, entry_price, stop_loss_price, leverage)
    position_value = size * entry_price
    required_margin = position_value / leverage
    required_margin_with_buffer = required_margin * FEE_BUFFER
    
    print(f"  Balance: ${balance:.2f}")
    print(f"  Entry Price: ${entry_price:.2f}")
    print(f"  Stop Loss: ${stop_loss_price:.2f} ({abs(entry_price - stop_loss_price) / entry_price * 100:.2f}% distance)")
    print(f"  Leverage: {leverage}x")
    print(f"  Calculated Position Size: {size:.4f} contracts")
    print(f"  Position Value: ${position_value:.2f}")
    print(f"  Required Margin: ${required_margin:.2f}")
    print(f"  Required Margin (with 5% buffer): ${required_margin_with_buffer:.2f}")
    print(f"  Available Margin: ${balance:.2f}")
    print(f"  Margin Check: {'✅ PASS' if required_margin_with_buffer <= balance else '❌ FAIL'}")
    
    assert required_margin_with_buffer <= balance, \
        f"Position requires ${required_margin_with_buffer:.2f} but only ${balance:.2f} available!"
    print(f"  ✓ Position size fits within available margin")
    
    # Test Case 2: Verify with different leverage (6x)
    print("\n📊 Test Case 2: Same balance with 6x leverage")
    print("="*70)
    leverage = 6
    size = manager.calculate_position_size(balance, entry_price, stop_loss_price, leverage)
    position_value = size * entry_price
    required_margin = position_value / leverage
    required_margin_with_buffer = required_margin * FEE_BUFFER
    
    print(f"  Balance: ${balance:.2f}")
    print(f"  Leverage: {leverage}x")
    print(f"  Calculated Position Size: {size:.4f} contracts")
    print(f"  Position Value: ${position_value:.2f}")
    print(f"  Required Margin: ${required_margin:.2f}")
    print(f"  Required Margin (with 5% buffer): ${required_margin_with_buffer:.2f}")
    print(f"  Margin Check: {'✅ PASS' if required_margin_with_buffer <= balance else '❌ FAIL'}")
    
    assert required_margin_with_buffer <= balance, \
        f"Position requires ${required_margin_with_buffer:.2f} but only ${balance:.2f} available!"
    print(f"  ✓ Position size fits within available margin")
    
    # Test Case 3: Larger balance
    print("\n📊 Test Case 3: Larger balance ($100) with 10x leverage")
    print("="*70)
    balance = 100.0
    leverage = 10
    entry_price = 50000.0  # BTC-like price
    stop_loss_price = entry_price * 0.985  # 1.5% stop loss
    
    size = manager.calculate_position_size(balance, entry_price, stop_loss_price, leverage)
    position_value = size * entry_price
    required_margin = position_value / leverage
    required_margin_with_buffer = required_margin * FEE_BUFFER
    
    print(f"  Balance: ${balance:.2f}")
    print(f"  Entry Price: ${entry_price:.2f}")
    print(f"  Stop Loss: ${stop_loss_price:.2f} ({abs(entry_price - stop_loss_price) / entry_price * 100:.2f}% distance)")
    print(f"  Leverage: {leverage}x")
    print(f"  Calculated Position Size: {size:.6f} contracts")
    print(f"  Position Value: ${position_value:.2f}")
    print(f"  Required Margin: ${required_margin:.2f}")
    print(f"  Required Margin (with 5% buffer): ${required_margin_with_buffer:.2f}")
    print(f"  Margin Check: {'✅ PASS' if required_margin_with_buffer <= balance else '❌ FAIL'}")
    
    assert required_margin_with_buffer <= balance, \
        f"Position requires ${required_margin_with_buffer:.2f} but only ${balance:.2f} available!"
    print(f"  ✓ Position size fits within available margin")
    
    # Test Case 4: Very tight stop loss (should be capped by margin)
    print("\n📊 Test Case 4: Very tight stop loss (0.5%) with small balance")
    print("="*70)
    balance = 20.0
    leverage = 8
    entry_price = 100.0
    stop_loss_price = entry_price * 0.995  # 0.5% stop loss (very tight)
    
    size = manager.calculate_position_size(balance, entry_price, stop_loss_price, leverage)
    position_value = size * entry_price
    required_margin = position_value / leverage
    required_margin_with_buffer = required_margin * FEE_BUFFER
    
    print(f"  Balance: ${balance:.2f}")
    print(f"  Entry Price: ${entry_price:.2f}")
    print(f"  Stop Loss: ${stop_loss_price:.2f} ({abs(entry_price - stop_loss_price) / entry_price * 100:.2f}% distance)")
    print(f"  Leverage: {leverage}x")
    print(f"  Risk per trade: {manager.risk_per_trade * 100:.1f}%")
    print(f"  Calculated Position Size: {size:.4f} contracts")
    print(f"  Position Value: ${position_value:.2f}")
    print(f"  Required Margin: ${required_margin:.2f}")
    print(f"  Required Margin (with 5% buffer): ${required_margin_with_buffer:.2f}")
    print(f"  Margin Check: {'✅ PASS' if required_margin_with_buffer <= balance else '❌ FAIL'}")
    
    assert required_margin_with_buffer <= balance, \
        f"Position requires ${required_margin_with_buffer:.2f} but only ${balance:.2f} available!"
    print(f"  ✓ Position size properly capped by available margin despite tight stop loss")
    
    print("\n" + "="*70)
    print("✅ All tests passed! Position sizing now respects margin constraints")
    print("="*70)
    return True


if __name__ == "__main__":
    try:
        success = test_position_size_respects_margin_with_leverage()
        if success:
            print("\n🎉 SUCCESS: Margin calculation fix is working correctly!")
            exit(0)
        else:
            print("\n❌ FAILURE: Test did not complete successfully")
            exit(1)
    except AssertionError as e:
        print(f"\n❌ ASSERTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
