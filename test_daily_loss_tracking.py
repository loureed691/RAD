"""
Test daily loss tracking functionality
"""
import sys
import os
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_daily_loss_tracking():
    """Test that daily loss is properly tracked and enforced"""
    print("\nTesting daily loss tracking...")
    
    from risk_manager import RiskManager
    
    # Create risk manager
    risk_mgr = RiskManager(
        max_position_size=1000,
        risk_per_trade=0.02,
        max_open_positions=3
    )
    
    # Verify initial state
    assert risk_mgr.daily_loss == 0.0, "Daily loss should start at 0"
    assert risk_mgr.daily_loss_limit == 0.10, "Daily loss limit should be 10%"
    print(f"  ✓ Initial daily loss: {risk_mgr.daily_loss:.2%}")
    print(f"  ✓ Daily loss limit: {risk_mgr.daily_loss_limit:.2%}")
    
    # Record some losses
    risk_mgr.record_trade_outcome(-0.02)  # -2% loss
    assert risk_mgr.daily_loss == 0.02, f"Expected daily_loss=0.02, got {risk_mgr.daily_loss}"
    print(f"  ✓ After -2% loss: daily_loss = {risk_mgr.daily_loss:.2%}")
    
    risk_mgr.record_trade_outcome(-0.03)  # -3% loss
    assert risk_mgr.daily_loss == 0.05, f"Expected daily_loss=0.05, got {risk_mgr.daily_loss}"
    print(f"  ✓ After -3% loss: daily_loss = {risk_mgr.daily_loss:.2%}")
    
    # Verify wins don't affect daily loss
    risk_mgr.record_trade_outcome(0.04)  # +4% win
    assert risk_mgr.daily_loss == 0.05, f"Win should not affect daily_loss, got {risk_mgr.daily_loss}"
    print(f"  ✓ After +4% win: daily_loss unchanged = {risk_mgr.daily_loss:.2%}")
    
    # Add more losses to reach limit
    risk_mgr.record_trade_outcome(-0.06)  # -6% loss
    assert risk_mgr.daily_loss == 0.11, f"Expected daily_loss=0.11, got {risk_mgr.daily_loss}"
    print(f"  ✓ After -6% loss: daily_loss = {risk_mgr.daily_loss:.2%}")
    
    # Check that daily loss limit prevents trading
    should_open, reason = risk_mgr.should_open_position(0, 1000)
    assert not should_open, "Should not open position when daily loss limit reached"
    assert "Daily loss limit" in reason, f"Reason should mention daily loss limit: {reason}"
    print(f"  ✓ Daily loss limit enforced: {reason}")
    
    # Verify guardrails also block trading
    is_allowed, block_reason = risk_mgr.validate_trade_guardrails(
        balance=1000,
        position_value=100,
        current_positions=0,
        is_exit=False
    )
    assert not is_allowed, "Guardrails should block trade when daily loss limit reached"
    assert "daily loss" in block_reason.lower(), f"Block reason should mention daily loss: {block_reason}"
    print(f"  ✓ Guardrails block trade: {block_reason}")
    
    print("✓ Daily loss tracking working correctly")
    return True

def test_daily_loss_reset():
    """Test that daily loss resets on new day"""
    print("\nTesting daily loss reset...")
    
    from risk_manager import RiskManager
    from datetime import date, timedelta
    
    # Create risk manager
    risk_mgr = RiskManager(
        max_position_size=1000,
        risk_per_trade=0.02,
        max_open_positions=3
    )
    
    # Set some daily loss
    risk_mgr.record_trade_outcome(-0.05)
    assert risk_mgr.daily_loss == 0.05
    print(f"  ✓ Daily loss set to: {risk_mgr.daily_loss:.2%}")
    
    # Simulate day change by modifying trading_date
    risk_mgr.trading_date = date.today() - timedelta(days=1)
    
    # Save and reload state (this triggers the day check)
    risk_mgr.save_state()
    
    # Load state (should reset daily values)
    risk_mgr.load_state()
    
    # Verify reset
    assert risk_mgr.daily_loss == 0.0, f"Daily loss should reset on new day, got {risk_mgr.daily_loss}"
    print(f"  ✓ Daily loss reset to: {risk_mgr.daily_loss:.2%}")
    
    print("✓ Daily loss reset working correctly")
    return True

def test_daily_start_balance():
    """Test that daily start balance is initialized"""
    print("\nTesting daily start balance initialization...")
    
    from risk_manager import RiskManager
    
    # Create risk manager
    risk_mgr = RiskManager(
        max_position_size=1000,
        risk_per_trade=0.02,
        max_open_positions=3
    )
    
    # Verify initial state
    assert risk_mgr.daily_start_balance == 0.0
    print(f"  ✓ Initial daily start balance: ${risk_mgr.daily_start_balance:.2f}")
    
    # Call update_drawdown to initialize
    risk_mgr.update_drawdown(5000.0)
    
    # Verify it was initialized
    assert risk_mgr.daily_start_balance == 5000.0, f"Expected $5000, got ${risk_mgr.daily_start_balance}"
    print(f"  ✓ Daily start balance initialized: ${risk_mgr.daily_start_balance:.2f}")
    
    # Call again with different balance - should not change
    risk_mgr.update_drawdown(5100.0)
    assert risk_mgr.daily_start_balance == 5000.0, "Daily start balance should not change once set"
    print(f"  ✓ Daily start balance remains: ${risk_mgr.daily_start_balance:.2f}")
    
    print("✓ Daily start balance initialization working correctly")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("DAILY LOSS TRACKING TESTS")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(test_daily_loss_tracking())
    except Exception as e:
        print(f"✗ Daily loss tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    try:
        results.append(test_daily_loss_reset())
    except Exception as e:
        print(f"✗ Daily loss reset test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    try:
        results.append(test_daily_start_balance())
    except Exception as e:
        print(f"✗ Daily start balance test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {len([r for r in results if not r])} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
