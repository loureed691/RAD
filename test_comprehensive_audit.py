#!/usr/bin/env python3
"""
Comprehensive Bot Audit - Collisions, API Usage, and Calculations
Tests all critical bot functions for correctness
"""
import sys

def test_no_function_collisions():
    """Test 1: Verify no duplicate/colliding function implementations"""
    print("\n" + "="*80)
    print("TEST 1: Function Collisions Check")
    print("="*80)
    
    issues_found = []
    
    # 1.1: Kelly Criterion - should only be in risk_manager, not ml_model
    try:
        from risk_manager import RiskManager
        from ml_model import MLModel
        
        # Check risk_manager has Kelly
        if not hasattr(RiskManager, 'calculate_kelly_criterion'):
            issues_found.append("❌ RiskManager missing calculate_kelly_criterion method")
        else:
            print("✓ RiskManager has calculate_kelly_criterion")
        
        # Check ml_model doesn't have Kelly (this was removed in collision resolution)
        if hasattr(MLModel, 'get_kelly_fraction'):
            issues_found.append("❌ MLModel still has get_kelly_fraction - should be removed (collision)")
        else:
            print("✓ MLModel doesn't have get_kelly_fraction (collision resolved)")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking Kelly Criterion: {e}")
    
    # 1.2: Risk adjustment - should not have compounding adjustments
    try:
        from risk_manager import RiskManager
        import inspect
        
        # Check if adjust_risk_for_conditions is called in position sizing
        source = inspect.getsource(RiskManager.calculate_position_size)
        if 'adjust_risk_for_conditions' in source:
            issues_found.append("❌ calculate_position_size calls adjust_risk_for_conditions - potential compounding")
        else:
            print("✓ No risk adjustment compounding in calculate_position_size")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking risk adjustment: {e}")
    
    # 1.3: Position sizing - verify single implementation
    try:
        from risk_manager import RiskManager
        from position_manager import PositionManager
        
        # PositionManager should NOT have position sizing logic
        if hasattr(PositionManager, 'calculate_position_size'):
            issues_found.append("❌ PositionManager has calculate_position_size - should only be in RiskManager")
        else:
            print("✓ Position sizing is only in RiskManager")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking position sizing: {e}")
    
    # 1.4: Thread safety - verify locks are used correctly
    try:
        from position_manager import PositionManager
        import inspect
        
        source = inspect.getsource(PositionManager)
        
        # Should have a lock
        if '_positions_lock' not in source:
            issues_found.append("❌ PositionManager missing _positions_lock for thread safety")
        else:
            print("✓ PositionManager has thread lock")
            
        # Lock should be used when accessing positions dict
        if 'with self._positions_lock:' not in source:
            issues_found.append("⚠️  Warning: _positions_lock may not be used consistently")
        else:
            print("✓ PositionManager uses lock for position access")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking thread safety: {e}")
    
    if issues_found:
        print("\n❌ FUNCTION COLLISION ISSUES FOUND:")
        for issue in issues_found:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ NO FUNCTION COLLISIONS DETECTED")
        return True


def test_kucoin_api_usage():
    """Test 2: Verify KuCoin API is used correctly"""
    print("\n" + "="*80)
    print("TEST 2: KuCoin API Usage Validation")
    print("="*80)
    
    issues_found = []
    
    # 2.1: Margin calculation formula
    try:
        from kucoin_client import KuCoinClient
        import inspect
        
        # Check margin calculation formula
        source = inspect.getsource(KuCoinClient.calculate_required_margin)
        
        # Should be: position_value / leverage
        # Where position_value = amount * price * contract_size
        if 'position_value = amount * price * contract_size' in source:
            print("✓ Position value calculation includes contract_size")
        else:
            issues_found.append("⚠️  Position value may not include contract_size")
        
        if 'required_margin = position_value / leverage' in source:
            print("✓ Margin calculation is position_value / leverage (correct)")
        else:
            issues_found.append("❌ Margin calculation formula may be incorrect")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking margin calculation: {e}")
    
    # 2.2: Division by zero protection
    try:
        from kucoin_client import KuCoinClient
        import inspect
        
        # Check for zero/negative price protection
        source = inspect.getsource(KuCoinClient.adjust_position_for_margin)
        
        if 'if price <= 0:' in source or 'if price == 0:' in source:
            print("✓ Division by zero protection for price")
        else:
            issues_found.append("❌ Missing division by zero protection for price")
        
        # Check for zero margin protection
        if 'available_margin <= 0' in source or 'available_margin < 0' in source:
            print("✓ Division by zero protection for margin")
        else:
            issues_found.append("⚠️  May be missing division by zero protection for margin")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking division by zero: {e}")
    
    # 2.3: API priority system
    try:
        from kucoin_client import KuCoinClient, APICallPriority
        import inspect
        
        # Check critical operations use CRITICAL priority
        create_order_source = inspect.getsource(KuCoinClient.create_market_order)
        
        if 'APICallPriority.CRITICAL' in create_order_source:
            print("✓ Order creation uses CRITICAL priority")
        else:
            issues_found.append("❌ Order creation may not use CRITICAL priority")
        
        # Check scanning operations use lower priority
        get_ohlcv_source = inspect.getsource(KuCoinClient.get_ohlcv)
        
        if 'APICallPriority.NORMAL' in get_ohlcv_source or 'APICallPriority.LOW' in get_ohlcv_source:
            print("✓ Market scanning uses non-critical priority")
        else:
            issues_found.append("⚠️  Market scanning priority may be too high")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking API priority: {e}")
    
    # 2.4: Order book imbalance - check for division by zero
    try:
        from risk_manager import RiskManager
        import inspect
        
        source = inspect.getsource(RiskManager.analyze_order_book_imbalance)
        
        # Should check if best_bid is zero before dividing
        if 'if best_bid == 0:' in source or 'if best_bid <= 0:' in source:
            print("✓ Order book analysis has division by zero protection")
        else:
            issues_found.append("❌ Order book analysis missing zero price check")
            
        # Should check if total_volume is zero
        if 'if total_volume == 0:' in source or 'if total_volume <= 0:' in source:
            print("✓ Order book analysis has zero volume check")
        else:
            issues_found.append("⚠️  Order book analysis may be missing zero volume check")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking order book analysis: {e}")
    
    if issues_found:
        print("\n❌ API USAGE ISSUES FOUND:")
        for issue in issues_found:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ API USAGE APPEARS CORRECT")
        return True


def test_calculation_correctness():
    """Test 3: Verify all number calculations are correct"""
    print("\n" + "="*80)
    print("TEST 3: Number Calculation Validation")
    print("="*80)
    
    issues_found = []
    
    # 3.1: P&L calculation - should NOT multiply by leverage
    try:
        from position_manager import Position
        import inspect
        
        source = inspect.getsource(Position.get_pnl)
        
        # Should NOT have leverage multiplication (this was a bug that was fixed)
        if '* leverage' in source or '* self.leverage' in source:
            issues_found.append("❌ CRITICAL: P&L calculation multiplies by leverage (bug reintroduced!)")
        else:
            print("✓ P&L calculation does NOT multiply by leverage (correct)")
        
        # Should be simple price change percentage
        if '(current_price - self.entry_price) / self.entry_price' in source:
            print("✓ Long P&L calculation is correct")
        else:
            issues_found.append("⚠️  Long P&L formula may be incorrect")
        
        if '(self.entry_price - current_price) / self.entry_price' in source:
            print("✓ Short P&L calculation is correct")
        else:
            issues_found.append("⚠️  Short P&L formula may be incorrect")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking P&L calculation: {e}")
    
    # 3.2: Position sizing calculation
    try:
        from risk_manager import RiskManager
        import inspect
        
        source = inspect.getsource(RiskManager.calculate_position_size)
        
        # Formula should be: position_value = risk_amount / price_distance
        # This is correct because: risk = position_value * price_distance
        if 'position_value = risk_amount / price_distance' in source:
            print("✓ Position sizing formula is correct")
        else:
            issues_found.append("⚠️  Position sizing formula may be non-standard")
        
        # Should check for zero price_distance
        if 'if price_distance > 0:' in source or 'if price_distance == 0:' in source:
            print("✓ Position sizing has zero distance protection")
        else:
            issues_found.append("❌ Position sizing missing zero distance check")
            
        # Should cap at max_position_size
        if 'min(position_value, self.max_position_size)' in source:
            print("✓ Position value is capped at maximum")
        else:
            issues_found.append("⚠️  Position value may not be capped")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking position sizing: {e}")
    
    # 3.3: Stop loss percentage calculation
    try:
        from risk_manager import RiskManager
        import inspect
        
        source = inspect.getsource(RiskManager.calculate_stop_loss_percentage)
        
        # Should be adaptive based on volatility
        if 'volatility' in source and ('*' in source or 'base_stop' in source):
            print("✓ Stop loss is adaptive to volatility")
        else:
            issues_found.append("⚠️  Stop loss may not be adaptive")
        
        # Should be capped at reasonable bounds
        if 'max(' in source and 'min(' in source:
            print("✓ Stop loss is capped at min/max bounds")
        else:
            issues_found.append("⚠️  Stop loss may not be capped")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking stop loss: {e}")
    
    # 3.4: Leverage calculation
    try:
        from risk_manager import RiskManager
        import inspect
        
        source = inspect.getsource(RiskManager.get_max_leverage)
        
        # Should consider multiple factors
        factors = ['volatility', 'confidence', 'momentum', 'trend_strength', 'market_regime']
        for factor in factors:
            if factor in source:
                print(f"✓ Leverage considers {factor}")
            else:
                issues_found.append(f"⚠️  Leverage may not consider {factor}")
        
        # Should be capped at reasonable max
        if 'min(' in source and ('20' in source or '25' in source):
            print("✓ Leverage is capped at maximum")
        else:
            issues_found.append("⚠️  Leverage may not be capped")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking leverage calculation: {e}")
    
    # 3.5: Floating point precision - tolerance checks
    try:
        from position_manager import Position
        import inspect
        
        source = inspect.getsource(Position.should_close)
        
        # Should use tolerance for TP checks (not exact equality)
        if '0.99999' in source or '1.00001' in source:
            print("✓ Take profit uses floating point tolerance")
        else:
            issues_found.append("⚠️  Take profit may use exact equality (precision issue)")
            
    except Exception as e:
        issues_found.append(f"❌ Error checking floating point precision: {e}")
    
    # 3.6: Percentage/decimal consistency
    try:
        from risk_manager import RiskManager
        
        # Test with sample data
        manager = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
        
        # Test Kelly calculation
        kelly = manager.calculate_kelly_criterion(0.6, 0.05, 0.03, use_fractional=True)
        
        # Kelly should be between 0 and 1 (0-100%)
        if 0 <= kelly <= 1:
            print(f"✓ Kelly Criterion returns valid percentage: {kelly:.4f}")
        else:
            issues_found.append(f"❌ Kelly Criterion returns invalid value: {kelly}")
        
        # Test stop loss calculation
        stop_loss = manager.calculate_stop_loss_percentage(0.03)
        
        # Stop loss should be between 0.01 and 0.1 (1-10%)
        if 0.01 <= stop_loss <= 0.1:
            print(f"✓ Stop loss returns valid percentage: {stop_loss:.4f}")
        else:
            issues_found.append(f"❌ Stop loss returns invalid value: {stop_loss}")
            
    except Exception as e:
        issues_found.append(f"❌ Error testing calculation values: {e}")
    
    if issues_found:
        print("\n❌ CALCULATION ISSUES FOUND:")
        for issue in issues_found:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ ALL CALCULATIONS APPEAR CORRECT")
        return True


def test_edge_cases():
    """Test 4: Verify edge case handling"""
    print("\n" + "="*80)
    print("TEST 4: Edge Case Validation")
    print("="*80)
    
    issues_found = []
    
    try:
        from risk_manager import RiskManager
        from position_manager import Position
        
        manager = RiskManager(max_position_size=1000, risk_per_trade=0.02, max_open_positions=3)
        
        # 4.1: Zero balance
        try:
            size = manager.calculate_position_size(0, 100, 95, 10)
            if size == 0:
                print("✓ Zero balance handled correctly")
            else:
                issues_found.append(f"⚠️  Zero balance returned non-zero size: {size}")
        except Exception as e:
            issues_found.append(f"❌ Zero balance throws exception: {e}")
        
        # 4.2: Zero price distance (entry == stop loss)
        try:
            size = manager.calculate_position_size(1000, 100, 100, 10)
            # Should either return 0 or max_position_size as fallback
            print(f"✓ Zero price distance handled: size={size:.2f}")
        except Exception as e:
            issues_found.append(f"❌ Zero price distance throws exception: {e}")
        
        # 4.3: Negative price (should not happen but defensive)
        try:
            size = manager.calculate_position_size(1000, -100, -95, 10)
            print(f"⚠️  Negative price accepted: size={size:.2f}")
        except Exception as e:
            print(f"✓ Negative price rejected: {type(e).__name__}")
        
        # 4.4: Very high leverage
        try:
            leverage = manager.get_max_leverage(0.01, 0.9, 0.05, 0.8, 'trending')
            if leverage <= 25:
                print(f"✓ Max leverage capped at reasonable level: {leverage}x")
            else:
                issues_found.append(f"❌ Max leverage too high: {leverage}x")
        except Exception as e:
            issues_found.append(f"❌ Leverage calculation throws exception: {e}")
        
        # 4.5: Extreme volatility
        try:
            stop_loss = manager.calculate_stop_loss_percentage(1.0)  # 100% volatility
            if stop_loss <= 0.1:
                print(f"✓ Stop loss capped for extreme volatility: {stop_loss:.2%}")
            else:
                issues_found.append(f"❌ Stop loss too wide for extreme volatility: {stop_loss:.2%}")
        except Exception as e:
            issues_found.append(f"❌ Stop loss calculation throws exception: {e}")
        
        # 4.6: Position P&L at zero price
        try:
            pos = Position('BTC/USDT:USDT', 'long', 100, 1, 10, 95)
            pnl = pos.get_pnl(0)  # Current price is 0
            # Should handle gracefully (return large negative) or throw
            print(f"⚠️  Zero current price handled: pnl={pnl:.2f}")
        except Exception as e:
            print(f"✓ Zero current price handled: {type(e).__name__}")
            
    except Exception as e:
        issues_found.append(f"❌ Error in edge case testing: {e}")
    
    if issues_found:
        print("\n❌ EDGE CASE ISSUES FOUND:")
        for issue in issues_found:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ EDGE CASES HANDLED CORRECTLY")
        return True


def test_api_improvements():
    """Test 5: Verify API can be improved"""
    print("\n" + "="*80)
    print("TEST 5: API Usage Optimization Check")
    print("="*80)
    
    suggestions = []
    
    # 5.1: Check if order book depth is validated before placing orders
    try:
        from kucoin_client import KuCoinClient
        import inspect
        
        source = inspect.getsource(KuCoinClient.create_market_order)
        
        if 'validate_depth' in source:
            print("✓ Order book depth validation is optional (good)")
        else:
            suggestions.append("💡 Consider adding order book depth validation to prevent slippage")
            
        if 'max_slippage' in source:
            print("✓ Slippage limit is configurable")
        else:
            suggestions.append("💡 Consider adding configurable slippage limits")
            
    except Exception as e:
        suggestions.append(f"⚠️  Could not check order validation: {e}")
    
    # 5.2: Check if there's retry logic for failed API calls
    try:
        from kucoin_client import KuCoinClient
        import inspect
        
        source = inspect.getsource(KuCoinClient.get_ohlcv)
        
        if 'max_retries' in source or 'for attempt in' in source:
            print("✓ API calls have retry logic")
        else:
            suggestions.append("💡 Consider adding retry logic for transient API failures")
            
    except Exception as e:
        suggestions.append(f"⚠️  Could not check retry logic: {e}")
    
    # 5.3: Check if rate limiting is properly configured
    try:
        from kucoin_client import KuCoinClient
        import inspect
        
        source = inspect.getsource(KuCoinClient.__init__)
        
        if 'enableRateLimit' in source and 'True' in source:
            print("✓ CCXT rate limiting is enabled")
        else:
            suggestions.append("💡 Consider enabling CCXT built-in rate limiting")
            
    except Exception as e:
        suggestions.append(f"⚠️  Could not check rate limiting: {e}")
    
    # 5.4: Check if position mode is set correctly
    try:
        from kucoin_client import KuCoinClient
        import inspect
        
        source = inspect.getsource(KuCoinClient.__init__)
        
        if 'set_position_mode' in source:
            print("✓ Position mode is explicitly set (prevents errors)")
        else:
            suggestions.append("💡 Consider explicitly setting position mode to prevent API errors")
            
    except Exception as e:
        suggestions.append(f"⚠️  Could not check position mode: {e}")
    
    if suggestions:
        print("\n💡 API IMPROVEMENT SUGGESTIONS:")
        for suggestion in suggestions:
            print(f"  {suggestion}")
        return True
    else:
        print("\n✅ API USAGE IS WELL OPTIMIZED")
        return True


def main():
    """Run all audit tests"""
    print("\n" + "="*80)
    print("COMPREHENSIVE BOT AUDIT")
    print("Checking Collisions, API Usage, and Calculations")
    print("="*80)
    
    results = {}
    
    # Run all tests
    results['collisions'] = test_no_function_collisions()
    results['api_usage'] = test_kucoin_api_usage()
    results['calculations'] = test_calculation_correctness()
    results['edge_cases'] = test_edge_cases()
    results['improvements'] = test_api_improvements()
    
    # Summary
    print("\n" + "="*80)
    print("AUDIT SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\n{passed}/{total} test categories passed")
    
    if passed == total:
        print("\n✅ ALL AUDITS PASSED - Bot appears to be functioning correctly!")
        return 0
    else:
        print("\n⚠️  SOME ISSUES FOUND - Review output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
