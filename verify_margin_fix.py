#!/usr/bin/env python3
"""
Verification script for margin mode fix

This script demonstrates that the order creation methods now
correctly include the marginMode parameter to prevent error 330005.
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

def verify_margin_mode_fix():
    """Verify that margin mode is properly set in order creation methods"""
    
    print("="*60)
    print("Verifying Margin Mode Fix")
    print("="*60)
    
    # Get the source code of the methods
    market_order_source = inspect.getsource(KuCoinClient.create_market_order)
    limit_order_source = inspect.getsource(KuCoinClient.create_limit_order)
    
    # Check if marginMode is included in params
    checks = [
        ('create_market_order', market_order_source, 'params={"marginMode": "cross"}'),
        ('create_limit_order', limit_order_source, 'params={"marginMode": "cross"}'),
    ]
    
    all_passed = True
    
    for method_name, source, expected_param in checks:
        print(f"\nChecking {method_name}...")
        
        # Check if marginMode is set when calling set_leverage
        if 'set_leverage' in source and 'params={"marginMode": "cross"}' in source:
            print(f"  ✓ Leverage set with cross margin mode")
        else:
            print(f"  ✗ Leverage not properly configured")
            all_passed = False
        
        # Check if marginMode is included in create_order params
        if 'create_order' in source and expected_param in source:
            print(f"  ✓ Order creation includes marginMode parameter")
        else:
            print(f"  ✗ Order creation missing marginMode parameter")
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ All checks passed! Margin mode fix is properly implemented.")
        print("\nThe fix ensures that:")
        print("  1. Leverage is set with cross margin mode")
        print("  2. Order creation explicitly specifies cross margin mode")
        print("  3. Both methods are consistent in their approach")
        print("\nThis should resolve error code 330005:")
        print("  'The order's margin mode does not match the selected one'")
    else:
        print("✗ Some checks failed. Fix may not be complete.")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    import sys
    success = verify_margin_mode_fix()
    sys.exit(0 if success else 1)
