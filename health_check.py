#!/usr/bin/env python3
"""
Health check script for KuCoin Futures Trading Bot
Monitors bot status and reports issues
"""
import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print header text"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def check_service_status():
    """Check if the bot service is running"""
    print_info("Checking systemd service status...")
    exit_code = os.system("systemctl is-active --quiet kucoin-bot.service")
    if exit_code == 0:
        print_success("Bot service is running")
        return True
    else:
        print_error("Bot service is not running")
        print_info("Start with: sudo systemctl start kucoin-bot")
        return False

def check_config_file():
    """Check if .env configuration exists"""
    print_info("Checking configuration...")
    if os.path.exists('.env'):
        print_success(".env file exists")
        
        # Check if credentials are set
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('KUCOIN_API_KEY', '')
        if api_key and api_key != 'your_api_key_here':
            print_success("API credentials configured")
            return True
        else:
            print_warning("API credentials not configured in .env")
            return False
    else:
        print_error(".env file not found")
        return False

def check_log_file():
    """Check log file for recent activity and errors"""
    print_info("Checking log file...")
    log_file = Path('logs/bot.log')
    
    if not log_file.exists():
        print_warning("Log file not found (bot may not have started yet)")
        return False
    
    # Check log file age
    mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
    age = datetime.now() - mod_time
    
    if age > timedelta(minutes=5):
        print_warning(f"Log file last modified {age.seconds // 60} minutes ago")
        print_info("Bot may not be actively running")
    else:
        print_success("Log file recently updated")
    
    # Check for errors in last 100 lines
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-100:] if len(lines) > 100 else lines
            
            errors = [line for line in recent_lines if 'ERROR' in line]
            warnings = [line for line in recent_lines if 'WARNING' in line]
            
            if errors:
                print_warning(f"Found {len(errors)} error(s) in recent logs")
                print_info("Last error:")
                print(f"  {errors[-1].strip()}")
            else:
                print_success("No recent errors in logs")
            
            if warnings:
                print_info(f"Found {len(warnings)} warning(s) in recent logs")
            
            return len(errors) == 0
    except Exception as e:
        print_error(f"Could not read log file: {e}")
        return False

def check_directories():
    """Check if required directories exist"""
    print_info("Checking directories...")
    required_dirs = ['logs', 'models']
    all_exist = True
    
    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print_success(f"{dir_name}/ directory exists")
        else:
            print_error(f"{dir_name}/ directory missing")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Check if required Python packages are installed"""
    print_info("Checking Python dependencies...")
    required_packages = [
        'ccxt',
        'pandas',
        'numpy',
        'sklearn',
        'ta',
        'dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print_error(f"Missing packages: {', '.join(missing)}")
        print_info("Install with: pip install -r requirements.txt")
        return False
    else:
        print_success("All dependencies installed")
        return True

def get_system_info():
    """Display system information"""
    print_info("System information...")
    
    # Disk usage
    import shutil
    total, used, free = shutil.disk_usage(".")
    disk_percent = (used / total) * 100
    
    print(f"  Disk usage: {used // (2**30)} GB / {total // (2**30)} GB ({disk_percent:.1f}%)")
    
    if disk_percent > 90:
        print_warning("Disk usage is high")
    
    # Memory usage (if psutil available)
    try:
        import psutil
        memory = psutil.virtual_memory()
        print(f"  Memory usage: {memory.percent}%")
        
        if memory.percent > 90:
            print_warning("Memory usage is high")
    except ImportError:
        pass

def main():
    """Main health check function"""
    print_header("KuCoin Bot Health Check")
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    results = {
        'config': check_config_file(),
        'dependencies': check_dependencies(),
        'directories': check_directories(),
        'logs': check_log_file(),
    }
    
    # Try to check service (may fail if not installed)
    try:
        results['service'] = check_service_status()
    except:
        print_info("Service status check skipped (not running as systemd service)")
        results['service'] = None
    
    get_system_info()
    
    # Summary
    print_header("Health Check Summary")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    if skipped > 0:
        print(f"⊘ Skipped: {skipped}")
    
    if failed == 0:
        print_success("\n✅ Bot appears to be healthy!")
        return 0
    elif failed <= 2:
        print_warning("\n⚠️  Bot has some issues but may be functional")
        return 1
    else:
        print_error("\n❌ Bot has significant issues")
        return 2

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nHealth check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Health check failed: {e}")
        sys.exit(1)
