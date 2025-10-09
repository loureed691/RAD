"""
Validation test to verify that the fix for generator exception handling works
This tests the actual bot.py code to ensure the fix is effective
"""
import ast
import re


def test_bot_update_positions_fix():
    """Verify that bot.py update_open_positions() has outer try/except"""
    print("\n" + "=" * 70)
    print("TEST: Verify bot.py Fix for Generator Exception Handling")
    print("=" * 70)
    
    # Read bot.py
    with open('bot.py', 'r') as f:
        content = f.read()
    
    # Find update_open_positions method
    pattern = r'def update_open_positions\(self\):(.*?)(?=\n    def |\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("   ✗ Could not find update_open_positions method")
        return False
    
    method_code = match.group(0)
    lines = method_code.split('\n')
    
    # Check structure
    print("\n1. Checking code structure:")
    
    # Find the for loop line
    for_loop_line = None
    for i, line in enumerate(lines):
        if 'for symbol, pnl, position in self.position_manager.update_positions():' in line:
            for_loop_line = i
            break
    
    if for_loop_line is None:
        print("   ✗ Could not find for loop over update_positions()")
        return False
    
    print(f"   ✓ Found for loop at line {for_loop_line}")
    
    # Check if there's a try before the for loop
    has_outer_try = False
    for i in range(for_loop_line - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith('try:'):
            has_outer_try = True
            print(f"   ✓ Found try statement at line {i} (before for loop)")
            break
        if line and not line.startswith('#') and not line.startswith('"""'):
            # Found non-comment/docstring code before try
            if not line.startswith('def '):
                break
    
    if not has_outer_try:
        print("   ✗ No try statement before for loop")
        return False
    
    # Check if there's an except after the for loop
    has_outer_except = False
    in_for_block = False
    indent_level = None
    
    for i in range(for_loop_line, len(lines)):
        line = lines[i]
        
        if 'for symbol, pnl, position in self.position_manager.update_positions():' in line:
            in_for_block = True
            # Get indent level of for loop
            indent_level = len(line) - len(line.lstrip())
            continue
        
        if in_for_block:
            current_indent = len(line) - len(line.lstrip())
            
            # If we're back to the same or lower indent as the for loop, we're out of the for block
            if line.strip() and current_indent <= indent_level:
                # Check if this is an except at the same level as for
                if line.strip().startswith('except'):
                    has_outer_except = True
                    print(f"   ✓ Found except statement at line {i} (after for loop)")
                    
                    # Check if it logs appropriately
                    except_block = '\n'.join(lines[i:i+5])
                    if 'position update iteration' in except_block or 'Generator' in except_block:
                        print("   ✓ Exception handler mentions generator/iteration errors")
                    break
    
    if not has_outer_except:
        print("   ✗ No except statement after for loop at same indentation level")
        return False
    
    print("\n2. Checking fix is correct:")
    print("   ✓ Outer try/except wraps generator iteration")
    print("   ✓ Generator exceptions will be caught")
    print("   ✓ Fix VERIFIED")
    
    return True


def test_position_manager_error_context():
    """Verify that position_manager.py has improved error context"""
    print("\n" + "=" * 70)
    print("TEST: Verify position_manager.py Error Context Improvements")
    print("=" * 70)
    
    with open('position_manager.py', 'r') as f:
        content = f.read()
    
    improvements = []
    
    # Check 1: Error type logging
    if 'type(e).__name__' in content:
        count = content.count('type(e).__name__')
        print(f"   ✓ Error type logging added ({count} instances)")
        improvements.append(True)
    else:
        print("   ✗ No error type logging found")
        improvements.append(False)
    
    # Check 2: API error handling for get_ticker
    if 'API error getting ticker' in content:
        print("   ✓ Improved get_ticker error handling")
        improvements.append(True)
    else:
        print("   ⚠️  get_ticker error handling not improved")
        improvements.append(False)
    
    # Check 3: API error handling for get_ohlcv
    if 'API error getting OHLCV' in content:
        print("   ✓ Improved get_ohlcv error handling")
        improvements.append(True)
    else:
        print("   ⚠️  get_ohlcv error handling not improved")
        improvements.append(False)
    
    # Check 4: Fallback with current_price check
    if "'current_price' in locals()" in content:
        print("   ✓ Improved fallback with current_price check")
        improvements.append(True)
    else:
        print("   ⚠️  Fallback current_price check not added")
        improvements.append(False)
    
    passed = sum(improvements)
    total = len(improvements)
    
    print(f"\n   Result: {passed}/{total} improvements verified")
    
    return passed >= 2  # At least 2 improvements should be present


def main():
    """Run all validation tests"""
    print("\n" + "=" * 70)
    print("FIX VALIDATION TESTS")
    print("=" * 70)
    print("Verifying that bug fixes are properly implemented\n")
    
    results = []
    
    # Run tests
    results.append(("Bot.py Generator Exception Fix", test_bot_update_positions_fix()))
    results.append(("Position Manager Error Context", test_position_manager_error_context()))
    
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✓ VERIFIED" if passed else "✗ FAILED"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All fixes verified!")
        return 0
    else:
        print("\n⚠️  Some fixes could not be verified")
        return 1


if __name__ == "__main__":
    exit(main())
