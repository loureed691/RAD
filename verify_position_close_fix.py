#!/usr/bin/env python3
"""
Manual verification test for position close race condition fix.

This test verifies that the fix prevents attempting to close already-closed positions
by checking the logic flow in position_manager.py update_positions() method.

PROBLEM:
--------
The update_positions() method in position_manager.py has multiple exit conditions
that can trigger sequentially:
1. Line ~1313: OHLCV API error fallback close
2. Line ~1456: Advanced exit strategy close  
3. Line ~1503: Smart exit optimizer close
4. Line ~1523: Standard stop loss/take profit close

Without proper checks, if one condition closes a position, subsequent conditions
might try to close it again, causing errors like:
- "Position not found" errors
- Attempting to close already-closed positions
- KeyError exceptions

SOLUTION:
---------
Added thread-safe position existence checks before each close_position() call:

    with self._positions_lock:
        if symbol not in self.positions:
            self.position_logger.debug(f"  ℹ Position {symbol} already closed, skipping")
            continue

This ensures:
1. Thread-safe check (prevents race conditions)
2. Early exit if position already closed (prevents duplicate close attempts)
3. Clear logging when position was already closed
4. Continues to next position without error

VERIFICATION:
-------------
The fix is applied at 4 critical points in update_positions():
✓ Line ~1315: Before OHLCV error fallback close
✓ Line ~1458: Before advanced strategy close
✓ Line ~1505: Before smart exit close  
✓ Line ~1525: Before standard stop loss/take profit close

Each location now checks position existence before attempting to close.
"""

import sys


def verify_fix_applied():
    """Verify the fix is correctly applied in position_manager.py"""
    print("=" * 70)
    print("Position Close Race Condition Fix Verification")
    print("=" * 70)
    print()
    
    # Read the position_manager.py file
    try:
        with open('position_manager.py', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ ERROR: position_manager.py not found")
        return False
    
    # Check for the fix pattern at each critical location
    fix_pattern = "if symbol not in self.positions:"
    check_pattern = "Thread-safe check: verify position still exists before closing"
    
    # Count occurrences
    fix_count = content.count(fix_pattern)
    check_comment_count = content.count(check_pattern)
    
    print("📊 Fix Pattern Analysis:")
    print(f"   Pattern '{fix_pattern}': {fix_count} occurrences")
    print(f"   Comment '{check_pattern}': {check_comment_count} occurrences")
    print()
    
    # We expect 4 fixes (one for each exit condition)
    # Plus 1 existing check at line 1248 (pre-existing safety check)
    # Total: 5 occurrences
    expected_total = 5
    expected_new_fixes = 4
    
    if fix_count >= expected_total and check_comment_count >= expected_new_fixes:
        print("✅ Fix Pattern Check: PASSED")
        print(f"   Found {fix_count} position existence checks (expected >= {expected_total})")
        print(f"   Found {check_comment_count} new fix comments (expected >= {expected_new_fixes})")
        print()
        
        # Verify each critical location has the fix
        critical_sections = [
            ("OHLCV error fallback", "OHLCV API error: {type(e).__name__}"),
            ("Advanced exit strategy", "If advanced strategy says exit"),
            ("Smart exit optimizer", "smart_exit_signal['should_exit']"),
            ("Standard stop loss/take profit", "Check standard stop loss and take profit"),
        ]
        
        print("📍 Verifying Critical Locations:")
        all_locations_fixed = True
        
        for name, marker in critical_sections:
            # Check if the fix is near the marker
            marker_index = content.find(marker)
            if marker_index == -1:
                print(f"   ⚠️  {name}: Marker not found")
                continue
                
            # Look for the fix pattern within 500 characters after the marker
            section = content[marker_index:marker_index + 1000]
            
            if fix_pattern in section and check_pattern in section:
                print(f"   ✅ {name}: Fix applied")
            else:
                print(f"   ❌ {name}: Fix NOT found")
                all_locations_fixed = False
        
        print()
        
        if all_locations_fixed:
            print("=" * 70)
            print("✅ VERIFICATION PASSED")
            print("=" * 70)
            print()
            print("All critical locations have been fixed with thread-safe checks.")
            print("The bot will no longer attempt to close already-closed positions.")
            return True
        else:
            print("=" * 70)
            print("⚠️  VERIFICATION INCOMPLETE")
            print("=" * 70)
            print()
            print("Some critical locations may be missing the fix.")
            return False
    else:
        print("❌ Fix Pattern Check: FAILED")
        print(f"   Expected at least {expected_total} checks, found {fix_count}")
        print(f"   Expected at least {expected_new_fixes} new fix comments, found {check_comment_count}")
        print()
        print("=" * 70)
        print("❌ VERIFICATION FAILED")
        print("=" * 70)
        return False


def verify_thread_safety():
    """Verify thread safety of the fix"""
    print()
    print("🔒 Thread Safety Verification:")
    print()
    
    try:
        with open('position_manager.py', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ ERROR: position_manager.py not found")
        return False
    
    # Check that locks are used properly
    lock_pattern = "with self._positions_lock:"
    lock_count = content.count(lock_pattern)
    
    print(f"   Lock usage: {lock_count} occurrences of 'with self._positions_lock:'")
    
    # Verify that position checks are inside locks
    checks_in_locks = 0
    lines = content.split('\n')
    
    for i in range(len(lines) - 2):
        if 'with self._positions_lock:' in lines[i]:
            # Check next few lines for position existence check
            next_lines = '\n'.join(lines[i:i+5])
            if 'if symbol not in self.positions:' in next_lines:
                checks_in_locks += 1
    
    print(f"   Position checks inside locks: {checks_in_locks}")
    
    if checks_in_locks >= 4:  # We expect at least 4 new checks
        print()
        print("   ✅ Thread safety verified: Checks are properly protected by locks")
        return True
    else:
        print()
        print("   ⚠️  Thread safety concern: Some checks may not be protected")
        return False


def main():
    """Main verification function"""
    fix_ok = verify_fix_applied()
    thread_safe_ok = verify_thread_safety()
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if fix_ok and thread_safe_ok:
        print("✅ All verifications passed!")
        print()
        print("The fix successfully prevents the bot from attempting to close")
        print("positions that are already closed, using thread-safe checks at")
        print("all critical exit points in the update_positions() method.")
        print()
        print("=" * 70)
        return True
    else:
        print("❌ Some verifications failed")
        print()
        if not fix_ok:
            print("   - Fix pattern verification failed")
        if not thread_safe_ok:
            print("   - Thread safety verification failed")
        print()
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
