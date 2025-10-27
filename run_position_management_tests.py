#!/usr/bin/env python3
"""
Unified Position Management Test Runner

Runs all position management test suites:
1. Comprehensive tests (9 tests)
2. Advanced tests (7 tests)

Total: 16 tests covering all aspects of position management
"""

import sys
import subprocess
import os
from datetime import datetime


# Allow timeout configuration via environment variable
TEST_TIMEOUT = int(os.environ.get('TEST_TIMEOUT', '120'))


def run_test_suite(script_name, description):
    """Run a test suite and return results"""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print(f"Timeout: {TEST_TIMEOUT} seconds")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=TEST_TIMEOUT
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"✗ {description} timed out after {TEST_TIMEOUT} seconds")
        return False
    except Exception as e:
        print(f"✗ {description} failed with error: {e}")
        return False


def main():
    """Run all test suites"""
    print("="*80)
    print("POSITION MANAGEMENT - FULL TEST SUITE")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Timeout per suite: {TEST_TIMEOUT} seconds")
    print(f"(Set TEST_TIMEOUT env var to override)\n")
    
    test_suites = [
        (
            "test_position_management_comprehensive.py",
            "Comprehensive Position Management Tests (9 tests)"
        ),
        (
            "test_position_management_advanced.py",
            "Advanced Position Management Tests (7 tests)"
        ),
    ]
    
    results = []
    for script, description in test_suites:
        success = run_test_suite(script, description)
        results.append((description, success))
    
    # Print final summary
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {description}")
    
    print("\n" + "="*80)
    print(f"Results: {passed}/{total} test suites passed")
    print(f"Total tests: 16 (9 comprehensive + 7 advanced)")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    if passed == total:
        print("\n✅ ALL POSITION MANAGEMENT TESTS PASSED!")
        print("Position management is production-ready.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please review the failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
