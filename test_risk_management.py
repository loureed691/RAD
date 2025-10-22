#!/usr/bin/env python3
"""
Test the risk management and order execution enhancements
"""
import sys
from risk_manager import RiskManager

class MockPosition:
    """Mock position for testing"""
    def __init__(self, symbol, side, entry_price, amount, stop_loss):
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.amount = amount
        self.stop_loss = stop_loss

def test_portfolio_heat():
    """Test portfolio heat calculation"""
    print("\n" + "="*70)
    print("TESTING PORTFOLIO HEAT CALCULATION")
    print("="*70)
    
    rm = RiskManager(1000, 0.02, 3)
    
    # Test with no positions
    print("\n1. Empty Portfolio...")
    heat0 = rm.get_portfolio_heat([])
    print(f"   Positions: 0")
    print(f"   Portfolio Heat: ${heat0:.2f}")
    assert heat0 == 0.0, "Empty portfolio should have 0 heat"
    print("   ✓ Empty portfolio handled correctly")
    
    # Test with one position
    print("\n2. Single Position...")
    positions1 = [
        MockPosition('BTC/USDT:USDT', 'long', 50000, 0.1, 48000)
    ]
    heat1 = rm.get_portfolio_heat(positions1)
    print(f"   Position: BTC long, entry $50,000, SL $48,000")
    risk_pct = (50000 - 48000) / 50000 * 100
    print(f"   Risk per position: {risk_pct:.1f}% = ${(50000-48000)/50000 * 0.1 * 50000:.2f}")
    print(f"   Portfolio Heat: ${heat1:.2f}")
    assert heat1 > 0, "Should have positive heat"
    print("   ✓ Single position heat calculated")
    
    # Test with multiple positions
    print("\n3. Multiple Positions...")
    positions2 = [
        MockPosition('BTC/USDT:USDT', 'long', 50000, 0.1, 48000),
        MockPosition('ETH/USDT:USDT', 'long', 3000, 1.0, 2900),
        MockPosition('SOL/USDT:USDT', 'short', 100, 10, 105)
    ]
    heat2 = rm.get_portfolio_heat(positions2)
    print(f"   Positions: 3 (BTC, ETH, SOL)")
    print(f"   Portfolio Heat: ${heat2:.2f}")
    assert heat2 > heat1, "More positions should have higher heat"
    print("   ✓ Multiple position heat calculated")
    
    print("\n✓ All portfolio heat tests passed!")

def test_correlation_risk():
    """Test correlation risk checking"""
    print("\n" + "="*70)
    print("TESTING CORRELATION RISK MANAGEMENT")
    print("="*70)
    
    rm = RiskManager(1000, 0.02, 3)
    
    # Test with no positions
    print("\n1. Empty Portfolio (Any Asset Safe)...")
    safe, reason = rm.check_correlation_risk('BTC/USDT:USDT', [])
    print(f"   Open positions: None")
    print(f"   New symbol: BTC")
    print(f"   Safe to add: {safe}")
    assert safe, "Should be safe with no positions"
    print("   ✓ Empty portfolio allows any asset")
    
    # Test with one major coin
    print("\n2. One Major Coin (Another Major Safe)...")
    positions1 = [
        MockPosition('BTC/USDT:USDT', 'long', 50000, 0.1, 48000)
    ]
    safe, reason = rm.check_correlation_risk('ETH/USDT:USDT', positions1)
    print(f"   Open positions: BTC")
    print(f"   New symbol: ETH (same group)")
    print(f"   Safe to add: {safe}")
    assert safe, "Should allow 2 from same group"
    print("   ✓ Two assets from same group allowed")
    
    # Test with two major coins (third should be blocked)
    print("\n3. Two Major Coins (Third Blocked)...")
    positions2 = [
        MockPosition('BTC/USDT:USDT', 'long', 50000, 0.1, 48000),
        MockPosition('ETH/USDT:USDT', 'long', 3000, 1.0, 2900)
    ]
    safe, reason = rm.check_correlation_risk('BTC/USDT:USDT', positions2)
    print(f"   Open positions: BTC, ETH")
    print(f"   New symbol: BTC (3rd in same group)")
    print(f"   Safe to add: {safe}")
    print(f"   Reason: {reason}")
    assert not safe, "Should block 3rd from same group"
    print("   ✓ Third asset from same group correctly blocked")
    
    # Test with different groups
    print("\n4. Different Groups (Allowed)...")
    positions3 = [
        MockPosition('BTC/USDT:USDT', 'long', 50000, 0.1, 48000),
        MockPosition('ETH/USDT:USDT', 'long', 3000, 1.0, 2900)
    ]
    safe, reason = rm.check_correlation_risk('SOL/USDT:USDT', positions3)
    print(f"   Open positions: BTC (major), ETH (major)")
    print(f"   New symbol: SOL (layer1 group)")
    print(f"   Safe to add: {safe}")
    assert safe, "Should allow different groups"
    print("   ✓ Different correlation groups allowed")
    
    print("\n✓ All correlation risk tests passed!")

def test_risk_adjustment():
    """Test dynamic risk adjustment"""
    print("\n" + "="*70)
    print("TESTING DYNAMIC RISK ADJUSTMENT")
    print("="*70)
    
    rm = RiskManager(1000, 0.02, 3)
    base_risk = 0.02  # 2%
    
    # Test win streak adjustment
    print("\n1. Win Streak Adjustment...")
    rm.win_streak = 4
    rm.loss_streak = 0
    adjusted1 = rm.adjust_risk_for_conditions(base_risk, market_volatility=0.03, win_rate=0.5)
    print(f"   Base risk: {base_risk:.2%}")
    print(f"   Win streak: {rm.win_streak}")
    print(f"   Adjusted risk: {adjusted1:.2%}")
    print(f"   Change: {(adjusted1/base_risk - 1)*100:+.0f}%")
    assert adjusted1 > base_risk, "Win streak should increase risk"
    print("   ✓ Win streak increases risk")
    
    # Test loss streak adjustment
    print("\n2. Loss Streak Adjustment...")
    rm2 = RiskManager(1000, 0.02, 3)
    rm2.win_streak = 0
    rm2.loss_streak = 4
    adjusted2 = rm2.adjust_risk_for_conditions(base_risk, market_volatility=0.03, win_rate=0.5)
    print(f"   Base risk: {base_risk:.2%}")
    print(f"   Loss streak: {rm2.loss_streak}")
    print(f"   Adjusted risk: {adjusted2:.2%}")
    print(f"   Change: {(adjusted2/base_risk - 1)*100:+.0f}%")
    assert adjusted2 < base_risk, "Loss streak should decrease risk"
    print("   ✓ Loss streak decreases risk")
    
    # Test high volatility adjustment
    print("\n3. High Volatility Adjustment...")
    rm3 = RiskManager(1000, 0.02, 3)
    adjusted3 = rm3.adjust_risk_for_conditions(base_risk, market_volatility=0.08, win_rate=0.5)
    print(f"   Base risk: {base_risk:.2%}")
    print(f"   Market volatility: 8%")
    print(f"   Adjusted risk: {adjusted3:.2%}")
    print(f"   Change: {(adjusted3/base_risk - 1)*100:+.0f}%")
    assert adjusted3 < base_risk, "High volatility should decrease risk"
    print("   ✓ High volatility decreases risk")
    
    # Test high win rate adjustment
    print("\n4. High Win Rate Adjustment...")
    rm4 = RiskManager(1000, 0.02, 3)
    adjusted4 = rm4.adjust_risk_for_conditions(base_risk, market_volatility=0.03, win_rate=0.75)
    print(f"   Base risk: {base_risk:.2%}")
    print(f"   Win rate: 75%")
    print(f"   Adjusted risk: {adjusted4:.2%}")
    print(f"   Change: {(adjusted4/base_risk - 1)*100:+.0f}%")
    assert adjusted4 > base_risk, "High win rate should increase risk"
    print("   ✓ High win rate increases risk")
    
    # Test drawdown protection
    print("\n5. Drawdown Protection...")
    rm5 = RiskManager(1000, 0.02, 3)
    rm5.current_drawdown = 0.18  # 18% drawdown
    adjusted5 = rm5.adjust_risk_for_conditions(base_risk, market_volatility=0.03, win_rate=0.5)
    print(f"   Base risk: {base_risk:.2%}")
    print(f"   Current drawdown: 18%")
    print(f"   Adjusted risk: {adjusted5:.2%}")
    print(f"   Change: {(adjusted5/base_risk - 1)*100:+.0f}%")
    assert adjusted5 < base_risk, "Drawdown should decrease risk"
    print("   ✓ Drawdown protection active")
    
    # Test combined effects
    print("\n6. Combined Effects (Cold Streak + High Vol)...")
    rm6 = RiskManager(1000, 0.02, 3)
    rm6.loss_streak = 3
    adjusted6 = rm6.adjust_risk_for_conditions(base_risk, market_volatility=0.07, win_rate=0.3)
    print(f"   Base risk: {base_risk:.2%}")
    print(f"   Loss streak: 3, High vol: 7%, Low win rate: 30%")
    print(f"   Adjusted risk: {adjusted6:.2%}")
    print(f"   Change: {(adjusted6/base_risk - 1)*100:+.0f}%")
    assert adjusted6 < base_risk * 0.5, "Multiple negative factors should significantly reduce risk"
    print("   ✓ Combined effects work correctly")
    
    print("\n✓ All risk adjustment tests passed!")

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 RISK MANAGEMENT & ORDER EXECUTION - VALIDATION TESTS")
    print("="*70)
    print("\nValidating advanced risk management features...")
    
    try:
        success = True
        success = test_portfolio_heat() and success
        success = test_correlation_risk() and success
        success = test_risk_adjustment() and success
        
        print("\n" + "="*70)
        if success:
            print("✅ ALL RISK MANAGEMENT TESTS PASSED!")
            print("\nNew features validated:")
            print("  • Portfolio heat calculation")
            print("  • Correlation-aware position limits")
            print("  • Dynamic risk adjustment (streaks, volatility, drawdown)")
            print("  • Multi-factor risk scaling")
        else:
            print("❌ SOME TESTS FAILED")
        print("="*70)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
