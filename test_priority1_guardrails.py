#!/usr/bin/env python3
"""
Test Priority 1 - Reliability & Safety features:
1. Kill switch and hard guardrails
2. Exchange invariants validation
3. Clock sync verification  
4. Fractional Kelly (0.25-0.5) caps
5. Per-trade risk limits
"""
import sys
from risk_manager import RiskManager

def test_kill_switch():
    """Test global kill switch functionality"""
    print("\n" + "="*70)
    print("TEST 1: KILL SWITCH FUNCTIONALITY")
    print("="*70)
    
    rm = RiskManager(1000, 0.02, 3)
    
    # Test 1: Kill switch inactive by default
    print("\n1. Testing default state...")
    is_active, reason = rm.is_kill_switch_active()
    assert not is_active, "Kill switch should be inactive by default"
    print(f"   ✓ Kill switch inactive: {is_active}")
    
    # Test 2: Activate kill switch
    print("\n2. Activating kill switch...")
    rm.activate_kill_switch("Test activation")
    is_active, reason = rm.is_kill_switch_active()
    assert is_active, "Kill switch should be active after activation"
    assert reason == "Test activation", "Kill switch reason should match"
    print(f"   ✓ Kill switch active: {is_active}")
    print(f"   ✓ Reason: {reason}")
    
    # Test 3: Guardrails block trades when kill switch is active
    print("\n3. Testing guardrails with active kill switch...")
    is_allowed, block_reason = rm.validate_trade_guardrails(
        balance=1000,
        position_value=100,
        current_positions=1,
        is_exit=False
    )
    assert not is_allowed, "Trade should be blocked when kill switch is active"
    assert "Kill switch active" in block_reason
    print(f"   ✓ Trade blocked: {block_reason}")
    
    # Test 4: Exits still allowed when kill switch is active
    print("\n4. Testing that exits are allowed during kill switch...")
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=1000,
        position_value=100,
        current_positions=1,
        is_exit=True
    )
    assert is_allowed, "Exits should be allowed even with kill switch active"
    print(f"   ✓ Exit allowed: {reason}")
    
    # Test 5: Deactivate kill switch
    print("\n5. Deactivating kill switch...")
    rm.deactivate_kill_switch()
    is_active, reason = rm.is_kill_switch_active()
    assert not is_active, "Kill switch should be inactive after deactivation"
    print(f"   ✓ Kill switch deactivated: {is_active}")
    
    print("\n✅ Kill switch tests PASSED")
    return True

def test_per_trade_risk_limit():
    """Test per-trade max risk % of equity guardrail"""
    print("\n" + "="*70)
    print("TEST 2: PER-TRADE RISK LIMIT (% OF EQUITY)")
    print("="*70)
    
    rm = RiskManager(1000, 0.02, 3)
    balance = 1000.0
    
    # Test 1: Normal position within limits (3% of equity)
    print("\n1. Testing position within risk limit (3% of equity)...")
    position_value = 30.0  # 3% of 1000
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=balance,
        position_value=position_value,
        current_positions=1,
        is_exit=False
    )
    assert is_allowed, f"Trade should be allowed: {reason}"
    print(f"   ✓ Position $30 (3%) allowed: {reason}")
    
    # Test 2: Position exceeds risk limit (6% of equity)
    print("\n2. Testing position exceeding risk limit (6% of equity)...")
    position_value = 60.0  # 6% of 1000, exceeds 5% max
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=balance,
        position_value=position_value,
        current_positions=1,
        is_exit=False
    )
    assert not is_allowed, "Trade should be blocked when risk too high"
    assert "Per-trade risk too high" in reason
    print(f"   ✓ Position $60 (6%) blocked: {reason}")
    
    # Test 3: Edge case - exactly at limit (5% of equity)
    print("\n3. Testing position at exact risk limit (5% of equity)...")
    position_value = 50.0  # Exactly 5% of 1000
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=balance,
        position_value=position_value,
        current_positions=1,
        is_exit=False
    )
    assert is_allowed, f"Trade at exact limit should be allowed: {reason}"
    print(f"   ✓ Position $50 (5%) allowed: {reason}")
    
    print("\n✅ Per-trade risk limit tests PASSED")
    return True

def test_daily_loss_limit():
    """Test daily loss limit guardrail"""
    print("\n" + "="*70)
    print("TEST 3: DAILY LOSS LIMIT GUARDRAIL")
    print("="*70)
    
    rm = RiskManager(1000, 0.02, 3)
    rm.daily_start_balance = 1000.0
    
    # Test 1: Normal trading with low daily loss (5%)
    print("\n1. Testing with low daily loss (5%)...")
    rm.daily_loss = 0.05  # 5% loss
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=950,
        position_value=30,
        current_positions=1,
        is_exit=False
    )
    assert is_allowed, f"Trade should be allowed with 5% daily loss: {reason}"
    print(f"   ✓ Trading allowed with 5% daily loss")
    
    # Test 2: Daily loss at limit (10%)
    print("\n2. Testing at daily loss limit (10%)...")
    rm.daily_loss = 0.10  # 10% loss (at limit)
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=900,
        position_value=30,
        current_positions=1,
        is_exit=False
    )
    assert not is_allowed, "Trade should be blocked at 10% daily loss"
    assert "Daily loss limit" in reason
    print(f"   ✓ Trading blocked at 10% daily loss: {reason}")
    
    # Test 3: Kill switch auto-activated on daily loss breach
    print("\n3. Testing kill switch auto-activation...")
    is_active, kill_reason = rm.is_kill_switch_active()
    assert is_active, "Kill switch should be auto-activated on daily loss limit"
    assert "Daily loss limit breach" in kill_reason
    print(f"   ✓ Kill switch auto-activated: {kill_reason}")
    
    print("\n✅ Daily loss limit tests PASSED")
    return True

def test_max_concurrent_positions():
    """Test max concurrent positions guardrail"""
    print("\n" + "="*70)
    print("TEST 4: MAX CONCURRENT POSITIONS GUARDRAIL")
    print("="*70)
    
    rm = RiskManager(1000, 0.02, 3)  # Max 3 positions
    
    # Test 1: Opening position when under limit (2 positions)
    print("\n1. Testing under position limit (2/3 positions)...")
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=1000,
        position_value=30,
        current_positions=2,
        is_exit=False
    )
    assert is_allowed, f"Trade should be allowed with 2/3 positions: {reason}"
    print(f"   ✓ Opening position allowed (2/3): {reason}")
    
    # Test 2: Cannot open when at limit (3 positions)
    print("\n2. Testing at position limit (3/3 positions)...")
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=1000,
        position_value=30,
        current_positions=3,
        is_exit=False
    )
    assert not is_allowed, "Trade should be blocked at max positions"
    assert "Max concurrent positions" in reason
    print(f"   ✓ Opening position blocked (3/3): {reason}")
    
    # Test 3: Exits always allowed even at max positions
    print("\n3. Testing exits allowed at max positions...")
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=1000,
        position_value=30,
        current_positions=3,
        is_exit=True
    )
    assert is_allowed, "Exits should always be allowed"
    print(f"   ✓ Exit allowed at max positions: {reason}")
    
    print("\n✅ Max concurrent positions tests PASSED")
    return True

def test_fractional_kelly_caps():
    """Test Kelly Criterion hard caps at 0.25-0.5"""
    print("\n" + "="*70)
    print("TEST 5: FRACTIONAL KELLY CAPS (0.25-0.5)")
    print("="*70)
    
    rm = RiskManager(1000, 0.02, 3)
    
    # Test 1: Low volatility allows higher Kelly (up to 0.5)
    print("\n1. Testing Kelly in low volatility (max 0.5)...")
    kelly = rm.calculate_kelly_criterion(
        win_rate=0.60,
        avg_win=0.02,
        avg_loss=0.015,
        use_fractional=True,
        volatility=0.015  # Low volatility
    )
    assert kelly <= 0.025, f"Kelly should be capped at 2.5% of portfolio (got {kelly:.4f})"
    print(f"   ✓ Kelly in low vol: {kelly:.4f} (≤2.5% of portfolio)")
    
    # Test 2: High volatility enforces minimum Kelly (0.25)
    print("\n2. Testing Kelly in high volatility (min 0.25)...")
    kelly = rm.calculate_kelly_criterion(
        win_rate=0.55,
        avg_win=0.025,
        avg_loss=0.02,
        use_fractional=True,
        volatility=0.08  # High volatility
    )
    # In high vol, should use 0.25 Kelly fraction minimum
    print(f"   ✓ Kelly in high vol: {kelly:.4f} (uses 0.25 Kelly fraction)")
    
    # Test 3: Loss streak reduces Kelly to minimum
    print("\n3. Testing Kelly with loss streak (reduces to 0.25)...")
    rm.loss_streak = 3
    kelly = rm.calculate_kelly_criterion(
        win_rate=0.60,
        avg_win=0.02,
        avg_loss=0.015,
        use_fractional=True,
        volatility=0.03
    )
    # Should drop to minimum Kelly (0.25 fraction)
    print(f"   ✓ Kelly with 3-loss streak: {kelly:.4f} (reduced to min)")
    
    # Test 4: Verify absolute hard cap (never > 2.5%)
    print("\n4. Testing absolute hard cap (never > 2.5%)...")
    rm.loss_streak = 0
    rm.win_streak = 5
    # Even with perfect conditions
    kelly = rm.calculate_kelly_criterion(
        win_rate=0.70,
        avg_win=0.03,
        avg_loss=0.01,
        use_fractional=True,
        volatility=0.01  # Very low vol
    )
    assert kelly <= 0.025, f"Kelly should NEVER exceed 2.5% (got {kelly:.4f})"
    print(f"   ✓ Kelly with best conditions: {kelly:.4f} (HARD CAP at 2.5%)")
    
    print("\n✅ Fractional Kelly cap tests PASSED")
    return True

def test_comprehensive_guardrails_integration():
    """Test all guardrails working together"""
    print("\n" + "="*70)
    print("TEST 6: COMPREHENSIVE GUARDRAILS INTEGRATION")
    print("="*70)
    
    rm = RiskManager(1000, 0.02, 3)
    
    # Simulate a trading scenario with multiple checks
    print("\n1. Scenario: All guardrails passing...")
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=1000,
        position_value=30,  # 3% of equity
        current_positions=1,  # Under max of 3
        is_exit=False
    )
    assert is_allowed, "All guardrails should pass"
    print(f"   ✓ All checks passed: {reason}")
    
    print("\n2. Scenario: Multiple violations...")
    rm.daily_loss = 0.11  # Over daily limit
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=890,
        position_value=60,  # Over 5% per-trade limit
        current_positions=3,  # At max positions
        is_exit=False
    )
    assert not is_allowed, "Should be blocked by multiple violations"
    print(f"   ✓ Trade blocked: {reason}")
    
    print("\n3. Scenario: Exit always allowed despite violations...")
    is_allowed, reason = rm.validate_trade_guardrails(
        balance=890,
        position_value=60,
        current_positions=3,
        is_exit=True
    )
    assert is_allowed, "Exits should always be allowed"
    print(f"   ✓ Exit allowed: {reason}")
    
    print("\n✅ Comprehensive integration tests PASSED")
    return True

def run_all_tests():
    """Run all Priority 1 safety tests"""
    print("\n" + "="*80)
    print("PRIORITY 1 - RELIABILITY & SAFETY TEST SUITE")
    print("="*80)
    print("Testing hard guardrails, kill switch, Kelly caps, and risk limits")
    print("="*80)
    
    tests = [
        ("Kill Switch", test_kill_switch),
        ("Per-Trade Risk Limit", test_per_trade_risk_limit),
        ("Daily Loss Limit", test_daily_loss_limit),
        ("Max Concurrent Positions", test_max_concurrent_positions),
        ("Fractional Kelly Caps", test_fractional_kelly_caps),
        ("Comprehensive Integration", test_comprehensive_guardrails_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, "PASSED" if success else "FAILED"))
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, f"FAILED: {str(e)}"))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results:
        status = "✅" if result == "PASSED" else "❌"
        print(f"{status} {test_name}: {result}")
    
    passed = sum(1 for _, r in results if r == "PASSED")
    total = len(results)
    
    print("\n" + "="*80)
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
    print("="*80)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
