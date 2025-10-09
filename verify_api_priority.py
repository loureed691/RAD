#!/usr/bin/env python3
"""
Quick verification script for API priority fix

Run this to verify the API priority fix is properly installed.
"""

def verify_priority_fix():
    """Verify the API priority fix is installed and working"""
    print("=" * 70)
    print("API PRIORITY FIX - VERIFICATION")
    print("=" * 70)
    print()
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: bot.py exists and has priority code
    print("CHECK 1: Verifying bot.py has priority system...")
    checks_total += 1
    try:
        with open('bot.py', 'r') as f:
            bot_content = f.read()
        
        has_priority_logging = 'THREAD START PRIORITY' in bot_content
        has_position_first = bot_content.find('self._position_monitor_thread.start()') < bot_content.find('self._scan_thread.start()')
        has_delay = 'time.sleep(0.5)' in bot_content or 'time.sleep(1)' in bot_content
        
        if has_priority_logging and has_position_first and has_delay:
            print("  ✅ PASS: bot.py has priority system installed")
            checks_passed += 1
        else:
            print("  ❌ FAIL: bot.py missing priority system")
            if not has_priority_logging:
                print("     Missing: Priority logging")
            if not has_position_first:
                print("     Missing: Position monitor starts first")
            if not has_delay:
                print("     Missing: Startup delay")
    except FileNotFoundError:
        print("  ❌ FAIL: bot.py not found")
    print()
    
    # Check 2: Test file exists
    print("CHECK 2: Verifying test file exists...")
    checks_total += 1
    try:
        with open('test_api_priority.py', 'r') as f:
            test_content = f.read()
        if 'test_thread_start_order' in test_content:
            print("  ✅ PASS: test_api_priority.py exists")
            checks_passed += 1
        else:
            print("  ❌ FAIL: test_api_priority.py incomplete")
    except FileNotFoundError:
        print("  ❌ FAIL: test_api_priority.py not found")
    print()
    
    # Check 3: Documentation exists
    print("CHECK 3: Verifying documentation exists...")
    checks_total += 1
    docs_exist = True
    required_docs = [
        'WHATS_NEW_API_PRIORITY.md',
        'QUICKREF_API_PRIORITY.md',
        'API_PRIORITY_FIX.md',
    ]
    for doc in required_docs:
        try:
            with open(doc, 'r'):
                pass
        except FileNotFoundError:
            print(f"  ⚠️  Missing: {doc}")
            docs_exist = False
    
    if docs_exist:
        print("  ✅ PASS: All documentation files present")
        checks_passed += 1
    else:
        print("  ❌ FAIL: Some documentation files missing")
    print()
    
    # Check 4: Scanner has startup delay
    print("CHECK 4: Verifying scanner has startup delay...")
    checks_total += 1
    try:
        with open('bot.py', 'r') as f:
            bot_content = f.read()
        
        scanner_start = bot_content.find('def _background_scanner')
        if scanner_start == -1:
            print("  ❌ FAIL: def _background_scanner not found in bot.py")
        else:
            scanner_method = bot_content[scanner_start:scanner_start + 2000]
            first_while = scanner_method.find('while self._scan_thread_running')
            before_loop = scanner_method[:first_while] if first_while != -1 else scanner_method
            
            if 'time.sleep' in before_loop:
                print("  ✅ PASS: Scanner has startup delay")
                checks_passed += 1
            else:
                print("  ❌ FAIL: Scanner missing startup delay")
    except Exception as e:
        print(f"  ❌ FAIL: Error checking scanner: {e}")
    print()
    
    # Summary
    print("=" * 70)
    print(f"VERIFICATION RESULTS: {checks_passed}/{checks_total} checks passed")
    print("=" * 70)
    print()
    
    if checks_passed == checks_total:
        print("✅ API PRIORITY FIX IS PROPERLY INSTALLED!")
        print()
        print("Next steps:")
        print("  1. Restart your bot to activate the priority system")
        print("  2. Check logs for priority messages at startup")
        print("  3. Run 'python3 test_api_priority.py' for detailed tests")
        print()
        print("See WHATS_NEW_API_PRIORITY.md for more information.")
        return True
    else:
        print("⚠️  API PRIORITY FIX IS INCOMPLETE")
        print()
        print("Some checks failed. Please:")
        print("  1. Ensure you have the latest code")
        print("  2. Check if all files were pulled correctly")
        print("  3. Review the failed checks above")
        print()
        print("For help, see API_PRIORITY_FIX.md")
        return False


if __name__ == "__main__":
    import sys
    success = verify_priority_fix()
    sys.exit(0 if success else 1)
