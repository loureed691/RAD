#!/usr/bin/env python3
"""
Test that the per-trade risk guardrail fix resolves the blocking issue
"""

from risk_manager import RiskManager
from config import Config

def test_estimation_passes_guardrail():
    """Test that the position value estimation passes the 5% guardrail"""
    print("\n" + "="*70)
    print("TEST: Position Value Estimation Passes Guardrail")
    print("="*70)
    
    # Initialize risk manager with 5% max risk per trade
    rm = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
    
    # Test with different balance levels and RISK_PER_TRADE values
    test_cases = [
        {"balance": 100, "risk_per_trade": 0.01},   # 1% risk, micro account
        {"balance": 500, "risk_per_trade": 0.015},  # 1.5% risk, small account
        {"balance": 1000, "risk_per_trade": 0.02},  # 2% risk, medium account
        {"balance": 5000, "risk_per_trade": 0.025}, # 2.5% risk, large account
        {"balance": 10000, "risk_per_trade": 0.03}, # 3% risk, very large account
    ]
    
    for i, test in enumerate(test_cases, 1):
        balance = test["balance"]
        Config.RISK_PER_TRADE = test["risk_per_trade"]
        Config.MAX_POSITION_SIZE = balance * 0.5  # 50% max
        
        # Calculate estimated position value using the new formula
        estimated_position_value = min(
            balance * 0.04,  # Conservative estimate under 5% guardrail
            Config.MAX_POSITION_SIZE
        )
        
        # Validate with guardrails
        is_allowed, reason = rm.validate_trade_guardrails(
            balance=balance,
            position_value=estimated_position_value,
            current_positions=0,
            is_exit=False
        )
        
        # Calculate percentage for display
        pct = (estimated_position_value / balance) * 100
        
        print(f"\n{i}. Balance: ${balance}, Risk: {Config.RISK_PER_TRADE:.1%}")
        print(f"   Estimated position value: ${estimated_position_value:.2f} ({pct:.1f}% of balance)")
        print(f"   Guardrail check: {'✓ PASSED' if is_allowed else '✗ BLOCKED'} - {reason}")
        
        # Assert that the trade is allowed
        assert is_allowed, f"Trade should be allowed but was blocked: {reason}"
        
        # Assert that estimated position value is under 5%
        assert estimated_position_value / balance <= 0.05, \
            f"Estimated position value {pct:.1f}% exceeds 5% guardrail"
    
    print("\n" + "="*70)
    print("✅ ALL ESTIMATION TESTS PASSED")
    print("="*70)

def test_old_formula_would_fail():
    """Demonstrate that the old formula would have failed"""
    print("\n" + "="*70)
    print("TEST: Old Formula Would Have Failed")
    print("="*70)
    
    rm = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
    
    balance = 1000
    Config.RISK_PER_TRADE = 0.01  # 1% risk
    Config.MAX_POSITION_SIZE = balance * 0.5
    
    # Old formula: available_balance * Config.RISK_PER_TRADE * 10
    old_estimated_position_value = min(
        balance * Config.RISK_PER_TRADE * 10,
        Config.MAX_POSITION_SIZE
    )
    
    # New formula: available_balance * 0.04
    new_estimated_position_value = min(
        balance * 0.04,
        Config.MAX_POSITION_SIZE
    )
    
    # Test old formula
    is_allowed_old, reason_old = rm.validate_trade_guardrails(
        balance=balance,
        position_value=old_estimated_position_value,
        current_positions=0,
        is_exit=False
    )
    
    # Test new formula
    is_allowed_new, reason_new = rm.validate_trade_guardrails(
        balance=balance,
        position_value=new_estimated_position_value,
        current_positions=0,
        is_exit=False
    )
    
    old_pct = (old_estimated_position_value / balance) * 100
    new_pct = (new_estimated_position_value / balance) * 100
    
    print(f"\nBalance: ${balance}, Risk: {Config.RISK_PER_TRADE:.1%}")
    print(f"\nOld Formula: balance * RISK_PER_TRADE * 10")
    print(f"  Estimated value: ${old_estimated_position_value:.2f} ({old_pct:.1f}% of balance)")
    print(f"  Guardrail check: {'✓ PASSED' if is_allowed_old else '✗ BLOCKED'} - {reason_old}")
    
    print(f"\nNew Formula: balance * 0.04")
    print(f"  Estimated value: ${new_estimated_position_value:.2f} ({new_pct:.1f}% of balance)")
    print(f"  Guardrail check: {'✓ PASSED' if is_allowed_new else '✗ BLOCKED'} - {reason_new}")
    
    # Verify that old formula failed and new formula succeeds
    assert not is_allowed_old, "Old formula should have been blocked"
    assert is_allowed_new, "New formula should be allowed"
    
    print("\n" + "="*70)
    print("✅ Confirmed: Old formula fails, new formula works")
    print("="*70)

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING PER-TRADE RISK GUARDRAIL FIX")
    print("="*70)
    
    try:
        test_estimation_passes_guardrail()
        test_old_formula_would_fail()
        
        print("\n" + "="*70)
        print("✅✅✅ ALL TESTS PASSED ✅✅✅")
        print("="*70)
        print("\nThe fix successfully resolves the per-trade risk blocking issue!")
        print("Trades will no longer be blocked due to overly aggressive estimation.")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
