"""
Extreme test cases to verify the position sizing fix handles edge cases
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_extreme_scenarios():
    """Test extreme scenarios that would have broken before the fix"""
    from risk_manager import RiskManager
    
    print("="*80)
    print("EXTREME SCENARIO TESTING")
    print("="*80)
    
    manager = RiskManager(
        max_position_size=10000,  # Intentionally huge
        risk_per_trade=0.02,
        max_open_positions=3
    )
    
    test_cases = [
        {
            'name': 'Tiny balance with huge max_position_size',
            'balance': 5.0,
            'entry_price': 100000.0,  # Very expensive asset
            'stop_loss_price': 98000.0,
            'leverage': 10,
        },
        {
            'name': 'Extremely tight stop (0.1%)',
            'balance': 100.0,
            'entry_price': 50000.0,
            'stop_loss_price': 49950.0,  # 0.1% stop
            'leverage': 20,
        },
        {
            'name': 'Very high leverage (50x) - should be capped',
            'balance': 100.0,
            'entry_price': 1000.0,
            'stop_loss_price': 980.0,
            'leverage': 50,
        },
        {
            'name': 'Micro account ($2) with normal settings',
            'balance': 2.0,
            'entry_price': 30000.0,
            'stop_loss_price': 29400.0,
            'leverage': 5,
        },
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {test['name']}")
        print('='*80)
        
        balance = test['balance']
        entry_price = test['entry_price']
        stop_loss_price = test['stop_loss_price']
        leverage = test['leverage']
        
        print(f"\nSetup:")
        print(f"  Balance: ${balance:.2f}")
        print(f"  Entry: ${entry_price:.2f}")
        print(f"  Stop: ${stop_loss_price:.2f} ({abs(entry_price-stop_loss_price)/entry_price:.2%})")
        print(f"  Leverage: {leverage}x")
        
        try:
            position_size = manager.calculate_position_size(
                balance, entry_price, stop_loss_price, leverage
            )
            
            position_value = position_size * entry_price
            required_margin = position_value / leverage
            
            print(f"\nResult:")
            print(f"  Position Size: {position_size:.8f} contracts")
            print(f"  Position Value: ${position_value:.2f}")
            print(f"  Required Margin: ${required_margin:.2f}")
            print(f"  Margin Usage: {required_margin/balance:.1%}")
            
            # Validation
            if required_margin > balance:
                print(f"\n  ❌ FAILED: Required margin ${required_margin:.2f} > balance ${balance:.2f}")
                all_passed = False
            else:
                print(f"\n  ✅ PASSED: Position respects balance limits")
            
            # Additional sanity checks
            if position_value < 0:
                print(f"  ❌ FAILED: Negative position value")
                all_passed = False
            
            if position_size < 0:
                print(f"  ❌ FAILED: Negative position size")
                all_passed = False
                
        except Exception as e:
            print(f"\n  ❌ EXCEPTION: {e}")
            all_passed = False
    
    print(f"\n{'='*80}")
    if all_passed:
        print("✅ ALL EXTREME SCENARIOS PASSED!")
        print("The fix handles even extreme edge cases correctly.")
    else:
        print("❌ SOME TESTS FAILED")
        print("There may be remaining issues with extreme scenarios.")
    print('='*80)
    
    return all_passed


if __name__ == "__main__":
    success = test_extreme_scenarios()
    sys.exit(0 if success else 1)
