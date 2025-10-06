#!/usr/bin/env python3
"""
Test price formatting for various cryptocurrency prices
"""

def format_price(price: float) -> str:
    """
    Format price with appropriate precision based on magnitude.
    
    Args:
        price: Price value to format
        
    Returns:
        Formatted price string with appropriate decimal places
    """
    if price == 0:
        return "0.00"
    
    abs_price = abs(price)
    
    # For prices >= 1000, use 2 decimals (e.g., 1213.68)
    if abs_price >= 1000:
        return f"{price:.2f}"
    # For prices >= 1, use 2 decimals (e.g., 5.33, 16.78)
    elif abs_price >= 1:
        return f"{price:.2f}"
    # For prices >= 0.1, use 2 decimals (e.g., 0.88, 0.50)
    elif abs_price >= 0.1:
        return f"{price:.2f}"
    # For prices >= 0.01, use 4 decimals (e.g., 0.0567)
    elif abs_price >= 0.01:
        return f"{price:.4f}"
    # For prices >= 0.001, use 5 decimals (e.g., 0.00567)
    elif abs_price >= 0.001:
        return f"{price:.5f}"
    # For very small prices, use 6 decimals (e.g., 0.001234)
    else:
        return f"{price:.6f}"

def format_pnl_usd(pnl_usd: float) -> str:
    """
    Format P/L USD amount with sign prefix and appropriate precision.
    
    Args:
        pnl_usd: P/L in USD
        
    Returns:
        Formatted P/L string with sign (e.g., "$+1.23", "$-0.0045")
    """
    sign = "+" if pnl_usd >= 0 else "-"
    abs_value = abs(pnl_usd)
    formatted = format_price(abs_value)
    return f"${sign}{formatted}"

def test_format_price():
    """Test format_price function with various price ranges"""
    print("Testing format_price function:")
    print("=" * 60)
    
    test_cases = [
        # (input, expected_format_description)
        (1213.68, "Large price >= 1000"),
        (50000.12345, "Very large price"),
        (5.33, "Medium price >= 1"),
        (16.78, "Medium price >= 1"),
        (0.88, "Price >= 0.1"),
        (0.50, "Price >= 0.1"),
        (0.06, "Price >= 0.01 (should show 4 decimals)"),
        (0.0567, "Price >= 0.01"),
        (0.02, "Price >= 0.01"),
        (0.001234, "Price >= 0.001 (should show 5 decimals)"),
        (0.005678, "Price >= 0.001"),
        (0.0001234, "Very small price (should show 6 decimals)"),
        (0.00005678, "Very small price"),
        (0.0, "Zero price"),
    ]
    
    all_passed = True
    for price, description in test_cases:
        formatted = format_price(price)
        print(f"  {description}:")
        print(f"    Input: {price}")
        print(f"    Output: {formatted}")
        
        # Verify we don't lose precision for small values
        if 0 < price < 0.01:
            if formatted == "0.00":
                print(f"    ✗ FAIL: Lost precision!")
                all_passed = False
            else:
                print(f"    ✓ PASS: Precision preserved")
        else:
            print(f"    ✓ OK")
        print()
    
    return all_passed

def test_format_pnl_usd():
    """Test format_pnl_usd function with various P/L amounts"""
    print("\nTesting format_pnl_usd function:")
    print("=" * 60)
    
    test_cases = [
        # (input, expected_prefix)
        (10.50, "+"),
        (-5.25, "-"),
        (0.001234, "+"),
        (-0.005678, "-"),
        (0.0, "+"),
        (-0.00001, "-"),
        (1000.50, "+"),
        (-1234.56, "-"),
    ]
    
    all_passed = True
    for pnl_usd, expected_sign in test_cases:
        formatted = format_pnl_usd(pnl_usd)
        print(f"  Input: {pnl_usd:+.6f}")
        print(f"    Output: {formatted}")
        
        # Verify sign is correct
        if pnl_usd >= 0:
            if not formatted.startswith("$+"):
                print(f"    ✗ FAIL: Expected positive sign")
                all_passed = False
            else:
                print(f"    ✓ PASS: Correct positive sign")
        else:
            if not formatted.startswith("$-"):
                print(f"    ✗ FAIL: Expected negative sign")
                all_passed = False
            else:
                print(f"    ✓ PASS: Correct negative sign")
        
        # Verify we don't lose precision for small values
        abs_value = abs(pnl_usd)
        if 0 < abs_value < 0.01:
            # Check if the formatted value rounds to zero
            value_part = formatted[2:]  # Remove $+ or $-
            if value_part == "0.00":
                print(f"    ✗ FAIL: Lost precision in small P/L!")
                all_passed = False
            else:
                print(f"    ✓ PASS: Precision preserved in P/L")
        print()
    
    return all_passed

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PRICE FORMATTING TESTS")
    print("=" * 60 + "\n")
    
    price_test_passed = test_format_price()
    pnl_test_passed = test_format_pnl_usd()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if price_test_passed and pnl_test_passed:
        print("✓ All tests PASSED")
        return 0
    else:
        print("✗ Some tests FAILED")
        return 1

if __name__ == "__main__":
    exit(main())
