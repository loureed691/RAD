#!/usr/bin/env python3
"""
Comprehensive test runner for the RAD KuCoin Futures Trading Bot

This script runs all test suites and provides a summary of results.
Run with: python run_all_tests.py
"""
import subprocess
import sys
import os
from datetime import datetime

# Test configuration: (name, file, expected_test_count)
TEST_SUITES = [
    ("Core Components", "test_bot.py", 12),
    ("Bug Fixes", "test_bug_fixes.py", 4),
    ("Position Sync", "test_position_sync.py", 3),
    ("Position Mode", "test_position_mode_fix.py", 3),
    ("Strategy Optimizations", "test_strategy_optimizations.py", 5),
    ("Adaptive Stops", "test_adaptive_stops.py", 9),
    ("Logger Enhancements", "test_logger_enhancements.py", 7),
    ("Unicode Fix", "test_unicode_fix.py", 1),
    ("Advanced Features", "test_advanced_features.py", 6),
]

def print_header():
    """Print test runner header"""
    print("=" * 70)
    print("🧪 RAD TRADING BOT - COMPREHENSIVE TEST RUNNER")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Suites: {len(TEST_SUITES)}")
    print("=" * 70)

def run_test_suite(name, file, expected_count):
    """
    Run a single test suite
    
    Args:
        name: Display name of the test suite
        file: Python test file to run
        expected_count: Expected number of tests in the suite
        
    Returns:
        tuple: (success: bool, test_count: int)
    """
    try:
        result = subprocess.run(
            [sys.executable, file],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            return True, expected_count
        else:
            print(f"\n   ❌ Test output (last 20 lines):")
            for line in result.stdout.split("\n")[-20:]:
                if line.strip():
                    print(f"      {line}")
            return False, 0
            
    except subprocess.TimeoutExpired:
        print(f"\n   ⚠️  Test timed out after 60 seconds")
        return False, 0
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        return False, 0

def print_summary(results, total_tests):
    """Print test results summary"""
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print("\n" + "=" * 70)
    print(f"📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"Test Suites Passed: {passed}/{total}")
    print(f"Individual Tests Passed: {total_tests}")
    print("=" * 70)
    
    if all(results):
        print("\n✅ ALL TEST SUITES PASSED!")
        print("\n🎉 Bot functionality verified completely!")
        print(f"\nTotal tests: {total_tests}")
        print("\nThe bot is ready for deployment!")
    else:
        print("\n❌ SOME TEST SUITES FAILED")
        print("\nPlease review the failed tests above and fix any issues.")
        print("Run individual test files for more details:")
        for i, (name, file, _) in enumerate(TEST_SUITES):
            if not results[i]:
                print(f"  python {file}")

def main():
    """Main test runner"""
    print_header()
    
    results = []
    total_tests = 0
    
    for i, (name, file, expected_count) in enumerate(TEST_SUITES, 1):
        print(f"\n{i}️⃣  Running {name} ({file})...")
        
        success, count = run_test_suite(name, file, expected_count)
        results.append(success)
        
        if success:
            print(f"   ✅ PASSED ({count}/{count} tests)")
            total_tests += count
        else:
            print(f"   ❌ FAILED")
    
    print_summary(results, total_tests)
    
    return 0 if all(results) else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
