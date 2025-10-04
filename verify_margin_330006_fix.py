#!/usr/bin/env python3
"""
Verification script for margin mode fix (error 330006)

This script demonstrates that the order creation methods now
correctly switch to cross margin mode before setting leverage,
which prevents error 330006: "Current mode is set to isolated margin. 
Please switch to cross margin before making further adjustments."
"""
import inspect
try:
    from kucoin_client import KuCoinClient
except ImportError as e:
    print("="*60)
    print("ERROR: Could not import 'KuCoinClient' from 'kucoin_client'.")
    print("Reason:", str(e))
    print("\nPlease ensure that the 'kucoin_client' module is installed and accessible.")
    print("="*60)
    import sys
    sys.exit(1)

def verify_margin_330006_fix():
    """Verify that margin mode is switched to cross before setting leverage"""
    
    print("="*60)
    print("Verifying Margin Mode Fix (Error 330006)")
    print("="*60)
    
    # Get the source code of the methods
    market_order_source = inspect.getsource(KuCoinClient.create_market_order)
    limit_order_source = inspect.getsource(KuCoinClient.create_limit_order)
    
    # Check if set_margin_mode is called before set_leverage
    checks = [
        ('create_market_order', market_order_source),
        ('create_limit_order', limit_order_source),
    ]
    
    all_passed = True
    
    for method_name, source in checks:
        print(f"\nChecking {method_name}...")
        
        # Check if set_margin_mode is called
        if "set_margin_mode('cross', symbol)" in source:
            print(f"  ✓ Calls set_margin_mode('cross', symbol)")
        elif 'set_margin_mode("cross", symbol)' in source:
            print(f"  ✓ Calls set_margin_mode('cross', symbol)")
        else:
            print(f"  ✗ Missing set_margin_mode('cross', symbol) call")
            all_passed = False
        
        # Check order of calls - set_margin_mode should come before set_leverage
        margin_mode_pos = source.find('set_margin_mode')
        leverage_pos = source.find('set_leverage')
        
        if margin_mode_pos > 0 and leverage_pos > 0:
            if margin_mode_pos < leverage_pos:
                print(f"  ✓ set_margin_mode called before set_leverage (correct order)")
            else:
                print(f"  ✗ set_margin_mode called after set_leverage (wrong order)")
                all_passed = False
        
        # Check if marginMode is set when calling set_leverage
        if 'set_leverage' in source and 'params={"marginMode": "cross"}' in source:
            print(f"  ✓ Leverage set with cross margin mode")
        else:
            print(f"  ✗ Leverage not properly configured")
            all_passed = False
        
        # Check if marginMode is included in create_order params
        if 'create_order' in source and 'params={"marginMode": "cross"}' in source:
            print(f"  ✓ Order creation includes marginMode parameter")
        else:
            print(f"  ✗ Order creation missing marginMode parameter")
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ All checks passed! Margin mode fix is properly implemented.")
        print("\nThe fix ensures that:")
        print("  1. Margin mode is switched to 'cross' for the symbol")
        print("  2. Leverage is set with cross margin mode")
        print("  3. Order creation explicitly specifies cross margin mode")
        print("  4. All calls are in the correct order")
        print("\nThis should resolve error code 330006:")
        print("  'Current mode is set to isolated margin. Please switch")
        print("   to cross margin before making further adjustments.'")
    else:
        print("✗ Some checks failed. Fix may not be complete.")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    import sys
    success = verify_margin_330006_fix()
    sys.exit(0 if success else 1)
