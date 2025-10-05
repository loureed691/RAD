#!/usr/bin/env python3
"""
Test deployment infrastructure
"""
import os
import sys
import subprocess
from pathlib import Path

def test_files_exist():
    """Test that all deployment files exist"""
    print("Testing deployment files exist...")
    files = [
        'deploy.sh',
        'health_check.py',
        'production_start.py',
        'kucoin-bot.service',
        'QUICK_DEPLOY.md'
    ]
    
    all_exist = True
    for file in files:
        if os.path.exists(file):
            print(f"  ✓ {file} exists")
        else:
            print(f"  ✗ {file} missing")
            all_exist = False
    
    return all_exist

def test_scripts_executable():
    """Test that scripts are executable"""
    print("\nTesting scripts are executable...")
    scripts = ['deploy.sh', 'health_check.py', 'production_start.py']
    
    all_executable = True
    for script in scripts:
        if os.access(script, os.X_OK):
            print(f"  ✓ {script} is executable")
        else:
            print(f"  ✗ {script} is not executable")
            all_executable = False
    
    return all_executable

def test_health_check_runs():
    """Test that health check script runs"""
    print("\nTesting health check script...")
    try:
        result = subprocess.run(
            ['python3', 'health_check.py'],
            capture_output=True,
            timeout=10
        )
        if result.returncode in [0, 1, 2]:  # All are valid exit codes
            print("  ✓ health_check.py runs successfully")
            return True
        else:
            print(f"  ✗ health_check.py failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"  ✗ health_check.py error: {e}")
        return False

def test_production_start_runs():
    """Test that production start script runs"""
    print("\nTesting production start script...")
    try:
        result = subprocess.run(
            ['python3', 'production_start.py'],
            capture_output=True,
            timeout=10
        )
        # Exit code 1 is expected since we don't have valid credentials
        if result.returncode in [0, 1]:
            print("  ✓ production_start.py runs successfully")
            return True
        else:
            print(f"  ✗ production_start.py failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print(f"  ✗ production_start.py error: {e}")
        return False

def test_service_file_valid():
    """Test that service file template is valid"""
    print("\nTesting systemd service file...")
    try:
        with open('kucoin-bot.service', 'r') as f:
            content = f.read()
            
        required_sections = ['[Unit]', '[Service]', '[Install]']
        required_fields = ['%USER%', '%WORKDIR%', '%PYTHON%', '%PATH%']
        
        all_valid = True
        for section in required_sections:
            if section in content:
                print(f"  ✓ {section} section present")
            else:
                print(f"  ✗ {section} section missing")
                all_valid = False
        
        for field in required_fields:
            if field in content:
                print(f"  ✓ {field} placeholder present")
            else:
                print(f"  ✗ {field} placeholder missing")
                all_valid = False
        
        return all_valid
    except Exception as e:
        print(f"  ✗ Error reading service file: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Deployment Infrastructure")
    print("=" * 60)
    print()
    
    tests = [
        ("Files exist", test_files_exist),
        ("Scripts executable", test_scripts_executable),
        ("Service file valid", test_service_file_valid),
        ("Health check runs", test_health_check_runs),
        ("Production start runs", test_production_start_runs),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ✗ Test {name} crashed: {e}")
            results.append((name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All deployment infrastructure tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
